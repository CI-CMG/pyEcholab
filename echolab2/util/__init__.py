# coding=utf-8
'''
.. module:: echolab.util

    util/
        date_conversion.py      -   Helper functions for converting between UNIX and NT epoch times
        unit_conversion.py      -   Helper functions for converting between various units (eg power -> Sv)
        triwave.py              -   Functions for estimating and correcting ES60 trinagle wave gain offsets

    useful functions in echolab.util:
    
        align_nmea_to_ping_times -   Interpolate NMEA data to ping timestamps
        find_indx_for_nearest    -   Searches an array & returns index of closest match
        grid_data                -   Partition data
        gps_distance             -   estimate the distance between two gps coordinates
        smooth_bottom_track      -   Attempt to fill gaps in bottom depth estimates

 | Zac Berkowitz <zachary.berkowitz@noaa.gov>
 | National Oceanic and Atmospheric Administration
 | Alaska Fisheries Science Center
 | Midwater Assesment and Conservation Engineering Group

$Id$
'''

from datetime import datetime
from pytz import utc as pytz_utc
import os
import numpy as np
import logging
import re

from . import date_conversion, unit_conversion, triwave


log = logging.getLogger(__name__)

__all__ = ['date_conversion', 'unit_conversion', 'triwave', 'find_indx_for_nearest',
           'grid_data', 'get_datetime_from_filename']


def get_datetime_from_filename(filename_str):
    try:
        filename_datestr = re.search('D[0-9]+-T[0-9]+', os.path.basename(filename_str)).group()
    except AttributeError:
        return None
    
    return pytz_utc.localize(datetime.strptime(filename_datestr, 'D%Y%m%d-T%H%M%S'))

