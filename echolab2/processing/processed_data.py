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

import copy
from future.utils import implements_iterator
import numpy as np
from scipy import sparse
from ..ping_data import ping_data
from ..processing import mask


@implements_iterator
class processed_data(ping_data):
    """The processed_data class defines the horizontal and vertical axes of
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
            synthetic or derived channels.

        is_log: a boolean which is set True when the data is in log form and
            False when it is in linear form. This is handled automatically
            when using the to_log and to_linear methods but if the data is
            converted outside those methods by the user they will need to
            update this attribute appropriately.
        sample_thickness: a float defining the vertical extent of the samples
            in meters. It is calculated as thickness = sample interval(s) *
            sound speed(m/s) / 2.
        sample_offset: The sample number of the first sample in the data array.
            This is typically 0, but can be larger if the data is a subset extracted
            from a larger array.

        *Either* depth or range will be present:

        range: An array of floats defining the distance of the individual samples
            in meters from the transducer face.
        depth: An array of floats defining the distance of the individual samples
            in meters from the surface. Depth is range with the transducer offset
            and (optionally) heave compensation applied.


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

    """

    def __init__(self, channel_id, frequency, data_type):
        """Initializes processed_data class object.

        Creates an empty processed data object
        """
        super(processed_data, self).__init__()

        # Set the frequency, channel_id, and data type.
        if channel_id:
            self.channel_id = channel_id
        else:
            self.channel_id = ''
        self.frequency = frequency
        self.data_type = data_type

        # Data contains the 2d sample data.
        self.data = np.array((),dtype=self.sample_dtype)

        # is_log should be set to True if the data contained within it is in log
        # form, and False otherwise. This is handled internally if you use the
        # to_log and to_linear methods, but if you are manipulating the data
        # manually you should set this state value accordingly.
        self.is_log = False

        # is_heave_corrected will be true when heave correction has been applied.
        self.is_heave_corrected = False

        # The sound velocity used when applying calibrations
        self.sound_velocity = None

        # Sample thickness is the vertical extent of the samples in meters.  It
        # is calculated as thickness = sample interval(s)*sound speed(m/s) / 2.
        self.sample_thickness = 0

        # Sample offset is the number of samples the first row of data are
        # offset away from the transducer face.
        self.sample_offset = 0

        # Define the attribute names for "navigation" data. These are the
        # list of possible field names that store data related to the movement
        # and motion of the sampling platform.
        self._nav_attributes = ['latitude', 'longitude', 'heading', 'trip_distance_nmi',
                'spd_over_grnd_kts', 'pitch', 'heave', 'roll']

        #  extend the _data_attributes list adding our data attribute
        self._data_attributes += ['data']

        #  create a list that stores the scalar object attributes
        self._object_attributes += ['sample_thickness',
                                    'sample_offset',
                                    'sound_velocity',
                                    'frequency',
                                    'data_type',
                                    'is_log',
                                    'is_heave_corrected']


    def replace(self, obj_to_insert, ping_number=None, ping_time=None,
                index_array=None):
        """Inserts data

        This method inserts data without shifting the existing data, resulting
        in the existing data being overwritten by the data in "obj_to_insert".
        You must specify a ping number, ping time or provide an index array.
        Replace only replaces data ping-by-ping. It will never add pings. Any
        extra data in obj_to_insert will be ignored.

        Args:
            obj_to_insert (processed_data): an instance of
                echolab2.processed_data that contains the data you are using
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

        # When inserting/replacing data in processed_data objects we have to
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
        super(processed_data, self).replace(obj_to_insert, ping_number=None,
                ping_time=None, insert_after=True, index_array=None)


    def get_v_axis(self, return_copy=False):
        """Returns a reference to the vertical axis data along with the type in the form:
            [[vertical axis data], vertical axis type as string]]
        for example:
            [[1,2,3,4], 'range']
        """
        if hasattr(self, 'range'):
            #  this is range based data
            attr = getattr(self, 'range')
            if return_copy:
                attr = attr.copy()
            axis_data = [attr, 'range']
        elif hasattr(self, 'depth'):
            #  this is depth based data
            attr = getattr(self, 'depth')
            if return_copy:
                attr = attr.copy()
            axis_data = [attr, 'depth']
        else:
            #  we don't seem to have either range or depth
            axis_data = [[], 'none']

        return axis_data


    def insert(self, obj_to_insert, ping_number=None, ping_time=None,
               insert_after=True, index_array=None, force=False):
        """Inserts the data from the provided echolab2.processed_data object
        into this object.

        The insertion point is specified by ping number or time.

        Args:
            obj_to_insert: an instance of echolab2.processed_data that
                contains the data you are inserting. If required the object's
                sample data will be regridded to the vertical axis of this
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
            force (bool): Set to True to disable checks on frequency and
                datatype. This should only be set when inserting "empty"
                pings (pings where data and attributes are NaN.)
        """
        # If passed an index array, make sure it's a numpy array
        if isinstance(index_array, list):
            index_array = np.array(index_array).astype('uint32')

        # Check that the data types are the same.
        if self.data_type != obj_to_insert.data_type and not force:
            raise TypeError('You cannot insert an object that contains ' +
                    obj_to_insert.data_type + ' data into an object that ' +
                    'contains ' + self.data_type + ' data.')

        # Regrid the object we're inserting to our vertical axis (if the
        # vertical axes are the same regrid will return w/o doing anything).
        obj_to_insert.match_samples(self)

        # We are now coexisting in harmony - call parent's insert.
        super(processed_data, self).insert(obj_to_insert,
                ping_number=ping_number, ping_time=ping_time,
                insert_after=insert_after, index_array=index_array,
                force=force)


    def empty_like(self, n_pings=None, empty_times=False, channel_id=None,
            data_type=None, is_log=False, no_data=False):
        """Returns an object filled with NaNs.

        This method returns a processed_data object with the same general
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
                the new processed_data object will eventually contain. This
                can be used to identify derived or synthetic data types.
            is_log: Set this to True if the new processed_data object will
                contain data in log form. Set it to False if not.
            no_data (bool): When True, the sample data array will not be
                created and the data attribute will be set to None. This
                saves allocating the sample array here if you are planning
                on replacing it in your own code. This is primarily used
                internally in echolab but may be useful to others. The
                default value is False.

        Returns:
            An empty processed_data object.
        """
        # If no data_type is provided, copy this data_type.
        if data_type is None:
            data_type = self.data_type
            is_log = self.is_log

        # Copy this channel id if none provided.
        if channel_id:
            channel_id = channel_id
        else:
            channel_id = self.channel_id

        # Get an empty processed_data object "like" this object.
        empty_obj = processed_data(channel_id, self.frequency, data_type)

        # Call the parent _like helper method
        self._like(empty_obj, n_pings, np.nan, empty_times=empty_times,
                no_data=no_data)
        empty_obj.data_type = data_type
        empty_obj.is_log = is_log

        return empty_obj


    def zeros_like(self, n_pings=None, empty_times=False, channel_id=None,
            data_type=None, is_log=False):
        """Returns an object filled with zeros.

        This method returns a processed_data object with the same general
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
                the new processed_data object will eventually contain. This
                can be used to identify derived or synthetic data types.
            is_log (bool): Set this to True if the new processed_data object
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
            channel_id = self.channel_id

        # Get an empty processed_data object "like" this object.
        zeros_obj = processed_data(channel_id, self.frequency, self.data_type)

        # Call the parent _like helper method
        self._like(zeros_obj, n_pings, 0.0, empty_times=empty_times)
        zeros_obj.data_type = data_type
        zeros_obj.is_log = is_log

        return zeros_obj


    def copy(self):
        """creates a deep copy of this object."""

        # Create an empty processed_data object with the same basic props as
        # our self.
        pd_copy = processed_data(self.channel_id, self.frequency, self.data_type)

        # Call the parent _copy helper method and return the result.
        return self._copy(pd_copy)


    def view(self, ping_slice, sample_slice):
        """Creates a processed_data object whose data attributes are views
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
            A processed_data object, p_data.
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
        p_data = processed_data(self.channel_id, self.frequency, self.data_type)

        # Copy object and data attributes
        p_data._data_attributes = list(self._data_attributes)
        p_data._object_attributes  = list(self._object_attributes)

        # Copy object attributes
        for attr_name in self._object_attributes:
            attr = getattr(self, attr_name)
            # check if this attribute is a numpy array
            if isinstance(attr, np.ndarray):
                # it is - use ndarray's copy method
                setattr(p_data, attr_name, attr.copy())
            elif isinstance(attr, str):
                # Strings are imutable and thus are always copies
                setattr(p_data, attr_name, attr)
            else:
                # it's not - use the copy module
                setattr(p_data, attr_name, copy.deepcopy(attr))

        # Work through the data attributes, slicing them and adding to the new
        # processed_data object.
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


    def to_depth(self, heave_correct=False):
        """to_depth converts the vertical axis to depth by applying the
        transducer offset vertically shifting each ping. If heave_correct
        is set to True, heave correction will be applied as well.

        If the primary axis is already depth and heave_correct is set to
        True and heave compensation has not been applied, only heave
        compensation will be applied. If the primary axis is depth and
        heave_correct is set and heave compensation has been applied
        nothing happens.

        NOTE! HEAVE CORRECTION PERFORMS LINEAR INTERPOLATION OF THE SAMPLE DATA.
        IT IS NOT ADVISED TO APPLY HEAVE CORRECTION AND THEN USE THE DATA FOR
        QUANTITATIVE PURPOSES AT THIS TIME. I have not been able to write a
        performant regridding method that shifts data on a per-ping basis and
        doing so is a low priority at this time. You are welcome to add this
        feature if you need it.
        """

        # Check if vert axis is range or depth
        if not hasattr(self, 'depth'):
            # Get the transducer depth
            if hasattr(self, 'transducer_offset'):
                vert_shift = self.transducer_offset
            else:
                vert_shift = 0
            # note that we're converting from range
            from_range = True
        else:
            #  vert axis is already depth so no shift
            vert_shift = 0
            from_range = False

        # Check if we're applying heave correction
        if heave_correct and hasattr(self, 'heave') and \
                self.is_heave_corrected == False:
            # add heave to our vertical shift
            vert_shift += self.heave
            self.is_heave_corrected == True

        # Now shift the pings if required.
        if np.any(vert_shift):
            #  we have at least 1 ping to shift
            new_axis = self._shift_pings(vert_shift)

            #  update attribute(s) with new axis values
            if from_range:
                # We're converting from range so add depth
                self.add_data_attribute('depth', new_axis)
                # And remove range
                self.remove_data_attribute('range')
            else:
                # Vert axis is already depth - update it
                setattr(self, 'depth', new_axis)
        else:
            #  no shift, but we may need to change the axis
            if from_range:
                # No shift so just swap range and depth
                self.add_data_attribute('depth', self.range)
                self.remove_data_attribute('range')


    def to_range(self):
        """to_range converts the vertical axis to range by removing the
        transducer offset vertically shifting each ping. If heave correction.
        has been applied, it will be backed out.

        If the primary axis is already range this function does nothing.

        In order for heave correction to be applied, you must call the
        processed_data.get_motion() method to

        """
        # Check if vert axis is range or depth
        if hasattr(self, 'depth'):
            # Get the transducer depth
            if hasattr(self, 'transducer_offset'):
                vert_shift = -self.transducer_offset
            else:
                vert_shift = 0
            # note that we're converting from range
            from_depth = True
        else:
            #  vert axis is already range so no shift
            vert_shift = 0
            from_depth = False

        # Check if we need to back out heave correction
        if self.is_heave_corrected:
            if hasattr(self, 'heave'):
                # subtract heave from our vertical shift
                vert_shift -= self.heave
                self.is_heave_corrected == False
            else:
                # is_heave_corrected is set, but we don't have heave data anymore
                AttributeError('Cannot convert to range. Heave correction is applied ' +
                        'but the heave attribute is not present so there is ' +
                        'no way to back out heave.')

        # Now shift the pings if required.
        if np.any(vert_shift):
            #  we have at least 1 ping to shift
            new_axis = self._shift_pings(vert_shift)

            #  update attribute(s) with new axis values
            if from_depth:
                # We're converting from depth so add range
                self.add_data_attribute('range', new_axis)
                # And remove depth
                self.remove_data_attribute('depth')
            else:
                # Vert axis is already range - update it
                setattr(self, 'range', new_axis)
        else:
            #  no shift, but we may need to change the axis
            if from_depth:
                # No shift so just swap depth and range
                self.add_data_attribute('range', self.depth)
                self.remove_data_attribute('depth')


    def heave_correct(self, motion_obj=None):
        """heave_correct applies heave correction. Since heave correction implies
        conversion to depth, we call to_depth with heave_correct set.

        This method will replace the range attribute with depth and apply heave
        correction, shifting samples vertically based on the heave attribute.

        NOTE! THIS METHOD PERFORMS LINEAR INTERPOLATION OF THE SAMPLE DATA. IT IS
        NOT ADVISED TO APPLY HEAVE CORRECTION AND THEN USE THE DATA FOR QUANTITATIVE
        PURPOSES AT THIS TIME. I have not been able to write a performant regridding
        method that shifts data on a per-ping basis and doing so is a low priority
        at this time. You are welcome to add this feature if you need it.

        """

        # Since we're now adding the transducer_offset and heave values to
        # the processed_data object during creation in the EKx0 classes, the
        # motion object is only needed if you need to change the heave data
        if motion_obj is not None:
            #  if the motion_obj is provided, get/update heave
            attr_names, data = motion_obj.interpolate(self, 'heave')

            # iterate through the returned data and add or update it
            for attr_name in attr_names:
                #  check if we had data for this attribute
                if data[attr_name] is not None:
                    #  yes - add or update it
                    if hasattr(self, attr_name):
                        #  update existing attribute
                        setattr(self, attr_name, data[attr_name])
                    else:
                        #  add attribute
                        self.add_data_attribute(attr_name, data[attr_name])

        #  call to_depth, setting heave_correct. If our vert axis already is
        #  depth, to_depth will not apply the transducer draft again.
        self.to_depth(heave_correct=True)


    def shift_pings(self, vert_shift):
        """Shifts sample data vertically by an arbitrary amount.

        If the shift is constant, the vertical axis is changed but the sample
        data remains unchaned.

        If the shift is not constant for all pings, the sample data is interpolated
        to the new vertical axis on a per ping basis.

        NOTE! THE CURRENT IMPLEMENTATION USES LINEAR INTERPOLATION WHEN APPLYING
        A NON-CONSTANT SHIFT. THIS IS NOT IDEAL.

        Args:
            vert_shift (float): A scalar or vector n_pings long that contains the
                constant shift for all pings or a per-ping shift respectively.
        """

        #  get the vertical axis
        _, axis_attr = self.get_v_axis()

        #  compute the new axis (sample data is updated if required)
        new_axis = self._shift_pings(vert_shift)

        #  update the vertical axis
        setattr(self, axis_attr, new_axis)


    def _shift_pings(self, vert_shift):
        """_shift_pings is an internal method that implents interpolated ping
        shifts. If you need to shift data by an arbitrary amount, use the
        processed_data.shift_pings method.
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
                self.data[ping, :] = np.interp( new_axis, vert_axis + vert_shift[ping],
                    self.data[ping, :old_samps], left=np.nan, right=np.nan)

            # Convert back to log units if required.
            if is_log:
                self.to_log()

        return new_axis


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


    def match_samples(self, other_obj, _return_data=False):
        '''match_samples adjusts the vertical axis of this object to match the vertical
        axis of the provided processed_data object. The regridding is a linear combination
        of the inputs based on the fraction of the source bins to the range bins.

        This method performs the same function as the Echoview Match Geometry operator.

        Original code by: Nils Olav Handegard, Alba Ordonez, Rune Øyerhamn
        https://github.com/CRIMAC-WP4-Machine-learning/CRIMAC-preprocessing/blob/NOH_pyech/regrid.py

        Args:
            other_obj (processed_data): Pass a reference to the processed_data object
                    with the vertical axis you would like this object to match.

        '''

        def resample_weights(r_t, r_s):
            """Generates the weights used for resampling
            Original code by: Nils Olav Handegard, Alba Ordonez, Rune Øyerhamn
            """

            # Create target bins from target range
            bin_r_t = np.append(r_t[0]-(r_t[1] - r_t[0])/2, (r_t[0:-1] + r_t[1:])/2)
            bin_r_t = np.append(bin_r_t, r_t[-1]+(r_t[-1] - r_t[-2])/2)

            # Create source bins from source range
            bin_r_s = np.append(r_s[0]-(r_s[1] - r_s[0])/2, (r_s[0:-1] + r_s[1:])/2)
            bin_r_s = np.append(bin_r_s, r_s[-1]+(r_s[-1] - r_s[-2])/2)

            # Initialize W matrix
            W = sparse.lil_matrix((len(r_t), len(r_s)+1), dtype=self.sample_dtype)

            # Loop over the target bins
            for i, rt in enumerate(r_t):

                # Check that this is not an edge case
                if bin_r_t[i] > bin_r_s[0] and bin_r_t[i+1] < bin_r_s[-1]:
                    # Compute the size of the target bin
                    drt = bin_r_t[i+1] - bin_r_t[i]

                    # find the indices in source that overlap this target bin
                    j0 = np.searchsorted(bin_r_s, bin_r_t[i], side='right') - 1
                    j1 = np.searchsorted(bin_r_s, bin_r_t[i+1], side='right')

                    # CASE 1: Target higher resolution, overlapping 1 source bin
                    # target idx     i    i+1
                    # target    -----[-----[-----
                    # source    --[-----------[--
                    # source idx  j0          j1

                    if j1-j0 == 1:
                        W[i, j0] = 1

                    # CASE 2: Target higher resolution, overlapping 1 source bin
                    # target idx      i   i+1
                    # target    --[---[---[---[-
                    # source    -[------[------[-
                    # source idx j0            j1

                    elif j1-j0 == 2:
                        W[i, j0] = (bin_r_s[j0+1]-bin_r_t[i])/drt
                        W[i, j1-1] = (bin_r_t[i+1]-bin_r_s[j1-1])/drt

                    # CASE 3: Target lower resolution
                    # target idx    i       i+1
                    # target    ----[-------[----
                    # source    --[---[---[---[--
                    # source idx  j0          j1

                    elif j1-j0 > 2:
                        for j in range(j0, j1):
                            if j == j0:
                                W[i, j] = (bin_r_s[j+1]-bin_r_t[i])/drt
                            elif j == j1-1:
                                W[i, j] = (bin_r_t[i+1]-bin_r_s[j])/drt
                            else:
                                W[i, j] = (bin_r_s[j+1]-bin_r_s[j])/drt

                #  Edge case 1
                # target idx    i       i+1
                # target    ----[-------[----
                # source        #end# [---[---[
                # source idx          j0  j1

                #  Edge case 2
                # target idx    i       i+1
                # target    ----[-------[----
                # source    --[---[ #end#
                # source idx  j0  j1
                else:
                    # Edge case (NaN must be in W, not in sv_s. Or else np.dot failed)
                    W[i, -1] = np.nan

            return W

        # Get the vertical axes for the source and target objects
        this_v_axis, this_axis_type = self.get_v_axis()
        target_v_axis, other_axis_type = other_obj.get_v_axis(return_copy=True)

        # Check if the new axis is the the same length.
        if len(this_v_axis) == len(target_v_axis):
            # Now check if they are identical.
            if np.all(np.isclose(this_v_axis, target_v_axis)):
                # They are identical.  Nothing to do.
                return

        # Check if they share the same axis type - we'll not allow
        # regridding if the axis types are different.
        if this_axis_type != other_axis_type:
            raise AttributeError("The provided data object's vertical axis type (" +
                    other_axis_type +  ") does not match this object's type (" +
                    this_axis_type + "). The axes types " + "must match.")

        # create the output array, add a row of zeros at the bottom to be used in edge cases
        sv_s_mod = np.full((self.data.shape[1]+1, self.data.shape[0]), 1e-30,
            dtype=self.sample_dtype)
        sv_s_mod[0:self.data.shape[1],0:self.data.shape[0]] = \
                np.rot90(self.data[0:self.data.shape[0], 0:self.data.shape[1]])

        # Generate the weights
        weights = resample_weights(target_v_axis, this_v_axis)

        # Normally we'll update this object's attributes but internal methods
        # that call this method just want the regridded data only. If _return_data
        # is set, we'll just return the data.
        if not _return_data:
            # Compute the regridded values - update shape and sample count
            self.data = np.rot90(weights.dot(sv_s_mod), k=-1)
            self.shape = self.data.shape
            self.n_samples = self.data.shape[1]

            # Update this object's vertical axis
            setattr(self, this_axis_type, target_v_axis)
        else:
            # Return the gridded data only
            sv_s_mod = np.rot90(np.matmul(weights, sv_s_mod), k=-1)
            return sv_s_mod


    def match_pings(self, other_data, match_to='cs'):
        """Matches the ping times in this object to the ping times in the
        processed_data object provided. It does this by matching times, inserting
        and/or deleting pings as needed. It does not interpolate. Ping times in
        the other object that aren't in this object are inserted. Ping times in
        this object that aren't in the other object are deleted. If the time axes
        do not intersect at all, all of the data in this object will be deleted and
        replaced with empty pings for the ping times in the other object.


        This method performs a similar function to the Echoview Match Pings operator.

        Args:
            other_data (processed_data): A processed_data object that this object
                will be matched to.

            match_to (str): Set to a string defining the precision of the match.

                cs : Match to a 100th of a second
                ds : Match to a 10th of a second
                s  : Match to the second
        Returns:
            A dictionary with the keys 'inserted' and 'removed' containing the
            indices of the pings inserted and removed.

        """
        return super(processed_data, self).match_pings(other_data, match_to='cs')


    def resize(self, new_ping_dim, new_sample_dim):
        """Resizes sample data.

        This method re-implements ping_data.resize, adding updating of the
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

        # Call the parent method to resize the arrays (n_samples is updated here).
        super(processed_data, self).resize(new_ping_dim, new_sample_dim)

        # Update n_pings.
        self.n_pings = self.ping_time.shape[0]


    def set_motion(self, motion_obj):
        """set_motion will extract and interpolate pitch, heave, roll, and
        heading data in the provided "motion object" to this object's time
        axis and add them as attributes

        The motion_object is stored in the motion_data attribute of the
        EK60/EK80 object.

        p_data.set_motion(ek80.motion_data)
        """
        motion_types = ['pitch', 'roll', 'heave', 'heading']
        for type in motion_types:
            #  get the interpolated data for this type
            attr_names, data = motion_obj.interpolate(self, type)

            # iterate through the returned data and add or update it
            for attr_name in attr_names:
                #  check if we had data for this attribute
                if attr_name in data:
                    #  yes - add or update it
                    if hasattr(self, attr_name):
                        #  update existing attribute
                        setattr(self, attr_name, data[attr_name])
                    else:
                        #  add attribute
                        self.add_data_attribute(attr_name, data[attr_name])


    def set_navigation(self, nmea_obj):
        """set_navigation will extract and interpolate common navigation
        NMEA datagrams from the provided "NMEA object" to this object's time
        axis and add them as an attributes.

        If 'GGA','RMC', or 'GLL' datagrams are present, the "latitude" and
        "longitude" attributes will be added. If more than one of these
        datagrams are present, preference will be given to GGA or RMC over
        GLL.

        If the 'VTG' datagram is present, the "spd_over_grnd_kts" attribute
        will be added.

        If the 'VLW' datagram is present, the "trip_distance_nmi" attribute
        will be added.

        If the 'SHR' datagram is present, the "heave", "pitch", and "roll"
        attributes will be added.

        When using the EK60 or EK80 classes, the nmea_object is stored in
        the nmea_data attribute.

        p_data.set_navigation(ek80.nmea_data)
        """
        # Define the message types we're going to try to add using the
        # nmea_data metatypes
        nav_types = ['position', 'speed', 'attitude', 'distance']
        for type in nav_types:
            #  get the interpolated data for this type
            attr_names, data = nmea_obj.interpolate(self, type)

            # iterate through the returned data and add or update it
            for attr_name in attr_names:
                #  check if we had data for this attribute
                if attr_name in data:
                    #  yes - add or update it
                    if hasattr(self, attr_name):
                        #  update existing attribute
                        setattr(self, attr_name, data[attr_name])
                    else:
                        #  add attribute
                        self.add_data_attribute(attr_name, data[attr_name])


    def set_navigation_like(self, p_obj):
        """set_navigation_like sets this object's navigation attributes
        like another ping_data object's nav attributes. The other object
        must share this object's time axis.

        This method *does not* copy the data and is best used when processing
        multiple channels that share the same time axis as you can avoid
        interpolating and storing the same data for all of your channels.
        """
        for attr_name in self._nav_attributes:
            if hasattr(p_obj, attr_name):
                if hasattr(self, attr_name):
                    setattr(self, attr_name, getattr(p_obj, attr_name))
                else:
                    self.add_data_attribute(attr_name, getattr(p_obj, attr_name))


    def set_motion_like(self, p_obj):
        """set_motion_like sets this object's motion attributes
        like another ping_data object's motion attributes. The other object
        must share this object's time axis.

        This method *does not* copy the data and is best used when processing
        multiple channels that share the same time axis as you can avoid
        interpolating and storing the same data for all of your channels.
        """
        for attr_name in self._nav_attributes:
            if hasattr(p_obj, attr_name):
                if hasattr(self, attr_name):
                    setattr(self, attr_name, getattr(p_obj, attr_name))
                else:
                    self.add_data_attribute(attr_name, getattr(p_obj, attr_name))


    def __setitem__(self, key, value):
        """
        We can assign to sample data elements in processed_data objects using
        assignment with mask objects or we can use python array slicing.

        When assigning data, the assignment is to the sample data only.
        Currently echolab2 only supports assigning sample data that share the
        exact shape of the mask or data that can be broadcasted into this
        shape. Scalars always work and if using a sample mask, arrays that
        are the same size as the mask work. You'll need to think about how
        this applies to ping masks if you want to assign using these.

        Args:
            key: A mask object or python array slice.
            value (float): A scalar to assign.
        """
        # Determine if we're assigning with a mask or assigning with slice
        # object.
        if isinstance(key, mask.mask):
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
        if isinstance(value, processed_data):
            # It is a processed_data object.  Check if it's compatible.
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


    def __iter__(self):
        """processed_data objects are iterable
        """
        self._iter_idx = 0
        return self


    def __next__(self):
        """processed_data objects are iterable and return a vector containing
        a pings worth of data per iteration.
        """
        self._iter_idx += 1
        if (self._iter_idx > self.n_pings):
            raise StopIteration
        else:
            return self.data[self._iter_idx - 1,:]


    def __getitem__(self, key):
        """processed_data objects can be sliced with standard index based
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
            mask (mask): A mask object.

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

        This method ensures that the processed_data object's dimensions and axes
        values match our data's dimensions and values.

        Args:
            pd_object (processed_data): The processed_data object we are checking.

        Raises:
            ValueError: Ping times do not match.
            ValueError: Ranges do not match.
            AttributeError: Can't operate on depth object with range object.
            ValueError: Depths do not match.
        """

        # Check the ping times and make sure they match.
        if not np.array_equal(self.ping_time, pd_object.ping_time):
            if not self.range.shape == pd_object.range.shape:
                    raise ValueError("The processed_data object has a different "
                            "number of range elements.")
            # Try again, but allow for +- 1 ms
            diff = np.abs((self.ping_time-pd_object.ping_time).astype(np.int32))
            if not np.all(diff <= 1):
                #  OK, these are too different
                raise ValueError("The processed_data object's ping times do not "
                                 "match our ping times.")

        # Make sure the vertical axis is the same.
        if hasattr(pd_object, 'range'):
            if hasattr(self, 'range'):
                if not self.range.shape == pd_object.range.shape:
                    raise ValueError("The processed_data object " + pd_object.channel_id +
                            " has a different number of range values that this object.")
                if not np.allclose(self.range, pd_object.range):
                    raise ValueError("The processed_data object " + pd_object.channel_id +
                            " ranges are different than our ranges.")
            else:
                raise AttributeError('You cannot operate on a range based '
                                     'object with a depth based object.')
        else:
            if hasattr(self, 'depth'):
                if not self.depth.shape == pd_object.depth.shape:
                    raise ValueError("The processed_data object" + pd_object.channel_id +
                            " has a different number of depth values that this object.")
                if not np.allclose(self.depth, mask.depth):
                    raise ValueError("The processed_data object " + pd_object.channel_id +
                            "depths do not match our depths.")
            else:
                raise AttributeError('You cannot operate on a depth based '
                                     'object with a range based object.')


    def __gt__(self, other):
        """Implements the "greater than" operator.

        We accept either a like sized processed_data object, a like sized
        numpy array, or a scalar value.  The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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

        We accept either a like sized processed_data object, a like sized
        numpy array or a scalar value. The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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

        We accept either a like sized processed_data object, a like sized
        numpy array or a scalar value.  The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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

        We accept either a like sized processed_data object, a like sized
        numpy array or a scalar value.  The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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

        We accept either a like sized processed_data object, a like sized
        numpy array or a scalar value. The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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

        We accept either a like sized processed_data object, a like sized
        numpy array or a scalar value. The comparison operators always do a
        element-by-element comparison and return the results in a sample mask.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

        Raises:
            ValueError: Array has wrong shape.

        Returns:
            An array of data from "other".
        """

        # Determine what we're comparing our self to.
        if isinstance(other, processed_data):
            # We've been passed a processed_data object.  Make sure it's kosher.
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
            other: a processed_data object, numpy array, or scalar value.

        Returns:
            A mask object and references to data from "other".

        """
        # Do some checks and get references to the data.
        other_data = self._setup_operators(other)

        # Create the mask we will return.
        compare_mask = mask.mask(like=self)

        # Disable warning for comparing NaNs.
        self._old_npset = np.seterr(invalid='ignore')

        return compare_mask, other_data


    def _setup_numeric(self, other, inplace=False):
        """An internal method that contains generalized code for the numeric
        operators.

        Args:
            other: a processed_data object, numpy array, or scalar value.
            inplace (bool): Set to True to operate in-place.  Otherwise,
                need to create an object to return.

        Returns:
            References to self and the data from "other".
        """
        # Do some checks and get references to the data.
        other_data = self._setup_operators(other)

        # If we're not operating in-place, create a processed_data object to
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
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """

        return self.__add__(other)


    def __iadd__(self, other):
        """Implements the in-place binary addition operator.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """
        return self.__sub__(other)


    def __isub__(self, other):
        """Implements the in-place binary subtraction operator.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """

        return self.__mul__(other)


    def __imul__(self, other):
        """Implements the in-place binary multiplication operator.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """

        return self.__truediv__(other)


    def __itruediv__(self, other):
        """Implements the in-place binary fp division operator.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

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
            other: a processed_data object, numpy array, or scalar value.

        Returns:
            An object containing the results.
        """
        return self.__pow__(other)


    def __ipow__(self, other):
        """Implements the in-place binary power operator.

        Args:
            other: a processed_data object, numpy array, or scalar value.

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
        the processed_data object

        Returns:
            A string with information about the processed_data instance.
        """

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the processed_data instance
        n_pings = len(self.ping_time)
        if n_pings > 0:
            msg =  msg + "                channel(s): [" + self.channel_id + "]\n"
            msg = (msg + "            frequency (Hz): " + str(self.frequency)
                   + "\n")
            msg = (msg + "           data start time: " + str(self.ping_time[
                                                                  0]) + "\n")
            msg = (msg + "             data end time: " + str(self.ping_time[
                                                                  n_pings-1])
                   + "\n")
            msg = msg + "           number of pings: " + str(n_pings) + "\n"
            msg = msg + "           data attributes:"
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
            msg = msg + "  processed_data object contains no data\n"

        return msg


def read_ev_mat(channel_id, frequency, ev_mat_filename, data_type='Sv',
        sample_dtype=np.float32, pad_n_samples=0):
    '''read_ev_mat will read a .mat file exported by Echoview v7 or newer and
    return a processed data object containing the data.
    '''

    import os
    from datetime import datetime
    import scipy.io

    #  read in the echoview data
    ev_mat_filename = os.path.normpath(ev_mat_filename)
    ev_data = scipy.io.loadmat(ev_mat_filename, struct_as_record=False,
            squeeze_me=True)

    #  determine the array sizes
    n_pings = len(ev_data['PingNames'])
    max_samples = -1
    for p in ev_data['PingNames']:
        this_samples = ev_data[p].Sample_count + pad_n_samples
        if this_samples > max_samples:
            max_samples = this_samples

    #  create an empty processed_data object
    p_data = processed_data(channel_id, frequency, data_type)

    #  create the data arrays
    data = np.empty((n_pings, max_samples), dtype=sample_dtype)
    data.fill(np.nan)
    p_data.add_data_attribute('data', data)
    ping_time = np.empty((n_pings), dtype='datetime64[ms]')
    p_data.add_data_attribute('ping_time', ping_time)
    latitude = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('latitude', latitude)
    longitude = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('longitude', longitude)
    trip_distance_nmi = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('trip_distance_nmi', trip_distance_nmi)
    transducer_draft = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('transducer_draft', transducer_draft)

    #  determine the transducer draft - again assume we're on a
    #  fixed grid making this a constant value
    draft = ev_data['P0'].Depth_start - ev_data['P0'].Range_start
    transducer_draft.fill(draft)

    #  set sample thickness - we assume that the the first sample is
    #  centered on 0,0 and the samples are on a fixed grid
    p_data.sample_thickness = np.abs(ev_data['P0'].Range_start) * 2

    #  create the range attribute - this is built on our sample
    #  thickness assumptions above.
    range = np.arange(0, max_samples, dtype=sample_dtype)
    range = range * p_data.sample_thickness
    p_data.add_data_attribute('range', range)

    if data_type in ['Sv', 'Sp', 'TS', 'power','Power']:
        p_data.is_log = True
    else:
        p_data.is_log = False

    #  extract the data
    for idx, ping in enumerate(ev_data['PingNames']):
        p_data.trip_distance_nmi[idx] = ev_data[ping].Distance_vl
        p_data.latitude[idx] = ev_data[ping].Latitude
        p_data.longitude[idx] = ev_data[ping].Longitude
        this_time = ev_data[ping].Ping_date + ' ' + ev_data[ping].Ping_time + '.' + \
                '%3.3i' % ev_data[ping].Ping_milliseconds
        this_time = np.datetime64(datetime.strptime(this_time, "%m-%d-%Y %H:%M:%S.%f"))
        p_data.ping_time[idx] = this_time
        this_n_samps = ev_data[ping].Data_values[:].size
        p_data.data[idx,pad_n_samples:this_n_samps+pad_n_samples] = ev_data[ping].Data_values[:]

    return p_data


def read_ev_csv(channel_id, frequency, ev_csv_filename, data_type='Ts',
        sample_dtype=np.float32):
    '''read_ev_csv will read a .csv file exported by Echoview v7 or newer and
    return a processed data object containing the data.
    '''

    import os
    from datetime import datetime
    import csv

    def convert_float(val):
        try:
            val = float(val)
        except:
            val = np.nan

        return val

    #  read in the echoview data
    ev_csv_filename = os.path.normpath(ev_csv_filename)

    # First determine the array size - this is a bit inefficient but I
    # am feeling lazy. You can implement chunked allocation and skip the
    # double read if you feel you need the performance.
    with open(ev_csv_filename, 'r') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        #  skip the header
        next(csv_reader)
        n_pings = 0
        max_samples = -1
        for row in csv_reader:
            this_samples = int(row[12])
            if this_samples > max_samples:
                max_samples = this_samples
            n_pings += 1

    #  create an empty processed_data object
    p_data = processed_data(channel_id, frequency, data_type)

    #  create the data arrays
    data = np.empty((n_pings, max_samples), dtype=sample_dtype)
    if data_type == 'angles':
        athwart = np.empty((n_pings, max_samples), dtype=sample_dtype)
    p_data.add_data_attribute('data', data)
    ping_time = np.empty((n_pings), dtype='datetime64[ms]')
    p_data.add_data_attribute('ping_time', ping_time)
    latitude = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('latitude', latitude)
    longitude = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('longitude', longitude)
    trip_distance_nmi = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('trip_distance_nmi', trip_distance_nmi)
    transducer_draft = np.empty((n_pings), dtype=sample_dtype)
    p_data.add_data_attribute('transducer_draft', transducer_draft)

    # Now read the file again, loading the data
    idx = 0
    with open(ev_csv_filename, 'r') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        #  skip the header
        next(csv_reader)
        for row in csv_reader:
            if idx == 0:
                #  determine the transducer draft - again assume we're on a
                #  fixed grid making this a constant value
                draft = convert_float(row[8]) - convert_float(row[10])
                transducer_draft.fill(draft)

                #  set sample thickness - we assume that the the first sample is
                #  centered on 0,0 and the samples are on a fixed grid
                p_data.sample_thickness = np.abs(convert_float(row[10])) * 2

                #  create the range attribute - this is built on our sample
                #  thickness assumptions above.
                range = np.arange(0, max_samples, dtype=sample_dtype)
                range = range * p_data.sample_thickness
                p_data.add_data_attribute('range', range)

            p_data.trip_distance_nmi[idx] = convert_float(row[2])
            p_data.latitude[idx] = convert_float(row[6])
            p_data.longitude[idx] = convert_float(row[7])
            this_time = row[3].strip() + ' ' + row[4].strip() + '.' + '%3.3i' % int(float(row[5]))
            this_time = np.datetime64(datetime.strptime(this_time, "%Y-%m-%d %H:%M:%S.%f"))
            p_data.ping_time[idx] = this_time
            this_samples = int(row[12])
            if data_type == 'angles':
                p_data.data[idx,0:this_samples] = row[13:this_samples*2 + 13:2]
                athwart[idx,0:this_samples] = row[14:this_samples * 2 + 14:2]
            else:
                p_data.data[idx,0:this_samples] = row[13:int(row[12]) + 13]
            idx += 1
    p_data.data[p_data.data < -9.9000003e+36] = np.nan

    if data_type.lower() in ['ts', 'sp', 'sv', 'power']:
        p_data.is_log = True

        #  Echoview seems to output 0 for empty (nan) samples in csv format
        #  We can safely convert them to NaN for everything except angles
        p_data.data[p_data.data == 0] = np.nan

    else:
        p_data.is_log = False

    if data_type in ['angles', 'Angles']:
        p_data_athwart = p_data.empty_like()
        p_data_athwart.data = athwart
        p_data_athwart.data_type = 'angles_athwartship'

        p_data.data_type = 'angles_alongship'
        return p_data, p_data_athwart

    else:

        return p_data
