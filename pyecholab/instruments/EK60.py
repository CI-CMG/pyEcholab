# coding=utf-8

#     National Oceanic and Atmospheric Administration
#     Alaskan Fisheries Science Center
#     Resource Assessment and Conservation Engineering
#     Midwater Assessment and Conservation Engineering

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

import os
import datetime
from pytz import timezone
import logging
import numpy as np
from util.raw_file import RawSimradFile, SimradEOF
from util.date_conversion import nt_to_unix, unix_to_nt
from collections import defaultdict

log = logging.getLogger(__name__)


class EK60(object):

    def __init__(self):

        #  define the reader's default state
        self.start_time = None
        self.end_time = None
        self.start_ping = None
        self.end_ping = None
        self.read_power = True
        self.read_angles = True
        self.max_sample_range = None
        self.frequencies = None

        #  create a dictionary to store the EK60RawData objects
        self.raw_data = {}


    def read_raw(self, raw_files, power=True,  angles=True,  max_sample_range=None,  start_time=None,
            end_time=None,  start_ping=None,  end_ping=None,  frequencies=None,  channels=None,
            time_format_string='%Y-%m-%d %H:%M:%S'):
        '''
        read_raw reads one or many Simrad EK60 ES60/70 .raw files
        '''

        #  update the reader state variables
        if (start_time):
            self.start_time = self._convert_time_bound(start_time, format_string=time_format_string)
        if (end_time):
            self.end_time = self._convert_time_bound(end_time, format_string=time_format_string)
        if (start_ping):
            self.start_ping = start_ping
        if (end_ping):
            self.end_ping = end_ping
        if (power):
            self.read_power = power
        if (angles):
            self.read_angles = angles
        if (max_sample_range):
            self.max_sample_range = max_sample_range
        if (frequencies):
            self.frequencies = frequencies

        #  ensure that the raw_files argument is a list
        if isinstance(raw_files, str):
            raw_files = [raw_files]

        #  iterate thru our list of .raw files to read
        for filename in raw_files:

            #  Read data from file and add to self.raw_data.
            with RawSimradFile(filename, 'r') as fid:

                #  read the "CON" configuration datagrams
                config_datagrams= {}
                datagram = fid.read(1)
                while datagram['type'].startswith('CON'):
                    config_datagrams[datagram['type']] = datagram
                    datagram = fid.read(1)

                #  create an EK60RawData object for eqach channel in the file
                for channel in config_datagrams['CON0']['transceivers']:
                    channel_id = config_datagram['CON0']['transceivers'][channel]['channel_id']
                    if channel_id not in self.raw_data:

                channel_ids[channel] = channel_id #Create channel map.

                self.raw_data[channel_id] = EK60RawData(channel_id)
            self.raw_data[channel_id].append_file(filename)

                config_datagram = self._read_config_datagram(fid)

                channel_ids = self._read_data_header(config_datagram, filename)

                self._read_datagrams(fid, channel_ids)


    def _read_config_datagram(self, fid):
        '''
        _read_config_datagram reads the CON0 datagram from the raw file and extracts
        '''
        config_datagrams = {}
        while fid.peek()['type'].startswith('CON'):
            config_datagram = fid.read(1)
            if config_datagram['type'] in config_datagrams:
                raise ValueError('Malformed raw file. Multiple config datagrams of type %s found', config_datagram['type'])
            config_datagrams[config_datagram['type']] = config_datagram

        return config_datagrams


    def _read_data_header(self, config_datagram, filename):
        '''
        _read_raw_data_setup
        '''
        channel_ids = {}
        for channel in config_datagram['transceivers']:
            channel_id = config_datagram['transceivers'][channel]['channel_id']
            if channel_id not in self.raw_data:
                if channel in channel_ids:
                    #FIXME If these mappings vary from one file to the next, how should I handle that?
                    pass

                channel_ids[channel] = channel_id #Create channel map.
                self.raw_data[channel_id] = EK60RawData(channel_id)
            self.raw_data[channel_id].append_file(filename)
        return channel_ids


    def _read_datagrams(self, fid, channel_ids):
        '''
        _read_datagrams reads the datagrams contai
        '''

        num_sample_datagrams = 0
        num_sample_datagrams_skipped = 0
        num_unknown_datagrams_skipped = 0
        num_datagrams_parsed = 0
        sample_datagrams = {}
        sample_datagrams.setdefault('sample', [])

        while True:
            try:
                next_header = fid.peek()
            except SimradEOF:
                break

            try:
                new_datagram = fid.read(1)
            except SimradEOF:
                break

            #  convert from NT time to python datetime
            datagram_timestamp = nt_to_unix((next_header['low_date'], next_header['high_date']))

            #  check if we should continue to read this data based on time bounds
            if self.start_time is not None:
                if datagram_timestamp < self.start_time:
                    continue
            if self.end_time is not None:
                if datagram_timestamp > self.end_time:
                    continue

            num_datagrams_parsed += 1

            if new_datagram['type'].startswith('RAW'):

                if new_datagram['channel'] in channel_ids:
                    channel_id = channel_ids[new_datagram['channel']]
                    new_datagram['ping_time'] = datagram_timestamp
                    self.raw_data[channel_id].append_ping(new_datagram)
                    num_sample_datagrams += 1

                else:
                    num_sample_datagrams_skipped += 1

            elif new_datagram['type'].startswith('NME'):
                #TODO:  Implement NMEA reading
                pass
            elif new_datagram['type'].startswith('TAG'):
                #TODO: Implement annotation reading
                pass
            else:
                #  unknown datagram type - issue a warning
                log.warning('Skipping unkown datagram type: %s @ %s', new_datagram['type'], datagram_timestamp)
                num_unknown_datagrams_skipped += 1

            if not (num_datagrams_parsed % 10000):
                log.debug('    Parsed %d datagrams (%d sample).', num_datagrams_parsed, num_sample_datagrams)


        num_datagrams_skipped = num_unknown_datagrams_skipped + num_sample_datagrams_skipped
        log.info('  Read %d datagrams (%d skipped).', num_sample_datagrams, num_datagrams_skipped)


    def _convert_time_bound(self, time, format_string):
        '''
        internally all times are datetime objects converted to UTC timezone. This method
        converts arguments to comply.
        '''
        utc = timezone('utc')
        if (isinstance(time, str)):
            #  we have been passed a string, convert to datetime object
            time = datetime.datetime.strptime(time, format_string)

        #  convert to UTC and return
        return utc.localize(time)


