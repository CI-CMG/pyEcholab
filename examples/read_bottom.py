# -*- coding: utf-8 -*-
"""
read_bottom is an echolab2 example demonstrating how to read
raw and bot/out files and plot the data.
"""

from matplotlib.pyplot import figure, show
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram

#############################################################
##
##  A lot of testing needs to be done in regards to
##  plotting bottom detections on echograms.
##
##  This code is quite fresh and it appears to me that the
##  horizontal axes doesn't totally line up. The issue is with
##  the plotting. Using matplotlib imshow you don't specify the
##  X,Y locations of the samples but instead provide a start and
##  end value and handles the rest. Need to look into this more\
##  closely.
##
#############################################################

#  create a list of .raw files
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw']
#  and a list of .bot files
botfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.bot']

#  create an instance of ER60
ek60 = EK60.EK60()

#  read the .raw files
print('reading raw files...')
ek60.read_raw(rawfiles, frequencies=[38000,120000])

#  read the .bot files
print('reading bot files...')
ek60.read_bot(botfiles)

#  get a reference to the raw_data object
raw_data_38 = ek60.get_raw_data(channel_number=1)
raw_data_120 = ek60.get_raw_data(channel_number=2)

#  get Sv
Sv_38_as_depth = raw_data_38.get_Sv(heave_correct=True)
Sv_120_as_depth = raw_data_120.get_Sv(heave_correct=True)

#  get the sounder detected bottom data - The astute observer
#  would wonder why we're applying heave correction to the
#  sounder detected bottom since you shouldn't do this (you
#  only correct the underlying sample data which defines the axes.)
#  We have chosen to allow the heave_correct keyword in this context
#  to maintain a consistent interface with the get_* methods. When
#  set, no heave correction is applied but it ensures that get_bottom
#  returns *depth*. You could achieve the same thing by setting
#  the return_depth keyword to true.
bottom_38 = raw_data_38.get_bottom(heave_correct=True)
bottom_120 = raw_data_120.get_bottom(heave_correct=True)

#  and display the results
fig_38 = figure()
eg = echogram.echogram(fig_38, Sv_38_as_depth, threshold=[-70,-34])
eg.axes.set_title("Heave Corrected with Detected Bottom - 38kHz")
eg.plot_line(bottom_38, linewidth=2.5)

fig_120 = figure()
eg = echogram.echogram(fig_120, Sv_120_as_depth, threshold=[-70,-34])
eg.axes.set_title("Heave Corrected with Detected Bottom - 120kHz")
eg.plot_line(bottom_120, linewidth=2.5)

show()


#  now read ES60 data with .out files. There is usually not a 1-1
#  relationship between ,out and .raw files so you have to use the
#  file name to determine which .raw files are associated with
#  and out file.

#  create a list of .raw files
rawfiles = ['./data/ES60/L0226-D20170624-T143908-ES60.raw',
            './data/ES60/L0226-D20170624-T155849-ES60.raw']
#  and a list of .out files
botfiles = ['./data/ES60/L0226-D20170624-T143908-ES60.out']

#  create an instance of ER60
ek60 = EK60.EK60()

#  read the .raw files
print('reading raw files...')
ek60.read_raw(rawfiles)

#  read the .bot files
print('reading out files...')
ek60.read_bot(botfiles)

#  get a reference to the raw_data object
raw_data_38 = ek60.get_raw_data(channel_number=1)

#  get Sv as range
Sv_38_as_range = raw_data_38.get_Sv()
#  get bottom as range
bottom_38 = raw_data_38.get_bottom()

#  and display the results
fig_1 = figure()
eg = echogram.echogram(fig_1, Sv_38_as_range, threshold=[-70,-34])
eg.axes.set_title("Bottom as range - 38kHz")
eg.plot_line(bottom_38, linewidth=2.5)

#  now get Sv as depth
Sv_38_as_depth = raw_data_38.get_Sv(return_depth=True)
#  and bottom as depth
bottom_38 = raw_data_38.get_bottom(return_depth=True)

#  and display the results - use a processed_data.view to zoom
#  into the upper part of the water column.
fig_2 = figure()
Sv_38_view = Sv_38_as_depth.view((None,None,None),(0,500,None))
eg = echogram.echogram(fig_2, Sv_38_view, threshold=[-70,-34])
eg.axes.set_title("Bottom as depth - 38kHz")
eg.plot_line(bottom_38, linewidth=2.5)
show()
