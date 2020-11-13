# -*- coding: utf-8 -*-
"""

resampling test

"""

from echolab2.instruments import echosounder
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt

# EK80 CW-complex files
files = ['C:/EK80 Test Data/Saildrone/range_change/SD_alaska_2020_SD1043-Phase0-D20200810-T195959-0.raw',
         'C:/EK80 Test Data/Saildrone/range_change/SD_alaska_2020_SD1043-Phase0-D20200810-T205959-0.raw']

# EK60
#files = ['C:/Users/rick.towler/Work/AFSCGit/pyEcholab/examples/data/EK60/DY1201_EK60-D20120214-T231011.raw',
#         'C:/Users/rick.towler/Work/AFSCGit/pyEcholab/examples/data/EK60/DY1706_EK60-D20170609-T005736.raw']


# use echosounder.read() to read the file, regardless of type, and return
# an instrument object. Since we will make sure that our input files will
# always be from the same instrument (all EK60 or all EK80) we can assume
# echosounder.read() will return a list with a single instrument object
# which contains the data from the files in our list above.
instrumet_ojbs = echosounder.read(files)
data_obj = instrumet_ojbs[0]
print(data_obj)

chan_data = data_obj.get_channel_data()
for channel_id in chan_data:

    raw_data = chan_data[channel_id][0]
    calibration=raw_data.get_calibration()
    Sv = raw_data.get_Sv(calibration=calibration , resample_interval=1)
    freq = raw_data.frequency[0]

    #  show the Sv echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, Sv, threshold=[-70,-34])
    eg.axes.set_title("EK80 Sv " + str(freq) + " kHz")

#    #  compute the difference
#    diff = orig_Sv - rewrite_Sv
#    fig = plt.figure()
#    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
#    eg.axes.set_title("Original Sv - Reqrite Sv " + str(orig_freq) + " kHz")

#    #  plot up a single Sv ping
#    fig2 = plt.figure()
#    plt.plot(Sv[-2], Sv.range, label='Original', color='blue', linewidth=1.5)
#    plt.gca().invert_yaxis()
#    plt.xlabel("Sv (dB)")
#    plt.ylabel("Range (m)")
#    plt.legend()

    # Show our figures.
    plt.show()

print()
