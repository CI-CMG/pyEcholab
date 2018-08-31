# -*- coding: utf-8 -*-
"""
Developmental workflow for making NCEI multifrequency plots using PyEcholab
"""

import numpy as np
from ast import literal_eval
from configparser import ConfigParser
from scipy.ndimage.filters import gaussian_filter as gf
from echolab2.instruments.EK60 import EK60


from echolab2.processing.batch_utils import FileAggregator as fa
from echolab2.processing.align_pings import AlignPings
from echolab2.processing.ncei_multifrequency import MultifrequencyData
from echolab2.plotting.matplotlib.multifrequency_plotting import MultifrequencyPlot


def smooth(data_objects, sigma=3):
    smooth_objects = {}

    for frequency, data in data_objects.items():
        smooth_data = gf(data.data, sigma)
        new_object = data.empty_like()
        setattr(new_object, 'data', smooth_data)
        smooth_objects[frequency] = new_object

    return smooth_objects


def interp_positions(array):
    """
    Interpolate position arrays by replacing Nans wiht hearest non-nan value.
    Args:
        array (np.arra): 1D numpy array or either latitude or longitude values.

    Returns: Array with Nans replaced.

    """
    mask = np.isnan(array)
    array[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask),
                            array[~mask])
    return array


config_file = 'ncei.conf'

# Read the configuration file and assign values to variables.
config = ConfigParser()
config.read(config_file)

data_dir = config.get('DEFAULT', 'data_dir')
interval = int(config.get('DEFAULT', 'interval'))
low_threshold = int(config.get('DEFAULT', 'low_threshold'))
high_threshold = int(config.get('DEFAULT', 'high_threshold'))
values = literal_eval(config.get('DEFAULT', 'values'))
sigma = int(config.get('DEFAULT', 'sigma'))
color_table = (literal_eval(config.get('PLOTTING', 'color_table')))
logo = config.get('PLOTTING', 'logo_file')
output_dir = config.get('DEFAULT', 'image_dir')

# Get a list of lists that are aggregates of files binned into time blocks
# controlled by the interval value (in minutes).
raw_files = fa(data_dir, interval)

# Get a list of the bottom files binned the same as ,raw files. NOTE! There
# has to be a 1 to 1 pairing of .raw and .bot files for this to work.
bottom_files = fa(data_dir, interval, extension='.bot')

# # Create instance of MultifrequencyPlot for plotting.
# plot = MultifrequencyPlot(logo=logo, output_dir=output_dir)

# Process file blocks and generate plot for each.
for index in range(0, len(raw_files.file_bins)):

    # Create instance of MultifrequencyPlot for plotting.
    plot = MultifrequencyPlot(logo=logo, output_dir=output_dir)

    # Get title for plot. title is first and last file in list of files.
    # Sometimes there might only be 1 file if file covers more time than
    # specified by interval.
    first_file = raw_files.file_bins[index][0].split('/')[-1].split('.')[0]
    last_file = raw_files.file_bins[index][-1].split('/')[-1].split('.')[0]
    if first_file == last_file:
        title = first_file
    else:
        title = '{0} to {1}'.format(first_file, last_file)

    # Create an instance of the EK60 class to hold raw data.
    ek60 = EK60()

    # Use the read_raw method to read in the files.
    ek60.read_raw(raw_files.file_bins[index])

    # Use the read_bottom method to add bottom data.
    ek60.read_bot(bottom_files.file_bins[index])

    # Create a dictionary of RawData objects from the channels in the data.
    raw_data = {}
    for channel in ek60.channel_id_map:
        raw_data[channel] = ek60.get_raw_data(channel_number=channel)

    # Create dictionary of Sv ProcessedData objects. THe channels frequency (
    # in KHz) is the key.
    Sv = {}
    for channel, data in raw_data.items():
        frequency = int(data.frequency[0]/1000)
        Sv[frequency] = data.get_Sv(heave_correct=True)

    # Get a list of channels for use by AlignPings
    channels = []
    for frequency, data in Sv.items():
        channels.append(data)

    # Align pings using padding for dropped pings.
    aligned = AlignPings(channels, 'delete')  # 'delete' or 'pad'\

    # Get a smoothed version of the data
    smooth_data = smooth(Sv, sigma=3)

    # Get positions interpolating against first frequency in Sv dictionary.
    # Because nav might start a few pings after data, interpolate to
    # replace Nans with nearest non nan values.
    positions = ek60.nmea_data.interpolate(Sv[list(Sv.keys())[0]], 'position')
    latitude = interp_positions(positions['latitude'])
    longitude = interp_positions(positions['longitude'])

    # Multifrequency MUST be done post ping alignment!!!!!
    final_data = MultifrequencyData(Sv, latitude, longitude, low_threshold,
                                    high_threshold, values)
    smooth_data = MultifrequencyData(smooth_data, latitude, longitude,
                                     low_threshold, high_threshold, values)

    # Get the bottom data from the 18kHz data. We need to get the indicies of
    #  the pings in the raw data that are still in the Sv data after time
    # aligning so teh bottom ping times match the data ping times.
    xsorted = np.argsort(raw_data[1].ping_time)
    ypos = np.searchsorted(raw_data[1].ping_time[xsorted], Sv[18].ping_time)
    indices = xsorted[ypos]

    raw_bottom = raw_data[1].get_bottom(heave_correct=True,
                                        return_indices=indices)
    bottom_values = raw_bottom.data[:,np.newaxis]

    bottom_mask = np.zeros([final_data.n_pings, final_data.n_samples])
    bottom_mask[:] = final_data.depth
    bottom_mask = (bottom_mask >= bottom_values)

    final_data.data = np.ma.masked_array(final_data.data, bottom_mask,
                                         fill_value=2)
    smooth_data.data = np.ma.masked_array(smooth_data.data, bottom_mask,
                                          fill_value=2)

    plot.plot(smooth_data, bottom=raw_bottom, title=title,
              day_night=True)

