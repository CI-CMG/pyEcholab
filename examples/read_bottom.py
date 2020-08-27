# -*- coding: utf-8 -*-
"""Reads raw and bot/out files and plots data.

This script is an echolab2 example demonstrating how to read raw and bot/out
files and plot echograms of the data. It demonstrates the basics of reading
raw and bottom data, getting a calibration object, altering a cal parameter,
then getting Sv and bottom data in displaying it in various ways.

The key takeaways:

 1) Bottom data must be read *after* its corresponding raw data. Bottom
    data will be matched to an existing "ping". If that ping doesn't
    exist, the bottom data value will be discarded.

 2) Keep your vertical axes consistent. If you get Sv on a range axis
    and a bottom line on a depth axis, they're not going to line up.

 3) If you change any parameters in the calibration object you must
    pass it using the "calibration" keyword when "getting" data from
    a raw_data object. In no calibration is provided, those methods
    will use the parameters from the .raw file.

 4) Views can be used to work with slices of your data. Not just for
    literal viewing as an echogram but also for processing.

"""

from matplotlib.pyplot import figure, show
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


# Specify the color of the bottom line
line_color = [1, 1, 0]

# Create a list of .raw files.
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw']

# Also create a list of corresponding .bot files.
botfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.bot']

# Create an instance of EK60.
ek60 = EK60.EK60()

# Read the .raw files. Only store the 38 and 120 kHz data.
print('reading raw files...')
ek60.read_raw(rawfiles, frequencies=[38000, 120000])

# Read the .bot files.
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
print(cal_38)
cal_120 = raw_data_120.get_calibration()
print(cal_120)

# For fun, we'll provide our own sound speed. You can either provide
# calibration parameters as a scalar, in which case the value will
# be used for all data pings or you can provide a ping-by-ping value.
# Here we'll just set a static value.
cal_38.sound_velocity = 1475
cal_120.sound_velocity = 1475

# Get Sv data.
Sv_38 = raw_data_38.get_Sv(calibration=cal_38)
Sv_120 = raw_data_120.get_Sv(calibration=cal_120)

# Apply heave correction. You must pass a calibration object to
# the processed_data.heave_correct() method.
# NOTE - applying heave correction will convert the processed_data
#        object's vertical axis from range to depth.
Sv_38.heave_correct(cal_38)
Sv_120.heave_correct(cal_120)

# Now get the bottom detection data - raw_data.get_bottom() returns
# a echolab2 line object representing the bottom detections.
# We set the return_depth keyword to return the line as depth.
# Also, since we have modified the calibration object (by setting
# the sound speed) we must pass it to the get_bottom method to
# ensure the new sound speed value is used.
bottom_38 = raw_data_38.get_bottom(calibration=cal_38, return_depth=True)
bottom_120 = raw_data_120.get_bottom(calibration=cal_120, return_depth=True)

# We'll change the color of our lines to yellow

bottom_38.color = line_color
bottom_120.color = line_color

# Create matplotlib figures and display the results.
fig_38 = figure()
eg = echogram.Echogram(fig_38, Sv_38, threshold=[-70, -34])
eg.axes.set_title("Heave Corrected with Detected Bottom - 38kHz")
eg.plot_line(bottom_38, linewidth=2.5)

fig_120 = figure()
eg = echogram.Echogram(fig_120, Sv_120, threshold=[-70, -34])
eg.axes.set_title("Heave Corrected with Detected Bottom - 120kHz")
eg.plot_line(bottom_120, linewidth=2.5)

show()


# Now read ES60 data with .out files.  There is usually not a 1-1
# relationship between .out and .raw files so you have to use the file name
# to determine which .raw files are associated with an out file.

# Create a list of .raw files.
rawfiles = ['./data/ES60/L0226-D20170624-T143908-ES60.raw',
            './data/ES60/L0226-D20170624-T155849-ES60.raw']
# Also create a list of .out files.
botfiles = ['./data/ES60/L0226-D20170624-T143908-ES60.out']

# Create an instance of ER60.
ek60 = EK60.EK60()

# Read the .raw files.
print('reading raw files...')
ek60.read_raw(rawfiles)

# Read the .bot files.
print('reading out files...')
ek60.read_bot(botfiles)

# Get the references to our data. If we provide no arguments
# to get_channel_data we'll get a dict keyed by channel ID.
raw_data = ek60.get_channel_data()

# We can iterate through the channels and plot the echogram
for chan in raw_data:
    # Again, we assume there is only 1 data type
    data = raw_data[chan][0]

    # Get a cal obj for this data
    cal_obj = data.get_calibration()

    # Again, we'll set the sound speed
    cal_obj.sound_velocity = 1475.3
    print(cal_obj)

    # Get Sv - If we don't specify the return_depth keyword the
    # vertical axis of the returned object will be range.
    Sv = data.get_Sv(calibration=cal_obj)

    # Get the bottom detections as a line - default is to return
    # the line as range. Again, gotta also pass the cal_object because
    # we changed the sound speed. get_bottom will automatically adjust
    # the bottom detection values based on the recorded sound speed and
    # the sound speed provided in the calibration object.
    bottom = data.get_bottom(calibration=cal_obj, color=line_color)

    #  Get our channel's frequnecy in kHz
    freq = int(data.configuration[0]['frequency'] / 1000)

    # Plot the full echogram as range.
    fig_1 = figure()
    eg = echogram.Echogram(fig_1, Sv, threshold=[-70, -34])
    eg.axes.set_title("Full echogram with bottom as range - " + str(freq) + ' kHz')
    eg.plot_line(bottom, linewidth=-1)

    # Convert the vertical axes to depth
    Sv.to_depth(cal_obj)

    # Get the bottom as depth.
    bottom = data.get_bottom(calibration=cal_obj, return_depth=True,
            color=line_color)
    print(Sv)
    print(bottom)

    # Plot a second figure that provides a zoomed view of our data. We use the
    # view method of the processed_data object. You specify the time slice
    # (start, stop, stride) and the sample slice (start, stop, stride)

    # Create the view including all pings and samples 1-500.
    Sv_38_view = Sv.view((None, None, None), (0, 500, None))

    # And create the echogram figure to show it
    fig_2 = figure()
    eg = echogram.Echogram(fig_2, Sv_38_view, threshold=[-70, -34])
    eg.axes.set_title("Zoomed view with bottom(samples 1-500) as depth - " + str(freq) + ' kHz')
    eg.plot_line(bottom, linewidth=-1)

    show()
