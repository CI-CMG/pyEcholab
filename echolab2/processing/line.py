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
from ..ping_data import ping_data


class line(ping_data):
    """The line class implements lines based on ping_time and depth/range values.
    The class provides methods manipulating these values in various ways. The
    numerical operators operate on the data, allowing offset lines to easily
    be created. Color and name properties can be used in plotting the lines.

    Attributes:
        ping_time (numpy array): ping_time is a array of datetime64 objects
                defining the horizontal vertices of the line.
        data: (None, float or numpy array): data can be None, a float or a 1d numpy
                array defining the line's vertical vertices. If data is None, the
                vertex data will be NaNs. If it is a float, the vertex values
                will be replicated for all vertices creating a flat horizontal line
                at the specified range/depth. If data is a numpy array, its shape
                must match the ping_time array.
        color: color is 3 element tuple [r, g, b] which defines the color of the line.
               What values you supply and how they are used is dependent on your
               plotting library. For example, Matplotlib accepts floats in the range
               0-1 while Qt accepts integers in the range 0-255.
        name (string): name or label for the line.
        linestyle: linestyle is a string that defines the style of the line.
        thickness: thickness is a float the defines the width of the line.
    """

    def __init__(self, ping_time=None, data=None, color=[0.58, 0.0, 0.83],
                 name='line', linestyle='solid', thickness=1.0, **_):
        """Initializes line class object.
        
        Args:
            ping_time (numpy array): ping_time is a array of datetime64 objects
                    defining the horizontal vertices of the line.
            data: (None, float or numpy array): data can be None, a float or a 1d numpy
                    array defining the line's vertical vertices. If data is None, the
                    vertex data will be NaNs. If it is a float, the vertex values
                    will be replicated for all vertices creating a flat horizontal line
                    at the specified range/depth. If data is a numpy array, its shape
                    must match the ping_time array.
            color: color is 3 element tuple [r, g, b] which defines the color of the line.
                   What values you supply and how they are used is dependent on your
                   plotting library. For example, Matplotlib accepts floats in the range
                   0-1 while Qt accepts integers in the range 0-255.
            name (string): name or label for the line.
            linestyle: linestyle is a string that defines the style of the line.
            thickness: thickness is a float the defines the width of the line.

        """
        super(line, self).__init__()

        # Set the ping time.
        self.ping_time = ping_time

        # if None is passed as data, change it to nan
        if data is None:
            data = np.nan

        # Set the number of pings.
        if ping_time is not None:
            self.n_pings = ping_time.shape[0]

        # Assign data based on what we're given. Arrays must be the same shape
        # as ping_time, scalars are expanded to the same shape as ping_time.
        if isinstance(data, np.ndarray):
            if data.ndim == 0:
                self.data = np.full(ping_time.shape[0], data, dtype='float32')
            else:
                if data.shape[0] == ping_time.shape[0]:
                    # assume that if we have been given the data as an array,
                    # we don't need to copy it. IOW, it is the user's responsibility.
                    self.data = data
                else:
                    # data array has a different number of elements
                    raise ValueError("The data array must be None, a scalar "
                                     "or an array the same size as ping_time.")
        else:
            try:
                data = float(data)
                self.data = np.full(ping_time.shape[0], data, dtype='float32')
            except Exception:
                raise ValueError("The data array must be None, a scalar or an"
                                 " array the same size as ping_time.")

        # Set the initial attribute values.
        self.color = color
        self.name = name
        self.linestyle = linestyle
        self.thickness = thickness

        # Update out data_attributes list, adding the "data" attribute.
        self._data_attributes += ['data']


