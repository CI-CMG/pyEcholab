# coding=utf-8
'''

Last updated 9/25/17 - RHT

This file contains sketches of classes which will define much of the "public" API
of pyEcholab2. This is not a final specification. Names and methods may/will change
based on input from you all.

I have just started to add specifications for the reader class. Still a work in progress.

In general I see these pieces fitting together something like:

Reader handles file IO. It opens a file and determines the number of channels in
the file by reading the CON0 header. It then creates a RawData object for each channel,
sticking them in a dictionary keyed by channel ID. It then calls the AppendFile
method of each RawData object, passing the full file path and the data from the CON0
datagram. Then the reader reads the datagrams and calls RawData.AppendPing for
each channel passing the ping data. AppendPing will determine if any array resizing
needs to be done (for example if the range has increased or we have filled all of the
array columns and need to allocate more columns) and then it will populate the various
RawData properties with that ping's data. If a new file is opened, it would again
call the RawData.AppendFile method, and then append the pings from that file. When
all files have been read, the RawData.Trim method would be called to clip unused
portions of the data arrays (since we allocate in chunks).




Terminology:

These aren't meant to be 100% technically correct, just enough to help Pamme navigate
the jargon. Some are probably obvious

recording PC:
    the computer that runs the Simrad software used to operate the sonar
    and write data files. The recording PC will have hardware connected to it
    that comprise one or more "channels".

PC time:
    the recording PC's clock time converted to GMT using the PC's local time and
    time zone. This is what is stored in the datagram headers. This time may or may not
    be correct in that it can drift from a valid reference time. This time can also be
    incorrect if the time zone is set incorrectly. This clock can be changed by the user
    while data is being recorded.

channel:
    a sonar data source. Regardless of the hardware details, a channel is the data from
    some hunks of ceramic that are vibrated in a certain way to project sound into the
    water column and then they "listen" for that sound to be reflected back.

channel_id:
    channel_id is just a unique identifier for a channel. We may use the terms channel
    and channel_id interchangibly.

    These are from what Simrad calls their "General Purpose Transceiver" or GPT which
    inlcludes the EK60, ES60, and ES70 systems. They include the name, frequency,
    MAC address of the sonar hardware, beam information, and transducer information.

    GPT  38 kHz 009072033fa2 1-1 ES38B
    GPT  38 kHz 009072034283 1 ES38B
    GPT 120 kHz 00907205794e 5-1 ES120-7C

    These are examples from the ME70 multibeam system. They include the beam number,
    frequency, and alongship and athwartship beam :angles

    MBES-00 73 kHz x=0 y=-66
    MBES-19 106 kHz x=0 y=12
    MBES-30 75 kHz x=0 y=66

    channel_id will be a fixed string of 128 bytes. It should be trimmed to remove the trailing
    whitespace.

frequency:
    we will always specify frequency in Hz. While frequency is often used to differentiate
    channels, and often all channels in a file will have unique frequencies, there is no
    guarantee that it will be unique in a file.

split-beam vs single beam:

    single-beam sonars listen to the whole transducer at once and only can provide
    power data since they lack the circuitry to "triangulate" the location of the target in the
    beam thus they will not have angle data.

    split-beam systems listen independently in 3 or 4 quadrants of the transducer and using this
    phase information can "triangulate" the direction (angle alongship and angle athwartship) to the
    target in each sample. split-beam systems will have angle data available.

    For volume backscatter (Sv or sv), the "split-beam" capability is not utilized and all 3 or 4
    quadrants are summed analoguous to the single-beam systems. This is the "power" output by the
    Simrad echosounders.

    I believe that this is specified by the "beamtype"

pulse_length:

    the length in time (seconds) of the transmit pulse. This basically defines the sonars vertical
    resolution. The EK/ES 60 and ES70 take 4 samples per pulse_length interval.

sample_interval:

    the time in seconds that 1 sample spans. Since the EK/ES60 and ES70 take 4 samples per
    pulse length interval, the sample interval is equal to the pulse_length / 4.0. When creating
    processed data arrays, we must ensure that the sample interval is the same for all pings.



Random thoughts:

The reader's read and append methods should accept a callback function handle
that will be called with the estimated progress %. This will allow applicaitons
to provide feedback to the user as to the progress of the reading.


'''

from raw_file import RawSimradFile, SimradEOF
from util.date_conversion import nt_to_unix, unix_to_nt

import os
import datetime
import logging
import numpy as np


