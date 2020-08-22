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


class annotation_data(object):
    '''
    The annotation_data class stores data from TAG0 datagrams in Simrad raw files.
    It may be useful if other sonar file types have a similar annotation
    '''

    CHUNK_SIZE = 50

    def __init__(self):

        # Create a counter to keep track of the number of datagrams.
        self.n_datagrams = 0

        # Create arrays to store MRU0 data
        self.times = np.empty(annotation_data.CHUNK_SIZE, dtype='datetime64[ms]')
        self.text = np.empty(annotation_data.CHUNK_SIZE, dtype=object)


    def add_datagram(self, time, text):
        """
        Add annotation text

        Args:
            annotation_datagram (dict) - The motion datagram dictionary returned by
                    the simrad datagram parser.

        """

        # Check if we need to resize our arrays.
        if self.n_datagrams == self.times.shape[0]:
            self._resize_arrays(self.times.shape[0] + annotation_data.CHUNK_SIZE)

        # Add this datagram to our data arrays
        self.times[self.n_datagrams] = time
        self.text[self.n_datagrams] = text

        # Increment datagram counter.
        self.n_datagrams += 1


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
            start_time = np.min(self.times)
        if end_time is None:
            end_time = np.max(self.times)

        # Sort time index if returning time ordered indexes.
        if time_order:
            primary_index = self.times.argsort()
        else:
            primary_index = self.times

        # Determine the indices of the data that fall within the time span
        # provided.
        mask = self.times[primary_index] >= start_time
        mask = np.logical_and(mask, self.times[primary_index] <= end_time)

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

        self.times = np.resize(self.times,(new_size))
        self.text = np.resize(self.text,(new_size))


    def trim(self):
        """
        Trim arrays to proper size after all data are added.

        trim is called when one is done adding data to the object. It
        removes empty elements of the data arrays.
        """

        self._resize_arrays(self.n_datagrams)


    def __str__(self):
        """
        Reimplemented string method that provides some basic info about the
        nmea_data object.

        """

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the motion_data instance
        if (self.n_datagrams > 0):
            msg = "{0}       Annotation data start time: {1}\n".format(msg, self.times[0])
            msg = "{0}         Annotation data end time: {1}\n".format(msg,self.times[self.n_datagrams-1])
            msg = "{0}            Number of annotations: {1}\n".format(msg,self.n_datagrams+1)
        else:
            msg = msg + ("  annotation_data object contains no data\n")

        return msg