#class Grid(object):
#    '''
#   
#    Tick indices follow python slicing rules where the
#    lower bound is INCLUSIVE and the upper bound is EXCLUSIVE.
#    
#    .. note:: 'None' values:  To use the tick indices for slices, values
#        of 'None' are required for intervals which include the last element in an
#        array.  For instance, the pair (10, None) is equivalent to the slice [10:], 
#        where the upper bound is left unbounded to include the last array value.
#    
#    
#    '''
#    
#    
#    x_vector = None
#    '''
#    X axis physical values
#    '''
#    
#    
#    y_vector = None
#    '''
#    Y axis physical values
#    '''
#    
#    x_ticks = None
#    '''
#    X axis tic mark locations by index
#    '''
#
#    y_ticks = None
#    '''
#    Y axis tic mark locations by index
#    '''
#    
#    grid_dtype = np.dtype([('x0', object),
#                        ('y0', object),
#                        ('x1', object),
#                        ('y1', object)])
#    '''
#    | Data type for arrays returned from :attr:`Grid.cells`
#    | Named fields: 'x0', 'x1', 'y0', 'y1'
#    '''
#    
#    grid_physical_dtype = np.dtype([('x0', float),
#                        ('y0', float),
#                        ('x1', float),
#                        ('y1', float)])
#    '''
#    | Data type for arrays returned from :attr:`Grid.physical_cells`
#    | Named fields: 'x0', 'x1', 'y0', 'y1'
#    '''
#    
#    def __init__(self):
#        
#        self.x_ticks = []
#        self.x_vector = []
#        
#        self.y_ticks = []
#        self.y_vector = []
#            
#        
#        
#    @property
#    def x_labels(self):
#        '''
#        Labels for x axis tic marks
#        '''
#        return [self.x_vector[k] if k is not None else self.x_vector[-1] for k in self.x_ticks]
#
#    @property
#    def y_labels(self):
#        '''
#        Labels for y axis tic marks
#        '''
#        return [self.y_vector[k] if k is not None else self.y_vector[-1] for k in self.y_ticks]
#        
#      
#    @property
#    def cells(self):
#        '''
#        List of regions in [x0, y0, x1, y0] groups, where x and y are column
#        and row indices.
#        
#        :rtype: :class:`numpy.ndarray` of type :attr:`Grid.grid_dtype`
#        '''
#        shape = (len(self.y_ticks) - 1, len(self.x_ticks) - 1)
#        
#        cells = np.zeros(shape, self.grid_dtype)
#
#        for col_indx in range(len(self.x_ticks) - 1):
#            x0 = self.x_ticks[col_indx]
#            x1 = self.x_ticks[col_indx + 1]
#
#            for row_indx in range(len(self.y_ticks) - 1):
#                y0 = self.y_ticks[row_indx]
#                y1 = self.y_ticks[row_indx + 1]    
#                #cells.append([x0, y0, x1, y1])
#                
#                cells[row_indx, col_indx] = x0, y0, x1, y1
#
#        return cells
#    
#    @property
#    def physical_cells(self):
#        '''
#        List of regions in [x0, y0, x1, y0] groups, where x and y are column
#        and row labels.
#
#        :rtype: :class:`numpy.ndarray` of type :attr:`Grid.grid_physical_dtype`
#        
#        This is equivalent to calling::
#        
#            for x0, y0, x1, y1 in Grid.cells:
#
#                x0_phys = self.x_vector[x0]
#                x1_phys = self.x_vector[x1]
#                
#                y0_phys = self.y_vector[y0]
#                y1_phys = self.y_vector[y1]
#                
#        '''
#        
#        shape = (len(self.y_ticks) - 1, len(self.x_ticks) - 1)
#        cells = np.zeros(shape, self.grid_physical_dtype)
#        
#        for col_indx in range(len(self.x_ticks) - 1):
#            x0 = self.x_ticks[col_indx]
#            x0_u = self.x_vector[x0]
#            
#            x1 = self.x_ticks[col_indx + 1]
#            if x1 is None:
#                x1 = -1
#            
#            x1_u = self.x_vector[x1]
#
#            for row_indx in range(len(self.y_ticks) - 1):
#                y0 = self.y_ticks[row_indx]
#                y0_u = self.y_vector[y0]
#                
#                y1 = self.y_ticks[row_indx + 1]
#                if y1 is None:
#                    y1 = -1
#                
#                y1_u = self.y_vector[y1]
#                
#                cells[row_indx, col_indx] = x0_u, y0_u, x1_u, y1_u
#                #cells.append([x0, y0, x1, y1])
#
#        return cells
#
#    def __repr__(self):
#        x = 'x ticks:  %s\nx labels:  %s\n\n'%(str(self.x_ticks), str(self.x_labels))
#        
#        y = 'y ticks:  %s\ny labels:  %s' %(str(self.y_ticks), str(self.y_labels))
#    
#        return x + y
#
#    
#def find_indx_for_nearest(array, value):
#    '''
#    :param array: Array-like object
#    
#    :param value: Desired value to match against
#    
#    :returns: int
#    
#    Finds the index for the value in `array` which most closely matches
#    the given desired `value`.  Simple wrapper around argmin to allow use
#    of datetime objects.
#    
#    
#    argmin cannot be used as is for datetime.timedelta objects, but it's
#    algorithm can.   See 
#    http://mail.scipy.org/pipermail/numpy-discussion/2011-March/055562.html
#    '''
#    if isinstance(value, datetime):
#        time_delta_vector = abs(array - value)
#        min_value = time_delta_vector.min()
#        indx = (min_value - time_delta_vector).argmax()
#    
#    else:
#        indx = (abs(array - value)).argmin()
#    return indx
#
#
#def grid_data(data_matrix, interval_spacing, layer_spacing,
#               return_partial=True,
#               shift_first_row=False):
#    '''
#    :param data_matrix: 2D Rectangular matrix of data to grid
#    :type data_matrix: :class:`echolab._DerivedQuantity`
#    
#    :param interval_spacing: Stride length along columns (in nmi)
#    :type interval_spacing: float
#    
#    :param layer_spacing: Stride length along rows (in m)
#    :type layer_spacing: float
#        
#    :param return_partial:  Include cells at edges of data that do not meet a full stride
#    :type return_partial: bool
#    
#    :param shift_first_row: Ignore first sample of every ping (emulates Echoview behavior)
#    :type shift_first_row: bool
#      
#    :returns: Grid object
#    :rtype: :class:`echolab.util.Grid`
#    
#    
#    Example::
#        
#        import echolab.simrad_io
#        import echolab.util
#        
#        filename = 'somefile.raw'
#        
#        er60_data = echolab.simrad_io.ER60Data(filename)
#        Sv = er60_data.pings[0].Sv()
#        
#        #Set up grid:  50m depth layers, 1nmi intervals
#        Sv_grid = echolab.util.grid_data(Sv, interval_spacing=1.0,
#            layer_spacing=50.0, shift_first_row=True)
#    '''
#    
#    
#    tick_marks = []
#    tick_labels = []
#    dim = 0
#    
#    col_vector = data_matrix.distances
#    row_vector = data_matrix.ranges
#    
#    for stride, unit_vector in [(layer_spacing, row_vector),
#                                (interval_spacing, col_vector)]:
#        
#    
#
#
#
#        if not np.isscalar(stride):
#            do_indexed_stride = True
#        else:
#            do_indexed_stride = False
#
#        #Indexed stride
#        if do_indexed_stride:
#            # import pdb; pdb.set_trace()
#            # last_val = []
#            marks = [0]
#            labels = [unit_vector[0]]
#
#            ub_idx = 1
#            ub = stride[ub_idx]
#
#            for indx in range(1, data_matrix.shape[dim]):
#                this_val = unit_vector[indx]
#
#                if this_val > ub:
#                    if indx == data_matrix.shape[dim]:
#                        marks.append(None)
#                    else:
#                        marks.append(indx)
#
#                    labels.append(this_val)
#                    # last_val = this_val
#
#                    ub_idx += 1
#                    if ub_idx == len(stride):
#                        break
#                    else:
#                        ub = stride[ub_idx]
#            #End indexed
#
#        else:
#            last_val = unit_vector[0]
#            
#            marks = [0]
#            labels = [last_val]
#            #Constant Stride
#            for indx in range(1, data_matrix.shape[dim]):
#                
#                this_val = unit_vector[indx]
#                    
#                if this_val - last_val > stride:
#                    if indx == data_matrix.shape[dim]:
#                        marks.append(None)
#                    else:
#                        marks.append(indx)
#
#                    labels.append(this_val)
#                    last_val = this_val
#                    
#            
#            if return_partial and last_val != this_val:
#                marks.append(None)
#            #End Constant
#
#
#        tick_marks.append(marks)
#        tick_labels.append(labels)
#        dim += 1
#
#    
#    if shift_first_row:
#        for k in range(1, len(tick_marks[0])):
#            if tick_marks[0][k] is not None:
#                tick_marks[0][k] -=1
#                tick_labels[0][k] = row_vector[tick_marks[0][k]]
#
#    new_grid = Grid()
#    new_grid.shape = data_matrix.shape
#    new_grid.x_ticks = tick_marks[1]
##    new_grid.x_labels = tick_labels[1]
#    
#    new_grid.y_ticks = tick_marks[0]
##    new_grid.y_labels = tick_labels[0]
#
#    new_grid.x_vector = col_vector
#    new_grid.y_vector = row_vector
#
#    return new_grid

