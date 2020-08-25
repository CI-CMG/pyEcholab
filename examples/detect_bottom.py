# -*- coding: utf-8 -*-
"""Reads raw and bot/out files, detects bottom using super simple detector and plots data.

This example implements a comically simple bottom detector. It has been written to
demonstrate and explore how and where bottom detection would fit into the
current pyEcholab2 framework.

I am not constraining the input data into the bottom detector so it is on you to
parameterize it correctly. In this example I'm passing heave corrected Sv data
and so I need to set the bottom search minimum in depth (not range as one
typically would when configuring your sounder.) The backstep should be in
Sv units.

The afsc_bot_detector class used in this example is not intended to be used
for any real science. This is simply something to get development started and
to work out details around implementing additional processing algorithms.

"""

from matplotlib.pyplot import figure, show
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
from echolab2.processing import afsc_bot_detector


# Create a list of .raw files.
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw']
# Also create a list of .bot files.
botfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.bot']

# Create an instance of ER60.
ek60 = EK60.EK60()

#  set the minimum detection distance - the simple bottom detection algorithm
#  implemented in afsc_bot_detector is depth/range agnostic. It simply operates
#  on what you give it so it is up to you to set this to a reasonable value. In this
#  example we're getting our heave compensated Sv data on a depth grid so we need
#  to make sure the min is set to a fairly large value.

#  since we'll be passing our bottom detector data on a depth grid, set this to the
#  minimum DEPTH in meters to search for the bottom
search_min = 15

#  since we'll be passing Sv data to the bottom detector,, set the backstep in Sv (db)
backstep = 35

#  create an instance of our bottom detector
bot_detector = afsc_bot_detector.afsc_bot_detector(search_min=search_min,
        backstep=backstep)

# Read the .raw files.
print('reading raw files...')
ek60.read_raw(rawfiles, frequencies=[38000, 120000])

# Read the .bot files.
print('reading bot files...')
ek60.read_bot(botfiles)

# Get a reference to the RawData object for specified channels.
raw_data_38 = ek60.get_channel_data(channel_number=1)
raw_data_120 = ek60.get_raw_data(channel_number=2)

# Get Sv data.
Sv_38_as_depth = raw_data_38.get_Sv(heave_correct=True)
Sv_120_as_depth = raw_data_120.get_Sv(heave_correct=True)

# Get the sounder detected bottom data.  The astute observer would wonder why
# we're applying heave correction to the sounder detected bottom since you
# shouldn't do this (you only correct the underlying sample data which
# defines the axes).  We have chosen to allow the heave_correct keyword in this
# context to maintain a consistent interface with the get_* methods.  When
# set, no heave correction is applied, but it ensures that get_bottom returns
# *depth*.  You could achieve the same thing by setting the return_depth
# keyword to True.
bottom_38 = raw_data_38.get_bottom(heave_correct=True)
bottom_120 = raw_data_120.get_bottom(heave_correct=True)

#  now use our simple bottom detector to pick a bottom line for the 38. The bottom
#  detector class returns a pyEcholab2 Line object representing the bottom.
bottom_38_detected = bot_detector.detect(Sv_38_as_depth)
#  Give the line a nice gold color (since we're using Matplotlib, our colors must
#  be in the range of 0-1)
bottom_38_detected.color = [244./255, 200./255, 66/255.]

#  and pick the 120 and give it a gold color
bottom_120_detected = bot_detector.detect(Sv_120_as_depth)
bottom_120_detected.color = [244./255, 200./255, 66/255.]


# Create matplotlib figures and display the results.
fig_38 = figure()
eg = echogram.Echogram(fig_38, Sv_38_as_depth, threshold=[-70, -34])
eg.axes.set_title("Heave Corrected with Two Detected Bottoms - 38kHz")
eg.plot_line(bottom_38, linewidth=2.5)
eg.plot_line(bottom_38_detected, linewidth=2.5)

fig_120 = figure()
eg = echogram.Echogram(fig_120, Sv_120_as_depth, threshold=[-70, -34])
eg.axes.set_title("Heave Corrected with Two Detected Bottoms - 120kHz")
eg.plot_line(bottom_120, linewidth=2.5)
eg.plot_line(bottom_120_detected, linewidth=2.5)

show()

