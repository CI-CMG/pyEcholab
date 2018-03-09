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
        self.ping_time = np.full(size[0], np.datetime64('NaT'),
                dtype='datetime64[ms]')
        self.sample_offset = sample_offset


    def like(self, like_obj, value=False, type='sample'):
        '''
        like creates a mask with shape and axes properties that match an existing
        processed_data object.
        '''

        #  ensure the value arg is a bool
        if (value):
            value = True
        else:
            value = False

        #  copy attributes common to both mask types
        self.n_pings = like_obj.n_pings
        self.ping_time = like_obj.ping_time.copy()
        self.sample_offset = like_obj.sample_offset

        #  masks must be based on processed_data objects or other masks
        if (isinstance(like_obj, processed_data.processed_data)):
            #  base this mask off of a processed_data object

            #  create the type specific attributes
            if (type.lower() == 'sample'):
                #  set the type
                self.type = 'sample'

                #  create a 2d mask array
                self.mask = np.full((like_obj.n_pings,like_obj.n_samples),
                        value, dtype=bool)
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

        elif (isinstance(like_obj, mask)):
            #  base this mask off of another mask - copy the rest of the attributes
            self.type = like_obj.type
            self.n_samples = like_obj.n_samples
            if (hasattr(like_obj, 'range')):
                self.range = like_obj.range.copy()
            else:
                self.depth = like_obj.depth.copy()

            #  and set the mask data
            self.mask = np.full(like_obj.shape, value, dtype=bool)

        else:
            #  we only can base masks on processed_data or mask objects
            raise TypeError('"like_obj" argument must be an instance of echolab2 ' +
                    'procesed_data or mask classes' )


    def copy(self):
        '''
        copy returns a deep copy of this mask.
        '''
        #  create a new empty mask
        mask_copy = mask.mask(type=self.type, color=self.color, name=self.name,
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


    def apply_line(self, line_obj, above=True, below=False):
        """
        apply_line (working name) sets mask elements above the line object to
        the value specified by the above keyword and mask elements below the
        line to the value specified by the below keyword.

        This is a place holder. A method similar to this should be implemented.
        """
        pass


    def apply_polygon(self, poly_obj, inside=True, outside=False):
        """
        apply_polygon (working name) sets mask elements inside the polygon object to
        the value specified by the inside keyword and mask elements outside the
        polygon to the value specified by the outside keyword.

        This is a place holder. A method similar to this should be implemented.
        """
        pass


    def __eq__(self, other):

        try:
            #  check that the two masks are the same shape and share common axes
            other_mask, ret_mask = self._check_mask(other)

            return np.all(ret_mask.mask == other.mask)
        except:
            return False


    def __ne__(self, other):

        try:
            #  check that the two masks are the same shape and share common axes
            other_mask, ret_mask = self._check_mask(other)

            return np.any(ret_mask.mask != other.mask)
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


    def __and__(self, other):
        """
        __and__ implements the logical AND operator (&)
        """
        #  check that the two masks are the same shape and share common axes
        other_mask, ret_mask = self._check_mask(other)

        #  set the mask
        ret_mask.mask[:] = self.mask & other_mask.mask

        #  and return the result
        return ret_mask


    def __rand__(self, other):
        """
        __rand__ implements the reflected logical AND operator (&)
        """

        return self.__and__(other)


    def __iand__(self, other):
        """
        __iand__ implements the in-place logical AND operator (&)
        """
        #  check that the two masks are the same shape and share common axes
        other_mask, ret_mask = self._check_mask(other, inplace=True)

        #  set the mask
        ret_mask.mask[:] = self.mask & other_mask.mask

        #  and return the result
        return ret_mask


    def __or__(self, other):
        """
        __or__ implements the logical OR operator (|)
        """
        #  check that the two masks are the same shape and share common axes
        other_mask, ret_mask = self._check_mask(other)

        #  set the mask
        ret_mask.mask[:] = self.mask | other_mask.mask

        #  and return the result
        return ret_mask


    def __ror__(self, other):
        """
        __rand__ implements the reflected logical OR operator (|)
        """

        return self.__or__(other)


    def __ior__(self, other):
        """
        __iand__ implements the in-place logical OR operator (|)
        """
        #  check that the two masks are the same shape and share common axes
        other_mask, ret_mask = self._check_mask(other, inplace=True)

        #  set the mask
        ret_mask.mask[:] = self.mask | other_mask.mask

        #  and return the result
        return ret_mask


    def __xor__(self, other):
        """
        __rand__ implements the logical exclusive or XOR operator (^)
        """
        #  check that the two masks are the same shape and share common axes
        other_mask, ret_mask = self._check_mask(other)

        #  set the mask
        ret_mask.mask[:] = self.mask ^ other_mask.mask

        #  and return the result
        return ret_mask


    def __rxor__(self, other):
        """
        __rand__ implements the reflected logical exclusive or XOR operator (^)
        """

        return self.__xor__(other)


    def __ixor__(self, other):
        """
        __iand__ implements the in-place logical exclusive or XOR operator (^)
        """
        #  check that the two masks are the same shape and share common axes
        other_mask, ret_mask = self._check_mask(other, inplace=True)

        #  set the mask
        ret_mask.mask[:] = self.mask ^ other_mask.mask

        #  and return the result
        return ret_mask


    def __invert__(self):
        """
        __invert__ implements the unary arithmetic operatior ~ which when applied
        to logical arrays will invert the values. There is no in-place version of
        this operator in Python.
        """

        #  create the mask to return
        ret_mask = self.copy()

        #  set the return mask elements to the inverted state of this mask
        ret_mask.mask[:] = ~self.mask

        return ret_mask


    def to_sample_mask(self, like_obj):
        """
        to_sample_mask returns a new 2d sample based mask created when called
        by a ping based mask and provided with another sample mask or
        processed_data object to obtain the sample count from.
        """
        pass


    def _check_mask(self, other, inplace=False):
        '''
        _check_mask ensures that the dimensions and axes values match. If possible,
        it will coerce a ping mask to a sample mask by vertically expanding the
        ping mask.
        '''
        #  make sure we share the same ping_time axis
        if (not np.array_equal(self.ping_time, other.ping_time)):
            raise ValueError('Mask ping times do not match.')

        #  make sure the vertical axes are the same (if present)
        if (hasattr(self, 'range')):
            if (hasattr(other, 'range')):
                if (not np.array_equal(self.range, other.range)):
                    raise ValueError('Mask ranges do not match.')
            else:
                raise AttributeError('You cannot apply a range based mask ' +
                        'to a depth based mask.')
        else:
            if (hasattr(other, 'depth')):
                if (not np.array_equal(self.depth, other.depth)):
                    raise ValueError('Mask depths do not match.')
            else:
                raise AttributeError('You cannot apply a depth based mask ' +
                        'to a range based mask.')

        #  check if we need to do any coercion - we can convert ping masks to sample
        #  masks in most cases. The only time we cannot is when someone is trying
        #  to do an in-place operation applying a sample mask to a ping mask because
        #  this requires that a new mask array be created which violates in-place
        ret_mask = None
        if (self.type == 'ping' and other.type == 'sample'):
            if (inplace):
                raise AttributeError('You cannot apply a sample based mask ' +
                        'to a ping based mask in-place')
            else:
                #  create a new 2d mask based on the "other" sample mask
                ret_mask = mask(like=other)

                #  set all samples to true for each ping set true in the this mask
                ret_mask[self.mask,:] = True
        elif (self.type == 'sample' and other.type == 'ping'):
            #  coerce the other mask to a sample mask
            other_mask = mask(like=self)

            #  set all samples to true for each ping set true in the other mask
            other_mask[other.mask,:] = True

        if (ret_mask is None):
            #  we didn't have to coerce the return mask so set the return mask now
            if (inplace):
                #  if we're operating in-place - return self
                ret_mask = self
            else:
                #  we're returning a new mask - create it
                ret_mask = mask(like=self)

        return (other_mask, ret_mask)


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