#def haversin(x):
#    '''
#    haversine(x) = sin(x/2)^2
#    
#    x is in radians
#    '''
#    
#    return np.sin(x/2)**2
#
#def archaversin(x):
#    '''
#    inverse haversine
#    
#    archarversine(x) = 2 * arcsin(sqrt(x))
#    '''
#    
#    return 2 * np.arcsin(np.sqrt(x))
#
#
#def gps_distance(lat0, lon0, lat1, lon1, r=6356.78):
#    '''
#    Calculates the distance between two gps coordinates using the haversine
#    formula.  Uses the value 'r' for the radius of the Earth (in km).
#    
#    haversin(d/r) = haversin(lat1 - lat0) + cos(lat0)*cos(lat1)*haversin(lon1-lon0)
#    
#    so
#    
#    d = r * archaversin(RHS)
#    
#    :returns: distance (in meters)
#    '''
#    
#    r_m = r * 1e3
#    
#    PI_DIV_180 = np.pi/180
#    lat0_r = lat0 * PI_DIV_180
#    lat1_r = lat1 * PI_DIV_180
#    lon0_r = lon0 * PI_DIV_180
#    lon1_r = lon1 * PI_DIV_180
#    
#    RHS = haversin(lat1_r - lat0_r) + np.cos(lat0_r)*np.cos(lat1_r)*haversin(lon1_r-lon0_r)
#    
#    d = r_m * archaversin(RHS)
#    
#    return d
    
