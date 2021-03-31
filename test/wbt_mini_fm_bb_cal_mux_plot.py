# -*- coding: utf-8 -*-
"""
@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and outputs created by Echoview.

These data were collected using a WBT-Mini configured to multiplex 2 channels


EK80 Software version: 1.11.1.0
Raw file format version: 1.20


"""

from echolab2.instruments import EK80
import echolab2.processing.processed_data as processed_data
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt


#  specify the difference echogram's threshold.
diff_threshold = [-0.1, 0.1]

#  specify the color table used for the difference echograms
#  The matplotlib diverging maps are best here:
#  https://matplotlib.org/stable/tutorials/colors/colormaps.html#diverging
diff_cmap='PuOr'

# Specify the input raw file
in_file = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test.raw'

# Echoview power, Sv, TS, and angles data exports of above raw file
ev_Sv_filename = {}
ev_Sv_filename['WBT Mini 253624-15-1 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_1_pc.Sv.mat'
ev_Sv_filename['WBT Mini 253624-15-2 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_2_pc.Sv.mat'

ev_TS_filename = {}
ev_TS_filename['WBT Mini 253624-15-1 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_1_pc.ts.csv'
ev_TS_filename['WBT Mini 253624-15-2 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_2_pc.ts.csv'

ev_power_filename = {}
ev_power_filename['WBT Mini 253624-15-1 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_1_pc.power.csv'
ev_power_filename['WBT Mini 253624-15-2 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_2_pc.power.csv'

ev_angles_filename = {}
ev_angles_filename['WBT Mini 253624-15-1 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_1_pc.angles.csv'
ev_angles_filename['WBT Mini 253624-15-2 ES70-7CD'] = './data/EK80_WBTmini_FM_bb-cal_67-90(4)_mux_test_EV_2_pc.angles.csv'



#  read in the .raw data file
print('Reading the raw file %s' % (in_file))
ek80 = EK80.EK80()
ek80.read_raw(in_file)

#  now iterate through the reference files and display results
for idx, chan_id in enumerate(ev_Sv_filename):

    #  get the list of raw_data objects by channel
    raw_list = ek80.raw_data[chan_id]

    #  I also know that for the purposes of these comparisons, I am
    #  only reading a single data type so I can assume there will be
    #  only 1 raw_data object in the list and it will be at index 0.
    raw_data = raw_list[0]

    #  get the tx center frequency
    frequency = raw_data.get_frequency(unique=True)[0]

    #  The calibration object provides all of the parameters required to
    #  convert raw data to the various processed forms. Here we will get
    #  a cal object that is populated with parameters from the .raw data
    #  file. While you don't *have* to pass a calibration object to the
    #  conversion methods, it is most efficient to get a cal object from
    #  your raw_data, modify values as needed, and then pass that to your
    #  conversion method(s).
    calibration = raw_data.get_calibration()

    #  Convert the raw data. Some computed conversion parameters are cached
    #  in the calibration object during conversion. Normally they are
    #  discarded at the end of the conversion process but since we will
    #  be calling multiple conversion methods below, we'll set the clear_cache
    #  keyword to False to keep that data. By keeping it, the next method
    #  called doesn't need to recompute it.

    #  convert to power
    ek80_power = raw_data.get_power(calibration=calibration, clear_cache=False)

    #  convert to Sv
    ek80_Sv = raw_data.get_Sv(calibration=calibration, clear_cache=False)

    #  and convert to Ts
    ek80_Ts = raw_data.get_Sp(calibration=calibration, clear_cache=False)

    # Try to get the angle data (not all tests have angle data)
    try:
        alongship, athwartship = raw_data.get_physical_angles(calibration=calibration)
    except:
        alongship, athwartship = (None, None)


    #  read in the echoview data - we can read .mat and .csv files exported
    #  from EV 7+ directly into a processed_data object
    ev_filename = ev_Sv_filename[chan_id]
    print('Reading the echoview file %s' % (ev_Sv_filename[chan_id]))
    ev_Sv_data = processed_data.read_ev_mat('', frequency, ev_filename,
            data_type='Sv')

    ev_filename = ev_TS_filename[chan_id]
    print('Reading the echoview file %s' % (ev_TS_filename[chan_id]))
    ev_Ts_data = processed_data.read_ev_csv('', frequency, ev_filename,
            data_type='Ts')

    ev_filename = ev_power_filename[chan_id]
    print('Reading the echoview file %s' % (ev_power_filename[chan_id]))
    ev_power_data = processed_data.read_ev_csv('', frequency, ev_filename,
            data_type='Power')

    # Try to read the EV angle data (not all tests have angle data)
    try:
        ev_filename = ev_angles_filename[chan_id]
        print('Reading the echoview file %s' % (ev_angles_filename[chan_id]))
        ev_alongship, ev_athwartship = processed_data.read_ev_csv('', frequency,
                ev_filename, data_type='angles')
    except:
        ev_alongship, ev_athwartship = (None, None)


    #  now plot all of this up

    #  show the Echolab Sv and TS echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Sv, threshold=[-70,-34])
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 Sv " + str(frequency) + " kHz")
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Ts, threshold=[-70,-34])
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolab2 Ts " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab Sv data
    diff = ek80_Sv - ev_Sv_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolog Sv - EV Sv " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab TS data
    diff = ek80_Ts - ev_Ts_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolog TS - EV TS " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab TS data
    diff = ek80_power - ev_power_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolog power - EV power " + str(frequency) + " kHz")

    if alongship:
        #  compute the difference of EV and Echolab alongship angles
        diff = alongship - ev_alongship
        fig = plt.figure()
        eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
        eg.add_colorbar(fig, units='deg')
        eg.axes.set_title("Echolog alongship - EV alongship " + str(frequency) + " kHz")

        #  compute the difference of EV and Echolab athwartship angles
        diff = athwartship - ev_athwartship
        fig = plt.figure()
        eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
        eg.add_colorbar(fig, units='deg')
        eg.axes.set_title("Echolog athwartship - EV athwartship " + str(frequency) + " kHz")

    #  plot up a single Sv ping
    fig2 = plt.figure()
    plt.plot(ev_Sv_data[-1], ev_Sv_data.range, label='Echoview', color='blue', linewidth=1.5)
    plt.plot( ek80_Sv[-1], ek80_Sv.range, label='Echolab', color='red', linewidth=1)
    plt.gca().invert_yaxis()
    fig2.suptitle("Ping " + str(ev_Sv_data.n_pings) + " comparison EV vs Echolab")
    plt.xlabel("Sv (dB)")
    plt.ylabel("Range (m)")
    plt.legend()

    # Show our figures.
    plt.show()