class rawfile_metadata(object):
    '''
    The rawfile_metadata class stores the channel configuration data as well as
    some metadata about the file. One of these is created for each channel for
    every .raw file read.

    These objects are stored in a list in the raw_data class and

    '''

    def __init__(self, file):

        #  split the filename
        file = os.path.normpath(file).split(os.path.sep)

        #  store the base filename and path separately
        self.data_file = file[-1]
        self.data_file_path = os.path.sep.join(file[0:-1])

        #  define some basic metadata properties
        self.start_ping = 0
        self.end_ping = 0
        self.start_time = None
        self.end_time = None

        #  we will replicate the ConfigurationHeader struct here since there
        #  is no better place to store it
        self.survey_name = ''
        self.transect_name = ''
        self.sounder_name = ''
        self.version = ''

        #  the beam typre for this channel - split or single
        self.beam_type = 0

        #  the channel frequency in Hz
        self.frequency = 0

        #  the system gain when the file was recorded
        self.gain = 0

        #  beam calibration properties
        self.equivalent_beam_angle = 0
        self.beamwidth_alongship = 0
        self.beamwidth_athwartship = 0
        self.angle_sensitivity_alongship = 0
        self.angle_sensitivity_athwartship = 0
        self.angle_offset_alongship = 0
        self.angle_offset_athwartship = 0

        #  transducer installation/orientation parameters
        self.posx = 0
        self.posy = 0
        self.posz = 0
        self.dirx = 0
        self.diry = 0
        self.dirz = 0

        #  the possile pulse lengths for the recording system
        self.pulse_length_table = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.spare2 = ''
        #  the gains set for each of the system pulse lengths
        self.gain_table = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.spare3 = ''
        #  the sa correction values set for each pulse length
        self.sa_correction_table = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.spare4 = ''


