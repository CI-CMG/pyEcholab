# -*- coding: utf-8 -*-
"""

"""

import cProfile, pstats
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from echolab2.instruments import EK60


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
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw','./data/EK60/DY1706_EK60-D20170609-T005736.raw']


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
#  their transceiver number in the ER60 software changed. This isn't ideal, I considered
#  allowing for a looser ID matching scheme but that makes things a lot more complicated.
print(ek60)

#  now print out some infor about our first 38 channel
raw_data_38_1 = ek60.get_rawdata(channel_number=2)
print(raw_data_38_1)

#  and the second 38 channel
raw_data_38_2 = ek60.get_rawdata(channel_number=7)
print(raw_data_38_2)

#  append tghe 2nd to the first and print out the results
raw_data_38_1.append(raw_data_38_2)
print(raw_data_38_1)

power = raw_data_38_1.get_power()

pass

