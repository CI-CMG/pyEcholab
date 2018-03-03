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

'''


'''
import numpy as np
import processed_data

class mask(object):
    '''

    '''

    def __init__(self, like=None, value=None):

        super(mask, self).__init__()


        #  sample offset is the number of samples the first row of data are offset away from
        #  the transducer face.
        self.sample_offset = 0

        self.color = [20, 20, 200]
        self.name = 'Mask'

        #  if we've been provided with an object to base our properties on, call the like method
        if (like):
            self.like(like, value)


    def like(self, like_obj, value):

        #  masks must be based on processed_data objects
        if (not isinstance(like_obj, processed_data)):
            raise TypeError('"like_obj" argument must be an instance of echolab2 procesed_data class' )

        #  ensure value is a bool
        if (value):
            value = True
        else:
            value = False

        #  create the mask array
        self.mask = np.full((like_obj.n_pings,like_obj.n_samples), value, dtype=bool)

        self.n_pings = like_obj.n_pings
        self.n_samples = like_obj.n_samples

        #  copy the axes
        self.ping_time = like_obj.ping_time.copy()

        #  get our range/depth vector
        if (hasattr(like_obj, 'range')):
            self.range = like_obj.range.copy()
        else:
            self.depth = like_obj.depth.copy()


    def __eq__(self, other):

        try:
            #  check that the two masks are the same shape and share common axes
            self._check_mask(other)

            return np.all(self.mask == other.mask)
        except:
            return False


    def __ne__(self, other):

        try:
            #  check that the two masks are the same shape and share common axes
            self._check_mask(other)

            return np.any(self.mask != other.mask)
        except:
            return False


    def any(self):

        try:
            return np.any(self.mask)
        except:
            return False


    def all(self):

        try:
            return np.all(self.mask)
        except:
            return False


    def logical_and(self, other, in_place=True):
        pass


    def _check_mask(self, other, ignore_axes=False):
        '''
        _check_mask ensures that the dimensions and axes values match
        '''

        if (not np.array_equal(self.ping_times, other.ping_times)):
            raise ValueError('Mask ping times do not match.')

        #  make sure the vertical axis is the same
        if (hasattr(self, 'range')):
            if (hasattr(other, 'range')):
                if (not np.array_equal(self.range, other.range)):
                    raise ValueError('Mask ranges do not match.')
                else:
                    raise AttributeError('You cannot compare a range based mask with a depth based mask.')
        else:
            if (hasattr(other, 'depth')):
                if (not np.array_equal(self.depth, other.depth)):
                    raise ValueError('Mask depths do not match.')
                else:
                    raise AttributeError('You cannot compare a depth based mask with a range based mask.')


    def __str__(self):
        '''
        reimplemented string method that provides some basic info about the processed_data object
        '''

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the processed_data instance
        n_pings = len(self.ping_time)
        if (n_pings > 0):
            msg = msg + "                channel(s): ["
            for channel in self.channel_id:
                msg = msg + channel + ", "
            msg = msg[0:-2] + "]\n"
            msg = msg + "                 frequency: " + str(self.frequency)+ "\n"
            msg = msg + "           data start time: " + str(self.ping_time[0])+ "\n"
            msg = msg + "             data end time: " + str(self.ping_time[n_pings-1])+ "\n"
            msg = msg + "           number of pings: " + str(n_pings)+ "\n"
            msg = msg + "          data attributes:"
            n_attr = 0
            padding = " "
            for attr_name in self._data_attributes:
                attr = getattr(self, attr_name)
                if (n_attr > 0):
                    padding = "                           "
                if (isinstance(attr, np.ndarray)):
                    if (attr.ndim == 1):
                        msg = msg + padding + attr_name + " (%u)\n" % (attr.shape[0])
                    else:
                        msg = msg + padding + attr_name + " (%u,%u)\n" % (attr.shape[0], attr.shape[1])
                elif (isinstance(attr, list)):
                        msg = msg + padding + attr_name + " (%u)\n" % (len(attr))
                n_attr += 1
        else:
            msg = msg + ("  processed_data object contains no data\n")

        return msg
