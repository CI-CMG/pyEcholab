# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

# THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
# AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
# IS. THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
# OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
# AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
# THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
# DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assessment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import numpy as np

class grid(object):

    """
    The grid class generates grid vertices and associated properties for the provided
    processed_data object and can be used both for display purposes and echo-integration.

    The grid is generated using the specified horizontal axis and width value, and the
    specified vertical axes and height value. Note that the processed_data object must
    contain the attributes specified as the horizontal and vertical axes. An error will
    be raised if the provided processed_data object lacks one of the required attributes.

    The vertical axis can be specified as 'range' or 'depth' and the units are always
    meters. The horizontal axes units and required attribute depends on the axis selected:

                            required processed_data
    interval_axis value           attribute             interval_length units
    ---------------------------------------------------------------------------
    trip_distance_nmi         trip_distance_nmi             nautical miles
     trip_distance_m          trip_distance_nmi                meters
        ping_time                 ping_time                  timedelta64
       ping_number                 <none>                      pings

    When specifying interval length in time units, you must provide a Numpy timedelta64
    object defining the interval. For example, to specify a 30 minute interval:

        interval_length = numpy.timedelta64(30, 'm')


    The primary grid attributes are

        n_intervals: the number of intervals in the grid

        interval_edges: the location of the interval boundaries including the right
            boundary of the last interval. There are n_intervals + 1 edges.

        interval_pings: the number of pings in each interval

        ping_interval_map:
        n_layers
        layer_edges
        layer_samples
        sample_layer_map


    """

    def __init__(self, interval_length=0.5, interval_axis='trip_distance_nmi',
            layer_thickness=10, layer_axis='depth', data=None, color=[0.0, 0.0, 0.0],
                 name='grid', linestyle='solid', linewidth=1.0, interval_start=None,
                 round_interval_starts=True, interval_end=None, layer_start=0,
                 layer_end=None):
                 
        """Initializes a new grid class object.

    Arguments:

        interval_length (int OR float OR timedelta64): Specify the length of the grid intervals in
                units specified in the interval_axis keyword argument.
        interval_axis (string): A string specifying the horizontal axis to use when creating
                the grid. Valid values are:
                    trip_distance_nmi: The horizontal grid will be based on the vessel log
                            distance in nautical miles. Interval length is specified as a float.
                    trip_distance_m: The horizontal grid will be based on the vessel log
                            distance in meters. Interval length is specified as a float.
                    ping_time: The horizontal grid will be based on the ping time. Interval
                            length is specified as a timedelta64 object.
                    ping_number: The horizontal grid will be based on the ping number. Interval
                            length is specified as a integer.

        round_interval_starts (bool): When set to True, the grid will 
        
        
        layer_thickness (float): specify the layer thickness in meters
        layer_axis (string): specify the processed_data attribute to use for the vertical
                axis. Can be 'range' or 'depth'

        ignore_first_sample (bool): set ignore_first_sample to True to start the grid layers
                at the second sample. Echoview discards the first sample and setting this
                to True will match that behavior when integrating.
                
                    default: True

        color: color is a list of 3 floats [R, G, B] which defines the color
                of the grid line when plotted. Values are in the range of [0,1]
        name (string): name or label for the grid.
        linestyle: linestyle is a string that defines the style of the line when plotted.
        linewidth: linewidth is a float the defines the width of the line when plotted.

        """
        super(grid, self).__init__()

        # Initialize the grid attributes
        self.interval_length = interval_length
        self.interval_axis = interval_axis
        self.interval_start = interval_start
        
        self.interval_end = interval_end
        
        self.round_interval_starts = round_interval_starts
        self.layer_thickness = layer_thickness
        self.layer_axis = layer_axis
        self.layer_start = layer_start
        self.layer_end = layer_end
        self.name = name
        self.linestyle = linestyle
        self.linewidth = linewidth
        self.color = color

        # data dependent attributes
        self.n_intervals = 0
        self.interval_edges = np.array([])
        self.interval_pings = np.array([])
        self.ping_interval_map = np.array([])
        self.n_layers = 0
        self.layer_edges = np.array([])
        self.layer_samples = np.array([])
        self.sample_layer_map = np.array([])
        self.grid_data = None
        self.interval_axis_data = None
        self.interval_ping_start = np.array([])
        self.interval_ping_middle = np.array([])
        self.interval_ping_end = np.array([])
        self.interval_time_start = np.array([])
        self.interval_time_middle = np.array([])
        self.interval_time_end = np.array([])
        self._iter_interval = 0
        self._iter_layer = 0
        self._gc_last_interval = -1
        self._gc_last_layer = -1

        # If data is provided, update the grid
        if data:
            self.update(data)


    def update(self, p_data):
        """
        update 'applies' the grid to the provided processed_data object.

        When update is called, the ping_interval_map and sample_layer_map (and associated properties)
        are updated based on the object's current interval length, layer thickness, interval axis and
        layer axis properties.
        """

        # Echolab2 uses datetime64 objects with millisecond resolution and when you convert
        # the time to a float, it is the number of ms since the epoch.

        # Get the horizontal axis data - ping_number is special since we have to create it
        if self.interval_axis == 'ping_number':
            axis_data = np.arange(p_data.n_pings, dtype='float32')
        else:
            if  hasattr(p_data, self.interval_axis):
                # get a copy of the interval axis data
                axis_data = getattr(p_data, self.interval_axis).copy().astype('float64')
            else:
                raise AttributeError("The provided processed_data object lacks the specified " +
                        "interval_axis attribute '" + self.interval_axis + "'.")

        # nan axis data outside our axis range
        nan_mask = np.zeros(axis_data.shape, dtype='bool')
        if self.interval_start is not None:
            int_start = self.interval_start
            if self.interval_axis == 'ping_time':
                int_start = int_start.astype('<M8[ms]').astype('float64')
            nan_mask[axis_data < int_start] = True
        else:
            int_start = axis_data[0]
        if self.interval_end is not None:
            int_end = self.interval_end
            if self.interval_axis == 'ping_time':
                int_end = int_end.astype('<M8[ms]').astype('float64')
            nan_mask[axis_data > int_end] = True
        else:
            int_end = axis_data[-1]
        axis_data[nan_mask] = np.nan
            
        # convert axis units if necessary
        if self.interval_axis == 'trip_distance_m':
            # Convert nmi to meters
            axis_data *= 1852

        # Convert the interval length if required and set interval start
        if self.interval_axis == 'ping_time':
            # Since the interval length can be specified in arbitrary time units
            # we must first get the interval length in ms then get that as a float64
            int_len = self.interval_length.astype('<m8[ms]').astype('float64')
            
            if self.round_interval_starts:
                #  we're creating a grid with inner intervals that start at times rounded
                #  to the interval length. For example, if you have a 5 minute interval and
                #  your data starts at 12:03 and stops at 12:26, the grid edges would be at
                #  12:03, 12:05, 12:10, 12:15, 12:20, and 12:26.
                
                #  determine the interval length units and set the rounding units
                dtype_str = str(self.interval_length.dtype)
                dtype_units = dtype_str[dtype_str.find('['):]
                round_dtype = 'datetime64' + dtype_units
                
                # find the pings closest to the rounded interval - this will also include
                # the first ping which we will ignore later.
                rounded_edges = np.mod(axis_data, int_len)
                rounded_edges = (np.r_[True, rounded_edges[1:] < rounded_edges[:-1]] &
                        np.r_[rounded_edges[:-1] < rounded_edges[1:], True])
                # now convert back to datetime64[ms] so we can round
                rounded_edges = axis_data[rounded_edges].astype('datetime64[ms]')
                # and then round to the interval length unit
                rounded_edges =  rounded_edges.astype(round_dtype)
                # finally convert back to datetime64[ms] and then to float
                rounded_edges =  rounded_edges.astype('datetime64[ms]').astype('float64')
                n_rounded = len(rounded_edges)
                        
                # now build the array of edges including the start, the rounded edges
                # and the last ping. First create the edges array
                axis_edges = np.empty((n_rounded + 1), dtype='float64')
                # add the first and last edge
                axis_edges[0] = int_start
                axis_edges[-1] = int_end
                # and add the rounded inner edges (discarding the rounded first ping)
                axis_edges[1:n_rounded] = rounded_edges[1:]
                
            else:
                # for non-rounded interval starts we compute the edges in the _grid_axis() method
                axis_edges = None
                
        else:
            # This is a distance or ping number based interval

            # Set the interval length
            int_len = self.interval_length

            # Check if we're rounding the interval starts
            if self.round_interval_starts:
                #  we're creating a grid with inner intervals that start at distance/pings 
                #  rounded to the interval length. For example, if you have an interval
                #  length of 0.5 nmi and the data starts at 231.3 nmi and stops at 233.6,
                #  the grid edges will be at 231.3, 231.5, 232.0, 232.5, 233.0, 233.5, and
                #  233.6.
                
                # find the pings closest to the rounded interval - this will also include
                # the first ping which we will ignore later.
                rounded_edges = np.mod(axis_data, int_len)
                rounded_edges = (np.r_[True, rounded_edges[1:] < rounded_edges[:-1]] &
                        np.r_[rounded_edges[:-1] < rounded_edges[1:], True])

                # determine the rounding factor
                int_len_parts = repr(float(int_len)).split('.')
                if int(int_len_parts[1]) > 0:
                    # the interval length is fractional - we'll round on the RHS of the decimal
                    round_factor = len(int_len_parts[1])
                else:
                    # the interval length is a whole number - figure out what position to
                    # round to on the LHS of the decimal
                    round_factor = 0
                    for x in range(len(int_len_parts[0]) - 1, -1, -1):
                        if int_len_parts[0][x] != '0':
                            break
                        round_factor -= 1
                
                # and round the edges
                rounded_edges = np.round(axis_data[rounded_edges], round_factor)
                n_rounded = len(rounded_edges)
                        
                # now build the array of edges including the start, the rounded edges
                # and the last ping. First create the edges array
                axis_edges = np.empty((n_rounded + 1), dtype='float64')
                # add the first and last edge
                axis_edges[0] = int_start
                axis_edges[-1] = int_end
                # and add the rounded inner edges (discarding the rounded first ping)
                axis_edges[1:n_rounded] = rounded_edges[1:]
                
            else:
                # for non-rounded interval starts we compute the edges in the _grid_axis() method
                axis_edges = None

        # Update the horizontal axis properties
        self.n_intervals, interval_edges, self.interval_pings, self.ping_interval_map = \
                self._grid_axis(axis_data, int_len, axis_edges=axis_edges, axis_start=int_start,
                axis_end=int_end)

        if self.interval_axis == 'ping_time':
            # Convert the edges back to datetime64[ms]
            self.interval_edges = interval_edges.astype('<M8[ms]')
        else:
            self.interval_edges = interval_edges

        #  store the horizontal axis data
        self.interval_axis_data = axis_data

        # Generate the vertical axis grid attributes
        if  hasattr(p_data, self.layer_axis):
            axis_data = getattr(p_data, self.layer_axis)
        else:
            raise AttributeError("The provided processed_data object lacks the specified " +
                    "layer_axis attribute '" + self.layer_axis + "'.")

        # set the layer start and end
        if self.layer_start is not None:
            layer_start = self.layer_start
        else:
            layer_start = axis_data[0]
        if self.layer_end is not None:
            layer_end = self.layer_end
        else:
            layer_end = axis_data[-1]
            
        # Update the vertical axis properties
        self.n_layers, self.layer_edges, self.layer_samples, self.sample_layer_map = \
                self._grid_axis(axis_data, self.layer_thickness, axis_start=layer_start,
                axis_end=layer_end)

        #  store a reference to the data used to generate the grid
        self.grid_data = p_data
        
        # lastly, update the extended grid attributes
        self._update_extended_attributes()


    def get_cell_data(self, interval, layer, data_obj):
        '''
        get_cell_data will return a numpy array containing the data in the
        provided data_obj contained within the grid cell defined by the
        provided interval and layer values.
        
        You do not have to pass the same data object that the grid is based
        upon, but it must share the same size and axes otherwise it will
        raise an error.

        interval and layer numbers start at 0 with the upper left cell at
        (0,0)


        '''

        #  make sure we've been given sane interval and layer values
        if (interval >= self.n_intervals) or (interval < 0):
            # this interval doesn't exist in this grid
            return np.array([], dtype='float32')
        if (layer >= self.n_layers) or (layer < 0):
            # this layer doesn't exist in this grid
            return np.array([], dtype='float32')

        # Make sure the data_obj has the same axes as the grid
        if not np.array_equal(self.grid_data.ping_time, data_obj.ping_time):
            raise ValueError("The provided data_obj's ping times do not " +
                    "match the grid's ping times.")

        # Make sure the vertical axes are the same
        if hasattr(self.grid_data, 'range'):
            if hasattr(data_obj, 'range'):
                if not np.array_equal(self.grid_data.range, data_obj.range):
                    raise ValueError("The grid's ranges and provided data_obj's " +
                            "ranges do not match.")
            else:
                raise AttributeError("The grid is range based but the provided data_obj " +
                        "doesn't have the range attribute.")
        else:
            if hasattr(data_obj, 'depth'):
                if not np.array_equal(self.grid_data.depth, data_obj.depth):
                    raise ValueError("The grid's depths and provided data_obj's " +
                            "depths do not match.")
            else:
                raise AttributeError("The grid is depth based but the provided data_obj " +
                        "doesn't have the depth attribute.")

        #  check if we need to create a new interval index
        if interval != self._gc_last_interval:
            self._interval_pings = self.ping_interval_map == interval
            self._gc_last_interval = interval

        #  check if we need to create a new layer index
        if layer != self._gc_last_layer:
            self._layer_samples = self.sample_layer_map == layer
            self._gc_last_layer = layer

        #  return the data and the mask
        return data_obj[self._interval_pings,:][:,self._layer_samples]


    def get_cell_mask(self, interval, layer):
        '''
        get_cell_data will return a numpy array of the sample data contained
        in the provided interval and layer as well as a mask

        '''

        #  make sure we've been given sane interval and layer values
        if (interval >= self.n_intervals) or (interval < 0):
            # this interval doesn't exist in this grid
            return np.array([], dtype='float32')
        if (layer >= self.n_layers) or (layer < 0):
            # this layer doesn't exist in this grid
            return np.array([], dtype='float32')

        #  check if we need to create a new interval index
        if interval != self._gc_last_interval:
            self._interval_pings = self.ping_interval_map == interval
            self._gc_last_interval = interval

        #  check if we need to create a new layer index
        if layer != self._gc_last_layer:
            self._layer_samples = self.sample_layer_map == layer
            self._gc_last_layer = layer

        #  return the mask
        return self._layer_samples & self._interval_pings[:, np.newaxis]


    def _grid_axis(self, axis_data, axis_size, axis_edges=None, axis_start=None,
            axis_end=None):

        '''
        _grid_axis is an internal method that generates the grid parameters for the
        provided axis_data and size (horizontal length or vertical height)
        '''
            
        #  check if we've been given explicit edges
        if axis_edges is None:
            # Get the span of the axis data
            span = float(axis_end) - float(axis_start)

            # Compute the number of intervals/cells
            n_units = np.ceil(span / axis_size).astype('uint32')

            # compute the interval/cell edges, including the rightmost/bottommost edge
            axis_edges = (np.arange(n_units + 1) * axis_size) + float(axis_start)
            axis_edges[-1] = axis_end
        else:
            # we have, get the number of intervals/cells
            n_units = len(axis_edges) - 1

        # create the axis mapping array - we include all pings/samples in an interval/cell
        # that are >= to the interval/cell start and < the interval/cell end EXCEPT FOR
        # THE LAST INTERVAL where we include the last ping if it <= the interval/cell end.
        axis_map = np.full(axis_data.shape, 0, dtype='uint32')
        n_els = np.full((n_units), 0, dtype='uint32')
        for b in range(n_units):
            if b < (n_units - 1):
                # for all intervals up to the last interval - include >= start and < end
                mask = np.logical_and(axis_data >= axis_edges[b], axis_data < axis_edges[b+1])
            else:
                # for the last interval, include >= start and <= end to ensure last ping is captured
                mask = np.logical_and(axis_data >= axis_edges[b], axis_data <= axis_edges[b+1])
            n_els[b] = mask.sum()
            axis_map[mask] = b

        return n_units, axis_edges, n_els, axis_map


    def _update_extended_attributes(self):
        '''
        _update_extended_attributes is an internal method called after the initial grid
        is created. This method updates the "extended" grid properties which are things
        like the start, middle, and end ping times for each grid interval and start, middle,
        and end layer ranges or depths. If the processed data object the grid is based on
        has navigation data associated with it, the additional properties like start, middle
        and end lat/lon, mean speed, and start/middle/stop vessel log data will also
        be created/updated.
        '''
        
        # initialize attributes all data objects should have.
        self.interval_ping_start = np.empty((self.n_intervals), dtype='uint32')
        self.interval_ping_middle = np.empty((self.n_intervals), dtype='uint32')
        self.interval_ping_end = np.empty((self.n_intervals), dtype='uint32')
        self.interval_time_start = np.empty((self.n_intervals), dtype='datetime64[ms]')
        self.interval_time_middle = np.empty((self.n_intervals), dtype='datetime64[ms]')
        self.interval_time_end = np.empty((self.n_intervals), dtype='datetime64[ms]')
        
        # initialize the layer property arrays - we will assign these to an attribute below
        ax_start = np.empty((self.n_layers), dtype='float32')
        ax_middle = np.empty((self.n_layers), dtype='float32')
        ax_end = np.empty((self.n_layers), dtype='float32')
        
        # now initialize attributes for optional attributes.
        if hasattr(self.grid_data, 'latitude'):
            self.interval_lat_start = np.full((self.n_intervals), np.nan)
            self.interval_lat_middle = np.full((self.n_intervals), np.nan)
            self.interval_lat_end = np.full((self.n_intervals), np.nan)
        if hasattr(self.grid_data, 'longitude'):
            self.interval_lon_start = np.full((self.n_intervals), np.nan)
            self.interval_lon_middle = np.full((self.n_intervals), np.nan)
            self.interval_lon_end = np.full((self.n_intervals), np.nan)
        if hasattr(self.grid_data, 'spd_over_grnd_kts'):
            self.interval_mean_sog = np.full((self.n_intervals), np.nan)
        if hasattr(self.grid_data, 'trip_distance_nmi'):
            self.interval_trip_distance_nmi_start = np.full((self.n_intervals), np.nan)
            self.interval_trip_distance_nmi_middle = np.full((self.n_intervals), np.nan)
            self.interval_trip_distance_nmi_end = np.full((self.n_intervals), np.nan)
        
        # generate the layer properties
        for l in range(self.n_layers):
            ax_start[l] = self.layer_edges[l]
            ax_middle[l] = self.layer_edges[l] + (self.layer_edges[l + 1] - self.layer_edges[l]) / 2.0
            ax_end[l] = self.layer_edges[l + 1]
            
        # assign layer attributes based on the vertical axis
        _, v_axis = self.grid_data.get_v_axis()
        setattr(self, 'layer_' + v_axis + '_start', ax_start)
        setattr(self, 'layer_' + v_axis + '_middle', ax_middle)
        setattr(self, 'layer_' + v_axis + '_end', ax_end)
        
        # now generate the interval properties
        # first create a ping vector (processed data objects don't usually have a ping number attribute)
        ping_idx = np.arange(self.grid_data.n_pings, dtype='float32')
        # then work thru the intervals
        for i in range(self.n_intervals):
            # get a bool mask of this interval's pings
            ping_map = self.ping_interval_map == i
            #  and get the middle ping relative to this interval
            int_middle_ping = np.floor(self.interval_pings[i] / 2.0).astype('uint32')
            
            #  create the ping number axis (pings start at 1) and assign values
            ax_data = ping_idx[ping_map] + 1
            self.interval_ping_start[i] = ax_data[0]
            self.interval_ping_middle[i] = ax_data[0] + int_middle_ping
            self.interval_ping_end[i] = ax_data[-1]
            
            # get the time axis and assign values
            ax_data = self.grid_data.ping_time[ping_map]
            self.interval_time_start[i] = ax_data[0]
            self.interval_time_middle[i] = ax_data[int_middle_ping]
            self.interval_time_end[i] = ax_data[-1]
        
            # now do some of the optional attributes
            if hasattr(self.grid_data, 'latitude'):
                ax_data = self.grid_data.latitude[ping_map]
                self.interval_lat_start[i] = ax_data[0]
                self.interval_lat_middle[i] = ax_data[int_middle_ping]
                self.interval_lat_end[i] = ax_data[-1]
            if hasattr(self.grid_data, 'longitude'):
                ax_data = self.grid_data.longitude[ping_map]
                self.interval_lon_start[i] = ax_data[0]
                self.interval_lon_middle[i] = ax_data[int_middle_ping]
                self.interval_lon_end[i] = ax_data[-1]
            if hasattr(self.grid_data, 'spd_over_grnd_kts'):
                ax_data = self.grid_data.spd_over_grnd_kts[ping_map]
                ax_data = np.nanmean(ax_data)
                self.interval_mean_sog[i] = ax_data
            if hasattr(self.grid_data, 'trip_distance_nmi'):
                ax_data = self.grid_data.trip_distance_nmi[ping_map]
                self.interval_trip_distance_nmi_start[i] = ax_data[0]
                self.interval_trip_distance_nmi_middle[i] = ax_data[int_middle_ping]
                self.interval_trip_distance_nmi_end[i] = ax_data[-1]

 
    def __str__(self):
        """Re-implements string method to provide basic information.

        Reimplemented string method that provides some basic info about the
        grid object.

        Return:
            A message with basic information about the grid object.
        """

        # Print the class and address.
        msg = "{0} at {1}\n".format(str(self.__class__), str(hex(id(self))))

        # Print some other basic information.
        msg = "{0}                 grid name: {1}\n".format(msg, self.name)
        msg = "{0}           horizontal axis: {1}\n".format(msg, self.interval_axis)
        msg = "{0}           interval length: {1}\n".format(msg, str(self.interval_length))
        msg = "{0}               n intervals: {1}\n".format(msg, self.n_intervals)
        msg = "{0}                layer axis: {1}\n".format(msg, self.layer_axis)
        msg = "{0}           layer thickness: {1}\n".format(msg, self.layer_thickness)
        msg = "{0}                  n layers: {1}\n".format(msg, self.n_layers)

        return msg
