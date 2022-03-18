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

        #  create a dict to map ECS variables to Echolab cal object properties
        #  A few mappings may be updated in the child class init.
        self.ECS_ECHOLAB_MAP = {'AbsorptionCoefficient':'absorption_coefficient',
                                'AbsorptionDepth':'depth',
                                'Acidity':'acidity',
                                'EffectivePulseLength':'',
                                'EK60SaCorrection':'sa_correction',
                                'Frequency':'frequency',
                                'MajorAxis3dbBeamAngle':'beam_width_alongship',
                                'MajorAxisAngleOffset':'angle_offset_alongship',
                                'MajorAxisAngleSensitivity':'angle_sensitivity_alongship',
                                'MinorAxis3dbBeamAngle':'beam_width_athwartship',
                                'MinorAxisAngleOffset':'angle_offset_athwartship',
                                'MinorAxisAngleSensitivity':'angle_sensitivity_athwartship',
                                'Salinity':'salinity',
                                'SamplingFrequency':'sampling_frequency',
                                'TransceiverSamplingFrequency':'rx_sample_frequency',
                                'TransceiverImpedance':'transceiver_impedance',
                                'SoundSpeed':'sound_speed',
                                'Temperature':'temperature',
                                'TransducerGain':'gain',
                                'TransmittedPower':'transmit_power',
                                'TransmittedPulseLength':'pulse_length',
                                'TvgRangeCorrection':'tvg_range_correction',
                                'TwoWayBeamAngle':'equivalent_beam_angle'}

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
            IT IS ASSUMED THE PARAMETER VALUES WILL BE ORDERED CORRECTLY FOR
            THE return_indices ARRAY PROVIDED. That is, the first param value
            will be applied to the raw_data at return_indices[0], the second
            will be applied to the raw_data at return_indices[1], and so on.

            If the calibration object's parameter is a 1D array the length of
            self.ping_time, it will return a 1D array the length of return_indices
            that is the subset of this data defined by the return_indices index
            array. In this case it is assumed the parameter is ordered to match
            the order of the data in the raw_data object.

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
                # It doesn't, extract from the raw_data object - do not
                # provide the return_indices - we want this ordered as
                # it is stored in the raw_data object.
                param = self.get_attribute_from_raw(raw_data, param_name)

            # Check if the param is a numpy array.
            if isinstance(param, np.ndarray):
                # Check if it is a single value array.
                if param.shape[0] == 1:
                    param_data = np.empty((return_indices.shape[0]), dtype=dtype)
                    param_data.fill(param)
                # Check if it is an array the same length as contained in the
                # raw data. This check must come *before* checking if our param's
                # shape is the same as return_indices.
                elif param.shape[0] == raw_data.ping_time.shape[0]:
                    # Calibration parameters provided as full length array.
                    # When provided this way, we assume they are ordered as
                    # the same as the data in raw_data. In this case we must
                    # get the selection subset.
                    param_data = param[return_indices]
                # Check if it is an array the same length as return_indices.
                elif param.shape[0] == return_indices.shape[0]:
                    # Calibration parameters provided as a subset, so no need
                    # to index with return_indices because we assume they are
                    # in the correct order.
                    param_data = param
                else:
                    # It is an array that is the wrong shape.
                    raise ValueError("The calibration parameter array " +
                            param_name + " is the wrong length.")
            # It is not an array.  Check if it is a scalar int or float.
            elif type(param) in [int, float, np.int32, np.uint32, np.int64, np.float32, np.float64]:
                param_data = np.empty((return_indices.shape[0]), dtype=type(param))
                param_data.fill(param)
            elif type(param) in [str, object, dict, list]:
                param_data = np.empty((return_indices.shape[0]), dtype='object')
                param_data.fill(param)
            elif param is None:
                # This must be a computed parameter since it exists but None is returned.
                # Pass along the None - the value will be computed later.
                param_data = None
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
        """Reads an echoview ecs file and parses out the parameters for a given channel.

        channel (str): Specify the "SourceCal" channel ID, eg "T1" "T2" etc

        """

        def parse_ecs_param(ecs_text):
            #  first split on the equals sign
            line_parts = line.split('=')
            param = line_parts[0].strip()

            #  try to map this parameter to this cal object's attribute
            try:
                our_param = self.ECS_ECHOLAB_MAP[param]
            except:
                raise NotImplementedError('Echoview ECS parameter ' + param +
                        ' is not implemented.')

            #  then clean up the RHS by stripping off any comments
            value = line_parts[1].split('#')[0]

            #  try to convert to a float
            try:
                value = float(value)
            except:
                value.strip()

            return our_param, value


        ecs_version = None
        current_section = ''
        current_channel = ''

        with open(ecs_file, 'r') as fp:
            for line in fp:

                #  strip leading and trailing whitespace
                line = line.strip()

                #  skip blank lines
                if len(line) == 0:
                    continue

                if line[0] == "#":
                    #  this is a comment line - process for section headers
                    if line.find('FILESET SETTINGS') > -1:
                        current_section = 'FILESET SETTINGS'
                    elif line.find('SOURCECAL SETTINGS') > -1:
                        current_section = 'SOURCECAL SETTINGS'
                    elif line.find('LOCALCAL SETTINGS') > -1:
                        current_section = 'LOCALCAL SETTINGS'

                    # otherwise we ignore commented lines

                else:
                    #  this line is *not* commented - proceed based on what section we're in

                    if current_section == '':
                        #  this must be the version
                        line_parts = line.split(' ')
                        if line_parts[0].lower() == 'version':
                            ecs_version = line_parts[1].strip()

                    elif current_section == 'FILESET SETTINGS':
                        #  process the fileset params -
                        param, value = parse_ecs_param(line)

                        #  these params apply to all channels so we set our attribute
                        setattr(self, param, value)

                    elif current_section == 'SOURCECAL SETTINGS':
                        line_parts = line.split(' ')
                        if line_parts[0].lower() == 'sourcecal':
                            current_channel = line_parts[1].strip()
                        else:
                            #  check if these are the params we're looking for...
                            if current_channel == channel:

                                #  parse the value
                                param, value = parse_ecs_param(line)

                                #  and set the attribute
                                setattr(self, param, value)

                    elif current_section == 'LOCALCAL SETTINGS':
                        #  not really sure what to do with localcal settings
                        raise NotImplementedError('LOCALCAL settings are currently not implemented.')


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

        # Determine the data type and size of the param and create empty array.
        # Since we can have "empty" pings where the array of dicts we're unpacking
        # may contain NaNs, we can't assume the first (or any) ping will contain
        # data and have to search for the first dict in the array.
        found_data = False
        for idx in return_indices:
            # Check if this attribute is a dict
            if isinstance(raw_attribute[idx], dict):
                # Check if the requested parameter exists in this dict
                if param_name not in raw_attribute[idx]:
                    # it doesn't - move on to the
                    continue
                # The key exists, now get the size and type of this data
                if isinstance(raw_attribute[idx][param_name], np.ndarray):
                    dtype = raw_attribute[idx][param_name].dtype
                    dsize = (return_indices.shape[0], raw_attribute[idx][param_name].shape[0])
                elif isinstance(raw_attribute[idx][param_name], int):
                    dtype = np.int32
                    dsize = (return_indices.shape[0])
                elif isinstance(raw_attribute[idx][param_name], float):
                    dtype = np.float32
                    dsize = (return_indices.shape[0])
                else:
                    dtype = 'object'
                    dsize = (return_indices.shape[0])

                # Create the return array
                param_data = np.empty(dsize, dtype=dtype)

                # And set the comparison value
                first_val = raw_attribute[idx][param_name]

                # We found a valid dict, we can stop searching
                found_data = True
                break;

        #  check if we found any data
        if found_data:
            # Populate the empty array - track the parameter value to determine
            # if the parameter is constant throughout all specified pings. If
            # constant, we'll return a scalar. Numpy array_equal doesn't always
            # return what we need so it has to be done element wise
            data_idx = 0
            param_is_constant = True
            for idx in return_indices:
                # Get this idx's value - raw_attribute[idx] will be a dict or NaN
                if isinstance(raw_attribute[idx], dict):
                    # It is a dict, extract the value
                    if param_data.ndim == 1:
                        this_val = raw_attribute[idx][param_name]
                    elif param_data.ndim == 2:
                        this_val = raw_attribute[idx][param_name][:]
                else:
                    #this_val = first_val
                    if np.issubdtype(dtype, np.inexact):
                        this_val = np.nan
                    elif np.issubdtype(dtype, np.integer):
                        this_val = 0
                    else:
                        this_val = ''

                    # Expand the empty value if required
                    if param_data.ndim == 2:
                        this_val = np.full(dsize[1], this_val)

                # Assign the value to the return array and check if it has changed
                if param_data.ndim == 1:
                    param_data[data_idx] = this_val
                    param_is_constant &= this_val == first_val
                else:
                    param_data[data_idx,:] = this_val
                    param_is_constant &= np.array_equal(this_val, first_val)

                # Increment the index counter
                data_idx += 1

            # Check if our param value was constant
            if param_is_constant:
                # It was, return a scalar
                param_data = first_val

        else:
            # There was no data found - in these cases we return NaN
            param_data = np.nan

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

        def compute_sound_speed(T, D, S):
            '''
            compute_sound_speed in saltwater (Mackenzie, 1981)

            '''
            c = 1448.96 + 4.591 * T - 0.05304 * T ** 2
            c += 2.374e-4 * T ** 3 + 1.34 * (S - 35) + 0.0163 * D
            c += 1.675e-7 * D**2 - 0.01025 * T * (S - 35) - 7.139e-13*(T*D)**3

            return c

        # Get depth in m
        D = self.get_parameter(raw_data, 'depth',
                return_indices=return_indices)

        # Acidity pH
        pH = self.get_parameter(raw_data, 'acidity',
                return_indices=return_indices)

        # Salinity in PSU
        S = self.get_parameter(raw_data, 'salinity',
                return_indices=return_indices)

        # Temperature in deg c
        T = self.get_parameter(raw_data, 'temperature',
                return_indices=return_indices)

        # Sound speed in m/s
        c = self.get_parameter(raw_data, 'sound_speed',
                return_indices=return_indices)

        # Get the tx frequency
        fhz = self.get_parameter(raw_data, 'frequency',
                return_indices=return_indices)
        if fhz is None:
            # Must be FM - get the center frequency
            fhz_start = self.get_parameter(raw_data, 'frequency_start',
                return_indices=return_indices)
            fhz_end = self.get_parameter(raw_data, 'frequency_end',
                return_indices=return_indices)
            # Compute center freq in kHz
            fkhz = (fhz_start + fhz_end) / 2000.
        else:
            # This is CW - just convert freq to kHz
            fkhz = fhz / 1000.0

        # Compute absorption using the specified method
        if method.lower() in ['am', 'a&m']:
            # Ainslie M. A., McColm J. G.

            # Frequency in kHz squared
            fsq = fkhz ** 2

            # Depth in km
            D = D / 1000.0

            # Compute relaxation frequencies
            f1 = 0.78 * np.sqrt(S/35.0) * np.exp(T / 26.0)
            f2 = 42.0 * np.exp(T / 17.0)

            # Compute absorption in dB/m
            a = 0.106 * np.exp((pH - 8.0) / 0.56) * f1 / (f1**2 + fsq)
            a += 0.52 * (1 + T / 43.0) * (S / 35.0) * np.exp(-D / 6.0) * f2 / (fsq + f2**2)
            a *= 0.00049 * np.exp(-(T/27.0 + D/17.0))

            a = (fsq/1000) * a

        elif method.lower() in ['fg', 'f&g']:
            # Francois R. E., Garrison G. R.

            # Frequency in kHz
            f = fkhz

            # We don't compute the sound speed but instead use the speed provided
            # in the raw file or calibration object.
            #c = compute_sound_speed(T, D, S)

            # from echopype.utils.uwa.calc_seawater_absorption
            A1 = 8.86 / c * 10**(0.78 * pH - 5)
            P1 = 1.0
            f1 = 2.8 * np.sqrt(S / 35) * 10**(4 - 1245 / (T + 273))
            A2 = 21.44 * S / c * (1 + 0.025 * T)
            P2 = 1.0 - 1.37e-4 * D + 6.2e-9 * D * D
            f2 = 8.17 * 10 ** (8 - 1990 / (T + 273)) / (1 + 0.0018 * (S - 35))
            P3 = 1.0 - 3.83e-5 * D + 4.9e-10 * D * D
            A3 = np.empty((T.shape[0]), np.float32)
            tidx = T <= 20
            A3[tidx] = (4.937e-4 - 2.59e-5 * T[tidx] + 9.11e-7 * T[tidx] ** 2 - 1.5e-8 * T[tidx] ** 3)
            tidx = T > 20
            A3[tidx] = 3.964e-4 - 1.146e-5 * T[tidx] + 1.45e-7 * T[tidx] ** 2 - 6.5e-10 * T[tidx] ** 3

            # Compute absorption in dB/m
            a = A1 * P1 * f1 * f * f / (f1 * f1 + f * f) + A2 * P2 * f2 * f * \
                    f / (f2 * f2 + f * f) + A3 * P3 * f * f
            a = -20 * np.log10(10**(-a * 1.0 / 20.0)) / 1000

        return a
