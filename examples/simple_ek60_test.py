# -*- coding: utf-8 -*-
"""A simple ek60 test.

This example script demonstrates simple file reading and data plotting of ek60
data.  In general, the script reads files passed to it, stores the data in
a data object, parses specific pieces of information from the data,
and generates plots.  More specifically, this script demonstrates processes
such as retrieving specific types of data (power, Sv, angles) from specified
channels/frequencies, appending and inserting data from different sample
intervals, and plotting multiple echograms on multiple matplotlib figures.
"""

from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


# Create the list of input files.  For this test we purposely picked two files
# with the same channels, but with different pulse lengths and a different
# installation order.

# The descriptions below apply to reading these 2 files in the following order.
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw',
            './data/EK60/DY1706_EK60-D20170609-T005736.raw']

# Create a matplotlib figure to plot our echograms on.
fig = figure()
# Set some properties for the sub plot layout.
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None,
                hspace=0.5)

# Create an instance of the EK60 instrument. This is the top level object used
# to interact with EK60 and  data sources.
ek60 = EK60.EK60()

# Use the read_raw method to read in a data file.
ek60.read_raw(rawfiles)

# Print some basic info about our object.  As you will see, 10 channels are
# reported.  Each file has 5 channels, and are in fact, physically the same
# hardware.  The reason there are 10 channels reported is because their
# transceiver number in the ER60 software changed.
print(ek60)

# Now, get a reference to the RawData object that contains data from the first
# 38 kHz channel.
raw_data_38_1 = ek60.get_raw_data(channel_number=2)

# The sample data from channel 2 is contained in a 136x994 array.  The data was
# recorded with a 1024us transmit pulse length, which on the EK60 and related
# hardware results in a sample interval of 256us (sample interval = pulse
# length / 4).  The data were recorded in 2012.

print(raw_data_38_1)

# Also get a reference to the RawData object that contains data from the
# second 38 kHz channel.
raw_data_38_2 = ek60.get_raw_data(channel_number=7)

# Channel 7's sample data is a 763x1059 array recoded with a 512us pulse length
# resulting in a sample interval of 128us.  These data were recorded in 2017.

print(raw_data_38_2)

# Append the 2nd object's data to the first and print out the results.
raw_data_38_1.append(raw_data_38_2)

# The result of this append is that raw_data_38_1 now contains data from 899
# pings.  The first 136 pings are the 2012 data and the next 763 the 2017
# data.  The sample data arrays are 899x1059 and the object contains 2 unique
# sample intervals.

print(raw_data_38_1)

# Insert the 2nd object's data into the first at ping 50.
raw_data_38_1.insert(raw_data_38_2, ping_number=50)

# Now raw_data_38_1 contains 1662 pings. Pings 1-50 are from the 2012 data.
# Pings 51-813 are the 763 pings from the 2012 data. Pings 814-899 are the
# rest of the 2012 data and pings 900-1663 are a second copy of the 2017 data.

print(raw_data_38_1)

# Create an axis.
ax_1 = fig.add_subplot(3, 1, 1)
# Create an echogram to plot up the raw sample data.
echogram_2 = echogram.echogram(ax_1, raw_data_38_1, 'power')
ax_1.set_title("Raw power as stored in raw_data object")


# At this point, we have a 1662x1059 array with data recorded at two different
# sample intervals.  When we convert this data to return a processed_data
# object, we have to resample to a constant sample interval.  By default,
# the get_* methods will resample to the shortest sample interval (highest
# resolution) in the data that is being returned.  In our case, that will
# result in the 136 pings from 2012 recorded with a sample rate of 256us
# being resampled to 128us.

# The two files were also recorded with slightly different sound speed values
# and we're not going to supply a constant sound speed (or any calibration
# values) to the get_power method so it will use the calibration parameter
# values from the raw data.  When no sound speed calibration data is provided,
# the get_* methods will resort to interpolating range using the sound speed
# that occurs most in the data (in other words, it interpolates the fewest
# pings it needs to).

# When we request data using the get_* methods, we can provide a time range or
# ping range to return data from.  Providing no constraints on the range of
# data returned will return all of the data.  By default, the data will be in
# time order. You can force the method to return data in ping order (the
# order it exists in the RawData object) by setting the time_order keyword to
# False.  Advanced indexing can be done outside of the get_* methods and
# passed into them using the return_indices keyword.


# Call get_power to get a processed data object that contains power data.  We
# provide no arguments so we get all pings ordered by time.
processed_power_1 = raw_data_38_1.get_power()
# That should be 1662 pings by 1988 samples.
print(processed_power_1)

# Create an axis.
ax_2 = fig.add_subplot(3, 1, 2)
# Create an echogram which will display on our newly created axis.
echogram_2 = echogram.echogram(ax_2, processed_power_1)
ax_2.set_title("Power data in time order")

# Now request Sv data in time order.
Sv = raw_data_38_1.get_Sv()
# This will also be 1662 pings by 1988 samples, but is Sv ordered by time.
print(Sv)

# Create another axis.
ax_3 = fig.add_subplot(3, 1, 3)
# Create an echogram which will display on our newly created axis.
echogram_3 = echogram.echogram(ax_3, Sv, threshold=[-70,-34])
ax_3.set_title("Sv data in time order")

# Show our figure.
show()

# Create another matplotlib figure.
fig = figure()
# Set some properties for the sub plot layout.
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None,
                hspace=0.5)

angle_cmap = get_cmap('plasma')

# Now request angles data in time order.
angles_along, angles_athwart = raw_data_38_1.get_physical_angles()
print(angles_along)
print(angles_athwart)

# Create another axis.
ax_1 = fig.add_subplot(2, 1, 1)
# Create an echogram which will display on our newly created axis.
echogram_3 = echogram.echogram(ax_1, angles_along, cmap=angle_cmap)
ax_1.set_title("angles_alongship data in time order")

# Create another axis.
ax_2 = fig.add_subplot(2, 1, 2)
# Create an echogram which will display on our newly created axis.
echogram_3 = echogram.echogram(ax_2, angles_athwart, cmap=angle_cmap)
ax_2.set_title("angles_athwartship data in time order")

# Show our figure.
show()


pass
