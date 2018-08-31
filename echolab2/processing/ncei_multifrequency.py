# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     National Centers for Environmental Information (NCEI)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS,#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""


| Developed by:  Chuck Anderson   <charles.anderson@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| National centers for Environmental Information (NCEI)
| Center for Coast Oceans and Geophysics (CCOG)
|
| Author:
|       Chuck Anderson  <charles.anderson@noaa.gov>
| Maintained by:
|       Chuck Anderson  <charles.anderson@noaa.gov>

"""



from ..ping_data import PingData
from numpy import zeros, int8


class MultifrequencyData(PingData):
    """
    MultifrequencyData is a class to create and contain NCEI style
    multi-frequency data
    """

    def __init__(self, data_objects, latitude, longitude, low_threshold,
                 high_threshold, values):
        """Initializes ProcessedData class object.

        Creates and sets several internal properties used to store information
        about data and control operation of processed data object instance.
        Code is heavily commented to facilitate use.
        """
        super(MultifrequencyData, self).__init__()

        # Set n_pings, n_samples, and ping times from 1st data object by
        # getting 1st key in data_objects dictionary
        first = list(data_objects.keys())[0]
        self.n_pings = data_objects[first].data.shape[0]
        self.n_samples = data_objects[first].data.shape[1]
        self.ping_time = data_objects[first].ping_time.copy()
        if hasattr(data_objects[first], 'depth'):
            self.add_attribute('depth', data_objects[first].depth.copy())
            self._data_attributes.append('depth')
        elif hasattr(data_objects[first], 'range'):
            self.add_attribute('range', data_objects[first].range.copy())
            self._data_attributes.append('range')

        # Create an empty Numpy array of proper size to hold integer values
        # from multifrequency analysis.
        data = zeros((self.n_pings, self.n_samples), dtype=int8, order='C')
        self.add_attribute('data', data)
        self._data_attributes.append('data')

        self.low_threhold = low_threshold
        self.high_threshold = high_threshold
        self.values = values

        # Create and populate list of longitude and latitude values from
        # first ProcessedData object in data_objects
        self.longitude = latitude
        self.latitude = longitude

        # Create attributes that are dictionaries containing references to
        # ProcessedData objects and Mask objects.
        self.masks = {}
        self.processed_data = {}

        self.get_multifrequency_data(data_objects, self.low_threhold,
                                     self.high_threshold, self.values)

    @staticmethod
    def make_masks(data_objects, low_threshold, high_threshold):
        masks = {}
        for frequency, data in data_objects.items():
            masks[frequency] = (data >= low_threshold) & (
                        data <= high_threshold)
        return masks

    def mask_data(self, data_objects, masks, values=None):
        processed_data = {}
        for frequency, data in data_objects.items():
            processed_data[frequency] = data.zeros_like()
            processed_data[frequency][masks[frequency]] = values[frequency]

        return processed_data

    def get_multifrequency_data(self, data_objects, low_threshold,
                                high_threshold, values):

        self.masks = self.make_masks(data_objects, low_threshold,
                                     high_threshold)
        self.processed_data = self.mask_data(data_objects, self.masks, values)

        # Add each channels integer values to create final data array
        for numbers in self.processed_data.values():
            self.data += numbers.data.astype(int8)
        self.data[self.data == 0] = 2

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

            # If the minor axis is changing, we have to either concatenate or
            # copy into a new resized array.  We take the second approach
            # for now, as there shouldn't be a performance differences between
            # the two approaches.

            # Create a new array.
            new_array = np.empty((ping_dim, sample_dim))
            # Fill it with NaNs.
            new_array.fill(np.nan)
            # Copy the data into our new array and return it.
            new_array[0:data.shape[0], 0:data.shape[1]] = data
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

            #  Update the attribute.
            setattr(self, attr_name, attr)

        # Set the new sample count.
        self.n_samples = new_sample_dim

        # We cannot update the n_pings attribute here since raw_data uses
        # this attribute to store the number of pings read, *not* the total
        # number of pings in the array as the processed_data class uses it.
        # Instead, we have to set it either in the child class, or when context
        # permits, in other methods of this class.
