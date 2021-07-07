# -*- coding: utf-8 -*-
"""
combine_ek60_rawfiles is an example showing how to combine two different
raw files into a single raw file. It reads the two files, writes a combined
file to disk, then reads this combined file and plots the original and
re-written data. It also provides a simple example of using the progress
callback.

When writing raw files, the EK60 writer uses data in the channel configuration
dictionary to determine how many unique files to write. This is done to
ensure that the correct parameters are written to the raw file configuration
header and results in the writer creating the same number of files as were
originally read.

This means that if one wants to combine two or more files, the references
to the configuration data must be updated in all raw_data objects to point
to a single configuration dictionary. Obviously this should only be done
when you know that the files you are combining were all recorded using
the same system parameters (There is *some* wiggle room here but you really
need to know what you are doing if you stray outside the lines.)


"""
import sys
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
import matplotlib.pyplot as plt



def read_write_callback(filename, cumulative_pct, cumulative_bytes, userref):
    '''
    read_write_callback is a simple example of using the progress_callback
    functionality of the EK60.read_raw and EK60.write_raw methods.
    '''

    if cumulative_pct > 100:
        return

    if cumulative_pct == 0:
        sys.stdout.write(filename)

    if cumulative_pct % 4:
        sys.stdout.write('.')

    if cumulative_pct == 100:
        sys.stdout.write('  done!\n')


# Specify the raw files to combine
combine_files = ['./data/OfotenDemo-D20001214-T145902.raw',
                 './data/OfotenDemo-D20001214-T154020.raw']


# specify the output path AND file name header. write_raw() will
# generate an output file name using this in a similar manner as
# the ER60 software. The actual file written will be named:
#
#   './Ofoten-Combined-Test-DYYYYMMDD-Thhmmss'
#
# where the date and time will be determined by the time of the first
# raw datagram in the file. This may or may not exactly match the first
# input file's time.
out_file = './Ofoten-Combined-Test'

# Create an instance of the EK60 instrument.
ek60 = EK60.EK60()

# Use the read_raw method to read in our list of data files.
print('Reading source file(s):')
ek60.read_raw(combine_files, progress_callback=read_write_callback)

# Print some basic info about our object.
print(ek60)

# get references to the raw data we just read. Calling get_channel_data without
# arguments will return all channels in a dict keyed by channel ID
orig_chan_data = ek60.get_channel_data()

# The write_raw method uses the .raw file configuration data to determine
# how data is grouped into files when writing. This is done to ensure that
# all files have the correct configuration data. In cases where we want to
# combine data from multiple .raw files into a single file, we need to
# update the references to the configuration data for all channels such that
# they point to the same data.
#
# Note that you should only do this if you know all the files you are
# combining share the same configuration data. If they don't, it is up to
# you to ensure you create valid .raw files.

# iterate through the channels
for chan in orig_chan_data:
    # iterate through the data types associated with this channel
    for data in orig_chan_data[chan]:
        # make all of the configuration references for this raw_data
        # object point to configuration from the first ping in the
        # first file that we read.
        data.configuration[:] = data.configuration[0]


# Now write our file. Only 1 file will be written.
print('Writing combined file:')
out_files = ek60.write_raw(out_file, overwrite=True, progress_callback=read_write_callback)


# Now create a second EK60 object to contain the freshly written data
print('Reading combined file:')
ek60rewrite = EK60.EK60()
ek60rewrite.read_raw(out_files, progress_callback=read_write_callback)

# get references to the raw data we just read.
rewrite_chan_data = ek60rewrite.get_channel_data()

# We'll iterate through each of the channels

for channel_id in rewrite_chan_data:
    # For this example we will assume there is only 1 datatype per channel
    # and we will reference that directly in our code below.
    print('Plotting channel ' + channel_id)

    #  grab the first datatype
    rewrite_data = rewrite_chan_data[channel_id][0]

    #  convert to Sv
    rewrite_Sv = rewrite_data.get_Sv(calibration=rewrite_data.get_calibration())
    rewrite_freq = rewrite_data.frequency[0]

    # now get our original file's Sv - Since these files should be the same, we know
    # we will have the same channel IDs so we'll use the id from our iterator. Also,
    # we know there is only one datatype so we index into this directly.
    orig_data = orig_chan_data[channel_id][0]

    #  convert to Sv
    orig_Sv = orig_data.get_Sv(calibration=orig_data.get_calibration())
    orig_freq = orig_data.frequency[0]

    #  now plot all of this up - create the Sv echograms
    fig = plt.figure()
    eg = echogram.Echogram(fig, orig_Sv, threshold=[-70,-34])
    eg.axes.set_title("Original Sv " + str(int(round(orig_freq/1000.,0))) + " kHz")

    fig = plt.figure()
    eg = echogram.Echogram(fig, rewrite_Sv, threshold=[-70,-34])
    eg.axes.set_title("Rewrite Sv " + str(int(round(rewrite_freq/1000.))) + " kHz")

    # Show our figures.
    plt.show()

print('done')
