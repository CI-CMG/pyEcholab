# -*- coding: utf-8 -*-
"""

@author: rick.towler

1m_exclusion_integration_check

This script compares the integration output from Echoview with the integration
results computed by pyEcholab.

The reference data was created using Echoview 5.4, ringdown(1.5m)_exclusion.ev,
and test_data.raw and results for each channel were exported to csv. I added a
1.5m exclude above line to exclude the "ringdown" samples because the first 7
samples differ between Echoview and pyEcholab resulting in differences between
them when integrating.

THIS SCRIPT IS A WORK IN PROGRESS AND IS NOT COMPLETE

"""

import echolab
from matplotlib import pyplot as plt
import hashlib
import pandas
import logging


#  set up logging - used to give feedback from the ecolab package
logging.basicConfig(level=logging.DEBUG)


raw_filename = ['./test/data/test_data.raw',
                './test/data/test_data.raw.md5']

channels = [38000,120000]
reference_input = [['./test/data/ringdown(1.5m)_exclusion-38kHz.csv',
                    './test/data/ringdown(1.5m)_exclusion-38kHz.csv.md5'],
                   ['./test/data/ringdown(1.5m)_exclusion-120kHz.csv',
                    './test/data/ringdown(1.5m)_exclusion-120kHz.csv.md5']]


def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "r+b") as f:
        for block in iter(lambda: f.read(blocksize), ""):
            hash.update(block)
    return hash.hexdigest()


if __name__ == "__main__":

    #  check the reference input file checksums
    print('verifying files...')
    for i in range(2):
        print('Verifying checksum for %s' % (reference_input[i][1]))
        calc_cksum = md5sum(reference_input[i][0])

        with open(reference_input[i][1]) as f:
            ref_cksum = f.readlines()
        if (ref_cksum[0] == calc_cksum):
            print('Checksum is OK')
        else:
            raise IOError('Checksums do not match!')


    #  check the
    print('Verifying checksum for %s' % (raw_filename[0]))
    calc_cksum = md5sum(raw_filename[0])

    with open(raw_filename[1]) as f:
        ref_cksum = f.readlines()
    if (ref_cksum[0] == calc_cksum):
        print('Checksum is OK')
    else:
        raise IOError('Raw file checksum does not match!')

    #  read the echoview results into dataframes
    print('Reading Echoview output')
    ev_results_38kHz = pandas.io.parsers.read_csv(reference_input[0][0],
                            index_col=[1,2], skipinitialspace=True)
    ev_results_120kHz= pandas.io.parsers.read_csv(reference_input[1][0],
                            index_col=[1,2],skipinitialspace=True)

    #  combine echoview results into one dataframe -
    ev_results = pandas.concat([ev_results_38kHz,ev_results_120kHz], axis=1,
                               keys=[38000,120000])

    #  read in the .raw data file
    print('Reading the raw file %s' % (raw_filename[0]))
    raw_data = echolab._io.raw_reader.RawReader(raw_filename[0]) #,

    #  calculate inter-ping distances using GPS data or VLW NMEA datagrams
    print('interpolating distance...')
    raw_data.interpolate_ping_dist(ignore_checksum=True)

    #  Set the calibration parameters by using the values from the raw file
    raw_data.calibration_params = raw_data.fill_default_transceiver_calibration()

    #  calculate sv
    print('calculating sv...')
    raw_data.Sv(linear=True)

    #  define the integration grid.
    print('creating integration grid...')
    int_grid_parms = echolab.grid.GridParameters(layer_spacing=10, layer_unit='range',
                     interval_spacing=0.5, interval_unit='distance')

    #  create a mask objec
    print('creating mask...')
    mask = echolab.mask.EchogramMask()

    #  create the 1m exclude above sub mask
    mask.mask_above_range(name='exclude_above', reference=1.5)


    for chan in channels:

        #  get a AxisArray object containing the linear SV data.
        linear_sv = raw_data.to_array('sv', channel=channels.index(chan)+1)

        #  create a grid by calling the grid method of the GridParameters object.
        #  You can re-use a grid for different channels but I'm recreating it here
        #  because it's just easier.
        integration_grid = int_grid_parms.grid(linear_sv)

        #  integrate. By not specifing the max threshold it is not applied.
        #  Echoview was set to apply a min threshold at -70 and not apply a max threshold.
        print('integrating %i kHz...' % (chan / 1000))
        int_results, mask_results = echolab.integration.integrate_single_beam_Sv(data=linear_sv,
                                    grid=integration_grid, mask=mask, min_threshold=-70,
                                    log_thresholds=True)

        int_results.to_csv('test_%i.csv' % (chan / 1000))
        fig = plt.figure()
        for i in range(1,5):
            print('    pyEcholab interval %i start ping %i end ping %i total pings %i' % (i,
                        int_results['ping_start'][i][1],int_results['ping_end'][i][1],
                        int_results['ping_end'][i][1]-int_results['ping_start'][i][1]))
            print('    Echoview interval %i start ping %i end ping %i total pings %i' % (i,
                        ev_results[chan]['Ping_S'][i][1],ev_results[chan]['Ping_E'][i][1],
                        ev_results[chan]['Ping_E'][i][1]-ev_results[chan]['Ping_S'][i][1]))

            ev_data = ev_results[chan]['Sv_mean'][i][:]
            ev_data[ev_data < -998] = 0
            sv_mean_difference = ev_data - int_results['Sv_mean'][i][:]
            nasc_difference = ev_results[chan]['NASC'][i][:] - int_results['nasc'][i][:]
            pct_nasc_difference = (1 - (ev_results[chan]['NASC'][i][:] / int_results['nasc'][i][:])) * 100
            print('  %i kHz Mean Sv difference min %4.6f max %4.6f' % (chan / 1000, sv_mean_difference.min(), sv_mean_difference.max()))
            print('  %i kHz NASC difference min %10.4f max %10.4f' % (chan / 1000, nasc_difference.min(), nasc_difference.max()))

            plt.plot(pct_nasc_difference)

        plt.show(block=True)

