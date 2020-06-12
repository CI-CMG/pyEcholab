# -*- coding: utf-8 -*-
"""A simple ek60 reader test.

This script demonstrates simple file reading and plotting of ek60 data.  In
general, the script reads files passed to it, stores data in a data object,
parses information from the data, and generates plots.  Specifically,
this script demonstrates processes such as retrieving values from the data (
power, Sv, and angles from specified channels/frequencies), appending and
inserting data from different sample intervals, and using matplotlib to
plot echograms.
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
subplots_adjust(left=0.11, bottom=0.1, right=0.98, top=.93, wspace=None,
                hspace=0.9)

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

# A digression - .raw files can contain power, angle, power AND angle, or with
# EK80 hardware complex data. Following this, raw_data objects can contain power,
# angle, power AND angle, or complex data. If a new data type is encountered while
# reading data from a specific channel ID, a new raw_data object is created for
# that data. If you look at the output of the print() statmement above, you will
# see that data type listed after the channel ID.

# Now, get a reference to the raw_data objects that contain data at 38 kHz. Since
# we read data at 38 kHz from two channels, this will return a list 2 items long.
# Each item in this list will be a list containing the raw_data objects containing the
# 38 kHz data associate with a channel. These inner lists will contain a raw_data
# object for each of the distinct data types (described above) encountered in the
# raw files. In this example the data files only have power/angle data so there
# will only be a single raw_data object.
raw_data_38 = ek60.get_raw_data(frequency=38000.0)

# When working with this library, you are either going to know something about the
# data you are reading and you will be able to make assumptions about the list that
# is returned or you'll know nothing and need to iterate through both the outer and
# inner lists. Here we know that the outer list is 2 elements long and each inner
# list is 1 element long.
raw_data_38_1 = raw_data_38[0][0]
raw_data_38_2 = raw_data_38[1][0]


# The sample data from the first 38 kHz channel is contained in a 136x994 array.
# The data was recorded with a 1024us transmit pulse length, which on the EK60
# and related hardware results in a sample interval of 256us (sample interval = pulse
# length / 4). The data were recorded in 2012.
print(raw_data_38_1)

# The sample data from the first 38 kHz channel is contained in a 763x1059 array
# recoded with a 512us pulse length resulting in a sample interval of 128us.
# These data were recorded in 2017.
print(raw_data_38_2)

# Append the 2nd object's data to the first and print out the results.
raw_data_38_1.append(raw_data_38_2)

# The result of this append is that raw_data_38_1 now contains data from 899
# pings. The first 136 pings are the 2012 data and the next 763 the 2017
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
echogram_2 = echogram.Echogram(ax_1, raw_data_38_1, 'power')
ax_1.set_title("Raw power as stored in RawData object")


# At this point, we have a 1662x1059 array with data recorded at two different
# sample intervals.  When we convert this data to return a ProcessedData
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


# Call get_power to get a ProcessedData object that contains power data.  We
# provide no arguments so we get all pings ordered by time.
processed_power_1 = raw_data_38_1.get_power()
# That should be 1662 pings by 1988 samples.
print(processed_power_1)

# Create an axis.
ax_2 = fig.add_subplot(3, 1, 2)
# Create an echogram which will display on our newly created axis.
echogram_2 = echogram.Echogram(ax_2, processed_power_1)
ax_2.set_title("Power data in time order")

# Now request Sv data in time order.
Sv = raw_data_38_1.get_Sv()
# This will also be 1662 pings by 1988 samples, but is Sv ordered by time.
print(Sv)

# Create another axis.
ax_3 = fig.add_subplot(3, 1, 3)
# Create an echogram which will display on our newly created axis.
echogram_3 = echogram.Echogram(ax_3, Sv, threshold=[-70,-34])
ax_3.set_title("Sv data in time order")

# Show our figure.
show()

# Create another matplotlib figure.
fig = figure()
# Set some properties for the sub plot layout.
subplots_adjust(left=0.1, bottom=0.1, right=0.98, top=.93, wspace=None,
                hspace=0.5)

angle_cmap = get_cmap('plasma')

# Now request angles data in time order.
angles_along, angles_athwart = raw_data_38_1.get_physical_angles()
print(angles_along)
print(angles_athwart)

# Create another axis.
ax_1 = fig.add_subplot(2, 1, 1)
# Create an echogram which will display on our newly created axis.
echogram_3 = echogram.Echogram(ax_1, angles_along, cmap=angle_cmap)
ax_1.set_title("angles_alongship data in time order")

# Create another axis.
ax_2 = fig.add_subplot(2, 1, 2)
# Create an echogram which will display on our newly created axis.
echogram_3 = echogram.Echogram(ax_2, angles_athwart, cmap=angle_cmap)
ax_2.set_title("angles_athwartship data in time order")

# Show our figure.
show()


pass
