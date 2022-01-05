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
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T062521.raw']
# Also create a list of .bot files.
botfiles = ['./data/EK60/DY1706_EK60-D20170625-T062521.bot']

frequencies_to_read = [38000, 120000]

# Create an instance of EK60.
ek60 = EK60.EK60()

#  set the minimum detection distance - the simple bottom detection algorithm
#  implemented in afsc_bot_detector is depth/range agnostic. It simply operates
#  on what you give it so it is up to you to set this to a reasonable value. In this
#  example we're getting our heave compensated Sv data on a depth grid so we need
#  to make sure the min is set to a fairly large value.

#  since we'll be passing our bottom detector data on a depth grid, set this to the
#  minimum DEPTH in meters to search for the bottom
search_min = 15

#  since we'll be passing Sv data to the bottom detector, set the backstep in Sv (db)
backstep = 35

#  create an instance of our bottom detector
bot_detector = afsc_bot_detector.afsc_bot_detector(search_min=search_min,
        backstep=backstep)

# Read the .raw files. Only store data from the 38 and 120 kHz GPTs
print('reading raw files...')
ek60.read_raw(rawfiles, frequencies=frequencies_to_read)

# Read the .bot files.
print('reading bot files...')
ek60.read_bot(botfiles)



# Get a reference to the raw_data object for specified channels.
raw_data = ek60.get_channel_data(frequencies=frequencies_to_read)

# Grab the first raw_data object for each frequency
raw_data_38 = raw_data[38000][0]
raw_data_120 = raw_data[120000][0]

# Get calibration objects
cal_obj_38 = raw_data_38.get_calibration()
cal_obj_120 = raw_data_120.get_calibration()

# Get Sv data.
Sv_38 = raw_data_38.get_Sv(calibration=cal_obj_38)
Sv_120 = raw_data_120.get_Sv(calibration=cal_obj_120)

# Apply heave correction to the Sv data. This will also transform the
# vertical axis from range to depth since heave correction implies a
# depth grid.
Sv_38.heave_correct()
Sv_120.heave_correct()

# Get the sounder detected bottom data. Sounder deteced bottom as recorded
# in .bot, .out, and .xyz files are always on a depth grid and they always
# contain heave correction if heave data were input into the EK60/EK80
# system when the data were recorded.
bottom_38 = raw_data_38.get_bottom(calibration=cal_obj_38)
bottom_120 = raw_data_120.get_bottom(calibration=cal_obj_120)

#  now use our simple bottom detector to pick a bottom line for the 38. The bottom
#  detector class returns a pyEcholab2 Line object representing the bottom.
bottom_38_detected = bot_detector.detect(Sv_38)

#  Set this line's color to purple
bottom_38_detected.color = [1,1,0]

#  and pick the 120 and give it a purple color
bottom_120_detected = bot_detector.detect(Sv_120)
bottom_120_detected.color = [1, 1, 0]


# Create matplotlib figures and display the results.
fig_38 = figure()
eg = echogram.Echogram(fig_38, Sv_38, threshold=[-70, -34])
fig_38.suptitle("Heave Corrected - 38kHz", fontsize=14)
eg.axes.set_title("With sounder detected (yellow) and software detected " +
        "(purple) bottom lines", fontsize=10)
eg.add_colorbar(fig_38)
eg.plot_line(bottom_38, linewidth=2)
eg.plot_line(bottom_38_detected, linewidth=2)

fig_120 = figure()
eg = echogram.Echogram(fig_120, Sv_120, threshold=[-70, -34])
fig_120.suptitle("Heave Corrected - 120kHz", fontsize=14)
eg.axes.set_title("With sounder detected (yellow) and software detected " +
        "(purple) bottom lines", fontsize=10)
eg.add_colorbar(fig_120)
eg.plot_line(bottom_120, linewidth=2)
eg.plot_line(bottom_120_detected, linewidth=2)

show()