#def align_nmea_to_ping_times(nmea_data, ping_times, nmea_fields=[]):
#    '''
#    :param nmea_data:  List of nmea datagrams in ascending order
#    :type nmea_data: list
#    
#    :param nmea_fields:  List of desired nmea data fields to np.interpolate
#    :type nmea_fields: [str]
#    
#    :param ping_times:  List of ping times in datetime format
#    :type ping_times: datetime.datetime
#    
#    :returns:  [NMEA]  A list of NMEA datagrams with the interpolated values.
#    '''
#    
#
#    #nmea_data = self.get_nmea_type(nmea_key)
#    nmea_type = nmea_data[0].nmea_type
#
# 
#    if isinstance(nmea_fields, str):
#        nmea_fields = [nmea_fields]
#    
#    #NMEA timestamps
#    nmea_timestamps = [date_conversion.datetime_to_unix(x.datetime) for x in nmea_data] 
#    ping_timestamps = map(date_conversion.datetime_to_unix, ping_times)
#    
#    #Get the class for this NMEA type
##    NmeaKlass = getattr(nmea, nmea_type)
#    NmeaKlass = type(nmea_data[0])
#    
#    #Build a dictionary with interpolated data values
#    interpolated_fields = {}
#    for field in nmea_fields:
#        field_data = [x[field] for x in nmea_data]
#        interpolated_fields[field] = np.interp(ping_timestamps, nmea_timestamps, field_data)
#    
#    #Create list of interpolated datagrams
#    interpolated_dgrams = []
#    for ping_num in range(len(ping_timestamps)):
#        this_dgram = NmeaKlass()
#        #Insert static values from first dgram in provided list
#        this_dgram.update(nmea_data[0])
#        
#        #low_date = self.pings[channel_id].ping_data[ping_num]['low_date']
#        #high_date = self.pings[channel_id].ping_data[ping_num]['high_date']
#        simrad_datetime = ping_times[ping_num]
#
#        low_date, high_date = date_conversion.unix_to_nt(simrad_datetime)
#        
#        this_dgram.simrad_datetime = simrad_datetime
#        this_dgram.low_date = low_date
#        this_dgram.high_date = high_date
#        
#        #Insert the interpolated data values
#        for field in nmea_fields:
#            this_dgram[field] = interpolated_fields[field][ping_num]
#
#        this_dgram.update_checksum()
#        interpolated_dgrams.append(this_dgram)
#        
#    #return  self.pings[channel_id].ping_data[:]['datetime'], interpolated_dgrams
#    return interpolated_dgrams
#
#def smooth_bottom_track(depth_vector, time_vector=[]):
#    '''
#    :param nmea_data:  List of nmea datagrams in ascending order
#    :type nmea_data: list
#    
#    :param nmea_fields:  List of desired nmea data fields to np.interpolate
#    :type nmea_fields: [str]
#    
#    :param channel_id:  Channel index to draw ping times from (should be constant across datasets).  Default=0
#    :type channel_id: int
#    
#    :returns:  [NMEA]  A list of NMEA datagrams with the interpolated values.
#    
#    
#    If depth_vector is entirely 0.0, that is there are no valid bottom depths,
#    the original all-zero vector is returned to the caller.
#    '''
#    
#
#    if time_vector == []:
#        smooth_time_vector = range(len(depth_vector))
#    elif isinstance(time_vector[0], datetime):
#        smooth_time_vector = map(date_conversion.datetime_to_unix, time_vector)
#    else:
#        smooth_time_vector = time_vector[:]
#    
#    reduced_time_vector = []
#    reduced_depth_vector = []
#    
#    #for k, depth in enumerate(depth_vector):
#    for k in range(min(len(depth_vector), len(time_vector))):
#        depth = depth_vector[k]
#        time_ = smooth_time_vector[k]
#        
#        if depth_vector[k] != 0:
#            reduced_depth_vector.append(depth)
#            reduced_time_vector.append(time_)
#    
#    if len(reduced_depth_vector) == 0:
#        log.warning('No valid bottom depths to np.interpolate from (all 0.0)')
#        return depth_vector
#    
#    else: 
#        interpolated_depth = np.interp(smooth_time_vector, reduced_time_vector, reduced_depth_vector)
#        return interpolated_depth

                
                
