# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS IS."
#  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES, OFFICERS,
#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED, AS TO THE USEFULNESS
#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE. THEY ASSUME NO RESPONSIBILITY
#  (1) FOR THE USE OF THE SOFTWARE AND DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL
#  SUPPORT TO USERS.
"""
.. module:: echolab2.simrad_signal_proc

    :synopsis: Functions for processing Simrad EK80 data. Based on work
               by Chris Bassett, Lars Nonboe Anderson, Gavin Macaulay,
               Dezhang Chu, and many others.


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assesment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>
"""

import numpy as np

def create_ek80_tx(raw_data, calibration, return_pc=False,
        return_indices=None, fast=False):
    '''create_ek80_tx returns an array representing the ideal
    EK80 transmit signal computed using the parameters in the raw_data
    and calibration objects.

    fast (bool) - Set to true to assume all pings share the same Tx
                  signal. The signal and effective pulse length will
                  be computed for the first ping and replicated for
                  all others.

    '''

    # If we're not given specific indices, grab everything.
    if return_indices is None:
        return_indices = np.arange(raw_data.ping_time.shape[0])

    # Ensure that return_indices is a numpy array
    elif type(return_indices) is not np.ndarray:
        return_indices = np.array(return_indices, ndmin=1)

    #  create a dict to hold our calibration data parameters we need
    cal_parms = {'slope':None,
                 'transmit_power':None,
                 'pulse_duration':None,
                 'frequency_start':None,
                 'frequency_end':None,
                 'frequency':None,
                 'impedance':None,
                 'rx_sample_frequency':None,
                 'sample_interval':None,
                 'filters':None}

    # Check if we have already computed the Tx signal - This function is
    # called multiple times during the conversion process so we cache the
    # results in the calibration object to speed things up. The cached
    # data is normally discarded at the end of the conversion process to
    # ensure stale data is not used during another conversion.
    cal_has_tx_data = False
    if hasattr(calibration, '_tx_signal') and hasattr(calibration, '_tau_eff'):
        # Check if the existing data has the correct dimensions. This
        # should always be the case
        if calibration._tau_eff.shape[0] == return_indices.shape[0]:
            cal_has_tx_data = True

    # Check if we have cached data
    if not cal_has_tx_data:
        # No - compute new Tx signals

        # create the return arrays
        #tx_data = np.empty(return_indices.shape[0], dtype=np.ndarray)
        n_return = return_indices.shape[0]
        tx_data = []
        tau_eff = np.empty(n_return, dtype=np.float32)

        # Get the cal params we need
        for key in cal_parms:
            cal_parms[key] = calibration.get_parameter(raw_data, key, return_indices)

        # if this is CW data, we will not have the start/end params so we
        # set them to cal_parms['frequency']
        if cal_parms['frequency_start'] is None:
            cal_parms['frequency_start'] = cal_parms['frequency']
            cal_parms['frequency_end'] = cal_parms['frequency']

        # Iterate thru the return indices
        if fast:
            #  if the fast keyword is set, we assume all of the pings will
            #  be the same so we only compute the first Tx signal and then
            #  replicate it below.
            return_indices = [return_indices[0]]

        for idx, ping_index in enumerate(return_indices):

            #  get the theoretical tx signal
            t, y = ek80_chirp(cal_parms['transmit_power'][idx], cal_parms['frequency_start'][idx],
                    cal_parms['frequency_end'][idx], cal_parms['slope'][idx],
                    cal_parms['pulse_duration'][idx], raw_data.ZTRANSDUCER,
                    cal_parms['rx_sample_frequency'][idx])

            #  apply the stage 1 and stage 2 filters
            y = filter_and_decimate(y, cal_parms['filters'][idx], [1, 2])

            #  compute effective pulse duration
            if return_pc and raw_data.pulse_form[idx] > 0:
                y_eff = np.convolve(y, np.flipud(np.conj(y))) / np.linalg.norm(y) ** 2
            else:
                y_eff = y

            fs_dec = 1 / cal_parms['sample_interval'][idx]
            ptxa = np.abs(y_eff) ** 2
            teff =  np.sum(ptxa) / (np.max(ptxa) * fs_dec)

            #  store this ping's tx signal
            #tx_data[idx] = y
            tx_data.append(y)
            tau_eff[idx] =  teff

        if fast:
            #  We're assuming all pings are the same. Replicate first Tx signal to all pings.
            tx_data = [y] * n_return
            tau_eff[1:] =  teff

        # cache the results in the calibration object
        calibration._tx_signal = tx_data
        calibration._tau_eff = tau_eff

        return tx_data, tau_eff

    else:
        #  return the cached data
        return calibration._tx_signal, calibration._tau_eff


def compute_effective_pulse_duration(raw_data, calibration, return_pc=False,
        return_indices=None, fast=False):

    # Get the ideal transmit pulse which also returns effective pulse duration
    tx_data, tau_eff = create_ek80_tx(raw_data, calibration, return_pc=return_pc,
            return_indices=return_indices, fast=fast)

    return tau_eff


