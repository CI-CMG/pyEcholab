# -*- coding: utf-8 -*-
"""
@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and outputs created by Echoview.

This test compares EK80 FM Complex data from EK80 WBTs from the Oscar Dyson with
pulse compressed output from EV.


"""

from echolab2.instruments import EK80
import echolab2.processing.processed_data as processed_data
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt


plot_ping = 0;

input_path = 'C:/EK80 Test Data/'

#  define the paths to the reference data files
raw_filename = 'D20180303-T093354.raw'

ev_Sv_filename = {}
ev_Sv_filename['Echoview Sv - Channel 1'] = 'D20180303-T093354-1.mat'
ev_Sv_filename['Echoview Sv - Channel 2'] = 'D20180303-T093354-2.mat'

ev_Ts_filename = {}
ev_Ts_filename['Echoview TS - Channel 1'] = 'D20180303-T093354-1.ts.csv'
ev_Ts_filename['Echoview TS - Channel 2'] = 'D20180303-T093354-2.ts.csv'

ev_power_filename = {}
ev_power_filename['Echoview power - Channel 1'] = 'D20180303-T093354-1.power.csv'
ev_power_filename['Echoview power - Channel 2'] = 'D20180303-T093354-2.power.csv'


#  read in the .raw data file
print('Reading the raw file %s' % (raw_filename))
ek80 = EK80.EK80()
ek80.read_raw(input_path + raw_filename)

#  now iterate through the reference files and display results
for idx, sv_chan in enumerate(ev_Sv_filename):

    #  Get a list of raw data objects for this channel
    raw_list = ek80.raw_data[ek80.channel_ids[idx]]
    #  Assume a single data type
    raw_data = raw_list[0]

    #  get a cal object
    calibration = raw_data.get_calibration()

    #  convert to power
    ek80_power = raw_data.get_power(calibration=calibration)

    #  convert to Sv
    ek80_Sv = raw_data.get_Sv(calibration=calibration)

    #  and convert to Ts
    ek80_Ts = raw_data.get_Sp(calibration=calibration)


    #  read in the echoview data - we can read .mat and .csv files exported
    #  from EV 7+ directly into a processed_data object
    f_start = raw_data.frequency_start[0]
    f_end = raw_data.frequency_end[0]
    frequency = (f_start + f_end) / 2
    key_name = sv_chan
    ev_filename = input_path + ev_Sv_filename[key_name]
    print('Reading the echoview file %s' % (ev_Sv_filename[key_name]))
    ev_Sv_data = processed_data.read_ev_mat(key_name, frequency, ev_filename)
    key_name = list(ev_Ts_filename.keys())[idx]
    ev_filename = input_path + ev_Ts_filename[key_name]
    print('Reading the echoview file %s' % (ev_Ts_filename[key_name]))
    ev_Ts_data = processed_data.read_ev_csv(key_name, frequency, ev_filename)
    key_name = list(ev_power_filename.keys())[idx]
    ev_filename = input_path + ev_power_filename[key_name]
    print('Reading the echoview file %s' % (ev_power_filename[key_name]))
    ev_power_data = processed_data.read_ev_csv(key_name, frequency, ev_filename,
            data_type='Power')


    #  now plot all of this up
    f_string = "%d - %d" % (f_start / 1000, f_end / 1000)

    #  show the Echolab Sv and TS echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Sv, threshold=[-70,-34])
    eg.axes.set_title("Echolab2 Sv " + f_string + " kHz")
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Ts, threshold=[-70,-34])
    eg.axes.set_title("Echolab2 Ts " + f_string + " kHz")

    #  compute the difference of EV and Echolab Sv data
    diff = ek80_Sv - ev_Sv_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
    eg.axes.set_title("Echolog Sv - EV Sv " + f_string + " kHz")

    #  compute the difference of EV and Echolab TS data
    diff = ek80_Ts - ev_Ts_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
    eg.axes.set_title("Echolog TS - EV TS " + f_string + " kHz")

    #  compute the difference of EV and Echolab power data
    diff = ek80_power - ev_power_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
    eg.axes.set_title("Echolog power - EV power " + f_string + " kHz")

    #  plot up a single Sv ping
    fig2 = plt.figure()
    plt.plot(ev_power_data[plot_ping], ev_power_data.range, label='Echoview', color='blue', linewidth=1.5)
    plt.plot(ek80_power[plot_ping], ek80_power.range, label='Echolab', color='red', linewidth=1)
    plt.gca().invert_yaxis()
    fig2.suptitle("Ping " + str(plot_ping) + " comparison EV vs Echolab")
    plt.xlabel("power (dB)")
    plt.ylabel("Range (m)")
    plt.legend()

    # Show our figures.
    plt.show()

    print()
