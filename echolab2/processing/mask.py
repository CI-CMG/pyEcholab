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
from ..ping_data import ping_data


class mask(ping_data):
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
        super(mask, self).__init__()

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
        existing processed_data object but this method can be used to create
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
        existing processed_data object.

        Args:
            like_obj (processed_data obj): The object to base the mask off of.
            value (bool): Set to True to fill array with values.
            mask_type (str): The mask type.

        Raise:
            TypeError: Invalid mask type.
            TypeError: The object argument is not an instance of echolab2
                procesed_data or mask classes.
        """

        # Ensure the value arg is a bool.
        value = bool(value)

        # Copy attributes common to both mask types.
        self.n_pings = like_obj.n_pings
        self.ping_time = like_obj.ping_time.copy()
        self.sample_offset = like_obj.sample_offset

        # Masks must be based on processed_data objects or other masks.  Use
        # type().__name__ to determine if class of "like_obj" is a
        # processed_data object to avoid circular import references
        # (processed_data imports mask so mask cannot import processed_data)
        if type(like_obj).__name__ == 'processed_data':
            # Base this mask off of a processed_data object.

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

        elif isinstance(like_obj, mask):
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
            # We only can base masks on processed_data or mask objects.
            raise TypeError('"like_obj" argument must be an instance of '
                            'echolab2 procesed data or mask classes.')


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


    def apply_between_lines(self, upper_line, lower_line, value=True):
        """Sets mask elements between the provided lines to the specified
        value.

        This is a convenience function. See apply_line for details.

        Args:
            upper_line (line): The line object used to define the upper boundary
                               on the mask where the provided value will be
                               applied.
            lower_line (line): The line object used to define the lower boundary
                               on the mask where the provided value will be
                               applied.
            value (bool): Set this keyword to True to set the mask elements to
                          True, False to False. Default: True

        Raises:
            TypeError: When the mask is a ping mask (1-d mask). You cannot apply
                       a line to a ping mask.
            ValueError: Line line ping times do not match mask times. The line(s)
                        and mask axes must match.
        """

        self.apply_line(upper_line, value=value, other_line=lower_line)


    def apply_below_line(self, line_obj, value=True):
        """Sets mask elements below the line to the specified value.

        This is a convenience function. See apply_line for details.

        Args:
            line_obj (line): The line object used to define the upper boundary
                             on the mask where the provided value will be
                             applied. All mask elements at or below the line
                             will be set.
            value (bool): Set this keyword to True to set the mask elements to
                          True, False to False. Default: True

        Raises:
            TypeError: When the mask is a ping mask (1-d mask). You cannot apply
                       a line to a ping mask.
            ValueError: Line line ping times do not match mask times. The line(s)
                        and mask axes must match.
        """

        self.apply_line(line_obj, value=value, apply_above=False)


    def apply_above_line(self, line_obj, value=True):
        """Sets mask elements above the line to the specified value.

        This is a convenience function. See apply_line for details.

        Args:
            line_obj (line): The line object used to define the lower boundary
                             on the mask where the provided value will be
                             applied. All mask elements at or above the line
                             will be set.
            value (bool): Set this keyword to True to set the mask elements to
                          True, False to False. Default: True

        Raises:
            TypeError: When the mask is a ping mask (1-d mask). You cannot apply
                       a line to a ping mask.
            ValueError: Line line ping times do not match mask times. The line(s)
                        and mask axes must match.
        """

        self.apply_line(line_obj, value=value, apply_above=True)


    def apply_line(self, line_obj, apply_above=False, value=True,
            other_line=None):
        """Sets mask elements above, below, and between lines.

        This method sets this mask's elements above, below, or between the
        provided echolab2.processing.line object(s) to the specified boolean
        value.

        Set apply_above to True to apply the provided value to samples with
        range/depth values LESS THAN OR EQUAL TO the provided line.

        Set apply_above to False to apply the provided value to samples with
        range/depth values GREATER THAN OR EQUAL TO the provided line.

        If you set other_line to a line object, the apply_above argument will
        be ignored and samples greater than or equal to line_obj and samples
        less than or equal to other_line will be set to the provided value.
        In other words, setting other_line will set samples between the two
        lines.

        The line(s) and mask must share the same horizontal axis.

        Args:
            line_obj (line): The line object used to define the vertical
                             boundary for each
            apply_above (bool): Set apply_above to True to apply the provided
                                value to all samples equal to or less than the
                                line range/depth. Set to False to apply to
                                samples greater than or equal to the line range/
                                depth. Default: False
            other_line (line): Set other_line to a line object to set all samples
                               between line_obj and other_line to the provided
                               value. Default: None
            value (bool): Set this keyword to True to set the mask elements to
                          True, False to False. Default: True

        Raises:
            TypeError: When the mask is a ping mask (1-d mask). You cannot apply
                       a line to a ping mask.
            ValueError: Line line ping times do not match mask times. The line(s)
                        and mask axes must match.
        """
        # Make sure this is a sample mask.
        if self.type == 'ping':
            raise TypeError('You cannot apply a line to a ping mask.  You '
                            'must convert it to a sample mask first.')

        # Make sure we share the same ping_time axis.
        if not np.array_equal(self.ping_time, line_obj.ping_time):
            raise ValueError("line_obj ping times do not match this mask's times.")

        # Ensure value is a bool.
        value = bool(value)

        # get our vertical axis
        if hasattr(self, 'range'):
            v_axis = self.range
        else:
            v_axis = self.depth

        #  first check if we're setting between two lines
        if other_line is not None:
            #  we are, check the other line's ping_time axis
            if not np.array_equal(self.ping_time, other_line.ping_time):
                raise ValueError("other_line ping times do not match this mask's times.")

            # apply value to mask elements between the two provided lines
            for ping in range(self.n_pings):
                samps_to_mask = v_axis >= line_obj.data[ping]
                samps_to_mask &= v_axis <= other_line.data[ping]
                self.mask[ping, :][samps_to_mask] = value

        else:
            #  only one line passed so we'll apply above or below that line
            if apply_above:
                # apply value to mask elements less than or equal to the line
                for ping in range(self.n_pings):
                    samps_to_mask = v_axis <= line_obj.data[ping]
                    self.mask[ping, :][samps_to_mask] = value
            else:
                # apply value to mask elements greater than or equal to the line
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
            poly_obj (processed_data obj):
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

    def to_sample_mask(self, other):
        """Creates a new 2d sample based mask.

        to_sample_mask returns a new 2d sample based mask created when called
        by a ping based mask and provided with another sample mask or
        processed_data object to obtain the sample count from.

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


    def __getitem__(self, key):
        """mask objects can be sliced with standard index based
        slicing as well as other mask objects.

        Args:
            key: A mask object or python array slice.

        Returns:
            The sliced/masked mask data.
        """

        # Determine if we're "slicing" with a mask or slicing with slice object.
        if isinstance(key, mask):

            # Make sure the mask applies to this object.
            self._check_mask(key)

            if key.type.lower() == 'sample':
                # This is a 2d mask array which we can directly apply to the
                # data.
                sample_mask = key.mask
            else:
                # This is a ping based mask - create a 2d array based on the
                # mask to apply to the data.
                sample_mask = np.full((self.n_pings, self.n_samples), False,
                                      dtype=bool)

                # Set all samples to True for each ping set True in the ping
                # mask
                sample_mask[key.mask, :] = True

        else:
            # Assume we've been passed slice objects.  Just pass them along.
            sample_mask = key

        # Return the sliced/masked mask data.
        return self.mask[sample_mask]


    def __setitem__(self, key, value):
        """
        We can assign to mask data elements  using assignment with other mask
        objects or we can use python array slicing.

        Args:
            key: A mask object or python array slice.
            value (bool): A scalar to assign.
        """

        # Determine if we're assigning with a mask or assigning with slice
        # object.
        if isinstance(key, mask):
            # It's a mask.  Make sure the mask applies to this object.
            self._check_mask(key)

            if key.type.lower() == 'sample':
                # This is a 2d mask array which we can directly apply to the
                # data.
                sample_mask = key.mask
            else:
                # This is a ping based mask.  Create a 2d array based on the
                # mask to apply to the data.
                sample_mask = np.full((self.n_pings, self.n_samples), False,
                                      dtype=bool)

                # Set all samples to True for each ping set True in the ping
                # mask.
                sample_mask[key.mask, :] = True
        else:
            # Assume we've been passed slice objects.  Just pass them along.
            sample_mask = key

        # Set the mask data to the provided value(s).
        self.data[sample_mask] = bool(value)


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
                ret_mask = mask(like=self)

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
