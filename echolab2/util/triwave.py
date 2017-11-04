# coding=utf-8
'''
.. module:: echolab.util.triwave

 Functions for fitting and correcting the triangle-wave gain structure imposed
 on ES60 data files.
 
     general_triangle:       creates a triangle-wave
     es60_triangle:          generates an ES60-like triangle wave
     fit_es60_triangle:      estimates triangle-wave parameters from ES60 data
     triwave_correct:        eliminates triangle-wave gain offset from ES60 data
     

 | Zac Berkowitz <zachary.berkowitz@noaa.gov>
 | National Oceanic and Atmospheric Administration
 | Alaska Fisheries Science Center
 | Midwater Assesment and Conservation Engineering Group

$Id$
'''

import numpy as np
import logging
#Sfrom scipy import optimize

__all__ = ['general_triangle', 'es60_triangle', 'fit_es60_triangle', 
           'triwave_correct']

log = logging.getLogger(__name__)


def general_triangle(n, A=0.5, M=2721,  k=0, C=0, dtype=None):
    '''
    :param n: sample index
    :type n: array(int)
    
    :param A: Triangle wave amplitude (1/2 peak-to-peak)
    :type A: float
    
    :param M: Triangle wave period in samples
    :type M: int
    
    :param k: Sample offset
    :type k: int
    
    :param C: Amplitude offset
    :type C: float
    
    General triangle-wave function 
    '''
    n_div_M = ((n + k) % M) / float(M)
    triangle =  A*(2*abs(2 * (n_div_M - np.floor(n_div_M + 0.5))) - 1) + C
    
    if dtype is not None:
        return triangle.astype(dtype)
    else:
        return triangle

def es60_triangle(n, k=0, C=0):
    '''
    :param n: sample index
    :type n: array(int)
    
    :param k: sample offset
    :type k: int
    
    :param C: Amplitude Offset
    :type C: float
    
    Generates a triangle wave like those found in ES60/ES70 power values.
    Period = 2721 samples
    Amplitude = 0.5 dB
    '''
    return general_triangle(n, A=0.5, M=2721.0, k=k, C=C)

#def fit_es60_triangle(mean_ringdown_vec):
#    '''
#    :param mean_ringdown_vec:  Array of ping ringdown values.
#    
#    :returns: k, C, R
#    :raises: ValueError if the fit is unsuccessful.
#    
#    Attempts to fit the values in mean_ringdown_vec to the ES60 triangle
#    wave offset.  This function returns the two values, k and C.  k is
#    the sample offset from period origin (where the first ping lies along
#    the triangle period), C is the mean offset of the triangle wave.  R
#    is the "R^2" value of the fit (Coefficient of determination)
#    
#    The fitted triangle wave can be visualized using
#    
#    k, C, R = fit_es60_triangle(mean_ringdown_vec)
#    fitted_tri = es60_triangle(len(mean_ringdown_vec), k, C)
#    
#    plot(mean_ringdown_vec)
#    plot(fitted_tri)
#    '''
#    N = len(mean_ringdown_vec)
#    n = np.arange(N)
#    
#    fit_func = lambda p: general_triangle(n, p[0], p[1])
#    err_func = lambda p: abs(fit_func(p) - mean_ringdown_vec)
#    
#    guess_max = [1360-np.argmax(mean_ringdown_vec), np.mean(mean_ringdown_vec)]
#    guess_min = [2720-np.argmin(mean_ringdown_vec), np.mean(mean_ringdown_vec)]
#
#    fit_results_max = optimize.leastsq(err_func, guess_max[:], full_output=True)
#    fit_results_min = optimize.leastsq(err_func, guess_min[:], full_output=True)
#    
#    fit_params_max, fit_cov, fit_info, fit_msg, fit_success = fit_results_max
#    fit_params_min, fit_cov, fit_info, fit_msg, fit_success = fit_results_min
#
#    SStot = sum((mean_ringdown_vec - mean_ringdown_vec.mean())**2)
#    
#    SSerr_max = sum(err_func(fit_params_max)**2)
#    SSerr_min = sum(err_func(fit_params_min)**2)
#
#    R_max = 1 - SSerr_max/SStot
#    R_min = 1 - SSerr_min/SStot
#
#    if R_max > R_min:
#        k, C = fit_params_max
#        R = R_max
#    else:
#        k, C = fit_params_min
#        R = R_min
#    
#    k = k % 2721
#    
#    if abs(k - 2721) < abs(k):
#        k -= 2721
#    
#    return k, C, R