#    def empty_like(self, **kwargs):
#        """Creates a line that matches "this" line except the depth/range values
#        are NaNs.
#
#        This method creates a line with the same number of vertices (i.e. ping_times)
#        as "this" line with the depth/range values set to NaNs. You can optionally
#        set the keywords defined below. If they are not provided, the values are copied
#        from "this" line.
#
#        Args:
#            color: color is 3 element tuple [r, g, b] which defines the color of the line.
#                    What values you supply and how they are used is dependent on your
#                    plotting library. For example, Matplotlib accepts floats in the range
#                    0-1 while Qt accepts integers in the range 0-255. If not provided, it
#                    is copied "this" line.
#            name (string): name or label for the line. If not provided, it is copied
#                    "this" line.
#            linestyle: linestyle is a string that defines the style of the line. If not
#                    provided, it is copied "this" line.
#            thickness: thickness is a float the defines the width of the line. If not
#                    provided, it is copied "this" line.
#        """
#        
#        return line.empty_like(self, **kwargs)
#
#
#    def like(self, data=None, **kwargs):
#        """Creates a line that matches "this" line. It may or may not be an exact copy
#        depending on the arguments passed.
#
#        This method creates a line with the same number of vertices (i.e.
#        ping_times) as "this" line. If no arguments are provided, this method
#        will return a copy of this line. You can provide arguments to 
#
#        Args:
#            data: (None, float or numpy array): data can be None, a float or a 1d numpy
#                    array defining the line's vertical vertices. If data is None, the
#                    vertex data will be NaNs. If it is a float, the vertex values
#                    will be replicated for all vertices creating a flat horizontal line
#                    at the specified range/depth. If data is a numpy array, its shape
#                    must match the ping_time array.
#            color: color is 3 element tuple [r, g, b] which defines the color of the line.
#                    What values you supply and how they are used is dependent on your
#                    plotting library. For example, Matplotlib accepts floats in the range
#                    0-1 while Qt accepts integers in the range 0-255. If not provided, it
#                    is copied "this" line.
#            name (string): name or label for the line. If not provided, it is copied
#                    "this" line.
#            linestyle: linestyle is a string that defines the style of the line. If not
#                    provided, it is copied "this" line.
#            thickness: thickness is a float the defines the width of the line. If not
#                    provided, it is copied "this" line.
#
#        Raise:
#            ValueError: The length of the data array does not match the length of
#                    the ping_time attribute.
#
#        """
#        
#        return line.like(self, **kwargs)


    def copy(self, **kwargs):
        """Returns a copy of this line object. 

        Args:
            None
        Returns:
            A copy of this echolab2 line object with attributes that are the
            same as "this" object.
        """
        
        return line.like(self)
        

    def _setup_numeric(self, other):
        """Internal method containing generalized numeric operators code.

         _setup_numeric is an internal method that contains generalized code for
        the numeric operators. Biggest job is interpolating ping times if the
        current line instance has a different number of pings from "other".

        Args:
            other(line object or array or scalar value): The data that is
            being used in the operator along with the line instance being
            operated on.

        Returns:
            The data from other if it's a line object or other if other is a
            scalar or array.
        """

        if isinstance(other, line):
            if other.data.shape[0] != self.data.shape[0]:
                # The other line has a different number of pings so
                # interpolate to this line's pings.
                other_data = np.interp(self.ping_time, other.ping_time,
                                       self.data, left=np.nan, right=np.nan)
            else:
                other_data = other.data
        else:
            # Assume this is a scalar or array that is compatible.
            other_data = other

        return other_data


    def __add__(self, other):
        """Implements the binary addition operator.

        __add__ implements the binary addition operator.

        Args:
            other(line object or array or scalar value): The data that is
                being added to the line instance being operated on.

        Returns:
            line object that is the result of adding "other" to the line object.
        """
        other_data = self._setup_numeric(other)
        new_line = empty_like(self)

        if isinstance(other, line):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data + other_data

        return new_line


    def __radd__(self, other):
        """Implements the reflected binary addition operator.

        __radd__ implements the reflected binary addition operator.

        Args:
            other(line object or array or scalar value): The data that is
                being reflected added to the line instance being operated on.

        Returns:
            line object that is the result of reflective adding "other" to
            the line object.
        """

        return self.__add__(other)


    def __iadd__(self, other):
        """Implements the in-place binary addition operator.

        __iadd__ implements the in-place binary addition operator

        Args:
            other(line object or array or scalar value): The data that is
                being added to the line instance being operated on.

        Returns:
            Returns original line object with "other" added to it.
        """

        other_data = self._setup_numeric(other)
        self.data[:] = self.data + other_data

        return self


    def __sub__(self, other):
        """Implements the binary subtraction operator.

        __sub__ implements the binary subtraction operator.

        Args:
            other(line object or array or scalar value): The data that is
                being subtracted from the line instance being operated on.

        Returns:
            New line object that is the original object minus "other".
        """

        other_data = self._setup_numeric(other)
        new_line = empty_like(self)
        if isinstance(other, line):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data - other_data

        return new_line


    def __rsub__(self, other):
        """Implements the reflected binary subtraction operator.

        __rsub__ implements the reflected binary subtraction operator.

        Args:
            other(line object or array or scalar value): The data that is
            being subtracted from the line instance being operated on.

        Returns:
            New line object that is the original object minus "other".
        """

        return self.__sub__(other)


    def __isub__(self, other):
        """Implements the in-place binary subtraction operator.

        __isub__ implements the in-place binary subtraction operator.

        Args:
            other(line object or array or scalar value): The data that is
            being subtracted from the line instance being operated on.

        Returns:
            Original line object with "other" subtracted from it.
        """
        other_data = self._setup_numeric(other)
        self.data[:] = self.data - other_data

        return self


    def __mul__(self, other):
        """Implements the binary multiplication operator.

        __mul__ implements the binary multiplication operator.

        Args:
            other(line object or array or scalar value): The data that is
            being multiplied with the line instance being operated on.

        Returns:
            New line object that is the original object multiplied by  "other".
        """

        other_data = self._setup_numeric(other)
        new_line = empty_like(self)
        if isinstance(other, line):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data * other_data

        return new_line


    def __rmul__(self, other):
        """Implements the reflected binary multiplication operator.

        __rmul__ implements the reflected binary multiplication operator.

        Args:
            other(line object or array or scalar value): The data that is
            being multiplied with the line instance being operated on.

        Returns:
            New line object that is the original object multiplied by  "other".
        """

        return self.__mul__(other)


    def __imul__(self, other):
        """Implements the in-place binary multiplication operator.

        __imul__ implements the in-place binary multiplication operator.

        Args:
            other(line object or array or scalar value): The data that is
            being multiplied with the line instance being operated on.

        Returns:
            Original line object multiplied by other".
        """

        other_data = self._setup_numeric(other)
        self.data[:] = self.data * other_data

        return self


    def __truediv__(self, other):
        """Implements the binary fp division operator.

        __truediv__ implements the binary fp division operator.

        Args:
            other(line object or array or scalar value): The data to divide the
            line instance being operated on.

        Returns:
            New line object that is the original line object divided bu other.
        """
        other_data = self._setup_numeric(other)
        new_line = empty_like(self)
        if isinstance(other, line):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data / other_data

        return new_line


    def __rtruediv__(self, other):
        """Implements the reflected binary fp division operator.

        __rtruediv__ implements the reflected binary fp division operator.

        Args:
            other(line object or array or scalar value): The data to divide the
            line instance being operated on.
        Returns:
            New line object that is the original line object divided bu other.
        """

        return self.__truediv__(other)


    def __itruediv__(self, other):
        """Implements the in-place binary fp division operator.

        __itruediv__ implements the in-place binary fp division operator.

        Args:
            other(line object or array or scalar value): The data to divide the
            line instance being operated on.

        Returns:
            Original line object divided by other.
        """

        other_data = self._setup_numeric(other)
        self.data[:] = self.data / other_data

        return self


    def __pow__(self, other):
        """Implements the binary power operator.

        __pow__ implements the binary power operator.

        Args:
            other(line object or array or scalar value): The data to raise the
            line instance being operated on.

        Returns:
            New line object that is the original line raided to "other".
        """
        other_data = self._setup_numeric(other)
        new_line = empty_like(self)
        if isinstance(other, line):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data ** other_data

        return new_line


    def __rpow__(self, other):
        """Implements the reflected binary power operator.

        __rpow__ implements the reflected binary power operator.

        Args:
            other(line object or array or scalar value): The data to raise the
            line instance being operated on.

        Returns:
            New line object that is the original line raided to "other".
        """

        return self.__pow__(other)


    def __ipow__(self, other):
        """Implements the in-place binary power operator.

        __ipow__ implements the in-place binary power operator.

        Args:
           other(line object or array or scalar value): The data to raise the
            line instance being operated on.

        Returns:
            Original line object that raided to "other".
        """

        other_data = self._setup_numeric(other)
        self.data[:] = self.data ** other_data

        return self


    def __str__(self):
        """Re-implements string method to provide basic information.

        Reimplemented string method that provides some basic info about the
        mask object.

        Return:
            A message with basic information about the mask object.
        """

        # Print the class and address.
        msg = "{0} at {1}\n".format(str(self.__class__), str(hex(id(self))))

        # Print some other basic information.
        msg = "{0}                 line name: {1}\n".format(msg, self.name)
        msg = "{0}             n data points: {1}\n".format(
                                                            msg,
                                                            self.data.shape[0])
        msg = "{0}                start time: {1}\n".format(msg,
                                                            self.ping_time[0])
        msg = "{0}                  end time: {1}\n" .format(msg,
                                                             self.ping_time[-1])

        return msg


