# -*- coding: utf-8 -*-
"""
This example demonstrates manipulating the raw_data and processed_data
objects using the insert and delete methods. The primary purpose of
this example is to verify basic operation of the insert and delete methods
but it also provides some simple and somewhat contrived examples of using
index arrays with these methods.
"""

import numpy as np
from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
from echolab2.processing import mask


#  read in some data
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw']
ek60 = EK60.EK60()
ek60.read_raw(rawfiles)

#  get a reference to the raw_data object
raw_data_38 = ek60.get_rawdata(channel_number=2)
print(raw_data_38)

Sv = raw_data_38.get_sv()

#  create a couple of masks. Masks come in two types. "Ping" masks are 1d masks
#  that apply to all samples in a ping while "sample" masks are 2d and apply
#  to the

m = mask.mask(like=Sv)
Sva=Sv[0:10,:]
m.mask[100:110, 20:30] = True
x = Sv[m]


##  and display the results
#fig = figure()
#subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None, hspace=0.5)
#
##  plot up the synthetic power data
#ax = fig.add_subplot(2,1,1)
#eg = echogram.echogram(ax, raw_data_38, 'power')
#ax.set_title("Synthetic power after delete - should be 136 pings")
#
##  get the Sv data in time order and plot
#Sv = raw_data_38.get_sv()
#ax = fig.add_subplot(2,1,2)
#eg = echogram.echogram(ax, Sv, 'Sv')
#ax.set_title('Sythetic power after delete converted to Sv shown in time order.')
#
##  show the results
#show()

pass
