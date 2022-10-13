# -*- coding: utf-8 -*-
"""
integration_example_plot.py

This script demonstrates using the grid and integration classes to
perform basic echo integration. The results are plotted on an echogram
using the Qt based echogram viewer.

This script is identical to integration_example_export.py except that
it plots the echogram and integration results instead of writing them
to a CSV file.

"""

from PyQt5 import QtWidgets
from echolab2.plotting.qt import echogram_viewer
from echolab2.instruments import echosounder
from echolab2.processing import line, grid, integration
import numpy as np
 

# Alex modified this as had trouble with paths 
#import os
#os.chdir("C:/Users/alex.derobertis/Work/GitHub/pyEcholab/") # set the Working directory
#os.getcwd() # check the working directory


"""
First we specify our integration parameters. We'll define the parameters for
creating the integration grid as well as the surface and bottom exclusion
lines that will be used to exclude near surface and bottom/below bottom data
from integration. We'll also set some basic thresholds used during integration.
"""

# specify the minimum Sv value for integration. Samples with Sv values below this
# threshold are "zeroed" out. The sample volume is still included in the integration
# calculation but thresholded samples contribute no backscatter.
min_integration_threshold = -70

# Set apply_min_threshold to True to apply the threshold. If False, the min 
# threshold is ignored.
apply_min_threshold = True

# specify the maximum Sv value for integration. Samples with Sv values above this
# threshold are "zeroed" out. The sample volume is still included in the integration
# calculation but thresholded samples contribute no backscatter.
max_integration_threshold = -10

# Set apply_max_threshold to True to apply the threshold. If False, the max 
# threshold is ignored.
apply_max_threshold = False


# Next specify your integration grid parameters. The grid defines the horizontal
# "intervals" and vertical "layers" 

# specify the interval axis. The interval axis can be trip_distance_nmi,
# trip_distance_m, ping_time, or ping_number. If you specify a distance based
# unit, your raw data must contain GPS data. See echolab2.processing.grid for
# more details. 
interval_axis = 'ping_time'

# specify the interval length. for time based intervals the length must be
# specified as a numpy timedelta64 object. Here we'll create a 5 minute interval.
# See the docs for timedelta64 for more info.
interval_length = np.timedelta64('5', 'm')

# define the vertical axis for the grid. This can be 'range' or 'depth' and it
# must match the vertical axis of your data. (in this example we will make sure
# the data is in range or depth depending on what you specify here.)
layer_axis = 'depth'

# specify the layer thickness. This is always in meters.
layer_thickness = 10

# lastly, specify whether the first full interval should start at the first
# ping, or if the first full interval should start at a ping "rounded" to your
# interval length. For example, if our data starts at 10:23:31 and we have a 5
# minute interval:
#  non-rounded starts would create intervals at 10:23:31, 10:28:31, 10:33:31, ... 
#  rounded starts would create intervals as 10:23:31, 10:25:00, 10:30:00, ...
# The same logic holds for distance and ping based intervals.
round_interval_starts = True


# And finally let's specify some parameters that define our upper and lower
# integration exclusion lines. 

# define the upper exclusion line depth. For this example we will create a simple
# line at a fixed depth/range. This may not be appropriate if you are applying
# heave correction to your data (which we do not do in this example.)
# Define the upper exclusion line in ->DEPTH<- We will convert this to range
# below if you have specified the grid layer axis as range above.
upper_exclusion_line_depth = 15

# define the lower exclusion line offset. We will define this line as an offset 
# from the bottom detection line. The value is in meters. Negative values are
# above the bottom
lower_exclusion_line_offset = -0.5


'''
The next thing we need to do is get the data we want to integrate and any
ancillary data we may need. For integration you typically need the calibrated
backscatter data as Sv, the bottom detection data (so you can exclude data
below the bottom) and the NMEA data for distance traveled and (possibly)
vessel heave. 
'''

# specify some data files
rawfiles = ['C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T223129.raw',
            'C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T223821.raw',
            'C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T224512.raw',
            'C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T225202.raw']