def empty_like(like_obj, **kwargs):
    """Creates an empty line object with the same time values as the provided object.

    empty_like creates an empty line (where data values are NaN) that is the same
    length as the provided line or processed data object. If a line object is passed,
    the name and color attributes are copied if not explicitly provided. If a
    processed data object is passed the returned line will have the default line
    attributes if not explicitly provided.
    
    Args:
        like_obj (processed_data obj or line object): The object to base the
            mask off of. The line will have the same number of pings with the
            same ping times as the "like" object. If a processed_data object
            is provided, the ancillary properties such as color and thickness
            will be set to the default values. If a line object is provided
            these attributes will be copied.
    
    """

    # make sure the user didn't pass the data keyword
    kwargs.pop('data', None)
    
    # call line.like not passing anything for data which results in nans
    return like(like_obj, **kwargs)
    

def like(like_obj, data=None, **kwargs):
    """Creates a line that matches a provided data object. It may or may not be
    an exact copy depending on the arguments passed.

    This method creates a line with shape and axes properties that match an
    existing processed_data or line object. This 

    Args:
        like_obj (processed_data obj or line object): The object to base the
                line off of. The line will have the same number of pings with the
                same ping times as the "like" object. If a processed_data object
                is provided, the ancillary properties such as color and thickness
                will be set to the default values if none are provided. If a line
                object is provided these attributes will be copied if not
                explicitly provided.
        data: (None, float or numpy array): data can be None, a float or a 1d numpy
                array defining the line's vertical vertices. If data is None, the
                vertex data will be NaNs. If it is a float, the vertex values
                will be replicated for all vertices creating a flat horizontal line
                at the specified range/depth. If data is a numpy array, its shape
                must match the ping_time array.
        color: color is 3 element tuple [r, g, b] which defines the color of the line.
                What values you supply and how they are used is dependent on your
                plotting library. For example, Matplotlib accepts floats in the range
                0-1 while Qt accepts integers in the range 0-255. If not provided, it
                is copied "this" line.
        name (string): name or label for the line. If not provided, it is copied
                "this" line.
        linestyle: linestyle is a string that defines the style of the line. If not
                provided, it is copied "this" line.
        thickness: thickness is a float the defines the width of the line. If not
                provided, it is copied "this" line.

    Raise:
        ValueError: The length of the data array does not match the length of
                the ping_time attribute.
    """

    # lines must be based on processed_data objects or other lines.
    # Use type().__name__ to determine if class of "like_obj" is a 
    # processed_data object to avoid circular import references
    if type(like_obj).__name__ == 'processed_data':
        # Base this line off of a processed_data object.
        new_line = line(ping_time=like_obj.ping_time.copy(),
            data=data, **kwargs)
        
    elif isinstance(like_obj, line):
        # Base this line off of another line. If the user doesn't provide an 
        # argument we copy the attribute from the provided line.
        
        if data is None:
            data = like_obj.data.copy()
        if 'color' not in kwargs:
            color = like_obj.color.copy()
        if 'name' not in kwargs:
            name = like_obj.name
        if 'linestyle' not in kwargs:
            linestyle = like_obj.linestyle
        if 'thickness' not in kwargs:
            thickness = like_obj.thickness

        new_line = line(ping_time=like_obj.ping_time.copy(),
            data=data, color=color, name=name, linestyle=linestyle,
            thickness=thickness)

    return new_line


