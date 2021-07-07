# -*- coding: utf-8 -*-
"""Reads raw and bot files and plots data.

This script is an echolab2 example demonstrating how to read raw and bot
files and plot echograms of the data. It demonstrates the basics of reading
raw and bottom data, getting a calibration object, altering a cal parameter,
then getting Sv and bottom data in displaying it in various ways.

The EK80 class shares the same API for reading .bot files.

Definitions:

  The following attribute names are used in this example and they are
  defined here for clarity.

    transducer_offset is the vertical position of the transducer WITHOUT
    heave applied. It is a combination of the transducer_z_offset and the
    transducer_depth (EK60) or drop_keel_offset or water_level_draft (EK80)

    heave is the dynamic vertical displacement of your sampling platform
    provided by yor platform's AHRS/IMU and as recorded by the EK60/EK80.

    transducer_draft is the vertical position of the transducer WITH heave
    applied:

        transducer_draft = transducer_offset + heave


The key takeaways:

 1) Bottom data must be read *after* its corresponding raw data. Bottom
    data will be matched to an existing "ping". If that ping doesn't
    exist, the bottom data value will be discarded.

 2) Keep your vertical axes consistent. Bottom detections are always
    returned as depth with heave correction applied (if heave data were
    available at the time of recording.) You must adjust the bottom line
    accordingly depending on the vertical axis of your sample data and
    whether or not heave correction has been applied to it. This can be
    done using the transducer_draft attribute of the bottom detection
    lines and the transducer_offset attribute of your processed_data
    object.

 3) If you change any parameters in the calibration object you must
    pass it using the "calibration" keyword when "getting" data from
    a raw_data object. In no calibration is provided, those methods
    will use the parameters from the .raw file.

"""

from matplotlib.pyplot import figure, show
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


# Create a list of .raw files.
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw']

# Also create a list of corresponding .bot files.
botfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.bot']

# Create an instance of EK60.
ek60 = EK60.EK60()

# Read the .raw files. Only store the 38 and 120 kHz data.
print('reading raw files...')
ek60.read_raw(rawfiles, frequencies=[38000, 120000])

# Read the .bot files using the EK60.read_bot() method. Note that
# you have to read the .raw files first before reading the corresponding
# bot file.
print('reading bot files...')
ek60.read_bot(botfiles)

# Get a reference to the raw_data objects for our two frequencies.
# Calling get_channel_data while specifying the frequency or
# frequencies (as list) will return a dict keyed by frequency
# where the values are a list data objects associated with that
# frequency.
raw_data = ek60.get_channel_data(frequencies=[38000,120000])

# Get references to the 38 and 120 kHz data objects.
# Remember that calls to ek60.get_channel_data return a dictionary
# of *lists* where the lists contain the data for the specified
# channel by datatype. We know the example file contains a single
# raw datatype so we can assume there will be one and only one
# raw_data object per frequency.
raw_data_38 = raw_data[38000][0]
raw_data_120 = raw_data[120000][0]

# Create calibration objects for each channel. Calling
# raw_data.get_calibration() will return a calibration object
# populated from the raw_data object. You are free to change
# any or all of the calibration parameters as required.
cal_38 = raw_data_38.get_calibration()
cal_120 = raw_data_120.get_calibration()

# For fun, we'll provide our own sound speed. You can either provide
# calibration parameters as a scalar, in which case the value will
# be used for all pings or you can provide a ping-by-ping value.
# Here we'll just set a static value.
cal_38.sound_velocity = 1475
cal_120.sound_velocity = 1475

# Get Sv data on a range grid.
Sv_38 = raw_data_38.get_Sv(calibration=cal_38)
Sv_120 = raw_data_120.get_Sv(calibration=cal_120)

## Apply heave correction. You must pass a calibration object to
## the processed_data.heave_correct() method.
## NOTE - applying heave correction will convert the processed_data
##        object's vertical axis from range to depth.
#Sv_38.heave_correct(cal_38)
#Sv_120.heave_correct(cal_120)

# Now get the bottom detection data - raw_data.get_bottom() returns
# an echolab2 line object representing the bottom detections.
#
# Since we have modified the calibration object (by setting the
# sound speed) we must pass it to the get_bottom method to ensure
# the new sound speed value is used. The get_bottom() method will
# adjust the data values based on the difference between the recorded
# sound speed and the value in the calibration object.
#
# IMPORTANT! - Bottom detections are *always* returned as depth with
#              heave corrections applied (if data were available at the
#              time of recording.)

