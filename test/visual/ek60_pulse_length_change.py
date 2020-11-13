# -*- coding: utf-8 -*-
"""
@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and outputs created by Echoview.

This test compares EK80 CW complex data from EK80 WBTs from the Oscar Dyson.
The Oscar Dyson has 6 WBTs each driving 4 sector transducers.


"""
from echolab2.instruments import echosounder
import echolab2.processing.processed_data as processed_data
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt


#  specify the index of the single ping to plot
plot_ping = 0;

in_files = ['../data/EK60_GPT_18(4s-1024us)_38(4s-256us)_70(4s-1024us)_120(4s_1024us)_200(4s-1024us)_1461.4ms_100m_test.raw',
            '../data/EK60_GPT_18(4s-1024us)_38(4s-1024us)_70(4s-1024us)_120(4s_1024us)_200(4s-1024us)_1461.4ms_100m_test.raw',
            '../data/EK60_GPT_18(4s-1024us)_38(4s-4096us)_70(4s-1024us)_120(4s_1024us)_200(4s-1024us)_1461.4ms_100m_test.raw']

ev_Sv_filename = {}
ev_Sv_filename['Echoview Sv - 18 kHz'] = '../data/EK_60_example_multiple_pulse_lengths_Sv_T1.mat'
ev_Sv_filename['Echoview Sv - 38 kHz'] = '../data/EK_60_example_multiple_pulse_lengths_Sv_T2.mat'
ev_Sv_filename['Echoview Sv - 70 kHz'] = '../data/EK_60_example_multiple_pulse_lengths_Sv_T3.mat'
ev_Sv_filename['Echoview Sv - 120 kHz'] = '../data/EK_60_example_multiple_pulse_lengths_Sv_T4.mat'
ev_Sv_filename['Echoview Sv - 200 kHz'] = '../data/EK_60_example_multiple_pulse_lengths_Sv_T5.mat'

ev_Ts_filename = {}
ev_Ts_filename['Echoview TS - 18 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-18kHz.ts.csv'
ev_Ts_filename['Echoview TS - 38 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-38kHz.ts.csv'
ev_Ts_filename['Echoview TS - 70 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-70kHz.ts.csv'
ev_Ts_filename['Echoview TS - 120 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-120kHz.ts.csv'
ev_Ts_filename['Echoview TS - 200 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-200kHz.ts.csv'

ev_power_filename = {}
ev_power_filename['Echoview power - 18 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-18kHz.power.csv'
ev_power_filename['Echoview power - 38 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-38kHz.power.csv'
ev_power_filename['Echoview power - 70 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-70kHz.power.csv'
ev_power_filename['Echoview power - 120 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-120kHz.power.csv'
ev_power_filename['Echoview power - 200 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-200kHz.power.csv'

ev_angles_filename = {}
ev_power_filename['Echoview power - 18 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-18kHz.angles.csv'
ev_power_filename['Echoview power - 38 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-38kHz.angles.csv'
ev_power_filename['Echoview power - 70 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-70kHz.angles.csv'
ev_power_filename['Echoview power - 120 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-120kHz.angles.csv'
ev_power_filename['Echoview power - 200 kHz'] = 'DY2000_EK80_Cal-D20200126-T060729-200kHz.angles.csv'


#  read in the .raw data file
print()
print('Reading raw files...')
raw_data_types = echosounder.read(in_files)

# echosounder.read returns a list of data objects. The list will
# contain an EK80 object if any of the files read were in EK80
# format and/or an EK60 object if any of the files read were recorded
# using the ER60 application with EK60 GPTs.

# We are only reading a single type so we'll grab the first reference
ekX0 = raw_data_types[0]


#  now iterate through the echoview reference files and display results
for idx, sv_chan in enumerate(ev_Sv_filename):

    #  get the list of raw_data objects by channel - I know
    #  in this case the channels are ordered from low to high
    #  frequency. This may not always be the case.
    raw_list = ekX0.raw_data[ekX0.channel_ids[idx]]

    #  I also know that for the purposes of these comparisons, I am
    #  only reading a single data type so I can assume there will be
    #  only 1 raw_data object in the list and it will be at index 0.
    raw_data = raw_list[0]

    #  get a cal object populated with params from the raw_data object.
    #  the calibration object stores the data from the EK80 configuration
    #  datagram as well as some computed values and provides a simple
    #  interface to get and set these values and ultimately deliver right
    #  sized arrays to methods that convert the complex or power/angle
    #  data into "processed" data.
    calibration = raw_data.get_calibration()

    #  convert to power
    ek_power = raw_data.get_power(calibration=calibration)

    #  convert to Sv
    ek_Sv = raw_data.get_Sv(calibration=calibration)

    #  and convert to Ts
    ek_Ts = raw_data.get_Sp(calibration=calibration)


    #  read in the echoview data - we can read .mat and .csv files exported
    #  from EV 7+ directly into a processed_data object
    frequency = raw_data.frequency[0]
    key_name = sv_chan
    ev_filename = ev_Sv_filename[key_name]
    print('Reading the echoview file %s' % (ev_Sv_filename[key_name]))
    ev_Sv_data = processed_data.read_ev_mat(key_name, frequency, ev_filename, pad_n_samples=1)
#    key_name = list(ev_Ts_filename.keys())[idx]
#    ev_filename = input_path + ev_Ts_filename[key_name]
#    print('Reading the echoview file %s' % (ev_Ts_filename[key_name]))
#    ev_Ts_data = processed_data.read_ev_csv(key_name, frequency, ev_filename)
#    key_name = list(ev_power_filename.keys())[idx]
#    ev_filename = input_path + ev_power_filename[key_name]
#    print('Reading the echoview file %s' % (ev_power_filename[key_name]))
#    ev_power_data = processed_data.read_ev_csv(key_name, frequency, ev_filename,
#            data_type='Power')


    #  now plot all of this up

    #  show the Echolab Sv and TS echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek_Sv, threshold=[-70,-34])
    eg.axes.set_title("Echolab2 Sv " + str(frequency) + " kHz")
    #fig = plt.figure()
    #eg = echogram.Echogram(fig, ek80_Ts, threshold=[-70,-34])
    #eg.axes.set_title("Echolab2 Ts " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab Sv data
    diff = ek_Sv - ev_Sv_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
    eg.axes.set_title("Echolog Sv - EV Sv " + str(frequency) + " kHz")

#    #  compute the difference of EV and Echolab TS data
#    diff = ek80_Ts - ev_Ts_data
#    fig = plt.figure()
#    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
#    eg.axes.set_title("Echolog TS - EV TS " + str(frequency) + " kHz")
#
#    #  compute the difference of EV and Echolab power data
#    diff = ek80_power - ev_power_data
#    fig = plt.figure()
#    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
#    eg.axes.set_title("Echolog power - EV power " + str(frequency) + " kHz")

    #  plot up a single power ping
    fig2 = plt.figure()
    plt.plot(ev_Sv_data[plot_ping], ev_Sv_data.range, label='Echoview', color='blue', linewidth=1.5)
    plt.plot(ek_Sv[plot_ping], ek_Sv.range, label='Echolab', color='red', linewidth=1)
    plt.gca().invert_yaxis()
    fig2.suptitle("Ping " + str(plot_ping) + " comparison EV vs Echolab")
    plt.xlabel("power (dB)")
    plt.ylabel("Range (m)")
    plt.legend()

    # Show our figures.
    plt.show()

    print()
