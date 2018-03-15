# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS IS."
#  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES, OFFICERS,
#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED, AS TO THE USEFULNESS
#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE. THEY ASSUME NO RESPONSIBILITY
#  (1) FOR THE USE OF THE SOFTWARE AND DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL
#  SUPPORT TO USERS.

"""


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assesment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import numpy as np


class line(object):
    '''
    The line class implements lines based on ping_time and depth/range values.
    The class provides methods manipulating these values in various ways. The
    numerical operators operate on the data, allowing offset lines to easily
    be created. Color and name properties can be used in plotting the lines.
    '''

    def __init__(self, ping_time=None, data=None, color=[148,0,211], name='line'):

        super(line, self).__init__()

        #  set the ping time
        self.ping_time = ping_time

        #  assign data based on what we're given. Arrays must be the same shape
        #  as ping_time, scalars are expanded to the same shape as ping_time
        #  and None is None.
        if (isinstance(data, np.ndarray)):
            if (data.ndim == 0):
                data = np.full(ping_time.shape[0], data, dtype='float32')
            else:
                if (data.shape[0] != ping_time.shape[0]):
                    raise ValueError("The data array must be None, a scalar " +
                            "or an array the same size as ping_time.")
        else:
            try:
                data = float(data)
                data = np.full(ping_time.shape[0], data, dtype='float32')
            except:
                raise ValueError("The data array must be None, a scalar " +
                            "or an array the same size as ping_time.")
        self.data = data

        #  set the initial attribute values
        self.color = color
        self.name = name


    def empty_like(self, line_obj, name=None, color=None):
        """
        empty_like creates an empty line (where data values are NaN) that
        is the same length as the provided line object. The name and
        color attributes are copied if not explicitly provided.
        """
        #  create a new line object to return
        new_line = line(ping_time=line_obj.ping_time.copy())

        #  check if new props were provided
        if (color):
            new_line.color = color
        else:
            new_line.color = line_obj.color
        if (name):
            new_line.name = name
        else:
            new_line.name = line_obj.name

        #  set the data array to NaNs
        new_line.data = np.full(new_line.ping_time.shape[0], np.nan)

        #  and return the new line object
        return new_line


    def interpolate(self, new_times):
        """
        interpolate interpolates the data values to the provided time vector.
        """
        self.data[:] = np.interp(self.ping_time, new_times,
                    self.data, left=np.nan, right=np.nan)
        self.ping_time = new_times.copy()


    def _setup_numeric(self, other):
        """
        _setup_numeric is an internal method that contains generalized code for
        the numeric operators.
        """

        if (isinstance(other, line)):
            if (other.data.shape[0] != self.data.shape[0]):
                #  the other line has a different number of pings
                #  so interpolate to this line's pings
                other_data = np.interp(self.ping_time, other.ping_time,
                    self.data, left=np.nan, right=np.nan)
            else:
                other_data = other.data
        else:
            #  assume this is a scalar or array thats compatible
            other_data = other

        return other_data


    def __add__(self, other):
        """
        __add__ implements the binary addition operator
        """
        other_data = self._setup_numeric(other)
        new_line = self.empty_like(self)
        if (isinstance(other, line)):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data + other_data

        return new_line


    def __radd__(self, other):
        """
        __radd__ implements the reflected binary addition operator
        """

        return self.__add__(other)


    def __iadd__(self, other):
        """
        __iadd__ implements the in-place binary addition operator
        """
        other_data = self._setup_numeric(other)
        self.data[:] = self.data + other_data

        return self


    def __sub__(self, other):
        """
        __sub__ implements the binary subtraction operator
        """
        other_data = self._setup_numeric(other)
        new_line = self.empty_like(self)
        if (isinstance(other, line)):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data - other_data

        return new_line


    def __rsub__(self, other):
        """
        __rsub__ implements the reflected binary subtraction operator
        """

        return self.__sub__(other)


    def __isub__(self, other):
        """
        __isub__ implements the in-place binary subtraction operator
        """
        other_data = self._setup_numeric(other)
        self.data[:] = self.data - other_data

        return self


    def __mul__(self, other):
        """
        __mul__ implements the binary multiplication operator
        """
        other_data = self._setup_numeric(other)
        new_line = self.empty_like(self)
        if (isinstance(other, line)):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data * other_data

        return new_line


    def __rmul__(self, other):
        """
        __rmul__ implements the reflected binary multiplication operator
        """

        return self.__mul__(other)


    def __imul__(self, other):
        """
        __imul__ implements the in-place binary multiplication operator
        """
        other_data = self._setup_numeric(other)
        self.data[:] = self.data * other_data

        return self


    def __truediv__(self, other):
        """
        __truediv__ implements the binary fp division operator
        """
        other_data = self._setup_numeric(other)
        new_line = self.empty_like(self)
        if (isinstance(other, line)):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data / other_data

        return new_line


    def __rtruediv__(self, other):
        """
        __rtruediv__ implements the reflected binary fp division operator
        """

        return self.__truediv__(other)


    def __itruediv__(self, other):
        """
        __itruediv__ implements the in-place binary fp division operator
        """
        other_data = self._setup_numeric(other)
        self.data[:] = self.data / other_data

        return self


    def __pow__(self, other):
        """
        __pow__ implements the binary power operator
        """
        other_data = self._setup_numeric(other)
        new_line = self.empty_like(self)
        if (isinstance(other, line)):
            other_data = other.data
        else:
            other_data = other

        new_line.data[:] = self.data ** other_data

        return new_line


    def __rpow__(self, other):
        """
        __rpow__ implements the reflected binary power operator
        """

        return self.__pow__(other)


    def __ipow__(self, other):
        """
        __ipow__ implements the in-place binary power operator
        """
        other_data = self._setup_numeric(other)
        self.data[:] = self.data ** other_data

        return self


    def __str__(self):
        '''
        reimplemented string method that provides some basic info about the mask object
        '''

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  and some other basic info
        msg = msg + "                 line name: " + self.name + "\n"
        msg = msg + "                      type: " + self.type + "\n"
        msg = msg + "                     color: " + str(self.color) + "\n"
        msg = msg + "                Start Time: " + str(self.ping_time[0]) + "\n"
        msg = msg + "                  End Time: " + str(self.ping_time[-1]) + "\n"


        return msg
