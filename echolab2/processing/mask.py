# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

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
import matplotlib
from ..ping_data import PingData


class Mask(PingData):
    # TODO:   add description of class and attributes to the docstring.
    """
    DESCRIPTION OF CLASS AND ATTRIBUTES

    Attributes:
        size:
        like:
        value (bool):
        type (str):
        color (array):
        name (str):
        sample_offset:
    """

    def __init__(self, size=None, like=None, value=False, type='sample',
                 color=[148, 0, 211], name='Mask', sample_offset=0):
        """Initializes Mask class object.

        Creates and sets several internal properties.
        """
        super(Mask, self).__init__()

        # Ensure the value arg is a bool.
        value = bool(value)

        # Set the initial attribute values.
        self.type = type
        self.color = color
        self.name = name
        self.sample_offset = sample_offset

        # Update out data_attributes list adding the "mask" attribute.
        self._data_attributes += ['mask']

        # If we've been provided with an object or size to base our mask on,
        # create it.
        if like:
            self.like(like, value, mask_type=type)
        elif size:
            self.create(size, value, mask_type=type,
                        sample_offset=self.sample_offset)


    def create(self, size, value, mask_type='sample', sample_offset=0):
        """Creates a new mask array and axes.

        This method creates a new mask array and axes given a mask size,
        type, and initial value.  Size must be a list/tuple defining the mask
        dimensions as [n_pings, n_samples]. For ping masks, it must at least
        contain 1 elements and for sample masks it must contain 2. Because
        this mask is not based on an existing object, the axes will be empty.

        99% of the time you will call "like" to create a mask size to an
        existing ProcessedData object but this method can be used to create
        masks of any size.

        Args:
            size (list): A list defining the mask dimensions as [n_pings,
                n_samples]
            value:
            mask_type (str):
            sample_offset (int):
        """

        if mask_type.lower() == 'sample':
            self.mask = np.full(size, value, dtype=bool)
            self.n_samples = size[1]
            self.range = np.full(size[1], np.nan)
        elif mask_type.lower() == 'ping':
            self.mask = np.full(size, value, dtype=bool)
            self.n_samples = 0
        else:
            raise TypeError('Unknown mask type: ' + mask_type)

        self.n_pings = size[0]
        self.ping_time = np.full(size[0], np.datetime64('NaT'),
                dtype='datetime64[ms]')
        self.sample_offset = sample_offset


    def like(self, like_obj, value=False, mask_type='sample'):
        """Creates a mask that matches a provided data object.

        This method creates a mask with shape and axes properties that match an
        existing ProcessedData object.

        Args:
            like_obj (ProcessedData obj): The object to base the mask off of.
            value (bool): Set to True to fill array with values.
            mask_type (str): The mask type.

        Raise:
            TypeError: Invalid mask type.
            TypeError: The object argument is not an instance of echolab2
                ProcesedData or Mask classes.
        """

        # Ensure the value arg is a bool.
        value = bool(value)

        # Copy attributes common to both mask types.
        self.n_pings = like_obj.n_pings
        self.ping_time = like_obj.ping_time.copy()
        self.sample_offset = like_obj.sample_offset

        # Masks must be based on ProcessedData objects or other masks.  Use
        # type().__name__ to determine if class of "like_obj" is a
        # ProcessedData object to avoid circular import references
        # (ProcessedData imports mask so mask cannot import ProcessedData)
        if type(like_obj).__name__ == 'ProcessedData':
            # Base this mask off of a ProcessedData object.

            # Create the type specific attributes.
            if mask_type.lower() == 'sample':
                # Set the type.
                self.type = 'sample'

                # Create a 2d mask array.
                self.mask = np.full((like_obj.n_pings, like_obj.n_samples),
                                    value, dtype=bool)
                self.n_samples = like_obj.n_samples

                # Get the range or depth vector
                if hasattr(like_obj, 'range'):
                    self.range = like_obj.range.copy()
                else:
                    self.depth = like_obj.depth.copy()
            elif mask_type.lower() == 'ping':
                # Set the type.
                self.type = 'ping'

                # Ping masks don't have a sample dimension.
                self.n_samples = 0

                # Create a 1D mask that is n_pings long.
                self.mask = np.full(like_obj.n_pings, value, dtype=bool)

            else:
                raise TypeError('Unknown mask type: ' + mask_type)

        elif isinstance(like_obj, Mask):
            # Base this mask off of another mask.  Copy the rest of the
            # attributes.
            self.type = like_obj.type
            self.n_samples = like_obj.n_samples
            if hasattr(like_obj, 'range'):
                self.range = like_obj.range.copy()
            else:
                self.depth = like_obj.depth.copy()

            # Set the mask data.
            self.mask = np.full(like_obj.mask.shape, value, dtype=bool)

        else:
            # We only can base masks on ProcessedData or mask objects.
            raise TypeError('"like_obj" argument must be an instance of '
                            'echolab2 ProcesedData or Mask classes.')


    def copy(self):
        """Returns a deep copy of this mask."""

        # Create a new empty mask.
        mask_copy = mask.mask(type=self.type, color=self.color, name=self.name,
            sample_offset=self.sample_offset)

        # Copy common attributes.
        mask_copy.n_pings = self.n_pings
        mask_copy.n_samples = self.n_samples
        mask_copy.mask = self.mask.copy()
        mask_copy.ping_time = self.ping_time.copy()

        # Copy the vertical axis for sample masks.
        if self.type.lower() == 'sample':
            if hasattr(self, 'range'):
                mask_copy.range = self.range.copy()
            else:
                mask_copy.depth = self.depth.copy()


    def apply_line(self, line_obj, apply_above=False, value=True):
        """Sets mask elements above and below the line object.

        This method sets mask elements above the line object to the value
        specified by the above keyword and mask elements below the
        line to the value specified by the below keyword.

        NOTE: This is a place holder. A method similar to this should be
        implemented.

        Args:
            line_obj (ProcessedData obj): The line object the mask refers to.
            apply_above (bool):
            value (bool):

        Raises:
            TypeError: The line isn't a sample mask.
            ValueError: Line ping times do not match mask times.
        """
        # Make sure this is a sample mask.
        if self.type == 'ping':
            raise TypeError('You cannot apply a line to a ping mask.  You '
                            'must convert it to a sample mask first.')

        # Make sure we share the same ping_time axis.
        if not np.array_equal(self.ping_time, line_obj.ping_time):
            raise ValueError('Line ping times do not match mask times.')

        # Ensure value is a bool.
        value = bool(value)

        if hasattr(self, 'range'):
            v_axis = self.range
        else:
            v_axis = self.depth

        if apply_above:
            for ping in range(self.n_pings):
                samps_to_mask = v_axis <= line_obj.data[ping]
                self.mask[ping, :][samps_to_mask] = value
        else:
            for ping in range(self.n_pings):
                samps_to_mask = v_axis >= line_obj.data[ping]
                self.mask[ping, :][samps_to_mask] = value


    def apply_polygon(self, poly_obj, inside=True, outside=False):
        """Sets mask elements inside and outside the polygon object.

        This method sets mask elements inside the polygon object to the value
        specified by the inside keyword and mask elements outside the polygon
        to the value specified by the outside keyword.

        NOTE: This code is based on code posted to Stack Overflow by Yusuke N.:
        https://stackoverflow.com/questions/3654289/scipy-create-2d-polygon-mask

        Args:
            poly_obj (ProcessedData obj):
            inside (bool):
            outside (bool):

        Raises:
            TypeError: Polygon isn't a sample mask.
        """

        if self.type == 'ping':
            raise TypeError('You cannot apply a polygon to a ping mask. You '
                            'must convert it to a sample mask first.')

        # Get a reference to the vertical axis.
        if hasattr(self, 'range'):
            v_axis = self.range
        else:
            v_axis = self.depth

        # Create a matplotlib path.
        path = matplotlib.path.Path(poly_obj)

        # Generate the vertices for the mask.
        x = np.resize(self.ping_time.copy(), self.n_samples)
        y = np.repeat(v_axis, self.n_pings)
        points = np.vstack((x,y)).T

        # Determine which samples fall within the polygon.
        mask = path.contains_points(points)

        # Reshape the results back into our 2d.
        self.mask = mask.reshape((self.n_pings,self.n_samples))


    def __eq__(self, other):
        """Compares two masks

        Args:
            other (Mask obj):  A given mask object to compare with.

        Returns:
            Returns True if the two masks match.
        """
        try:
            # Check that the two masks are the same shape and share common axes.
            other_mask, ret_mask = self._check_mask(other)

            return np.all(ret_mask.mask == other.mask)
        except:
            return False


    def __ne__(self, other):
        """Compares two masks.

        Args:
            other (Mask obj):  A given mask object to compare with.

        Returns:
            Returns True if the two masks don't match.
        """
        try:
            #  check that the two masks are the same shape and share common axes
            other_mask, ret_mask = self._check_mask(other)

            return np.any(ret_mask.mask != other.mask)
        except:
            return False


    def any(self):
        """Checks if any elements of the mask are True.

        Returns:
            Returns True if at least one element in the mask is True.
        """

        try:
            return np.any(self.mask)
        except:
            return False


    def all(self):
        """Checks if all elements of the mask are True.

        Returns:
            Returns True if all elements of the mask are True.
        """

        try:
            return np.all(self.mask)
        except:
            return False


    def __and__(self, other):
        """Implements the logical AND operator (&).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """
        # Check that the two masks are the same shape and share common axes.
        other_mask, ret_mask = self._check_mask(other)

        # Set the mask.
        ret_mask.mask[:] = self.mask & other_mask.mask

        # Return the result.
        return ret_mask


    def __rand__(self, other):
        """Implements the reflected logical AND operator (&).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """

        return self.__and__(other)


    def __iand__(self, other):
        """Implements the in-place logical AND operator (&=).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """
        # Check that the two masks are the same shape and share common axes.
        other_mask, ret_mask = self._check_mask(other, inplace=True)

        # Set the mask.
        ret_mask.mask[:] = self.mask & other_mask.mask

        # Return the result.
        return ret_mask


    def __or__(self, other):
        """Implements the logical OR operator (|).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """
        # Check that the two masks are the same shape and share common axes.
        other_mask, ret_mask = self._check_mask(other)

        # Set the mask.
        ret_mask.mask[:] = self.mask | other_mask.mask

        # Return the result.
        return ret_mask


    def __ror__(self, other):
        """Implements the reflected logical OR operator (|).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """

        return self.__or__(other)


    def __ior__(self, other):
        """Implements the in-place logical OR operator (|=).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """
        # Check that the two masks are the same shape and share common axes.
        other_mask, ret_mask = self._check_mask(other, inplace=True)

        # Set the mask.
        ret_mask.mask[:] = self.mask | other_mask.mask

        # Return the result.
        return ret_mask


    def __xor__(self, other):
        """Implements the logical exclusive or XOR operator (^).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """
        # Check that the two masks are the same shape and share common axes.
        other_mask, ret_mask = self._check_mask(other)

        # Set the mask.
        ret_mask.mask[:] = self.mask ^ other_mask.mask

        # Return the result.
        return ret_mask


    def __rxor__(self, other):
        """Implements the reflected logical exclusive or XOR operator (^).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """

        return self.__xor__(other)


    def __ixor__(self, other):
        """Implements the in-place logical exclusive or XOR operator (^=).

        Args:
            other (Mask obj): A given mask object to use the operator on.

        Returns:
            A mask with the result of the operation.
        """
        # Check that the two masks are the same shape and share common axes.
        other_mask, ret_mask = self._check_mask(other, inplace=True)

        # Set the mask.
        ret_mask.mask[:] = self.mask ^ other_mask.mask

        # Return the result.
        return ret_mask


    def __invert__(self):
        """Implements the unary arithmetic operator.

        When applied to logical arrays, this method will invert the values.
        There is no in-place version of this operator in Python.

        Returns:
            A mask with the result of the operation.
        """

        # Create the mask to return.
        ret_mask = self.copy()

        # Set the return mask elements to the inverted state of this mask.
        ret_mask.mask[:] = ~self.mask

        return ret_mask


    def to_sample_mask(self, other):
        """Creates a new 2d sample based mask.

        to_sample_mask returns a new 2d sample based mask created when called
        by a ping based mask and provided with another sample mask or
        ProcessedData object to obtain the sample count from.

        Args:
            other (Mask obj): A sample mask object used to create a new sample
                based mask.
        """
        if self.type == 'sample':
            return

        # Create a new 2d mask based on the "other" sample mask.
        new_mask = mask(like=other)

        # Set all samples to True for each ping set True in this mask.
        new_mask.mask[self.mask, :] = True

        # Update the type and data.
        self.type = 'sample'
        self.mask = new_mask.mask


    def _check_mask(self, other, inplace=False):
        """Checks that the dimensions and axes values match.

        _check_mask ensures that the dimensions and axes values match. If
        possible, it will coerce a ping mask to a sample mask by vertically
        expanding the ping mask.

        Args:
            other (Mask obj): A given mask object to compare.
            inplace (bool): Set to True if operating in-place.

        Raises:
            ValueError: Mask ping times do not match.
            ValueError: Mask ranges do not match.
            AttributeError: A range baed mask cannot be applied to a depth
                based mask.
            ValueError: Mask depths do not match.
            AttributeError: A depth based mask cannot be applied to a range
                based mask.
            AttributeError: A sample based mask cannot be applied to a ping
                based mask in-place.

        Returns:
            Two mask objects, other_mask and ret_mask.
        """
        # Make sure we share the same ping_time axis.
        if not np.array_equal(self.ping_time, other.ping_time):
            raise ValueError('Mask ping times do not match.')

        # Make sure the vertical axes are the same (if present).
        if hasattr(self, 'range'):
            if hasattr(other, 'range'):
                if not np.array_equal(self.range, other.range):
                    raise ValueError('Mask ranges do not match.')
            else:
                raise AttributeError('You cannot apply a range based mask to '
                                     'a depth based mask.')
        else:
            if hasattr(other, 'depth'):
                if not np.array_equal(self.depth, other.depth):
                    raise ValueError('Mask depths do not match.')
            else:
                raise AttributeError('You cannot apply a depth based mask ' +
                        'to a range based mask.')

        # Check if we need to do any coercion.  We can convert ping masks to
        # sample masks in most cases.  The only time we cannot is when someone
        # is trying to do an in-place operation applying a sample mask to a
        # ping mask because this requires that a new mask array be created
        # which violates in-place.
        ret_mask = None
        if self.type == 'ping' and other.type == 'sample':
            if inplace:
                raise AttributeError('You cannot apply a sample based mask ' +
                        'to a ping based mask in-place')
            else:
                # Create a new 2d mask based on the "other" sample mask.
                ret_mask = mask(like=other)

                # Set all samples to true for each ping set true in the this
                # mask.
                ret_mask.mask[self.mask, :] = True
        elif self.type == 'sample' and other.type == 'ping':
            # Coerce the other mask to a sample mask.
            other_mask = mask(like=self)

            # Set all samples to true for each ping set true in the other mask.
            other_mask.mask[other.mask, :] = True

        else:
            # Mask types match, nothing to do.
            other_mask = other

        if ret_mask is None:
            # We didn't have to coerce the return mask so set the return mask
            # now.
            if inplace:
                # If we're operating in-place, return self.
                ret_mask = self
            else:
                # Create and return a new mask.
                ret_mask = Mask(like=self)

        return other_mask, ret_mask


    def __str__(self):
        """Re-implements string method that provides some basic information
        about the mask object.

        Returns:
            A message with basic information about the mask object.

        """

        # Print the class and address.
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        # Some other basic information.
        msg = msg + "                 mask name: " + self.name + "\n"
        msg = msg + "                      type: " + self.type + "\n"
        msg = msg + "                     color: " + str(self.color) + "\n"
        if self.type.lower() == 'ping':
            msg = (msg + "                dimensions: (" + str(self.n_pings)
                   + ")\n")
        else:
            msg = (msg + "                dimensions: (" + str(self.n_pings)
                   + "," + str(self.n_samples) + ")\n")
            msg = (msg + "             sample offset: " + str(
                self.sample_offset) + "\n")

        return msg
