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
            self.n_samples = 0
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

            #  ping masks don't have a sample dimension
            self.n_samples = 0

            #  create a 1D mask n_pings long
            self.mask = np.full((like_obj.n_pings), value, dtype=bool)

        else:
            raise TypeError('Unknown mask type: ' + type)


    def copy(self):
        '''
        copy returns a deep copy of this mask.
        '''

        #  modify the name to indicate it is a copy
        copy_name = self.name + '-copy'

        #  create a new empty mask
        mask_copy = mask.mask(type=self.type, color=self.color, name=copy_name,
            sample_offset=self.sample_offset)

        #  copy common attributes
        mask_copy.n_pings = self.n_pings
        mask_copy.n_samples = self.n_samples
        mask_copy.mask = self.mask.copy()
        mask_copy.ping_time = self.ping_time.copy()

        #  copy the vertical axis for sample masks
        if (self.type.lower() == 'sample'):
            if (hasattr(self, 'range')):
                mask_copy.range = self.range.copy()
            else:
                mask_copy.depth = self.depth.copy()


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
        '''
        any returns True if any elements of the mask are True
        '''

        try:
            return np.any(self.mask)
        except:
            return False


    def all(self):
        '''
        all returns True if all elements of the mask are True
        '''

        try:
            return np.all(self.mask)
        except:
            return False


    def logical_and(self, other, in_place=True, where=True):
        '''
        logical_and performs an element by element ANDing of our mask and the
        mask provided in the "other" argument.

        If in_place is True, "this" mask's data is modified. If in_place
        is False, a copy of "this" mask is returned containing the results
        of the AND.

        Where is the same as the numpy.logical_* keyword.
        '''

        #  check that the two masks are the same shape and share common axes
        self._check_mask(other)

        #  check if we are operating on our data or a copy
        if (in_place):
            #  operating on our data
            np.logical_and(self.mask, other.mask, out=self.mask, where=where)
            #  return a reference to ourself
            return self
        else:
            #  returning a copy - create a copy to return
            mask_copy = self.copy()
            #  and it
            np.logical_and(self.mask, other.mask, out=mask_copy.mask, where=where)
            #  and return the copy
            return mask_copy


    def logical_or(self, other, in_place=True, where=True):
        '''
        logical_or performs an element by element ORing of our mask and the
        mask provided in the "other" argument.

        If in_place is True, "this" mask's data is modified. If in_place
        is False, a copy of "this" mask is returned containing the results
        of the OR.

        Where is the same as the numpy.logical_* keyword.
        '''

        #  check that the two masks are the same shape and share common axes
        self._check_mask(other)

        #  check if we are operating on our data or a copy
        if (in_place):
            #  operating on our data
            np.logical_or(self.mask, other.mask, out=self.mask, where=where)
            #  return a reference to ourself
            return self
        else:
            #  returning a copy - create a copy to return
            mask_copy = self.copy()
            #  and it
            np.logical_or(self.mask, other.mask, out=mask_copy.mask, where=where)
            #  and return the copy
            return mask_copy


    def logical_not(self, other, in_place=True, where=True):
        '''
        logical_not performs an element by element NOTing of our mask and the
        mask provided in the "other" argument.

        If in_place is True, "this" mask's data is modified. If in_place
        is False, a copy of "this" mask is returned containing the results
        of the NOT.

        Where is the same as the numpy.logical_* keyword.
        '''

        #  check that the two masks are the same shape and share common axes
        self._check_mask(other)

        #  check if we are operating on our data or a copy
        if (in_place):
            #  operating on our data
            np.logical_not(self.mask, other.mask, out=self.mask, where=where)
            #  return a reference to ourself
            return self
        else:
            #  returning a copy - create a copy to return
            mask_copy = self.copy()
            #  and it
            np.logical_not(self.mask, other.mask, out=mask_copy.mask, where=where)
            #  and return the copy
            return mask_copy


    def logical_xor(self, other, in_place=True, where=True):
        '''
        logical_xor performs an element by element XORing of our mask and the
        mask provided in the "other" argument.

        If in_place is True, "this" mask's data is modified. If in_place
        is False, a copy of "this" mask is returned containing the results
        of the XOR.

        Where is the same as the numpy.logical_* keyword.
        '''

        #  check that the two masks are the same shape and share common axes
        self._check_mask(other)

        #  check if we are operating on our data or a copy
        if (in_place):
            #  operating on our data
            np.logical_xor(self.mask, other.mask, out=self.mask, where=where)
            #  return a reference to ourself
            return self
        else:
            #  returning a copy - create a copy to return
            mask_copy = self.copy()
            #  and it
            np.logical_xor(self.mask, other.mask, out=mask_copy.mask, where=where)
            #  and return the copy
            return mask_copy


    def _check_mask(self, other):
        '''
        _check_mask ensures that the dimensions and axes values match
        '''

        if (not self.type == other.type):
            raise ValueError('Cannot operate on masks that are different types.')

        if (not np.array_equal(self.ping_time, other.ping_time)):
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
        reimplemented string method that provides some basic info about the mask object
        '''

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  and some other basic info
        msg = msg + "                 mask name: " + self.name + "\n"
        msg = msg + "                      type: " + self.type + "\n"
        msg = msg + "                     color: " + str(self.color) + "\n"
        if (self.type.lower() == 'ping'):
            msg = msg + "                dimensions: (" + str(self.n_pings) + ")\n"
        else:
            msg = msg + "                dimensions: (" + str(self.n_pings) + "," + \
                    str(self.n_samples) + ")\n"
            msg = msg + "             sample offset: " + str(self.sample_offset) + "\n"

        return msg
