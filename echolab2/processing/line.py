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


def empty_like(obj, name=None, color=None, linestyle=None, thickness=None):
    """Creates an empty line object.

    empty_like creates an empty line (where data values are NaN) that
    is the same length as the provided line or processed data object.
    If a line object is passed, the name and color attributes are copied if not
    explicitly provided. If a processed data object is passed the returned
    line will have the default line attributes if not explicitly provided.

    Args:
        obj (line or ProcessedData object): The line or ProcessedData object
        instance that is the template for the new object being created.
        name (str): Optional name for the new line object.
        color (): Optional color for the new line object.
        linestyle(str): Optional linestyle is a string that defines the style of the line.
        thickness(float): Optional thickness is a float the defines the width of the line.

    Returns:
        New empty instance of line object with name and color ether
        copied from line object passed in or using optional parameters
        passed to method.
    """
    # Create a new line object to return.
    new_line = line(ping_time=obj.ping_time.copy())

    # Check if new properties were provided, otherwise copy from original.
    if color:
        new_line.color = color
    else:
        if isinstance(obj, line):
            new_line.color = obj.color
    if name:
        new_line.name = name
    else:
        if isinstance(obj, line):
            new_line.name = obj.name
    if linestyle:
        new_line.linestyle = linestyle
    else:
        if isinstance(obj, line):
            new_line.linestyle = obj.linestyle
    if thickness:
        new_line.thickness = thickness
    else:
        if isinstance(obj, line):
            new_line.thickness = obj.thickness

    # Set the data array to NaNs.
    new_line.data = np.full(new_line.ping_time.shape[0], np.nan)

    return new_line


class line(ping_data):
    #   TODO: Review attributes in this docstring
    """The line class implements lines based on ping_time and depth/range values.
    The class provides methods manipulating these values in various ways. The
    numerical operators operate on the data, allowing offset lines to easily
    be created. Color and name properties can be used in plotting the lines.

    Attributes:
        ping_time: ping_time is a datetime object that defines the time the
            ping was recorded.
        data: data is a numpy array which contains the float data.
        color: color is a list which defines the color of the line.
        name (string): name or label for the line is a string.
        linestyle: linestyle is a string that defines the style of the line.
        thickness: thickness is a float the defines the width of the line.
    """

    def __init__(self, ping_time=None, data=None, color=[0.58, 0.0, 0.83],
                 name='line', linestyle='solid', thickness=1.0, **_):
        """Initializes line class object.

        Creates and sets several internal properties.
        """
        super(line, self).__init__()

        # Set the ping time.
        self.ping_time = ping_time

        # Set the number of pings.
        if ping_time is not None:
            self.n_pings = ping_time.shape[0]

        # Assign data based on what we're given. Arrays must be the same shape
        # as ping_time, scalars are expanded to the same shape as ping_time
        # and None is None.
        if isinstance(data, np.ndarray):
            if data.ndim == 0:
                data = np.full(ping_time.shape[0], data, dtype='float32')
            else:
                if data.shape[0] != ping_time.shape[0]:
                    raise ValueError("The data array must be None, a scalar "
                                     "or an array the same size as ping_time.")
        elif data is not None:
            try:
                data = float(data)
                data = np.full(ping_time.shape[0], data, dtype='float32')
            except Exception:
                raise ValueError("The data array must be None, a scalar or an"
                                 " array the same size as ping_time.")
        self.data = data

        # Set the initial attribute values.
        self.color = color
        self.name = name
        self.linestyle = linestyle
        self.thickness = thickness

        # Update out data_attributes list, adding the "data" attribute.
        self._data_attributes += ['data']


    def interpolate(self, new_times):
        """Interpolates the data values to the provided time vector.

        Interpolate interpolates the data values to the provided time vector.

        Args:
            new_times (array): 1D numpy array of new dateTime64 times
        """

        self.data[:] = np.interp(self.ping_time, new_times,
                    self.data, left=np.nan, right=np.nan)
        self.ping_time = new_times.copy()


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
        msg = "{0}                 line name: ({1})\n".format(msg, self.name)
        msg = "{0}                 ping_time: ({1})\n".format(
                                                    msg,
                                                    self.ping_time.shape[0])
        msg = "{0}                      data: ({1})\n".format(
                                                            msg,
                                                            self.data.shape[0])
        msg = "{0}                start time: {1}\n".format(msg,
                                                            self.ping_time[0])
        msg = "{0}                  end time: {1}\n" .format(msg,
                                                             self.ping_time[-1])

        return msg
