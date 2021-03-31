# -*- coding: utf-8 -*-
"""This is an example exercising masks.

This script demonstrates the use of masks for modifying and thresholding
data.  Specifically, it demonstrates processes such as creating masks,
copying and changing values in a mask, and plotting masks.
"""

from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
from echolab2.processing import mask


# Read in some data from files.
rawfiles = ['./data/OfotenDemo-D20001214-T145902.raw',
            './data/OfotenDemo-D20001214-T154020.raw']

# Specify the channel nummber to work with. This example shows
channel_number = 1

ek60 = EK60.EK60()
ek60.read_raw(rawfiles)

# Get a reference to the raw_data objects associated with
# the channel specified above. Calling get_channel_data
# and specifying one or more channel numbers will return a
# dictionary keyed by channel number. The values will be a
# list of data objects associated with that channel number.
raw_data = ek60.get_channel_data(channel_numbers=channel_number)

# Now get a reference to the first raw_data object for this
# channel.
raw_data = raw_data[channel_number][0]
print(raw_data)

# Since we used channel number to select our raw data we don't
# know what frequency we're working with. We will assume that
# the frequency is constant throughout the file.
this_freq_khz = int(raw_data.frequency[0] / 1000.)

# Get a processed_data object containing Sv.
Sv = raw_data.get_Sv()
print(Sv)

# Create a copy of Sv to compare against the copy we will manipulate.
orig_Sv = Sv.copy()

# Create a couple of masks.  Masks come in two types.  "Ping" masks are 1d masks
# that apply to all samples in a ping while "sample" masks are 2d masks and
# apply to the individual sample data elements.

# Mask objects are comprised of either a 2d or 1d boolean array and one or
# two 1d arrays containing the axes for the array.  When applying masks,
# the axes are checked against the axes of the object you're applying the
# mask to and they must be the same.  Because of this, most of the time you
# will create a mask that is "like" an existing processed_data object, which
# results in the mask array being sized correctly for the processed_data
# object and the axes are copied from the processed_data object and thus are
# the same.

# The default behavior of the constructor is to create a sample mask so we'll
# create a sample mask that is like our "Sv" processed_data object.
sample_mask = mask.mask(like=Sv)
print(sample_mask)

# Masks are by default created with all elements set to "False".  You can use
# the value keyword of the constructor to set it to True if you so desire.

# Create a ping mask like Sv, setting all values to True.
ping_mask = mask.mask(like=Sv, type='ping', value=True)
print(ping_mask)

# Masks can be used on their own to present data (though mask plotting isn't
# implemented yet) or more commonly used as a logical index array to operate on
# specific samples in a processed_data object.  Since mask plotting isn't
# implemented, we'll focus on the second, more common use.

# At the most basic level, setting mask elements to True will specify that
# an operation occurs on that element. For example, if we wanted to set
# a block of samples between sample 50 and 800 from ping 20-1500 to -999
# we could set those mask values to True and then use the mask to "index"
# into our processed_data object Sv.
sample_mask.mask[20:1500, 50:800] = True

# Now use the mask to set these samples to -999.
Sv[sample_mask] = -999

# Create a matplotlib figure to plot our echograms on.
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None,
                hspace=0.5)

# Plot the original data.
ax1 = fig.add_subplot(2, 1, 1)
eg = echogram.Echogram(ax1, orig_Sv, threshold=[-70, -34])
ax1.set_title('Original ' + str(this_freq_khz) + ' kHz Sv Data')

# Plot the data we modified.
ax2 = fig.add_subplot(2, 1, 2)
eg = echogram.Echogram(ax2, Sv, threshold=[-70, -34])
ax2.set_title('Modified ' + str(this_freq_khz) + ' kHz Sv Data')

# Display the results.
show()

# But that's not really how you would use a mask since you can set
# rectangular regions directly by slicing the processed_data object.
# Thresholding is a more realistic example of using a mask.

# Using Python comparison operators with processed_data objects will return
# masks so thresholding is as simple as using <, >, <=, >=, etc.

Sv = orig_Sv.copy()

# The comparison operators work on scalars.  Create 3 masks, each with a
# different threshold.
mask_1 = Sv < -70
mask_3 = Sv > -25

# You can apply boolean operators to masks as well, which also returns a mask.
# Just make sure you group the operations properly.
mask_2 = (Sv >= -50) & (Sv <= -25)

# Instead of using the masks to set values in the original Sv object, let's
# create a processed_data object that is a copy of Sv with the sample data set
# to zeros.
synth_data = Sv.zeros_like()

# Now set the values in our new processed_data object.
synth_data[mask_1] = 0
synth_data[mask_2] = 10
synth_data[mask_3] = 15

# Create a matplotlib figure to plot our echograms on.
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None,
                hspace=0.5)

# Plot the original data.
ax1 = fig.add_subplot(2, 1, 1)
eg = echogram.Echogram(ax1, orig_Sv, threshold=[-70, -34])
ax1.set_title('Original ' + str(this_freq_khz) + ' kHz Sv Data')

# Plot the data we modified.
ax2 = fig.add_subplot(2, 1, 2)
eg = echogram.Echogram(ax2, synth_data, threshold=[0, 20])
ax2.set_title('Threshold results')

# Display the results.
show()