class ek60_cal_parameters(object):
    '''
    The EK60CalParameters class contains parameters required for transforming
    power and electrical angle data to Sv/sv TS/SigmaBS and physical angles.
    '''

    def __init__(self, file):

        self.channel_id = ''
        self.frequency = 0
        self.sound_velocity = 0.0
        self.sample_interval = 0
        self.absorption_coefficient = 0.0
        self.gain = 0.0
        self.equivalent_beam_angle = 0.0
        self.beamwidth_alongship = 0.0
        self.beamwidth_athwartship = 0.0
        self.pulse_length_table = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.gain_table  = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.sa_correction_table = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.transmit_power = 0.0
        self.pulse_length = 0.0
        self.angle_sensitivity_alongship = 0.0
        self.angle_sensitivity_athwartship = 0.0
        self.angle_offset_alongship = 0.0
        self.angle_offset_athwartship = 0.0
        self.transducer_depth = 0.0


    def from_raw_data(self, raw_data, raw_file_idx=0):
        '''
        from_raw_data populated the CalibrationParameters object's properties given
        a reference to a RawData object.

        This would query the RawFileData object specified by raw_file_idx in the
        provided RawData object (by default, using the first).
        '''

        pass


    def read_ecs_file(self, ecs_file, channel):
        '''
        read_ecs_file reads an echoview ecs file and parses out the
        parameters for a given channel.
        '''
        pass


