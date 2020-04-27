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


#  This class may ultimately become simrad_calibration

class calibration(object):
    """
    The calibration class contains parameters required for transforming power,
    electrical angle, and complex data to Sv/sv TS/SigmaBS and physical angles.

    Calibration objects are specific to the hardware and/or data file format
    and are usually implemented within the specific instrument modules. This
    class is the base clase for these instrument specific calibration classes.


    When converting raw data to power, Sv/sv, Sp/sp, or to physical angles
    you have the option of passing a calibration object containing the data
    you want used during these conversions. To use this object you create an
    instance and populate the attributes with your calibration data.

    You can provide the data in 2 forms:
        As a scalar - the single value will be used for all pings.
        As a vector - a vector of values as long as the number of pings
            in the raw_data object where the first value will be used
            with the first ping, the second with the second, and so on.

    If you set any attribute to None, that attribute's values will be obtained
    from the raw_data object which contains the value at the time of recording.
    If you do not pass a calibration object to the conversion methods
    *all* of the cal parameter values will be extracted from the raw_data
    object.
    """

    def __init__(self, absorption_method='A&M'):
        '''

            absorption_method (str): specifies the method used to calculate
                                     absorption of sound in seawater.

            Available methods are:

                'A&M': Computes absorption using the equation describe in:

                Ainslie M. A., McColm J. G., "A simplified formula for viscous and
                  chemical absorption in sea water", Journal of the Acoustical Society
                  of America, 103(3), 1671-1672, 1998.

                http://resource.npl.co.uk/acoustics/techguides/seaabsorption/physics.html


                'F&G': Computes absorption using the equation describe in:

                Francois R. E., Garrison G. R., "Sound absorption based on ocean
                  measurements: Part II:Boric acid contribution and equation for
                  total absorption", Journal of the Acoustical Society of America,
                  72(6), 1879-1890, 1982.

                  The code for the F&G method was adapted from code contributed to
                  the Echopype project by ``arlpy``
                  https://github.com/OSOceanAcoustics/echopype

        '''

        # Set the initial calibration property values.
        self.channel_id = None
        self.absorption_method = absorption_method

        # each attribute below represents a place where "calibration" data can
        # be found depending on the specific instrument and/or file format. These
        # lists are populated in the child classes to inform the other methods
        # where to get/set the various parameters. The

        #  raw attributes are direct attributes of the raw_data class
        self._raw_attributes = []

        #  config attributes are attributes with values that are stored in the
        #  raw_data.configuration dictionary unique to each data file and linked
        #  to each ping.
        self._config_attributes = []

        #  environment attributes are attributes with values that are stored in the
        #  raw_data.environment object and may or may not be linked to pings.
        self._environment_attributes = []


    def from_raw_data(self, raw_data, return_indices=None):
        """Populates the calibration object using the data from the provided raw_data
        object.

        Args:
            raw_data (raw_data): The object where parameters will be extracted
                from and used to populate the calibration object.
            return_indices (array): A numpy array of indices to return.
        """

        # Set the channel_id.
        self.channel_id = raw_data.channel_id

        # If we're not given specific indices, grab everything.
        if return_indices is None:
            return_indices = np.arange(raw_data.ping_time.shape[0])

        # Extract the direct attributes - these are calibration params
        # stored as top level attributes in the raw_data class
        for param_name in self._raw_attributes:
            self.set_attribute_from_raw(raw_data, param_name,
                    return_indices=return_indices)

        # Extract attributes from the configuration dict - these are
        # attribues that are stored in the .raw file configuration
        # datagram and apply to all data within a .raw file
        for param_name in self._config_attributes:
            self.set_attribute_from_raw(raw_data, param_name,
                    return_indices=return_indices)

        # Extract attributes from the environment datagrams
        for param_name in self._environment_attributes:
            self.set_attribute_from_raw(raw_data, param_name,
                    return_indices=return_indices)


    def read_ecs_file(self, ecs_file, channel):
        """Reads an echoview ecs file and parses out the
        parameters for a given channel.
        """

        current_section = ''
        current_transceiver = ''


        with open(ecs_file, 'r') as fp:
            line = fp.readline()


    def get_attribute_from_raw(self, raw_data, param_name, return_indices=None):
        """get_attribute_from_raw gets an individual attribute using the data
        within the provided raw_data object.
        """
        param_data = None

        # If we're not given specific indices, grab everything.
        if return_indices is None:
            return_indices = np.arange(raw_data.ping_time.shape[0])

        if param_name in self._raw_attributes:
            # Extract data from raw_data attribues
            if hasattr(raw_data, param_name):
                raw_param = getattr(raw_data, param_name)
                param_data = raw_param[return_indices]

                # Check if the param data is constant and return a scalar if so.
                if param_data.dtype == object:
                    if np.all(param_data == param_data[0]):
                        # This param is constant
                        param_data = param_data[0]
                else:
                    if np.all(np.isclose(param_data, param_data[0])):
                        # This param is constant
                        param_data = param_data[0]
            else:
                param_data = None

        elif param_name in self._config_attributes:
            # Extract param from the configuration dictionary
            param_data = self._get_param_data(raw_data.configuration, param_name,
                    return_indices)

        elif param_name in self._environment_attributes:
            # Extract param from the environment dictionary
            param_data = self._get_param_data(raw_data.environment, param_name,
                    return_indices)

        return param_data, return_indices


    def set_attribute_from_raw(self, raw_data, param_name, return_indices=None):
        """set_attribute_from_raw updates an individual attribute using the data
        within the provided raw_data object.
        """
        param_data = self.get_attribute_from_raw(raw_data, param_name,
            return_indices=return_indices)

        # If param_data is not none, update the attribute
        if not param_data is None:

            # Update the attribute.
            setattr(self, param_name, param_data)


    def _init_attributes(self, attributes):
        """ Internal method to initialize the provided attribute to None
        """

        for attribute in attributes:
            # Add the attribute
            setattr(self, attribute, None)


    def _get_param_data(self, raw_attribute, param_name, return_indices):
        '''_get_param_data is an internal method that extracts and returns the
        data identified by the raw_attribute dictionary and param_name key.
        '''

        # Bail if we don't have this particular parameter
        if param_name not in raw_attribute[0]:
            param_data = None

        # Determine the data type and size of the param and create empty array
        if isinstance(raw_attribute[0][param_name], np.ndarray):
            dtype = raw_attribute[0][param_name].dtype
            dsize = (return_indices.shape[0], raw_attribute[0][param_name].shape[0])
        elif isinstance(raw_attribute[0][param_name], int):
            dtype = np.int32
            dsize = (return_indices.shape[0])
        elif isinstance(raw_attribute[0][param_name], float):
            dtype = np.float32
            dsize = (return_indices.shape[0])
        else:
            dtype = 'object'
            dsize = (return_indices.shape[0])
        param_data = np.empty(dsize, dtype=dtype)

        # Populate the empty array - track the parameter value to determine
        # if the parameter is constant throughout all specified pings. If
        # constant, we'll return a scalar. Numpy array_equal doesn't always
        # return what we need so it has to be done element wise
        ret_idx = 0
        param_is_constant = True
        last_val = None
        for idx in return_indices:
            if last_val is None:
                # Nothing to compare yet so set the first item to compare
                last_val = raw_attribute[idx][param_name]
            else:
                #  check if our value has changed
                if param_data.ndim > 1:
                    param_is_constant &= np.array_equal(raw_attribute[idx][param_name], last_val)
                else:
                    param_is_constant &= raw_attribute[idx][param_name] == last_val

            #  insert this param value into the param_data array
            if param_data.ndim == 1:
                param_data[ret_idx] = raw_attribute[idx][param_name]
            elif param_data.ndim == 2:
                param_data[ret_idx,:] = raw_attribute[idx][param_name][:]
            ret_idx += 1

        # Check if our param value was constant
        if param_is_constant:
            # It was, return a scalar
            param_data = last_val

        return param_data


    def _compute_absorption(self, raw_data, return_indices, method):
        '''_compute_absorption computes seawater absorption based on the
        specified method.

        Available methods are:

            'A&M': Computes absorption using the equation describe in:

            Ainslie M. A., McColm J. G., "A simplified formula for viscous and
              chemical absorption in sea water", Journal of the Acoustical Society
              of America, 103(3), 1671-1672, 1998.

            http://resource.npl.co.uk/acoustics/techguides/seaabsorption/physics.html


            'F&G': Computes absorption using the equation describe in:

            Francois R. E., Garrison G. R., "Sound absorption based on ocean
              measurements: Part II:Boric acid contribution and equation for
              total absorption", Journal of the Acoustical Society of America,
              72(6), 1879-1890, 1982.

            The code for the F&G method was adapted from code contributed to
            the Echopype project by ``arlpy``
            https://github.com/OSOceanAcoustics/echopype

        absorption is returned as dB/m
        '''
        # Get depth in km
        D = self.get_attribute_from_raw(raw_data, 'depth',
                return_indices=return_indices)
        D = D / 1000.0

        # Acidity pH
        pH = self.get_attribute_from_raw(raw_data, 'acidity',
                return_indices=return_indices)

        # Salinity in PSU
        S = self.get_attribute_from_raw(raw_data, 'salinity',
                return_indices=return_indices)

        # Temperature in deg c
        T = self.get_attribute_from_raw(raw_data, 'temperature',
                return_indices=return_indices)

        if method.lower() in ['am', 'a&m']:

            # Frequency in kHz squared
            fsq = np.square(raw_data.frequency / 1000.0)

            # Compute relaxation frequencies
            f1 = 0.78 * np.sqrt(S/35.0) * np.exp(T / 26.0)
            f2 = 42.0 * np.exp(T / 17.0)

            # Compute absorption in dB/m
            a = 0.106 * (f1 / (np.square(f1) + fsq)) * np.exp((pH - 8.0) / 0.56)
            a += 0.52 * (1 + T / 43.0) * (S / 35.0) * (f2 / (np.square(f2) + fsq)) * np.exp(-D / 6.0)
            a += 0.00049 * np.exp(-(T / 27.0 + D / 17.0))
            a = a * (fsq / 1000)

        elif method.lower() in ['fg', 'f&g']:

            # Frequency in kHz
            f = raw_data.frequency / 1000.0

            # from echopype.utils.uwa.calc_seawater_absorption
            c = 1412.0 + 3.21 * T + 1.19 * S + 0.0167 * D
            A1 = 8.86 / c * 10**(0.78 * pH - 5)
            P1 = 1.0
            f1 = 2.8 * np.sqrt(S / 35) * 10**(4 - 1245 / (T + 273))
            A2 = 21.44 * S / c * (1 + 0.025 * T)
            P2 = 1.0 - 1.37e-4 * D + 6.2e-9 * D * D
            f2 = 8.17 * 10 ** (8 - 1990 / (T + 273)) / (1 + 0.0018 * (S - 35))
            P3 = 1.0 - 3.83e-5 * D + 4.9e-10 * D * D
            if T < 20:
                A3 = (4.937e-4 - 2.59e-5 * T + 9.11e-7 * T ** 2 -
                      1.5e-8 * T ** 3)
            else:
                A3 = 3.964e-4 - 1.146e-5 * T + 1.45e-7 * T ** 2 - 6.5e-10 * T ** 3

            # Compute absorption in dB/m
            a = A1 * P1 * f1 * f * f / (f1 * f1 + f * f) + A2 * P2 * f2 * f * \
                    f / (f2 * f2 + f * f) + A3 * P3 * f * f
            a = -20 * np.log10(10**(-a * 1.0 / 20.0)) / 1000

        return a
