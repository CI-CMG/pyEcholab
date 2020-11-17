# -*- coding: utf-8 -*-
"""
ek60_subsample_and_write.py

This example shows how to use the advanced indexing option for raw data
when calling ek60.write_raw() to create a raw file that contains a
subset of data contained in the original files.

It also demonstrates using match_pings to plot the subsampled data on
the same time axis as the original data.

"""
import numpy as np
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt


# Starting at the first ping, subsample 50 pings then skip 100, and repeat
# until the end of the file.
start_ping = 1
subsample_n_pings = 50
skip_n_pings = 100

# Specify the in file(s) to subsample
in_files = ['../examples/data/EK60/OfotenDemo-D20001214-T145902.raw',
            '../examples/data/EK60/OfotenDemo-D20001214-T154020.raw',
            '../examples/data/EK60/OfotenDemo-D20001214-T162003.raw',
            '../examples/data/EK60/OfotenDemo-D20001214-T164709.raw']

# Specify the output path and subsampled raw file base name. The write
# method will add the date and time.
out_dir = 'C:/Temp_EK_Test/subsample_1'

# Create an instance of the EK60 instrument.
ek60 = EK60.EK60()

# Use the read_raw method to read in our list of data files.
ek60.read_raw(in_files)

# get references to the raw data we just read. We'll use there when we compare
# this original data with the data we have re-written.
orig_chan_data = ek60.get_channel_data()

# When calling the ek60.write_raw() method, you can pass in a collection of
# index arrays that specify what data to write. This allows you to write data
# in non-contiguous chunks without having to modify the underlying data.


# Create the empty raw index dictionary. This will be keyed by channel ID
# and contain the boolean array identifying the pings to write.
raw_index_array = {}

# At this point it is up to you as to how to create your index arrays. For
# this example I'll write 50 pings, then skip 100, and write 50 and skip
# 100 and so on. We'll just brute force this and iterate through the channels
# and build an index for each one.

# first, iterate through the channels we have read
for channel in ek60.raw_data:
    # And then the data objects associated with each channel
    for data in ek60.raw_data[channel]:

        # Create the boolean array we'll use to specify the pings to write
        n_pings = data.ping_time.shape[0]
        idx_array = np.full(data.ping_time.shape, 0, np.bool_)

        # I'm sure there is a clever way to set the blocks but
        # we'll do it the hard way.
        n_loops = np.ceil((n_pings - start_ping) / (subsample_n_pings + skip_n_pings))
        n_loops = n_loops.astype(int)

        for i in range(n_loops):
            # calculate the start for this block
            start = start_ping + (i * (subsample_n_pings + skip_n_pings)) - 1
            # and the end
            end = start + subsample_n_pings
            idx_array[start:end] = True

        # set the index array for this raw_data object
        raw_index_array[data] = idx_array

        # Since we want to combine multiple raw files in our
        # subsampled file, we need to make sure *all* of the
        # configuration references are the same. This tricks
        # the writer into writing all of the data into a single
        # file. It is up to you to ensure that the individual files
        # were all created with the same configuration params.
        # If this is not the case, the data in the file you
        # write will not be interpreted correctly.
        #
        # If you comment this line, you should get an output
        # file for each input file specified above.
        data.configuration[:] = data.configuration[0]


# Write the subsampled file. The key is that we're passing the
# boolean array that specifies the pings to write. In theory this
# should work with an index array too (array that contains index
# numbers instead of True/False.) I haven't tested that yet.
out_files = ek60.write_raw(out_dir, raw_index_array=raw_index_array,
        overwrite=True)


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

    #  grab the first raw_data object
    rewrite_data = rewrite_chan_data[channel_id][0]

    #  convert to Sv
    rewrite_Sv = rewrite_data.get_Sv(calibration=rewrite_data.get_calibration())
    rewrite_freq = rewrite_data.frequency[0]

    #  now get our original file's Sv - Since these files should be the same, we know
    #  we will have the same channel IDs so we'll use the id from our iterator. Also,
    #  we know there is only one datatype so we index into this directly.
    orig_data = orig_chan_data[channel_id][0]

    #  convert to Sv
    orig_Sv = orig_data.get_Sv(calibration=orig_data.get_calibration())
    orig_freq = orig_data.frequency[0]

    # To illustrate the subsampling, we'll match the subsampled data to the
    # original. The missing pings will be replaced with NaNs in the echogram.
    rewrite_Sv.match_pings(orig_Sv)

    #  show the Sv echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, orig_Sv, threshold=[-70,-34])
    eg.axes.set_title("Original Sv " + str(orig_freq) + " kHz")

    fig = plt.figure()
    eg = echogram.Echogram(fig, rewrite_Sv, threshold=[-70,-34])
    eg.axes.set_title("Matched rewrite Sv " + str(rewrite_freq) + " kHz")

    # Show our figures.
    plt.show()