class EK60RawData(object):
    '''
    the EK60RawData class contains a single channel's data extracted from a Simrad raw
    file. collected from an EK/ES60 or ES70. A EK60RawData object is created for each
    unique channel in an EK/ES60 ES70 raw file.

    EK60RawData has all of the properties we defined at the Boulder meeting but instead
    of a dictionary, I think that Pamme's suggestion of a class is the better way to
    go. The RawData class contains methods to manage the raw data at a low level
    allowing the reader to mainly handle the lower level reading business.

    To support streaming data sources (broadcast telegrams, server/client interface)
    you can set the "rolling" keyword and specify the initial array dimensions when
    you instantiate the class. Then when using the add_ping method, the data arrays
    will act as FIFO, "rolling left" when the array is full.

    We can use callbacks to support announcing when the add_ping method is finished
    to, for example, notify an live display application to redraw the echogram.


    '''

    #  define some instrument specific constants
    SAMPLES_PER_PULSE = 4

    #FIXME Values?
    RESAMPLE_LOWEST = 64
    RESAMPLE_64 = 64
    RESAMPLE_128 = 128
    RESAMPLE_256 = 256
    RESAMPLE_512 = 512
    RESAMPLE_1024 = 1024
    RESAMPLE_2048 = 2048
    RESAMPLE_4096 = 4096
    RESAMPLE_HIGHEST = 4096


    to_shortest = 0
    to_longest = 1

    def __init__(self, channel_id, n_pings=0, n_samples=1000, rolling=False,
            chunk_width=500):
        '''
        Creates a new, empty EK60RawData object. The EK60RawData class stores raw
        echosounder data from a single channel of an EK60 or ES60/70 system.

        if rolling is True, arrays of size (n_pings, n_samples) are created for power
        and angle data upon instantiation and are filled with NaNs. These arrays are
        fixed in size and if a ping is added beyond the "width" of the array the
        array is "rolled left", and the new ping is added at the end of the array. This
        feature is intended to support streaming data sources such as telegram
        broadcasts and the client/server interface.

        chunk_width specifies the number of columns to add to data arrays when they
        fill up when rolling == False.


        When allow_pulse_length_change == False (default) we emit a warning and return
        false when append is called with a datagram that has a different pulse length
        than the existing data. If allow_pulse_length_change == True, we will resize the
        data arays to the specified pulse length resolution in target_pulse_length if provided
        or we will resize everything to the resolution of the initial ping. More details are in
        the append method. The units of target_pulse_length are seconds.



        '''
        self.data_attributes = ['transducer_depth', 'frequency', 'transmit_power', \
                'pulse_length', 'bandwidth', 'sample_interval', 'sound_velocity',  \
                'absorption_coefficient', 'heave', 'pitch', 'roll', 'temperature', \
                'heading', 'transmit_mode', 'sample_offset', 'sample_count', 'power', \
                'angles_alongship_e', 'angles_athwartship_e']

        #  we can come up with a better name, but this specifies if we have a fixed data
        #  array size and roll it when it fills or if we expand the array when it fills
        self.rolling_array = bool(rolling)

        #  raw_file_data is a list of RawFileData objects, one for each file that
        #  has been appended to the dataset stored in this object.
        self.raw_file_data = []

        #  current_file is the index into raw_file_data
        self.current_file = -1

        #  the channel ID is the unique identifier
        self.channel_id = channel_id

        #  a counter incremented when a ping is added
        self.n_pings = 0

        #  specify the horizontal size (columns) of the array allocation size.
        self.chunk_width = chunk_width

        #  the following are all 1D arrays that are n_pings long

        #  ping_number is the sequential number of pings for this channel starting at 0 (?)
        self.ping_number = []

        #  the logging PC time that is read from the datagram header of the sample datagram
        self.ping_time = []

        #  the index into raw_file_data to the specific RawDataFile object for each ping.
        self.data_file_id = []

        #TODO replace lists with array.array, faster, less mem.  Need data types.
        self.transducer_depth = []
        self.frequency = []
        self.transmit_power = []
        self.pulse_length = []
        self.bandwidth = []
        self.sample_interval = []
        self.sound_velocity = []
        self.absorption_coefficient = []
        self.heave = []
        self.pitch = []
        self.roll = []
        self.temperature = []
        self.heading = []
        # transmit mode: 0-Active, 1-Passive, 2-Test, -1-Unknown
        self.transmit_mode = []
        #  what is the sample offset? Anyone?
        self.sample_offset =  []
        #  the number of samples in a ping
        self.sample_count = []


        #  check if we need to initialize our fixed arrays
        if (self.rolling_array):
            #  create acoustic data arrays and fill with NaNs
            self.power = np.empty(n_samples, n_pings)
            self.power.fill(np.nan)
            self.angles_alongship_e = np.empty(n_samples, n_pings)
            self.angles_alongship_e.fill(np.nan)
            self.angles_athwartship_e = np.empty(n_samples, n_pings)
            self.angles_athwartship_e.fill(np.nan)
        else:
            #  delay array creation until first ping is added
            self.power = None
            self.angles_alongship_e = None
            self.angles_athwartship_e = None


        #  create a logger instance
        self.logger = logging.getLogger('EK60RawData')


    def add_data_file(self, filename):
        '''
        add_data_file is called before adding pings from a new raw data file. It creates
        a RawDataFile object, populates it, appends it to the raw_file_data list, and updates
        the current_file pointer.

        As pings are appended, the current_file pointer is appended to the data_file_id
        vector so we can track which pings came from which file and access the config
        parameters (if needed).

        '''

        self.raw_file_data.append(RawFileData(filename))
        self.current_file += 1


    def append_ping(self, sample_datagram):
        '''
        append_ping is called when adding a ping's worth of data to the object. It should accept
        the parsed values from the sample datagram. It will handle the details of managing
        the array sizes, resizing as needed (or rolling in the case of a fixed size). Append ping also
        updates the RawFileData object's end_ping and end_time values for the current file.

        append_ping will return True if the operation was successful and False if it failed. It
        should also emit a warning if it fails.

        9/28 - Contrary to my previous thought, we will not resample raw data when appending
                 data. We will allow data with different pulse_lengths to be appended, resizing
                 and padding as needed but we will not resample. Resampling will be done when
                 calling the To* methods.

        Managing the data array sizes is the bulk of what this method does. It will either resize
        the array is rolling == false or roll the array if it is full and rolling == true.

        The data arrays will change size in 2 ways:

            Adding pings will add columns (or roll the array if all of the columns are filled and
            rolling == true.) This can easily be handled by allocating columns in chunks using
            the resize method of the numpy array and maintaining an index into
            the *next* available column (self.n_pings). Empty pings can be left uninitialized (if
            that is possible with resize) or set to NaN if it is free. If it takes additional steps to
            set to NaN, then just leave them at the default value.

            Changing the recording range or pulse length will either require adding rows (if there
            are more samples) or padding (if there are fewer. If rows are added to the array,
            existing pings will need to be padded with NaNs.

        If rolling == true, we will never resize the array. If a ping has more samples than the
        array has allocated the extra samples will be dropped. In all cases if a ping has fewer
        samples than the array has allocated it should be padded with NaNs.


        We can use the resize method of a numpy array to extend the arrays in chunks
        when they fill up during reading. resize should attempt to resize in place,
        which would is going to be faster and more efficient than anything we could do.
        https://docs.scipy.org/doc/numpy/reference/generated/numpy.ndarray.resize.html#numpy.ndarray.resize

        When we have a fixed buffer size (rolling == True) we can use the roll method to
        shift the data in the array left when it fills up.
        https://docs.scipy.org/doc/numpy-1.13.0/reference/generated/numpy.roll.html#numpy.roll


        '''


        success = True

        #  handle intialization of data arrays on our first ping
        if (self.n_pings == 0 and self.rolling_array == False):
            #  assume the initial array size doesn't involve resizing
            data_dims = [ self.chunk_width, len(sample_datagram['power'])]

            #  create acoustic data arrays - no need to fill with NaNs at this point
            self.power = np.empty(data_dims)
            self.angles_alongship_e = np.empty(data_dims)
            self.angles_athwartship_e = np.empty(data_dims)


        #  append the index into self.raw_file_data to the current RawFileData object
        self.data_file_id.append(self.current_file)

        #  append the data in sample_datagram to our internal arrays
        self.append_data(sample_datagram)


        #  check if power or angle data needs to be padded or trimmed
        #  FIXME how to determine this.


        #  increment the ping counter
        self.end_ping = self.n_pings #FIXME What should this be?
        self.end_time = sample_datagram['ping_time']


        #  check if our 2d arrays need to be resized
        if self.n_pings >= len(self.power):
            self.resize_array(sample_datagram)

        #  and finally copy the data into the arrays
        self.power[self.n_pings-1,:] = sample_datagram['power']
        #FIXME Add these to the sample datagram.
        #self.angles_alongship_e[self.n_pings-1,:] = sample_datagram['angles_alongship_e']
        #self.angles_athwartship_e[self.n_pings-1,:] = sample_datagram['angles_athwartship_e']

        return success


    def append_data_new(self, datagram):
        appended_data = defaultdict()
        try:
            for attribute, data in self.get_data():
                if attribute in datagram:
                    if isinstance(data, list):
                        appended_data[attribute] = getattr(self, attribute).append(datagram[attribute])
                    elif isinstance(data, np.ndarray):
                        appended_data[attribute] = np.concatenate((getattr(self, attribute), datagram[attribute]))
        except Exception as err:
            #TODO Add filename and ping num in file.
            log.warning("Error appending ping data.", err)
        else:
            self.ping_number.append(self.n_pings + 1)
            self.n_pings += 1
            for attribute, data in appended_data:
                setattr(self, attribute, data)


    def append_data(self, datagram):
        # FIXME define these attributes in one place to be used here and in parsers.py
        # FIXME or loop through checking key each time
        # or throw error if attr is missing

        try:
            ping_time = self.ping_time.copy()
            ping_time.append(datagram['ping_time'])
            transducer_depth = self.transducer_depth.copy()
            transducer_depth.append(datagram['transducer_depth'])
            frequency = self.frequency.copy()
            frequency.append(datagram['frequency'])
            transmit_power = self.transmit_power.copy()
            transmit_power.append(datagram['transmit_power'])
            pulse_length = self.pulse_length.copy()
            pulse_length.append(datagram['pulse_length'])
            bandwidth = self.bandwidth.copy()
            bandwidth.append(datagram['bandwidth'])
            sample_interval = self.sample_interval
            sample_interval.append(datagram['sample_interval'])
            sound_velocity = self.sound_velocity
            sound_velocity.append(datagram['sound_velocity'])
            absorption_coefficient = self.absorption_coefficient
            absorption_coefficient.append(datagram['absorption_coefficient'])
            heave = self.heave
            heave.append(datagram['heave'])
            pitch = self.pitch
            pitch.append(datagram['pitch'])
            roll = self.roll
            roll.append(datagram['roll'])
            temperature = self.temperature
            temperature.append(datagram['temperature'])
            heading = self.heading
            heading.append(datagram['heading'])
            transmit_mode = self.transmit_mode
            transmit_mode.append(datagram['transmit_mode'])
            #self.sample_offset.append(datagram['sample_offset'])
            #self.sample_count.append(datagram['sample_count'])
        except KeyError as err:
            #TODO Add filename and ping num in file.
            log.warning("The key, %s, wasn't found in the sample datagram.  This datagram will not be included.", err)
        else:
            self.ping_number.append(self.n_pings + 1)
            self.n_pings += 1
            self.ping_time = ping_time.copy()
            self.transducer_depth = transducer_depth.copy()
            self.frequency = frequency.copy()
            self.transmit_power = transmit_power.copy()
            self.pulse_length = pulse_length.copy()
            self.bandwidth = bandwidth.copy()
            self.sample_interval = sample_interval.copy()
            self.sound_velocity = sound_velocity.copy()
            self.absorption_coefficient = absorption_coefficient.copy()
            self.heave = heave.copy()
            self.pitch = pitch.copy()
            self.roll = roll.copy()
            self.temperature = temperature.copy()
            self.heading = heading.copy()
            self.transmit_mode = transmit_mode.copy()


    def resize_array(self, datagram):
        new_array_length = len(self.power) + self.chunk_width
        new_array_width = max([self.power[0].size, len(datagram['power'])])
        new_data_dims = [new_array_length, new_array_width]

        try:
            self.power.resize(new_data_dims)
            #self.angle_alongship_e.resize(new_data_dims)
            #self.angles_athwartship_e.resize(new_data_dims)
        except ValueError as err:
            log.error('Error resizing numpy array:', err)
            success = False
        except Exception as err:
            log.error('Error resizing numpy array:', type(err), err)
            success = False

    def append_raw_data(self):
        '''
        append_raw_data would append another RawData object to this one. This would call
        insert_raw_data specifying the end ping number
        '''
        #FIXME how is this different?
        self.append_ping(datagram)
        pass


    def delete_pings(self, remove=True, **kwargs):
        '''
        delete_pings deletes ping data defined by the start and end bounds.

        If remove == True, the arrays are shrunk. If remove == False, the data
        defined by the start and end are set to NaN
        '''

        #  get the horizontal start and end indicies
        h_index = self.get_indices(**kwargs)

    def get_data(self):
        for attribute, data in self:
            if attribute in self.data_attributes:
                yield (attribute, data)


    def insert_raw_data(self, raw_data_obj, ping_number=None, ping_time=None):
        '''
        insert_raw_data would insert the contents of another RawData object at the specified location
        into this one

        the location should be specified by either ping_number or ping_time

        '''
        if ping_number is None and ping_time is None:
            raise ValueError('Either ping_number or ping_time needs to be defined.')

        idx = self.get_index(time=ping_time, ping=ping_number)
        if idx <= self.n_pings - 1:
            for attribute, data in self.get_data():
                #TODO Do we want to make sure all data arrays are the same length?
                #TODO Do we want to wait to add the data until we've made sure all the data is good to avoid misalignment?
                try:
                    data_to_insert = getattr(raw_data_obj, attribute)
                except Exception as err:
                    log.error('Error reading data from raw_data_obj, ', raw_data_obj, attribute, ': ',  type(err), err)
                    return
                data_before_insert = data[0:idx] #Data up to index before idx.
                data_after_insert = data[idx:]


                if isinstance(data, list):
                    new_data = data_before_insert + data_to_insert + data_after_insert
                    setattr(self, attribute, new_data)
                elif isinstance(data, np.ndarray):
                    new_data = np.concatenate((data_before_insert, data_to_insert, data_after_insert))
                    setattr(self, attribute, new_data)


    def trim(self):
        '''
        trim deletes the empty portions of pre-allocated arrays. This should be called
        when you are done adding pings to a non-rolling raw_data instance.
        '''
        pass


    def get_index(self, time=None, ping=None):

        def nearest_idx(list, value):
            '''
            return the index of the nearest value in a list.
            Adapted from: https://stackoverflow.com/questions/32237862/find-the-closest-date-to-a-given-date
            '''
            return list.index(min(list, key=lambda x: abs(x - value)))

        #  check if we have an start time defined and determine index
        if (ping == None and time == None):
            index = 0
        elif (ping == None):
            #  start must be defined by time
            #  make sure we've been passed a datetime object defining the start time
            if (not type(time) is datetime.datetime):
                raise TypeError('time must be a datetime object.')

            #  and find the index of the closest ping_time
            index = nearest_idx(self.ping_time, time)
        else:
            #  ping must have been provided
            #  make sure we've been passed an integer defining the start ping
            ping = int(ping)
            if (not type(ping) is int):
                raise TypeError('ping must be an Integer.')

            #  and find the index of the closest ping_number
            index = nearest_idx(self.ping_number, ping)

        return (index)


    def get_indices(self, start_ping=None, end_ping=None, start_time=None, end_time=None):
        '''
        get_indices maps ping number and/or ping time to an index into the acoustic
        data arrays.

        This should be extended to handle sample_start/sample_end, range_start/range_end
        but this would require calculating range if range was provided. Not a big deal,
        but there will need to be some mechanics to determine if range has been calculated
        and if it is still valid (i.e. no data has changed that would null the cached range
        data)

        '''

        def nearest_idx(list, value):
            '''
            return the index of the nearest value in a list.
            Adapted from: https://stackoverflow.com/questions/32237862/find-the-closest-date-to-a-given-date
            '''
            return list.index(min(list, key=lambda x: abs(x - value)))

        #  check if we have an start time defined and determine index
        if (start_ping == None and start_time == None):
            start_index = 0
        elif (start_ping == None):
            #  start must be defined by start_time
            #  make sure we've been passed a datetime object defining the start time
            if (not type(start_time) is datetime.datetime):
                raise TypeError('start_time must be a datetime object.')

            #  and find the index of the closest ping_time
            start_index = nearest_idx(self.ping_time, start_time)
        else:
            #  start_ping must have been provided
            #  make sure we've been passed an integer defining the start ping
            start_ping = int(start_ping)
            if (not type(end_ping) is int):
                raise TypeError('start_ping must be an Integer.')

            #  and find the index of the closest ping_number
            start_index = nearest_idx(self.ping_number, start_ping)

        #  check if we have an end time defined and determine index
        if (end_ping == None and end_time == None):
            end_index = -1
        elif (end_ping == None):
            #  start must be defined by end_time
            #  make sure we've been passed a datetime object defining the end time
            if (not type(end_time) is datetime.datetime):
                raise TypeError('end_time must be a datetime object.')

            #  and find the index of the closest ping_time
            end_index = nearest_idx(self.ping_time, end_time)
        else:
            #  end_ping must have been provided
            #  make sure we've been passed an integer defining the end ping
            end_ping = int(end_ping)
            if (not type(end_ping) is int):
                raise TypeError('end_ping must be an Integer.')

            #  and find the index of the closest ping_number
            end_index = nearest_idx(self.ping_number, end_ping)

        #  make sure the indices are sane
        if (start_index > end_index):
            raise ValueError('The end_ping or end_time provided comes before ' +
                    'the start_ping or start_time.')

        return (start_index, end_index)


    def get_sv(self, cal_parameters=None, linear=False, **kwargs):
        '''
        get_sv returns a ProcessedData object containing Sv (or sv if linear is
        True).

        MATLAB readEKRaw eq: readEKRaw_Power2Sv.m

        The value passed to cal_parameters is a calibration parameters object.
        If cal_parameters == None, the calibration parameters will be extracted
        from the corresponding fields in the raw_data object.




                    add rows. This will present itself as a datagram that
            has the same pulse_length but more samples. In this case we resize the array
            vertically. Same goes in terms of resizing in the most efficient way with one important
            difference: empty array elements of *existing pings* must be set to NaN.

            The last way the arrays will (possibly) change sizes is if the pulse_length changes.
            pulse_length directly effects the vertical "resolution". Since vetical resolution must be
            fixed within the 2d data arrays, we will deal with this in a couple of ways:

                if self.allow_pulse_length_change == False we will simply issue a warning and return
                False.

                if self.allow_pulse_length_change == True and self.target_pulse_length == None we
                will resample the data to the resolution of the first ping in our data arrays.

                if self.allow_pulse_length_change == True and self.target_pulse_length != None we
                will resample *all* of the data to the resolution specified by self.target_pulse_length.
                The value specified by target_pulse_length must be a valid pulse length.

                EK/ES60 ES70 pulse lengths in us: [256, 512, 1024, 2048, 4096]
                there are always 4 samples per pulse in time
                sample resolution in us by pulse length [64, 128, 256, 512, 1024]


                   ####  pulse_length units are seconds in the raw data ####



        '''

        #  get the horizontal start and end indicies
        h_index = self.get_indices(**kwargs)


    def get_ts(self, cal_parameters=None, linear=False, **kwargs):
        '''
        get_ts returns a ProcessedData object containing TS (or sigma_bs if linear is
        True). (in MATLAB code TS == Sp and sigma_bs == sp)

        MATLAB readEKRaw eq: readEKRaw_Power2Sp.m

        The value passed to cal_parameters is a calibration parameters object.
        If cal_parameters == None, the calibration parameters will be extracted
        from the corresponding fields in the raw_data object.

        '''

        #  get the horizontal start and end indicies
        h_index = self.get_indices(**kwargs)


    def get_physical_angles(self, **kwargs):
        '''
        get_physical_angles returns a processed data object that contains the alongship and
        athwartship angle data.

        This method would call getElectricalAngles to get a vertically aligned

        '''

    def get_power(self, **kwargs):
        '''
        get_power returns a processed data object that contains the power data.

        This method will vertically resample the raw power data according to the keyword inputs.
        By default we will resample to the highest resolution (shortest pulse length) in the object.

        resample = RawData.to_shortest

        '''





    def get_electrical_angles(self, **kwargs):
        '''
        '''

    def __iter__(self):
        for attribute in vars(self).keys():
            yield (attribute, getattr(self, attribute))



    def __resample_data(self, data, pulse_length, target_pulse_length, is_power=False):
        '''
        __resample_data returns a resamples the power or angle data based on it's pulse length
        and the provided target pulse length. If is_power is True, we log transform the
        data to average in linear units (if needed).

        The funtion returns the resized array.
        '''

        #  first make sure we need to do something
        if (pulse_length == target_pulse_length):
            #  nothing to do, just return the data unchanged
            return data

        if (target_pulse_length > pulse_length):
            #  we're reducing resolution - determine the number of samples to average
            sample_reduction = int(target_pulse_length / pulse_length)

            if (is_power):
                #  convert *power* to linear units
                data = np.power(data/20.0, 10.0)

            # reduce
            data = np.mean(data.reshape(-1, sample_reduction), axis=1)

            if (is_power):
                #  convert *power* back to log units
                data = 20.0 * np.log10(data)

        else:
            #  we're increasing resolution - determine the number of samples to expand
            sample_expansion = int(pulse_length / target_pulse_length)

            #  replicate the values to fill out the higher resolution array
            data = np.repeat(data, sample_expansion)


        #  update the pulse length and sample interval values
        data['pulse_length'] = target_pulse_length
        data['sample_interval'] = target_pulse_length / self.SAMPLES_PER_PULSE

        return data


