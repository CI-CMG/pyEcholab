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
    The calibration class provides parameters required for transforming power,
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

    def __init__(self, absorption_method='F&G'):
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


    def get_parameter(self, raw_data, param_name, return_indices,
                               dtype='float32'):
        """Retrieves calibration parameter values.

        This method returns appropriately sized arrays containing the calibration
        parameter specified in param_name. The calibration object's attributes
        can be set to None, to a scalar value, or to a 1d array and this function
        creates and fills these arrays based on the data in the calibration object
        and the value passed to return_indices. It handles 4 cases:

            If the calibration object's parameter is a scalar value, the function
            will return a 1D array the length of return_indices filled with
            that scalar.

            If the calibration object's parameter is a 1D array the length of
            return_indices, it will return that array without modification.

            If the calibration object's parameter is a 1D array the length of
            self.ping_time, it will return a 1D array the length of return_indices
            that is the subset of this data defined by the return_indices index
            array.

            Lastly, If the calibration object's parameter is None this function will
            return a 1D array the length of return_indices filled with data
            extracted from the raw data object.

        Args:
            cal_object (calibration object): The calibration object from which
                parameter values will be retrieved.
            param_name (str):  Attribute name needed to get parameter value in
                calibration object.
            return_indices (array): A numpy array of indices to return.
            dtype (str): Numpy data type of the returned array.

        Raises:
            ValueError: The calibration parameter array is the wrong length.
            ValueError: The calibration parameter isn't a ndarray or scalar
                float.

        Returns:
            A numpy array, param_data, with calibration parameter values.
        """

        # If we're not given specific indices, grab everything.
        if return_indices is None:
            return_indices = np.arange(raw_data.ping_time.shape[0])
        # Ensure that return_indices is a numpy array
        elif type(return_indices) is not np.ndarray:
            return_indices = np.array(return_indices, ndmin=1)

        # Check if the provided calibration object has the requested attribute
        if hasattr(self, param_name):

            # Yes. Get a reference to it
            param = getattr(self, param_name)

            # Check if it contains data
            if param is None:
                # It doesn't, extract from the raw_data object
                param = self.get_attribute_from_raw(raw_data, param_name,
                        return_indices=return_indices)

            # Check if the input param is a numpy array.
            if isinstance(param, np.ndarray):
                # Check if it is a single value array.
                if param.shape[0] == 1:
                    param_data = np.empty((return_indices.shape[0]), dtype=dtype)
                    param_data.fill(param)
                # Check if it is an array the same length as contained in the
                # raw data.
                elif param.shape[0] == raw_data.ping_time.shape[0]:
                    # Calibration parameters provided as full length
                    # array.  Get the selection subset.
                    param_data = param[return_indices]
                # Check if it is an array the same length as return_indices.
                elif param.shape[0] == return_indices.shape[0]:
                    # Calibration parameters provided as a subset, so no need
                    # to index with return_indices.
                    param_data = param
                else:
                    # It is an array that is the wrong shape.
                    raise ValueError("The calibration parameter array " +
                            param_name + " is the wrong length.")
            # It is not an array.  Check if it is a scalar int or float.
            elif type(param) in [int, float, np.int32, np.uint32, np.int64, np.float32, np.float64]:
                param_data = np.empty((return_indices.shape[0]), dtype=dtype)
                param_data.fill(param)
            elif type(param) in [str, object, dict, list]:
                param_data = np.empty((return_indices.shape[0]), dtype='object')
                param_data.fill(param)
            else:
                # Invalid type provided.
                raise ValueError("The calibration parameter " + param_name +
                        " must be an ndarray or scalar value.")

        else:
            # The requested parameter is not availailable
            param_data = None

        return param_data


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

        ecs_version = None
        sourcecal = {}
        localcal = {}
        fileset = {}
        current_section = ''
        current_transceiver = ''

        with open(ecs_file, 'r') as fp:
            line = fp.readline()

            line = line.strip()
            if line[0] == "#":
                #  this is a comment line - process for section headers
                if line.find('FILESET SETTINGS'):
                    current_section = 'FILESET SETTINGS'

                elif line.find('SOURCECAL SETTINGS'):
                    current_section = 'SOURCECAL SETTINGS'

                elif line.find('LOCALCAL SETTINGS'):
                    current_section = 'LOCALCAL SETTINGS'

            else:
                if line:
                    line_parts = line.split(' ')

                    if current_section == '':
                        if line_parts[0].lower() == 'version':
                            ecs_version = line_parts[2]

                    elif current_section == 'FILESET SETTINGS':
                        #  not sure how localcal section is laid out
                        #  for now just dump into the top level
                        fileset[line_parts[0]] = line_parts[2]

                    elif current_section == 'SOURCECAL SETTINGS':
                        if line_parts[0].lower() == 'sourcecal':
                            current_transceiver = line_parts[1]
                        else:
                            #  this must be a param in the current xcvr sourcecal section
                            if not current_transceiver in sourcecal.keys():
                                sourcecal[current_transceiver] = {}

                            sourcecal[current_transceiver][line_parts[0]] = line_parts[2]

                    elif current_section == 'LOCALCAL SETTINGS':
                        #  not sure how localcal section is laid out
                        #  for now just dump into the top level
                        localcal[line_parts[0]] = line_parts[2]

        return (ecs_version, sourcecal, localcal, fileset)


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
            return None

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
        # Get depth in m
        D = self.get_attribute_from_raw(raw_data, 'depth',
                return_indices=return_indices)

        # Acidity pH
        pH = self.get_attribute_from_raw(raw_data, 'acidity',
                return_indices=return_indices)

        # Salinity in PSU
        S = self.get_attribute_from_raw(raw_data, 'salinity',
                return_indices=return_indices)

        # Temperature in deg c
        T = self.get_attribute_from_raw(raw_data, 'temperature',
                return_indices=return_indices)

        # Compute absorption using the specified method
        if method.lower() in ['am', 'a&m']:
            # Ainslie M. A., McColm J. G.

            # Frequency in kHz squared
            fsq = np.square(raw_data.frequency / 1000.0)

            # Depth in km
            D = D / 1000.0

            # Compute relaxation frequencies
            f1 = 0.78 * np.sqrt(S/35.0) * np.exp(T / 26.0)
            f2 = 42.0 * np.exp(T / 17.0)

            # Compute absorption in dB/m
            a = 0.106 * ((f1 * fsq) / (np.square(f1) + fsq)) * np.exp((pH - 8.0) / 0.56)
            a += 0.52 * (1 + T / 43.0) * (S / 35.0) * ((f2 * fsq) / (np.square(f2) + fsq)) * np.exp(-D / 6.0)
            a += 0.00049 * fsq * np.exp(-(T / 27.0 + D / 17.0))
            #  return value in dB/m
            a = a / 1000

        elif method.lower() in ['fg', 'f&g']:
            # Francois R. E., Garrison G. R.

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