def read_evl(evl_filename, name='evl_line', ignore_status=False, **kwargs):
    '''read_evl will read a .evl file exported by Echoview and return a line object
    containing the Echoview line data. Vertices that have a status other than 3 ("good")
    will be assigned NaN.

    evl_filename (string): The full path to the Echoview .evl file to read
    name (string): name or label for the line.
    ignore_status (bool): Set to True to ignore the .evl vertex status. Vertices in
        Echoview .evl files are assigned a status where:
            0 = no status
            1 = unverified
            2 = bad
            3 = good
        By default, status values less than 3 are assigned a value of NaN. Set this
        keyword to True to assign depth values to the vertices regardeless of status.
        Note that vertices with the special value of -10000.99 are always assigned NaN
    color: color is a list which defines the color of the line.
    linestyle: linestyle is a string that defines the style of the line.
    thickness: thickness is a float the defines the width of the line.

    '''

    import os
    from datetime import datetime

    def convert_float(val):
        try:
            val = float(val)
        except:
            val = np.nan
        return val

    # Normalize filename and read the file
    evl_filename = os.path.normpath(evl_filename)
    with open(evl_filename, 'r') as infile:
        evl_data = infile.readlines()

    # Discard the file headers
    evl_data = evl_data[2:]

    #  determine the number of line vertices
    n_pings = len(evl_data)

    # Echoview .evl files contain ping time, depth, and line status data.
    # Create the time and depth arrays. Status is used to determine if the
    # depth data is valid or a Nan is inserted instead
    depth_data = np.empty((n_pings), dtype=np.float32)
    ping_time = np.empty((n_pings), dtype='datetime64[ms]')

    # Loop thru the rows of data, parsing each line
    for idx, row in enumerate(evl_data):
        #  strip the trailing whitespace
        row.rstrip()

        # Parse the elements
        (d, t, depth, status) = row.split(maxsplit=3)

        # Use date and time strings to make numpy datetime object
        ping_time[idx] = np.datetime64(datetime.strptime(d + t, "%Y%m%d%H%M%S%f"))

        # Convert depth and status to floats
        depth = convert_float(depth)
        if ignore_status:
            # Assume all points are valid
            status = 3
        else:
            status = convert_float(status)

        # Assign the depth value based on the status. For our purposes, any status
        # less than 3 in an .evl file will be considered "bad" and assigned NaN. Also,
        # .evl files have a special value (-10000.99000 ) used to indicate an invalid
        # sounder detected bottom vertex and these will also be assigned NaN.
        if status < 3 or depth < -10000.0:
            # This is an invalid vertex
            depth_data[idx] = np.nan
        else:
            depth_data[idx] = depth

    # Create the line object to return
    ev_line = line(ping_time=ping_time, data=depth_data, name=name, **kwargs)

    return ev_line


