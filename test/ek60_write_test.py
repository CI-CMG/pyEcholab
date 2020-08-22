# -*- coding: utf-8 -*-
"""
ek60_write_test.py

This script can be used to test the writing of EK60 data to .raw files. It will
read in one or more .raw files, write them to disk, then read the re-written
file and compare the original to the re-written file.

A successful round trip will result in data that differs no more than +-0.0118 dB
These differences are due to the effects of converting from the 16 bit linear
sample data to the "EK500 DB Format" as 32-bit float, then back to the packed
16 bit value.

While significant effort was made to ensure the write_raw method creates sane files,
pyEcholab gives you a lot of flexibility when working with raw data and you can
quickly run into issues when combining data from different sources or modifying
data and writing the results.
"""

from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt


# This test script can and should be run with different files to test as many instrument
# configurations and file combinations as possible. There are a couple of different files
# defined below. You can change the list passed to the ek60.read_raw() method to try
# the different files below or add your own.

# Define the files that we will work with. The simplest test we can do is with a single file
# When using this input, the example will create a single output file that is functionally
# identical to the original. The script will then generate figures for each of the five
# channels in the file.
one_file = ['../examples/data/EK60/DY1706_EK60-D20170609-T005736.raw']

# Spice it up with two different files. These two files were recorded 5 years apart
# with different system settings. Further, while the hardware is the same, the transceiver
# installation is different between the two files so the EK60 class rightly treats
# them as different channels and the channel numbers for the second file are re-mapped
# (you will see this when the EK60 object is printed.) This tests the EK60 class's
# ability to identify file boundaries, group data correctly, and remap channel
# numbers back to the original values.
#
# By default, the ER60 class will write an output file for each input file you have read.
# In this case we're reading two files and we will write two files.
two_files = ['../examples/data/EK60/DY1706_EK60-D20170609-T005736.raw',
             '../examples/data/EK60/DY1201_EK60-D20120214-T231011.raw']

#  specify the output path AND file name header
out_file = 'C:/Temp_EK_Test/EK-Raw-Write-Test'

# Create an instance of the EK60 instrument. The EK60 class represents a
# collection of synchronous "ping" data, asynchronous data like GPS, motion,
# and annotation datagrams, and general attributes about this data.
ek60 = EK60.EK60()

# Use the read_raw method to read in our list of data files.
ek60.read_raw(two_files)

# Print some basic info about our object.
print(ek60)

# get references to the raw data we just read. We'll use there when we compare
# this original data with the data we have re-written.
orig_chan_data = ek60.get_channel_data()

# Write the unmodified data to disk. out_file can be a string or dict. You can
# read the docs in the ek60.write_raw method header, but for know know that if
# you pass a string, it expects it to be a path + file name header which it will
# append "-DYYYYMMDD-Thhmmss.raw". So if you pass "C:/test/EK_Test" you will get
# files like "C:/test/EK_Test-D20200101-T120015.raw". The method returns a list
# of filenames.
out_files = ek60.write_raw(out_file, overwrite=True)


# Now create a second EK60 object to contain the freshly written data
ek60rewrite = EK60.EK60()
ek60rewrite.read_raw(out_files)

# get references to the raw data we just read. The ek60.get_channel_data method
# allows you to get these references by frequency, channel ID, or channel number.
# Here we don't provide any arguments so we get back a dict, keyed by channel ID.
# containing the raw_data
rewrite_chan_data = ek60rewrite.get_channel_data()

# We'll iterate through each of the channels
for channel_id in rewrite_chan_data:
    # NOTE HERE A CHANGE IN API - Channel data is now returned as a LIST of different data types.

    # Simrad raw files can contain power, angle, power+angle, or complex data and the
    # raw_data class is designed to store a single data type. We faked it with the EK60.raw_data
    # class by making that one data type power+angle but adding EK80 support forced this
    # change. In our case here I know that we are dealing with a single data type so I
    # am going to index directly. In cases where you don't know, you would have to handle
    # this detail.

    #  grab the first (and only, in this data) datatype
    rewrite_data = rewrite_chan_data[channel_id][0]

    #  convert to Sv
    rewrite_Sv = rewrite_data.get_Sv(calibration=rewrite_data.get_calibration())
    rewrite_freq = rewrite_data.frequency[0]

    #  now get our original file's Sv - Since these files should be the same, we know
    #  we will have the same channel IDs so we'll use the id from our iterator. Also,
    # we know there is only one datatype so we index into this directly.
    orig_data = orig_chan_data[channel_id][0]

    #  convert to Sv
    orig_Sv = orig_data.get_Sv(calibration=orig_data.get_calibration())
    orig_freq = orig_data.frequency[0]


    #  now plot all of this up

    #  show the Sv echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, orig_Sv, threshold=[-70,-34])
    eg.axes.set_title("Original Sv " + str(orig_freq) + " kHz")

    fig = plt.figure()
    eg = echogram.Echogram(fig, rewrite_Sv, threshold=[-70,-34])
    eg.axes.set_title("Rewrite Sv " + str(rewrite_freq) + " kHz")

    #  compute the difference
    diff = orig_Sv - rewrite_Sv
    fig = plt.figure()
    eg = echogram.Echogram(fig, diff, threshold=[-0.25,0.25])
    eg.axes.set_title("Original Sv - Reqrite Sv " + str(orig_freq) + " kHz")

    #  plot up a single Sv ping
    fig2 = plt.figure()
    plt.plot(orig_Sv[-1], orig_Sv.range, label='Original', color='blue', linewidth=1.5)
    plt.plot( rewrite_Sv[-1], rewrite_Sv.range, label='Rewrite', color='red', linewidth=1)
    plt.gca().invert_yaxis()
    fig2.suptitle("Ping " + str(rewrite_Sv.n_pings) + " comparison original vs pyEcholab2 re-write")
    plt.xlabel("Sv (dB)")
    plt.ylabel("Range (m)")
    plt.legend()

    # Show our figures.
    plt.show()

print()
