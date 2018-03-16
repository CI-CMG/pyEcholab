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

The processed_data class stores and manipulates a 2d sample data array along
with 1d arrays that define the horizontal and vertical axes of that data.
The horizontal axis is defined as 'ping_time' and the vertical axis is 'range'
or 'depth'.

    properties:
        channel_id: a list of channel id's that are linked to this data

        frequency: The frequency, in Hz, of the data contained in the object

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

            n_pings: n_pings stores the total number of pings in the object

            n_samples: the number of samples in the 2d sample array

            ping_time: An array of numpy datetime64 objects representing the times
                of the individual pings.

        The attribute name of the sample data is "data". The sample data array
        is a 2d numpy array indexed as [n_pings, n_samples]. To access the 100th
        ping, you would do something like:

            p_data.data[100,:]

        Note that you can access the data directly without specifying the data
        attribute when you slice the object. To access the same 100th ping
        you would do this:

            p_data[100,:]


        NEED TO ADD A SECTION REGARDING SLICING


        NEED TO ADD A SECTION REGARDING OPERATORS



        IMPORTANT NOTE!
            This software is under heavy development and while the API is fairly
            stable, it may still change. Further, while reviewing the code you may
            wonder why certain things are done a certain way. Understanting that
            this class initially was written to have an arbitrary number of
            "sample data" arrays will shed some light on this. This was changed
            later in development so that processed_data objects only contain
            a single sample data array but much of the mechanics of dealing with
            multiple 2d arrays are in place in part because the sample_data class
            still operates this way and in part because the code hasn't been
            changed yet.



