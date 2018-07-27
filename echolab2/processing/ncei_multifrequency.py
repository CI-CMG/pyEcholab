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



class MultifrequencyData(PingData):
    """
    MultifrequencyData is a class to create and contain NCEI style
    multi-frequency data
    """

    def __init__(self, data_objects, config_file, sigma=None):
        """Initializes ProcessedData class object.

        Creates and sets several internal properties used to store information
        about data and control operation of processed data object instance.
        Code is heavily commented to facilitate use.
        """
        super(MultifrequencyData, self).__init__()

        self.sigma = sigma

        # Create attributes that are dictionaries containing references to
        # ProcessedData objects and Mask objects.
        self.masks = {}
        self.smooth_objects = {}
        self.processed_data = {}

        self.get_multifrequency_data(data_objects)

    def make_masks(self, data_objects, low_threshold, high_threshold):
        masks = {}
        for frequency, data in data_objects.items():
            masks[frequency] = (data >= low_threshold) & (
                        data <= high_threshold)
        return masks

    def mask_data(self, data_objects, masks, values=None):
        if not values:
            values = {18: 1, 38: 3, 70: 29, 120: 7, 200: 13}

        processed_data = {}
        for frequency, data in data_objects.items():
            processed_data[frequency] = data.zeros_like()
            processed_data[frequency][masks[frequency]] = values[frequency]

        return processed_data

    def smooth(self, data_objects, sigma=3):
        smooth_objects = {}

        for frequency, data in data_objects.items():
            smooth_data = gf(data.data, sigma)
            new_object = data.empty_like()
            setattr(new_object, 'data', smooth_data)
            smooth_objects[frequency] = new_object

        return smooth_objects

    def get_multifrequency_data(self, data_objects, low_threshold=-66,
                                high_threshold=-25, values=None):

        masks = make_masks(data_objects, low_threshold, high_threshold)
        processed_data = mask_data(data_objects, masks)

        # Make a new Processed Data object to hold final data array (using the
        # the first channel as a template.
        channels = list(data_objects.keys())
        first_channel = channels[0]
        # final_data = data_objects[first_channel].zeros_like()

        # Add each channels integer values to create final data array
        for value in processed_data.values():
            self.data += value

        return final_data