class EK60Reader(object):

    def __init__(self, power=True,  angles=True,  max_sample_range=None,  start_time=None,
            end_time=None,  start_ping=None,  end_ping=None,  frequencies=None,  channels=None):

        #  define a subset of data to read using time - if no times are provided read all data
        self.start_time = start_time
        self.end_time = end_time

        #  define a subset of data to read using ping number - if no values are provided read all data
        self.start_ping = start_ping
        self.end_ping = end_ping

        #  specify if we should read/store power data
        self.read_power = power

        #  specify if we should read/store angles data
        self.read_angles = angles

        #  specify a max sample range to read - samples beyond this are dropped
        #  if max_sample_range == None all samples are read
        self.max_sample_range = max_sample_range

        #  specify the frequencies to read. This could
        self.frequencies = frequencies

        #  a dictionary to store the EK60RawData objects
        self.raw_data = {}


    def read_file(self, filename):

        datagrams = {}

        with RawSimradFile(filename, 'r') as fid:

            config_datagrams = {}
            while fid.peek()['type'].startswith('CON'):
                config_datagram = fid.read(1)
                if config_datagram['type'] in config_datagrams:
                    raise ValueError('Multiple config datagrams of type %s found', config_datagram['type'])
                config_datagrams[config_datagram['type']] = config_datagram

            while True:
                try:
                    next_header = fid.peek()
                except SimradEOF:
                    break

                datagram_timestamp = nt_to_unix((next_header['low_date'], next_header['high_date']))

                try:
                    new_datagram = fid.read(1)
                except SimradEOF:
                    break

                

                if 'channel' in new_datagram:

                    channel = new_datagram['channel']
                    if channel not in self.raw_data.keys():
                        self.raw_data[channel] = EK60RawData(channel)


                    ping_times = getattr(self.raw_data[channel], 'ping_time')
                    ping_times.append(datagram_timestamp)
                    setattr(self.raw_data[channel], 'ping_time', ping_times)


                    for key in new_datagram: #TODO parsers.py _unpack_contents directly into data object?
                        if hasattr(self.raw_data[channel], key):
                            attr_data = getattr(self.raw_data[channel], key)
                            if isinstance(attr_data, list):
                                attr_data.append(new_datagram[key])
                                setattr(self.raw_data[channel], key, attr_data)
                            else:
                                setattr(self.raw_data[channel], key, new_datagram[key])


        print(self.raw_data)

        return self.raw_data


    def append(self):
        pass