def fit_triangle(mean_ringdown_vec, amplitude=None, period_offset=None,
                      amplitude_offset=None):
    '''
    :param mean_ringdown_vec:  Array of ping ringdown values.
    
    :returns: k, C, R
    :raises: ValueError if the fit is unsuccessful.
    
    Attempts to fit the values in mean_ringdown_vec to the ES60 triangle
    wave offset.  This function returns the two values, k and C.  k is
    the sample offset from period origin (where the first ping lies along
    the triangle period), C is the mean offset of the triangle wave.  R
    is the "R^2" value of the fit (Coefficient of determination)
    
    The fitted triangle wave can be visualized using
    
    k, C, R = fit_es60_triangle(mean_ringdown_vec)
    fitted_tri = es60_triangle(len(mean_ringdown_vec), k, C)
    
    plot(mean_ringdown_vec)
    plot(fitted_tri)
    '''
    N = len(mean_ringdown_vec)
    n = np.arange(N)
    
    fit_func = lambda p: general_triangle(n, p[0], 2721.0, p[1], p[2])
    err_func = lambda p: (mean_ringdown_vec-fit_func(p))
    
    if period_offset is None:
        period_offset = 1360 - np.argmax(mean_ringdown_vec)
        
    if amplitude is None:
        amplitude = 1.0
        
    if amplitude_offset is None:
        amplitude_offset = np.mean(mean_ringdown_vec)
        
    guess = [amplitude, period_offset, amplitude_offset]
#    guess_max = [1360-np.argmax(mean_ringdown_vec), np.mean(mean_ringdown_vec)]
#    guess_min = [2720-np.argmin(mean_ringdown_vec), np.mean(mean_ringdown_vec)]

    fit_results = optimize.leastsq(err_func, guess[:], full_output=True)
    
    fit_params, fit_cov, fit_info, fit_msg, fit_success = fit_results
    
    SStot = sum((mean_ringdown_vec - mean_ringdown_vec.mean())**2)
    
    SSerr = sum(err_func(fit_params)**2)

    fit_r_squared = 1 - SSerr/SStot
    
    fit_amplitude, fit_period_offset, fit_amplitude_offset = fit_params
    
    fit_period_offset = fit_period_offset % 2721
    
    if abs(fit_period_offset - 2721) < abs(fit_period_offset):
        fit_period_offset -= 2721
    
    if fit_amplitude < 0:
        fit_amplitude = -fit_amplitude

    return dict(period_offset=fit_period_offset,
                amplitude_offset=fit_amplitude_offset,
                amplitude=fit_amplitude,
                r_squared=fit_r_squared)

def fill_gap(bad_indx, vector, max_change):

    
    if bad_indx == 0:
        vector[0] = vector[1] 
    
    elif abs(vector[bad_indx] - vector[bad_indx - 1]) < max_change:
        return
    
    elif bad_indx == len(vector) - 1:
        vector[bad_indx] = vector[bad_indx - 1]
        return
    
    elif abs(vector[bad_indx - 1] - vector[bad_indx + 1]) <= max_change:
        vector[bad_indx] = (vector[bad_indx - 1] + vector[bad_indx + 1]) / 2
        return
    else:
        fill_gap(bad_indx - 1, vector, max_change)

def correct_triwave(data, ringdown_upper_bound=2, num_samples=2,
                    fit_guess=None, stomp_spikes=True, fit_only=False):
    '''
    :param pingset: Raw data set
    :type :class:`echolab.simrad_io.ER60PingSeries`:
    
    :param ringdown_bound:  Lower (deeper) sample index for ringdown volume
    :type ringdown_bound: int
    
    :returns: R-squared values after correction (values are corrected in place)
    :rtype:  [float]
    
    
    Corrects the triangle-wave gain offset present in ES60 data and updates the
    raw data contained in the :class:`echolab.simrad_io.ER60PingSeries` object
    '''
    
    
