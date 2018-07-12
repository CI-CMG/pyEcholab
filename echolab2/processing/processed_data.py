# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS,#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

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
from ..ping_data import PingData
from echolab2.processing import mask


class ProcessedData(PingData):
    """The ProcessedData class defines the horizontal and vertical axes of
    the data.

    This class stores and manipulates a 2d sample data array along with 1d
    arrays that define the horizontal and vertical axes of that data.  The
    horizontal axis is defined as 'ping_time' and the vertical axis is
    'range' or 'depth'.

    Attributes:
        channel_id: a list of channel id's that are linked to this data.
        frequency: The frequency, in Hz, of the data contained in the object.
        data_type: Data_type is a string defining the type of sample data the
            object contains. Built-in values are:
            'Sv', 'sv', 'Sp', 'sp', 'angles_alongship', 'angles_athwartship',
            'angles_alongship_e', 'angles_athwartship_e', 'power'

            User specified data types are allowed and can be used to identify
            "synthetic" channels.

        is_log: a boolean which is set True when the data is in log form and
            False when it is in linear form. This is handled automatically
            when using the to_log and to_linear methods but if the data is
            converted outside those methods by the user they will need to
            update this attribute appropriately.
        sample_thickness: a float defining the vertical extent of the samples
            in meters. It is calculated as thickness = sample interval(s) *
            sound speed(m/s) / 2.
        sample_offset: The number of samples this data
        range: An array of floats defining the ranges of the individual samples
            in the sample data array. Initially this is range relative to the
            transducer face but you can change this.
        depth: Depth is range relative to the surface.

        *Either* depth or range will be present.

        This class inherits the following attributes from sample_data:

            n_pings: n_pings stores the total number of pings in the object.
            n_samples: the number of samples in the 2d sample array.
            ping_time: An array of numpy datetime64 objects representing the
                times of the individual pings.

        data: The attribute name of the sample data is "data". The sample
            data array is a 2d numpy array indexed as [n_pings, n_samples].
            To access the 100th ping, you would do something like:
            p_data.data[100,:]

            Note that you can access the data directly without specifying the
            data attribute when you slice the object. To access the same
            100th ping you would do this: p_data[100,:]


        NEED TO ADD A SECTION REGARDING SLICING


        NEED TO ADD A SECTION REGARDING OPERATORS



        IMPORTANT NOTE!
            This software is under heavy development and while the API is fairly
            stable, it may still change. Further, while reviewing the code
            you may wonder why certain things are done a certain way.
            Understanding that this class initially was written to have an
            arbitrary number of "sample data" arrays will shed some light on
            this. This was changed later in development so that
            ProcessedData objects only contain a single sample data array
            but much of the mechanics of dealing with multiple 2d arrays are
            in place in part because the sample_data class still operates
            this way and in part because the code hasn't been changed yet.
    """

    def __init__(self, channel_id, frequency, data_type):
        """Initializes ProcessedData class object.

        Creates and sets several internal properties used to store information
        about data and control operation of processed data object instance.
        Code is heavily commented to facilitate use.
        """
        super(ProcessedData, self).__init__()

        # Set the frequency, channel_id, and data type.
        if channel_id:
            if isinstance(channel_id, list):
                # If we've been passed a list as a channel id, copy the list.
                self.channel_id = list(channel_id)
            else:
                # We've been given not a list - just set the id.
                self.channel_id = channel_id
        else:
            self.channel_id = None
        self.frequency = frequency
        self.data_type = data_type

        # Data contains the 2d sample data.
        self.data = None

        #    TODO: finish comment
        # is_log should be set to True if the data contained within it is in log
        # form, and False otherwise. This is handled internally if you use the
        # to_log and to_linear methods, but if you are manipulating the
        self.is_log = False

        # Sample thickness is the vertical extent of the samples in meters.  It
        # is calculated as thickness = sample interval(s)*sound speed(m/s) / 2.
        self.sample_thickness = 0

        # Sample offset is the number of samples the first row of data are
        # offset away from the transducer face.
        self.sample_offset = 0


    def replace(self, obj_to_insert, ping_number=None, ping_time=None,
                index_array=None):
        """Inserts data

        This method inserts data without shifting the existing data, resulting
        in the existing data being overwritten by the data in "obj_to_insert".
        You must specify a ping number, ping time or provide an index array.
        Replace only replaces data ping-by-ping. It will never add pings. Any
        extra data in obj_to_insert will be ignored.

        Args:
            obj_to_insert (ProcessedData): an instance of
                echolab2.ProcessedData that contains the data you are using
                as the replacement. obj_to_insert's sample data will be
                vertically interpolated to the vertical axis of this object.
            ping_number (int): The ping number specifying the first ping to
                replace ping_time: The ping time specifying the first ping to
                replace.
            index_array (array): A numpy array containing the indices of the
                pings you want to replace. Unlike when using a ping number or
                ping time, the pings do not have to be consecutive, but the
                number of "pings" in the obj_to_insert must be the same as
                the number of elements in your index_array. When this keyword is
                present, the ping_number and ping_time keywords are ignored.

        Raises:
            TypeError: Data isn't the same type.
        """

        # Determine how many pings we're inserting.
        if index_array:
            n_inserting = index_array.shape[0]
        else:
            idx = self.get_indices(start_time=ping_time, end_time=ping_time,
                    start_ping=ping_number, end_ping=ping_number)[0]
            n_inserting = self.n_pings - idx
            index_array = np.arange(n_inserting) + idx

        if obj_to_insert is None:
            # When obj_to_insert is None, we automatically create a matching
            # object that contains no data (all NaNs).
            obj_to_insert = self.empty_like(n_inserting, empty_times=True)

            # When replacing, we copy the ping times.
            obj_to_insert.ping_times = self.ping_times[index_array]

        # When inserting/replacing data in ProcessedData objects we have to
        # make sure the data are the same type. The parent method will check
        # if the frequencies are the same.
        if self.data_type != obj_to_insert.data_type:
            raise TypeError('You cannot replace data in an object that '
                            'contains ' + self.data_type.data_type + ' data '
                            'using an object that contains ' +
                            obj_to_insert.data_type + ' data.')

        # Get our range/depth vector.
        if hasattr(self, 'range'):
            this_vaxis = getattr(self, 'range')
        else:
            this_vaxis = getattr(self, 'depth')

        # Interpolate the object we're inserting to our vertical axis (if
        # the vertical axes are the same interpolate will return w/o doing
        # anything).
        obj_to_insert.interpolate(this_vaxis)

        # We are now coexisting in harmony - call parent's insert.
        super(ProcessedData, self).replace( obj_to_insert, ping_number=None,
                ping_time=None, insert_after=True, index_array=None)


    def insert(self, obj_to_insert, ping_number=None, ping_time=None,
               insert_after=True, index_array=None):
        """Inserts the data from the provided echolab2.ProcessedData object
        into this object.

        The insertion point is specified by ping number or time.

        Args:
            obj_to_insert: an instance of echolab2.ProcessedData that
                contains the data you are inserting. The object's sample data
                will be vertically interpolated to the vertical axis of this
                object.
            ping_number: The ping number specifying the insertion point.
            ping_time: The ping time specifying the insertion point. If you
                specify a ping number or ping time, existing data from the
                insertion point on will be shifted after the inserted data.
            insert_after: Set to True to insert *after* the specified ping time
                or ping number. Set to False to insert *at* the specified time
                or ping number.
            index_array: A numpy array containing the indices of the pings you
                want to insert. Unlike when using a ping number or ping time,
                the pings do not have to be consecutive. When this keyword is
                present, the ping_number, ping_time and insert_after keywords
                are ignored.
        """
        # Determine how many pings we're inserting.
        if index_array is None:
            in_idx = self.get_indices(start_time=ping_time, end_time=ping_time,
                    start_ping=ping_number, end_ping=ping_number)[0]
            n_inserting = self.n_pings - in_idx
        else:
            n_inserting = index_array.shape[0]

        if obj_to_insert is None:
            # When obj_to_insert is None, we create automatically create a
            # matching object that contains no data (all NaNs).
            obj_to_insert = self.empty_like(n_inserting, empty_times=True)

        # Check that the data types are the same.
        if self.data_type != obj_to_insert.data_type:
            raise TypeError('You cannot insert an object that contains ' +
                    obj_to_insert.data_type + ' data into an object that ' +
                    'contains ' + self.data_type + ' data.')

        # Get our range/depth vector.
        if hasattr(self, 'range'):
            this_vaxis = getattr(self, 'range')
        else:
            this_vaxis = getattr(self, 'depth')

        # Interpolate the object we're inserting to our vertical axis (if the
        # vertical axes are the same interpolate will return w/o doing
        # anything).
        obj_to_insert.interpolate(this_vaxis)

        # We are now coexisting in harmony - call parent's insert.
        super(ProcessedData, self).insert(obj_to_insert,
                                           ping_number=ping_number,
                                           ping_time=ping_time,
                                           insert_after=insert_after,
                                           index_array=index_array)


    def empty_like(self, n_pings=None, empty_times=False, channel_id=None,
            data_type=None, is_log=False):
        """Returns an object filled with NaNs.

        This method returns a ProcessedData object with the same general
        characteristics of "this" object with all of the data arrays
        filled with NaNs.

        Args:
            n_pings: Set n_pings to an integer specifying the number of pings
                in the new object. By default the number of pings will match
                this object's ping count. The vertical axis (both number of
                samples and depth/range values) will be the same as this object.
            empty_times: Set empty_times to True to return an object with
                an "empty" ping_time attribute (all values set to NaT).
                If n_pings is set and it does not equal this object's n_pings
                value this keyword is forced to True since there isn't a
                1:1 mapping of times between the existing and new object.
            channel_id: Set channel_id to a string specifying the channel_id
                for the new object. If this value is None, the channel_id is
                copied from this object's id.
            data_type: Set data_type to a string defining the type of data
                the new ProcessedData object will eventually contain. This
                can be used to identify derived or synthetic data types.
            is_log: Set this to True if the new ProcessedData object will
                contain data in log form. Set it to False if not.

        Returns:
            An empty ProcessedData object.
        """
        # If no data_type is provided, copy this data_type.
        if data_type is None:
            data_type = self.data_type
            is_log = self.is_log

        # Copy this channel id if none provided.
        if channel_id:
            channel_id = channel_id
        else:
            channel_id = list(self.channel_id)

        # Get an empty ProcessedData object "like" this object.
        empty_obj = ProcessedData(channel_id, self.frequency,
                data_type)
        empty_obj.sample_thickness = self.sample_thickness
        empty_obj.sample_offset = self.sample_offset
        empty_obj.is_log = is_log

        # Call the parent _like helper method and return the result.
        return self._like(empty_obj, n_pings, np.nan, empty_times=empty_times)


    def zeros_like(self, n_pings=None, empty_times=False, channel_id=None,
            data_type=None, is_log=False):
        """Returns an object filled with zeros.

        This method returns a ProcessedData object with the same general
        characteristics of "this" object with all of the data arrays
        filled with zeros.

        This method is commonly used to create synthetic channels.

        Args:
            n_pings (int): Set n_pings to an integer specifying the number of
                pings in the new object. By default the number of pings will
                match this object's ping count. The vertical axis (both
                number of samples and depth/range values) will be the same as
                this object.
            empty_times (bool): Set empty_times to True to return an object with
                an "empty" ping_time attribute (all values set to NaT).
                If n_pings is set and it does not equal this object's n_pings
                value this keyword is forced to True since there isn't a
                1:1 mapping of times between the existing and new object.
            channel_id (str): Set channel_id to a string specifying the
                channel_id for the new object. If this value is None,
                the channel_id is copied from this object's id.
            data_type (str): Set data_type to a string defining the type of data
                the new ProcessedData object will eventually contain. This
                can be used to identify derived or synthetic data types.
            is_log (bool): Set this to True if the new ProcessedData object
                will contain data in log form. Set it to False if not.
        """
        # If no data_type is provided, copy this data_type.
        if data_type is None:
            data_type = self.data_type
            is_log = self.is_log

        # Copy this channel id if none provided.
        if channel_id:
            channel_id = channel_id
        else:
            channel_id = list(self.channel_id)

        # Get an empty ProcessedData object "like" this object.
        empty_obj = ProcessedData(channel_id, self.frequency,
                self.data_type)
        empty_obj.sample_thickness = self.sample_thickness
        empty_obj.sample_offset = self.sample_offset
        empty_obj.is_log = is_log

        # Call the parent _like helper method and return the result.
        return self._like(empty_obj, n_pings, 0.0,
                empty_times=empty_times)


    def copy(self):
        """creates a deep copy of this object."""

        # Create an empty ProcessedData object with the same basic props as
        # our self.
        pd_copy = ProcessedData(self.channel_id,
                self.frequency, self.data_type)

        # Copy the other base attributes of our class.
        pd_copy.sample_thickness = self.sample_thickness
        pd_copy.sample_offset = self.sample_offset
        pd_copy.is_log = self.is_log

        # Call the parent _copy helper method and return the result.
        return self._copy(pd_copy)


    def view(self, ping_slice, sample_slice):
        """Creates a ProcessedData object who's data attributes are views
        into this instance's data.

        This method is intended to be a convenient method for displaying or
        processing rectangular sections of your data. Views are not a method
        for reducing memory usage since as long as the view object exists,
        the original full sized numpy arrays that the new object references
        will exist.

        Args:
            ping_slice (tuple): Set this to a tuple that defines the slicing
                parameters (start, stop, stride) for the ping axis.
            sample_slice (tuple): Set this to a tuple that defines the slicing
                parameters (start, stop, stride) for the sample axis.

        Returns:
            A ProcessedData object, p_data.
        """

        # Check if we've been passed tuples instead of slice objs. Convert
        # to slices if needed.
        if not isinstance(ping_slice, slice):
            ping_slice = slice(ping_slice[0], ping_slice[1], ping_slice[2])
        if not isinstance(sample_slice, slice):
            sample_slice = slice(sample_slice[0], sample_slice[1],
                                 sample_slice[2])

        # Create a new object to return.  The data attributes of the new
        # instance will be views into this instance's data.
        p_data = ProcessedData(self.channel_id, self.frequency, self.data_type)

        # Copy common attributes (include parent class attributes since we
        # don't call a parent method to do this).
        p_data.sample_thickness = self.sample_thickness
        p_data.sample_dtype = self.sample_dtype
        p_data.frequency = self.frequency
        p_data._data_attributes = list(self._data_attributes)
        p_data.is_log = self.is_log

        # Work through the data attributes, slicing them and adding to the new
        # ProcessedData object.
        for attr_name in self._data_attributes:
            attr = getattr(self, attr_name)
            if attr.ndim == 2:
                # 2d arrays can just be sliced as usual.
                setattr(p_data, attr_name, attr.__getitem__((ping_slice,
                                                             sample_slice)))
            else:
                # For 1d arrays, we need to make sure we pick up the correct
                # slice.
                if attr.shape[0] == self.n_pings:
                    # This is a ping axis value.  Slice and set the new
                    # object's attribute.
                    sliced_attr = attr.__getitem__(ping_slice)
                    setattr(p_data, attr_name, sliced_attr)
                    # Update the n_pings attribute.
                    p_data.n_pings = sliced_attr.shape[0]
                else:
                    # We'll assume this is a sample axis value - slice and set.
                    sliced_attr = attr.__getitem__(sample_slice)
                    setattr(p_data, attr_name, sliced_attr)
                    # Update the n_samples attribute.
                    p_data.n_samples = sliced_attr.shape[0]

        # Update the sample_offset if we're slicing on the sample axis.
        if sample_slice.start:
            p_data.sample_offset += sample_slice.start

        return p_data


    def pad_top(self, n_samples):
        """Shifts the data array vertically.

        This method shifts the data array vertically by the specified number of
        samples and inserts NaNs.  Range or depth are updated accordingly.
        This method differs from shift_pings in that you must shift by whole
        samples. No interpolation is performed.

        Args:
            n_samples (int): The number of samples to shift the data array by.
        """
        # Store the old sample number.
        old_samples = self.n_samples

        # Resize the sample data arrays.
        self.resize(self.n_pings, self.n_samples + n_samples)

        # Generate the new range/depth array.
        if hasattr(self, 'range'):
            attr = getattr(self, 'range')
        else:
            attr = getattr(self, 'depth')
        attr[:] = ((np.arange(self.n_samples) - n_samples) *
                   self.sample_thickness + attr[0])

        # Shift and pad the data array.
        self.data[:,n_samples:] = attr[:,0:old_samples]
        self.data[:,0:n_samples] = np.nan


    def shift_pings(self, vert_shift, to_depth=False):
        """Shifts sample data vertically.

        This method shifts sample data vertically by an arbitrary amount,
        interpolating sample data to the new vertical axis.

        Args:
            vert_shift (int): A scalar or vector n_pings long that contains the
                constant shift for all pings or a per-ping shift respectively.
            to_depth (bool): Set to_depth to True if you are converting from
                range to depth.  This option will remove the range attribute
                and replace it with the depth attribute.
        """
        # Determine the vertical extent of the shift.
        min_shift = np.min(vert_shift)
        max_shift = np.max(vert_shift)
        vert_ext = max_shift - min_shift

        # Determine our vertical axis - this has to be range or depth.
        if hasattr(self, 'range'):
            vert_axis = self.range
        else:
            vert_axis = self.depth
            # If we've already converted to depth, unset the to_depth keyword.
            to_depth = False

        # If there is a new vertical extent resize our arrays.
        if vert_ext != 0:
            # Determine the number of new samples as a result of the shift.
            new_samps = (np.ceil(vert_ext.astype('float32') /
                    self.sample_thickness)).astype('uint')
            # Calculate new sample dimension.
            new_sample_dim = (self.n_samples + new_samps).astype('uint')
            # Resize array (n_samples will be updated in the _resize method).
            old_samps = self.n_samples
            self.resize(self.n_pings, new_sample_dim)

        # Create the new vertical axis.
        new_axis = (np.arange(self.n_samples) * self.sample_thickness) + \
                np.min(vert_axis) + min_shift

        # Check if this is not a constant shift.
        if vert_ext != 0:
            # Not a constant, work through the 2d attributes and interpolate
            # the sample data.

            # First convert to linear units if required.
            if self.is_log:
                is_log = True
                self.to_linear()
            else:
                is_log = False

            # Iterate through the pings and interpolate.
            for ping in range(self.n_pings):
                self.data[ping, :] = np.interp(
                    new_axis, vert_axis + vert_shift[ping],
                    self.data[ping, :old_samps], left=np.nan, right=np.nan)

            # Convert back to log units if required.
            if is_log:
                self.to_log()

        # Assign the new axis.
        if to_depth:
            # If we're converting from range to depth, add depth and remove
            # range.
            self.add_attribute('depth', new_axis)
            self.remove_attribute('range')
        else:
            # No conversion, just assign the new vertical axis data.
            vert_axis = new_axis


    def to_linear(self):
        """Converts sample data from log to linear."""
        # Check if we're already in linear form.
        if not self.is_log:
            return

        # Convert the "known" types.
        if self.data_type == 'Sv':
            self.data[:] = 10.0 ** (self.data / 10.0)
            self.data_type = 'sv'
        elif self.data_type == 'Sp':
            self.data[:] = 10.0 ** (self.data / 10.0)
            self.data_type = 'sp'
        else:
            # We're going to assume you know what you're doing.
            self.data[:] = 10.0 ** (self.data / 10.0)

        # Set the is_log flag.
        self.is_log = False


    def to_log(self):
        """Converts sample data from linear to log."""
        #  check if we're already in log form
        if self.is_log:
            return

        # Convert the "known" types.
        if self.data_type == 'sv':
            self.data[:] = 10.0 * np.log10(self.data)
            self.data_type = 'Sv'
        elif self.data_type == 'sp':
            self.data[:] = 10.0 * np.log10(self.data)
            self.data_type = 'Sp'
        else:
            # We're going to assume you know what you're doing.
            self.data[:] = 10.0 * np.log10(self.data)

        # Set the is_log flag.
        self.is_log = True


    def interpolate(self, new_vaxis):
        """Interpolates our sample data to a new vertical axis.

        If the new vertical axis has more samples than the existing
        vertical axis, the sample data array will be resized.

        Args:
            new_vaxis (array): A numpy array that will be the new vertical
                axis for the sample data.

        Raises:
            AttributeError: Range and depth missing.
        """

        # Get the existing vertical axis.
        if hasattr(self, 'range'):
            old_vaxis = getattr(self, 'range').copy()
        elif hasattr(self, 'depth'):
            old_vaxis = getattr(self, 'depth').copy()
        else:
            raise AttributeError('The data object has neither'
                                 ' a range nor depth attribute.')

        # Check if we need to vertically resize our sample data.
        if new_vaxis.shape[0] != self.n_samples:
            self.resize(self.n_pings, new_vaxis.shape[0])
        else:
            # They are the same length.  Check if they are identical.
            if np.all(np.isclose(old_vaxis, new_vaxis)):
                # They are identical.  Nothing to do.
                return

        # Update our sample thickness.
        self.sample_thickness = np.mean(np.ediff1d(new_vaxis))

        # Convert to linear units if required.
        if self.is_log:
            is_log = True
            self.to_linear()
        else:
            is_log = False

        # Interpolate sample data.
        for ping in range(self.n_pings):
            self.data[ping, :] = np.interp(
                new_vaxis, old_vaxis, self.data[ping,:old_vaxis.shape[0]],
                left=np.nan, right=np.nan)

        # Convert back to log units if required.
        if is_log:
            self.to_log()


    def resize(self, new_ping_dim, new_sample_dim):
        """Resizes sample data.

        This method re-implements sample_data.resize, adding updating of the
        vertical axis and n_pings attribute.

        Args:
            new_ping_dim (int): Used to resize the sample data array
                (horizontal axis).
            new_sample_dim (int): Used to resize the sample data array
                (vertical axis).
        """

        # Get the existing vertical axis.
        if hasattr(self, 'range'):
            vaxis = getattr(self, 'range')
        else:
            vaxis = getattr(self, 'depth')

        # Generate the new vertical axis.
        vaxis = np.arange(new_sample_dim) * self.sample_thickness + vaxis[0]

        # Call the parent method to resize the arrays (n_samples is updated
        # here).
        super(ProcessedData, self).resize(new_ping_dim, new_sample_dim)

        # Update n_pings.
        self.n_pings = self.ping_time.shape[0]


    def __setitem__(self, key, value):
        """
        We can assign to sample data elements in ProcessedData objects using
        assignment with mask objects or we can use python array slicing.

        When assigning data, the assignment is to the sample data only.
        Currently echolab2 only supports assigning sample data that share the
        exact shape of the mask or data that can be broadcasted into this
        shape. Scalars always work and if using a sample mask, arrays that
        are the same size as the mask work. You'll need to think about how
        this applies to ping masks if you want to assign using these.

        Args:
            key: A mask object or python array slice.
            value (int): A scalar to assign.
        """
        # Determine if we're assigning with a mask or assigning with slice
        # object.
        if isinstance(key, mask.Mask):
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

        # Check what value we've been given.
        if isinstance(value, ProcessedData):
            # It is a ProcessedData object.  Check if it's compatible.
            self._is_like_me(value)

            # Get a view of the sliced sample data.
            other_data = value.data[sample_mask]
        else:
            # Assume that this is a scalar or numpy array.  We'll let numpy
            # raise the error if the value cannot be broadcast into our
            # sample data array.
            other_data = value

        # Set the sample data to the provided value(s).
        self.data[sample_mask] = other_data


    def __getitem__(self, key):
        """ProcessedData objects can be sliced with standard index based
        slicing as well as mask objects.

        Args:
            key: A mask object or python array slice.

        Returns:
            The sliced/masked sample data.
        """

        # Determine if we're "slicing" with a mask or slicing with slice object.
        if isinstance(key, mask.mask):

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

        # Return the sliced/masked sample data.
        return self.data[sample_mask]


    def _check_mask(self, mask):
        """Checks mask dimensions and values.

        Ensures that the mask dimensions and axes values match our data's
        dimensions and values.
        Args:
            mask (Mask): A mask object.

        Raises:
            ValueError: Ranges do not match.
            AttributeError: Can't compare range mask with depth mask.
            ValueError: Depths do not match.

        """
        # Check the ping times and make sure they match.
        if not np.array_equal(self.ping_time, mask.ping_time):
            raise ValueError('Mask ping times do not match the data ping '
                             'times.')

        # Make sure the mask's vertical axis is the same.  If it exists,
        # ping masks will not have one.
        if hasattr(mask, 'range'):
            # Mask has range.  Check if we have range.
            if hasattr(self, 'range'):
                # We have range.  Make sure they are the same.
                if not np.array_equal(self.range, mask.range):
                    raise ValueError(
                        "The mask's ranges do not match the data ranges.")
            else:
                # We don't have range, so we must have depth and we can't do
                # that.
                raise AttributeError('You cannot compare a range based mask '
                                     'with depth based data.')
        elif hasattr(mask, 'depth'):
            # Mask has depth.  Check if we have depth.
            if hasattr(self, 'depth'):
                # We have depth.  Make sure they are the same.
                if not np.array_equal(self.depth, mask.depth):
                    raise ValueError(
                        "The mask's depths do not match the data depths.")
            else:
                # We don't have depth so we must have range and we can't do
                # that.
                raise AttributeError('You cannot compare a depth based mask '
                                     'with range based data.')


    def _is_like_me(self, pd_object):
        """Checks that the object dimensions and values match data's.

        This method ensures that the ProcessedData object's dimensions and axes
        values match our data's dimensions and values.

        Args:
            pd_object (ProcessedData): The ProcessedData object we are checking.

        Raises:
            ValueError: Ping times do not match.
            ValueError: Ranges do not match.
            AttributeError: Can't operate on depth object with range object.
            ValueError: Depths do not match.
        """

        # Check the ping times and make sure they match.
        if not np.array_equal(self.ping_time, pd_object.ping_time):
            raise ValueError("The ProcessedData object's ping times do not "
                             "match our ping times.")

        # Make sure the vertical axis is the same.
        if hasattr(pd_object, 'range'):
            if hasattr(self, 'range'):
                if not np.array_equal(self.range, pd_object.range):
                    raise ValueError("The ProcessedData object's ranges do "
                                     "not match our ranges.")
            else:
                raise AttributeError('You cannot operate on a range based '
                                     'object with a depth based object.')
        else:
            if hasattr(self, 'depth'):
                if not np.array_equal(self.depth, mask.depth):
                    raise ValueError("The ProcessedData object's depths do "
                                     "not match our depths.")
            else:
                raise AttributeError('You cannot operate on a depth based '
                                     'object with a range based object.')


    def __gt__(self, other):
        """Implements the "greater than" operator.

        We accept either a like sized ProcessedData object, a like sized
        numpy array, or a scalar value.  The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object containing the results of the comparison.
        """
        # Get the new mask and data references.
        compare_mask, other_data = self._setup_compare(other)

        # Set the mask.
        compare_mask.mask[:] = self.data > other_data

        # Restore the error settings we disabled in _setup_compare.
        np.seterr(**self._old_npset)

        return compare_mask


    def __lt__(self, other):
        """Implements the "less than" operator.

        We accept either a like sized ProcessedData object, a like sized
        numpy array or a scalar value. The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object containing the results of the comparison.
        """
        # Get the new mask and data references.
        compare_mask, other_data = self._setup_compare(other)

        # Set the mask.
        compare_mask.mask[:] = self.data < other_data

        # Restore the error settings we disabled in _setup_compare.
        np.seterr(**self._old_npset)

        return compare_mask


    def __ge__(self, other):
        """Implements the "greater than or equal to" operator.

        We accept either a like sized ProcessedData object, a like sized
        numpy array or a scalar value.  The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object containing the results of the comparison.
        """
        # Get the new mask and data references.
        compare_mask, other_data = self._setup_compare(other)

        # Set the mask.
        compare_mask.mask[:] = self.data >= other_data

        # Restore the error settings we disabled in _setup_compare.
        np.seterr(**self._old_npset)

        return compare_mask


    def __le__(self, other):
        """Implements the "less than or equal to" operator.

        We accept either a like sized ProcessedData object, a like sized
        numpy array or a scalar value.  The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object containing the results of the comparison.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data <= other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def __eq__(self, other):
        """Implements the "equal" operator.

        We accept either a like sized ProcessedData object, a like sized
        numpy array or a scalar value. The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object containing the results of the comparison.
        """
        # Get the new mask and data references.
        compare_mask, other_data = self._setup_compare(other)

        # Set the mask.
        compare_mask.mask[:] = self.data == other_data

        # Restore the error settings we disabled in _setup_compare.
        np.seterr(**self._old_npset)

        return compare_mask


    def __ne__(self, other):
        """Implements the "not equal" operator.

        We accept either a like sized ProcessedData object, a like sized
        numpy array or a scalar value. The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object containing the results of the comparison.
        """
        # Get the new mask and data references.
        compare_mask, other_data = self._setup_compare(other)

        # Set the mask.
        compare_mask.mask[:] = self.data != other_data

        # Restore the error settings we disabled in _setup_compare.
        np.seterr(**self._old_npset)

        return compare_mask


    def _setup_operators(self, other):
        """Determines if we can apply the operators.

        This is an internal method that contains generalized code for all of
        the operators. It determines the type of "other" and gets references
        to the sample data and performs some basic checks to ensure that we can
        *probably* successfully apply the operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Raises:
            ValueError: Array has wrong shape.

        Returns:
            An array of data from "other".
        """

        # Determine what we're comparing our self to.
        if isinstance(other, ProcessedData):
            # We've been passed a ProcessedData object.  Make sure it's kosher.
            self._is_like_me(other)

            # Get the references to the other sample data array.
            other_data = other.data

        elif isinstance(other, np.ndarray):
            # The comparison data is a numpy array.  Check its shape.
            if other.shape != self.data.shape:
                raise ValueError(
                    "The numpy array provided for this operation/comparison "
                    "is the wrong shape. this obj:" + str(self.data.shape) +
                    ", array:" + str(other.shape))
            # The array is the same shape as our data array.  Set the reference.
            other_data = other

        else:
            # Assume we've been given a scalar value or something that can be
            # broadcast into our sample data's shape.
            other_data = other

        return other_data


    def _setup_compare(self, other):
        """An internal method that contains generalized code for the
        comparison operators.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            A mask object and references to data from "other".

        """
        # Do some checks and get references to the data.
        other_data = self._setup_operators(other)

        # Create the mask we will return.
        compare_mask = mask.Mask(like=self)

        # Disable warning for comparing NaNs.
        self._old_npset = np.seterr(invalid='ignore')

        return compare_mask, other_data


    def _setup_numeric(self, other, inplace=False):
        """An internal method that contains generalized code for the numeric
        operators.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.
            inplace (bool): Set to True to operate in-place.  Otherwise,
                need to create an object to return.

        Returns:
            References to self and the data from "other".
        """
        # Do some checks and get references to the data.
        other_data = self._setup_operators(other)

        # If we're not operating in-place, create a ProcessedData object to
        # return.
        if not inplace:
            # Return references to a new pd object.
            op_result = self.empty_like()
        else:
            # We're operating in-place.  Return references to our self.
            op_result = self

        return op_result, other_data


    def __add__(self, other):
        """Implements the binary addition operator

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        #  Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other)

        #  Do the math.
        op_result.data[:] = self.data + other_data

        #  Return the result.
        return op_result


    def __radd__(self, other):
        """Implements the reflected binary addition operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """

        return self.__add__(other)


    def __iadd__(self, other):
        """Implements the in-place binary addition operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """

        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other, inplace=True)

        # Do the math.
        op_result.data[:] = self.data + other_data

        # Return the result.
        return op_result


    def __sub__(self, other):
        """Implements the binary subtraction operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references
        op_result, other_data = self._setup_numeric(other)

        # Do the math.
        op_result.data[:] = self.data - other_data

        # Return the result.
        return op_result


    def __rsub__(self, other):
        """Implements the reflected binary subtraction operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """
        return self.__sub__(other)


    def __isub__(self, other):
        """Implements the in-place binary subtraction operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other, inplace=True)

        # Do the math.
        op_result.data[:] = self.data - other_data

        # Return the result.
        return op_result


    def __mul__(self, other):
        """Implements the binary multiplication operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other)

        # Do the math.
        op_result.data[:] = self.data * other_data

        # Return the result.
        return op_result


    def __rmul__(self, other):
        """Implements the reflected binary multiplication operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """

        return self.__mul__(other)


    def __imul__(self, other):
        """Implements the in-place binary multiplication operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.

        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other, inplace=True)

        # Do the math.
        op_result.data[:] = self.data * other_data

        # Return the result.
        return op_result


    def __truediv__(self, other):
        """Implements the binary fp division operator

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other)

        # Do the math.
        op_result.data[:] = self.data / other_data

        # Return the result.
        return op_result


    def __rtruediv__(self, other):
        """Implements the reflected binary fp division operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """

        return self.__truediv__(other)


    def __itruediv__(self, other):
        """Implements the in-place binary fp division operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other, inplace=True)

        # Do the math.
        op_result.data[:] = self.data / other_data

        # Return the result.
        return op_result


    def __pow__(self, other):
        """Implements the binary power operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other)

        # Do the math.
        op_result.data[:] = self.data ** other_data

        # Return the result.
        return op_result


    def __rpow__(self, other):
        """Implements the reflected binary power operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """
        return self.__pow__(other)


    def __ipow__(self, other):
        """Implements the in-place binary power operator.

        Args:
            other: a ProcessedData object, numpy array, or scalar value.

        Returns:
            An object, op_result, containing the results.
        """
        # Do some checks and get the data references.
        op_result, other_data = self._setup_numeric(other, inplace=True)

        # Do the math.
        op_result.data[:] = self.data ** other_data

        # Return the result.
        return op_result


    def __str__(self):
        """Re-implements string method that provides some basic info about
        the ProcessedData object

        Returns:
            A string with information about the ProcessedData instance.
        """

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the ProcessedData instance
        n_pings = len(self.ping_time)
        if n_pings > 0:
            msg = msg + "                channel(s): ["
            for channel in self.channel_id:
                msg = msg + channel + ", "
            msg = msg[0:-2] + "]\n"
            msg = (msg + "                 frequency: " + str(self.frequency)
                   + "\n")
            msg = (msg + "           data start time: " + str(self.ping_time[
                                                                  0]) + "\n")
            msg = (msg + "             data end time: " + str(self.ping_time[
                                                                  n_pings-1])
                   + "\n")
            msg = msg + "            number of pings: " + str(n_pings) + "\n"
            msg = msg + "            data attributes:"
            n_attr = 0
            padding = " "
            for attr_name in self._data_attributes:
                attr = getattr(self, attr_name)
                if n_attr > 0:
                    padding = "                            "
                if isinstance(attr, np.ndarray):
                    if attr.ndim == 1:
                        msg = msg + padding + attr_name + " (%u)\n" % (
                            attr.shape[0])
                    else:
                        msg = msg + padding + attr_name + " (%u,%u)\n" % (
                            attr.shape[0], attr.shape[1])
                elif isinstance(attr, list):
                        msg = msg + padding + attr_name + " (%u)\n" % (len(
                            attr))
                n_attr += 1
        else:
            msg = msg + "  ProcessedData object contains no data\n"

        return msg