class RawFileData(object):
    '''
    RawFileData (final name TBD) is a class which stores the channel configuration
    data (the ConfigurationTransducer struct) as well as some metadata about the file.
    One of these is created for all unique channels for every file read.

    These objects are stored in a list in the raw_data class.

    Note that I have not fleshed out a way to populate these data fields beyond the
    filename. Additional arguments could be added to the init method or they
    could be updated after instantiation by directly accessing the properties or
    other methods could be added.
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

        #  each property below should have a comment explaining what it is
        #  this should be in the docs?

        self.beam_type = 0

        #  the channel frequency in Hz
        self.frequency = 0

        #  the system gain when the file was recorded
        self.gain = 0

        self.equivalent_beam_angle = 0
        self.beamwidth_alongship = 0
        self.beamwidth_athwartship = 0
        self.angle_sensitivity_alongship = 0
        self.angle_sensitivity_athwartship = 0
        self.angle_offset_alongship = 0
        self.angle_offset_athwartship = 0
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


class CON1Data(object):
    '''
    CON1Data (final name TBD) is a class which represents the Simrad raw file CON1
    datagram used by the ME70 and ???.

    This would be implemented when making the minor additions required to support
    the ME70.
    '''

    pass



class ProcessedData(object):
    '''
    The ProcessedData class contains
    '''

    def __init__(self, file):

        self.channel_id = ''
        self.frequency = 0
        self.sample_interval = 0
        self.range

class CalibrationParameters(object):
    '''
    The CalibrationParameters class contains parameters required for transforming
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


    def FromRawData(self, raw_data, raw_file_idx=0):
        '''
        FromRawData populated the CalibrationParameters object's properties given
        a reference to a RawData object.

        This would query the RawFileData object specified by raw_file_idx in the
        provided RawData object (by default, using the first).
        '''

        pass


    def ReadEchoviewEcsFile(self, ecs_file, channel):
        '''
        ReadEchoviewEcsFile would read an echoview ecs file and parse out the
        parameters for a given channel. This is low priority and this is really
        a place holder for an idea.
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

    to_shortest = 0
    to_longest = 1

    def __init__(self, channel_id, n_pings=500, n_samples=1000, rolling=False,
            chunk_width=500):
        '''
        Creates a new, empty RawData object.

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



        #  specify the horizontal size (cols) of the array allocation size
        self.chunk_width = chunk_width

        #  the following are all 1D arrays that are n_pings long

        #  ping_number is the sequential number of pings for this channel starting at 0 (?)
        self.ping_number = []

        #  the logging PC time that is read from the datagram header of the sample datagram
        self.ping_time = []

        #  the index into raw_file_data to the specific RawDataFile object for each ping.
        self.data_file_id = []

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


    def AppendFile(self, filename, config_data):
        '''
        AppendFile is called before adding pings from a new data file. It would create
        a RawFileData object, populate it, append it to the raw_file_data list, and update
        the current_file pointer.

        As pings are then appended, the current_file pointer is appended to the data_file_id
        vector so we can track which pings came from which file and access the config
        parameters (if needed).

        THIS PROBABLY SHOULD HAVE A DIFFERENT/BETTER NAME

        '''

        pass


    def AppendPing(self, sample_datagram):
        '''
        AppendPing is called when adding a ping's worth of data to the object. It should accept
        the parsed values from the sample datagram. It will handle the details of managing
        the array sizes, resizing as needed (or rolling in the case of a fixed size). Append ping also
        updates the RawFileData object's end_ping and end_time values for the current file.

        AppendPing will return True if the operation was successful and False if it failed. It
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

        #  handle intialization of data arrays on our first ping
        if (self.n_pings == 0 and self.rolling == False):
            #  assume the initial array size doesn't involve resizing
            data_dims = [ len(sample_datagram['power']), self.chunk_width]

            #  create acoustic data arrays - no need to fill with NaNs at this point
            self.power = np.empty(data_dims)
            self.angles_alongship_e = np.empty(data_dims)
            self.angles_athwartship_e = np.empty(data_dims)


        #  append the index into self.raw_file_data to the current RawFileData object
        self.data_file_id.append(self.current_file)

        #  append the data in sample_datagram to our internal arrays
        self.ping_number.append(self.n_pings + 1)
        self.ping_time.append(sample_datagram['ping_time'])
        self.transducer_depth.append(sample_datagram['transducer_depth'])
        self.frequency.append(sample_datagram['frequency'])
        self.transmit_power.append(sample_datagram['transmit_power'])
        self.pulse_length.append(sample_datagram['pulse_length'])
        self.bandwidth.append(sample_datagram['bandwidth'])
        self.sample_interval.append(sample_datagram['sample_interval'])
        self.sound_velocity.append(sample_datagram['sound_velocity'])
        self.absorption_coefficient.append(sample_datagram['absorption_coefficient'])
        self.heave.append(sample_datagram['heave'])
        self.pitch.append(sample_datagram['pitch'])
        self.roll.append(sample_datagram['roll'])
        self.temperature.append(sample_datagram['temperature'])
        self.heading.append(sample_datagram['heading'])
        self.transmit_mode.append(sample_datagram['transmit_mode'])
        self.sample_offset.append(sample_datagram['sample_offset'])
        self.sample_count.append(sample_datagram['sample_count'])

        #  check if power or angle data needs to be padded or trimmed

        #  check if our 2d arrays need to be resized

        #  and finally copy the data into the arrays
        self.power[:,self.n_pings] = sample_datagram['power']
        self.angles_alongship_e[:,self.n_pings] = sample_datagram['angles_alongship_e']
        self.angles_athwartship_e[:,self.n_pings] = sample_datagram['angles_athwartship_e']

        #  increment the ping counter
        self.n_pings = self.n_pings + 1

        #  obviously there is no error handling now, but this method should have some and return false if
        #  there is a problem. I think the only problem would be the inability to allocate an array when
        #  expanding.
        return True


    def AppendRawData(self):
        '''
        AppendRawData would append another RawData object to this one. This would call
        InsertRawData specifying the end ping number
        '''
        pass


    def DeletePings(self, remove=True, **kwargs):
        '''
        DeletePings deletes ping data defined by the start and end bounds.

        If remove == True, the arrays are shrunk. If remove == False, the data
        defined by the start and end are set to NaN
        '''

        #  get the horizontal start and end indicies
        h_index = self.GetIndices(**kwargs)


    def InsertRawData(self, ping_number=None, ping_time=None, **kwargs):
        '''
        InsertRawData would insert the contents of another RawData object at the specified location
        into this one

        the location should be specified by either ping_number or ping_time

        '''
        pass


    def Trim(self):
        '''
        Trim deletes the empty portions of pre-allocated arrays. This should be called
        when you are done adding pings to a non-rolling raw_data instance.
        '''
        pass


    def GetIndex(self, time=None, ping=None):

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
            if (not type(end_ping) is int):
                raise TypeError('ping must be an Integer.')

            #  and find the index of the closest ping_number
            index = nearest_idx(self.ping_number, ping)

        return (index)


    def GetIndices(self, start_ping=None, end_ping=None, start_time=None, end_time=None):
        '''
        GetIndices maps ping number and/or ping time to an index into the acoustic
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


    def GetSv(self, cal_parameters=None, linear=False, **kwargs):
        '''
        GetSv returns a ProcessedData object containing Sv (or sv if linear is
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
        h_index = self.GetIndices(**kwargs)


    def GetTs(self, cal_parameters=None, linear=False, **kwargs):
        '''
        GetTs returns a ProcessedData object containing TS (or sigma_bs if linear is
        True). (in MATLAB code TS == Sp and sigma_bs == sp)

        MATLAB readEKRaw eq: readEKRaw_Power2Sp.m

        The value passed to cal_parameters is a calibration parameters object.
        If cal_parameters == None, the calibration parameters will be extracted
        from the corresponding fields in the raw_data object.

        '''

        #  get the horizontal start and end indicies
        h_index = self.GetIndices(**kwargs)


    def GetPhysicalAngles(self, **kwargs):
        '''
        GetPhysicalAngles returns a processed data object that contains the alongship and
        athwartship angle data.

        This method would call getElectricalAngles to get a vertically aligned

        '''

    def GetPower(self, **kwargs):
        '''
        GetPower returns a processed data object that contains the power data.

        This method will vertically resample the raw power data according to the keyword inputs.
        By default we will resample to the highest resolution (shortest pulse length) in the object.

        resample = RawData.to_shortest

        '''

    def GetElectricalAngles(self, **kwargs):
        '''
        '''


class NMEAData(object):
    '''
    The NMEAData class provides storage for and parsing of NMEA data commonly
    collected along with sonar data.

    Potential library to use for NMEA parsing.
        https://github.com/Knio/pynmea2

        We can just pull something like that into this project. It doesn't have
        to be this one, and we could roll our own if needed. Just throwing it
        out there.
    '''

    #import pynmea2 FIXME Uncomment once this is available.

    def __init__(self, file):

        #  store the raw NMEA datagrams by time to facilitate easier writing
        #  raw_datagrams is a list of dicts in the form {'time':0, 'text':''}
        #  where time is the datagram time and text is the unparsed NMEA text.
        self.raw_datagrams = []
        self.n_raw = 0

        #  type_data is a dict keyed by datagram talker+message. Each element of
        #  the dict is a list of integers that are an index into the raw_datagrams
        #  list for that talker+message. This allows easy access to the datagrams
        #  by type.
        self.type_index = {}

        #  self types is a list of the unique talker+message NMEA types received.
        self.types = []

        #  create a logger instance
        self.logger = logging.getLogger('NMEAData')


    def AddDatagram(self, time, text):
        '''
        AddDatagram adds a NMEA datagram to the class. It adds it to the raw_datagram
        list as well as parsing the header and adding the talker+mesage ID to the
        type_index dict.

        time is a datetime object
        text is a string containing the NMEA text
        '''

        #  add the raw NMEA datagram
        self.raw_datagrams.append({'time':time, 'text':text})

        #  extract the header
        header = text[1:6].upper()

        #  make sure we have a plausible header
        if (header.isalpha() and len(header) == 5):
            #  check if we already have this header
            if (header not in self.types):
                #  nope - add it
                self.types.append(header)
                self.type_index[header] = []
            #  update the type_index
            self.type_index[header].append(self.n_raw)
        else:
            #  inform the user of a bad NMEA datagram
            self.logger.info('Malformed or missing NMEA header: ' + text)

        #  increment the index counter
        self.n_raw = self.n_raw + 1


    def GetDatagrams(self, type, raw=False):
        '''
        GetDatagrams returns a list of the requested datagram type. By default the
        datagram will be parsed. If raw == True the raw datagram text will be returned.
        '''

        #  make sure the type is upper case
        type = type.upper()

        #  create the return dict depending on if were returning raw or parsed
        if (raw):
            datagrams = {'type':type, 'times':[], 'text':[]}
        else:
            datagrams = {'type':type, 'times':[], 'datagram':[]}

        if (type in self.types):
            #  append the time
            datagrams['times'].append(self.raw_datagrams[type]['time'])
            if (raw):
                for dg in self.type_index[type]:
                    #  just append the raw text
                    datagrams['text'].append(self.raw_datagrams[type]['text'])
            else:
                for dg in self.type_index[type]:
                    #  parse the NMEA string using pynmea2
                    nmea_obj = pynmea2.parse(self.raw_datagrams[type]['text'])
                    datagrams['datagram'].append(nmea_obj)

        #  return the dictionary
        return datagrams



class TAGData(object):
    '''
    The TAGData class provides storage for the TAG0, aka annotations datagrams
    in Simrad .raw files.
    '''

    def __init__(self, file):

        #  store the annotation text as  a list of dicts in the form {'time':0, 'text':''}
        self.annotations = []



    def AddDatagram(self, time, text):
        '''
        AddDatagram adds a TAG0 datagram to the

        time is a datetime object
        text is a string containing the annotation text
        '''

        #  add the raw NMEA datagram
        self.annotations.append({'time':time, 'text':text})










        def resampleData(self, data, pulse_length, target_pulse_length, is_power=False):
            '''
            resampleData resamples the power or angle data based on it's pulse length
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


        #  handle intialization on our first ping
        if (self.n_pings == 0):
            #  assume the initial array size doesn't involve resizing
            data_dims = [ len(sample_datagram['power']), self.chunk_width]

            #  determine the target pulse length and if we need to resize our data right off the bat
            #  note that we use self.target_pulse_length to store the pulse length of all data in the
            #  array
            if (self.target_pulse_length == None):
                #  set the target_pulse_length to the pulse length of this initial ping
                self.target_pulse_length = sample_datagram['pulse_length']
            else:
                #  the vertical resolution has been explicitly specified - check if we need to resize right off the bat
                if (self.target_pulse_length != sample_datagram['pulse_length']):
                    #  we have to resize - determine the new initial array size
                    if (self.target_pulse_length > sample_datagram['pulse_length']):
                        #  we're reducing resolution
                        data_dims[0] = data_dims[0]  / int(self.target_pulse_length /
                                sample_datagram['pulse_length'])
                    else:
                        #  we're increasing resolution
                        data_dims[0] = data_dims[0]  * int(sample_datagram['pulse_length'] /
                                self.target_pulse_length)

            #  allocate the initial arrays if we're *not* using a rolling buffer
            if (self.rolling == False):
                #  create acoustic data arrays - no need to fill with NaNs at this point
                self.power = np.empty(data_dims)
                self.angles_alongship_e = np.empty(data_dims)
                self.angles_alongship_e = np.empty(data_dims)

        #  if we're not allowing pulse_length to change, make sure it hasn't
        if (not self.allow_pulse_length_change) and (sample_datagram['pulse_length'] != self.target_pulse_length):
            self.logger.warning('AppendPing failed: pulse_length does not match existing data and ' +
                    'allow_pulse_length_change == False')
            return False


        #  check if any resizing needs to be done. The data arrays can be full (all columns filled) and would then
        #  need to be expanded horizontally. The new sample_data vector could be longer with the same pulse_length
        #  meaning the recording range has changed so we need to expand vertically and set the new data for exitsing
        #  pings to NaN.

        #  it is also possible that the incoming power or angle array needs to be padded with NaNs if earlier pings
        #  were recorded to a longer range.

        #  lastly, it is possible that the incoming power/angle arrays need to be trimmed if we're using a rolling
        #  buffer where the user has set a hard limit on the vertical extent of the array.


        #  check if our pulse length has changed
        if (self.n_pings > 0) and (sample_datagram['pulse_length'] != self.pulse_length[self.n_pings-1]):
            if (self.allow_pulse_length_change):
                #  here we need to change the vertical resolution of either the incoming data or the data
                if (sample_datagram['power']):
                    sample_datagram['power'] = resampleData(sample_datagram['power'],
                            sample_datagram['pulse_length'], self.target_pulse_length, is_power=True)
                if (sample_datagram['angle_alongship_e']):
                    sample_datagram['angle_alongship_e'] = resampleData(sample_datagram['angle_alongship_e'],
                            sample_datagram['pulse_length'], self.target_pulse_length)
                if (sample_datagram['angle_athwartship_e']):
                    sample_datagram['angle_athwartship_e'] = resampleData(sample_datagram['angle_athwartship_e'],
                            sample_datagram['pulse_length'], self.target_pulse_length)
