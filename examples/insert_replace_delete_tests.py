# -*- coding: utf-8 -*-
"""

"""

import time
from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram



rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw',
            './data/EK60/DY1706_EK60-D20170609-T005736.raw']

#  create a matplotlib figure to plot our echograms on
fig = figure()
#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

ek60 = EK60.EK60()
ek60.read_raw(rawfiles)



#  now get a reference to the RawData object that contains data from the first 38 kHz channel.
raw_data_38_1 = ek60.get_rawdata(channel_number=2)
'''
the sample data from channel 2 is contained in a 136x994 array. The data was recorded
with a 1024us transmit pulse length which on the EK60 and related hardware results
in a sample interval of 256us (sample interval = pulse length / 4). The data were
recorded in 2012.
'''
print(raw_data_38_1)

#  and get a reference to the RawData object that contains data from the second 38 kHz channel.
raw_data_38_2 = ek60.get_rawdata(channel_number=7)
'''
Channel 7's sample data is a 763x1059 array recoded with a 512us pulse length
resulting in a sample interval of 128us. These data were recorded in 2017.
'''
print(raw_data_38_2)

#  append the 2nd object's data to the first and print out the results
t = time.clock()
raw_data_38_1.append(raw_data_38_2)
print("append 1 time: " + str(time.clock() - t))
'''
The result of this append is that raw_data_38_1 now contains data from 899 pings.
The first 136 pings are the 2012 data and the next 763 the 2017 data. The sample
data arrays are 899x1059 and the object contains 2 unique sample intervals.
'''
print(raw_data_38_1)

#  insert the 2nd object's data into the first at ping 50
t = time.clock()
raw_data_38_1.insert(raw_data_38_2, ping_number=50)
print("insert time: " + str(time.clock() - t))

print(raw_data_38_1)

#  create an axes
ax_1 = fig.add_subplot(3,1,1)
#  create an echogram to plot up the raw sample data
echogram_2 = echogram.echogram(ax_1, raw_data_38_1, 'power')
ax_1.set_title("Raw power as stored in RawData object")




#  call get_power to get a processed data object that contains power data. We provide
#  no arguments so we get all pings ordered by time.
t = time.clock()
processed_power_1 = raw_data_38_1.get_power()
print("get_power - time ordered: " + str(time.clock() - t))
#  that should be 1662 pings by 1988 samples.
print(processed_power_1)

#  create an axes
ax_2 = fig.add_subplot(3,1,2)
#  create an echogram which will display on our newly created axes
echogram_2 = echogram.echogram(ax_2, processed_power_1, 'power')
ax_2.set_title("Power data in time order")

#  now request Sv data in time order
t = time.clock()
Sv = raw_data_38_1.get_sv()
print("get_Sv - time ordered: " + str(time.clock() - t))
#  this will also be 1662 pings by 1988 samples but is Sv ordered by time
print(Sv)

#  create another axes
ax_3 = fig.add_subplot(3,1,3)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_3, Sv, 'Sv', threshold=[-70,-34])
ax_3.set_title("Sv data in time order")

#  show our figure
show()


fig = figure()
#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

angle_cmap = get_cmap('plasma')

#  now request angles data in time order
t = time.clock()
angles = raw_data_38_1.get_physical_angles()
print("get_physical_angles - time ordered: " + str(time.clock() - t))
print(angles)

#  create another axes
ax_1 = fig.add_subplot(2,1,1)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_1, angles, 'angles_alongship', cmap=angle_cmap)
ax_1.set_title("angles_alongship data in time order")

#  create another axes
ax_2 = fig.add_subplot(2,1,2)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_2, angles, 'angles_athwartship', cmap=angle_cmap)
ax_2.set_title("angles_athwartship data in time order")

#  show our figure
show()


pass
