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

                      CLASS DESCRIPTION GOES HERE

'''
import numpy as np
from ..sample_data import sample_data


class processed_data(sample_data):
    '''
    The processed_data class contains
    '''

    def __init__(self, channel_id, frequency, data_type):

        super(processed_data, self).__init__()

        #  set the frequency, channel_id, and data type
        self.channel_id = channel_id
        self.frequency = frequency
        self.data_type = data_type

        #  sample thickness is the vertical extent of the samples in meters
        #  it is calculated as thickness = sample interval(s) * sound speed(m/s) / 2
        #  you should not insert/append processed data arrays with different sample thicknesses
        self.sample_thickness = 0

        #  sample offset is the number of samples the first row of data are offset away from
        #  the transducer face.
        self.sample_offset = 0



    def replace(self, obj_to_insert, **kwargs):

        #  when inserting/replacing data in processed_data objects we have to make sure
        #  the data are the same type and are on the same vertical "grid". (The parent
        #  method will check if the frequencies are the same.)

        #  check that the data types are the same
        if (self.data_type != obj_to_insert.data_type):
            raise TypeError('You cannot insert an object that contains ' +
                    obj_to_insert.data_type + ' data into an object that ' +
                    'contains ' + self.data_type + ' data.')

        #  check that the data share the same vertical grid
        if (self.sample_thickness != obj_to_insert.sample_thickness):
            raise TypeError('You cannot insert an object into another object ' +
                    'that has a different sample thickness.')

        #  get the range/depth vectors
        if (hasattr(self, 'range')):
            this_vaxis = getattr(self, 'range')
        else:
            this_vaxis = getattr(self, 'depth')
        this_vlen = this_vaxis.shape[0]
        if (hasattr(obj_to_insert, 'range')):
            ins_vaxis = getattr(obj_to_insert, 'range')
        else:
            ins_vaxis = getattr(obj_to_insert, 'depth')
        ins_vlen = ins_vaxis.shape[0]

        #  determine the min and max extents of the two vertical axes
        min_vaxis = np.amin([np.amin(ins_vaxis),np.amin(this_vaxis)])
        max_vaxis = np.amax([np.amax(ins_vaxis),np.amax(this_vaxis)])



        #  determine the combined range

        #  check if they are the same length
        if (ins_vlen == this_vlen):
            #  they are the same length - check if same values
            if (not np.all(np.isclose(ins_vaxis - this_vaxis))):
                #  same length but different values - don't need to resize but interp inserted to this axis
                old_axis = ins_vaxis.copy()
                obj_to_interp.interpolate(old_axis, this_vaxis)
            else:

                pass


        elif (this_vlen > ins_vlen):
            #  this instance's vertical axis vector is longer - need to resize obj_to_insert

            #  first get a copy of the existing axis
            old_axis = ins_vaxis.copy()

            #  resize the object we're inserting
            obj_to_insert.resize(obj_to_insert.n_pings, this_vlen)

            #  and initerpolate the sample data in the object we're inserting
            obj_to_interp.interpolate(old_axis, this_vaxis)

        else:
            #  the object we're inserting has a longer vertical axis
            new_samps = ins_vlen

            #  first get a copy of this object's existing vertical axis
            old_axis = this_vaxis.copy()

            #  resize this object
            self.resize(self.n_pings, new_samps)

            #  and initerpolate the sample data in the object we're inserting
            self.interpolate(old_axis, ins_vaxis)

            #  TODO: how to handle inserting range into depth and oppostite???

            #  and set our new vertical axis
            if (hasattr(self, 'range')):
                setattr(self, 'range', ins_vaxis.copy())
            else:
                setattr(self, 'depth', ins_vaxis.copy())


        #  we are now coexisting in harmony - call parent's insert
        sample_data.insert(self, obj_to_insert, **kwargs)



    def insert(self, obj_to_insert, ping_number=None, ping_time=None,
               index_array=None):

        pass


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

        #  shift the sample data atrributes
        for attr_name in self._data_attributes:
            #  get the attribute
            attr = getattr(self, attr_name)
            #  check if it is a 2d array (which is a sample data array)
            if (attr.ndim == 2):
                #  this is a sample data array - shift the data and pad
                attr[:,n_samples:] = attr[:,0:old_samples]
                attr[:,0:n_samples] = np.nan



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
            new_samps = (np.ceil(vert_ext.astype('float32') / self.sample_thickness)).astype('uint')
            # calculate new sample dimension
            new_sample_dim = (self.n_samples+new_samps).astype('uint')
            #  and resize (n_samples will be updated in the _resize method)
            old_samps = self.n_samples
            self.resize(self.n_pings, new_sample_dim)

        # create the new vertical axis
        new_axis = (np.arange(self.n_samples) * self.sample_thickness) + np.min(vert_axis) + min_shift

        #  check if this is not a constant shift
        if (vert_ext != 0):
            #  not constant, work thru the 2d attributes and interpolate the sample data

            #  first convert to linear units if required
            if (self.data_type[0] == 'S'):
                is_log = True
                self.to_linear()
            else:
                is_log = False
            #  then pick out the sample data arrays and interpolate
            for attr_name in self._data_attributes:
                attr = getattr(self, attr_name)
                if (isinstance(attr, np.ndarray) and (attr.ndim == 2)):
                    for ping in range(self.n_pings):
                        attr[ping,:] = np.interp(new_axis, vert_axis + vert_shift[ping],
                                attr[ping,:old_samps], left=np.nan, right=np.nan)
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
        if (self.data_type == 'Sv'):
            self.Sv[:] = np.power(self.Sv / 20.0, 10.0)
            self.data_type = 'sv'
        elif (self.data_type == 'Sp'):
            self.Sp[:] = np.power(self.Sp / 20.0, 10.0)
            self.data_type = 'sp'


    def to_log(self):
        """
        to_log converts sample data from linear to log
        """
        if (self.data_type[0] == 'sv'):
            self.sv[:] = 20.0 * np.log10(self.sv)
            self.data_type = 'Sv'
        elif (self.data_type == 'sp'):
            self.sp[:] = 20.0 * np.log10(self.sp)
            self.data_type = 'Sp'


    def interpolate(self, old_vaxis, new_vaxis):

        #  first convert to linear units if required
        if (self.data_type[0] == 'S'):
            is_log = True
            self.to_linear()
        else:
            is_log = False
        #  then pick out the sample data arrays and interpolate
        for attr_name in self._data_attributes:
            attr = getattr(self, attr_name)
            if (isinstance(attr, np.ndarray) and (attr.ndim == 2)):
                for ping in range(self.n_pings):
                    attr[ping,:] = np.interp(new_vaxis, old_vaxis,
                            attr[ping,:old_vaxis.shape[0]], left=np.nan, right=np.nan)
        #  convert back to log units if required
        if (is_log):
            self.to_log()


    def __getitem__(self, key):

        #  create a new processed_data object to return
        p_data = processed_data(self.channel_id, self.frequency)

        #  copy common attributes
        p_data.sample_thickness = self.sample_thickness
        p_data.sample_offset = self.sample_offset

        #  and work thru the attributes, slicing them and adding to the new processed_data object
        for attr_name in self._data_attributes:
            attr = getattr(self, attr_name)
            if (isinstance(attr, np.ndarray) and (attr.ndim == 2)):
                p_data.add_attribute(attr_name, attr.__getitem__(key))
            else:
                p_data.add_attribute(attr_name, attr.__getitem__(key[0]))

        return p_data


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
