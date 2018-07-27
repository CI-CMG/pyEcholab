# -*- coding: utf-8 -*-
"""
Developmental workflow for making NCEI multifrequency plots using PyEcholab
"""

import numpy as np
from scipy.ndimage.filters import gaussian_filter as gf

from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap
from echolab2.instruments import EK60


from echolab2.processing.batch_utils import FileAggregator as fa
from echolab2.processing.align_pings import AlignPings
from echolab2.plotting.matplotlib.echogram import echogram




# def make_masks(data_objects, low_threshold, high_threshold):
#     masks = {}
#     for frequency, data in data_objects.items():
#         masks[frequency] = (data >= low_threshold) & (data <= high_threshold)
#     return masks
#
#
# def mask_data(data_objects, masks, values=None):
#     if not values:
#         values = {18: 1, 38: 3, 70: 29, 120: 7, 200: 13}
#
#     processed_data = {}
#     for frequency, data in data_objects.items():
#         processed_data[frequency] = data.zeros_like()
#         processed_data[frequency][masks[frequency]] = values[frequency]
#
#     return processed_data
#
# def smooth(data_objects, sigma=3):
#     smooth_objects = {}
#
#     for frequency, data in data_objects.items():
#         smooth_data = gf(data.data, sigma)
#         new_object = data.empty_like()
#         setattr(new_object, 'data', smooth_data)
#         smooth_objects[frequency] = new_object
#
#     return smooth_objects
#
#
# def get_multifrequency_data(data_objects, low_threshold=-66,
#                             high_threshold=-25, values=None):
#
#     masks = make_masks(data_objects, low_threshold, high_threshold)
#     processed_data = mask_data(data_objects, masks)
#
#     # Make a new Processed Data object to hold final data array (using the
#     # the first channel as a template.
#     channels = list(data_objects.keys())
#     first_channel = channels[0]
#     final_data = data_objects[first_channel].zeros_like()
#
#     # Add each channels integer values to create final data array
#     for value in processed_data.values():
#         final_data += value
#
#     return final_data


# Get a list of lists that are aggregates of files binned into 1 hour blocks
rawfiles = fa('data/SH1507', interval=10)

# Create a matplotlib figure to plot our echograms on.
fig = figure()
# Set some properties for the sub plot layout.
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None,
                hspace=0.5)

# Create an instance of the EK60 instrument. This is the top level object used
# to interact with EK60 and  data sources.
ek60 = EK60.EK60()

# Use the read_raw method to read in the first bin of files.
ek60.read_raw(rawfiles.file_bins[0])

# Print some basic info about our object.  As you will see, 10 channels are
# reported.  Each file has 5 channels, and are in fact, physically the same
# hardware.  The reason there are 10 channels reported is because their
# transceiver number in the ER60 software changed.
# print(ek60)


# create a list RawData objects from the channels in the data.
raw_data = {}
for channel in ek60.channel_id_map:
    raw_data[channel] = ek60.get_raw_data(channel_number=channel)

# Get heave corrected Sv for each channel and add to dictionary is Sv data.
Sv = {}
for channel, data in raw_data.items():
    frequency = int(data.frequency[0]/1000)
    Sv[frequency] = data.get_Sv(heave_correct=True)


channels = []
for frequency, data in Sv.items():
    channels.append(data)

# Align pings using padding for dropped pings.
aligned = AlignPings(channels, 'pad')  # 'delete' or 'pad'

smooth_data = smooth(Sv, sigma=3)
smooth_data = get_multifrequency_data(smooth_data)

final_data = get_multifrequency_data(Sv)

print(type(final_data.data))
print(final_data.data.min(), final_data.data.max())
print(np.unique(final_data.data))

# Plot Sv values.
threshold = [0, 53]

ax_1 = fig.add_subplot(2, 1, 1)
raw = echogram(ax_1, final_data, 'data', threshold=threshold)
ax_1.set_title("NCEI multifrequency in time order")

ax_2 = fig.add_subplot(2, 1, 2)
smooth = echogram(ax_2, smooth_data, 'data', threshold=threshold)
ax_2.set_title("Smooth NCEI multifrequency in time order")

# Display our figure.
show()
