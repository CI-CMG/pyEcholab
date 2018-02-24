# -*- coding: utf-8 -*-
"""

"""

import time
import numpy as np
from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram




#  read in some data
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw']
ek60 = EK60.EK60()
ek60.read_raw(rawfiles)

#  get a reference to the raw_data object
raw_data_38 = ek60.get_rawdata(channel_number=2)
print(raw_data_38)

#  insert synthetic data - create data where each ping is a constant value and the
#  values change significantly from ping to ping so it is easy to distinguish the
#  pings and see verify (or not) that data is in the right place.
fake_data = np.arange(20) * 9.0 - 150.0
j = 0
for i in range(raw_data_38.n_pings):
    raw_data_38.power[i,:] = fake_data[j]
    j += 1
    if (j == fake_data.shape[0]):
        j = 0



fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

#  plot up the synthetic power data
ax = fig.add_subplot(3,1,1)
eg = echogram.echogram(ax, raw_data_38, 'power')
ax.set_title("Synthetic power - 136 pings")

#  now resize the data - "new" pings will be filled with existing data
raw_data_38.resize(raw_data_38.n_pings+24, raw_data_38.n_samples)
print(raw_data_38)

#  and plot the resized data
ax2 = fig.add_subplot(3,1,2)
eg = echogram.echogram(ax2, raw_data_38, 'power')
ax2.set_title("Synthetic power resized to 160 pings")


#  now insert empty data. first create an index array containing the indices
#  where we will insert the data.
insert_idx = np.array([20,21,22,23,40,41,42,43,60,61,62,63,80,81,82,83,
        100,101,102,103,120,121,122,123])
#  insert the data - notice that if we call insert with the "object to insert"
#  argument set to None, it will automagically insert "empty" data.
raw_data_38.insert(None, index_array=insert_idx)

#  and plot the power with empty data
ax3 = fig.add_subplot(3,1,3)
eg = echogram.echogram(ax3, raw_data_38, 'power')
ax3.set_title("Synthetic power resized to 160 pings with empty data inserted")

#  show the results
show()

#  THIS SCRIPT DOES NOT WORK BEYOND THIS POINT


Sv = raw_data_38.get_sv()

fig = figure()
ax = fig.add_subplot(1,1,1)
eg = echogram.echogram(ax, Sv, 'Sv')
ax.set_title("Sv")
show()

pass