# and the matching bottom files.
botfiles = ['C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T223129.bot',
            'C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T223821.bot',
            'C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T224512.bot',
            'C:/EK Test Data/EK60/DY1807/DY1807_EK60-D20180607-T225202.bot']


# Use the echosounder function read our data. This function figures
# out what format the data is in (EK60 or EK80), creates the correct
# object and reads the data.
print('Reading the raw files...')
echosounder_data = echosounder.read(rawfiles, frequencies=[38000])

# The echosounder function returns a list of echolab2 instrument objects
# containing the data read from the files you passed it. Assuming
# you are reading data files collected from the same echosounder model
# configured with the same general settings there will always be a single
# object in the list so it's convenient to unpack it here.
echosounder_data = echosounder_data[0]

# Now, if you read some EK80 files and some EK60 files and some files
# had complex, others power/angle you're going to have a bunch of objects
# and it is your business to sort it out.

# Read the .bot files. When reading bot/out files, you must read the raw
# data first. When you read the bot/out files, the bottom detection data
# associated with the channels+pings you have read will be stored. 
print('Reading the bot files...')
echosounder_data.read_bot(botfiles)

# Get the raw_data objects from the echosounder_data object. raw_data
# objects contain raw echosounder data from a single channel.

# Use the get_channel_data() method to do this. You can get channels
# by frequency, channel id, or channel number. It returns a dict, keyed
# by frequency, channel id, or channel number where the dict elements
# are lists containing the raw_data objects that match your request.
raw_data = echosounder_data.get_channel_data(frequencies=[38000])

# Again, 90% of the time you're going to only have 1 element in the
# list so it's convenient to unpack it here. If you read a file with
# multiple channels at the same frequency, or data from the same channel
# saved as in some files as complex and others reduced, multiple objects
# will be returned in the list and like above, it's your business to
# sort that out.
raw38_data = raw_data[38000][0]

# Next get a calibration object populated with data from the raw file.
cal_obj = raw38_data.get_calibration()

# If you need to change any of the cal parameters (for example, you
# calibrated after collecting your data and computed new gain and
# sa_correction), you can do that here.

#cal_obj.gain = 22.09
#cal_obj.sa_correction =  -0.64
#cal_obj.sound_speed = 1477.0

# Get Sv. Pass the cal_obj so the method uses our (potentially)
# modified settings. If you don't pass the calibration argument, the
# method will grab the cal params from the data file which you may not
# want. We will set the return_depth argument based on what you have
# defined above for the grid's layer axis to ensure we're working with
# the same vertical axis.

if layer_axis == 'depth':
    return_depth = True
else:
    return_depth = False

Sv_data = raw38_data.get_Sv(calibration=cal_obj,
        return_depth=return_depth)
print(Sv_data)

# We also are going to need some of the "NMEA" data such as GPS and
# (possibly) vessel motion recorded along with the acoustic data. This
# data is collected asynchronously from the acoustic data and is
# shared between all channels in a raw file. Each raw_data object has
# a "nmea_data" attribute that references this data. We can pass this
# reference to the processed_data.set_navigation() method to interpolate
# the data to the axes of our Sv_data object. 
Sv_data.set_navigation(raw38_data.nmea_data)

# now when we print Sv_data you will see additional data attributes.
# For our DY1807 data this includes latitude, longitude, heave,
# vessel speed (spd_over_grnd_kts), and vessel log (trip_distance_nmi)
print(Sv_data)


"""
The next thing we need to do is to define the integration domain.
At a minimum, this is done by creating a grid defined by horizontal
"intervals" and vertical "layers". Intervals can be defined by time,
distance (m or nmi), or ping number and layers are defined by distance
(in meters) and can be in range or depth.

You may also choose to define upper and/or lower exclusion lines
which exclude "surface noise" (transducer ringing, bubbles, etc.)
and bottom and below bottom data from integration.

While we will not do it in this example, you can also pass an
"inclusion_mask" and/or a "no_data_mask" to exercise additional
control of what samples are integrated.
"""