'''
import numpy as np
from ..ping_data import ping_data
from echolab2.processing import mask


class processed_data(ping_data):
    '''

    '''

    def __init__(self, channel_id, frequency, data_type):

        super(processed_data, self).__init__()

        #  set the frequency, channel_id, and data type
        if (channel_id):
            if (isinstance(channel_id, list)):
                #  if we've been passed a list as a channel id, copy the list
                self.channel_id = list(channel_id)
            else:
                #  we've been given not a list - just set the id
                self.channel_id = channel_id
        else:
            self.channel_id = None
        self.frequency = frequency
        self.data_type = data_type

        #  data contains the 2d sample data
        self.data = None

        #  is_log should be set to True if the data contained within is in log
        #  form and False otherwise. This is handled internally if you use the
        #  to_log and to_linear methods, but if you are manipulating th
        self.is_log = False

        #  sample thickness is the vertical extent of the samples in meters
        #  it is calculated as thickness = sample interval(s) * sound speed(m/s) / 2
        self.sample_thickness = 0

        #  sample offset is the number of samples the first row of data are offset away from
        #  the transducer face.
        self.sample_offset = 0


    def replace(self, obj_to_insert, ping_number=None, ping_time=None,
               index_array=None):
        """
        replace inserts data without shifting the existing data resulting in the
        existing data being overwritten by the data in "obj_to_insert"

        Args:
            obj_to_insert: an instance of echolab2.processed_data that contains the
                data you are using as the replacement. obj_to_insert's sample data
                will be vertically interpolated to the vertical axis of this object.

            ping_number: The ping number specifying the first ping to replace

            ping_time: The ping time specifying the first ping to replace

            index_array: A numpy array containing the indices of the pings you
                want to replace. Unlike when using a ping number or ping time,
                the pings do not have to be consecutive but the number of "pings"
                in the obj_to_insert must be the same as the number of elements
                in your index_array. When this keyword is present, the ping_number
                and ping_time keywords are ignored.

        You must specify a ping number, ping time or provide an index array.

        Replace only replaces data ping-by-ping. It will never add pings. Any extra
        data in obj_to_insert will be ignored.
        """

        #  determine how many pings we're inserting
        if (index_array):
            n_inserting = index_array.shape[0]
        else:
            idx  = self.get_indices(start_time=ping_time, end_time=ping_time,
                    start_ping=ping_number, end_ping=ping_number)[0]
            n_inserting = self.n_pings - idx
            index_array = np.arange(n_inserting) + idx

        if (obj_to_insert is None):
            #  when obj_to_insert is None, we create automatically create a matching
            #  object that contains no data (all NaNs)
            obj_to_insert = self.empty_like(n_inserting, empty_times=True)

            #  when replacing, we copy the ping times
            obj_to_insert.ping_times = self.ping_times[index_array]

        #  when inserting/replacing data in processed_data objects we have to make sure
        #  the data are the same type. The parent method will check if the frequencies are the same.
        if (self.data_type != obj_to_insert.data_type):
            raise TypeError('You cannot replace data in an object that contains ' +
                    self.data_type.data_type + ' data using an object that ' +
                    'contains ' + obj_to_insert.data_type + ' data.')

        #  get our range/depth vector
        if (hasattr(self, 'range')):
            this_vaxis = getattr(self, 'range')
        else:
            this_vaxis = getattr(self, 'depth')

        #  interppolate the object we're inserting to our vertical axis (if the vertical
        #  axes are the same interpolate will return w/o doing anything.)
        obj_to_insert.interpolate(this_vaxis)

        #  we are now coexisting in harmony - call parent's insert
        super(processed_data, self).replace( obj_to_insert, ping_number=None,
                ping_time=None, insert_after=True, index_array=None)


    def insert(self, obj_to_insert, ping_number=None, ping_time=None,
               insert_after=True, index_array=None):
        """
        insert inserts the data from the provided echolab2.processed_data object into
        this object. The insertion point is specified by ping number or time.

        Args:
            obj_to_insert: an instance of echolab2.processed_data that contains the
                data you are inserting. The object's sample data will be vertically
                interpolated to the vertical axis of this object.

            ping_number: The ping number specifying the insertion point

            ping_time: The ping time specifying the insertion point

            If you specify a ping number or ping time, existing data from
            the insertion point on will be shifted after the inserted data.

            insert_after: Set to True to insert *after* the specified ping time
                or ping number. Set to False to insert *at* the specified time
                or ping number.

            index_array: A numpy array containing the indices of the pings you
                want to insert. Unlike when using a ping number or ping time,
                the pings do not have to be consecutive. When this keyword is
                present, the ping_number, ping_time and insert_after keywords
                are ignored.
        """
        #  determine how many pings we're inserting
        if (index_array is None):
            in_idx  = self.get_indices(start_time=ping_time, end_time=ping_time,
                    start_ping=ping_number, end_ping=ping_number)[0]
            n_inserting = self.n_pings - in_idx
        else:
            n_inserting = index_array.shape[0]

        if (obj_to_insert is None):
            #  when obj_to_insert is None, we create automatically create a
            # matching object that contains no data (all NaNs)
            obj_to_insert = self.empty_like(n_inserting, empty_times=True)

        #  check that the data types are the same
        if (self.data_type != obj_to_insert.data_type):
            raise TypeError('You cannot insert an object that contains ' +
                    obj_to_insert.data_type + ' data into an object that ' +
                    'contains ' + self.data_type + ' data.')

        #  get our range/depth vector
        if (hasattr(self, 'range')):
            this_vaxis = getattr(self, 'range')
        else:
            this_vaxis = getattr(self, 'depth')

        #  interpolate the object we're inserting to our vertical axis (if
        # the vertical axes are the same interpolate will return w/o doing
        # anything.)
        obj_to_insert.interpolate(this_vaxis)

        #  we are now coexisting in harmony - call parent's insert
        super(processed_data, self).insert(obj_to_insert,
                                           ping_number=ping_number,
                                           ping_time=ping_time,
                                           insert_after=insert_after,
                                           index_array=index_array)


    def empty_like(self, n_pings=None, empty_times=False, channel_id=None,
            data_type=None, is_log=False):
        """
        empty_like returns a processed_data object with the same general
        characteristics of "this" object with all of the data arrays
        filled with NaNs

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

        """
        #  if no data_type is provided, copy this data_type
        if (data_type is None):
            data_type = self.data_type
            is_log = self.is_log

        #  copy this channel id if none provided
        if (channel_id):
            channel_id = channel_id
        else:
            channel_id = list(self.channel_id)

        #  get an empty processed_data object "like" this object
        empty_obj = processed_data(channel_id, self.frequency,
                data_type)
        empty_obj.sample_thickness = self.sample_thickness
        empty_obj.sample_offset = self.sample_offset
        empty_obj.is_log = is_log

         #  call the parent _like helper method and return the result
        return self._like(empty_obj, n_pings, np.nan,
                empty_times=empty_times)


    def zeros_like(self, n_pings=None, empty_times=False, channel_id=None,
            data_type=None, is_log=False):
        """
        zeros_like returns a processed_data object with the same general
        characteristics of "this" object with all of the data arrays
        filled with zeros

        This method is commonly used to create synthetic channels.

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
        """
        #  if no data_type is provided, copy this data_type
        if (data_type is None):
            data_type = self.data_type
            is_log = self.is_log

        #  copy this channel id if none provided
        if (channel_id):
            channel_id = channel_id
        else:
            channel_id = list(self.channel_id)

        #  get an empty processed_data object "like" this object
        empty_obj = processed_data(channel_id, self.frequency,
                self.data_type)
        empty_obj.sample_thickness = self.sample_thickness
        empty_obj.sample_offset = self.sample_offset
        empty_obj.is_log = is_log

        #  call the parent _like helper method and return the result
        return self._like(empty_obj, n_pings, 0.0,
                empty_times=empty_times)


    def copy(self):
        """
        copy creates a deep copy of this object.
        """

        #  create an empty processed_data object with the same basic props as ourself
        pd_copy = processed_data(self.channel_id,
                self.frequency, self.data_type)

        #  copy the other base attributes of our class
        pd_copy.sample_thickness = self.sample_thickness
        pd_copy.sample_offset = self.sample_offset
        pd_copy.is_log = self.is_log

        #  call the parent _copy helper method and return the result
        return self._copy(pd_copy)


    def view(self, ping_slice, sample_slice):
        """
        view returns a processed_data object who's data attributes are views
        into this instance's data. This is intended to be a convienient method
        for displaying or processing rectangular sections of your data.

        args:
            ping_slice: Set this to a tuple that defines the slicing parameters
                (start, stop, stride) for the ping axis.
            sample_slice: Set this to a tuple that defines the slicing parameters
                (start, stop, stride) for the sample axis.

        Views are not a method for reducing memory usage since as long as the view
        object exists, the original full sized numpy arrays that the new object
        references will exist.

        """

        #  check if we've been passed tuples instead of slice objs. Convert
        #  to slices if needed.
        if (not isinstance(ping_slice, slice)):
            ping_slice = slice(ping_slice[0], ping_slice[1], ping_slice[2])
        if (not isinstance(sample_slice, slice)):
            sample_slice = slice(sample_slice[0], sample_slice[1], sample_slice[2])

        #  create a new object to return - the data attributes of the new instance will
        #  be views into this instance's data.
        p_data = processed_data(self.channel_id, self.frequency, self.data_type)

        #  copy common attributes (include parent class attributes since
        #  we don't call a parent method to do this.)
        p_data.sample_thickness = self.sample_thickness
        p_data.sample_dtype = self.sample_dtype
        p_data.frequency = self.frequency
        p_data._data_attributes = list(self._data_attributes)
        p_data.is_log = self.is_log

        #  work thru the data attributes, slicing them and adding to the new
        #  processed_data object.
        for attr_name in self._data_attributes:
            attr = getattr(self, attr_name)
            if (attr.ndim == 2):
                #  2d arrays can just be sliced as usual
                setattr(p_data, attr_name, attr.__getitem__((ping_slice, sample_slice)))
            else:
                #  for 1d arrays we need to make sure we pick up the correct slice
                if (attr.shape[0] == self.n_pings):
                    #  this is a ping axis value - slice and set the new object's attribute
                    sliced_attr = attr.__getitem__(ping_slice)
                    setattr(p_data, attr_name, sliced_attr)
                    #  update the n_pings attribute
                    p_data.n_pings = sliced_attr.shape[0]
                else:
                    #  we'll assume this is a sample axis value - slice and set
                    sliced_attr = attr.__getitem__(sample_slice)
                    setattr(p_data, attr_name, sliced_attr)
                    #  update the n_samples attribute
                    p_data.n_samples = sliced_attr.shape[0]

        #  update the sample_offset if we're slicing on the sample axis
        if (sample_slice.start):
            p_data.sample_offset += sample_slice.start

        return p_data


    def pad_top(self, n_samples):
        """
        pad_top shifts the data array vertically the specified number of samples
        and insert NaNs. The range or depth axis is updated accordingly.

        This method differs from shift_pings in that that you must shift by whole
        samples. No interpolation is performed.
        """
        #  store the old sample number
        old_samples = self.n_samples

        #  resize the sample data arrays
        self.resize(self.n_pings, self.n_samples + n_samples)

        #  generate the new range/depth array
        if (hasattr(self, 'range')):
            attr = getattr(self, 'range')
        else:
            attr = getattr(self, 'depth')
        attr[:] = (np.arange(self.n_samples) - n_samples) * self.sample_thickness + attr[0]

        #  shift and pad
        self.data[:,n_samples:] = attr[:,0:old_samples]
        self.data[:,0:n_samples] = np.nan


    def shift_pings(self, vert_shift, to_depth=False):
        """
        shift_pings shifts sample data vertically by an arbitrary amount,
        interpolating sample data to the new vertical axis.

            vert_shift is a scalar or vector n_pings long that contains the
            constant shift for all pings or a per-ping shift respectively.

            Set to_depth to True if you are converting from range to depth
            This option will remove the range attribute and replace it with
            the depth attribute.

        """
        #  determine the vertical extent of the shift
        min_shift = np.min(vert_shift)
        max_shift = np.max(vert_shift)
        vert_ext = max_shift - min_shift

        #  determine our vertical axis - this has to be range or depth
        if hasattr(self, 'range'):
            vert_axis = self.range
        else:
            vert_axis = self.depth
            #  if we've already converted to depth, unset the to_depth keyword
            to_depth = False

        #  if there is a new vertical extent resize our arrays
        if (vert_ext != 0):
            #  determine the number of new samples as a result of the shift
            new_samps = (np.ceil(vert_ext.astype('float32') /
                    self.sample_thickness)).astype('uint')
            # calculate new sample dimension
            new_sample_dim = (self.n_samples + new_samps).astype('uint')
            #  and resize (n_samples will be updated in the _resize method)
            old_samps = self.n_samples
            self.resize(self.n_pings, new_sample_dim)

        # create the new vertical axis
        new_axis = (np.arange(self.n_samples) * self.sample_thickness) + \
                np.min(vert_axis) + min_shift

        #  check if this is not a constant shift
        if (vert_ext != 0):
            #  not constant, work thru the 2d attributes and interpolate the sample data

            #  first convert to linear units if required
            if (self.is_log):
                is_log = True
                self.to_linear()
            else:
                is_log = False

            #  iterate thru the pings and interpolate
            for ping in range(self.n_pings):
                self.data[ping,:] = np.interp(new_axis, vert_axis + vert_shift[ping],
                        self.data[ping,:old_samps], left=np.nan, right=np.nan)

            #  convert back to log units if required
            if (is_log):
                self.to_log()

        # and assign the new axis
        if (to_depth):
            #  if we're converting from range to depth, add depth and remove range
            self.add_attribute('depth', new_axis)
            self.remove_attribute('range')
        else:
            #  no conversion, just assign the new vertical axis data
            vert_axis = new_axis


    def to_linear(self):
        """
        to_linear converts sample data from log to linear
        """
        #  check if we're already in linear form
        if (not self.is_log):
            return

        #  convert the "known" types
        if (self.data_type == 'Sv'):
            self.data[:] = 10.0 ** (self.data / 10.0)
            self.data_type = 'sv'
        elif (self.data_type == 'Sp'):
            self.data[:] = 10.0 ** (self.data / 10.0)
            self.data_type = 'sp'
        else:
            #  we're going to assume you know what you're doing
            self.data[:] = 10.0 ** (self.data / 10.0)

        #  set the is_log flag
        self.is_log = False


    def to_log(self):
        """
        to_log converts sample data from linear to log
        """
        #  check if we're already in log form
        if (self.is_log):
            return

        #  convert the "known" types
        if (self.data_type == 'sv'):
            self.data[:] = 10.0 * np.log10(self.data)
            self.data_type = 'Sv'
        elif (self.data_type == 'sp'):
            self.data[:] = 10.0 * np.log10(self.data)
            self.data_type = 'Sp'
        else:
            #  we're going to assume you know what you're doing
            self.data[:] = 10.0 * np.log10(self.data)

        #  set the is_log flag
        self.is_log = True


    def interpolate(self, new_vaxis):
        """
        interpolate vertically interpolates our sample data to a new vertical
        axis. If the new vertical axis has more samples than the existing
        vertical axis the sample data array will be resized.

        """

        #  get the existing vertical axis
        if (hasattr(self, 'range')):
            old_vaxis = getattr(self, 'range').copy()
        elif (hasattr(self, 'depth')):
            old_vaxis = getattr(self, 'depth').copy()
        else:
            raise AttributeError('The data object has neither'
                                 ' a range nor depth attribute.')

        #  check if we need to vertically resize our sample data
        if (new_vaxis.shape[0] != self.n_samples):
            self.resize(self.n_pings, new_vaxis.shape[0])
        else:
            #  they are the same length - check if they are identical
            if (np.all(np.isclose(old_vaxis, new_vaxis))):
                #  they are the same - nothing to do
                return

        #  update our sample thickness
        self.sample_thickness = np.mean(np.ediff1d(new_vaxis))

        #  convert to linear units if required
        if (self.is_log):
            is_log = True
            self.to_linear()
        else:
            is_log = False

        #  interpolate
        for ping in range(self.n_pings):
            self.data[ping,:] = np.interp(new_vaxis, old_vaxis,
                    self.data[ping,:old_vaxis.shape[0]], left=np.nan, right=np.nan)

        #  convert back to log units if required
        if (is_log):
            self.to_log()


    def resize(self, new_ping_dim, new_sample_dim):
        """
        resize reimplements sample_data.resize adding updating of the vertical axis and
        n_pings attribute.
        """

        #  get the existing vertical axis
        if (hasattr(self, 'range')):
            vaxis = getattr(self, 'range')
        else:
            vaxis = getattr(self, 'depth')

        #  and generate the new vertical axis
        vaxis = np.arange(new_sample_dim) * self.sample_thickness + vaxis[0]

        #  call the parent method to resize the arrays (n_samples is updated here)
        super(processed_data, self).resize(new_ping_dim, new_sample_dim)

        #  and then update n_pings
        self.n_pings = self.ping_time.shape[0]


    def __setitem__(self, key, value):
        """
        we can assign to sample data elements in processed_data objects using
        assignment with mask objects or we can use python array slicing.

        When assigning data, the assigment is to the sample data only. Currently
        echolab2 only supports assigning sample data that share the exact
        shape of the mask or data that can be broadcasted into this shape. Scalars
        always work and if using a sample mask, arrays that are the same size as the
        mask work. You'll need to think about how this applies to ping masks
        if you want to assign using these.
        """
        #  determine if we're assigning with a mask or assigning with slice object
        if (isinstance(key, mask.mask)):
            #  it's a mask - make sure the mask applies to this object
            self._check_mask(key)

            if (key.type.lower() == 'sample'):
                #  this is a 2d mask array which we can directly apply to the data
                sample_mask = key.mask
            else:
                #  this is a ping based mask - create a 2d array based on the mask
                #  to apply to the data.
                sample_mask = np.full((self.n_pings,self.n_samples), False, dtype=bool)

                #  set all samples to true for each ping set true in the ping mask
                sample_mask[key.mask,:] = True
        else:
            #  assume we've been passed slice objects - just pass them along
            sample_mask = key

        #  check what value we've been given
        if (isinstance(value, processed_data)):
            #  it is a processed_data object - check if it's compatible
            self._is_like_me(value)

            # and get a view of the sliced sample data
            other_data = value.data[sample_mask]
        else:
            #  assume that this is a scalar or numpy array - we'll let
            #  numpy raise the error if the value cannot be broadcast into
            #  our sample data array.
            other_data = value

        #  set the sample data to the provided value(s)
        self.data[sample_mask] = other_data


    def __getitem__(self, key):
        """
        processed_data objects can be sliced with standard index based slicing as
        well as mask objects.
        """

        #  determine if we're "slicing" with a mask or slicing with slice object
        if (isinstance(key, mask.mask)):

            #  make sure the mask applies to this object
            self._check_mask(key)

            if (key.type.lower() == 'sample'):
                #  this is a 2d mask array which we can directly apply to the data
                sample_mask = key.mask
            else:
                #  this is a ping based mask - create a 2d array based on the mask
                #  to apply to the data.
                sample_mask = np.full((self.n_pings,self.n_samples), False, dtype=bool)

                #  set all samples to true for each ping set true in the ping mask
                sample_mask[key.mask,:] = True

        else:
            #  assume we've been passed slice objects - just pass them along
            sample_mask = key

        #  return the sliced/masked sample data
        return self.data[sample_mask]


    def _check_mask(self, mask):
        '''
        _check_mask ensures that the mask dimensions and axes values match
        our data's dimensions and values.
        '''
        #  check the ping times and make sure they match
        if (not np.array_equal(self.ping_time, mask.ping_time)):
            raise ValueError('Mask ping times do not match the data ping times.')

        #  make sure the mask's vertical axis (if it exists - ping masks will not have one) is the same
        if (hasattr(mask, 'range')):
            #  mask has range - check if we have range
            if (hasattr(self, 'range')):
                #  we have range - make sure they are the same
                if (not np.array_equal(self.range, mask.range)):
                    raise ValueError("The mask's ranges do not match the data ranges.")
            else:
                #  we don't have range so we must have depth and we can't do that
                raise AttributeError('You cannot compare a range based mask with depth based data.')
        elif (hasattr(mask, 'depth')):
            #  mask has depth - check if we have depth
            if (hasattr(self, 'depth')):
                #  we have depth - make sure they are the same
                if (not np.array_equal(self.depth, mask.depth)):
                    raise ValueError("The mask's depths do not match the data depths.")
            else:
                #  we don't have depth so we must have range and we can't do that
                raise AttributeError('You cannot compare a depth based mask with range based data.')


    def _is_like_me(self, pd_object):
        '''
        _is_like_me ensures that the processed_data object's dimensions and axes
        values match our data's dimensions and values.
        '''

        #  check the ping times and make sure they match
        if (not np.array_equal(self.ping_time, pd_object.ping_time)):
            raise ValueError("The processed_data object's ping times do not match our ping times.")

        #  make sure the vertical axis is the same
        if (hasattr(pd_object, 'range')):
            if (hasattr(self, 'range')):
                if (not np.array_equal(self.range, pd_object.range)):
                    raise ValueError("The processed_data object's ranges do not match our ranges.")
            else:
                raise AttributeError('You cannot operate on a range based object with a depth based object.')
        else:
            if (hasattr(self, 'depth')):
                if (not np.array_equal(self.depth, mask.depth)):
                    raise ValueError("The processed_data object's depths do not match our depths.")
            else:
                raise AttributeError('You cannot operate on a depth based object with a range based object.')


    def __gt__(self, other):
        """
        __gt__ implements the "greater than" operator. We accept either a like sized
        processed_data object, a like sized numpy array or a scalar value.

        The comparison operators always do a element-by-element comparison and return
        the results in a sample mask.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data > other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def __lt__(self, other):
        """
        __lt__ implements the "less than" operator. We accept either a like
        sized processed_data object, a like sized numpy array or a scalar value.

        The comparison operators always do a element-by-element comparison
        and return the results in a sample mask.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data < other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def __ge__(self, other):
        """
        __ge__ implements the "greater than or equal to" operator. We accept
        either a like sized processed_data object, a like sized numpy array
        or a scalar value.

        The comparison operators always do a element-by-element comparison
        and return the results in a sample mask.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data >= other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def __le__(self, other):
        """
        __le__ implements the "less than or equal to" operator. We accept
        either a like sized processed_data object, a like sized numpy array
        or a scalar value.

        The comparison operators always do a element-by-element comparison
        and return the results in a sample mask.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data <= other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def __eq__(self, other):
        """
        __eq__ implements the "equal" operator. We accept either a like sized
        processed_data object, a like sized numpy array or a scalar value.

        The comparison operators always do a element-by-element comparison and return
        the results in a sample mask.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data == other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def __ne__(self, other):
        """
        __ne__ implements the "not equal" operator. We accept either a like sized
        processed_data object, a like sized numpy array or a scalar value.

        The comparison operators always do a element-by-element comparison and return
        the results in a sample mask.
        """
        #  get the new mask and data references
        compare_mask, other_data = self._setup_compare(other)

        #  and set the mask
        compare_mask.mask[:] = self.data != other_data

        #  restore the error settings we disabled in _setup_compare
        np.seterr(**self._old_npset)

        return compare_mask


    def _setup_operators(self, other):
        """
        _setup_operators is an internal method that contains generalized code for
        all of the operators. It determines the type of "other" and gets references
        to the sample data and performs some basic checks to ensure that we can
        *probably* successfully apply the operator.
        """

        #  determine what we're comparing ourself to
        if (isinstance(other, processed_data)):
            #  we've been passed a processed_data object - make sure it's kosher
            self._is_like_me(other)

            #  get the references to the other sample data array
            other_data = other.data

        elif (isinstance(other, np.ndarray)):
            #  the comparison data is a numpy array - check its shape
            if (other.shape != self.data.shape):
                raise ValueError("The numpy array provided for this operation/comparison is " +
                        "the wrong shape. this obj:" + str(self.data.shape) + ", array:" +
                        str(other.shape))
            #  the array is the same shape as our data array - set the reference
            other_data = other

        else:
            #  assume we've been given a scalar value or something that can
            #  be broadcast into our sample data's shape.
            other_data = other

        return other_data


    def _setup_compare(self, other):
        """
        _setup_compare is an internal method that contains generalized code for
        the comparison operators.
        """
        #  do some checks and get references to the data
        other_data = self._setup_operators(other)

        #  create the mask we will return
        compare_mask = mask.mask(like=self)

        #  disable warning for comparing NaNs
        self._old_npset = np.seterr(invalid='ignore')

        return (compare_mask, other_data)


    def _setup_numeric(self, other, inplace=False):
        """
        _setup_numeric is an internal method that contains generalized code for
        the numeric operators.
        """
        #  do some checks and get references to the data
        other_data = self._setup_operators(other)

        #  if we're not operating in-place, create a processed_data object to return
        if (not inplace):
            #  return refs to a new pd object
            op_result = self.empty_like()
        else:
            #  we're operating in-place - return refs to ourself
            op_result = self

        return (op_result, other_data)


    def __add__(self, other):
        """
        __add__ implements the binary addition operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other)

        #  do the math
        op_result.data[:] = self.data + other_data

        #  and return the result
        return op_result


    def __radd__(self, other):
        """
        __radd__ implements the reflected binary addition operator
        """

        return self.__add__(other)


    def __iadd__(self, other):
        """
        __iadd__ implements the in-place binary addition operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other, inplace=True)

        #  do the math
        op_result.data[:] = self.data + other_data

        #  and return the result
        return op_result


    def __sub__(self, other):
        """
        __sub__ implements the binary subtraction operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other)

        #  do the math
        op_result.data[:] = self.data - other_data

        #  and return the result
        return op_result


    def __rsub__(self, other):
        """
        __rsub__ implements the reflected binary subtraction operator
        """

        return self.__sub__(other)


    def __isub__(self, other):
        """
        __isub__ implements the in-place binary subtraction operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other, inplace=True)

        #  do the math
        op_result.data[:] = self.data - other_data

        #  and return the result
        return op_result


    def __mul__(self, other):
        """
        __mul__ implements the binary multiplication operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other)

        #  do the math
        op_result.data[:] = self.data * other_data

        #  and return the result
        return op_result


    def __rmul__(self, other):
        """
        __rmul__ implements the reflected binary multiplication operator
        """

        return self.__mul__(other)


    def __imul__(self, other):
        """
        __imul__ implements the in-place binary multiplication operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other, inplace=True)

        #  do the math
        op_result.data[:] = self.data * other_data

        #  and return the result
        return op_result


    def __truediv__(self, other):
        """
        __truediv__ implements the binary fp division operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other)

        #  do the math
        op_result.data[:] = self.data / other_data

        #  and return the result
        return op_result


    def __rtruediv__(self, other):
        """
        __rtruediv__ implements the reflected binary fp division operator
        """

        return self.__truediv__(other)


    def __itruediv__(self, other):
        """
        __itruediv__ implements the in-place binary fp division operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other, inplace=True)

        #  do the math
        op_result.data[:] = self.data / other_data

        #  and return the result
        return op_result


    def __pow__(self, other):
        """
        __pow__ implements the binary power operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other)

        #  do the math
        op_result.data[:] = self.data ** other_data

        #  and return the result
        return op_result


    def __rpow__(self, other):
        """
        __rpow__ implements the reflected binary power operator
        """

        return self.__pow__(other)


    def __ipow__(self, other):
        """
        __ipow__ implements the in-place binary power operator
        """
        #  do some checks and get the data references
        op_result, other_data = self._setup_numeric(other, inplace=True)

        #  do the math
        op_result.data[:] = self.data ** other_data

        #  and return the result
        return op_result


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
            msg = msg + "           data attributes:"
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
