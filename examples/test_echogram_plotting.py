# -*- coding: utf-8 -*-
"""
THIS IS A WORK IN PROGRESS - IT DOES NOT RUN AT ALL!!!
"""
import numpy as np
from matplotlib.pyplot import figure, show
from echolab2.processing import processed_data
from echolab2.plotting.matplotlib import echogram


test_data_pings = 100
test_data_samples = 1000

#  create a list of .raw files
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw']

#  create an instance of ER60
ek60 = EK60.EK60()

#  read the .raw files
print('reading raw files...')
ek60.read_raw(rawfiles, frequencies=[38000])

#  get a reference to the raw_data object
raw_data_38 = ek60.get_raw_data(channel_number=1)

#  get Sv
Sv_38 = raw_data_38.get_Sv()



##  now get Sv as depth
#Sv_38_as_depth = raw_data_38.get_Sv(return_depth=True)
##  and bottom as depth
#bottom_38 = raw_data_38.get_bottom(return_depth=True)
#print(Sv_38_as_depth)
#print(bottom_38)
#
##  and display the results - use a processed_data.view to zoom
##  into the upper part of the water column.
#fig_2 = figure()
#Sv_38_view = Sv_38_as_depth.view((None,None,None),(0,500,None))
#eg = echogram.echogram(fig_2, Sv_38_view, threshold=[-70,-34])
#eg.axes.set_title("Bottom as depth - 38kHz")
#eg.plot_line(bottom_38, linewidth=2.5)
#show()