bottom_38_as_depth_w_heave = raw_data_38.get_bottom(calibration=cal_38)
bottom_120_as_depth_w_heave = raw_data_120.get_bottom(calibration=cal_120)

# Set the color of our DEPTH_WITH_HEAVE lines to yellow
bottom_38_as_depth_w_heave.color = [1, 1, 0]
bottom_120_as_depth_w_heave.color = [1, 1, 0]

# We'll first display the data on a range grid. The vertical axis for the
# Sv data is already in range, but as stated above, the bottom detection
# data read from the .bot file will have transducer offset and heave (if
# available) applied. We first have to back those out from the bottom
# lines.
#
# In echolab transducer_draft = transducer_offset + heave
#
# When we sbtract the transducer_draft we remove both the offset and heave
# which results in a line in RANGE. For convienience the transducer_draft
# data is included as attributes of the line object by the get_bottom() method:
bottom_38_as_range = bottom_38_as_depth_w_heave - \
        bottom_38_as_depth_w_heave.transducer_draft
bottom_120_as_range = bottom_120_as_depth_w_heave - \
        bottom_120_as_depth_w_heave.transducer_draft

# Set the color of our RANGE lines to purple
bottom_38_as_range.color = [1, 0, 1]
bottom_120_as_range.color = [1, 0, 1]

# Create matplotlib echograms and plot the data on a RANGE grid
# Plot the bottom detections as range as a purple line
# We also plot the detected bottom line that includes heave as a yellow line
fig_38 = figure()
eg = echogram.Echogram(fig_38, Sv_38, threshold=[-70, -34])
eg.axes.set_title("38 kHz on Range grid")
eg.plot_line(bottom_38_as_range, linewidth=2)
eg.plot_line(bottom_38_as_depth_w_heave, linewidth=2)

fig_120 = figure()
eg = echogram.Echogram(fig_120, Sv_120, threshold=[-70, -34])
eg.axes.set_title("120 kHz on Range grid")
eg.plot_line(bottom_120_as_range, linewidth=2)
eg.plot_line(bottom_120_as_depth_w_heave, linewidth=2)


# Now plot the data on a DEPTH grid. The first thing to do is convert
# the Sv data to a depth grid. This is done by calling the
# processed_data.to_depth() method.
Sv_38.to_depth()
Sv_120.to_depth()

# Next we have to back out the heave from the bottom line. Line
# objects contain the transducer_draft attribute which is a combination
# of transducer_offset and heave so that doesn't help us here. But,
# processed data objects have the heave attribute if heave data were
# recorded so we can use that.
if hasattr(Sv_38, 'heave'):
    # heave data are available so we need to back that it out
    bottom_38_as_depth = bottom_38_as_depth_w_heave - Sv_38.heave
    # heave is global, so if one channel has it, all channels will
    # so we don't have to check the 120.
    bottom_120_as_depth = bottom_120_as_depth_w_heave - Sv_120.heave
else:
    # No heave data available which means no heave would have been
    # applied to the bottom detections so bottom_38_as_depth_w_heave
    # is depth without heave. Same for the 120 kHz.
    bottom_38_as_depth = bottom_38_as_depth_w_heave
    bottom_38_as_depth = bottom_38_as_depth_w_heave

# Set the color of our DEPTH lines to green
bottom_38_as_depth.color = [0, 1, 0]
bottom_38_as_depth.color = [0, 1, 0]


# Create matplotlib echograms and plot the data on a DEPTH grid
# Plot the bottom detections as range as a purple line
# Plot the bottom detections as depth without heave as a green line.
# We also plot the detected bottom line that includes heave as a yellow line
fig_38 = figure()
eg = echogram.Echogram(fig_38, Sv_38, threshold=[-70, -34])
eg.axes.set_title("38 kHz on Depth grid")
eg.plot_line(bottom_38_as_range, linewidth=2)
eg.plot_line(bottom_38_as_depth, linewidth=2)
eg.plot_line(bottom_38_as_depth_w_heave, linewidth=2)

fig_120 = figure()
eg = echogram.Echogram(fig_120, Sv_120, threshold=[-70, -34])
eg.axes.set_title("120 kHz on Depth grid")
eg.plot_line(bottom_120_as_range, linewidth=2)
eg.plot_line(bottom_120_as_depth, linewidth=2)
eg.plot_line(bottom_120_as_depth_w_heave, linewidth=2)


show()