#        #  handle intialization on our first ping
#        if (self.n_pings == 0):
#            #  assume the initial array size doesn't involve resizing
#            data_dims = [ len(sample_datagram['power']), self.chunk_width]
#
#            #  determine the target pulse length and if we need to resize our data right off the bat
#            #  note that we use self.target_pulse_length to store the pulse length of all data in the
#            #  array
#            if (self.target_pulse_length == None):
#                #  set the target_pulse_length to the pulse length of this initial ping
#                self.target_pulse_length = sample_datagram['pulse_length']
#            else:
#                #  the vertical resolution has been explicitly specified - check if we need to resize right off the bat
#                if (self.target_pulse_length != sample_datagram['pulse_length']):
#                    #  we have to resize - determine the new initial array size
#                    if (self.target_pulse_length > sample_datagram['pulse_length']):
#                        #  we're reducing resolution
#                        data_dims[0] = data_dims[0]  / int(self.target_pulse_length /
#                                sample_datagram['pulse_length'])
#                    else:
#                        #  we're increasing resolution
#                        data_dims[0] = data_dims[0]  * int(sample_datagram['pulse_length'] /
#                                self.target_pulse_length)
#
#            #  allocate the initial arrays if we're *not* using a rolling buffer
#            if (self.rolling == False):
#                #  create acoustic data arrays - no need to fill with NaNs at this point
#                self.power = np.empty(data_dims)
#                self.angles_alongship_e = np.empty(data_dims)
#                self.angles_alongship_e = np.empty(data_dims)
#
#        #  if we're not allowing pulse_length to change, make sure it hasn't
#        if (not self.allow_pulse_length_change) and (sample_datagram['pulse_length'] != self.target_pulse_length):
#            self.logger.warning('append_ping failed: pulse_length does not match existing data and ' +
#                    'allow_pulse_length_change == False')
#            return False
#
#
#        #  check if any resizing needs to be done. The data arrays can be full (all columns filled) and would then
#        #  need to be expanded horizontally. The new sample_data vector could be longer with the same pulse_length
#        #  meaning the recording range has changed so we need to expand vertically and set the new data for exitsing
#        #  pings to NaN.
#
#        #  it is also possible that the incoming power or angle array needs to be padded with NaNs if earlier pings
#        #  were recorded to a longer range.
#
#        #  lastly, it is possible that the incoming power/angle arrays need to be trimmed if we're using a rolling
#        #  buffer where the user has set a hard limit on the vertical extent of the array.
#
#
#        #  check if our pulse length has changed
#        if (self.n_pings > 0) and (sample_datagram['pulse_length'] != self.pulse_length[self.n_pings-1]):
#            if (self.allow_pulse_length_change):
#                #  here we need to change the vertical resolution of either the incoming data or the data
#                if (sample_datagram['power']):
#                    sample_datagram['power'] = resample_data(sample_datagram['power'],
#                            sample_datagram['pulse_length'], self.target_pulse_length, is_power=True)
#                if (sample_datagram['angle_alongship_e']):
#                    sample_datagram['angle_alongship_e'] = resample_data(sample_datagram['angle_alongship_e'],
#                            sample_datagram['pulse_length'], self.target_pulse_length)
#                if (sample_datagram['angle_athwartship_e']):
#                    sample_datagram['angle_athwartship_e'] = resample_data(sample_datagram['angle_athwartship_e'],
#                            sample_datagram['pulse_length'], self.target_pulse_length)

