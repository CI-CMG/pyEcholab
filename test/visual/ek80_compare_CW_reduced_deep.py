# -*- coding: utf-8 -*-
"""
@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and data exported from echoview. If everything is working correctly, the
difference plots should be green

"""


from echolab2.instruments import EK80
import echolab2.processing.processed_data as processed_data
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt


input_path = './data/EK80/CW/survey/'

#  define the paths to the reference data files
raw_filename = 'DY2002_EK80-D20200220-T070830.raw'

ev_Sv_filename = {}
ev_Sv_filename['Echoview Sv - 18 kHz'] = 'DY2002_EK80-D20200220-T070830-18 kHz-Sv.mat'
ev_Sv_filename['Echoview Sv - 38 kHz'] = 'DY2002_EK80-D20200220-T070830-38 kHz-Sv.mat'
ev_Sv_filename['Echoview Sv - 70 kHz'] = 'DY2002_EK80-D20200220-T070830-70 kHz-Sv.mat'
ev_Sv_filename['Echoview Sv - 120 kHz'] = 'DY2002_EK80-D20200220-T070830-120 kHz-Sv.mat'
ev_Sv_filename['Echoview Sv - 200 kHz'] = 'DY2002_EK80-D20200220-T070830-200 kHz-Sv.mat'


#  read in the .raw data file
print('Reading the raw file %s' % (raw_filename))
ek80 = EK80.EK80()
ek80.read_raw(input_path + raw_filename)

#  now iterate through the reference files and display results

for idx, sv_chan in enumerate(ev_Sv_filename):

    #  get the list of raw_data objects by channel - I know
    #  in this case the channels are ordered from low to high
    #  frequency. I don't think you can always assume that but
    #  in this case it is OK.
    raw_list = ek80.raw_data[ek80.channel_ids[idx]]
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

    #  convert to Sv
    ek80_Sv = raw_data.get_Sv(calibration=calibration)


    #  read in the echoview data - we can read .mat and .csv files exported
    #  from EV 7+ directly into a processed_data object
    frequency = raw_data.frequency[0]
    key_name = sv_chan
    ev_filename = input_path + ev_Sv_filename[key_name]
    print('Reading the echoview file %s' % (ev_Sv_filename[key_name]))
    ev_Sv_data = processed_data.read_ev_mat(key_name, frequency, ev_filename)


    #  now plot all of this up

    #  show the Echolab Sv and TS echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, ek80_Sv, threshold=[-70,-34])
    eg.axes.set_title("Echolab2 Sv " + str(frequency) + " kHz")

    #  compute the difference of EV and Echolab Sv data
    diff = ek80_Sv - ev_Sv_data
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
    eg.axes.set_title("Echolog Sv - EV Sv " + str(frequency) + " kHz")

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

