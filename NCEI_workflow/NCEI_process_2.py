# -*- coding: utf-8 -*-
"""
Developmental workflow for making NCEI multifrequency plots using PyEcholab
"""

import numpy as np
import datetime
from ast import literal_eval
from configparser import ConfigParser
from scipy.ndimage.filters import gaussian_filter as gf

from echolab2.instruments.EK60 import EK60
from echolab2.processing.mask import Mask
from echolab2.processing.line import Line
from echolab2.processing.batch_utils import FileAggregator as fa
from echolab2.processing.align_pings import AlignPings
from echolab2.processing.ncei_multifrequency import MultifrequencyData
from echolab2.plotting.matplotlib.multifrequency_plotting import MultifrequencyPlot

from echopy.mask_impulse import mask_in_ryan
from echopy.mask_attenuated import mask_as_ryan as at_mask
from echopy.mask_transient import mask_tn_fielding
from echopy.estimate_background import estimate_bgn_derobertis_mod
from echopy.mask_signal2noise import mask_s2n

np.set_printoptions(threshold=np.inf)

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
    Interpolate position arrays by replacing Nans with nearest non-nan value.
    Args:
        array (np.arra): 1D numpy array or either latitude or longitude values.

    Returns: Array with Nans replaced.

    """
    mask = np.isnan(array)
    array[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask),
                            array[~mask])
    return array


start_time = datetime.datetime.now()

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
        raw = ek60.get_raw_data(channel_number=channel)
        frequency = int(raw.frequency[0]/1000)
        raw_data[frequency] = raw

    # Create dictionary of Sv ProcessedData objects. The channels
    # frequency (\in KHz) is the key.
    Sv = {}
    for frequency, data in raw_data.items():
        Sv[frequency] = data.get_Sv(heave_correct=True)

    # Get a list of channels for use by AlignPings
    channels = []
    for frequency, data in Sv.items():
        channels.append(data)

    # # Mask impulse noise.
    # m, thr = 5, 10 # (metres, decibels)
    # for freq in Sv:
    #     print('Masking {0}kHz impulse noise'.format(freq))
    #     mask, Svasked = mask_in_ryan(np.transpose(Sv[freq].data),
    #                                               Sv[freq].depth, m, thr)
    #
    #     Sv[freq].data = np.transpose(Svasked)
    #
    # # Mask transient.
    # r0, n, thr = 100, 30, (3, 1)  # (metres, pings, decibels)
    # for freq in Sv:
    #     # print(Sv[freq].data_atributes)
    #
    #     print('Masking {0} transients'.format(freq))
    #     mask, Svmasked = mask_tn_fielding(np.transpose(Sv[freq].data),
    #                                       Sv[freq].depth, r0, n, thr, jumps=12,
    #                                       verbose=False)
    #     Sv[freq].data =  np.transpose(Svmasked)
    #
    # # Mask attenuated.
    # r0, r1, n, threshold = 100, 200, 30, -6  # (m, m, pings, dB)
    # for freq in Sv:
    #     print('Masking {0}kHz attenuated signal'.format(freq))
    #     mask, Svmasked = at_mask(np.transpose(Sv[freq].data),
    #                              Sv[freq].depth, r0, r1, n, threshold,
    #                              verbose=False)
    #     Sv[freq].data = np.transpose(Svmasked)

    # Remove background.
    m, n, operation = 10, 20, 'percentile90' # (m, npings, str)
    threshold = 3  # (decibels)
    for freq in Sv:
        print('Removing background from {0}kHz'.format(freq))
        # estimate background noise.
        bgn = estimate_bgn_derobertis_mod(
                                np.transpose(Sv[freq].data), Sv[freq].depth,
                                raw_data[freq].absorption_coefficient[0],
                                m, n, operation=operation)

        # Clean background noise.
        mask120, Svclean = mask_s2n(np.transpose(Sv[freq].data), bgn, threshold)
        Sv[freq].data = np.transpose(Svclean)

    # Align pings by deleting pings to make all channels match the channel
    # with fewest pings. Padding does not work when making NCEI plots because
    #  missing data is filled with zeros instead of interpolated values.
    aligned = AlignPings(channels, 'delete')

    # Get the bottom data from the 18kHz data. We need to get the indices of
    # the pings in the raw data that are still in the Sv data after time
    # aligning so teh bottom ping times match the data ping times.
    low_freq = min(list(raw_data.keys()))
    xsorted = np.argsort(raw_data[low_freq].ping_time)
    ypos = np.searchsorted(raw_data[low_freq].ping_time[xsorted],
                           Sv[low_freq].ping_time)
    indices = xsorted[ypos]

    raw_bottom = raw_data[low_freq].get_bottom(heave_correct=True,
                                        return_indices=indices)

    # There might be random zero values for bottom. Replace with linear
    # interpolated values.
    non_zero = np.nonzero(raw_bottom.data)
    idx = np.arange(len(raw_bottom.data))
    interp = np.interp(idx, idx[non_zero], raw_bottom.data[non_zero])
    raw_bottom.data = interp

    # Mask for bottom and surface.
    masks = {}
    for freq in Sv:
        # Create a mask.
        masks[freq] = Mask(like=Sv[freq])

        # Next create a new line that is 0.5m shallower. (in
        # place operators will change the existing line.)
        bot_line = raw_bottom - 3.0

        # Now create a surface exclusion line at data=Xm RANGE.
        surf_line = Line(ping_time=Sv[freq].ping_time, data=3)

        # Now apply that line to our mask.  We apply the value True BELOW our
        # line.  Note that we don't need to specify the value as True is the
        # default.
        masks[freq].apply_line(bot_line, apply_above=False)

        # Now apply our surface line to this same mask.
        masks[freq].apply_line(surf_line, apply_above=True)

        # Now use this mask to set sample data from 0.5m above the bottom
        # downward to NaN.
        Sv[freq][masks[freq]] = np.NaN

    # Get a smoothed version of the data
    smooth_data = smooth(Sv, sigma=2)

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

    # Plot the data.
    plot.plot(smooth_data, bottom=raw_bottom, title=title,
               day_night=True)

end_time = datetime.datetime.now()

print(start_time.strftime("%a, %d %B %Y %H:%M:%S"))
print(end_time.strftime("%a, %d %B %Y %H:%M:%S"))
