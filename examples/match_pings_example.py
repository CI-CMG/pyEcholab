# -*- coding: utf-8 -*-
"""match_pings_example.py

This script demonstrates the match_ping method of the ping_data class
which can be used to insert missing pings between channels that have
been recorded on the same system.

For this example, assume that we want to compute the frequency difference
between some channels in our data file. Unfortunately this sounder system
was not installed by a certified Kongsberg technician and the various
channels drop a lot of pings. When you read these files into pyEcholab
the axes of the various channels do not match so you cannot subtract them
to get your difference.

To overcome this, the match_pings method alters the ping time axes
in your data object with that of the "other" object. Ping times in the
other object that aren't in your object are inserted. Ping times in your
object that aren't in the other object are deleted.

The example will then execute the match_pings method on both the raw_data
object and the processed_data object to test the method for both of these
child classes. Each "match channel" vs "other channel" comparison for both
the raw_data match and the processed_data match will be plotted. The results
should be the same for both.


In reality, Kongsberg systems are known for their legendary reliability
so you probably don't have a file on hand that is actually missing any pings.
To overcome this, we'll randomly remove pings from each channel.

We're going to use the first channel as our "match" channel. This means
that the other channels will be modified (if requried) to share the same
time axis as the first channel by adding pings the first channel has
that the other channels lack, or removing pings the other channels have
but the first channel lacks.

"""

import numpy as np
from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram

# Our test data doesn't have any missing pings so we'll randonly
# drop pings in the data to simulate missing pings. Here we'll
# specify some parameters used when removing pings.

# Set the minimum number of pings to remove from a channel
min_pings_to_remove = 2

# Set the maximum number of pings to remove from a channel
max_pings_to_remove = 5

# Set this to True to remove pings from the "match" channel
# If set to False, the match channel will always have >= pings
# as the other channels. If True, the match channel may have
# fewer pings than the other channels. This tests the two
# way removal of the pings.
remove_from_match = True


# Specify a data file for this test
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T062521.raw']

# Create an instance of the EK60 instrument. This is the top level object used
# to interact with EK60 and  data sources.
ek60 = EK60.EK60()

# Read the data
ek60.read_raw(rawfiles)

# Print some basic info about our data
print('Original data:')
print(ek60)

# Our source data doesn't have any missing pings so we'll knock some out.
#
# We're going to use the first channel as our "match" channel. This means
# that the other channels will be modified (if requried) to share the same
# time axis as the first channel by adding pings the first channel has
# that the other channels lack, or removing pings the other channels have
# but the first channel lacks.
#
# Note that the match_pings method DOES NOT INTERPOLATE and it is assumed
# this method will be used to match channels that have been recorded
# simultaneously on the same system.

# get a dict containing our raw data keyed by channel ID
raw_data =  ek60.get_channel_data()

# Create some vars to store data and state in
other_data = []
removed_idx = {}
match_data = None

# Work through all of our channels
for channel_id in raw_data:

    # Grab the first data object for this channel
    data = raw_data[channel_id][0]

    # Grab the first channel as the one we'll match to.
    if match_data is None:
        match_data = data
        match_channel = channel_id
        # If we're not removing data from this channel, move on
        if not remove_from_match:
            continue
    else:
        # All "other" channels are added to the "other data" list
        other_data.append(data)

    # determine how many pings to remove
    del_npings = np.random.randint(min_pings_to_remove,
            max_pings_to_remove)

    # and the indexes to remove
    del_idx = np.random.randint(1, data.ping_time.size, del_npings)

    # Store the indexes we removed
    removed_idx[channel_id] = del_idx

    # now delete them from our raw data object
    if del_idx.size > 0:
        data.delete(index_array=del_idx)


# Print the updated info - note we'll have fewer pings.
print()
print('After randomly deleting from ' + str(min_pings_to_remove) +
        ' to ' + str(max_pings_to_remove) + ' pings per channel:')
print(ek60)
print()
print('Pings removed:')
for channel_id in removed_idx:
    print(channel_id + ' removed ' + str(removed_idx[channel_id]))
print()


# Get the raw data for this channel
match_data_Sv = match_data.get_Sv()

#  get the frequency of the match data in kHz (for labeling)
match_freq = int(match_data.get_frequency(unique=True)[0] / 1000)


# Now match the other_data to our match_data. We can match both
# raw_data objects and processed_data objects. We're going to test
# both ways but users would typically want to match processed_data
# objects.
for channel_id in raw_data:

    # Create a matplotlib figure to plot our echograms on.
    fig = figure()
    # Set some properties for the sub plot layout.
    subplots_adjust(left=0.11, bottom=0.1, right=0.95, top=.93, wspace=None,
                    hspace=0.4)

    # Get the raw data for this channel
    data = raw_data[channel_id][0]

    #  get the frequency in kHz (for labeling)
    freq = int(data.get_frequency(unique=True)[0] / 1000)

    # Get the unmatched data as Sv
    Sv_original = data.get_Sv()

    # First match the raw data in this channel to our match channel.
    # Note that self matches will return immediately with no changes.
    match_results = data.match_pings(match_data)

    # Now get matched Sv
    Sv_matched = data.get_Sv()

    # Now plot up the match data and the matched data
    label_text = '(raw_data) Match Data:' + str(match_freq) + ' kHz '
    ax_1 = fig.add_subplot(2, 1, 1)
    eg_1 = echogram.Echogram(ax_1, match_data_Sv, threshold=[-70,-34])
    ax_1.set_title(label_text)

    # Now plot up the match data and the matched data
    label_text = ('Matched Data:' + str(freq) + ' kHz :: removed pings ' +
        str(match_results['removed']) + ' :: inserted pings ' +
        str(match_results['inserted']))
    print(label_text)
    ax_2 = fig.add_subplot(2, 1, 2)
    eg_2 = echogram.Echogram(ax_2, Sv_matched, threshold=[-70,-34])
    ax_2.set_title(label_text)

    show()

    # Now match using the processed_data objects.

    # Create a matplotlib figure to plot our echograms on.
    fig = figure()
    # Set some properties for the sub plot layout.
    subplots_adjust(left=0.11, bottom=0.1, right=0.95, top=.93, wspace=None,
                    hspace=0.4)

    # Now match the processed_data.
    match_results = Sv_original.match_pings(match_data_Sv)

    # Now plot up the match data and the matched data
    label_text = '(processed_data) Match Data:' + str(match_freq) + ' kHz '
    ax_1 = fig.add_subplot(2, 1, 1)
    eg_1 = echogram.Echogram(ax_1, match_data_Sv, threshold=[-70,-34])
    ax_1.set_title(label_text)

    # Now plot up the match data and the matched data
    label_text = ('Matched Sv Data:' + str(freq) + ' kHz :: removed pings ' +
        str(match_results['removed']) + ' :: inserted pings ' +
        str(match_results['inserted']))
    ax_2 = fig.add_subplot(2, 1, 2)
    eg_2 = echogram.Echogram(ax_2, Sv_original, threshold=[-70,-34])
    ax_2.set_title(label_text)

    show()

print()


