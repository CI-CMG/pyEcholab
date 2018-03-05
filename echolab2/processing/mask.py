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

    def __init__(self, size=None, like=None, value=False, type='sample', color=[148,0,211],
            name='Mask', sample_offset=0):

        super(mask, self).__init__()

        #  ensure the value arg is a bool
        if (value):
            value = True
        else:
            value = False

        #  set the initial attribute values
        self.type = type
        self.color = color
        self.name = name
        self.n_pings = 0
        self.n_samples = 0
        self.sample_offset = sample_offset

        #  if we've been provided with an object or size to base our mask on, create it
        if (like):
            self.like(like, value, type=type)
        elif (size):
            self.create(size, value, type=type, sample_offset=self.sample_offset)


    def create(self, size, value, type='sample', sample_offset=0):
        '''
        create creates a new mask array and axes given a mask size, type, and
        initial value. Size must be a list/tuple defining the mask dimensions
        as [n_pings, n_samples]. For ping masks it must at least contain 1
        elements and for sample masks it must contain 2. Because this mask
        is not based on an existing object, the axes will be empty.

        99% of the time you will call "like" to create a mask size to an
        existing processed_data object but this method can be used to create
        masks of any size
        '''

        if (type.lower() == 'sample'):
            self.mask = np.full(size, value, dtype=bool)
            self.n_samples = size[1]
            self.range = np.full(size[1], np.nan)
        elif (type.lower() == 'ping'):
            self.mask = np.full(size, value, dtype=bool)
        else:
            raise TypeError('Unknown mask type: ' + type)

        self.n_pings = size[0]
        self.ping_time = np.full(size[0], np.datetime64('NaT'), dtype='datetime64[ms]')
        self.sample_offset = sample_offset


    def like(self, like_obj, value, type='sample'):
        '''
        like creates a mask with shape and axes properties that match an existing
        processed_data object.
        '''

        #  masks must be based on processed_data objects
        if (not isinstance(like_obj, processed_data.processed_data)):
            raise TypeError('"like_obj" argument must be an instance of echolab2 procesed_data class' )

        #  ensure the value arg is a bool
        if (value):
            value = True
        else:
            value = False

        #  copy attributes common to both mask types
        self.n_pings = like_obj.n_pings
        self.ping_time = like_obj.ping_time.copy()
        self.sample_offset = like_obj.sample_offset

        #  create the type specific attributes
        if (type.lower() == 'sample'):
            #  set the type
            self.type = 'sample'

            #  create a 2d mask array
            self.mask = np.full((like_obj.n_pings,like_obj.n_samples), value, dtype=bool)
            self.n_samples = like_obj.n_samples

            #  get the range or depth vector
            if (hasattr(like_obj, 'range')):
                self.range = like_obj.range.copy()
            else:
                self.depth = like_obj.depth.copy()
        elif (type.lower() == 'ping'):
            #  set the type
            self.type = 'ping'

            #  create a 1D mask n_pings long
            self.mask = np.full((like_obj.n_pings), value, dtype=bool)

        else:
            raise TypeError('Unknown mask type: ' + type)



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

        if (not self.type == other.type):
            raise ValueError('Cannot operate on masks that are different types.')

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
