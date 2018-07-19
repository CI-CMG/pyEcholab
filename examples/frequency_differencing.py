# -*- coding: utf-8 -*-
"""This example script demonstrates the use of numeric and boolean operators
on ProcessedData and Mask objects. It also provides an example of using the
ProcessedData.zeros_like() method to get an ProcessedData array we can use
to fill with the results of our simple analysis.  Lastly, it shows how to use
the ProcessedData.view() method to plot a subset of the data.

Note that this example is not intended to be an example of how to really do
frequency differencing.
"""

from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
from echolab2.processing import mask, line
import numpy as np


# Read in some data.
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T062521.raw',
            './data/EK60/DY1706_EK60-D20170625-T063335.raw',
            './data/EK60/DY1706_EK60-D20170625-T064148.raw']

# Specify the matching bottom files.
botfiles = ['./data/EK60/DY1706_EK60-D20170625-T062521.bot',
            './data/EK60/DY1706_EK60-D20170625-T063335.bot',
            './data/EK60/DY1706_EK60-D20170625-T064148.bot']

# Create an instance of our EK60 class.
ek60 = EK60.EK60()

# Read the raw files and store 18, 38, and 120 kHz.
print('Reading the raw files...')
ek60.read_raw(rawfiles, frequencies=[18000, 38000, 120000])

# Read the .bot files.
print('Reading the bot files...')
ek60.read_bot(botfiles)

# Get the raw_data objects from the ek60 object.  We'll call get_raw_data
# with no arguments to get a dict keyed by channel id of all the channels in
# the data.
raw_data = ek60.get_raw_data()

# Get the Sv for the frequencies we're looking for and put in a dictionary
# keyed by frequency. Note that I am aware that this approach would not work
# if there are multiple channels with the same frequency.
Sv_data = {18000: None, 38000: None, 120000: None}
bottom_lines = {18000: None, 38000: None, 120000: None}
for chan_id in raw_data:
    # Check if this is a frequency we're looking for.
    if (raw_data[chan_id].frequency[0] in Sv_data.keys()):
        # It is, so get Sv and assign it to our dictionary.
        Sv_data[raw_data[chan_id].frequency[0]] = \
            raw_data[chan_id].get_Sv()
        print(Sv_data[raw_data[chan_id].frequency[0]])
        bottom_lines[raw_data[chan_id].frequency[0]] = \
            raw_data[chan_id].get_bottom()

# Now create a mask for each frequency and apply surface and bottom lines
# to these masks such that we mask out samples near the surface and below the
# bottom.  We'll actually mask everything from 0.5m above the bottom down.

# First create a surface line.  Note that when we pass a scalar.

masks = {18000: None, 38000: None, 120000: None}
for freq in Sv_data.keys():

    # Create a mask.
    masks[freq] = mask.Mask(like=Sv_data[freq])

    # Next create a new line that is 0.5m shallower. (in place operators will
    # change the existing line.)
    bot_line = bottom_lines[freq] - 0.5

    # Now create a surface exclusion line at 10m RANGE.
    surf_line = line.Line(ping_time=Sv_data[freq].ping_time, data=10)

    # Now apply that line to our mask.  We apply the value True BELOW our
    # line.  Note that we don't need to specify the value as True is the
    # default.
    masks[freq].apply_line(bot_line, apply_above=False)

    # Now apply our surface line to this same mask.
    masks[freq].apply_line(surf_line, apply_above=True)

    # Now use this mask to set sample data from 0.5m above the bottom
    # downward to NaN.
    Sv_data[freq][masks[freq]] = np.nan

# Now lets compute some differences - the process_data class implements the
# basic Python arithmetic operators so we can simply subtract process_data
# objects like numeric objects.  Both,
#
# "regular": +, -, *, /  and  "in-place": +=, -=, *=, /=
#
# operators are implemented.  Regular operators return a new ProcessedData
# object with the same general properties containing the results of your
# operation.  The in-place operators will alter the data in the left hand side
# argument.

# 18 - 38
Sv_18m38 = Sv_data[18000] - Sv_data[38000]

# 120 - 38
Sv_120m38 = Sv_data[120000] - Sv_data[38000]


# Now we'll generate some masks identifying samples that fall within various
# ranges.
#
# The ProcessedData object also implements the Python comparison operators.
# These operators do an element by element comparison and will return a Mask
# object with samples set to the result of the comparison.

# For example, this operation will return a Mask object where samples in the
# Sv_18m38 "channel" with a value greater than 6 will be set to True.  All
# other samples will be False.
jellies = Sv_18m38 > 6

# Now we're going to do an in-place and-ing where we'll take the results of
# our first operation and AND them with the results of this operation where
# we're setting all samples in the Sv_120m38 channel to True if they are less
# than -1.
jellies &= Sv_120m38 < -1

# Here we'll get crazy and do two comparisons and AND the results.  Masks
# support boolean operations, both in-place and regular.  Just make sure you
# group your expressions since the boolean operators have a higher precedence
# than the comparison operators.
euphausiids = (Sv_120m38 > 9) & (Sv_18m38 < -5)

# Do another comparison.
myctophids = (Sv_18m38 < -9) & (Sv_120m38 < -8)

# Do another comparison.  This one will comprise the results of 4 comparisons.
fish = (Sv_18m38 < 2) & (Sv_18m38 > -4)
fish &= (Sv_120m38 < 0) & (Sv_120m38 > -6)


# Now lets create a ProcessedData object the same shape as our other data
# arrays but with the data array set to zeros.
diff_results = Sv_18m38.zeros_like()

# Also, we'll use the masks to set the various samples to values that
# represent what we think they are.
diff_results[jellies] = 4
diff_results[euphausiids] = 7
diff_results[myctophids] = 15
diff_results[fish] = 18


# Create a matplotlib figure to plot our echograms on.
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None,
                hspace=0.5)

# Plot the original data.
ax = fig.add_subplot(4, 1, 1)
# Use the view method to return a ProcessedData object that is a view into
# our original data. We will plot all pings and samples 0-2000.
v_data = Sv_data[18000].view((None, None, None),(0, 2000, None))
eg = echogram.echogram(ax, v_data, threshold=[-70, -34])
ax.set_title("Original 18 kHz Sv Data")

ax = fig.add_subplot(4, 1, 2)
v_data = Sv_data[38000].view((None, None, None), (0, 2000, None))
eg = echogram.echogram(ax, v_data, threshold=[-70,-34])
ax.set_title("Original 38 kHz Sv Data")

ax = fig.add_subplot(4, 1, 3)
v_data = Sv_data[120000].view((None, None, None), (0, 2000, None))
eg = echogram.echogram(ax, v_data, threshold=[-70, -34])
ax.set_title("Original 120 kHz Sv Data")


# Plot our differencing data.
ax = fig.add_subplot(4, 1, 4)
v_results = diff_results.view((None, None, None), (0, 2000, None))
# note that we set the threshold to something that will work with the values
# we assigned to our results.
eg = echogram.echogram(ax, v_results, threshold=[0, 20])
ax.set_title('Differencing results')

# Display the results.
show()


pass
