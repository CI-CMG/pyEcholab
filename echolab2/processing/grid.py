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
    The grid class generates grid vertices and associated propertes for the provided
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

    When specifying interval length in time units, you must provide a Numpy timedelta64
    object defining the interval. For example, to specify a 30 minute interval:

        interval_length = numpy.timedelta64(30, 'm')


    """

    def __init__(self, interval_length=0.5, interval_axis='trip_distance_nmi',
            layer_thickness=10, layer_axis='depth', data=None, color=[0.0, 0.0, 0.0],
                 name='grid', linestyle='solid', linewidth=1.0, layer_start=0,
                 interval_start=None):
        """Initializes a new grid class object.

    Arguments:

        interval_length (float OR timedelta64):
        interval_axis (string):
        layer_thickness (float): specify the layer thickness in meters
        layer_axis (string): specify the processed_data attribute to use for the vertical
                axis. Can be 'range' or 'depth'

        color: color is a list of 3 floats [R, G, B] which defines the color
                of the grid line when plotted. Values are in the range of [0,1]
        name (string): name or label for the grid.
        linestyle: linestyle is a string that defines the style of the line.
        linewidth: linewidth is a float the defines the width of the line.

        """
        super(grid, self).__init__()

        # Initialize the grid attributes
        self.interval_length = interval_length
        self.interval_axis = interval_axis
        self.interval_start = interval_start
        self.layer_thickness = layer_thickness
        self.layer_axis = layer_axis
        self.layer_start = layer_start
        self.name = name
        self.linestyle = linestyle
        self.linewidth = linewidth
        self.color = color

        self.n_intervals = 0
        self.interval_edges = np.array([])
        self.interval_pings = np.array([])
        self.ping_interval_map = np.array([])
        self.n_layers = 0
        self.layer_edges = np.array([])
        self.layer_samples = np.array([])
        self.sample_layer_map = np.array([])

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

        # Generate the horizontal axis grid attributes. Note that if intervals are time based
        # we need to convert the datetime64[ms] values to float64 to use with histogram()
        # datetime64 objects store time as the number of datetime64 units from the Unix epoch.
        # Echolab2 uses datetime64 objects with millisecond resolution and when you convert
        # the time to a float, it is the number of ms since the epoch.

        # Get the horizontal axis data
        if  hasattr(p_data, self.interval_axis):
            axis_data = getattr(p_data, self.interval_axis).astype('float64')
        else:
            raise AttributeError("The provided processed_data object lacks the specified " +
                    "interval_axis attribute '" + self.interval_axis + "'.")

        # convert axis units if necessary
        if self.interval_axis == 'trip_distance_m':
            # Convert nmi to meters
            axis_data *= 1852

        # Convert the interval length if required and set interval start
        if self.interval_axis == 'ping_time':
            # Since the interval length can be specified in arbitrary time units
            # we must first get the interval length in ms then get that as a float64
            int_len = self.interval_length.astype('<m8[ms]').astype('float64')
            if self.interval_start:
                int_start = self.interval_start.astype('<m8[ms]').astype('float64')
            else:
                int_start = axis_data[0]
        else:
            # this is a distance based interval
            if self.interval_start:
                int_start = self.interval_start
            else:
                int_start = axis_data[0]

        # Update the horizontal axis properties
        self.n_intervals, interval_edges, self.interval_pings, self.ping_interval_map = \
                self._grid_axis(axis_data, int_start, int_len)

        if self.interval_axis == 'ping_time':
            # Convert the edges back to datetime64[ms]
            self.interval_edges = interval_edges.astype('<M8[ms]')
        else:
            self.interval_edges = interval_edges


        # Generate the vertical axis grid attributes
        if  hasattr(p_data, self.layer_axis):
            axis_data = getattr(p_data, self.layer_axis)
        else:
            raise AttributeError("The provided processed_data object lacks the specified " +
                    "layer_axis attribute '" + self.layer_axis + "'.")

        # Update the vertical axis properties
        self.n_layers, self.layer_edges, self.layer_samples, self.sample_layer_map = \
                self._grid_axis(axis_data, self.layer_start, self.layer_thickness)


    def _grid_axis(self, axis_data, axis_start, axis_size):
        '''
        _grid_axis is an internal method that generates the grid parameters for the
        provided axis_data and size (horizontal length or vertical height)
        '''

        # Get the span of the axis data
        span = axis_data[-1] - float(axis_start)

        # Compute the number of intervals/cells
        n_intervals = np.ceil(span / axis_size).astype('uint32')

        # compute the interval/cell edges, including the rightmost/bottommost edge
        axis_edges = (np.arange(n_intervals + 1) * axis_size) + float(axis_start)

        # create the axis mapping array - we include all pings/samples in an
        # interval/cell that are >= to the interval/cell start and < the interval/cell end
        axis_map = np.full(axis_data.shape, 0, dtype='uint32')
        n_els = np.full((n_intervals), 0, dtype='uint32')
        for b in range(n_intervals):
            mask = np.logical_and(axis_data >= axis_edges[b], axis_data < axis_edges[b+1])
            n_els[b] = mask.sum()
            axis_map[mask] = b

        return n_intervals, axis_edges, n_els, axis_map


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
