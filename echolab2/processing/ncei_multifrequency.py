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

    def __init__(self, data_objects, low_threshold,
                 high_threshold, values,):
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

        # Create an empty Numpy array of proper size to hold integer values
        # from multifrequency analysis.
        data = zeros((self.n_pings, self.n_samples), dtype=int8, order='C')
        self.add_attribute('data', data)
        self._data_attributes.append('data')

        self.low_threhold = low_threshold
        self.high_threshold = high_threshold
        self.values = values

        # Create attributes that are dictionaries containing references to
        # ProcessedData objects and Mask objects.
        self.masks = {}
        self.processed_data = {}

        self.get_multifrequency_data(data_objects, self.low_threhold,
                                     self.high_threshold, self.values)

    def make_masks(self, data_objects, low_threshold, high_threshold):
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

