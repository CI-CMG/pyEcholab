# -*- coding: utf-8 -*-
"""
create_test_data_snippets.py

This script can be used to pare down data files to be included in the
test suite data. It also serves as a simple example of using the echosounder
module to read lists of mixed EK60 and EK80 style files.

The script sequentially reads all .raw files in the provided source directory
and it writes subsets of those files in the provided destination directory.

"""

import os
import glob
import numpy as np
from echolab2.instruments import echosounder


# Define the parameters used to create the the index array used to write the
# subset of data as well as the input and output file paths.

# Specify the start ping
start_ping = 0

# Specify the end ping (in Python's way, this end is exclusive)
end_ping = 50

# Set the ping stride
ping_stride = 1

# specify the input file directory. All raw files in this directory will be snipped.
in_path = './data/source/'

# specify the output file directory. The snipped files will be written here.
out_path = './data/'



#-------------------------------------------------------------------------------------#

# get a list of raw file filenames
in_files = glob.glob(os.path.normpath(in_path + '/*.raw'))

# Create an index array that defines the subset of pings we want to write.
write_idx = np.arange(start_ping, end_ping, ping_stride)

# Because we're going to write subsets of the files above, and we don't know
# anything about these files at this point, we're going to keep it simple and
# read and write one file at a time. We could use echosounder.read() to read
# multiple files at once, eliminating the need for this for loop, but because
# we want complete control over the output fileame and we don't know what we're
# reading, it is just easier to do it this way.
for in_file in in_files:

    # We'll still use echosounder.read() to read our file. This method will attempt
    # to determine file type by reading the first few bytes and then use the correct
    # instrument class to read the file. It will return a list of instrument objects
    # where the number and type of objects in the list depend on the data you read.
    # In our case we're reading a single file so we know that there will only be one
    # EK60 or one EK80 object returned in the list.
    this_file = os.path.normpath(in_path + in_file)
    raw_data_ojbs = echosounder.read(in_file)

    # Now work through the data objects and write the new files
    for data_obj in raw_data_ojbs:

        # The data objects themselves will contain a list of

        # get the input file name and path. This data is replicated across
        # all channels so it doesn't matter which channel we get it from.
        infile_name = data_obj.raw_data[data_obj.channel_ids[0]][0].configuration[write_idx[0]]['file_name']
        infile_path = data_obj.raw_data[data_obj.channel_ids[0]][0].configuration[write_idx[0]]['file_path']

        # split the filename and create the output filename
        infile_root, infile_ext = os.path.splitext(infile_name)
        outfile_name = os.path.normpath(out_path + os.path.sep + infile_root + '_test' + infile_ext)

        # The write method will accept an output filename in one of two forms. If you
        # provide a string, it will behave like the ER60/EK80 software where you provide
        # the filename prefix and the write method will append the date/time of the first
        # "ping" in the file. If you provide a dict, keyed by input file name, it will
        # expect the value to be the full path and filename - nothing will be appended.
        #
        # In our case here, we don't want dates/times so we're going to pass the write
        # method a dict with the full output file name we just created.
        out_file_dict = {infile_name:outfile_name}

        # Now write the data.
        #
        # You can pass raw_index_array either a dict, numpy array containing indices to write
        # (aka index array), or a boolean numpy array where the pings that map to the True
        # elements will be written. If you provide an index or boolean array, it is assumed
        # that those values map to all channels in the EKx0 object. You can pass a dict keyed
        # by channel ID, that maps an index or boolean array to that specific channel. The
        # latter allows you control over what pings are written to the individual channels.
        # In this example we are passing an index array.
        files_written = data_obj.write_raw(out_file_dict, overwrite=True, raw_index_array=write_idx)

        # and report that we're done.
        for fname in files_written:
            print('Done writing ' + fname)

