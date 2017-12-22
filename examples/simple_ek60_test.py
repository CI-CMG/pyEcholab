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
import matplotlib.pyplot as plt
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
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw','./data/EK60/DY1706_EK60-D20170609-T005736.raw']
#rawfiles = ['./data/EK60/DY1706_EK60-D20170609-T005736.raw']
#rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw']
#rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw','./data/EK60/DY1706_EK60-D20170625-T062521.raw']

#  APPEND ERROR
#rawfiles = ['./data/EK60/DY1706_EK60-D20170609-T005736.raw','./data/EK60/DY1706_EK60-D20170625-T061707.raw']


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

#  now print out some infor about our first 38 channel
raw_data_38_1 = ek60.get_rawdata(channel_number=2)
print(raw_data_38_1)

#  and the second 38 channel
raw_data_38_2 = ek60.get_rawdata(channel_number=7) #7
print(raw_data_38_2)

#  append tghe 2nd to the first and print out the results
raw_data_38_1.append(raw_data_38_2)
print(raw_data_38_1)


power = raw_data_38_1.get_power()
threshold = [np.nanmin(power.power),np.nanmax(power.power)]
eg = echogram.echogram(data=power.power, threshold=threshold)
plt.show()


pass