# create the integration grid using the parameters that have been
# defined above. The grid is created using the axis parameters and
# the axis data contained within the Sv_data object. This grid is
# reusable as long as the data you are integrating all share the
# same (or very similar) axes. For example, you should be able to
# use the same grid to integrate multiple channels from the same
# raw file. 
print("Creating grid and exclude lines...")
integration_grid = grid.grid(interval_axis=interval_axis,
        interval_length=interval_length, data=Sv_data,
        layer_axis=layer_axis, layer_thickness=layer_thickness,
        round_interval_starts=round_interval_starts)


# Next get our two "exclusion lines". We will first create an upper 
# exclusion line. Call the line.like method to create a line with ping
# times that match our data. We pass the depth value we defined above
# to create a line at a constant depth.
surf_exclusion_line = line.like(Sv_data,
        data=upper_exclusion_line_depth)

# This line must be in the same vertical units as our data. Since we
# have specified the surface exclusion line in depth above, we will 
# adjust it here if we have chosen to integrate on a range grid.
if layer_axis == 'range':
    # We specified a range based grid, so we want to convert our
    # surface exclusion line to range. To do this, we simply
    # subtract the transducer_offset
    surf_exclusion_line -= Sv_data.transducer_offset
    
# Note that if you were working with heave corrected data, you would
# probably want to base your surface exclusion line off of the vessel
# heave data and then *add* an offset:
#surf_exclusion_line = line.like(Sv_data, data=Sv_data.heave + offset)

# since we will be plotting these lines, we'll set some additional
# attributes related to plotting. These attributes only have meaning
# when plotting.
surf_exclusion_line.color = [200,0,200]
surf_exclusion_line.thickness = 2.0


# Next we create a bottom exclusion line. This will be based off of the
# sounder detected bottom so the first step is to get an echolab2 line
# object representing the detected bottom.  Bottom lines will always be
# returned as *depth* with heave correction applied (if heave correction
# was enabled during recording.) Read that again. It doesn't matter if
# you have applied heave correction to the sample data or not. The
# bottom detections always have heave included if heave correction was
# enabled when the data were recorded.

# Another important detail to remember is that bottom depths are computed
# using the sound speed at the time of recording. If you are processing
# your data using a different sound speed you *must* pass a calibration
# object with the correct sound speed to the get_bottom method to ensure
# that the bottom depths are corrected for the new sound speed.
detected_bottom = raw38_data.get_bottom(calibration=cal_obj)

# again, set some plotting attributes
detected_bottom.color=[200,200,0]
detected_bottom.thickness = 2.0

# As stated above, bottom detections are always returned as depth with
# heave corrections applied so we may need to back those out depending
# on whether heave correction was enabled during recording (it was in
# this example data) and if we specified a range based grid.

# first we'll remove heave corrections from the bottom line if heave
# data exists.
if hasattr(Sv_data, 'heave'):
    # we do have heave data which means heave will be included in
    # the bottom detections. Subtract that out here:
    detected_bottom += Sv_data.heave
    
# then we'll remove the transducer offset if we're working with a range
# based data and grid.
if layer_axis == 'range':
    detected_bottom -= Sv_data.transducer_offset

# at this point we have a bottom detection line that should match our
# data and grid. We will use that line to create a new bottom exclusion
# line that is offset from the bottom detection line by the amount
# specified above. We're adding here since we specify the sign when
# we define the lower_exclusion_line_offset
bot_exclusion_line = detected_bottom + lower_exclusion_line_offset

# and again with the plotting attributes
bot_exclusion_line.color = [200,0,200]
bot_exclusion_line.thickness = 2.0


"""
We are now ready to integrate. We use the echolab2.processing.integration
module to do this. 
"""

