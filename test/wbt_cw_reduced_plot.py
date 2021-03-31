# -*- coding: utf-8 -*-
"""
@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and outputs created by Echoview.

The original data file is from a 5 WBT system configured with 18, 38, 70, 120,
and 200 kHz as CW. Data was recorded in "reduced" form (power/angle). This data
file has been modified and only contains the first 50 pings. Data are recorded
to ~350m.

EK80 Software version: 1.12.4.0
Raw file format version: 1.22


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
in_file = './data/EK80_WBT_CW_reduced_test.raw'

# Echoview power, Sv, TS, and angles data exports of above raw file
ev_Sv_filename = {}
ev_Sv_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.Sv.mat'
ev_Sv_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.Sv.mat'
ev_Sv_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.Sv.mat'
ev_Sv_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.Sv.mat'
ev_Sv_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.Sv.mat'
ev_Sv_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.Sv.mat'

ev_TS_filename = {}
ev_TS_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.ts.csv'
ev_TS_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.ts.csv'
ev_TS_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.ts.csv'
ev_TS_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.ts.csv'
ev_TS_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.ts.csv'
ev_TS_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.ts.csv'

ev_power_filename = {}
ev_power_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.power.csv'
ev_power_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.power.csv'
ev_power_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.power.csv'
ev_power_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.power.csv'
ev_power_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.power.csv'
ev_power_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.power.csv'

ev_angles_filename = {}
ev_angles_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.angles.csv'
ev_angles_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.angles.csv'
ev_angles_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.angles.csv'
ev_angles_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.angles.csv'
ev_angles_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.angles.csv'
ev_angles_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.angles.csv'


#  read in the .raw data file
print('Reading the raw file %s' % (in_file))
ek80 = EK80.EK80()
ek80.read_raw(in_file)

#  now iterate through the reference files and display results
for idx, frequency in enumerate(ev_Sv_filename):

    #  get the list of raw_data objects by channel - I know
    #  in this case the channels are ordered from low to high
    #  frequency. I don't think you can always assume that but
    #  in this case it is OK.
    raw_list = ek80.raw_data[ek80.channel_ids[idx]]

    #  I also know that for the purposes of these comparisons, I am
    #  only reading a single data type so I can assume there will be
    #  only 1 raw_data object in the list and it will be at index 0.
    raw_data = raw_list[0]

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
    ek80_power = raw_data.get_power(calibration=calibration)#, clear_cache=False)

    #  convert to Sv
    ek80_Sv = raw_data.get_Sv(calibration=calibration)#, clear_cache=False)

    #  and convert to Ts
    ek80_Ts = raw_data.get_Sp(calibration=calibration)#, clear_cache=False)

    # Get the angle data
    alongship, athwartship = raw_data.get_physical_angles(calibration=calibration)


    #  read in the echoview data - we can read .mat and .csv files exported
    #  from EV 7+ directly into a processed_data object
    ev_filename = ev_Sv_filename[frequency]
    print('Reading the echoview file %s' % (ev_Sv_filename[frequency]))
    ev_Sv_data = processed_data.read_ev_mat('', frequency, ev_filename,
            data_type='Sv')

    ev_filename = ev_TS_filename[frequency]
    print('Reading the echoview file %s' % (ev_TS_filename[frequency]))
    ev_Ts_data = processed_data.read_ev_csv('', frequency, ev_filename,
            data_type='Ts')

    ev_filename = ev_power_filename[frequency]
    print('Reading the echoview file %s' % (ev_power_filename[frequency]))
    ev_power_data = processed_data.read_ev_csv('', frequency, ev_filename,
            data_type='Power')

    ev_filename = ev_angles_filename[frequency]
    print('Reading the echoview file %s' % (ev_angles_filename[frequency]))
    ev_alongship, ev_athwartship = processed_data.read_ev_csv('', frequency,
            ev_filename, data_type='angles')


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
    eg.axes.set_title("Echolog2 Sv - EV Sv " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab TS data
    diff = ek80_Ts - ev_Ts_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolog2 TS - EV TS " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab TS data
    diff = ek80_power - ev_power_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig)
    eg.axes.set_title("Echolog2 power - EV power " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab alongship angles
    diff = alongship - ev_alongship
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig, units='deg')
    eg.axes.set_title("Echolog2 alongship - EV alongship " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab athwartship angles
    diff = athwartship - ev_athwartship
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=diff_threshold, cmap=diff_cmap)
    eg.add_colorbar(fig, units='deg')
    eg.axes.set_title("Echolog2 athwartship - EV athwartship " + str(frequency) + " kHz")

    #  plot up a single Sv ping
    fig2 = plt.figure()
    plt.plot(ev_Sv_data[-1], ev_Sv_data.range, label='Echoview', color='blue', linewidth=1.5)
    plt.plot( ek80_Sv[-1], ek80_Sv.range, label='Echolab2', color='red', linewidth=1)
    plt.gca().invert_yaxis()
    fig2.suptitle("Ping " + str(ev_Sv_data.n_pings) + " comparison EV vs Echolab2")
    plt.xlabel("Sv (dB)")
    plt.ylabel("Range (m)")
    plt.legend()

    # Show our figures.
    plt.show()

