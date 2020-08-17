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


class simrad_motion_data(object):
    '''
    The simrad_motion_data class stores data from Simrad's MRU datagram and
    provides a method to interpolate the data to your ping times.
    '''

    CHUNK_SIZE = 500

    def __init__(self):

        # Create a counter to keep track of the number of datagrams.
        self.n_raw = 0

        # Create arrays to store MRU0 data
        self.time = np.empty(simrad_motion_data.CHUNK_SIZE, dtype='datetime64[ms]')
        self.heave = np.empty(simrad_motion_data.CHUNK_SIZE, dtype='f')
        self.pitch = np.empty(simrad_motion_data.CHUNK_SIZE, dtype='f')
        self.roll = np.empty(simrad_motion_data.CHUNK_SIZE, dtype='f')
        self.heading = np.empty(simrad_motion_data.CHUNK_SIZE, dtype='f')


    def add_datagram(self, motion_datagram):
        """
        Add MRU0 datagram data.

        Args:
            motion_datagram (dict) - The motion datagram dictionary returned by
                    the simrad datagram parser.

        """

        # Check if this datagram has the same time as the previous - This
        # simply filters replicate data when used with the EK60 class.
        if self.time[self.n_raw - 1] ==  motion_datagram['timestamp']:
            # We already have this motion datagram stored.
            return

        # Check if we need to resize our arrays.
        if self.n_raw == self.time.shape[0]:
            self._resize_arrays(self.time.shape[0] + simrad_motion_data.CHUNK_SIZE)

        # Add this datagram to our data arrays
        self.time[self.n_raw] = motion_datagram['timestamp']
        self.heave[self.n_raw] = motion_datagram['heave']
        self.pitch[self.n_raw] = motion_datagram['pitch']
        self.roll[self.n_raw] = motion_datagram['roll']
        self.heading[self.n_raw] = motion_datagram['heading']

        # Increment datagram counter.
        self.n_raw += 1


    def interpolate(self, p_data, data_type, start_time=None, end_time=None):
        """
        interpolate returns the requested motion data interpolated to the ping times
        that are present in the provided ping_data object.

            p_data is a ping_data object that contains the ping_time vector
                    to interpolate to.
            data_type is a string pecifying the motion attribute to interpolate, valid
                    values are: 'pitch', 'heave', 'roll', and 'heading'
            start_time is a datetime or datetime64 object defining the starting time of the data
                    to return. If None, the start time is the earliest time.
            end_time is a datetime or datetime64 object defining the ending time of the data
                    to return. If None, the end time is the latest time.
            attributes is a string or list of strings specifying the motion attribute(s)
                    to interpolate and return. If None, all attributes are interpolated
                    and returned.

        Returns a dictionary of numpy arrays keyed by attribute name that contain the
        interpolated data for that attribute.
        """
        # Create the dictionary to return
        out_data = {}

        # Return an empty dict if we don't contain any data
        if self.n_raw < 1:
            return out_data

        # Get the index for all datagrams within the time span.
        return_idxs = self.get_indices(start_time=start_time, end_time=end_time)

        # Check if we're been given specific attributes to interpolate
        if data_type is None:
            # No - interpolate all
            attributes = ['heave', 'pitch', 'roll', 'heading']
        elif isinstance(data_type, str):
            # We have a string, put it in a list
            attributes = [data_type]

        # Work through the attributes and interpolate
        for attribute in attributes:
            try:
                # Interpolate this attribute using the time vector in the
                # provided ping_data object
                i_data = np.interp(p_data.ping_time.astype('d'),
                        self.time.astype('d'), getattr(self, attribute),
                        left=np.nan, right=np.nan)
                out_data[attribute] = i_data[return_idxs]
            except:
                # Provided attribute doesn't exist
                out_data[attribute] = None

        return (attributes, out_data)


    def get_indices(self, start_time=None, end_time=None, time_order=True):
        """
        Return index of data contained in speciofied time range.

        get_indices returns an index array containing the indices contained
        in the range defined by the times provided. By default the indexes
        are in time order.

        Args:
            start_time is a datetime or datetime64 object defining the starting
                time of the data to return. If None, the start time is the
                earliest time.
            end_time is a datetime or datetime64 object defining the ending time
                of the data to return. If None, the end time is the latest time.
            time_order (bool): Control whether if indexes are returned in time
                order (True) or not.

        Returns: Index array containing indices of data to return.

        """
        #  Ensure that we have times to work with.
        if start_time is None:
            start_time = np.min(self.time)
        if end_time is None:
            end_time = np.max(self.time)

        # Sort time index if returning time ordered indexes.
        if time_order:
            primary_index = self.time.argsort()
        else:
            primary_index = self.time

        # Determine the indices of the data that fall within the time span
        # provided.
        mask = self.time[primary_index] >= start_time
        mask = np.logical_and(mask, self.time[primary_index] <= end_time)

        #  and return the indices that are included in the specified range
        return primary_index[mask]


    def _resize_arrays(self, new_size):
        """
        Resize arrays if needed to hold more data.

        _resize_arrays expands our data arrays and is called when said arrays
        are filled with data and more data need to be added.

        Args:
            new_size (int): New size for arrays, Since these are all 1d
            arrays the value is simply an integer.

        """

        self.time = np.resize(self.time,(new_size))
        self.pitch = np.resize(self.pitch,(new_size))
        self.roll = np.resize(self.roll,(new_size))
        self.heading = np.resize(self.heading,(new_size))
        self.heave = np.resize(self.heave,(new_size))


    def trim(self):
        """
        Trim arrays to proper size after all data are added.

        trim is called when one is done adding data to the object. It
        removes empty elements of the data arrays.
        """

        self._resize_arrays(self.n_raw)


    def __str__(self):
        """
        Reimplemented string method that provides some basic info about the
        nmea_data object.

        """

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the motion_data instance
        if (self.n_raw > 0):
            msg = "{0}       MRU data start time: {1}\n".format(msg, self.time[0])
            msg = "{0}         MRU data end time: {1}\n".format(msg,self.time[self.n_raw-1])
            msg = "{0}       Number of datagrams: {1}\n".format(msg,self.n_raw+1)
        else:
            msg = msg + ("  simrad_motion_data object contains no data\n")

        return msg