def read_xyz(xyz_filename, name='xyz_line', as_range=False, calibration=None,
        **kwargs):
    '''read_xyz will read a Simrad EK80 .xyz file and return a line object
    containing the bottom detection data.

    xyz_filename (string): The full path to the .xyz file to read
    name (string): name or label for the line.

    calibration (EK80.ek80_calibration): Set to an instance of EK80.ek80_calibration
                containing the calibration parameters
                you used when transforming to Sv/sv. The shound speed value in
                the calibration object will be used to shift the bottom detections
                if the sound speed used during data recording is different than
                the sound speed specified in this object.

    color: color is a list which defines the color of the line.
    linestyle: linestyle is a string that defines the style of the line.
    thickness: thickness is a float the defines the width of the line.

    '''

    import os
    from datetime import datetime

    def convert_float(val):
        try:
            val = float(val)
        except:
            val = np.nan
        return val

    # Normalize filename and read the file
    xyz_filename = os.path.normpath(xyz_filename)
    with open(xyz_filename, 'r') as infile:
        xyz_data = infile.readlines()

    #  determine the number of line vertices
    n_points = len(xyz_data)

    # Simrad .xyz files contain Lat, Lon, depth, date, time, and transducer draft
    depth_data = np.empty((n_points), dtype=np.float32)
    lat_data = np.empty((n_points), dtype=np.float32)
    lon_data = np.empty((n_points), dtype=np.float32)
    draft_data = np.empty((n_points), dtype=np.float32)
    ping_time = np.empty((n_points), dtype='datetime64[ms]')

    # Loop thru the rows of data, parsing each line
    for idx, row in enumerate(xyz_data):
        #  split the row
        parts = row.split()
        n_parts = len(parts)

        if n_parts == 8:
            #  this is the XYZ format introduced in EK80 21.15.x with hemisphere
            (lat, lat_h, lon, lon_h, depth, date, time, draft) = parts

            #  convert lat/lon to floats
            lat = convert_float(lat)
            lon = convert_float(lon)

            #  add the sign to the lat/lon
            lat *= 1 if lat_h == 'N' else -1
            lon *= 1 if lon_h == 'E' else -1

        elif n_parts == 6:
            #  this is the OG XYZ with signed lat/lon
            (lat, lon, depth, date, time, draft) = parts
            
            #  convert lat/lon to floats
            lat = convert_float(lat)
            lon = convert_float(lon)

        else:
            #  this XYZ file is not what we were expecting
            raise Exception('Unknown XYZ format with %d fields' % n_parts)

        # Convert the time elements to datetime64
        ping_time[idx] = np.datetime64(datetime.strptime(date + time, "%d%m%Y%H%M%S.%f"))

        # Convert depth and draft to floats
        draft_data[idx] = convert_float(draft)
        if as_range:
            depth_data[idx] = convert_float(depth) - draft_data[idx]
        else:
            depth_data[idx] = convert_float(depth)

        # Store lat and lon
        lat_data[idx] = lat
        lon_data[idx] = lon

    # Create the line object to return
    xyz_line = line(ping_time=ping_time, data=depth_data, name=name, **kwargs)

    # Add the additional data attributes
    xyz_line.add_data_attribute('latitude', lat_data)
    xyz_line.add_data_attribute('longitude', lon_data)
    xyz_line.add_data_attribute('transducer_draft', draft_data)

    return xyz_line