def calc_nmea_checksum(nmea_message):
    '''
    Calculates the propper checksum value based on nmea string
    with format $NMEA,some,data,inside*checksum

    :returns: str containing hex checksum
    '''

    nmea_string, _, orig_checksum = nmea_message.partition('*')[0]
    nmea_data = nmea_string.partition('$')[-1]

    checksum = 0
    for c in nmea_data:
        checksum ^= ord(c)

    return '%02X' % (checksum)             
            
            
def truncate_data_array(data, max_drop_percent=2.0):
    '''
    :param data: Data to truncate
    :type data: :class:np.ma.MaskedArray
    
    :param percent:  Upper limit of % valid data samples drop
    :type percent: float
    
    
    Attempts to find a new sample range that will minimize the final
    array size while dropping at most `max_drop_perecent` valid data
    samples.
    
    Helpful for data where there exists single deep-ping spikes that
    inflate a matrix with a large amount of masked values. 
    '''
    num_samples, num_pings = data.shape

    valid_sample_mask = ~data.mask
    #Total number of valid samples
    num_valid_samples = valid_sample_mask.sum()
    
    #Number of pings w/ valid sample @ each index
    valid_pings_per_sample = valid_sample_mask.sum(axis=1)
    
    #Number of pings w/ at least one valid sample
    num_valid_pings = (valid_sample_mask.sum(axis=0) > 0).sum()
    
    cumulative_valid_pings_per_sample = valid_pings_per_sample.cumsum()
    
    first_full_sample, last_full_sample = np.argwhere(valid_pings_per_sample == num_valid_pings)[[0, -1]]

    if first_full_sample == 0 and last_full_sample == num_samples - 1:
        log.info('  Full matrix, nothing to do...')
        return data
        
    #Push first_full_sample -> 1 if 0 to make sure loop runs
    if first_full_sample == 0:
        first_full_sample = 1
 
    new_ub = 0
    new_lb = num_samples
    new_final_size = np.prod(data.shape)
    new_valid_samples = num_valid_samples
    
#    if max_drop_percent > 1e:
#        drop_limit = max_drop_percent / 100.0
    if max_drop_percent < 0:
        raise ValueError("Invalid value for 'percent':  %s" % str(percent))
    else:
        drop_limit = max_drop_percent / 100.0


    
    for ub in range(first_full_sample):
        for lb in range(num_samples, last_full_sample, -1):
            num_valid = cumulative_valid_pings_per_sample[lb-1] - cumulative_valid_pings_per_sample[ub] \
                + cumulative_valid_pings_per_sample[0]
            frac_lost  = 1 - float(num_valid) / num_valid_samples
    
            if frac_lost > drop_limit:
                continue
    
            final_size = (lb - ub) * num_pings
    
            if final_size < new_final_size:
                new_ub = ub
                new_lb = lb
                new_final_size = final_size
                new_valid_samples = num_valid
                
                
    if new_ub == 0 and new_lb == num_samples:
        log.info('  Unable to resize data...')
        return data
    
    else:
        log.info('  New sample bounds:  %d:%d.  New array:  %.2fM samples, %.3f%% masked, %.3f%% dropped',
                 new_ub, new_lb, float(new_final_size)/1e6, 100 * (1 - new_valid_samples/float(new_final_size)),
                 100 * (1 - new_valid_samples/float(num_valid_samples)))

        return data[new_ub:new_lb, :]
    
    
    
    
    