# first create an instance of the integrator. IWe pass it the threshold we
# specified above and the booleans specifying if the thresholds should be
# applied. These values are persistent over the life of the object.
int_object = integration.integrator(min_threshold=min_integration_threshold,
        min_threshold_applied=apply_min_threshold,
        max_threshold=max_integration_threshold,
        max_threshold_applied=apply_max_threshold)
        

# next we integrate by calling the integrate method. We pass it our Sv data,
# the grid, and our exclusion lines. As hinted above, you can also pass it
# an "inclusion mask" and "no data mask" for more advanced integration but
# we're not doing that here. The integrate method will return an
# integration.results object that contains NASC, min/mean/max Sv, and some
# information about the samples included/excluded. All of these attributes
# are stored as numpy arrays n_intervals x n_cells in size where index [0,0]
# is the first interval and first layer (upper left corner of the grid.)
print("Integrating...")
int_results = int_object.integrate(Sv_data, integration_grid, 
            exclude_above_line=surf_exclusion_line,
            exclude_below_line=bot_exclusion_line)



"""
Now we'll create an echogram and plot the grid and results. The code from
here on out is less baked. 
"""

print('Plotting...')

# Create an application instance.
app = QtWidgets.QApplication([])

# Create the main application window and show it
eg_viewer = echogram_viewer.echogram_viewer()

#  show the application window
eg_viewer.show()

# Set the echogram data
eg_viewer.update_echogram(Sv_data)

# Add our bottom line and exclude above and below lines. The lines will
# be plotted using the color and thickness parameters we applied above.
eg_viewer.add_line(detected_bottom)
eg_viewer.add_line(surf_exclusion_line)
eg_viewer.add_line(bot_exclusion_line)

# Add the grid to the echogram. 
echogram_grid = eg_viewer.add_grid(integration_grid)

# lastly, add the NASC values as red text in the center of the grid cells.
# We'll skip cells that don't have any data (NaN).

# The integration.results class is iterable and will return data in a dict
# by interval,row:
for cell_results in int_results:
    # check if there are any results for this cell
    if np.isfinite(cell_results['nasc']):
        # yes, create the string label
        label = '%5.2f' % (cell_results['nasc'])
        
        # and add it to the cell
        echogram_grid.addCellLabel(label, [0.5,0.5], cell_results['interval']-1,
                cell_results['layer']-1, color=[255,0,0],
                halign='center', valign='center')

        
#  save the echogram at full resolution. Curently this does not
#  include the horizontal scaling that is appled to the sample data
#  to reduce the vertical exaggeration of the echograms.
#eg_viewer.save_image('test.png')

# Start event processing.
app.exec_()

print("Done!")



#integration_grid = grid.grid(interval_axis='ping_time',
#        interval_length=np.timedelta64('5', 'm'), data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=False)
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()

#integration_grid = grid.grid(interval_axis='ping_time',
#        interval_length=np.timedelta64('5', 'm'), data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=True)
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()


#integration_grid = grid.grid(interval_axis='ping_time',
#        interval_length=np.timedelta64('5', 'm'), data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=False,
#        interval_start=np.datetime64('2018-06-07T22:37:00'))
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()
#
#integration_grid = grid.grid(interval_axis='ping_time',
#        interval_length=np.timedelta64('5', 'm'), data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=True,
#        interval_start=np.datetime64('2018-06-07T22:37:00'))
#        
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()
#
#
#integration_grid = grid.grid(interval_axis='trip_distance_nmi',
#        interval_length=0.5, data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=False)
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()
#
#integration_grid = grid.grid(interval_axis='trip_distance_nmi',
#        interval_length=0.5, data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=True)
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()
#
#
#integration_grid = grid.grid(interval_axis='ping_number',
#        interval_length=47, data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=False, interval_start=22)
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()
#
#integration_grid = grid.grid(interval_axis='ping_number',
#        interval_length=47, data=Sv_data,
#        layer_axis='range', layer_thickness=layer_thickness,
#        round_interval_starts=True, interval_start=22)
#
#print(integration_grid)
#print(integration_grid.interval_edges)
#print()

