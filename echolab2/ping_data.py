# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS."  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""
.. module:: echolab2.ping_data

    :synopsis: Base class for containers use to store data collected
               from fisheries sonar systems.

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
import numpy as np
from scipy.interpolate import interp1d

class ping_data(object):
    """echolab2.ping_data is the base class for all classes that store time
    based data from fisheries sonar systems.

    This class is not intended to be instantiated by the user. It is a base
    class that defines the common data attributes and methods that the user
    facing classes share.

    Derived classes will add various attributes to this class that store
    either scalar values on a per-ping basis like sound velocity, transmit power
    transducer depth, etc. or attributes that store vector data such as
    sample power and sample angle data.

    One major assumption is that all data stored within an instance of our
    derived classes must exist on the same time grid. It is assumed that the
    index of a specific ping time should map to other attributes collected at
    that time. As a result, all attributes should share the same primary
    dimension.
    """

    def __init__(self):
        """Initializes ping_data class object.

        Creates and sets several internal properties used to store information
        about data and control operation of data processing of ping_data
        object instance. Code is heavily commented to facilitate use.
        """

        # Stores the total number of pings contained in our container.
        self.n_pings = -1

        # The number of samples in the 2d/3d sample arrays.
        self.n_samples = -1

        # A tuple describing the shape of the sample data array in the form
        # (n_pings, n_samples) or (n_pings, n_samples, s_sectors) for complex
        # data. If shape is None, the data arrays have not been allocated.
        self.shape = None

        # Allows the user to specify a dtype for the sample data.  This should
        # be set before any attributes are added.
        self.sample_dtype = 'float32'

        # Data_attributes is an internal list that contains the names of all
        # the class's "data attributes". The echolab2 package uses this
        # attribute list to generalize various functions that manipulate these
        # data.
        #
        # "data attributes" are attributes that store data by ping. They can
        # be 1d, such as ping_time, sample_interval, and transducer_depth. Or
        # they can be 2d, such as power, Sv, angle data, etc.  Echolab2
        # supports attributes that are 1d, 2d, and 3d numpy arrays.  When
        # subclassing, you must extend this list in your __init__ method to
        # contain all of the data attributes of that class that you want to
        # exist at instantiation (attributes can also be added later).

        # For the base class, we only define ping_time, which is the only
        # required attribute that all data objects must have.
        self._data_attributes = ['ping_time']

        # Attributes are added using the add_data_attribute method. You can add
        # them manually by appending the name of the new attribute to the
        # _data_attributes dictionary and then setting the attribute using
        # setattr().

        # Object attributes are similar to data attributes except they are not
        # linked to a data axis (time, sample_number, range/depth). Another
        # important difference is that they are not resized when the data arrays
        # are resized. Object attributes can be set to any value or object and
        # do not have to be numpy arrays.

        # Similar to the data attributes you can add and remove object attributes
        # using the add_object_attribute and remove_object_attribute methods.
        self._object_attributes = ['sample_dtype']

        # When writing methods that operate on these data, we will not assume
        # that they exist.  An attribute should only exist if it contains data.


    def add_data_attribute(self, name, data):
        """Adds a "data attribute" to the class.

        Data attributes are attributes that are linked to one of the data
        axes. Data attributes are resized when the data arrays are resized.

        This method first checks if the new attribute shares the same
        dimensions as existing attributes, and if so, appends the attribute
        name to the internal list of data attributes and then creates an
        attribute by that name and sets it to the provided reference.

        Args:
            name (str): The attribute name to be added to the class.
            data (array): A numpy array containing the data attributes.

        Raises:
            ValueError: The attribute has a different number of samples than
                the other attributes.
            TypeError: The attribute is not a numpy array.
            ValueError: The attribute has a different number of pings than
                the other attributes.
        """
        # Get the new data's dimensions.
        data_height = -1
        if isinstance(data, np.ndarray):
            if data.ndim == 1:
                data_width = data.shape[0]
            if data.ndim > 1:
                data_width = data.shape[0]
                data_height = data.shape[1]
                # Check if n_samples has been set yet.  If not, set it.
                # Otherwise, check that the dimensions match.
                if self.n_samples < 0:
                    self.n_samples = data_height
                elif self.n_samples != data_height:
                    raise ValueError('Cannot add attribute. New attribute has ' +
                        'a different number of samples than the other attributes.')
            if data.ndim == 3:
                # Add or update ourself.
                setattr(self, 'n_sectors', data.shape[2])
                self._object_attributes += ['n_sectors']
        else:
            # We only allow numpy arrays as data attributes.
            raise TypeError('Invalid data attribute type. Data attributes must ' +
                'be numpy arrays.')

        # Check if n_pings has been set yet.  If not, set it.  Otherwise,
        # check that the dimensions match.  When checking if dimensions
        # match, we allow a match on the number of pings OR the number of
        # samples since a 1d data attribute can be on either axis.
        if self.n_pings < 0:
            self.n_pings = data_width
        elif self.n_pings != data_width and self.n_samples != data_width:
            raise ValueError('Cannot add attribute. The new attribute has '
                    'a different number of pings or samples than the other attributes.')

        # Add the name to our list of attributes if it doesn't already exist.
        if name not in self._data_attributes:
            self._data_attributes.append(name)

        # Add or update ourself.
        setattr(self, name, data)

        #  update the shape attribute
        self.shape = self._shape()


    def add_object_attribute(self, name, data):
        """Adds a "object attribute" to the class.

        Object attributes are attributes that are not linked to a data axis.
        Object attributes are primarily used by the processed_data class to
        describe general attributes about the object or data like 'data_type'
        or 'is_log'. Object attributes can be any data type and are not
        resized or altered in any way when the data arrays are resized.

        Since the data is not linked to an axis there is no checking
        of dimensions before adding.

        Args:
            name (str): The attribute name to be added to the class.
            data (object): An python object/value

        """

        # Add the name to our list of attributes if it doesn't already exist.
        if name not in self._object_attributes:
            self._data_attributes.append(name)

        # Add or update ourself.
        setattr(self, name, data)


    def remove_object_attribute(self, name):
        """Removes a object attribute from the object.

        Args:
            name (str): The attribute name to be removed from the class.
        """
        #  we remove data and object attributes the same way
        self.remove_data_attribute(name)


    def remove_data_attribute(self, name):
        """Removes a data attribute from the object.

        Args:
            name (str): The attribute name to be removed from the class.
        """

        # Try to remove the attribute given the name.  Silently fail if the
        # name is not in our list.
        try:
            self._data_attributes.remove(name)
            delattr(self, name)
        except:
            pass


    def replace(self, obj_to_insert, ping_number=None, ping_time=None,
                index_array=None, _ignore_vertical_axes=False, force=False):
        """Replaces the data in this object with the data provided in the
        object to "insert".

        This method inserts data without shifting the existing data, resulting
        in the existing data being overwritten.  You must specify a ping
        number, ping time or provide an index array.  The number of pings
        replaced will be equal to the number of pings in the object you are
        adding.

        Args:
            obj_to_insert (ping_data): An instance of ping_data containing the
                replacement data to insert.
            ping_number (int): The ping number specifying the first ping to
                replace.
            ping_time (datetime): The ping time specifying the first ping to
                replace.
            index_array (array): A numpy array containing the indices of the
                pings you want to replace. Unlike when using a ping number or
                ping time, the pings do not have to be consecutive. When this
                keyword is present, the ping_number and ping_time keywords
                are ignored.
            _ignore_vertical_axes (bool): Controls whether to ignore vertical
                axes, range or depth, when resampling.

        Raises:
            ValueError: ping_number, ping_time or index array not provided.
            TypeError: The object provided isn't an instance of the ping_data
                class.
            TypeError: The frequency of the replacement data does not match
                the frequency of the data to be replaced.
            TypeError: The index array is not a numpy array.
            IndexError: The length of the index_array does not match the
                number of pings in the object providing the replacement data.
        """

        # Check that we have been given an insertion point or index array.
        if ping_number is None and ping_time is None and index_array is None:
            raise ValueError('Either ping_number or ping_time needs to be ' +
                             'defined or an index array needs to be provided ' +
                             'to specify a replacement point.')

        # Make sure that obj_to_insert class matches "this" class.
        if not isinstance(self, obj_to_insert.__class__):
            raise TypeError('The object provided as a source of replacement ' +
                            'pings must be an instance of ' +
                            str(self.__class__))

        # Make sure the data types are the same
        if self.data_type != obj_to_insert.data_type and not force:
            raise TypeError('The object you are inserting  does not have the same data ' +
                    'type as this object. This data type: ' + self.data_type +
                    ' object to insert data type: ' + obj_to_insert.data_type)

        #  if complex, make sure the number of sectors are the same
        if self.data_type == 'complex' and not force:
            if self.n_complex != obj_to_insert.n_complex:
                raise TypeError('The object you are inserting  does not have the same ' +
                    'number of complex samples as this object. This n_complex: ' + self.n_complex +
                    ' object to insert n_complex: ' + obj_to_insert.n_complex)

        # Make sure that the frequencies match.  Don't allow replacing pings
        # with different frequencies.
        if not force:
            freq_match = False
            if isinstance(self.frequency, np.float32):
                freq_match = self.frequency == obj_to_insert.frequency
            else:
                freq_match = self.frequency[0] == obj_to_insert.frequency[0]
            if not freq_match:
                raise TypeError('The frequency of the data you are providing as a '
                                + 'replacement does not match the frequency of ' +
                                'this object. The frequencies must match.')

        # Get information about the shape of the data we're working with.
        my_pings = self.n_pings
        new_pings = obj_to_insert.n_pings
        my_samples = self.n_samples
        new_samples = obj_to_insert.n_samples

        # Determine the index of the replacement point or indices of the
        # pings we're inserting.
        if index_array is None:
            # Determine the index of the replacement point.
            replace_index = self.get_indices(start_time=ping_time,
                    end_time=ping_time, start_ping=ping_number,
                    end_ping=ping_number)[0]

            # Create an index array.
            replace_index = np.arange(new_pings) + replace_index

            # Clamp the index to the length of our existing data.
            replace_index = replace_index[replace_index < my_pings]

        else:
            # An explicit array is provided.  These will be a vector of
            # locations to replace.
            replace_index = index_array

            # Make sure the index array is a numpy array.
            if not isinstance(replace_index, np.ndarray):
                raise TypeError('index_array must be a numpy.ndarray.')

            # If we replace the index with a user provided index, make sure the
            # dimensions of the index and the object to insert match.
            if replace_index.shape[0] != new_pings:
                raise IndexError('The length of the index_array does not '
                        'match the number of pings in the object with ' +
                        'the replacement data.  These dimensions must match.')

        # Check if we need to vertically resize one of the arrays.  If so, we
        # resize the smaller array to the size of the larger array.  It will
        # automatically be padded with NaNs.
        if my_samples < new_samples:
            # Resize our data arrays.  Check if we have a limit on the max
            # number of samples.
            if hasattr(self, 'max_sample_number') and self.max_sample_number:
                # We have the attribute and a value is set.  Check if the new
                # array exceeds our max_sample_count.
                if new_samples > self.max_sample_number:
                    # We have to change our new_samples.
                    new_samples = self.max_sample_number
                    # Vertically trim the array we're inserting.
                    obj_to_insert.resize(new_pings, new_samples)
            # Because we're not inserting, we can set the new vertical sample
            # size here.
            self.resize(my_pings, new_samples)
        elif my_samples > new_samples:
            # Resize the object we're inserting.
            obj_to_insert.resize(new_pings, my_samples)

        # Work through our data properties inserting the data from
        # obj_to_insert.
        for attribute in self._data_attributes:

            # Check if we have data for this attribute.
            if not hasattr(self, attribute):
                # data_obj does not have this attribute, move along.
                continue

            # Get a reference to our data object's attribute.
            data = getattr(self, attribute)

            # Check if we're ignoring vertical axes such as range or depth.
            # We do this when operating on processed data objects since the
            # assumption with them is that 1d arrays have the dimension equal
            # to the number of pings (horizontal axis).
            if _ignore_vertical_axes and data.shape[0] == my_samples:
                continue

            # Check if the obj_to_insert shares this attribute.
            if hasattr(obj_to_insert, attribute):
                # Get a reference to our obj_to_insert's attribute.
                data_to_insert = getattr(obj_to_insert, attribute)

                # We have to handle the 2d and 1d differently.
                if data.ndim == 1:
                    # Concatenate the 1d data.  Replace existing pings with
                    # this data.
                    data[replace_index] = data_to_insert[:]
                elif data.ndim == 2:
                    # Insert the new data.
                    data[replace_index, :] = data_to_insert[:,:]
                elif data.ndim == 3:
                    # Insert the new data.
                    data[replace_index, :, :] = data_to_insert[:,:,:]

        # Update our global properties.
        if hasattr(obj_to_insert, 'channel_id'):
            if obj_to_insert.channel_id not in self.channel_id:
                self.channel_id += obj_to_insert.channel_id


    def delete(self, start_ping=None, end_ping=None, start_time=None,
               end_time=None, remove=True, index_array=None):
        """Deletes data from an echolab2 data object.

        This method deletes data by ping over the range defined by the start
        and end ping times. If remove is True, the data arrays are shrunk.
        If False, the arrays stay the same size and the data values are set
        to NaNs (or an appropriate value based on type).

        Args:
            start_ping (int): The starting ping of the range of pings to delete.
            end_ping (int): The ending ping of the range of pings to delete.
            start_time (datetime64): The starting time of the range of pings to
                delete.
            end_time (datetime64): The ending time of the range of pings to
                delete.

                You should set only one start and end point.

            remove (bool): Set to True to remove the specified pings and
                shrink the data arrays. When set to False, data in the
                deleted pings are set to Nan (or appropriate value for the
                data type).
            index_array (array): A numpy array containing the indices of the
                pings you want to delete. Unlike when using starts/ends to
                define the ping range to delete, the pings do not have to be
                consecutive. When this keyword is present, the start/end
                keywords are ignored.
        """
        # Determine the indices of the pings we're deleting.
        if index_array is None:
            # We haven't been provided an explicit array, so create one based
            # on provided ranges.
            del_idx = self.get_indices(start_time=start_time, end_time=end_time,
                    start_ping=start_ping, end_ping=end_ping)
        else:
            # Explicit array provided.
            del_idx = index_array

        # Determine the indices of the pings we're keeping.
        keep_idx = np.delete(np.arange(self.ping_time.shape[0]), del_idx)

        # Determine the number of pings we're keeping.
        new_n_pings = keep_idx.shape[0]

        # Work through the attributes to delete the data.  If we're removing
        # the pings, we first copy the data we're keeping to a contiguous
        # block before we resize all of the arrays (which will shrink them).
        # If we're not removing the pings, we simply set the values of the
        # various attributes we're deleting to NaNs.
        for attr_name in self._data_attributes:
            attr = getattr(self, attr_name)
            if isinstance(attr, np.ndarray) and attr.ndim > 1:
                if attr.ndim == 2:
                    # 2d array
                    if remove:
                        attr[0:new_n_pings, :] = attr[keep_idx, :]
                    else:
                        attr[del_idx, :] = np.nan
                elif attr.ndim == 3:
                    # 3d array
                    if remove:
                        attr[0:new_n_pings, :, :] = attr[keep_idx, :, :]
                    else:
                        attr[del_idx, :, :] = np.nan
            else:
                if remove:
                    try:
                        # Copy the data we're keeping into a contiguous block.
                        attr[0:new_n_pings] = attr[keep_idx]
                    except:
                        # Range/Depth will fail and that's OK
                        pass
                else:
                    # Set the data to NaN or appropriate value.
                    if np.issubdtype(attr.dtype, np.integer):
                        # Set all other integers to zero
                        attr[del_idx] = 0
                    else:
                        # This is a float like object so set to NaN or NaT
                        attr[del_idx] = np.nan

        # If we're removing the pings, shrink the arrays.
        if remove:
            self.resize(new_n_pings, self.n_samples)
            self.n_pings = new_n_pings


    def append(self, obj_to_append, force=False):
        """Appends another echolab2 data object to this one.

        The objects must be instances of the same class and share the same
        frequency to append one to the other.
        """

        # Simply inserts a data object at the end of our internal array.
        self.insert(obj_to_append, ping_number=self.n_pings, force=False)


    def insert(self, obj_to_insert, ping_number=None, ping_time=None,
               insert_after=True, index_array=None, force=False):
        """Inserts data from the provided echolab2 data object into
        this object.

        The insertion point is specified by ping number or time (you must
        specify a ping number or ping time). Existing data from the insertion
        point onward will be shifted after the inserted data.  After
        inserting data, the ping_number property is updated and the ping
        numbers will be re-numbered accordingly.

        Args:
            ping_number (int): The ping number specifying the insertion point
            ping_time (datetime): The ping time specifying the insertion point
            insert_after (bool): Set to True to insert *after* the specified
                ping time or ping number. Set to False to insert *at* the
                specified time or ping number.
            index_array (array): A numpy array containing the indices of the
                pings you want to insert. Unlike when using a ping number or
                ping time, the pings do not have to be consecutive. When this
                keyword is present, the ping_number, ping_time and
                insert_after keywords are ignored.
            force (bool): Set to true to disable all checks and force the
                insert even if the frequency, channel ID, etc are different.

        Raises:
            ValueError: Insertion point not specified.
            TypeError: The object is not an instance of ping_data class.
            TypeError: The frequency of the object to be inserted
                doesn't match the frequency of this object.
            TypeError: Index array isn't a numpy array.
            IndexError: The length of the index array does not match the
                number of pings in the object to be inserted.
        """

        # Check that we have been given an insertion point or index array.
        if ping_number is None and ping_time is None and index_array is None:
            raise ValueError('Either ping_number or ping_time needs to be ' +
                             'defined or an index array needs to be provided ' +
                             'to specify an insertion point.')

        # Make sure that obj_to_insert class matches "this" class.
        if not isinstance(self, obj_to_insert.__class__):
            raise TypeError('The object you are inserting/appending must ' +
                            'be an instance of ' + str(self.__class__))

        # Make sure the two objects contain the same data type
        if self.data_type != obj_to_insert.data_type:
            raise TypeError('The object you are inserting/appending contains a different ' +
                            'data type than this object. You cannot insert objects containing ' +
                            'different data types.')

        # Make sure that the frequencies match.  This isn't perfect and there are
        # a lot of ways this can go bad. It is up to the user to ensure they insert
        # responsibly. We allow NaNs because we allow empty data to be inserted.
        if not force:
            freq_match = False
            # Need to handle FM and reduced data differently
            if self.data_type == 'complex-FM':
                if isinstance(self.frequency_start, np.ndarray):
                    # We get lazy with vectors of frequency since there isn't a simple solution.
                    # We will just check the first values.
                    if np.isnan(obj_to_insert.frequency_start[0]):
                        freq_match = True
                    else:
                        freq_match = self.frequency_start[0] == obj_to_insert.frequency_start[0]
                        freq_match &= self.frequency_end[0] == obj_to_insert.frequency_end[0]
                else:
                    # we must have been passed a single value
                    if obj_to_insert.frequency_start == np.nan or obj_to_insert.frequency_start == 0:
                        freq_match = True
                    else:
                        freq_match = self.frequency_start == obj_to_insert.frequency_start
                        freq_match &= self.frequency_end == obj_to_insert.frequency_end
            else:
                if isinstance(self.frequency, np.ndarray):
                    # Same deal here. We're lazy. Just check the first values
                    if np.isnan(obj_to_insert.frequency[0]):
                        freq_match = True
                    else:
                        freq_match = self.frequency[0] == obj_to_insert.frequency[0]
                else:
                    # we must have been passed a single value
                    if obj_to_insert.frequency == np.nan or obj_to_insert.frequency == 0:
                        freq_match = True
                    else:
                        freq_match = self.frequency == obj_to_insert.frequency

            if not freq_match:
                raise TypeError('The frequency of the object you are inserting' +
                                '/appending does not match the frequency of this ' +
                                'object. Frequencies must match to append or ' +
                                'insert.')

        # Get some info about the shape of the data we're working with.
        my_pings = self.n_pings
        new_pings = obj_to_insert.n_pings
        my_samples = self.n_samples
        new_samples = obj_to_insert.n_samples

        # Determine the index of the insertion point or indices of the pings
        # we're inserting.
        if index_array is None:
            # Determine the index of the insertion point.
            insert_index = self.get_indices(start_time=ping_time,
                                            end_time=ping_time,
                                            start_ping=ping_number,
                                            end_ping=ping_number)[0]

            # Check if we're inserting before or after the provided insert
            # point and adjust as necessary.
            if insert_after:
                # We're inserting *after*.
                insert_index += 1

            # Create an index array.
            insert_index = np.arange(new_pings) + insert_index

            # Generate the index used to move the existing pings.
            move_index = np.arange(my_pings)
            idx = move_index >= insert_index[0]
            move_index[idx] = move_index[idx] + new_pings

        else:
            # Explicit array provided.  These will be a vector of locations
            # to insert.
            insert_index = index_array

            # Make sure the index array is a numpy array.
            if (not isinstance(insert_index, np.ndarray)):
                raise TypeError('index_array must be a numpy.ndarray.')

            # If we are inserting with a user provided index, make sure the
            # dimensions of the index and the object to insert match.
            if insert_index.shape[0] != new_pings:
                raise IndexError('The length of the index_array does not ' +
                                 'match the number of pings in the object' +
                                 ' you are inserting.')

            # Generate the index used to move the existing pings.
            move_index = np.arange(my_pings)
            for i in insert_index:
                idx = move_index >= i
                move_index[idx] = move_index[idx] + 1

        # Check if we need to vertically resize one of the arrays.  We
        # resize the smaller array to the size of the larger array.  It will
        # automatically be padded with NaNs.
        if my_samples < new_samples:
            # Resize our data arrays and check if we have a limit on the
            # max number of samples.
            if hasattr(self, 'max_sample_number') and self.max_sample_number:
                # We have the attribute and a value is set.  Check if the
                # new array exceeds our max_sample_count.
                if new_samples > self.max_sample_number:
                    # We have to change our new_samples.
                    new_samples = self.max_sample_number
                    # Vertically trim the array we're inserting.
                    obj_to_insert.resize(new_pings, new_samples)
            # Set the new vertical sample size.
            my_samples = new_samples
        elif my_samples > new_samples:
            # Resize the object we're inserting.
            obj_to_insert.resize(new_pings, my_samples)

        # Update the number of pings in the object we're inserting into
        # and then resize it.
        my_pings = my_pings + new_pings
        self.resize(my_pings, my_samples)

        # Work through our data properties, inserting the data from
        # obj_to_insert.
        for attribute in self._data_attributes:

            # Check if we have data for this attribute.
            if not hasattr(self, attribute):
                # data_obj does not have this attribute, move along.
                continue

            # Get a reference to our data_obj's attribute.
            data = getattr(self, attribute)

            # Generate the move index.
            move_idx = np.arange(move_index.shape[0])

            # Check if the obj_to_insert shares this attribute.
            if hasattr(obj_to_insert, attribute):
                # Get a reference to our obj_to_insert's attribute.
                data_to_insert = getattr(obj_to_insert, attribute)

                # We have to handle the 2d and 1d differently.
                if data.ndim == 1 and data.shape[0] != my_samples:
                    # Skip vertical axis attributes, but move the other 1d data
                    # move right to left to avoid overwriting data before
                    # moving.
                    data[move_index[::-1],] = data[move_idx[::-1]]
                    # Insert the new data.
                    data[insert_index] = data_to_insert[:]
                elif data.ndim == 2:
                    # Move the existing data from right to left to avoid
                    # overwriting data yet to be moved.
                    data[move_index[::-1], :] = data[move_idx[::-1], :]
                    # Insert the new data.
                    data[insert_index, :] = data_to_insert[:, :]
                elif data.ndim == 3:
                    # Move 3d data
                    data[move_index[::-1], :, :] = data[move_idx[::-1], :, :]
                    # Insert the new data.
                    data[insert_index, :, :] = data_to_insert[:, :, :]

        # Now update our global properties.
        if hasattr(obj_to_insert, 'channel_id'):
            if obj_to_insert.channel_id not in self.channel_id:
                self.channel_id += " :: " + obj_to_insert.channel_id

        # Update the size/shape attributes.
        self.n_pings = self.ping_time.shape[0]
        self.n_samples = my_samples
        self.shape = self._shape()


    def match_pings(self, other_data, match_to='cs'):
        """Matches the ping times in this object to the ping times in the object
        provided. It does this by matching times, inserting and/or deleting
        pings as needed. It does not interpolate. Ping times in the other object
        that aren't in this object are inserted. Ping times in this object that
        aren't in the other object are deleted. If the time axes do not intersect
        at all, all of the data in this object will be deleted and replaced with
        empty pings for the ping times in the other object.


        Args:
            other_data (ping_data): A ping_data type object that this object
            will be matched to.

            match_to (str): Set to a string defining the precision of the match.

                cs : Match to a 100th of a second or
                ds : Match to a 10th of a second
                s  : Match to the second

        Returns:
            A dictionary with the keys 'inserted' and 'removed' containing the
            indices of the pings inserted and removed.

        """
        # Create a dict to store info on which pings were inserted/removed
        results = {'inserted':[], 'removed':[]}

        if match_to == 'cs':
            round_amt = np.uint64(5)
            truncate_to = -2
        elif match_to == 'ds':
            round_amt = np.uint64(50)
            truncate_to = -3
        elif match_to == 's':
            round_amt = np.uint64(500)
            truncate_to = -4

        # don't allow a recursive match
        if other_data is not self:

            # round our times to allow for a loose match window
            this_time = np.around(self.ping_time.astype('uint64') + round_amt,
                    truncate_to)
            other_time = np.around(other_data.ping_time.astype('uint64') + round_amt,
                    truncate_to)

            #  remove any "extra" pings this object may have
            idx_out = np.isin(this_time, other_time, invert=True)
            idx_out = np.nonzero(idx_out)[0]
            if idx_out.size > 0:
                # We have some extra pings, delete them
                results['removed'] = idx_out
                self.delete(index_array=idx_out)

            # Insert any pings that this object is missing
            idx_in = np.isin(other_time, this_time, invert=True)
            idx_in = np.nonzero(idx_in)[0]
            if idx_in.size > 0:
                # There were missing pings, we'll insert "empty" pings in their place
                results['inserted'] = idx_in
                self.insert(self.empty_like(len(idx_in)),
                        index_array=idx_in, force=True)

                # Lastly, update the times
                self.ping_time[idx_in] = other_data.ping_time[idx_in]

        return results


    def trim(self, n_pings=None):
        """Trims pings from an echolab2 data object to a given length.

        This method deletes pings from a data object to a length defined by
        n_pings.

        Args:
            n_pings (int): Number of pings (horizontal axis).
        """

        if not n_pings:
            n_pings = self.n_pings

        # Resize keeping the sample number the same.
        self.resize(n_pings, self.n_samples)


    def roll(self, roll_pings):
        """Rolls our data array elements along the ping axis.

        Elements that roll beyond the last position are re-introduced at the
        first position.

        Args:
            roll_pings ():
        """

        #TODO: Test these inline rolling functions
        #      Need to profile this code to see which methods are faster.
        #      Currently all rolling is implemented using np.roll which makes
        #      a copy of the data.
        #TODO: verify rolling direction
        #      Verify the correct rolling direction for both the np.roll
        #      calls and the 2 inline functions. I *think* the calls to
        #      np.roll are correct and the inline functions roll the wrong way.

        def roll_1d(data, n):
            # Rolls a 1d mostly in place.  Based on code found here:
            #    https://stackoverflow.com/questions/35916201/alternative-to
            #    -numpy-roll-without-copying-array
            # THESE HAVE NOT BEEN TESTED
            temp_view = data[:-n]
            temp_copy = data[-n]
            data[n:] = temp_view
            data[0] = temp_copy

        def roll_2d(data, n):
            # Rolls a 2d mostly in place.
            temp_view = data[:-n,:]
            temp_copy = data[-n,:]
            data[n:, :] = temp_view
            data[0, :] = temp_copy

        # Work through our list of attributes.
        for attr_name in self._data_attributes:

            # Get a reference to this attribute.
            attr = getattr(self, attr_name)

            # Resize the arrays using a technique dependent on the array
            # dimension.
            if attr.ndim == 1:
                attr = np.roll(attr, roll_pings)
                # attr[:] = roll_1d(attr, roll_pings)
            elif attr.ndim == 2:
                attr = np.roll(attr, roll_pings, axis=0)
                # attr[:] = roll_2d(attr, roll_pings)

            # Update the attribute.
            setattr(self, attr_name, attr)


    def resize(self, new_ping_dim, new_sample_dim):
        """Iterates through the provided list of attributes and resizes them.

        The size of the attributes in the instance of the provided object
        is resized given the new array dimensions.

        Args:
            new_ping_dim (int): Ping dimension gives the width of the array (
                horizontal axis).
            new_sample_dim (int): Sample dimension gives the height of the
                array (vertical axis).
        """

        def _resize2d(data, ping_dim, sample_dim):
            """
            _resize2d returns a new array of the specified dimensions with the
            data from the provided array copied into it. This function is
            used when we need to resize 2d arrays along the minor axis as
            ndarray.resize and numpy.resize don't maintain the order of the
            data in these cases.
            """
            # Create a new array.
            new_array = np.empty((ping_dim, sample_dim), dtype=self.sample_dtype)

            if data.shape[0] > ping_dim:
                n_pings = ping_dim
            else:
                n_pings = data.shape[0]
                new_array.fill(np.nan)
            if data.shape[1] > sample_dim:
                n_samps = sample_dim
            else:
                n_samps = data.shape[1]
                new_array.fill(np.nan)

            # Copy the data into our new array and return it.
            new_array[0:n_pings, 0:n_samps] = data[0:n_pings, 0:n_samps]
            return new_array


        def _resize3d(data, ping_dim, sample_dim, sector_dim):
            """
            _resize3d returns a new array of the specified dimensions with the
            data from the provided array copied into it. Same reasoning as above.
            """
            # Create a new array.
            new_array = np.empty((ping_dim, sample_dim, sector_dim), dtype=self.sample_dtype)
            # Fill it with NaNs.
            new_array.fill(np.nan)
            # Copy the data into our new array and return it.
            new_array[0:data.shape[0], 0:data.shape[1],:] = data
            return new_array

        # Store the old sizes.
        old_sample_dim = self.n_samples
        old_ping_dim = self.ping_time.shape[0]

        # Ensure our values are integers.  Some platforms/versions don't
        # automatically coerce floats to integers when used as integer
        # arguments.
        new_ping_dim = int(new_ping_dim)
        new_sample_dim = int(new_sample_dim)

        # Work through our list of attributes.
        for attr_name in self._data_attributes:

            # Get a reference to this attribute.
            attr = getattr(self, attr_name)

            # Resize the arrays using a technique dependent on the array
            # dimension.
            if attr.ndim == 1:
                # 1d arrays can be on the ping axes or sample axes and have
                # to be handled differently.
                if attr.shape[0] == old_sample_dim != new_sample_dim:
                    # Resize this sample axes attribute.
                    attr = np.resize(attr,(new_sample_dim))
                elif attr.shape[0] == old_ping_dim != new_ping_dim:
                    # Resize this ping axes attribute.
                    attr = np.resize(attr,(new_ping_dim))
            elif attr.ndim == 2:
                # Resize this 2d sample data array.
                if new_sample_dim == old_sample_dim:
                    # If the minor axes isn't changing, we can use
                    # np.resize() function.
                    attr = np.resize(attr,(new_ping_dim, new_sample_dim))
                else:
                    # If the minor axes is changing, we need to use our
                    # resize2d function.
                    attr = _resize2d(attr, new_ping_dim, new_sample_dim)
            elif attr.ndim == 3:
                # Resize this 3d sample data array.
                if new_sample_dim == old_sample_dim:
                    # If the minor axes isn't changing, we can use
                    # np.resize() function.
                    attr = np.resize(attr,(new_ping_dim, new_sample_dim, self.n_complex))
                else:
                    # If the minor axes is changing, we need to use our
                    # resize2d function.
                    attr = _resize3d(attr, new_ping_dim, new_sample_dim, self.n_complex)

            #  Update the attribute.
            setattr(self, attr_name, attr)

        # Set the new shape attributes
        self.n_samples = new_sample_dim
        self.shape = self._shape()

        # We cannot update the n_pings attribute here since raw_data uses
        # this attribute to store the number of pings read, *not* the total
        # number of pings in the array as the processed_data class uses it.
        # Instead, we have to set it either in the child class, or when context
        # permits, in other methods of this class.


    def get_indices(self, start_ping=None, end_ping=None, start_time=None,
                    end_time=None, time_order=True, **_):
        """Returns a index array containing where the indices in the
        range defined by the times and/or ping numbers provided are True.

        By default, the indices are returned in time order. If time_order is set
        to False, the data will be returned in the order they occur in the data
        arrays.

        Note that pings with "empty" times (ping time == NaT) will be sorted
        to the beginning of the index array for numpy versions < 1.18 and the
        END for versions >= 1.18

        Args:
            start_ping (int): The starting ping of the range of pings specified.
            end_ping (int): The ending ping of the range of pings specified.
            start_time (datetime64): The starting time of the range of pings
                specified.
            end_time (datetime64): The ending time of the range of pings
                specified.
            time_order (bool): Controls the order the indices will return.  If
                set to True, the indices will be in time order.  If False,
                the data will return in the order they occur in the data arrays.

        Returns:
            The indices that are included in the specified range.
        """

        # Generate the ping number vector.  We start counting pings at 1.
        ping_number = np.arange(self.n_pings) + 1

        # If starts and/or ends are omitted, assume first and last respectively.
        if start_ping == start_time is None:
            start_ping = ping_number[0]
        if end_ping == end_time is None:
            end_ping = ping_number[-1]

        # Get the primary index.
        if time_order:
            # Return indices in time order.  Note that empty ping times will be
            # sorted to the front for numpy versions < 1.18 and at the end for
            # versions >= 1.18
            primary_index = self.ping_time.argsort(kind='stable')
        else:
            # Return indices in ping order.
            primary_index = ping_number - 1

        # Generate a boolean mask of the values to return.
        if start_time:
            mask = self.ping_time[primary_index] >= start_time
        elif start_ping >= 1:
            mask = ping_number[primary_index] >= start_ping
        if end_time:
            mask = np.logical_and(mask, self.ping_time[primary_index] <= end_time)
        elif end_ping >= 2:
            mask = np.logical_and(mask, ping_number[primary_index] <= end_ping)

        # Return the indices that are included in the specified range.
        return primary_index[mask]


    def _vertical_resample(self, data, sample_intervals,
                           unique_sample_intervals, resample_interval,
                           sample_offsets, min_sample_offset, is_power=True):
        """Internal method that vertically resamples sample data given a target
        sample interval.

        If the resampling factor is a whole number, samples will be replicated
        when expanding vertically and averaged when reduced. If the resampling
        factor is a fractional number, the samples will be interpolated.
        Interpolation will result in aliasing. Aliasing while upsampling is
        relatively minor, but it can be significant when downsampling. Care
        should be taken when downsampling. The default behavior is to upsample.

        This method also shifts samples vertically based on their sample
        offset so they are positioned correctly relative to each other. The
        first sample in the resulting array will have an offset that is the
        minimum of all offsets in the data.

        Args:
            data:
            sample_intervals:
            unique_sample_intervals:
            resample_interval:
            sample_offsets:
            min_sample_offset:
            is_power:

        Returns:
            The resampled data and the sampling interval used.
        """

        def isclose(a, b, rel_tol=1e-9, abs_tol=0.0):
            return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

        # Determine the number of pings in the new array.
        n_pings = data.shape[0]

        # Check if we need to substitute our resample_interval value.
        if resample_interval == 0:
            # Resample to the shortest sample interval in our data.
            resample_interval = min(unique_sample_intervals)
        elif resample_interval >= 1:
            # Resample to the longest sample interval in our data.
            resample_interval = max(unique_sample_intervals)

        # Generate a vector of sample counts.  The generalized method works
        # with both raw_data and processed_data classes and finds the first
        # non-NaN value searching from the "bottom up".
        if data.ndim == 3:
            # just use the 1st element for complex data types
            sample_counts = data.shape[1] - np.argmax(~np.isnan(np.fliplr(data[:,:,0])), axis=1)
        else:
            sample_counts = data.shape[1] - np.argmax(~np.isnan(np.fliplr(data)), axis=1)

        # Create a couple of dictionaries to store resampling parameters by
        # sample interval.  They will be used when we fill the output array
        # with the resampled data.
        resample_factor = {}
        pings_this_interval = {}
        sample_offsets_this_interval = {}

        # Determine the number of samples in the output array.  To do this,
        # we must loop through the sample intervals, determine the resampling
        # factor, then find the maximum sample count at that sample interval
        # (taking into account the sample's offset) and multiply by the
        # resampling factor to determine the max number of samples for that
        # sample interval.
        new_sample_dims = 0
        for sample_interval in unique_sample_intervals:
            # Set the resampling factor for pings with this sample interval
            resample_factor[sample_interval] = sample_interval / resample_interval

            # Determine the rows in this subset with this sample interval.
            pings_this_interval[sample_interval] = np.where(sample_intervals == sample_interval)[0]

            # Determine the net vertical shift for the samples with this sample interval.
            sample_offsets_this_interval[sample_interval] = \
                    sample_offsets[pings_this_interval[sample_interval]] - min_sample_offset

            # Also, determine the maximum number of samples for this sample interval.  This
            # has to be done on a row-by-row basis since sample number can change between
            # pings. We include the sample offset to ensure we have room to shift our
            # samples vertically by the offset.
            max_samples_this_sample_int = max(sample_counts[pings_this_interval[sample_interval]] +
                sample_offsets_this_interval[sample_interval])

            # Now compute the number of samples for this sample interval and
            # store the largest value over all of the intervals.
            max_dim_this_sample_int = int(round(max_samples_this_sample_int *
                    resample_factor[sample_interval]))
            if max_dim_this_sample_int > new_sample_dims:
                new_sample_dims = max_dim_this_sample_int

        # Now that we know the dimensions of the output array, create it and fill with NaNs.
        if data.ndim == 3:
            resampled_data = np.empty((n_pings, new_sample_dims, data.shape[2]), order='C')
        else:
            resampled_data = np.empty((n_pings, new_sample_dims),order='C')
        resampled_data.fill(np.nan)

        # Now fill the array with data. We loop through the sample intervals  and within an
        # interval, extract slices of data that share the same number of samples. We then
        # determine if we're expanding or shrinking the number of samples and if the resample
        # factor is a whole number or float.  If it is a whole number and we are expanding
        # we replicate existing sample data to fill out the expanded array. If reducing, we
        # take the mean of the samples. If the resample factor is not a whole number we interpolate.
        for sample_interval in unique_sample_intervals:
            # get an index of the pings with this sample interval
            pings = pings_this_interval[sample_interval]

            # Determine the unique sample_counts for this sample interval.
            unique_sample_counts = np.unique(sample_counts[pings])

            # check if the resample factor is an whole number. When it is a whole nummber, we
            # can reduce or expand the array, if it is a float we have to interpolate.
            if isclose(resample_factor[sample_interval], round(resample_factor[sample_interval])):
                # it is, we will replicate samples when expanding and take the mean when reducing
                use_interp = False
            else:
                # the resample factor is a float - we need to interpolate
                use_interp = True

            for count in unique_sample_counts:
                # get an index into the pings with this sample count
                p_n_samples = sample_counts[pings] == count

                # Combine the index array for this sample interval/sample count chunk of data.
                pings_this_interval_count = pings[p_n_samples]

                # Determine if we're reducing, expanding, or keeping the same number of samples.
                if resample_interval > sample_interval:
                    # We're reducing the number of samples.

                    # If we're resampling power, convert power to linear units.
                    if is_power:
                        this_data = 10.0 ** (data[pings_this_interval_count] / 10.0)
                    else:
                        this_data = data[pings_this_interval_count]

                    if use_interp:
                        # We can't reduce by averaging a whole number of samples so we have to interpolate.
                        xp = sample_interval * np.arange(count)
                        rsf = int(count * resample_factor[sample_interval])
                        yp = resample_interval * np.arange(rsf)
                        interp_f = interp1d(xp, this_data[:,0:count], kind='previous', axis=1,
                                bounds_error=False, fill_value=np.nan, assume_sorted=True)
                        this_data = interp_f(yp)
                    else:
                        # Reduce the number of samples by taking the mean.
                        n_mean = int(resample_factor[sample_interval])
                        this_data = np.mean(this_data.reshape(-1, n_mean), axis=1)

                    if is_power:
                        # Convert power back to log units.
                        this_data = 10.0 * np.log10(this_data)

                elif resample_interval < sample_interval:
                    # We're increasing the number of samples.

                    if use_interp:
                        # If we're resampling power, convert power to linear units.
                        if is_power:
                            this_data = 10.0 ** (data[pings_this_interval_count] / 10.0)
                        else:
                            this_data = data[pings_this_interval_count]

                        # We can't expand by replicating a whole number of samples so we have to interpolate.
                        xp = sample_interval * np.arange(count)
                        rsf = int(count * resample_factor[sample_interval])
                        yp = resample_interval * np.arange(rsf)
                        interp_f = interp1d(xp, this_data[:,0:count], kind='previous', axis=1,
                                bounds_error=False, fill_value=np.nan, assume_sorted=True)
                        this_data = interp_f(yp)

                        if is_power:
                            # Convert power back to log units.
                            this_data = 10.0 * np.log10(this_data)

                    else:
                        # Replicate the values to fill out the higher resolution array.
                        n_repeat = int(resample_factor[sample_interval])
                        this_data = data[pings_this_interval_count]
                        if data.ndim == 3:
                            this_data = np.repeat(this_data[:, 0:count,:], n_repeat, axis=1)
                        else:
                            this_data = np.repeat(this_data[:, 0:count], n_repeat, axis=1)

                else:
                    # The data exists on the resample_interval grid - no change
                    this_data = data[pings_this_interval_count, 0:count]

                # Assign new values to output array.  At the same time, we will shift the data by sample offset.
                unique_sample_offsets = np.unique(sample_offsets_this_interval[sample_interval]).astype('int')
                for offset in unique_sample_offsets:
                    if this_data.ndim == 3:
                        resampled_data[pings_this_interval_count, offset:offset + this_data.shape[1],:] = this_data
                    else:
                        resampled_data[pings_this_interval_count, offset:offset + this_data.shape[1]] = this_data

        # Return the resampled data and the sampling interval used.
        return resampled_data, resample_interval


    def _vertical_shift(self, data, sample_offsets, unique_sample_offsets,
                        min_sample_offset):
        """Adjusts the output array size and pads the top of the samples
        array to vertically shift the positions of the sample data in
        the output array.

        Pings with offsets greater than the minimum will be padded on the
        top, shifting them into their correct location relative to the other
        pings.  The result is an output array with samples that are properly
        aligned vertically relative to each other with a sample offset that is
        constant and equal to the minimum of the original sample offsets.

        This method is only called if our data has a constant sample interval,
        but varying sample offsets. If the data has multiple sample intervals
        the offset adjustment is done in vertical_resample.

        Args:
            data (array): A numpy array of data to be shifted.
            sample_offsets (array): A numpy array with the sample offset for
                each ping.
            unique_sample_offsets (list): The lis tof unique sample offset
                values.
            min_sample_offset (int):

        Returns:
            The shifted data array.
        """

        # Determine the new array size.
        new_sample_dims = (data.shape[1] + max(sample_offsets) -
                min_sample_offset)

        # Create the new array.
        shifted_data = np.empty((data.shape[0], new_sample_dims),
                dtype=self.sample_dtype, order='C')
        shifted_data.fill(np.nan)

        # Fill the array, looping over the different sample offsets.
        for offset in unique_sample_offsets:
            rows_this_offset = np.where(sample_offsets == offset)[0]
            start_index = offset - min_sample_offset
            end_index = start_index + data.shape[1]
            shifted_data[rows_this_offset, start_index:end_index] = \
                    data[rows_this_offset, 0:data.shape[1]]

        return shifted_data


    def _copy(self, obj):
        """Copies attributes.

        This is an internal helper method that is called by child "copy"
        methods to copy the data and object attributes.

        Args:
            obj (ping_data): The object to copy attributes to.

        Returns:
            The copy of the object.
        """

        # Copy the common attributes.
        obj.sample_dtype = self.sample_dtype
        obj.n_samples = self.n_samples
        obj.n_pings = self.n_pings
        obj.shape = self.shape
        obj._data_attributes = list(self._data_attributes)
        obj._object_attributes  = list(self._object_attributes)

        # Copy object attributes
        for attr_name in self._object_attributes:
            attr = getattr(self, attr_name)
            # check if this attribute is a numpy array
            if isinstance(attr, np.ndarray):
                # it is - use ndarray's copy method
                setattr(obj, attr_name, attr.copy())
            else:
                # it's not - use the copy module
                setattr(obj, attr_name, copy.deepcopy(attr))

        # Copy the data attributes
        for attr_name in obj._data_attributes:
            attr = getattr(self, attr_name)
            # data attributes are always numpy arrays so use ndarray's copy method
            setattr(obj, attr_name, attr.copy())

        # Return the copy.
        return obj


    def _shape(self):
        '''Internal method used to update the shape attribute
        '''
        shape = None
        if hasattr(self, 'power'):
            shape = self.power.shape
        elif hasattr(self, 'angles_alongship_e'):
            shape = self.angles_alongship_e.shape
        elif hasattr(self, 'complex'):
            shape = self.complex.shape
        elif hasattr(self, 'data'):
            shape = self.data.shape
        return shape


    def _like(self, obj, n_pings, value, empty_times=False, no_data=False):
        """Copies ping_data attributes and creates data arrays filled with the
        specified value.

        This is an internal helper method that is called by "empty_like" and
        "zeros_like" methods of child classes which copy the ping_data
        attributes into the provided ping_data based object as well as
        create "data" arrays that are filled with the specified value. All
        vertical axes will be copied without modification.

        If empty_times is False, the ping_time vector of this instance is copied
        to the new object. If it is True, the new ping_time vector is filled
        with NaT (not a time) values. If n_pings != self.n_pings THIS
        ARGUMENT IS IGNORED AND THE NEW PING VECTOR IS FILLED WITH NaT.

        The result should be a new object where horizontal axes (excepting
        ping_time) and sample data arrays are empty (NaN or NaT). The
        contents of the ping_time vector will depend on the state of the
        empty_times keyword. The new object's shape will be (n_pings,
        self.n_samples).

        Args:
            obj (ping_data): An empty object to copy attributes to.
            n_pings (int): Number of pings (horizontal axis)
            value (int,float): A scalar value to fill the array with.
            empty_times (bool): Controls whether ping_time data is copied
                over to the new object (TRUE) or if it will be filled with NaT
                values (FALSE).
            no_data (bool): Set to True to to set 2d and 3d data attributes
                to None, rather than creating numpy arrays. When False,
                numpy arrays are created. This allows you to avoid allocating
                the data arrays if you are planning on replacing them.
                This is primarily used internally. Default: False

        Returns:
            The object copy, obj.
        """
        # If n_pings is None, we create an empty array with the same number
        # of pings.
        if n_pings is None:
            n_pings = self.n_pings

        # Copy the common attributes.
        obj.sample_dtype = self.sample_dtype
        obj.n_samples = self.n_samples
        obj.n_pings = n_pings
        obj._data_attributes = list(self._data_attributes)
        obj._object_attributes  = list(self._object_attributes)

        # Copy object attributes - this is simple as there are no
        # size or type checks.
        for attr_name in self._object_attributes:
            attr = getattr(self, attr_name)
            # check if attribute is a numpy array
            if isinstance(attr, np.ndarray):
                # it is - use ndarray's copy method
                setattr(obj, attr_name, attr.copy())
            else:
                # it's not - use the copy module
                setattr(obj, attr_name, copy.deepcopy(attr))

        # Check if n_pings != self.n_pings.  If the new object's horizontal
        # axis is a different shape than this object's we can't copy
        # ping_time data since there isn't a direct mapping and we don't know
        # what the user wants here. This can/should be handled in the child
        # method if needed.
        if n_pings != self.n_pings:
            # We have to force an empty ping_time vector since the axes differ.
            empty_times = True

        # Create the dynamic attributes.
        for attr_name in self._data_attributes:

            # Get the attribute.
            attr = getattr(self, attr_name)

            if attr.shape[0] == self.n_samples:
                # Copy all vertical axes w/o changing them.
                data = attr.copy()
            else:
                # Create an array with the appropriate shape filled with the
                # specified value.
                if attr.ndim == 1:
                    # Create an array with the same shape filled with the
                    # specified value.
                    data = np.empty(n_pings, dtype=attr.dtype)

                    # Check if this is the ping_time attribute and if we
                    # should copy this instance's ping_time data or create an
                    # empty ping_time vector
                    if attr_name == 'ping_time':
                        if empty_times:
                            data[:] = np.datetime64('NaT')
                        else:
                            data[:] = attr.copy()
                    elif data.dtype == 'datetime64[ms]':
                        data[:] = np.datetime64('NaT')
                    elif np.issubdtype(data.dtype, np.integer):
                        data[:] = 0
                    else:
                        data[:] = value
                else:
                    # Check if we're supposed to create the sample data arrays
                    if no_data:
                        # No - we'll set them to None assuming the user will set them
                        data = None
                    else:
                        # Yes, create the data arrays
                        if attr.ndim == 2:
                            # Create the 2d array(s).
                            data = np.empty((n_pings, self.n_samples), dtype=attr.dtype)
                            data[:, :] = value
                        elif attr.ndim == 3:
                            #  must be a 3d attribute
                            data = np.empty((n_pings, self.n_samples, self.n_complex),
                                dtype=attr.dtype)
                            data[:, :, :] = value

            # Add the attribute to our empty object.  We can skip using
            # add_data_attribute here because we shouldn't need to check
            # dimensions and we've already handled the low level stuff like
            # copying the _data_attributes list, etc.
            setattr(obj, attr_name, data)

        return obj
