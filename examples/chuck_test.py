# -*- coding: utf-8 -*-
"""
This is Chuck's personal testing script. It could well be in an unhappy
state. It's in the repo so I can access it at home and work without needing a
separate branch. You are happy to test this script but please don't change
it. thanks...Chuck
"""

import sys
import cProfile
import pstats

from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap

from echolab2.processing.batch_utils import FileAggregator as fa
from echolab2.processing.align_pings import AlignPings
from echolab2.instruments.EK60 import EK60
from echolab2.plotting.matplotlib.echogram import echogram

if sys.version_info[0] == 3:
    from io import StringIO
else:
    from StringIO import StringIO



def print_profile_stats(profiler):
    '''
    print_profile_stats prints out the results from a profiler run
    '''
    if (sys.version_info.major == 3):
        s = StringIO()
    else:
        s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())

#  create a profiler object
profiler = cProfile.Profile()

file_bins = fa('../NCEI_workflow/data/SH1507', 10).file_bins
raw_files = file_bins[0]


#  create a matplotlib figure to plot our echograms on
fig = figure()
#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None,
                hspace=1.25)

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 and  data sources
ek60 = EK60()

#  use the read_raw method to read in a data file
ek60.read_raw(raw_files, power=None, angles=None, max_sample_count=None,
              start_time=None, end_time=None, start_ping=None, end_ping=None,
              frequencies=None, channel_ids=None,
              time_format_string='%Y-%m-%d %H:%M:%S', incremental=None,
              start_sample=None, end_sample=None)


#  print some basic info about our object. As you can see, 10 channels are
# reported. Each file has 5 channels and they in fact are physically the same
#  hardware. The reason there are 10 channels reported is that their
# transceiver number in the ER60 software changed.
# print(ek60)


#  now get a reference to the RawData object for each channel
raw_18 = ek60.get_rawdata(channel_number=1)
raw_38 = ek60.get_rawdata(channel_number=2)
raw_70 = ek60.get_rawdata(channel_number=3)
raw_120 = ek60.get_rawdata(channel_number=4)
raw_200 = ek60.get_rawdata(channel_number=5)
raw = [raw_18, raw_38, raw_70, raw_120, raw_200]

# time 2015-06-26T06:12:03 is missing in the 38kHz channel. this is ping #
# 489 in he other channels

# uncomment to test aligning of raw data objects
print('Before alignment')
for channel in raw:
    print(channel.channel_id)
    for ping in range(488, 491):
        print(ping, channel.ping_time[ping], channel.power[ping][100])
    print()

# call align pings
aligned = AlignPings(raw, 'delete')

print('\n After align')
for index, channel in enumerate(raw):
    if aligned.missing[index]:
        print('missing pings:{0}'.format(aligned.missing[index]))
    else:
        print('extra pings:{0}'.format(aligned.extras[index]))
    for ping in range(488, 491):
        print(ping, channel.ping_time[ping], channel.power[ping][100])
    print()


# get Sv for each channel
Sv_18 = raw_18.get_sv()
Sv_38 = raw_38.get_sv()
Sv_70 = raw_70.get_sv()
Sv_120 = raw_120.get_sv()
Sv_200 = raw_200.get_sv()
Sv = [Sv_18, Sv_38, Sv_70, Sv_120, Sv_200]


# time 2015-06-26T06:12:03 is missing in the 38kHz channel. this is ping #
# 489 in he other channels

# uncomment to test aligning of processed data object.
# print('Before alignment')
# for channel in Sv:
#     for ping in range(488, 491):
#         print(ping, channel.ping_time[ping], channel.Sv[ping][100])
#     print()
#
# # call align pings
# AlignPings(Sv, 'pad')
#
# print('\n After align')
# for channel in Sv:
#     for ping in range(488, 491):
#         print(ping, channel.ping_time[ping], channel.Sv[ping][100])
#     print()

# plot Sv values
threshold = [-70, 0]

ax_18 = fig.add_subplot(5, 1, 1)
echo_18 = echogram(ax_18, Sv_18, 'Sv', threshold=threshold)
ax_18.set_title("18kHz Sv data in time order")
# print(Sv_18)

ax_38 = fig.add_subplot(5, 1, 2)
echo_38 = echogram(ax_38, Sv_38, 'Sv', threshold=threshold)
ax_38.set_title("38kHz Sv data in time order")
# print(Sv_38)

ax_70 = fig.add_subplot(5, 1, 3)
echo_70 = echogram(ax_70, Sv_70, 'Sv', threshold=threshold)
ax_70.set_title("70kHz Sv data in time order")
# print(Sv_70)

ax_120 = fig.add_subplot(5, 1, 4)
echo_120 = echogram(ax_120, Sv_120, 'Sv', threshold=threshold)
ax_120.set_title("120kHz Sv data in time order")
# print(Sv_120)

ax_200 = fig.add_subplot(5, 1, 5)
echo_200 = echogram(ax_200, Sv_200, 'Sv', threshold=threshold)
ax_200.set_title("200kHz Sv data in time order")
# print(Sv_200)

#  show our figure
show()

