# -*- coding: utf-8 -*-
"""This example script tests AlignPings functionality."""

import sys

from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap

from echolab2.processing.batch_utils import FileAggregator as fa
from echolab2.processing.align_pings import AlignPings
from echolab2.instruments.EK60 import EK60
from echolab2.plotting.matplotlib.echogram import echogram

# if sys.version_info[0] == 3:
#     from io import StringIO
# else:
#     from StringIO import StringIO


file_bins = fa('../NCEI_workflow/data/SH1507', 10).file_bins
raw_files = file_bins[0]


# Create a matplotlib figure to plot our echograms on.
fig = figure()
# Set some properties for the sub plot layout.
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None,
                hspace=1.25)

# Create an instance of the EK60 instrument.  This is the top level object used
# to interact with EK60 and data sources.
ek60 = EK60()

# Use the read_raw method to read in a data file.
ek60.read_raw(raw_files, power=None, angles=None, max_sample_count=None,
              start_time=None, end_time=None, start_ping=None, end_ping=None,
              frequencies=None, channel_ids=None,
              time_format_string='%Y-%m-%d %H:%M:%S', incremental=None,
              start_sample=None, end_sample=None)

# Print some basic info about our object.
# print(ek60)

# Get a reference to the RawData object for each channel.
raw_18 = ek60.get_raw_data(channel_number=1)
raw_38 = ek60.get_raw_data(channel_number=2)
raw_70 = ek60.get_raw_data(channel_number=3)
raw_120 = ek60.get_raw_data(channel_number=4)
raw_200 = ek60.get_raw_data(channel_number=5)
raw = [raw_18, raw_38, raw_70, raw_120, raw_200]

# Time 2015-06-26T06:12:03 is missing in the 38kHz channel.  This is ping number
# 489 in the other channels.
#
# Uncomment lines 57-75 to test aligning of raw data objects the keyword
# 'pad' aligns by padding, 'delete' aligns by dropping  extra pings. Pad
# method only works on processed data objects.
# print('Before alignment')
# for channel in raw:
#     print(channel.channel_id)
#     for ping in range(488, 491):
#         print(ping, channel.ping_time[ping], channel.power[ping][100])
#     print()
#
# # call align pings
# aligned = AlignPings(raw, 'delete')
#
# print('\n After align')
# for index, channel in enumerate(raw):
#     if hasattr(aligned, 'missing') and len(aligned.missing[index]) > 0:
#         print('missing pings:{0}'.format(aligned.missing[index]))
#     elif hasattr(aligned, 'extras') and len(aligned.extras[index]) > 0:
#         print('extra pings:{0}'.format(aligned.extras[index]))
#     for ping in range(488, 491):
#         print(ping, channel.ping_time[ping], channel.power[ping][100])
#     print()

# Get Sv for each channel.
Sv_18 = raw_18.get_Sv()
Sv_38 = raw_38.get_Sv()
Sv_70 = raw_70.get_Sv()
Sv_120 = raw_120.get_Sv()
Sv_200 = raw_200.get_Sv()
Sv = [Sv_18, Sv_38, Sv_70, Sv_120, Sv_200]


# Remove some pings for better testing of align functionality.  Comment these
# lines to test against the one missing ping in the 38KHz channel of the
# example files.
Sv_18.delete(start_ping=603, end_ping=605)
Sv_200.delete(start_ping=510, end_ping=512)

# print('Before alignment')
# for channel in Sv:
#     print(channel.channel_id)
#     for ping in range(488, 491):
#         print(ping, channel.ping_time[ping], channel.data[ping][100])
#     print()

# Call align pings.
aligned = AlignPings(Sv, 'pad')  # 'delete' or 'pad'


# print('\n After align')
# for index, channel in enumerate(Sv):
#     print(channel)
#     if hasattr(aligned, 'missing') and len(aligned.missing[index]) > 0:
#         print('missing pings:{0}'.format(aligned.missing[index]))
#     elif hasattr(aligned, 'extras') and len(aligned.extras[index]) > 0:
#         print('extra pings:{0}'.format(aligned.extras[index]))
#     for ping in range(488, 491):
#         print(ping, channel.ping_time[ping], channel.data[ping][100])
#     print()
#
# for channel in aligned.details:
#     print('\n'+channel)
#     for detail in aligned.details[channel]:
#         print ('\t{0}: {1}'.format(detail, aligned.details[channel][detail]))


# Plot Sv values.
threshold = [-70, 0]

ax_18 = fig.add_subplot(5, 1, 1)
echo_18 = echogram(ax_18, Sv_18, 'data', threshold=threshold)
ax_18.set_title("18kHz Sv data in time order")
# print(Sv_18)

ax_38 = fig.add_subplot(5, 1, 2)
echo_38 = echogram(ax_38, Sv_38, 'data', threshold=threshold)
ax_38.set_title("38kHz Sv data in time order")
# print(Sv_38)

ax_70 = fig.add_subplot(5, 1, 3)
echo_70 = echogram(ax_70, Sv_70, 'data', threshold=threshold)
ax_70.set_title("70kHz Sv data in time order")
# print(Sv_70)

ax_120 = fig.add_subplot(5, 1, 4)
echo_120 = echogram(ax_120, Sv_120, 'data', threshold=threshold)
ax_120.set_title("120kHz Sv data in time order")
# print(Sv_120)

ax_200 = fig.add_subplot(5, 1, 5)
echo_200 = echogram(ax_200, Sv_200, 'data', threshold=threshold)
ax_200.set_title("200kHz Sv data in time order")
# print(Sv_200)

# Display our figure.
show()