def filter_and_decimate(y, filters, stages):
    '''filter_and_decimate will apply one or more convolution and
    decimation operations on the provided data.

        y (complex) - The signal to be filtered
        filters (dict) - The filters dictionary associated with the signal
                         being filtered.
        stages (int, list) - A scalar integer or list of integers containing
                             the filter stage(s) to apply. Stages are applied
                             in the order they are added to the list.

    '''
    #  make sure stages is iterable - make it so if not.
    try:
        iter(stages)
    except Exception:
        stages = [stages]

    #  get the procided filter stages
    filter_stages = filters.keys()

    # iterate through the stages and apply filters in order provided
    for stage in stages:
        #  make sure this filter exists
        if not stage in filter_stages:
            raise ValueError("Filter stage " + str(stage) + " is not in the " +
                    "supplied filters dictionary.")

        # get the filter coefficients and decimation factor
        coefficients = filters[stage]['coefficients']
        decimation_factor = filters[stage]['decimation_factor']

        # apply filter
        y = np.convolve(y, coefficients)

        # and decimate
        y = y[0::decimation_factor]

    return y


def ek80_chirp(txpower, fstart, fstop, slope, tau, z, rx_freq):
    '''ek80_chirp returns a representation of the EK80 transmit signal
    as (time, amplitude) with a maximum amplitude of 1.

    This code was originally written in MATLAB by
        Chris Bassett - cbassett@uw.edu
        University of Washington Applied Physics Lab

    txpower (float) - The transmit power in watts
    fstart (float) - The starting Frequency of the tx signal obtained
                    from the raw file configuration datagram in Hz.
    fstart (float) - The starting Frequency of the tx signal obtained
                    from the raw file configuration datagram in Hz.
    slope (float) - The slope of the signal ramp up and ramp down
    tau (float) - The commanded transmit pulse length in s.
    z (float) - The transducer impedance obtained from the raw file
                configuration datagram in ohms.
    rx_freq (float) - the receiver A/D sampling frequency in Hz

    '''

    # Create transmit signal
    sf = 1.0 / rx_freq
    a  = np.sqrt((txpower / 4.0) * (2.0 * z))
    t = np.arange(0, tau, sf)
    nt = t.shape[0]
    nwtx = int(2 * np.floor(slope * nt))
    wtx_tmp = np.hanning(nwtx)
    nwtxh = int(np.round(nwtx / 2))
    wtx = np.concatenate([wtx_tmp[0:nwtxh], np.ones((nt - nwtx)), wtx_tmp[nwtxh:]])
    beta = (fstop - fstart) * (tau ** -1)
    chirp = np.cos(2.0 * np.pi * (beta / 2.0 * (t ** 2) + fstart * t))
    y_tmp = a * chirp * wtx

    # The transmit signal must have a max amplitude of 1
    y = y_tmp / np.max(np.abs(y_tmp))

    return t, y


def pulse_compression(raw_data, calibration, return_indices=None, fast=False):
    '''pulse_compression applies a matched filter to the received signal using
    the simulated Tx signal as the filter template. This method will only apply
    the filter to FM pings. It does nothing to CW pings.


    fast (bool) - Set to True if calibration parameters for all FM pings are
                  the same. When True, the Tx signal generated for the first
                  FM ping will be used for all other FM ping. When False,
                  a unique Tx signal is generated for each FM ping.
    '''

    # If we're not given specific indices, grab everything.
    if return_indices is None:
        return_indices = np.arange(raw_data.ping_time.shape[0])
    # Ensure that return_indices is a numpy array
    elif type(return_indices) is not np.ndarray:
        return_indices = np.array(return_indices, ndmin=1)

    # Check if we have any fm pings to process
    is_fm = raw_data.pulse_form[return_indices] > 0
    if np.any(is_fm):
        # we do have fm pings - get the indices for those fm pings
        fm_pings = return_indices[is_fm]

        # get the simulated tx signal for these pings
        tx_signal, _ = create_ek80_tx(raw_data, calibration, return_indices=fm_pings,
                fast=fast)

        # create a copy of the data to operate on and return
        p_data = raw_data.complex.copy()

        # apply match filter to these pings
        for p_idx, tx in enumerate(tx_signal):
            # create matched filter using tx signal for this ping
            tx_mf = np.flipud(np.conj(tx))
            ltx = tx_mf.shape[0]
            tx_n = np.linalg.norm(tx) ** 2

            # apply the filter to each of the transducer sectors
            for q_idx in range(p_data[p_idx,:,:].shape[1]):
                # apply the filter
                filtered = np.convolve(p_data[p_idx,:,q_idx], tx_mf) / tx_n
                # remove filter delay
                p_data[p_idx,:,q_idx] = filtered[ltx-1:]

    else:
        # don't copy if we're not modifying the data
        p_data = raw_data.complex

    return p_data
