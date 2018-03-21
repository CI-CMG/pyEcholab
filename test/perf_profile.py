# -*- coding: utf-8 -*-
"""

"""

import sys
import cProfile, pstats
if (sys.version_info[0] == 3):
    from io import StringIO
else:
    from StringIO import StringIO
import time
from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


def print_profile_stats(profiler):
    '''
    print_profile_stats prints out the results from a profiler run
    '''
    if (sys.version_info.major == 2):
        s = StringIO()
    else:
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

#  The descriptions below apply to reading these 2 files in this order:
#       ./data/EK60/DY1201_EK60-D20120214-T231011.raw
#       ./data/EK60/DY1706_EK60-D20170609-T005736.raw
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw',
            './data/EK60/DY1706_EK60-D20170609-T005736.raw']

#  create a matplotlib figure to plot our echograms on
fig = figure()
#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 and  data sources
ek60 = EK60.EK60()

#  use the read_raw method to read in a data file
#profiler.enable()
#time.clock()
ek60.read_raw(rawfiles)
#print("read time: " + str(time.clock()))
#profiler.disable()
#print_profile_stats(profiler)

#  print some basic info about our object


print(ek60)

raw_data_38_1 = ek60.get_raw_data(channel_number=2)


#  call get_power to get a processed data object that contains power data. We provide
#  no arguments so we get all pings ordered by time.
t = time.clock()
processed_power_1 = raw_data_38_1.get_power()
print("get_power - time ordered: " + str(time.clock() - t))
#  that should be 1662 pings by 1988 samples.
print(processed_power_1)



pass
