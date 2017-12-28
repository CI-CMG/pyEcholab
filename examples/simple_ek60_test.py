# -*- coding: utf-8 -*-
"""

"""

import sys
import cProfile, pstats
if (sys.version_info[0] == 3):
    from io import StringIO
else:
    from StringIO import StringIO
import numpy as np
#import matplotlib.pyplot as plt, figure
from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


def print_profile_stats(profiler):
    '''
    print_profile_stats prints out the results from a profiler run
    '''
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

#  create a profiler object
profiler = cProfile.Profile()


#  create the list of input files - for this test I am purposly picking
#  two files with the same channels but the channels have different pulse
#  lengths and a different installation order

# THESE WORK
#  The descriptions below apply to reading these 2 files in this order:
#       ./data/EK60/DY1201_EK60-D20120214-T231011.raw
#       ./data/EK60/DY1706_EK60-D20170609-T005736.raw
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw','./data/EK60/DY1706_EK60-D20170609-T005736.raw']

#  NEED TO CHECK ON AN APPEND ERROR WITH THESE FILES:
#rawfiles = ['./data/EK60/DY1706_EK60-D20170609-T005736.raw','./data/EK60/DY1706_EK60-D20170625-T061707.raw']


#  create a matplotlib figure to plot our echograms on
fig = figure()
#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 and  data sources
ek60 = EK60.EK60()

#  use the read_raw method to read in a data file
#profiler.enable()
ek60.read_raw(rawfiles)
#profiler.disable()
#print_profile_stats(profiler)

#  print some basic info about our object

#  as you can see, 10 channels are reported. Each file has 5 channels and they in fact
#  physically are the same hardware. The reason there are 10 channels reported is that
#  their transceiver number in the ER60 software changed.
print(ek60)

#  now get a reference to the RawData object that contains data from the first 38 kHz channel.
raw_data_38_1 = ek60.get_rawdata(channel_number=2)
'''
the sample data from channel 2 is contained in a 136x994 array. The data was recorded
with a 1024us transmit pulse length which on the EK60 and related hardware results
in a sample interval of 256us (sample interval = pulse length / 3). The data were
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
raw_data_38_1.append(raw_data_38_2)
'''
The result of this append is that raw_data_38_1 now contains data from 899 pings.
The first 136 pings are the 2012 data and the next 763 the 2017 data. The sample
data arrays are 899x1059 and the object contains 2 unique sample intervals.
'''
print(raw_data_38_1)

#  insert the 2nd object's data into the first at ping 50
raw_data_38_1.insert(raw_data_38_2, ping_number=50)
'''
Now raw_data_38_1 contains 1662 pings. Pings 1-50 are from the 2012 data. Pings
51-813 are the 763 pings from the 2012 data. Pings 814-899 are the rest of the 2012
data and pings 900-1663 are a second copy of the 2017 data
'''
print(raw_data_38_1)

#  create an axes
ax_1 = fig.add_subplot(3,1,1)
#  create an echogram to plot up the raw sample data
echogram_2 = echogram.echogram(ax_1, data=raw_data_38_1.power)
ax_1.set_title("Raw power as stored in RawData object")


'''
At this point we have a 1662x1059 array with data recorded at two different sample
intervals. When we convert this data to return a processed_data object we have
to resample to a constant sample interval. By default, the get_* methods will
resample to the shortest sample interval (highest resolution) in the data that is
being returned. In our case that will result in the 136 pings from 2012 recorded
with a sample rate of 256us being resampled to 128us.

The two files were also recorded with slightly different sound speed values and
we're not going to supply a constant sound speed (or any calibration values) to
the get_power method so it will use the calibration parameter values from the
raw data. When no sound speed calibration data is provided, the get_* methods will
resort to interpolating range using the sound speed that occurs most in the data
(in other words, it interpolates the fewest pings it needs to.)

When we request data using the get_* methods we can provide a time range or ping
range to return data from. Providing no constraints on the range of data returned
will return all of the data. By default the data will be in time order. You can
force the method to return data in ping order (the order it exists in the RawData
object) by setting the time_order keyword to False. Advanced indexing can be done
outside of the get_* methods and passed into them using the return_indices keyword.

'''

#  call get_power to get a processed data object that contains power data. We provide
#  no arguments so we get all pings ordered by time.
processed_power_1 = raw_data_38_1.get_power()
#  that should be 1662 pings by 1988 samples.
print(processed_power_1)

#  create an axes
ax_2 = fig.add_subplot(3,1,2)
#  create an echogram which will display on our newly created axes
echogram_2 = echogram.echogram(ax_2, data=processed_power_1.power)
ax_2.set_title("Power data in time order")


#  now request power data in ping order
processed_power_2 = raw_data_38_1.get_power(time_order=False)
#  this will also be 1662 pings by 1988 samples but the order will be identical
#  to the top figure
print(processed_power_2)

#  create another axes
ax_3 = fig.add_subplot(3,1,3)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_3, data=processed_power_2.power)
ax_3.set_title("Power data in ping order")

#  show our figure
show()

