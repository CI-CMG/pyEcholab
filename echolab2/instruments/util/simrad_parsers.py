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

"""
.. module:: echolab2.instruments.util.simrad_parsers

    :synopsis: Parsers for Simrad raw file datagrams

| Developed by:  Zac Berkowitz <zac.berkowitz@gmail.com> under contract for
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assesment and Conservation Engineering Group (MACE)
|
|
| Authors:
|       Zac Berkowitz <zac.berkowitz@gmail.com>
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import sys
import struct
import re
import numpy as np
from collections import OrderedDict
from lxml import etree as ET
from .date_conversion import nt_to_unix


__all__ = ['SimradNMEAParser', 'SimradDepthParser', 'SimradBottomParser',
            'SimradAnnotationParser', 'SimradConfigParser', 'SimradRawParser',
            'SimradFILParser', 'SimradXMLParser', 'SimradMRUParser']


class _SimradDatagramParser(object):
    '''
    '''

    def __init__(self, header_type, header_formats):
        self._id      = header_type
        self._headers = header_formats
        self._versions    = list(header_formats.keys())

    def header_fmt(self, version=0):
        return '=' + ''.join([x[1] for x in self._headers[version]])

    def header_size(self, version=0):
        return struct.calcsize(self.header_fmt(version))

    def header_fields(self, version=0):
        return [x[0] for x in self._headers[version]]

    def header(self, version=0):
        return self._headers[version][:]


    def validate_data_header(self, data):

        if isinstance(data, dict):
            type_ = data['type'][:3]
            version   = int(data['type'][3])

        elif isinstance(data, str):
            type_ = data[:3]
            version   = int(data[3])

        elif isinstance(data, unicode):
            data = str(data)
            type_ = data[:3]
            version   = int(data[3])

        else:
            raise TypeError('Expected a dict or str')

        if type_ != self._id:
            raise ValueError('Expected data of type %s, not %s' %(self._id, type_))

        if version not in self._versions:
            raise ValueError('No parser available for type %s version %d' %(self._id, version))

        return type_, version

    def from_string(self, raw_string, bytes_read):

        header = raw_string[:4]
        header = header.decode()
        id_, version = self.validate_data_header(header)
        return self._unpack_contents(raw_string, bytes_read, version=version)

    def to_string(self, data={}):

        id_, version = self.validate_data_header(data)
        datagram_content_str = self._pack_contents(data, version=version)
        return self.finalize_datagram(datagram_content_str)

    def _unpack_contents(self, raw_string='', version=0):
        raise NotImplementedError

    def _pack_contents(self, data={}, version=0):
        raise NotImplementedError

    @classmethod
    def finalize_datagram(cls, datagram_content_str):
        datagram_size = len(datagram_content_str)
        final_fmt = '=l%dsl' % (datagram_size)
        return struct.pack(final_fmt, datagram_size, datagram_content_str, datagram_size)


class SimradDepthParser(_SimradDatagramParser):
    '''
    ER60 Depth Detection datagram (from .bot files) contain the following keys:

        type:         string == 'DEP0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:    datetime.datetime object of NT date, assumed to be UTC
        transceiver_count:  [long uint] with number of tranceivers

        depth:        [float], one value for each active channel
        reflectivity: [float], one value for each active channel
        unused:       [float], unused value for each active channel

    The following methods are defined:

        from_string(str):    parse a raw ER60 Depth datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk

    '''
    def __init__(self):
        headers = {0: [('type', '4s'),
                       ('low_date', 'L'),
                       ('high_date', 'L'),
                       ('transceiver_count', 'L')
                      ]
                  }
        _SimradDatagramParser.__init__(self, "DEP", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''

        '''

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        if version == 0:
            data_fmt    = '=3f'
            data_size   = struct.calcsize(data_fmt)

            data['depth'] = np.zeros((data['transceiver_count'],))
            data['reflectivity'] = np.zeros((data['transceiver_count'],))
            data['unused'] = np.zeros((data['transceiver_count'],))

            buf_indx     = self.header_size(version)
            for indx in range(data['transceiver_count']):
                d, r, u = struct.unpack(data_fmt, raw_string[buf_indx:buf_indx + data_size])
                data['depth'][indx]         = d
                data['reflectivity'][indx]  = r
                data['unused'][indx]        = u

                buf_indx += data_size

        return data

    def _pack_contents(self, data, version):

        datagram_fmt      = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            lengths = [len(data['depth']), len(data['reflectivity']), len(data['unused']), data['transceiver_count']]

            if len(set(lengths)) != 1:
                min_indx = min(lengths)
#                log.warning('Data lengths mismatched:  d:%d, r:%d, u:%d, t:%d',
#                    *lengths)
#                log.warning('  Using minimum value:  %d', min_indx)
                data['transceiver_count'] = min_indx

            else:
                min_indx = data['transceiver_count']

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            datagram_fmt += '%df' % (3*data['transceiver_count'])

            for indx in range(data['transceiver_count']):
                datagram_contents.extend([data['depth'][indx], data['reflectivity'][indx], data['unused'][indx]])

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradBottomParser(_SimradDatagramParser):
    '''
    Bottom Detection datagram contains the following keys:

        type:         string == 'BOT0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        datetime:     datetime.datetime object of NT date converted to UTC
        transceiver_count:  long uint with number of tranceivers
        depth:        [float], one value for each active channel

    The following methods are defined:

        from_string(str):    parse a raw ER60 Bottom datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    def __init__(self):
        headers = {0: [('type', '4s'),
                     ('low_date', 'L'),
                     ('high_date', 'L'),
                     ('transceiver_count', 'L')
                     ]
                }
        _SimradDatagramParser.__init__(self, "BOT", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''

        '''

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        if version == 0:
            depth_fmt    = '=%dd' %(data['transceiver_count'],)
            depth_size   = struct.calcsize(depth_fmt)
            buf_indx     = self.header_size(version)
            data['depth'] = np.fromiter(struct.unpack(depth_fmt, raw_string[buf_indx:buf_indx + depth_size]), 'float')

        return data

    def _pack_contents(self, data, version):

        datagram_fmt      = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            if len(data['depth']) != data['transceiver_count']:
#                log.warning('# of depth values %d does not match transceiver count %d',
#                    len(data['depth']), data['transceiver_count'])
                data['transceiver_count'] = len(data['depth'])

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            datagram_fmt += '%dd' % (data['transceiver_count'])
            datagram_contents.extend(data['depth'])

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradAnnotationParser(_SimradDatagramParser):
    '''
    ER60 NMEA datagram contains the following keys:


        type:         string == 'TAG0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:     datetime.datetime object of NT date, assumed to be UTC

        text:         Annotation

    The following methods are defined:

        from_string(str):    parse a raw ER60 Annotation datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    def __init__(self):
        headers = {0: [('type', '4s'),
                     ('low_date', 'L'),
                     ('high_date', 'L')
                     ]
                }

        _SimradDatagramParser.__init__(self, "TAG", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''

        '''

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        if version == 0:

            if (sys.version_info.major > 2):
                data['text'] = str(raw_string[self.header_size(version):].strip(b'\x00'), 'ascii', errors='replace')
            else:
                data['text'] = unicode(raw_string[self.header_size(version):].strip('\x00'), 'ascii', errors='replace')

        return data

    def _pack_contents(self, data, version):

        datagram_fmt      = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            if data['text'][-1] != '\x00':
                tmp_string = data['text'] + '\x00'
            else:
                tmp_string = data['text']

            #Pad with more nulls to 4-byte word boundry if necessary
            if len(tmp_string) % 4:
                tmp_string += '\x00' * (4 - (len(tmp_string) % 4))

            #  handle Python 3 strings
            tmp_string = tmp_string.encode('latin_1')

            datagram_fmt += '%ds' % (len(tmp_string))
            datagram_contents.append(tmp_string)

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradNMEAParser(_SimradDatagramParser):
    '''
    ER60 NMEA datagram contains the following keys:


        type:         string == 'NME0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:     datetime.datetime object of NT date, assumed to be UTC

        nmea_string:  full (original) NMEA string

    The following methods are defined:

        from_string(str):    parse a raw ER60 NMEA datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    nmea_head_re = re.compile('\$[A-Za-z]{5},')

    def __init__(self):
        headers = {0: [('type', '4s'),
                             ('low_date', 'L'),
                             ('high_date', 'L')
                            ]
                        }

        _SimradDatagramParser.__init__(self, "NME", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''
        Parses the NMEA string provided in raw_string

        :param raw_string:  Raw NMEA strin (i.e. '$GPZDA,160012.71,11,03,2004,-1,00*7D')
        :type raw_string: str

        :returns: None
        '''

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        if version == 0:

            if (sys.version_info.major > 2):
                data['nmea_string'] = str(raw_string[self.header_size(version):].strip(b'\x00'), 'ascii', errors='replace')
            else:
                data['nmea_string'] = unicode(raw_string[self.header_size(version):].strip('\x00'), 'ascii', errors='replace')

            if self.nmea_head_re.match(data['nmea_string'][:7]) is not None:
                data['nmea_talker'] = data['nmea_string'][1:3]
                data['nmea_type']   = data['nmea_string'][3:6]
            else:
                data['nmea_talker'] = ''
                data['nmea_type']   = 'UNKNOWN'

        return data

    def _pack_contents(self, data, version):

        datagram_fmt      = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            if data['nmea_string'][-1] != '\x00':
                tmp_string = data['nmea_string'] + '\x00'
            else:
                tmp_string = data['nmea_string']

            #Pad with more nulls to 4-byte word boundry if necessary
            if len(tmp_string) % 4:
                tmp_string += '\x00' * (4 - (len(tmp_string) % 4))

            datagram_fmt += '%ds' % (len(tmp_string))

            #Convert to python string if needed
            if isinstance(tmp_string, str):
                tmp_string = tmp_string.encode('ascii', errors='replace')

            datagram_contents.append(tmp_string)


        return struct.pack(datagram_fmt, *datagram_contents)


class SimradMRUParser(_SimradDatagramParser):
    '''
    EK80 MRU datagram contains the following keys:


        type:         string == 'MRU0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:    datetime.datetime object of NT date, assumed to be UTC
        heave:        float
        roll :        float
        pitch:        float
        heading:      float

    The following methods are defined:

        from_string(str):    parse a raw EK800 MRU datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    def __init__(self):
        headers = {0: [('type', '4s'),
                       ('low_date', 'L'),
                       ('high_date', 'L'),
                       ('heave', 'f'),
                       ('roll', 'f'),
                       ('pitch', 'f'),
                       ('heading', 'f'),
                      ]
                   }

        _SimradDatagramParser.__init__(self, "MRU", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''
        Unpacks the data in raw_string into dictionary containing MRU data

        :param raw_string:
        :type raw_string: str

        :returns: None
        '''

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        return data

    def _pack_contents(self, data, version):

        datagram_fmt = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradIDXParser(_SimradDatagramParser):
    '''
    ER60/EK80 IDX datagram contains the following keys:


        type:         string == 'IDX0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:    datetime.datetime object of NT date, assumed to be UTC
        ping_number:  int
        distance :    float
        latitude:     float
        longitude:    float
        file_offset:  int

    The following methods are defined:

        from_string(str):    parse a raw ER60/EK80 IDX datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    def __init__(self):
        headers = {0: [('type', '4s'),
                       ('low_date', 'L'),
                       ('high_date', 'L'),
                       #('dummy', 'L'),   # There are 4 extra bytes in this datagram
                       ('ping_number', 'L'),
                       ('distance', 'd'),
                       ('latitude', 'd'),
                       ('longitude', 'd'),
                       ('file_offset', 'L'),
                      ]
                   }

        _SimradDatagramParser.__init__(self, "IDX", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''
        Unpacks the data in raw_string into dictionary containing IDX data

        :param raw_string:
        :type raw_string: str

        :returns: None
        '''

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        return data

    def _pack_contents(self, data, version):

        datagram_fmt = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradXMLParser(_SimradDatagramParser):
    '''
    EK80 XML datagram contains the following keys:


        type:         string == 'XML0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:    datetime.datetime object of NT date, assumed to be UTC
        subtype:      string representing Simrad XML datagram type: configuration, environment, or parameter

        [subtype]:    dict containing the data specific to the XML subtype.

    The following methods are defined:

        from_string(str):    parse a raw EK80 XML datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    #  define the XML parsing options - here we define dictionaries for the various xml datagram
    #  types. When parsing that datagram, these dictionaries are used to inform the parser about
    #  type conversion, name wrangling, and delimiter.
    #
    #  the dicts are in the form:
    #       'XMLParamName':[converted type,'fieldname', 'parse char']
    #
    #  For example: 'PulseDurationFM':[float,'pulse_duration_fm',';']
    #
    #  will result in a return dictionary field named 'pulse_duration_fm' that contains a list
    #  of float values parsed from a string that uses ';' to separate values. If the parse
    #  char is empty, the field is not parsed.
    #
    #  The switch to OrderedDict was required to ensure that when writing files, the generated
    #  XML follows the original XML parameter ordering.

    # These parameters are the known parameters for the transceiver XML tag
    transceiver_xml_map = OrderedDict({
            'TransceiverName':[str,'transceiver_name',''],
            'EthernetAddress':[str,'ethernet_address',''],
            'IPAddress':[str,'ip_address',''],
            'Version':[str,'transceiver_version',''],
            'TransceiverSoftwareVersion':[str,'transceiver_software_version',''],
            'TransceiverNumber':[int,'transceiver_number',''],
            'MarketSegment':[str,'market_segment',''],
            'TransceiverType':[str,'transceiver_type',''],
            'SerialNumber':[str,'serial_number',''],
            'Impedance':[int,'impedance',''],
            'Multiplexing':[int,'multiplexing',''],
            'RxSampleFrequency':[float,'rx_sample_frequency','']})

    channel_xml_map = OrderedDict({
            'ChannelID':[str,'channel_id',''],
            'ChannelIdShort':[str,'channel_id_short',''],
            'MaxTxPowerTransceiver':[int,'max_tx_power_transceiver',''],
            'PulseDuration':[float,'pulse_duration',';'],
            'PulseDurationFM':[float,'pulse_duration_fm',';'],
            'HWChannelConfiguration':[str,'hw_channel_configuration','']})

    channel_xdcr_xml_map = OrderedDict({
            'TransducerName':[str,'transducer_name',''],
            'SerialNumber':[str,'transducer_serial_number',''],
            'Frequency':[float,'transducer_frequency',''],
            'FrequencyMinimum':[float,'transducer_frequency_minimum',''],
            'FrequencyMaximum':[float,'transducer_frequency_maximum',''],
            'BeamType':[int,'transducer_beam_type',''],
            'EquivalentBeamAngle':[float,'equivalent_beam_angle',''],
            'Gain':[float,'gain',';'],
            'SaCorrection':[float,'sa_correction',';'],
            'MaxTxPowerTransducer':[float,'max_tx_power_transducer',''],
            'BeamWidthAlongship':[float,'beam_width_alongship',''],
            'BeamWidthAthwartship':[float,'beam_width_athwartship',''],
            'AngleSensitivityAlongship':[float,'angle_sensitivity_alongship',''],
            'AngleSensitivityAthwartship':[float,'angle_sensitivity_athwartship',''],
            'AngleOffsetAlongship':[float,'angle_offset_alongship',''],
            'AngleOffsetAthwartship':[float,'angle_offset_athwartship',''],
            'DirectivityDropAt2XBeamWidth':[float,'directivity_drop_at_2x_beam_width','']})

    xdcrs_xdcr_xml_map = OrderedDict({
            'TransducerName':[str,'transducer_name',''],
            'TransducerMounting':[str,'transducer_mounting',''],
            'TransducerCustomName':[str,'transducer_custom_name',''],
            'TransducerSerialNumber':[str,'transducer_serial_number',''],
            'TransducerOrientation':[str,'transducer_orientation',''],
            'TransducerOffsetX':[float,'transducer_offset_x',''],
            'TransducerOffsetY':[float,'transducer_offset_y',''],
            'TransducerOffsetZ':[float,'transducer_offset_z',''],
            'TransducerAlphaX':[float,'transducer_alpha_x',''],
            'TransducerAlphaY':[float,'transducer_alpha_y',''],
            'TransducerAlphaZ':[float,'transducer_alpha_z','']})

    header_xml_map = OrderedDict({
            'Copyright':[str,'copyright',''],
            'ApplicationName':[str,'application_name',''],
            'Version':[str,'application_version',''],
            'FileFormatVersion':[str,'file_format_version',''],
            'TimeBias':[str,'time_bias','']})

    #env_xdcr_xml_map = OrderedDict({
    #        'SoundSpeed':[float,'transducer_sound_speed','']})

    environment_xml_map = OrderedDict({
            'Depth':[float,'depth',''],
            'Acidity':[float,'acidity',''],
            'Salinity':[float,'salinity',''],
            'SoundSpeed':[float,'sound_speed',''],
            'Temperature':[float,'temperature',''],
            'Latitude':[float,'latitude',''],
            'SoundVelocityProfile':[float,'sound_velocity_profile',';'],
            'SoundVelocitySource':[str,'sound_velocity_source',''],
            'DropKeelOffset':[float,'drop_keel_offset',''],
            'DropKeelOffsetIsManual':[int,'drop_keel_offset_is_manual',''],
            'WaterLevelDraft':[float,'water_level_draft',''],
            'WaterLevelDraftIsManual':[int,'water_level_draft_is_manual','']})

    parameter_xml_map = OrderedDict({
            'ChannelID':[str,'channel_id',''],
            'ChannelMode':[int,'channel_mode',''],
            'PulseForm':[int,'pulse_form',''],
            'Frequency':[float,'frequency',''],
            'FrequencyStart':[float,'frequency_start',''],
            'FrequencyEnd':[float,'frequency_end',''],
            'PulseDuration':[float,'pulse_duration',''],
            'SampleInterval':[float,'sample_interval',''],
            'TransmitPower':[float,'transmit_power',''],
            'Slope':[float,'slope','']})

    freq_param_xml_map = OrderedDict({
            'Frequency':[float,'frequency',''],
            'Gain':[float,'gain',''],
            'Impedance':[float,'impedance',''],
            'Phase':[float,'phase',''],
            'BeamWidthAlongship':[float,'beam_width_alongship',''],
            'BeamWidthAthwartship':[float,'beam_width_athwartship',''],
            'AngleOffsetAlongship':[float,'angle_offset_alongship',''],
            'AngleOffsetAthwartship':[float,'angle_offset_athwartship','']})



    def __init__(self):
        headers = {0: [('type', '4s'),
                        ('low_date', 'L'),
                        ('high_date', 'L')
                            ]
                        }

        _SimradDatagramParser.__init__(self, "XML", headers)


    def _unpack_contents(self, raw_string, bytes_read, version):
        '''
        Parses the XML string provided in raw_string

        :param raw_string:  Raw XML string
        :type raw_string: str

        :returns: Dictionary containing parsed XML data where the keys are the XML
                  parameter names. Note that the names are converted from CamelCase
                  to lower case with "_" to follow the pyEcholab naming convention.
        '''


        def dict_to_dict(xml_dict, data_dict, parse_opts):
            '''
            dict_to_dict appends the xml value dicts to a provided dictionary
            and along the way converts the key name to conform to the project's
            naming convention and optionally parses and or converts values as
            specified in the parse_opts dictionary.
            '''

            for k in xml_dict:
                #  check if we're parsing this key/value
                if k in parse_opts:
                    #  try to parse the string
                    if (parse_opts[k][2]):
                        try:
                            data = xml_dict[k].split(parse_opts[k][2])
                        except:
                            #  bad or empty parse chararacter(s) provided
                            data = xml_dict[k]
                    else:
                        #  no parse char provided - nothing to parse
                        data = xml_dict[k]

                    # Try to convert to specified type
                    if isinstance(data, list):
                        # Lists are returned as numpy arrays
                        for i in range(len(data)):
                            try:
                                data[i] = parse_opts[k][0](data[i])
                            except:
                                pass

                        # Determine the array type
                        if parse_opts[k][0] == int:
                            dtype = np.int32
                        elif parse_opts[k][0] == float:
                            dtype = np.float32
                        else:
                            dtype = np.string_

                        # and create the array
                        data = np.array(data, dtype=dtype)
                    else:
                        data = parse_opts[k][0](data)

                    #  and add the value to the provided dict
                    data_dict[parse_opts[k][1]] = data


        #  unpack the header data
        data = {}
        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])
        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        #  add the unix timestanp and bytes read
        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        #  parse the datagram based on the version
        if version == 0:
            xml_string = raw_string[self.header_size(version):].strip(b'\x00')

            #  get the ElementTree element
            root_node = ET.fromstring(xml_string)

            #  get the XML message type
            data['subtype'] = root_node.tag.lower()

            #  create the dictionary that contains the message data
            data[data['subtype']] = {}

            #  parse it
            if data['subtype'] == 'configuration':

                #print(xml_string.decode('utf-8'))

                transducer_map = {}
                transducers_node = root_node.find('./Transducers')
                for xdcrs_node in transducers_node.iter('Transducer'):
                    transducer_map[xdcrs_node.get('TransducerName')] = xdcrs_node.attrib

                # Parse the Transceiver section
                xcvrs_node = root_node.find('./Transceivers')
                for xcvr_node in xcvrs_node.iter('Transceiver'):
                    # Get the transceiver attributes
                    xcvr_attributes = xcvr_node.attrib

                    #  parse the Channel section -- this works with multiple channels under 1 transceiver
                    for channel_node in xcvr_node.iter('Channel'):
                        # Get this channel's attributes
                        channel_attributes = channel_node.attrib
                        channel_id = channel_attributes['ChannelID']

                        #  create the configuration dict for this channel
                        data['configuration'][channel_id] = {}

                        # Save the raw XML string - needed when writing because we don't parse
                        # the whole configuration with certain configuration strings
                        data['configuration'][channel_id]['raw_xml'] = xml_string

                        #  add the transceiver data to the config dict (this is
                        #  replicated for all channels configured for this transceiver)
                        dict_to_dict(xcvr_attributes, data['configuration'][channel_id],
                                     self.transceiver_xml_map)

                        #  add the general channel data to the config dict
                        dict_to_dict(channel_attributes, data['configuration'][channel_id],
                                     self.channel_xml_map)

                        # Get this channel's transducer params
                        transducer_node = channel_node.find('./Transducer')
                        transducer_attributes = transducer_node.attrib

                        #  add the channel transducer attributes
                        dict_to_dict(transducer_attributes, data['configuration'][channel_id],
                                     self.channel_xdcr_xml_map)

                        # parse any wideband transducer calibration parameters.
                        wb_transducer_parm_nodes = transducer_node.findall('./FrequencyPar')
                        xdcr_params_wideband = {}
                        for node in wb_transducer_parm_nodes:
                            this_params = {}
                            dict_to_dict(node.attrib, this_params, self.freq_param_xml_map)
                            freq = this_params['frequency']
                            #this_params['gain'] = this_params['gain'][0]
                            this_params.pop('frequency', None)
                            xdcr_params_wideband[freq] = this_params
                        if len(xdcr_params_wideband):
                            data['configuration'][channel_id]['transducer_params_wideband'] = xdcr_params_wideband

                        # Now add the matching transducer from the transducers section
                        # we parsed above.
                        transducer_map[transducer_attributes['TransducerName']]
                        dict_to_dict(transducer_map[transducer_attributes['TransducerName']],
                                data['configuration'][channel_id], self.xdcrs_xdcr_xml_map)

                        #  add the header data to the config dict
                        h = root_node.find('Header')
                        dict_to_dict(h.attrib, data['configuration'][channel_id],
                                     self.header_xml_map)

            elif data['subtype'] == 'parameter':

                #print(xml_string.decode('utf-8'))

                #  parse the parameter XML datagram
                for h in root_node.iter('Channel'):
                    parm_xml = h.attrib
                    #  add the data to the environment dict
                    dict_to_dict(parm_xml, data['parameter'], self.parameter_xml_map)

            elif data['subtype'] == 'environment':

                #print(xml_string.decode('utf-8'))

                #  parse the environment XML datagram
                for h in root_node.iter('Environment'):
                    env_xml = h.attrib
                    #  add the data to the environment dict
                    dict_to_dict(env_xml, data['environment'], self.environment_xml_map)

                #  add the xdcr environment data
                data['environment']['transducer_name'] = []
                data['environment']['transducer_sound_speed'] = []
                for h in root_node.iter('Transducer'):
                    transducer_xml = h.attrib
                    data['environment']['transducer_name'].append(transducer_xml['TransducerName'])
                    data['environment']['transducer_sound_speed'].append(float(transducer_xml['SoundSpeed']))

        return data


    def _pack_contents(self, data, version):

        def update_xml(node, xml_map, data):
            '''update_xml updates a property in the xml tree using the provided
               node, map and data.
            '''
            # Iterate through the map keys
            for prop in xml_map:
                # try to extract a value from the dat
                str_val = None
                value = data.get(xml_map[prop][1], None)
                if isinstance(value, np.ndarray):
                    str_val = []
                    for v in value:
                        str_val.append('%f' % v)
                    str_val = xml_map[prop][2].join(str_val)
                elif value is not None:
                    str_val = str(value)

                # If there is a value, the property
                if str_val:
                    node.set(prop, str_val)

        # Initialize the datagram format and contents
        datagram_fmt = self.header_fmt(version)
        datagram_contents = []

        # Insert the datagram header fields
        for field in self.header_fields(version):
            if isinstance(data[field], str):
                data[field] = data[field].encode('latin_1')
            datagram_contents.append(data[field])

        if version == 0:

            if data['subtype'] == 'configuration':
                # This is a configuration datagram we need to pack

                # Get a list of the channels we're dealing with
                channel_ids = list(data['configuration'].keys())

                # Load the original configuration XML into etree - certain systems
                # write extended configuration data that we don't parse at this time.
                # Changes to parameters from the <Configuration> section will be updated
                # below. Other sections will pass through unchanged.
                root_node = ET.fromstring(data['configuration'][channel_ids[0]]['raw_xml'])

                #  update the header
                header_node = root_node.find('./Header')
                update_xml(header_node, self.header_xml_map, data['configuration'][channel_ids[0]])

                # Now work through the channels in the transceivers section
                transceivers_node = root_node.find('./Transceivers')
                for chan in channel_ids:
                    # Get a reference to this channels configuration data
                    chan_data = data['configuration'][chan]

                    # Update this channel's transceiver node
                    for xcvr_node in transceivers_node.findall('./Transceiver[@TransceiverName="' +
                            chan_data['transceiver_name'] + '"]'):
                        update_xml(xcvr_node, self.transceiver_xml_map, chan_data)

                        # And update this channels channel node
                        channels_node = xcvr_node.find('./Channels')
                        for channel_node in channels_node.findall('./Channel[@ChannelID="' + chan + '"]'):
                            update_xml(channel_node, self.channel_xml_map, chan_data)
                            # Update this channel's transducer node
                            for chan_xdcr_node in channel_node.findall('./Transducer[@TransducerName="' + chan_data['transducer_name'] + '"]'):
                                update_xml(chan_xdcr_node, self.channel_xdcr_xml_map, chan_data)

                    # Now update the transducers section
                    transducers_node = root_node.find('./Transducers')
                    for xdcr_node in transducers_node.findall('./Transducer[@TransducerCustomName="' +
                            chan_data['transducer_custom_name'] + '"]'):
                        update_xml(xdcr_node, self.xdcrs_xdcr_xml_map, chan_data)

            elif data['subtype'] == 'parameter':

                # Build the parameter XML string
                root_node = ET.Element('Parameter')
                chan_node = ET.SubElement(root_node, "Channel")
                update_xml(chan_node, self.parameter_xml_map, data['parameter'])

            elif data['subtype'] == 'environment':

                # Build the environment XML string
                root_node = ET.Element('Environment')
                update_xml(root_node, self.environment_xml_map, data['environment'])

                # Now add the transducer environmental params
                for i in range(len(data['environment']['transducer_name'])):
                    xdcr_node = ET.SubElement(root_node, "Transducer")
                    xdcr_node.set('TransducerName', data['environment']['transducer_name'][i])
                    xdcr_node.set('SoundSpeed', str(data['environment']['transducer_sound_speed'][i]))

            # Get the xml obj as a bytes, insert header, and convert to string
            xml_string = ET.tostring(root_node, encoding='utf8', method='xml',
                        pretty_print=True)
            xml_string = b'<?xml version="1.0" encoding="utf-8"?>\n' + xml_string
            #print(xml_string.decode('utf-8'))

            #Pad with more nulls to 4-byte word boundry if necessary
            xml_string = xml_string + bytes(len(xml_string) % 4)

            # Update the format string and append to the contents list
            datagram_fmt += '%ds' % (len(xml_string))
            datagram_contents.append(xml_string)

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradFILParser(_SimradDatagramParser):
    '''
    EK80 FIL datagram contains the following keys:


        type:               string == 'FIL1'
        low_date:           long uint representing LSBytes of 64bit NT date
        high_date:          long uint representing MSBytes of 64bit NT date
        timestamp:          datetime.datetime object of NT date, assumed to be UTC
        stage:              int
        channel_id:         string
        n_coefficients:     int
        decimation_factor:  int
        coefficients:       np.complex64

    The following methods are defined:

        from_string(str):    parse a raw EK80 FIL datagram
                            (with leading/trailing datagram size stripped)

        to_string():         Returns the datagram as a raw string (including leading/trailing size fields)
                            ready for writing to disk
    '''

    def __init__(self):
        headers = {1:[('type', '4s'),
                      ('low_date', 'L'),
                      ('high_date', 'L'),
                      ('stage', 'h'),
                      ('spare', '2s'),
                      ('channel_id', '128s'),
                      ('n_coefficients', 'h'),
                      ('decimation_factor', 'h')
                      ]
                   }

        _SimradDatagramParser.__init__(self, 'FIL', headers)


    def _unpack_contents(self, raw_string, bytes_read, version):

        data = {}
        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]

            #  handle Python 3 strings
            if isinstance(data[field], bytes):
                data[field] = data[field].decode('latin_1')

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        if version == 1:
            #  clean up the channel ID
            data['channel_id'] = data['channel_id'].strip('\x00')

            #  unpack the coefficients
            indx = self.header_size(version)
            block_size = data['n_coefficients'] * 8
            #data['coefficients'] = np.fromstring(raw_string[indx:indx + block_size], dtype='complex64')
            data['coefficients'] = np.frombuffer(raw_string[indx:indx + block_size], dtype='complex64')

        return data

    def _pack_contents(self, data, version):

        datagram_fmt = self.header_fmt(version)
        datagram_contents = []

        # No known version 0

        if version == 1:

            # Add the spare value (2 byte padding in datagram)
            data['spare'] = ''

            # Append the datagram values
            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            # Reform the coefficients into float vector
            coefficients = data['coefficients'].view(np.float32)
            datagram_contents.extend(coefficients)
            datagram_fmt += '%df' % (coefficients.shape[0])

        return struct.pack(datagram_fmt, *datagram_contents)


class SimradConfigParser(_SimradDatagramParser):
    '''
    Simrad Configuration Datagram parser. The CONx datagrams are present in data files
    collected using the ES/EK60, ES70, and ME70.

    5-15-20 - RHT: The output from this parser has been changed to follow the output
                   format of the XML parser configuration datagram.

  The parser operates on dictonaries with the following keys:

        type:           string == 'CON0'
        subtype:        string == 'configuration'
        low_date:       long uint representing LSBytes of 64bit NT date
        high_date:      long uint representing MSBytes of 64bit NT date
        timestamp:      datetime.datetime object of NT date, assumed to be UTC
        dg_version:     int representing the datagram version
        bytes_read:     int representing the number of bytes read from disk
        configuration:  dict, keyed by channel ID, containing the configuration header
                        data by channel. Common field values are replicated across
                        channels.

        The configuration dict contains the configuration parameters keyed by Channel ID.
        The common configuration field values like survery_name and sounder_name are
        replicated across channels. Note that when these data are packed, the values for
        the common fields are taken from the first channel.

    The common configuration fields are:

        survey_name                     [str]
        transect_name                   [str]
        sounder_name                    [str]
        version                         [str]
        spare0                          [str]
        transceiver_count               [long]
        transceivers                    [list] List of dicts representing Transducer Configs:

        ME70 Data contains the following additional values (data contained w/in first 14
            bytes of the spare0 field)

        multiplexing                    [short]  Always 0
        time_bias                       [long] difference between UTC and local time in min.
        sound_velocity_avg              [float] [m/s]
        sound_velocity_transducer       [float] [m/s]
        beam_config                     [str] Raw XML string containing beam config. info

    transceiver specific keys (ER60/ES60 sounders):
        channel_id                      [str]   channel ident string
        beam_type                       [long]  Type of channel (0 = Single, 1 = Split)
        frequency                       [float] channel frequency
        equivalent_beam_angle           [float] dB
        beamwidth_alongship             [float]
        beamwidth_athwartship           [float]
        angle_sensitivity_alongship     [float]
        angle_sensitivity_athwartship   [float]
        angle_offset_alongship          [float]
        angle_offset_athwartship        [float]
        pos_x                           [float]
        pos_y                           [float]
        pos_z                           [float]
        dir_x                           [float]
        dir_y                           [float]
        dir_z                           [float]
        pulse_length_table              [float[5]]
        spare1                          [str]
        gain_table                      [float[5]]
        spare2                          [str]
        sa_correction_table             [float[5]]
        spare3                          [str]
        gpt_software_version            [str]
        spare4                          [str]

    transceiver specific keys (ME70 sounders):
        channel_id                      [str]   channel ident string
        beam_type                       [long]  Type of channel (0 = Single, 1 = Split)
        reserved1                       [float] channel frequency
        equivalent_beam_angle           [float] dB
        beamwidth_alongship             [float]
        beamwidth_athwartship           [float]
        angle_sensitivity_alongship     [float]
        angle_sensitivity_athwartship   [float]
        angle_offset_alongship          [float]
        angle_offset_athwartship        [float]
        pos_x                           [float]
        pos_y                           [float]
        pos_z                           [float]
        beam_steering_angle_alongship   [float]
        beam_steering_angle_athwartship [float]
        beam_steering_angle_unused      [float]
        pulse_length                    [float]
        reserved2                       [float]
        spare1                          [str]
        gain                            [float]
        reserved3                       [float]
        spare2                          [str]
        sa_correction                   [float]
        reserved4                       [float]
        spare3                          [str]
        gpt_software_version            [str]
        spare4                          [str]

    from_string(str):   parse a raw config datagram
                        (with leading/trailing datagram size stripped)

    to_string(dict):    Returns raw string (including leading/trailing size fields)
                        ready for writing to disk
    '''

    def __init__(self):
        headers = {0:[('type', '4s'),
                      ('low_date', 'L'),
                      ('high_date', 'L'),
                      ('survey_name', '128s'),
                      ('transect_name', '128s'),
                      ('sounder_name', '128s'),
                      ('version', '30s'),
                      ('spare0', '98s'),
                      ('transceiver_count', 'l')
                      ],
                   1:[('type', '4s'),
                      ('low_date', 'L'),
                      ('high_date', 'L')
                      ]}

        _SimradDatagramParser.__init__(self, 'CON', headers)

        #  for CON0 datagrams, the data are not in XML format so the naming and
        #  typing system used for parsing XML data doesn't come into play. Here
        #  we define the dict keys and binary data types for CON0 headers.

        self._transducer_headers = {'ER60':[('channel_id', '128s'),
                                       ('beam_type', 'l'),
                                       ('frequency', 'f'),
                                       ('gain', 'f'),
                                       ('equivalent_beam_angle', 'f'),
                                       ('beamwidth_alongship', 'f'),
                                       ('beamwidth_athwartship', 'f'),
                                       ('angle_sensitivity_alongship', 'f'),
                                       ('angle_sensitivity_athwartship', 'f'),
                                       ('angle_offset_alongship', 'f'),
                                       ('angle_offset_athwartship', 'f'),
                                       ('pos_x', 'f'),
                                       ('pos_y', 'f'),
                                       ('pos_z', 'f'),
                                       ('dir_x', 'f'),
                                       ('dir_y', 'f'),
                                       ('dir_z', 'f'),
                                       ('pulse_length_table', '5f'),
                                       ('spare1', '8s'),
                                       ('gain_table', '5f'),
                                       ('spare2', '8s'),
                                       ('sa_correction_table', '5f'),
                                       ('spare3', '8s'),
                                       ('gpt_software_version', '16s'),
                                       ('spare4', '28s')
                                       ],
                                    'ES60':[('channel_id', '128s'),
                                       ('beam_type', 'l'),
                                       ('frequency', 'f'),
                                       ('gain', 'f'),
                                       ('equivalent_beam_angle', 'f'),
                                       ('beamwidth_alongship', 'f'),
                                       ('beamwidth_athwartship', 'f'),
                                       ('angle_sensitivity_alongship', 'f'),
                                       ('angle_sensitivity_athwartship', 'f'),
                                       ('angle_offset_alongship', 'f'),
                                       ('angle_offset_athwartship', 'f'),
                                       ('pos_x', 'f'),
                                       ('pos_y', 'f'),
                                       ('pos_z', 'f'),
                                       ('dir_x', 'f'),
                                       ('dir_y', 'f'),
                                       ('dir_z', 'f'),
                                       ('pulse_length_table', '5f'),
                                       ('spare1', '8s'),
                                       ('gain_table', '5f'),
                                       ('spare2', '8s'),
                                       ('sa_correction_table', '5f'),
                                       ('spare3', '8s'),
                                       ('gpt_software_version', '16s'),
                                       ('spare4', '28s')
                                       ],
                                    'MBES':[('channel_id', '128s'),
                                       ('beam_type', 'l'),
                                       ('frequency', 'f'),
                                       ('reserved1', 'f'),
                                       ('equivalent_beam_angle', 'f'),
                                       ('beamwidth_alongship', 'f'),
                                       ('beamwidth_athwartship', 'f'),
                                       ('angle_sensitivity_alongship', 'f'),
                                       ('angle_sensitivity_athwartship', 'f'),
                                       ('angle_offset_alongship', 'f'),
                                       ('angle_offset_athwartship', 'f'),
                                       ('pos_x', 'f'),
                                       ('pos_y', 'f'),
                                       ('pos_z', 'f'),
                                       ('beam_steering_angle_alongship', 'f'),
                                       ('beam_steering_angle_athwartship', 'f'),
                                       ('beam_steering_angle_unused', 'f'),
                                       ('pulse_length', 'f'),
                                       ('reserved2', 'f'),
                                       ('spare1', '20s'),
                                       ('gain', 'f'),
                                       ('reserved3', 'f'),
                                       ('spare2', '20s'),
                                       ('sa_correction', 'f'),
                                       ('reserved4', 'f'),
                                       ('spare3', '20s'),
                                       ('gpt_software_version', '16s'),
                                       ('spare4', '28s')
                                       ]
                                    }

    def _unpack_contents(self, raw_string, bytes_read, version):

        data = {}
        header_data = {}
        common_params = {}

        round6 = lambda x: round(x, ndigits=6)
        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])

        for indx, field in enumerate(self.header_fields(version)):
            header_data[field] = header_values[indx]

            #  handle Python 3 strings
            if isinstance(header_data[field], bytes):
                header_data[field] = header_data[field].decode('latin_1')

        #  add the common fields to the return dict
        data['low_date'] = header_data['low_date']
        data['high_date'] = header_data['high_date']
        data['timestamp'] = nt_to_unix((header_data['low_date'], header_data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['type'] = header_data['type']
        data['subtype'] = 'configuration'
        data['configuration'] = {}
        data['dg_version'] = version
        data['bytes_read'] = bytes_read

        if version == 0:

            for field in ['transect_name', 'version', 'survey_name', 'sounder_name']:
                common_params[field] = header_data[field].strip('\x00')

            sounder_name = common_params['sounder_name']
            if sounder_name == 'MBES':
                _me70_extra_values = struct.unpack('=hLff', header_data['spare0'][:14])
                common_params['multiplexing'] = _me70_extra_values[0]
                common_params['time_bias'] = _me70_extra_values[1]
                common_params['sound_velocity_avg'] = _me70_extra_values[2]
                common_params['sound_velocity_transducer'] = _me70_extra_values[3]
                common_params['spare0'] = data['spare0'][:14] + data['spare0'][14:].strip('\x00')

            else:
                common_params['spare0'] = header_data['spare0'].strip('\x00')

            buf_indx = self.header_size(version)

            try:
                transducer_header = self._transducer_headers[sounder_name]
                _sounder_name_used = sounder_name
            except KeyError:
#                log.warning('Unknown sounder_name:  %s, (no one of %s)', sounder_name,
#                    list(self._transducer_headers.keys()))
#                log.warning('Will use ER60 transducer config fields as default')

                transducer_header = self._transducer_headers['ER60']
                _sounder_name_used = 'ER60'

            txcvr_header_fields = [x[0] for x in transducer_header]
            txcvr_header_fmt    = '=' + ''.join([x[1] for x in transducer_header])
            txcvr_header_size   = struct.calcsize(txcvr_header_fmt)

            for txcvr_indx in range(1, header_data['transceiver_count'] + 1):
                txcvr_header_values_encoded = struct.unpack(txcvr_header_fmt,
                        raw_string[buf_indx:buf_indx + txcvr_header_size])
                txcvr_header_values = list(txcvr_header_values_encoded)
                for tx_idx, tx_val in enumerate(txcvr_header_values_encoded):
                    if isinstance(tx_val, bytes):
                        txcvr_header_values[tx_idx] = tx_val.decode()

                channel_id = txcvr_header_values[0].strip('\x00')
                txcvr = data['configuration'].setdefault(channel_id, {})
                txcvr.update(common_params)

                if _sounder_name_used in ['ER60', 'ES60']:
                    for txcvr_field_indx, field in enumerate(txcvr_header_fields[:17]):
                        txcvr[field] = txcvr_header_values[txcvr_field_indx]

                    txcvr['pulse_length_table']   = np.fromiter(list(map(round6, txcvr_header_values[17:22])), 'float')
                    txcvr['spare1']               = txcvr_header_values[22]
                    txcvr['gain_table']           = np.fromiter(list(map(round6, txcvr_header_values[23:28])), 'float')
                    txcvr['spare2']               = txcvr_header_values[28]
                    txcvr['sa_correction_table']  = np.fromiter(list(map(round6, txcvr_header_values[29:34])), 'float')
                    txcvr['spare3']               = txcvr_header_values[34]
                    txcvr['gpt_software_version'] = txcvr_header_values[35]
                    txcvr['spare4']               = txcvr_header_values[36]

                elif _sounder_name_used  == 'MBES':
                    for txcvr_field_indx, field in enumerate(txcvr_header_fields):
                        txcvr[field] = txcvr_header_values[txcvr_field_indx]

                else:
                    raise RuntimeError('Unknown _sounder_name_used (Should not happen, this is a bug!)')

                txcvr['channel_id']           = channel_id
                txcvr['spare1']               = txcvr['spare1'].strip('\x00')
                txcvr['spare2']               = txcvr['spare2'].strip('\x00')
                txcvr['spare3']               = txcvr['spare3'].strip('\x00')
                txcvr['spare4']               = txcvr['spare4'].strip('\x00')
                txcvr['gpt_software_version'] = txcvr['gpt_software_version'].strip('\x00')

                buf_indx += txcvr_header_size

        elif version == 1:
            #CON1 only has a single data field:  beam_config, holding an xml string
            data['beam_config'] = raw_string[self.header_size(version):].strip('\x00')


        return data


    def _pack_contents(self, data, version):

        datagram_fmt = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            # Build out the config dict so it can be unpacked
            # Pull the common configuration data out of the first channel available
            first_chan = list(data['configuration'].keys())[0]
            first_conf = data['configuration'][first_chan]

            data['transceiver_count'] = len(data['configuration'])

            sounder_name = first_conf['sounder_name']
            if sounder_name == 'MBES':
                _packed_me70_values = struct.pack('=hLff', first_conf['multiplexing'],
                    first_conf['time_bias'], first_conf['sound_velocity_avg'], first_conf['sound_velocity_transducer'])
                first_conf['spare0'] = _packed_me70_values + first_conf['spare0'][14:]

            data['survey_name'] = first_conf['survey_name'].encode('latin_1')
            data['transect_name'] = first_conf['transect_name'].encode('latin_1')
            data['sounder_name'] = first_conf['sounder_name'].encode('latin_1')
            data['version'] = first_conf['version'].encode('latin_1')
            data['spare0'] = first_conf['spare0'].encode('latin_1')

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            try:
                transducer_header = self._transducer_headers[sounder_name]
                _sounder_name_used = sounder_name
            except KeyError:
                transducer_header = self._transducer_headers['ER60']
                _sounder_name_used = 'ER60'

            txcvr_header_fields = [x[0] for x in transducer_header]
            txcvr_header_fmt    = '=' + ''.join([x[1] for x in transducer_header])

            for txcvr_indx, txcvr in list(data['configuration'].items()):
                txcvr_contents = []

                if _sounder_name_used in ['ER60', 'ES60']:
                    for field in txcvr_header_fields[:17]:
                        #  Python 3 convert str to bytes
                        if isinstance(txcvr[field], str):
                            txcvr[field] = txcvr[field].encode('latin_1')
                        txcvr_contents.append(txcvr[field])

                    txcvr_contents.extend(txcvr['pulse_length_table'])
                    txcvr_contents.append(txcvr['spare1'].encode('latin_1'))

                    txcvr_contents.extend(txcvr['gain_table'])
                    txcvr_contents.append(txcvr['spare2'].encode('latin_1'))

                    txcvr_contents.extend(txcvr['sa_correction_table'])
                    txcvr_contents.append(txcvr['spare3'].encode('latin_1'))

                    txcvr_contents.extend([txcvr['gpt_software_version'].encode('latin_1'), txcvr['spare4'].encode('latin_1')])

                    txcvr_contents_str = struct.pack(txcvr_header_fmt, *txcvr_contents)

                elif _sounder_name_used == 'MBES':
                    for field in txcvr_header_fields:
                        txcvr_contents.append(txcvr[field])

                    txcvr_contents_str = struct.pack(txcvr_header_fmt, *txcvr_contents)

                else:
                    raise RuntimeError('Unknown _sounder_name_used (Should not happen, this is a bug!)')

                datagram_fmt += '%ds' % (len(txcvr_contents_str))
                datagram_contents.append(txcvr_contents_str)

        elif version == 1:
            for field in self.header_fields(version):
                datagram_contents.append(data[field])

            datagram_fmt += '%ds' %(len(data['beam_config']))
            datagram_contents.append(data['beam_config'])

        return struct.pack(datagram_fmt, *datagram_contents)



class SimradRawParser(_SimradDatagramParser):
    '''
    Sample Data Datagram parser operates on dictonaries with the following keys:

        type:         string == 'RAW0'
        low_date:     long uint representing LSBytes of 64bit NT date
        high_date:    long uint representing MSBytes of 64bit NT date
        timestamp:    datetime.datetime object of NT date, assumed to be UTC

        channel                         [short] Channel number
        mode                            [short] 1 = Power only, 2 = Angle only 3 = Power & Angle
        transducer_depth                [float]
        frequency                       [float]
        transmit_power                  [float]
        pulse_length                    [float]
        bandwidth                       [float]
        sample_interval                 [float]
        sound_velocity                  [float]
        absorption_coefficient          [float]
        heave                           [float]
        roll                            [float]
        pitch                           [float]
        temperature                     [float]
        heading                         [float]
        transmit_mode                   [short] 0 = Active, 1 = Passive, 2 = Test, -1 = Unknown
        spare0                          [str]
        offset                          [long]
        count                           [long]

        power                           [numpy array] Unconverted power values (if present)
        angle                           [numpy array] Unconverted angle values (if present)

    from_string(str):   parse a raw sample datagram
                        (with leading/trailing datagram size stripped)

    to_string(dict):    Returns raw string (including leading/trailing size fields)
                        ready for writing to disk
    '''

    def __init__(self):
        headers = {0 : [('type', '4s'),
                        ('low_date', 'L'),
                        ('high_date', 'L'),
                        ('channel', 'h'),
                        ('mode', 'h'),
                        ('transducer_depth', 'f'),
                        ('frequency', 'f'),
                        ('transmit_power', 'f'),
                        ('pulse_length', 'f'),
                        ('bandwidth', 'f'),
                        ('sample_interval', 'f'),
                        ('sound_velocity', 'f'),
                        ('absorption_coefficient', 'f'),
                        ('heave', 'f'),
                        ('roll', 'f'),
                        ('pitch', 'f'),
                        ('temperature', 'f'),
                        ('heading', 'f'),
                        ('transmit_mode', 'h'),
                        ('spare0', '6s'),
                        ('offset', 'l'),
                        ('count', 'l')
                        ],
                   3 : [('type', '4s'),
                        ('low_date', 'L'),
                        ('high_date', 'L'),
                        ('channel_id', '128s'),
                        ('data_type', 'h'),
                        ('spare', '2s'),
                        ('offset', 'l'),
                        ('count', 'l')
                        ]
                    }
        _SimradDatagramParser.__init__(self, 'RAW', headers)

    def _unpack_contents(self, raw_string, bytes_read, version):

        header_values = struct.unpack(self.header_fmt(version), raw_string[:self.header_size(version)])

        data = {}

        for indx, field in enumerate(self.header_fields(version)):
            data[field] = header_values[indx]
            if isinstance(data[field], bytes):
                data[field] = data[field].decode()

        data['timestamp'] = nt_to_unix((data['low_date'], data['high_date']))
        data['timestamp'] = data['timestamp'].replace(tzinfo=None)
        data['bytes_read'] = bytes_read

        if version == 0:

            if data['count'] > 0:
                block_size = data['count'] * 2
                indx = self.header_size(version)

                if int(data['mode']) & 0x1:
                    data['power'] = np.frombuffer(raw_string[indx:indx + block_size], dtype='int16')
                    indx += block_size
                else:
                    data['power'] = None

                if int(data['mode']) & 0x2:
                    data['angle'] = np.frombuffer(raw_string[indx:indx + block_size], dtype='int8')
                    data['angle'].shape = (data['count'], 2)
                else:
                    data['angle'] = None

            else:
                data['power'] = np.empty((0,), dtype='int16')
                data['angle'] = np.empty((0,), dtype='int8')

        elif version == 3:

            #  clean up the channel ID
            data['channel_id'] = data['channel_id'].strip('\x00')

            if data['count'] > 0:

                #  set the initial block size and indx value.
                block_size = data['count'] * 2
                indx = self.header_size(version)

                if data['data_type'] & 0b1:
                    data['power'] = np.frombuffer(raw_string[indx:indx + block_size], dtype='int16')
                    indx += block_size
                else:
                    data['power'] = None

                if data['data_type'] & 0b10:
                    data['angle'] = np.frombuffer(raw_string[indx:indx + block_size], dtype='int8')
                    data['angle'].shape = (data['count'], 2)
                    indx += block_size
                else:
                    data['angle'] = None

                #  determine the complex sample data type - this is contained in bits 2 and 3
                #  of the datatype <short> value. I'm assuming the types are exclusive...
                #  Note that Numpy doesn't support the complex32 type so both the full precision
                #  (complex comprised of 2 32-bit floats) and reduced precision (complex
                #  comprised of 2 16-bit floats) are returned as np.complex64 which is complex
                #  comprised of 2 32-bit floats.
                data['complex_dtype'] = np.float16
                type_bytes = 2
                if ((data['data_type'] & 0b1000)):
                     data['complex_dtype'] = np.float32
                     type_bytes = 4

                #  determine the number of complex samples
                data['n_complex'] = data['data_type'] >> 8

                #  unpack the complex samples
                if (data['n_complex'] > 0):
                    #  determine the block size (complex data are comprised
                    #  of two values so we have to double this)
                    block_size = 2 * data['count'] * data['n_complex'] * type_bytes

                    #  convert and reshape the raw string data
                    data['complex'] = np.frombuffer(raw_string[indx:indx + block_size],
                            dtype=data['complex_dtype'])
                    data['complex'].shape = (data['count'], 2 * data['n_complex'])
                    data['complex'].dtype = np.complex64
                else:
                    data['complex'] = None

            else:
                data['power'] = np.empty((0,), dtype='int16')
                data['angle'] = np.empty((0,), dtype='int8')
                data['complex'] = np.empty((0,), dtype='complex64')
                data['n_complex'] = 0

        return data

    def _pack_contents(self, data, version):

        datagram_fmt = self.header_fmt(version)
        datagram_contents = []

        if version == 0:

            if data['count'] > 0 and data['mode'] == 0:
                    data['count'] = 0

            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            if data['count'] > 0:

                if int(data['mode']) & 0x1:
                    datagram_fmt += '%dh' % (data['count'])
                    datagram_contents.extend(data['power'])

                if int(data['mode']) & 0x2:
                    n_angles = data['count'] * 2
                    datagram_fmt += '%dB' % (n_angles)
                    #  reshape the angle array for writing
                    data['angle'].shape=(n_angles,)
                    datagram_contents.extend(data['angle'])

        elif version == 3:

            # Add the spare field
            data['spare'] = ''

            # work through the parameter dict and append data values to the
            # packed datagram list.
            for field in self.header_fields(version):
                if isinstance(data[field], str):
                    data[field] = data[field].encode('latin_1')
                datagram_contents.append(data[field])

            # Check if we have data to write
            if data['count'] > 0:

                if data['data_type'] & 0b0001:
                    # Add the power data
                    datagram_fmt += '%dh' % (data['count'])
                    datagram_contents.extend(data['power'])

                if data['data_type'] & 0b0010:
                    # Add the angle data
                    n_angles = data['count'] * 2
                    datagram_fmt += '%dB' % (n_angles)
                    #  reshape the angle array for writing
                    data['angle'].shape=(n_angles,)
                    datagram_contents.extend(data['angle'])

                if data['data_type'] & 0b1100:
                    # Add the complex data
                    if data['data_type'] & 0b0100:
                        # pack as 16 bit floats - struct doesn't have support for
                        # half floats so we use just pack them as bytes.
                        datagram_fmt += '%dB' % (data['complex'].shape[0] * 2)
                    else:
                        # pack as 32 bit floats
                        datagram_fmt += '%dB' % (data['complex'].shape[0] * 4)
                    datagram_contents.extend(data['complex'].view(np.ubyte))

        return struct.pack(datagram_fmt, *datagram_contents)
