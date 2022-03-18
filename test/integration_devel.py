# -*- coding: utf-8 -*-
"""
"""


from echolab2.instruments import echosounder
from echolab2.processing import mask, line, grid
import numpy as np


# specify some data files
rawfiles = ['../examples/data/EK60/DY1706_EK60-D20170625-T062521.raw',
            '../examples/data/EK60/DY1706_EK60-D20170625-T063335.raw']

# and the matching bottom files.
botfiles = ['../examples/data/EK60/DY1706_EK60-D20170625-T062521.bot',
            '../examples/data/EK60/DY1706_EK60-D20170625-T063335.bot']

#  specify an Echoview cal file
ecs_file = 'C:/EK Test Data/DY2104 final settings.ecs'

# Use the echosounder function read our data. This function figures
# out what format the data is in (EK60 or EK80), creates the correct
# object and reads the data.
print('Reading the raw files...')
echosounder_data = echosounder.read(rawfiles, frequencies=[38000])

# The echosounder function returns a list of echolab2 instrument objects
# containing the data read from the files you passed it. Assuming
# you are reading data files collected with the same general settings
# there will always be a single object in the list so it's convenient
# to unpack it here.
echosounder_data = echosounder_data[0]

# Now, if you read some EK80 files and some EK60 files and some files
# had complex, others power/angle you're going to have a bunch of objects
# and it is your business to sort it out.

# Read the .bot files.
print('Reading the bot files...')
echosounder_data.read_bot(botfiles)

# Get the raw_data objects from the echosounder_data object. raw_data
# objects contain raw echosounder data from a single channel.
#
# Use the get_channel_data() method to do this. You can get channels
# by frequency, channel id, or channel number. It returns a dict, keyed
# by frequency, channel id, or channel number where the dict elements
# are lists containing the raw_data objects that match your request.
raw_data = echosounder_data.get_channel_data(frequencies=[38000])

# Again, 90% of the time you're going to only have 1 element in the
# list so it's convenient to unpack it here. If you read a file with
# multiple channels at the same frequency, or data from the same channel
# saved as complex and reduced, multiple objects will be returned in
# the list and like above, it's your business to sort that out.
raw38_data = raw_data[38000][0]

# Next get a calibration object populated with data from the raw file.
cal_obj = raw38_data.get_calibration()

# If you need to change any of the cal parameters (for example, you
# calibrated after collecting your data and compute new gain and
# sa_correction), you can do that here.

cal_obj.gain = 27.13
cal_obj.sa_correction =  -0.09
cal_obj.sound_speed = 1477.0

# You can print() the cal_obj to see all of it's attributes:
#print(cal_obj)

# In theory you can also read an Echoview ECS file which will update
# your cal object with parameters from the file. This needs testing.
#cal_obj.read_ecs_file(ecs_file, 'T2')

# Get Sv. Pass the cal_obj so the method uses our modified settings.
# If you don't pass the calibration argument, the method will grab
# the cal params from the data file which you may not want. By default
# data will be returned with a range based vertical axis.
Sv_data = raw38_data.get_Sv(calibration=cal_obj)

#  get an echolab2 line object representing the detected bottom
bottom_line = raw38_data.get_bottom(calibration=cal_obj)


# Now create a mask and apply surface and bottom lines to these masks
# such that we mask out samples near the surface and below the bottom.

# create the mask to mask the surface and bottom. Note that we pass
# the "like" keyword to return a mask with the same shape and axes
# (aka "like") our sample data
surf_bot_mask = mask.mask(like=Sv_data)

# Create a surface exclusion line at 10m RANGE.
surf_line = line.line(ping_time=Sv_data.ping_time, data=10)

# Next create a line that is 0.5m shallower than the detected bottom.
# Note that the math operators are implemented for the line class so
# you can just subtract 0.5 and
bot_offset = bottom_line - 0.5

# Now apply our lines to our mask. The mask.apply_line() method sets
# all samples either above (apply_above=True) or below (apply_above=False)
# the line to the boolean value you specify.

# Mask out samples above our surface line
surf_bot_mask.apply_line(surf_line, apply_above=True, value=True)

# And mask out samples below our bottom offset line
surf_bot_mask.apply_line(bot_offset, apply_above=False, value=True)

# Now apply this mask to our data. When masking out surface and bottom
# data we set the data values to NaN since we do not want these samples
# to be considered *at all* for integration.

# You can apply a mask object just like a numpy boolean mask
Sv_data[surf_bot_mask] = np.nan


# When integrating, you probably want to apply an upper and possibly
# lower threshold on the data. This can easily be done using the
# comparison operators which return masks.

# find all samples that are greater than -34 dB.
max_threshold_mask = Sv_data > -34

# and all samples less than -100
min_threshold_mask = Sv_data < -100

# now OR them for the final threshold mask
threshold_mask = max_threshold_mask | min_threshold_mask

# When applying threshold masks for integration, you typically want the
# samples to be included in the layer thickness calculation so we will
# just set these samples to a tiny tiny number
Sv_data[threshold_mask] = -999


# Convert our data to linear units
Sv_data.to_linear()


# Next create a grid that defines the domain the samples are
# averaged over. The vertical axis is always in meters and the
# horizontal axis can be in distance, time, or pings. See the
# echolab2.processing.grid class for more info.

# create a grid with a time based horizontal axis with 5 minute
# intervals and a vertical axis of 10 m. Since our data has a
# range based vertical axis we have to specify the layer_axis
# as 'range'.
integration_grid = grid.grid(interval_axis='ping_time',
        interval_length=np.timedelta64('1', 'm'), data=Sv_data,
        layer_axis='range', layer_thickness=10)



# In the future, we would next call an integration function that
# accepts our data and grid and returns a processed data object
# containing NASC and some other stats as 2d properties and the
# axes containing the cell centers. But for now I'll leave it to
# you to work out computing NASC etc. down below in this script.



# Now that we have the grid, we can use it to extract the data
# interval by layer.
for interval in range(integration_grid.n_intervals):

    for layer in range(integration_grid.n_layers):

        # get a mask that we can use to return sample data for this cell.
        cell_mask = integration_grid.get_cell_mask(interval, layer)

        # use the mask to get the cell data
        cell_Sv = Sv_data[cell_mask]

        #  now get some info our our cell and cell sample data
        bad_samples = np.isnan(cell_Sv)
        n_good_samples = np.count_nonzero(~bad_samples)
        n_samples = integration_grid.interval_pings[interval]
        n_pings_in_cell = integration_grid.layer_samples[layer]
        n_total_samples = n_samples * n_pings_in_cell

        #  for examples sake - compute the cell mean Sv and sum of sv.
        if np.nansum(cell_Sv) > 0:
            cell_mean_Sv = 10.0 * np.log10(np.nanmean(cell_Sv))
            cell_sum_sv = np.nansum(cell_Sv)
        else:
            cell_mean_Sv = -999
            cell_sum_sv = 0

        #  and print out the info
        print("Interval %i, Layer %i" % (interval, layer))
        print("   total samples: %i" % (n_total_samples))
        print("    good samples: %i" % (n_good_samples))
        print("         mean Sv: %3.2f" % (cell_mean_Sv))