#    location_of_first_valid_sample_relative_to_reference = data.axes[1]['shift']
    location_of_first_valid_sample_relative_to_array = data.axes[1]['shift'] - data.axes[0][0]['sample']
    
    sample_ub = location_of_first_valid_sample_relative_to_array + \
            ringdown_upper_bound - data.axes[1]['offset']

    sample_lb = sample_ub + num_samples
    
    sample_ub[sample_ub < 0] = 0
    sample_lb[sample_lb < 0] = 0
    
    abs_first_sample = sample_ub.min()
    abs_last_sample  = sample_lb.max()
    
    if abs_first_sample > data.shape[0]:
        raise IndexError('First ringdown sample outside of data bounds')

    mean_ringdown = np.ma.MaskedArray(np.empty(data.shape[1]))
    mean_ringdown[:] = np.ma.masked
    
    data_ma_view = data.view(np.ma.MaskedArray)
    
    for bound in np.unique(sample_ub):
        data_ub = bound
        
        data_lb = data_ub + num_samples
        if data_lb > data.shape[0]:
            data_lb = data.shape[0]
            
        #Skip pings w/ no samples to filter
        if data_lb - data_ub < 1:
            continue
            
        ping_selector = sample_ub == bound
        
        mean_ringdown[ping_selector] = data_ma_view[data_ub:data_lb, ping_selector].mean(axis=0)

    mean_ringdown = mean_ringdown.filled(np.nan)
    
    
    bad_pings = np.isnan(mean_ringdown)
    
#    if data.info['data_type'] in ['Sv', 'Sp', 'power']:
#        data_is_linear = False
#
#    elif data.info['data_type'] in ['sv', 'sp']:
#        data_is_linear = True
#
#    else:
#        #Assume linear type
#        data_is_linear = True
#
#
#    if data_is_linear:
#        amplitude = (10**0.1 - 1)/(10**0.1 + 1) * mean_ringdown[~bad_pings].mean()  
#    else:
#        amplitude = 0.5

    if data.info['data_type'] is not 'power':
        raise ValueError('Triangle-wave correction only works with raw indexed power data.')
    
    #Amplitude:  1dB Pk-to-Pk = ~42.5 in after dividing by simrad's raw power
    #conversion factor = power_db = power_indexed * 10*log10(2) / 256 
    amplitude = 42.5        
    if stomp_spikes:
        bad_pings[np.argwhere(np.diff(mean_ringdown) < -0.15 * amplitude) + 1] = True
        
    if bad_pings.any():
        
#        for bad_indx in np.argwhere(bad_pings).flatten():
#            fill_gap(bad_indx, mean_ringdown, 0.4 * amplitude)
        bad_indxs = np.argwhere(bad_pings)
        mean_ringdown[bad_indxs] = mean_ringdown[bad_indxs - 1]

    if data.shape[1] < 1360:
        if fit_guess is None:
            period_offset = None
            amplitude_offset = None
            amplitude = None
        else:
            period_offset = fit_guess.get('period_offset', None)
            amplitude_offset = fit_guess.get('amplitude_offset', None)
            amplitude = fit_guess.get('amplitude', None)
            
        if period_offset is None:
            log.warning('Short pingset and no supplied guess, attempting to fit anyway..')
    else:
        period_offset = None
        amplitude_offset = None    
    
    fit_results = fit_triangle(mean_ringdown, amplitude=amplitude, 
            period_offset=period_offset, amplitude_offset=amplitude_offset)
    
    if not fit_only:        
        generated_triangle_offset = general_triangle(np.arange(data.shape[1]), A=fit_results['amplitude'],
                    M=2721.0, k = fit_results['period_offset'], C=0, dtype='float32')
             
        if np.prod(data.shape) < 10e6:        
            data[:] = data - np.repeat(np.reshape(generated_triangle_offset, (1, -1)), data.shape[0], axis=0)
        
        else:
            blocksize = int(5e6 / data.shape[0])
            log.debug('Using blocksize of %d to adjust power due to data size of %.2fM samples', blocksize, np.prod(data.shape)/1e6) 
    
            for indx in range(0, data.shape[1], blocksize):
                data[:, indx:indx+blocksize] = data[:, indx:indx+blocksize] -\
                    np.repeat(np.reshape(generated_triangle_offset[indx:indx+blocksize], (1, -1)), data.shape[0], axis=0)
        
    return fit_results
