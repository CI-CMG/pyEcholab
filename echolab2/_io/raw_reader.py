# coding=utf-8
'''
.. module:: echolab._io.raw_reader

    :synopsis:  A high-level interface for SIMRAD EK60/ER60 raw files


    Provides the RawReader class, a high-level object for 
        interacting with SIMRAD RAW formated datafiles.

| Zac Berkowitz <zachary.berkowitz@noaa.gov>
| National Oceanic and Atmospheric Administration
| Alaska Fisheries Science Center
| Midwater Assesment and Conservation Engineering Group
'''
import os
import logging
import pandas as pd
from pytz import utc as pytz_utc
import json

#Local package imports
from echolab2._io.raw_file import RawSimradFile, SimradEOF
from echolab2 import parsers, nmea
from echolab2.AxesArray import AxesArray
from echolab2.util.date_conversion import nt_to_unix, unix_to_nt
from echolab2.util import unit_conversion, gps, get_datetime_from_filename, triwave
from echolab2.util import calibration
from functools import reduce

__all__ = ['RawReader']

log = logging.getLogger(__name__)

class RawReader(object):
    '''
    Class for reading, writing, and manipulating Simrad RAW format data and
    associated bottom data (ie. .raw files and .out files)
    
    ==================  ============    ==================================
    attribute           type            description
    ==================  ============    ==================================
    config              dict            transceiver configuration 
    prefered_nmeas      dict            prefered NMEA types for GPS and 
                                        distance interpolation        
    calibration_params  dict            calibration values
    data                pd.DataFrame    ping data including calculated 
                                        quantities like Sv
    nmea                pd.DataFrame    NMEA datagrams 
    bottom              pd.DataFrame    Bottom depth estimates
    tags                pd.DataFrame    Annotations
    ==================  ============    ==================================
    '''

    def __init__(self, file=None, channel_names=None, channel_numbers=None,
        frequencies=None, first_ping_time=None, last_ping_time=None,
        prefered_nmeas=None, ignore_datagram_types=None, desired_nmea_types=None):
        '''
        :param file:  Filename or list of filenames to load
        :type file: str or [str]
        
        :param channel_names: List of channel ID's to load, or None for all
        :type channel_names: [str] or None
        
        :param channel_numbers: List of channel numbers (1-indexed) to load, or None for all
        :type channel_numbers: [int]
        
        :param frequencies: List of frequencies to load, in Hz, or None for all.
        :type frequencies: [int]
        
        :param first_ping_time:  Ignore all data before this time.
        :type first_ping_time: str or datetime.datetime
        
        :param last_ping_time: Ignore all data after this time.
        :type last_ping_time:  str or datetime.datetime
        
        :param prefered_nmeas:  Preferened NMEA datagrams for GPS and Distance calculations.
        :type prefered_nmea: dict
        
        :param ignore_datagram_types:  Do not load certain datagram types
        :type ignore_datagram_types: list

        :param desired_nmea_types:  Only load NMEA data of desired types
        :type desired_nmea_types:  list
        
        prefered_nmeas:
            key: 'gps', Suitable NMEA's: 'gll', 'gga'
                GPS information, interpolated to a per-ping basis.
                
            key: 'distance', Suitable NMEA's: 'vlw', 'gll', 'gga'
                Vessel distance information.  If 'vlw' datagrams are desired but
                not present, the desired 'gps' datagram will be used to calculate
                distance estimates.


        first_ping_time, last_ping_time:
            datetime.datetime objects or parseable string representations, e.g.
                '2011-09-23 12:00:54'

        ignore_datagram_types:
            Valid datagram types:  'nme', 'tag', 'bot', 'out', 'raw'

        desired_nmea_types:
            Three-letter NMEA abbreviation, e.g. 'gll', 'vlw', ...
        '''
        self.config = {}
        self.calibration_params = {}
        self.prefered_nmeas = {}
    
        if prefered_nmeas is None:
            self.prefered_nmeas = {'gps': 'GGA', 'distance': 'VLW'}
        elif isinstance(prefered_nmeas, dict):
            self.prefered_nmeas = prefered_nmeas.copy()
        else:
            raise ValueError('Expected dict or None for prefered_nmeas')
    
        self.nmea   = None
        self.tags   = None
        self.data   = None
        self.bottom = None


        if file is not None:
            self.append_file(file, channel_names, channel_numbers,
                frequencies, first_ping_time, last_ping_time,
                ignore_datagram_types=ignore_datagram_types,
                desired_nmea_types=desired_nmea_types)

    def copy_dicts(self, other):
        '''
        :param other: Other :class:`RawReader` instance.

        Copies meta-information dictionaries from self to other
        '''
        config_dict = getattr(other, 'config', {})
        calib_dict = getattr(other, 'calibration_params', {})
        pref_nmea_dict = getattr(other, 'prefered_nmeas', {})
        
        self.config = config_dict.copy()
        self.config['transceivers'] = config_dict.get('transceivers', {}).copy()
        self.prefered_nmeas = pref_nmea_dict.copy()
        self.calibration_params = calib_dict.copy()

    def _setup_config(self, config_datagrams, channel_names=None,
        channel_numbers=None, frequencies=None):
        '''
        :param config_datagrams: dict of configuration datagrams
        :type config_datagram: dict of dicts

        :param channel_names:  Names of channels to keep
        :type channel_names: list

        :param channel_numbers:  Channel indecies to keep.
        :type channel_numbers:  list

        :param frequencies:  Frequencies to keep
        :type frequencies: list

        :returns: channel_map
        
        Copies data from a file's CON (configuration) datagrams into the local
        self.config dictionary.

        Specifying channel_names, channel_numbers, or frequencies will 
        remap the local channel index stored in self.config.  This remapping
        is returned as a dictionary of source_channel_index -> local_channel_index
        '''
        #All files must have a valid CON0 datagra

        con0_datagram = config_datagrams['CON0']
        sounder_name = con0_datagram['sounder_name']

        config_fields = ['sounder_name', 'survey_name', 'version', 'transect_name', 'type']
        if sounder_name == 'MBES':
            config_fields.extend(['multiplexing', 'time_bias', 'sound_velocity_avg', 'sound_velocity_transducer'])
            try:
                con1_datagram = config_datagrams['CON1']
            except KeyError:
                log.warning('ME70 (MBES) data but no CON1 datagram found.  No beam config available')
                con1_datagram = {}

        if self.config == {}:
            for field in config_fields:
                self.config[field] = con0_datagram[field]
        
            if sounder_name == 'MBES':
                self.config['beam_config'] = con1_datagram.get('beam_config', '')

            channel_remap = self._remap_channels(con0_datagram['transceivers'],
                channel_names=channel_names, channel_numbers=channel_numbers,
                frequencies=frequencies)

            self.config['transceivers'] = {}

            for old_indx, new_indx in list(channel_remap.items()):
                transceiver = self.config['transceivers'].setdefault(new_indx, {})
                transceiver.update(con0_datagram['transceivers'][old_indx])
                
            self.config['transceiver_count'] = len(list(channel_remap.keys())) 
        else:
            channel_remap = self._remap_channels(con0_datagram['transceivers'],
                channel_names=[x['channel_id'] for x in list(self.config['transceivers'].values())])

        return channel_remap

    @classmethod
    def _remap_channels(cls, transceiver_dict, channel_names=None, channel_numbers=None,
        frequencies=None):
        '''
        :param transciever_dict:  Dictionary of transceiver configs
        :type transceiver dict: dict
        
        :param channel_names:  Names of channels to keep
        :type channel_names: list

        :param channel_numbers:  Channel indecies to keep.
        :type channel_numbers:  list

        :param frequencies:  Frequencies to keep
        :type frequencies: list

        :returns: channel_map
        
        Specifying channel_names, channel_numbers, or frequencies will 
        remap the local channel index stored in self.config.  This remapping
        is returned as a dictionary of source_channel_index -> local_channel_index
        '''
        channel_remap = {}
        if any([x is not None for x in [channel_numbers, channel_names, frequencies]]):
            
            channels_to_keep = []
            for indx, transceiver in list(transceiver_dict.items()):
                if channel_numbers is not None and indx in channel_numbers:
                    channels_to_keep.append(indx)
                    

                elif channel_names is not None and transceiver['channel_id'] in channel_names:
                    channels_to_keep.append(indx)
                    

                elif frequencies is not None and transceiver['frequency'] in frequencies:
                    channels_to_keep.append(indx)
                    

            if len(channels_to_keep) == 0:
                raise ValueError('No channels in file matched desired values.')

        else:
            channels_to_keep = list(transceiver_dict.keys())


        for new_indx, old_indx in enumerate(channels_to_keep, start=1):
            channel_remap[old_indx] = new_indx

        return channel_remap

    def load_calibration(self, calibration_file, channel_map=None):
        '''
        :param calibration_file: File to laod calibration from
        :type calibration_file: str
        
        :param channel_map:  Channel mapping from 
            ECS transceiver # -> local transceiver #
        :type channel_map: dict

        Load calibration data from an Echoview-like ECS file.

        :param channel_map: is required when loading a calibration file if
        you have removed or reordered channels.  This can happen if you
        originally loaded only a subset of channels.

        The expected map is a dictionary of original->new channel indices.

        For instance, if the original file contained two transcievers:

            1:   38kHz
            2:  120kHz

        But you only loaded the 120kHz channel.  The 120kHz channel will
        have been remapped to index #1.  You need to provide
        channel_map={2: 1} to correctly import transceiver 2 from the ECS
        calibration file as transceiver 1 (in our object).
        '''

        if os.path.splitext(calibration_file)[-1].lower().endswith('ecs'):
            calibration_dict = calibration.import_ecs(calibration_file)
            
        else:
            raise NotImplementedError
        
        if channel_map is None:
            channel_map = self._remap_channels(self.config['transceivers'], 
                        channel_numbers=list(calibration_dict.keys()))
                    
        for old_channel_num, new_channel_num in list(channel_map.items()):
            self.calibration_params[new_channel_num] =\
                calibration_dict[old_channel_num].copy()
            

    def get_channel(self, channel):
        '''
        :param channel:  Channel number or ID
        :type channel: int or str

        Returns a copy of sample data from the desired channel
        '''
     
        if self.data is None:
            log.warning('No sample data available')
            return None
        
        if isinstance(channel, str):
            channel = self.get_channel_number_from_id(channel)

        return self.data.xs(channel, level='channel')
    
    def get_nmea(self, nmea_type, talker_id=None, ignore_checksum=False,
                 drop_duplicates=True, max_records=None):
        '''
        :param nmea_type:  Type of NMEA you want (case-sensitive!)
        :type nmea_type: str
        
        :param talker_id: ID of talker (Optional)
        :type talker_id: str
        
        :param ignore_checksum: Ignore checksum validation
        :type ignore_checksum: bool
        
        :param drop_duplicates: Drop duplicate datagrams
        :type drop_duplicates: bool
        
        :param max_records:  Maximum number of NMEA records to return
        :type max_records: int
        
        :returns: :class:`pandas.DataFrame`
        
        Returned dataframe has columns matching the dictionary keys of the
        like-named NMEA parser found in :mod:`echolab.nmea` with an additional
        `nmea_string` column containing the original string (useful if parsing
        failed for some reason)

        NMEA datagrams are often duplicated across .raw and .bot/.out
        files, the .nmea DataFrame is often inflated with duplicated messages
        (differing only in the 'file' attribute used for writing back to disk).
        Setting `drop_duplicates`=True removes duplicate messages.
                
        If a NMEA string failed to parse, all columns except for `nmea_string`
        will contain the empty string ('').
        
        Returns up to `max_records` parsed NMEA strings across the entire
        time span (max_records does not act like 'head' which takes only
        up to `max_records`)
        '''
        #Function compares string against it's checksum, returns True if
        #they match, returns False if they don't or the original string
        #does not have a checksum
        
        def nmea_is_valid(nmea_str):
            nmea_data, _, checksum = [x.strip() for x in nmea_str.partition('*')]
            if checksum == '':
                return False
            
            try:
                nmea_data = nmea_data.split('$')[1]
            except IndexError:
                return False

            calcd_checksum = '{0:02X}'.format(reduce(lambda x,y: x ^ ord(y), nmea_data, 0))
            
            return True if calcd_checksum == checksum else False
        
        #If we don't have any nmeas... can't return any nmeas
        if self.nmea is None:
            return None
        
        #Index for values matching desired nmea type
        nmea_indx = self.nmea.nmea_type == nmea_type
        
        #If we've supplied a talker ID, trim down matches
        if talker_id is not None:
            nmea_indx &= self.nmea.nmea_talker == talker_id
        
        #Return immediately if there's no matches
        if nmea_indx.sum() == 0:
            return None
               
        #Get the nmea strings matching nmea_type & talker_id (if supplied)
        
        nmea_strings = self.nmea.nmea_string.loc[nmea_indx]
        
        #Drop duplicates        
        if drop_duplicates:
            nmea_strings = nmea_strings.drop_duplicates()
                
        #Check against checksums if we want..
        if not ignore_checksum:
            nmea_strings = nmea_strings.loc[nmea_strings.apply(nmea_is_valid)]            

        #If we're left w/ 0, return None
        num_nmea = len(nmea_strings)
        if num_nmea == 0:
            return None
        elif (max_records is not None) and (num_nmea > max_records):
            indx_ = pd.np.round(pd.np.linspace(0, num_nmea-1, num=max_records, endpoint=True)).astype('int')
            nmea_strings = nmea_strings[indx_]

        #Attempt to parse remaining strings
        NMEA_CLASS = getattr(nmea, nmea_type, None)
        if NMEA_CLASS is None:
            log.warning('No NMEA parser for type %s', nmea_type)
            return nmea_strings
        
        def tryconvert(nmea_string):
            try:
                nmea_dict = NMEA_CLASS(nmea_string)
            except:
                nmea_dict = NMEA_CLASS()
            
            return pd.Series(nmea_dict)
        
        nmea_df = nmea_strings.apply(tryconvert)
        nmea_df = nmea_df.join(nmea_strings)

        return nmea_df
    
    def get_nmea_types(self):
        '''
        :returns: :class:`pandas.DataFrame` or None
        
        Returns the number of distinct (unique timestamp + data string pair)
        NMEA messages split by NMEA type (i.e. GLL) and NMEA talker (i.e. GP)
        
        NMEA datagrams are often duplicated across .raw and .bot/.out
        files, the .nmea DataFrame is often inflated with duplicated messages
        (differing only in the 'file' attribute used for writing back to disk).
        
        '''
        if self.nmea is None:
            return None
        
        return self.nmea.drop_duplicates(cols=['nmea_string', 'reduced_timestamp']).groupby(['nmea_type', 'nmea_talker']).size()

    def check_timestamps(self, expected_offset=0, ignore_checksum=False,
                         max_records=None, adjust_timestamps=False,
                         max_offset=None, min_offset=None):
        '''
        :param expected_offset:  Expected UTC offset in seconds
        :type expected_offset: int
        
        :param ignore_checksum: Ignore checksum validation for NMEA data
        :type ignore_checksum: bool
        
        :param max_records: Maximum number NMEA strings to use
        :type max_records: int
        
        :param adjust_timestamps:  Automatically adjust timestamps after offset calculation
        :type  adjust_timestamps:  bool

        :param max_offset:  Maximum allowed offset (when auto-adjusting timestamps)
        :type max_offset: float

        :param min_offset:  Minimum enforced offset (when auto-adjusting timestamps)
        :type min_offset: float

        :returns: dict
        
        :raises: ValueError if an abs(adjustment_offset) > max_offset when
            auto-adjusting timestamps

        To check consistancy:
            
            -  A list of original filenames contained within the reader object,
                (i.e. values of data.file, nmea.file, etc.) is collected.
                
            -  If the reader object contains GPS data (NMEA datagrams of type
               GGA or GLL), this data is used to calculate the offset between
               actual UTC time and UTC time computed by SIMRAD.  If the 
               aquisition computer's local timezone was set correctly, this
               offset should be minimal, but may still be non-zero due to clock
               drifts.
               
            -  If the reader object contains no GPS data, or there is not 
               enough valid GPS fixes, the UTC offset will be inferred from the
               difference between the timestamp in the filename and the first
               available datagram, and the value given by `expected offset`
               
        The returned dictionary is keyed by filename, and contains the
        following values.  
        
        'Offset' here refers to the difference between actual UTC 
        (as reported by GPS or as expected by shifting the filename
        timestamp by `expected_offset`) and UTC recorded in data.  All
        values are in seconds:
        
            :param max_offset:  Maximum offset (or None if no GPS data)
            :param min_offset:  Minimum offset (or None if no GPS data)
            :param std_offset:  Standard deviation (or None if no GPS data)
            :param mean_offset: Mean offset.
            
        When clocks are set correctly, mean_offset should be small.  To correct
        for clock skews, this offset value can be supplied to 
        :member:`RawReader.adjust_timestamp`

        If `adjust_timestamps`=True, the offset values calculated will be used
        to adjust file timestamps using :func:`adjust_timestamps` for you with
        a few safeguards:

            Files with timestamp offset magnitudes < :param min_offset: will
            not be adjusted.

            Any offset magnitude > :param max_offset: will raise a 
            ValueError exception
        '''
        
        #Get all filenames in this reader object
        first_timestamps = {}
        for df_name in ['data', 'tags', 'nmea', 'bottom']:
            df = getattr(self, df_name, None)
            
            if df is None:
                continue
            
            
            filenames = df.file.unique()
            grouped = df.groupby('file')
            for filename, group in grouped:
                
                first_timestamp = group['reduced_timestamp'].iloc[0]
                prev_timestamp = first_timestamps.get(filename, None)
                
                if prev_timestamp is None:
                    first_timestamps[filename] = first_timestamp
                
                elif first_timestamp < prev_timestamp:
                    first_timestamps[filename] = first_timestamp
            
        filenames = list(first_timestamps.keys())

        gps_df = pd.DataFrame()
        def tryconvert(float_time):
            try:
                return pd.datetime.strptime('{0:06d}'.format(int(float_time)), '%H%M%S').time()
            except:
                return pd.np.nan
        
        #Comparing to GPS time is tricky because the GPS NMEA code does not include the
        #date, so we must discover midnight crossings ourselves.  Here we assume the
        #GPS NMEA data is accurate and the file timestamp is within one hour of GPS time
        #(possibly) from correction applied above                    
 
        #First stip, gather all GPS data.  We're forced to use full datetime
        #objects for difference opperations, and the GPS data lacks a date.
        #Use the date from the the data timestamps for year/month/day
        
        nmea_types = self.get_nmea_types()
        if nmea_types is not None:                
            for nmea_type in ['GGA', 'GLL']:
                if nmea_type not in nmea_types:
                    continue
                num_nmea = nmea_types[nmea_type].sum()
                
                if num_nmea < 10:
                    log.warning('  Not enough %s NMEAs available...', nmea_type)
                    continue
                
                _df = self.get_nmea(nmea_type, talker_id=None, ignore_checksum=ignore_checksum,
                                    max_records=max_records, drop_duplicates=False)        
            
                if _df is None:
                    log.warning('  No valid %s NMEAs -- try ignore_checksum=True?', nmea_type)
                    continue

                _df['gps_time'] = _df.UTC.apply(tryconvert)
                
                _df = _df.dropna(axis=0, how='any', subset=['gps_time'])
#                _df = _df.ix[~pd.isnull(_df.gps_time)]
                _df.reset_index(drop=False, inplace=True)
                gps_df = gps_df.append(_df[['reduced_timestamp', 'gps_time']], ignore_index=True)

        
        if len(gps_df) > 0:
            #Drop duplicate gps_time's ?
    #        gps_df.drop_duplicates(cols='gps_time', inplace=True)
            
            #Reindex
            gps_df.drop_duplicates(cols='reduced_timestamp', inplace=True)
            
            file_hour = gps_df.reduced_timestamp.apply(lambda x: x.hour)
            gps_hour  = gps_df.gps_time.apply(lambda x: x.hour)
            
            
            add_day_indx = (file_hour == 23) & (gps_hour < 12)
            sub_day_indx = (file_hour <  12) & (gps_hour == 23)
            
            gps_df['gps_timestamp'] = pd.to_datetime(gps_df.reduced_timestamp.apply(lambda x: str(x.date())) + \
                    gps_df.gps_time.apply(lambda x: ' ' + str(x))).astype(pd.datetime).apply(lambda x: pytz_utc.localize(x))
                    
            gps_df.gps_timestamp[add_day_indx] = gps_df.gps_timestamp[add_day_indx] + pd.datetools.timedelta(days=1)
            gps_df.gps_timestamp[sub_day_indx] = gps_df.gps_timestamp[sub_day_indx] - pd.datetools.timedelta(days=1)        
    
            gps_df.set_index('reduced_timestamp', drop=False, inplace=True)
            gps_df = gps_df.join(self.nmea.file, how='left')
            
            has_gps_nmea = True
        else:
            log.warning('  No valid GPS datagrams available for timestamp checking')
            has_gps_nmea = False
           

        clock_offsets = {}
        for filename in filenames:
            if has_gps_nmea:
                indx_ = gps_df.file == filename
                offset = (gps_df.reduced_timestamp[indx_] - gps_df.gps_timestamp[indx_]).apply(lambda x: x / pd.np.timedelta64(1, 's'))
                clock_offsets[filename] = dict(mean_offset = offset.mean(),
                                               max_offset  = offset.max(),
                                               min_offset  = offset.min(),
                                               std_offset  = offset.std())
                log.info('%s:  mean:  %.4e, min:  %.4e, max:  %.4e, std:  %.4e' %(filename,
                    clock_offsets[filename]['mean_offset'], clock_offsets[filename]['min_offset'],
                    clock_offsets[filename]['max_offset'], clock_offsets[filename]['std_offset']))   
            else:
                file_timestamp = get_datetime_from_filename(os.path.basename(filename))
                first_data_timestamp = first_timestamps[filename]
                clock_offsets[filename] = dict(mean_offset = (first_data_timestamp - file_timestamp).total_seconds() + expected_offset,
                                               max_offset = None,
                                               min_offset = None,
                                               std_offset = None)
                log.info('%s:  mean:  %.4e, min:  --, max:  --, std:  --' %(filename,
                    clock_offsets[filename]['mean_offset']))

        
        #Adjust timestamps automatically if desired
        if adjust_timestamps:

            #Create a copy of the offset dictionary
            adj_offsets = {}
            for file_, offset_dict in clock_offsets.items():
                #Replace offsets < min_offset w/ 0 to skip adjustment for these files
                if (min_offset is not None) and (abs(offset_dict['mean_offset']) < min_offset):
                    adj_offsets[file_] = 0

                #Throw ValueError if offset > max_offset
                elif (max_offset is not None) and (abs(offset_dict['mean_offset']) > max_offset):
                    err_str = 'Mean offset for %s > max magnitude allowed (%f)' %(file_, abs(offset_dict['mean_offset']))
                    raise ValueError(err_str)
                
                #Otherwise use the mean_offset value for adjustment
                else:
                    adj_offsets[file_] = offset_dict['mean_offset']

            #Adjust timestamps
            self.adjust_timestamps(offset=adj_offsets)

        return clock_offsets
  
    def adjust_timestamps(self, offset):
        '''
        :param offset: Dictionary of timestamp adjustments (in seconds)
        :type offset: dict
        
        
            
        This function adjusts all 'reduced_timestamp' quantities by `offset`
        seconds, then re-computes simrad 'high_date' and 'low_date' for all
        datagrams to reflect the adjustment.

        The dictionary `offsets` can be a simple dictionary like::

            offsets = {'path\\to\\some\\file.raw': correction_value,
                       'path\\to\\some\\other_file.raw':  correction_value}

        or the output from :func:`check_timestamps`::

            offsets = {'path\\to\\some\\file.raw': {'max_offset': 0.8
                                'mean_offset': 4.67,
                                'min_offset': 0.36,
                                'std_offset': 0.03},
                       ...
                       }
                       
        Adjustment values should satisfy:
            correct_time = current_timestamp - offset

        When the output dictionary from check_timestamps is provided, 
        the actual value used for correction is `mean_offset`
        '''
        def unix_to_nt_dict(x):
            low_nt, high_nt = unix_to_nt(x)
            return dict(low_date=low_nt, high_date=high_nt)

        for df_name in ['data', 'tags', 'nmea', 'bottom']:
            df = getattr(self, df_name, None)

            if df is None:
                continue

            df.reset_index(drop=True, inplace=True)
            grouped = df.groupby('file')
            
            for filename, group in grouped: 
                   
                sec_adj = offset.get(filename, 0)

                #Check if we passed a dictonary structure like what
                #check_timestamps() returns, and if so choose -mean_offset as
                #the adjustment
                if isinstance(sec_adj, dict):
                    sec_adj = sec_adj.get('mean_offset', 0)

                if sec_adj == 0:
                    continue

#                num_rows = row_indx.sum()
                #Adjust reduced_timestamps
                adjusted_timestamps = group['reduced_timestamp'] - pd.datetools.timedelta(seconds=sec_adj)
                df.update(adjusted_timestamps)
                
                #Adjust NT-date tuples

                
                new_nt_dates = adjusted_timestamps.apply(lambda x: pd.Series(unix_to_nt_dict(x)))
                df.update(new_nt_dates)
#                new_low_dates = new_nt_dates.apply(lambda x: x[0])
#                new_low_dates.name = 'low_date'
#                new_high_dates = new_nt_dates.apply(lambda x: x[1])
#                new_high_dates.name = 'high_date'
#                
#                df.high_date.update(new_high_dates)
#                df.low_date.update(new_low_dates)
            

            if df_name == 'data':
                index_cols = ['channel', 'reduced_timestamp']
            else:
                index_cols = 'reduced_timestamp'
            
            #Reset dataframe index
            df.set_index(index_cols, drop=False, inplace=True)


    def interpolate_ping_gps(self, nmea_type=None, ignore_checksum=False,
                             max_jump=None, max_iterations=40):
        '''
        :param nmea_type:  Type of NMEA you want (case-sensitive!)
        :type nmea_type: str
        
        :param ignore_checksum: Ignore checksum validation
        :type ignore_checksum: bool
        
        :param max_jump:  Maximum allowed instantaneous GPS position jump, in nmi
        :type max_jump: float
        
        Interpolates GPS NMEA data to per-ping intervals.
        
        'lat' and 'lon' columns will be appended to the
        RawReader.data dataframe.
        
        Longitude will be converted to Westerly coordinates
        (W is positive, E is negative)
        
        If max_jump is specified an attempt is made to look for and correct
        poor GPS fixes producing unreasonably large instantaneous jumps greater
        than the provided value.  A value of 0.1 is relatively safe to use.
        '''
        valid_nmea_types = ['GLL', 'GGA']
        
        if self.nmea is None:
            raise ValueError('No nmea data available')
        
        nmea_count = self.nmea.groupby('nmea_type').size()

        if nmea_type is None:
            nmea_type = self.prefered_nmeas.get('gps', valid_nmea_types[0])
            try:
                valid_nmea_types.pop(nmea_type)
            except:
                pass

        nmea_type_indx = 0            
        while not (nmea_type in nmea_count):
            log.info('No GPS datagrams of type %s', nmea_type)
            if nmea_type_indx == len(valid_nmea_types):
                log.error('No valid GPS types found...')
                self.data['dec_latitude'] = pd.np.nan
                self.data['dec_longitude'] = pd.np.nan
                return
            nmea_type = valid_nmea_types[nmea_type_indx]
            nmea_type_indx += 1

        log.info(  'Found %d datagrams for NMEA type %s', nmea_count[nmea_type], nmea_type)
        
        log.info('  Parsing and converting lat/lon to decimal degrees...')        
        gps_df = self.get_nmea(nmea_type, talker_id=None, ignore_checksum=ignore_checksum)        
        
        if gps_df is None:
            raise ValueError('No valid %s nmeas -- try ignore_checksum=True?' %(nmea_type))
        
        invalid_gps = gps_df['head'] == ''
        if invalid_gps.sum() > 0:
            log.warning('    %d datagrams failed parsing and will be ignored...', invalid_gps.sum())
            gps_df = gps_df.loc[~invalid_gps]

        def calc_decimal_degrees(x):
            try:
                d_, _, m_ = str(x).partition('.')
                d = int(d_[:-2])
                m = d_[-2:] + '.' + m_            
                dd = d + float(m) / 60.0
            except:
                dd = pd.np.nan
                
            return dd

        def check_direction(x):
            try:
                direction = x.lower()
            except:
                return pd.np.nan
            
            if direction == 'w':
                return 1
            elif direction == 'e':
                return -1
            else:
                return pd.np.nan
            
        gps_df['lat'] = gps_df['latitude'].apply(calc_decimal_degrees)
        gps_df['lon'] = gps_df['longitude'].apply(calc_decimal_degrees) * gps_df['lon_direction'].apply(check_direction)
        
        if not gps_df.index.is_unique:
            log.debug('  making raw-gps dataframe uniquely indexed...')
            gps_df = gps_df.reset_index(drop=False).drop_duplicates(cols='reduced_timestamp').set_index('reduced_timestamp', drop=True)

        log.info('  Interpolating data to ping timestamps...')
        interp_df = pd.DataFrame(index=self.data.index.get_level_values('reduced_timestamp').unique()).join(gps_df, how='outer')
        interp_df['lat'] = interp_df['lat'].interpolate(method='time')
        interp_df['lon'] = interp_df['lon'].interpolate(method='time')

        if max_jump is not None:
            log.info('  Checking for distance jumps > %.3fnmi. Max # of iterations: %d', max_jump, max_iterations)
            calc_distance = lambda x: gps.gps_distance(x['lat0'], 
                    x['lon0'], x['lat'], x['lon'], 
                    r=6356.78)            
            
            for loop_num in range(max_iterations):                
                interp_df['lat0'] = interp_df['lat'].shift(periods=1)
                interp_df['lon0'] = interp_df['lon'].shift(periods=1)
                
                interp_df['distance'] = interp_df.apply(calc_distance, axis=1) / 1852.0
                interp_df.distance[0] = 0
                
                bad_gps_indx = interp_df.distance > max_jump
                num_bad_gps = bad_gps_indx.sum()
                if num_bad_gps:
                    log.warning('    Loop %d found %d large jumps', loop_num, num_bad_gps)
                    shifted_bad_gps_indx = bad_gps_indx.shift(periods=1).astype('bool')
                    if not bad_gps_indx.iloc[0]:
                        shifted_bad_gps_indx.iloc[0] = False

                    bad_gps_indx |= shifted_bad_gps_indx
                    #Remove both sides of each large jump
                    interp_df = interp_df.loc[~bad_gps_indx]
                else:
                    break
            #Reset index to data timestamps & interpolate by time    
            interp_df =  pd.DataFrame(index=self.data.index.get_level_values('reduced_timestamp').unique()).join(interp_df[['lat', 'lon']], how='outer')
            interp_df['lat'] = interp_df['lat'].interpolate(method='time')
            interp_df['lon'] = interp_df['lon'].interpolate(method='time')
        
        log.debug('    Backfilling NaN values...')
        interp_df.lat.fillna(method='backfill', inplace=True)
        interp_df.lon.fillna(method='backfill', inplace=True)

        if 'lat' in self.data:
            log.debug('    Removing old interpolated lat. values...')
            del self.data['lat']
            
        if 'lon' in self.data:
            log.debug('    Removing old interpolated lon. values...')
            del self.data['lon']

        self.data = self.data.join(interp_df[['lat', 'lon']], on='reduced_timestamp')
        
 
    def interpolate_ping_dist(self, nmea_type=None, ignore_checksum=False, max_jump=None,
        max_iterations=40, units='nmi'):
        '''
        :param nmea_type:  Type of NMEA you want (case-sensitive!)
        :type nmea_type: str
        
        :param ignore_checksum: Ignore checksum validation
        :type ignore_checksum: bool
        
        :param max_jump:  Maximum allowed instantaneous GPS position jump, in nmi
        :type max_jump: float
        
        :param max_iterations:  Maximum number of iterations allowed when attempting
            to smooth large jumps in the GPS track.
        :type max_iterations: int

        :param units:  Distance units to use (default=nmi)
        :type units: str

        Valid NMEA types are:  'VLW', 'GLL', 'GGA'
        Valid unit types are:  'nmi', 'm'

        VLW contains distance directly, GPS datagrams GLL and GGA will
        first interpolate GPS data to per-ping intervals, then estimate
        vessel distance from gps fixes.
        
        If max_jump is specified an attempt is made to look for and correct
        poor GPS fixes producing unreasonably large instantaneous jumps greater
        than the provided value.  A value of 0.1nmi is relatively safe to use.    
        '''
        
        if self.nmea is None:
            raise ValueError('No nmea data available')

        valid_nmea_types = ['VLW', 'GLL', 'GGA']
        gps_nmea_types   = ['GLL', 'GGA']
        
        nmea_count = self.nmea.groupby('nmea_type').size()

        if nmea_type is None:
            nmea_type = self.prefered_nmeas.get('distance', valid_nmea_types[0])
        
        nmea_type = nmea_type.upper()    
        if nmea_type not in valid_nmea_types:
            raise ValueError('%s is not a supported NMEA type for distance interpolation' %(nmea_type))
        
        else:            
            _ = valid_nmea_types.remove(nmea_type)

        try:
            units = units.lower()
        except:
            raise ValueError('Unable to convert unit string to lower-case.. is it a string?')

        if units not in ['m', 'nmi']:
            raise ValueError("Unknown unit string: %s.  Use 'm' or 'nmi'" % (units,))

        nmea_type_indx = 0
        while not (nmea_type in nmea_count):
            log.info('No datagrams of type %s', nmea_type)
            if nmea_type_indx == len(valid_nmea_types):
                log.warning('No valid distance types found...')
                self.data['dec_latitude'] = pd.np.nan
                self.data['dec_longitude'] = pd.np.nan
                return
            nmea_type = valid_nmea_types[nmea_type_indx]
            nmea_type_indx += 1        
        
        if nmea_type == 'VLW':
            try:
                nmea_df = self.get_nmea('VLW', talker_id=None, ignore_checksum=ignore_checksum)['total_distance']
            except TypeError:
                log.warning('No valid VLW nmeas -- try ignore_checksum=True?')
                log.warning('Attmpting to derive distance from GPS instead...')
                nmea_df = None
                nmea_type = 'GLL'
            
            if nmea_df is not None:
                nmea_df.name = 'distance'
                
                interp_df    = pd.DataFrame(index=self.data.index.get_level_values('reduced_timestamp').unique()).join(nmea_df, how='outer')
                log.info('Interpolating VLW fixes...')            
                interp_df['distance'] = interp_df['distance'].interpolate(method='time')
                interp_df.fillna(method='backfill', inplace=True, axis=0)
       
        if nmea_type in gps_nmea_types:
            if ('lat' not in self.data.columns) or \
                ('lon' not in self.data.columns):
                log.info('Interpolating GPS fixes to estimate distance')
                self.interpolate_ping_gps(nmea_type, ignore_checksum=ignore_checksum, max_jump=max_jump)

            calc_distance = lambda x: gps.gps_distance(x['lat0'], 
                    x['lon0'], x['lat'], x['lon'], 
                    r=6356.78)            
            
            
            interp_df = self.data[['reduced_timestamp', 'lat', 'lon']].drop_duplicates('reduced_timestamp').reset_index('channel', drop=True)
            #Resort index by timestamp
            interp_df.sort_index(axis=0, inplace=True)
                            
            interp_df['lat0'] = interp_df['lat'].shift(periods=1)
            interp_df['lon0'] = interp_df['lon'].shift(periods=1)
            
            log.info('  Calculating differential ping distances...')
            interp_df['distance'] = interp_df.apply(calc_distance, axis=1)
            interp_df['distance'][0] = 0
            
            if units == 'm':
                pass

            elif units == 'nmi':
                log.debug('    converting distance from meters -> nautical miles')
                interp_df['distance'] = interp_df['distance'] / 1852.0

            else:
                raise RuntimeError('Illegal unit string: %s.  Should have been caught before..' %(units,))
            
            log.info('  Calculating running distance...')
            interp_df['distance'] = interp_df['distance'].cumsum() 

        if 'distance' in self.data:
            log.debug('    Removing old calculated distance values...')
            del self.data['distance']

        log.debug('  Joining... ')
        self.data = self.data.join(interp_df['distance'], on='reduced_timestamp')

                
                
    def interpolate_ping_bottom_range(self):
        '''
        Interpolates and smooths bottom estimates to per-ping intervals.
        Bottom estimates are RANGE based (adjusted for transducer depth)
        and appended to the RawReader.data dataframe in the 'bottom' column.
        
        Usually a bottom estimate is produced for each ping, but sometimes
        they are missed.  This function will:
            
            1.  Fill any gaps in the bottom estimate record
            2.  Replace bottom estimates of '0' in the data w/ interpolated
                values from adjacent estimates
                
        If RawReader.bottom is None (no bottom esitamtes to interpolate from),
        RawReader.data['bottom'] is set to NaN
        '''        

        if self.bottom is None:
            log.error('No bottom data available to interpolate...')
            raise ValueError('No bottom data available to interpolate')
 
        
        #Clear previous bottom values if calculated already
        try:
            del self.data['bottom']
        except KeyError:
            pass

        #Creates a DataFrame with reduced_timestamp for index and integer
        #column labels representing channel indices.  Values are depth
        
        grouped = self.bottom.groupby('transceiver_count')
        
        bottom_df = pd.DataFrame([])
        for transceiver_count, group in grouped:
            for channel in range(1, transceiver_count + 1):
                bottom_df = pd.concat([bottom_df, pd.DataFrame(group.apply(lambda x: pd.Series(dict(channel=int(channel), bottom=x[0][channel-1])), raw=True, axis=1))])
        
        bottom_df.index.name = 'reduced_timestamp'
        bottom_df.reset_index(drop=False, inplace=True)
        bottom_df.set_index(['channel', 'reduced_timestamp'], inplace=True)
        
        
        bottom_df = pd.DataFrame(index=self.data.index).join(bottom_df, how='outer')
        
        #Set 0 depth values to nan for interpolation to catch
        bottom_df[bottom_df['bottom'] == 0] = pd.np.nan

        for channel in bottom_df.index.get_level_values('channel').unique():
            if bottom_df.ix[channel, :]['bottom'].count() == 0:
                log.warning('Channel %d has no valid bottom data', channel)
                continue
     
            bottom_df.ix[channel, :]['bottom'] = bottom_df.ix[channel, :]['bottom'].interpolate(method='time').fillna(method='backfill')
            
        self.data = self.data.join(bottom_df, how='left')
       
        #Adjust depth based on calibration soundspeed
        log.debug('Checking for sound velocity calibration data')
        for channel in self.data.index.get_level_values('channel').unique():
           
            #Check for custom sound speed
            try:
                cal_sound_speed = self.calibration_params[channel]['sound_velocity']
            except KeyError:
                #No sound velocity in calibration data, no adjustnmet needed for this channel
                continue

            log.debug('  Channel %d has sound_velocity:  %7.3f m/s', channel, cal_sound_speed)
            chan_indx = self.data.channel == channel
            
            sound_speed_frac_chng = cal_sound_speed / self.data.sound_velocity[chan_indx]
            transducer_depth  = self.data.transducer_depth[chan_indx]
            
            new_bottom_depths = self.data.bottom[chan_indx] * sound_speed_frac_chng -\
                transducer_depth * (sound_speed_frac_chng - 1)
                
            log.debug('    Adjusting bottom depths by %f meters.', new_bottom_depths[0] - self.data.bottom[0])
            self.data.bottom[chan_indx] = new_bottom_depths
            
            
        #Adjust for transducer depth as recorded by transceiver
        #We ignore the calibration transducer_depth if present -- 
        #The offset used in depth data is the offset 'known' at 
        #time of aquisition and listed in ping header info.
        
        self.data.bottom -= self.data.transducer_depth
    
    def append_timeseries(self, other, inplace=False,
                          max_time_gap=None):
        '''
        :param other: Other RawReader instance
        :type other: :class:`RawReader`
        
        :param inplace:  Append other data in place
        :type inplace: bool
        
        :param max_time_gap:  Maximum allowed time offset between timeseries.
        
        Concatenates two RawReader instances together.
        
        A new RawReader object with the appended data is returned
        if inplace is False, otherwise `other`'s data will be appended in
        place to this object. 
        
        :max_time_gap: can be a float number of seconds, a :class:`datetime.timedelta`
        object, or None to disable the check.
        
         
        '''
        if not isinstance(other, RawReader):
            raise TypeError('Expected another %s instance' %(type(self)))
        
        #Some assurance that the transceiver configs are similar...
        if len(self.config['transceivers']) != len(other.config['transceivers']):
            raise ValueError('Transceiver counts differ.')
        
        for channel_num, transceiver in list(self.config['transceivers'].items()):
            other_transceiver = other.config['transceivers'].get(channel_num, None)
            
            if other_transceiver is None:    
                ValueError('Missing channel # %d' %(channel_num))
                
            
            for field in ['channel_id', 'frequency']:
                if transceiver.get(field, None) != other_transceiver.get(field, None):
                    raise ValueError('Missmatch on field %s for channel #%d' %(field, channel_num))

        if inplace:
            new = self
        else:
            new = RawReader()
            new.copy_dicts(other)
        
        #Check convert max_gap to datetime.timedelta
        if max_time_gap is not None:
            if isinstance(max_time_gap, (float, int)):
                max_time_gap = pd.datetools.timedelta(seconds=max_time_gap)
                
            elif isinstance(max_time_gap, pd.datetools.timedelta):
                pass
            
            else:
                raise TypeError('Expected a number or a datetime.timedelta object for max_time_gap')
            
  
        #Start appending dataframes
        for df_name in ['data', 'nmea', 'bottom', 'tags']:
            other_df = getattr(other, df_name, None)
            #'Other' have this dataframe?
            if other_df is not None:
                self_df = getattr(self, df_name, None)
                #Do we have this dataframe?
                if self_df is None:
                    #If not, just copy the 'other's attribute
                    setattr(new, df_name, other_df.copy())
                else:
                    #If so, append the other's attribute
                    if max_time_gap is not None:
                        other_timestamp = other_df.reduced_timestamp[0]
                        our_timestamp  = self_df.reduced_timestamp[-1]
                        
                        if (other_timestamp - our_timestamp) > max_time_gap:
                            err_str = 'Time difference between timeseries "{name:s}" exceeds maximum allowed value: {gap:f} > {max_gap:f}'.format(name=df_name,
                                                                    gap = (other_timestamp - our_timestamp).total_seconds(),
                                                                    max_gap=max_time_gap.total_seconds())
                            raise ValueError(err_str, (other_timestamp - our_timestamp).total_seconds())
                    
                    #For some reason the DataFrame.append member function drops
                    #timezone information on TimeSeries indexes.
                    #So here, after the append we rebuild the index from column
                    #data
                    self_df = self_df.append(other_df).reset_index(drop=True)
                    
                    if df_name == 'data':
                        indx_cols = ['channel', 'reduced_timestamp']
                    else:
                        indx_cols = 'reduced_timestamp'
                        
                    self_df = self_df.set_index(indx_cols, drop=False)
                    setattr(new, df_name, self_df.sort_index(axis=0, by=indx_cols))

        if not inplace:
            return new

    def truncate_timeseries(self, start_time=None, end_time=None, dayfirst=False,
                            inplace=False):
        '''
        :param start_time: Starting time of new series
        
        :param end_time:  Ending time of new series
        
        Removes data associated with timestamps before start_time and
        after end_time
        
        if start_time is None, the new series retains the original starting time.
        Similarly, if end_time is None, the new series retains the original end time
        
        Otherwise, start_time and end_time can be specified by anything that
        pandas' to_datetime methond recognizes.
        
        TZ-naive times will be treated as UTC.  TZ-aware times will be
        converted to UTC.
        '''
        
        if start_time is None and end_time is None:
            log.debug('Start and end times both None, nothing to do.')
            return
        
        if start_time is not None:
            start_time = pd.to_datetime(start_time, errors='raise',
                                        dayfirst=dayfirst, utc=True)
            if start_time.tzinfo is None:
                start_time = pytz_utc.localize(start_time)

            log.debug('Converted starting time to %s', start_time)
            
        if end_time is not None:
            end_time = pd.to_datetime(end_time, errors='raise',
                                        dayfirst=dayfirst, utc=True)
            if end_time.tzinfo is None:
                end_time = pytz_utc.localize(end_time)

            log.debug('Converted end time to %s', end_time)
        
        if inplace:
            other = self
        else:
            other = RawReader()
            other.copy_dicts(self)

        for df_name in ['data', 'nmea', 'tags', 'bottom']:
            df = getattr(self, df_name)
            
            if df is None:
                log.info('%s DataFrame is None, nothing to do.', df_name)
                continue
            
            selection_indx = pd.Series(True, index=df.index)
            
            if start_time is not None:
                selection_indx &= (df.reduced_timestamp >= start_time)
                
            if end_time is not None:
                selection_indx &= (df.reduced_timestamp <= end_time)
                
            log.debug('Retaining %d rows in %s', selection_indx.sum(), df_name)

            if selection_indx.sum() == 0:
                setattr(other, df_name, None)
            else:                        
                setattr(other, df_name, df[selection_indx])

        if not inplace:
            return other

    def _read_datagrams_from_file(self, filename, channel_names=None, channel_numbers=None,
            frequencies=None, first_ping_time=None, last_ping_time=None, 
            assume_monotonic=True, datagrams=None, ignore_datagram_types=None,
            desired_nmea_types=None):
        
        
        
        if datagrams is None:
            datagrams = {}
            
        if not isinstance(datagrams, dict):
            raise TypeError('Expected datagrams to be a dict')
            

        nmea_datagrams   = datagrams.setdefault('nmea', [])
        sample_datagrams = datagrams.setdefault('sample', [])
        tag_datagrams    = datagrams.setdefault('tag', [])
        bottom_datagrams = datagrams.setdefault('bottom', [])
        
        if ignore_datagram_types is not None:

            if isinstance(ignore_datagram_types, str):
                ignore_datagram_types = [ignore_datagram_types]

            log.info('  ignoring datagrams of types: %s', ignore_datagram_types)
        
        else:
            ignore_datagram_types = []

        if desired_nmea_types is not None:
            if isinstance(desired_nmea_types, str):
                desired_nmea_types = [desired_nmea_types]

            log.info('  keeping only NMEA datagrams of types: %s', desired_nmea_types)

        with RawSimradFile(filename, 'r') as fid:

            config_datagrams = {}
            while fid.peek()['type'].startswith('CON'):
                config_datagram = fid.read(1)
                if config_datagram['type'] in config_datagrams:
                    raise ValueError('Multiple config datagrams of type %s found', config_datagram['type'])

                config_datagrams[config_datagram['type']] = config_datagram
           
            channel_map  =  self._setup_config(config_datagrams, channel_names=channel_names,
                    channel_numbers=channel_numbers, frequencies=frequencies)
            
            num_channels = len(list(channel_map.keys()))
            num_sample_datagrams = 0
            num_sample_datagrams_skipped = 0
            num_unknown_datagrams_skipped = 0
            num_bottom_datagrams = 0
            num_nmea_datagrams   = 0
            num_nmea_datagrams_skipped = 0
            num_tag_datagrams    = 0
            num_skipped_before   = 0
            num_skipped_after    = 0
            num_datagrams_parsed = 0
            
            while True:
                try:
                    next_header = fid.peek()
                except SimradEOF:
                    break
                
                datagram_timestamp = nt_to_unix((next_header['low_date'], next_header['high_date']))
                num_datagrams_parsed += 1
                
                if (first_ping_time is not None) and ((first_ping_time - datagram_timestamp) > pd.datetools.timedelta(seconds=0)):
                #                        log.debug('Skipping %s datgram @ %s, %f seconds before first desired ping time',
                #                            next_header['type'], datagram_timestamp, (first_ping_time - datagram_timestamp).total_seconds())
                    fid.skip()
                    num_skipped_before += 1
                    continue
                
                elif (last_ping_time is not None) and ((datagram_timestamp - last_ping_time) > pd.datetools.timedelta(seconds=0)):
                #                        log.debug('Skipping %s datgram @ %s, %f seconds after last desired ping time',
                #                            next_header['type'], datagram_timestamp, (datagram_timestamp - last_ping_time).total_seconds())
                    
                    if not assume_monotonic:
                        fid.skip()
                        num_skipped_after += 1
                        continue
                    else:
                        log.info('Skipping remaining datagrams after %s', datagram_timestamp)
                        break
                
                elif next_header['type'] in ignore_datagram_types:
                    fid.skip()
                    continue
            
                new_datagram = fid.read(1)
                
                if new_datagram['type'].startswith('NME'):
                    if desired_nmea_types is None or new_datagram['nmea_type'] in desired_nmea_types:
                        nmea_datagrams.append(new_datagram)
                        nmea_datagrams[-1]['file'] = filename
                        num_nmea_datagrams += 1
                    
                    else:
                        num_nmea_datagrams_skipped += 1
                
                elif new_datagram['type'].startswith('RAW'):
                    if new_datagram['channel'] in channel_map:
                        sample_datagrams.append(new_datagram)
                        sample_datagrams[-1]['channel'] = channel_map[new_datagram['channel']]
                        sample_datagrams[-1]['file'] = filename
                        sample_datagrams[-1]['file_ping'] = num_sample_datagrams / len(channel_map)
                        num_sample_datagrams += 1
                    
                    else:
                        num_sample_datagrams_skipped += 1
                
                elif new_datagram['type'].startswith('DEP'):
                    bottom_datagrams.append(new_datagram)
                    bottom_datagrams[-1]['file'] = filename
                    
                    if len(bottom_datagrams[-1]['depth']) != num_channels:
                        bot_datagram = bottom_datagrams[-1]
                        bot_datagram['transceiver_count'] = num_channels
                        new_depths = pd.np.empty((num_channels,))
                        new_refl   = pd.np.empty((num_channels,))
                        new_unused = pd.np.zeros((num_channels,))
                        for old_channel, new_channel in list(channel_map.items()):
                            new_depths[new_channel-1] = bot_datagram['depth'][old_channel-1]
                            new_refl[new_channel-1] = bot_datagram['reflectivity'][old_channel-1]
                            new_unused[new_channel-1] = bot_datagram['unused'][old_channel-1]
                            
                        bot_datagram['depth'] = new_depths
                        bot_datagram['reflectivity'] = new_refl
                        bot_datagram['unused'] = new_unused
                
                    num_bottom_datagrams += 1
                
                elif new_datagram['type'].startswith('BOT'):
                    bottom_datagrams.append(new_datagram)
                    bottom_datagrams[-1]['file'] = filename
                    
                    if len(bottom_datagrams[-1]['depth']) != num_channels:
                        bot_datagram = bottom_datagrams[-1]
                        bot_datagram['transceiver_count'] = num_channels
                        new_depths = pd.np.empty((num_channels,))
                        for old_channel, new_channel in list(channel_map.items()):
                            new_depths[new_channel-1] = bot_datagram['depth'][old_channel-1]
                
                        bot_datagram['depth'] = new_depths

                    num_bottom_datagrams += 1
                
                elif new_datagram['type'].startswith('TAG'):
                    tag_datagrams.append(new_datagram)
                    tag_datagrams[-1]['file'] = filename
                    num_tag_datagrams += 1
                
                else:
                    log.warning('Skipping unkown datagram type: %s @ %s', new_datagram['type'], datagram_timestamp)
                    num_unknown_datagrams_skipped += 1
                
                if not (num_datagrams_parsed % 10000):
                    log.debug('    Parsed %d datagrams (%d sample, %d NMEA, %d tag, %d bottom).', num_datagrams_parsed,
                             num_sample_datagrams, num_nmea_datagrams, num_tag_datagrams, num_bottom_datagrams)


        num_datagrams_skipped = num_unknown_datagrams_skipped + num_skipped_before + num_skipped_after +\
           num_sample_datagrams_skipped + num_nmea_datagrams_skipped
           
        num_datagrams_read = num_tag_datagrams + num_sample_datagrams + \
           num_bottom_datagrams + num_nmea_datagrams
           
        log.info('  Read %d datagrams (%d skipped, %d sample, %d NMEA, %d tag, %d bottom).', num_datagrams_read, 
           num_datagrams_skipped, num_sample_datagrams, num_nmea_datagrams, num_tag_datagrams, num_bottom_datagrams)                
        

        return datagrams

    def append_file(self, file, channel_names=None, channel_numbers=None,
        frequencies=None, first_ping_time=None, last_ping_time=None,
        assume_monotonic=True, ignore_datagram_types=None, desired_nmea_types=None):
        '''
        :param file:  Filename or list of filenames to load
        :type file: str or [str]
        
        :param channel_names: List of channel ID's to load, or None for all
        :type channel_names: [str] or None
        
        :param channel_numbers: List of channel numbers (1-indexed) to load, or None for all
        :type channel_numbers: [int]
        
        :param frequencies: List of frequencies to load, in Hz, or None for all.
        :type frequencies: [int]
        
        :param first_ping_time:  Ignore all data before this time.
        :type first_ping_time: str or datetime.datetime
        
        :param last_ping_time: Ignore all data after this time.
        :type last_ping_time:  str or datetime.datetime
        
        :param prefered_nmeas:  Preferened NMEA datagrams for GPS and Distance calculations.
        :type prefered_nmea: dict
        
        :param assume_monotonic:  Assume data is monotonically increasing in time
        :type assume_monotonic: bool
        '''
   
        file_names = []

        if isinstance(file, str):
            file_names.append(file)
        else:
            file_names.extend(file)

        if first_ping_time is not None:
            first_ping_time = pd.to_datetime(first_ping_time, errors='raise', utc=True)
#            log.info('Skipping data before %s', first_ping_time)
            if first_ping_time.tzinfo is None:
                log.debug('Converting first_ping_time naive TZ to UTC')
                first_ping_time = first_ping_time.replace(tzinfo=pd.datetools.dateutil.tz.tzutc())
        
        if last_ping_time is not None:
            last_ping_time = pd.to_datetime(last_ping_time, errors='raise', utc=True)
#            log.info('Skipping data after %s', last_ping_time)
            if last_ping_time.tzinfo is None:
                log.debug('Converting last_ping_time naive TZ to UTC')
                last_ping_time = last_ping_time.replace(tzinfo=pd.datetools.dateutil.tz.tzutc())

        datagrams = dict(sample=[], nmea=[], tag=[], botttom=[])

        files = {}
        for ext, file_name in [(os.path.splitext(x)[1].lower(), x) for x in file_names]:
            if ext == '.raw':
                raw_list = files.setdefault('raw', [])
                raw_list.append(file_name)
            elif ext == '.out' or ext == '.bot':
                bot_list = files.setdefault('bot', [])
                bot_list.append(file_name)
            else:
                log.warning('Extension %s not recognized, skipping %s', ext, file_name)
                
        
        for file_indx, file_name in enumerate(files.get('raw', [])):
            log.info('Reading raw file %d:  %s', file_indx + 1, file_name)

            _ = self._read_datagrams_from_file(filename=file_name, 
                channel_names=channel_names, channel_numbers=channel_numbers, 
                frequencies=frequencies, first_ping_time=first_ping_time, 
                last_ping_time=last_ping_time, assume_monotonic=False,
                datagrams=datagrams, ignore_datagram_types=ignore_datagram_types,
                desired_nmea_types=desired_nmea_types)

        
        if len(datagrams['sample']) > 0:
            sample_timestamps    = [x['timestamp'] for x in datagrams['sample']] 
            first_ping_time = min(sample_timestamps)
            last_ping_time = max(sample_timestamps)
            
            log.info('Data spans time range of %s to %s', first_ping_time, last_ping_time)
            del sample_timestamps
            
        
        for file_indx, file_name in enumerate(files.get('bot', [])):
            log.info('Reading bottom file %d:  %s', file_indx + 1, file_name)

            _ = self._read_datagrams_from_file(filename=file_name, 
                channel_names=channel_names, channel_numbers=channel_numbers, 
                frequencies=frequencies, first_ping_time=first_ping_time, 
                last_ping_time=last_ping_time, assume_monotonic=True,
                datagrams=datagrams, ignore_datagram_types=ignore_datagram_types,
                desired_nmea_types=desired_nmea_types)
        
        total_sample_datagrams = len(datagrams['sample'])
        total_nmea_datagrams   = len(datagrams['nmea'])
        total_tag_datagrams    = len(datagrams['tag'])
        total_bottom_datagrams = len(datagrams['bottom'])
        total_datagrams = total_sample_datagrams + total_nmea_datagrams + total_tag_datagrams + total_bottom_datagrams
        
        log.info('Read %d datagrams total (%d sample, %d NMEA, %d tag, %d bottom)',
            total_datagrams, total_sample_datagrams, total_nmea_datagrams, total_tag_datagrams, total_bottom_datagrams)

        
        reduce_timestamp = lambda row: nt_to_unix((round(row['low_date'], -5), row['high_date']))
        
        log.info('Creating data structures...')
        if total_sample_datagrams > 0:
            log.debug('  Creating sample data DataFrame')
            if self.data is None:
                self.data = pd.DataFrame(datagrams['sample'])
            else:
                self.data.reset_index(inplace=True, drop=True)
                self.data   = self.data.append(pd.DataFrame(datagrams['sample']), ignore_index=True)
                
            #Recalculate timestamps w/ reduced resolution & use for indexing
            self.data['reduced_timestamp'] = self.data.apply(reduce_timestamp, axis=1)
            self.data.sort_values(by='reduced_timestamp', inplace=True, ascending=True)
            self.data.set_index(['channel', 'reduced_timestamp'], drop=False, inplace=True)

        if total_nmea_datagrams > 0:
            log.debug('  Creating nmea DataFrame')
            if self.nmea is None:
                self.nmea   = pd.DataFrame(datagrams['nmea'])
            else:
                self.nmea.reset_index(inplace=True, drop=True)
                self.nmea   = self.nmea.append(pd.DataFrame(datagrams['nmea']), ignore_index=True)

            self.nmea['reduced_timestamp'] = self.nmea.apply(reduce_timestamp,axis=1)
            self.nmea.sort_values(by='reduced_timestamp', inplace=True, ascending=True)
            self.nmea.set_index('reduced_timestamp', drop=False, inplace=True)

        if total_tag_datagrams > 0:
            log.debug('  Creating tag DataFrame')
            if self.tags is None:
                self.tags    = pd.DataFrame(datagrams['tag'])
            else:
                self.tags.reset_index(inplace=True, drop=True)
                self.tags    = self.tags.append(pd.DataFrame(datagrams['tag']), ignore_index=True)
            
            self.tags['reduced_timestamp'] = self.tags.apply(reduce_timestamp, axis=1)
            self.tags.sort_index(by='reduced_timestamp', inplace=True, ascending=True)
            self.tags.set_index(['reduced_timestamp'], drop=False, inplace=True)                
            

        if total_bottom_datagrams > 0:
            log.debug('  Creating bottom data DataFrame')
            if self.bottom is None:
                self.bottom = pd.DataFrame(datagrams['bottom'])
            else:
                self.bottom.reset_index(inplace=True, drop=True)
                self.bottom = self.bottom.append(pd.DataFrame(datagrams['bottom']), ignore_index=True)
                
            self.bottom['reduced_timestamp'] = self.bottom.apply(reduce_timestamp, axis=1)
            self.bottom.sort_index(by='reduced_timestamp', inplace=True, ascending=True)
            self.bottom.set_index(['reduced_timestamp'], drop=False, inplace=True)                   



    def save(self, prefix='', suffix='', date_fmt='D%Y%m%d-T%H%M%S', 
        path=None, max_size=55, overwrite=False):
        '''
         :param prefix: File prefix -- before date formatted string
         :type prefix: str
         
         :param suffix:  File suffix -- after date formatted string (exclusive of file extenion
         :type suffix: str
         
         :param date_fmt:  Timestamp format
         :type date_fmt: str
         
         :param path:  Output path, defaults to current directory
         :type path: str
         
         :param max_size: Maximum file size in MB
         :type max_size: float
                
         :param overwrite:  Overwrite existing files
         :type overwrite: bool
         
         :returns: list of (bot_filename, raw_filename) pair tuples

         Saves data to disk.  Filenames are constructed using 'prefix' + 'date_fmt' + 'suffix'
         triplets, so for traditional names like: 'L004-D20110705-T224423-ES60.raw', use
             prefix = 'L004-'
             date_fmt = 'D%Y%m%d-T%H%M%S' (Default)
             suffix = '-ES60'
         
         '''        
        
        DGRAM_PARSE_KEY = {'RAW': parsers.SimradRawParser(),
                          'CON': parsers.SimradConfigParser(),
                          'TAG': parsers.SimradAnnotationParser(),
                          'NME': parsers.SimradNMEAParser(),
                          'BOT': parsers.SimradBottomParser(),
                          'DEP': parsers.SimradDepthParser()}
    
        if path is None:
            path = os.getcwd()

        sounder_name = self.config['sounder_name']

        log.info('Converting data to formated strings for writing...')
        #Create a master index by time across all dataframes   
        if self.data is not None:
            log.debug('  making Sample datagrams...')
            #Time series w/ raw datagram strings
            data_df = pd.DataFrame(dict(raw_string=self.data.apply(lambda x: DGRAM_PARSE_KEY['RAW'].to_string(x.to_dict()), axis=1),
                                                ext='.raw'))
            data_df.reset_index(level='channel', drop=False, inplace=True)

        else:
            data_df = None
                                                

        if self.nmea is not None:
            log.debug('  making NMEA datagrams...')
            nmea_df = pd.DataFrame(dict(raw_string=self.nmea.apply(lambda x: DGRAM_PARSE_KEY['NME'].to_string(x.to_dict()), axis=1),
                                        ext=self.nmea['file'].apply(lambda x: os.path.splitext(x)[-1].lower()),
                                        channel=None))
        else:
            nmea_df = None
            
        if self.bottom is not None:
            log.debug('  making Bottom datagrams...')
            bottom_df = pd.DataFrame(dict(raw_string=self.bottom.apply(lambda x: DGRAM_PARSE_KEY[x['type'][:3]].to_string(x.to_dict()), axis=1),
                                          ext=self.bottom['file'].apply(lambda x: os.path.splitext(x)[-1].lower()),
                                          channel=None))
        else:
            bottom_df = None
            
        if self.tags is not None:
            log.debug('  making TAG datagrams...')
            tag_df = pd.DataFrame(dict(raw_string=self.tags.apply(lambda x: DGRAM_PARSE_KEY['TAG'].to_string(x.to_dict()), axis=1),
                                       ext=self.tags['file'].apply(lambda x: os.path.splitext(x)[-1].lower()),
                                       channel=None))
        else:
            tag_df = None
            
        
        datagram_df = pd.concat([x for x in [data_df, nmea_df, bottom_df, tag_df] if x is not None])
        log.info('Converted %d datagrams...', len(datagram_df))        
        
        log.info('Estimating # of files needed...')
        log.debug('   Caluclating datagram sizes')
        datagram_df['size'] = datagram_df['raw_string'].apply(lambda x: len(x))
        
        log.debug('   Reindexing...')
        datagram_df.reset_index(inplace=True, drop=False)
        datagram_df.sort_index(by=['reduced_timestamp', 'channel'], ascending=True, inplace=True)
        
                        
        total_datagram_sizes = datagram_df.groupby('ext')['size'].agg(['size', 'sum', 'count'])
        
        raw_datagram_index = datagram_df['ext'] == '.raw'
        bot_datagram_index = (datagram_df['ext'] == '.out') | (datagram_df['ext'] == '.bot')
        
        #Calculate ping time boundaries for files based on size
        if '.raw' not in total_datagram_sizes.index:
            ext = '.out'
        else:
            ext = '.raw'
        
        datagram_df['cumulative_size'] = datagram_df['size'].cumsum()
        datagram_df['file_number'] = None
        file_number = 1
        row_lb = 0

        file_dgram_index_bounds = []
        for row_index, row in datagram_df.iterrows():
            if row['ext'] == ext:
                if row['cumulative_size'] > (file_number * max_size * 1048576):
                    if row['channel'] is None:
                        file_number += 1
                        file_dgram_index_bounds.append((row_lb, row_index))
                        row_lb = row_index + 1

        if file_dgram_index_bounds[-1][-1] != row_index:
            file_dgram_index_bounds.append((row_lb, row_index))
      
        log.info("Splitting data into %d file pairs", len(file_dgram_index_bounds))
        #If everything fits into one pair of files
        saved_files = []
        for file_number, (row_lb, row_ub) in enumerate(file_dgram_index_bounds):

            starting_timestamp = datagram_df.reduced_timestamp.loc[row_lb]           
            ending_timestamp = datagram_df.reduced_timestamp.loc[row_ub]
            date_str     = starting_timestamp.strftime(date_fmt)

            raw_filename = os.path.join(path, prefix + date_str + suffix + '.raw')
            bot_filename = os.path.join(path, prefix + date_str + suffix + '.out')
            written_files = [None, None]

            con0_dict = self.config.copy()
            beam_config = con0_dict.pop('beam_config', '')

            con0_dict['low_date'], con0_dict['high_date'] = unix_to_nt(starting_timestamp)
            con0_dict['spare0'] = '\x00\x00\x00\x00'

            if sounder_name == 'MBES':
                con1_dict = {}
                con1_dict['low_date'] = con0_dict['low_date']
                con1_dict['high_date'] = con0_dict['high_date']
                con1_dict['type'] = 'CON1'
                con1_dict['beam_config'] = beam_config
            else:
                con1_dict = None

            if not os.path.exists(path):
                log.info('Creating directory:  %s', path)
                os.makedirs(path)


            if not overwrite and os.path.exists(raw_filename):
                raise IOError('File %s already exists.' %(raw_filename))

            if not overwrite and os.path.exists(bot_filename):
                raise IOError('File %s already exists.' %(bot_filename))

            num_raw_dgrams = len(datagram_df[raw_datagram_index].loc[row_lb:row_ub])
            if num_raw_dgrams > 0:
                log.info('Writing raw data to %s', raw_filename)
                with open(raw_filename, 'wb') as raw_fid:
                    raw_fid.write(DGRAM_PARSE_KEY['CON'].to_string(con0_dict))
                    if con1_dict is not None:
                        raw_fid.write(DGRAM_PARSE_KEY['CON'].to_string(con1_dict))               
                    datagram_df[raw_datagram_index].loc[row_lb:row_ub]['raw_string'].apply(lambda x: raw_fid.write(x))    
            
                written_files[0] = raw_filename

            num_bot_dgrams = len(datagram_df[bot_datagram_index].loc[row_lb:row_ub])
            if num_bot_dgrams > 0:
                log.info('Writing bottom data to %s', bot_filename)
                with open(bot_filename, 'wb') as bot_fid:
                    bot_fid.write(DGRAM_PARSE_KEY['CON'].to_string(con0_dict))
                    if con1_dict is not None:
                        bot_fid.write(DGRAM_PARSE_KEY['CON'].to_string(con1_dict))
                    datagram_df[bot_datagram_index].loc[row_lb:row_ub]['raw_string'].apply(lambda x: bot_fid.write(x))        

                written_files[1] = bot_filename

            saved_files.append(written_files)
        return saved_files
    def get_channel_number_from_id(self, channel_id):
        '''
        :param channel_id: Channel ID string
        :type channel_id: str
        
        Finds the channel number (1-indexed) for the provided channel ID string.
        
        Raises ValueError if no channels match the ID, or if multiple channels
        match.  Channel ID's should be unique, right?
        '''
        
        matching_channels = [num for (num, config) in list(self.config['transceivers'].items()) if config['channel_id'] == channel_id]
        if len(matching_channels) == 1:
            return matching_channels[0]
        elif len(matching_channels) > 1:
            raise ValueError('Multiple channels found using ID: %s'  %(channel_id))
        else:
            raise ValueError('No channels found using ID: %s'  %(channel_id))
        
    def update_from_array(self, data, update_raw=False):
        '''
        :param data: Data previously exported with .to_array()
        :type data: :class:`echolab.AxesArray.AxesArray`
        
        :param update_raw:  Propagate changes to raw sample values
        :type update_raw: bool
        
        
        Example data workflow, removing triangle-wave from es60 data:
        
        >>> data = echolab.io_.RawReader([file_0, file_1, ...])
        >>> data.Sv()      #Calculate Sv
        
        #For spice, operate on bottom-referenced data
        >>> Sv_bot = data.to_array(Sv, channel=1, reference='bottom')
        
        #Remove triangle wave corruption
        >>> fit_results = echolab.triwave.correct_triwave(Sv_bot)
        
        #Push data back into RawReader object
        >>> data.update_from_array(Sv_bot, update_raw=True)
        
        #Write data back to disk
        >>> data.save(suffix='tri_corrected')
        
        '''
        channel_id  = data.info['transceiver_info']['channel_id']
        channel_num = self.get_channel_number_from_id(channel_id)
        
        channel_data = self.get_channel(channel_id)
        
        array_sample_offset = data.axes[0][0]['sample']
        
        if data.ndim == 1:
            num_pings = 1
        else:
            num_pings = data.shape[1]
        
        for ping_indx in range(num_pings):
            ping_info = data.axes[1][ping_indx]
            ping_timestamp = ping_info['reduced_timestamp']
            ping_sample_offset = ping_info['shift'] - array_sample_offset
            
            sample_count = (~data.mask[ping_sample_offset:, ping_indx]).sum()
            if sample_count == 0:
                continue
            
            sample_offset = ping_info['offset']
            channel_data[data.info['data_type']][ping_timestamp][sample_offset:sample_offset + sample_count] = data._data[ping_sample_offset:ping_sample_offset + sample_count, ping_indx]


        if update_raw:
            self.update_raw_samples(from_type=data.info['data_type'],
                                    channels=channel_num)
            
            
        return
    
    
    def update_raw_samples(self, from_type, channels=None):
        '''
        :param from_type: What type of data to convert
        :type from_type: str
        
        :param channels: What channels to convert
        :type channels: str, int, list
        
        Converts derived quantities (such as Sv) back to raw indexed 
        samples (the .data['power'] and .data['angle'] columns) 
        for writing to file.
        
        Example data workflow, removing triangle-wave from es60 data:
        
        >>> data = echolab.io_.RawReader([file_0, file_1, ...])
        >>> data.Sv()      #Calculate Sv
        
        #For spice, operate on bottom-referenced data
        >>> Sv_bot = data.to_array(Sv, channel=1, reference='bottom')
        
        #Remove triangle wave corruption
        >>> fit_results = echolab.triwave.correct_triwave(Sv_bot)
        
        #Push data back into RawReader object, we'll do the raw update manually
        >>> data.update_from_array(Sv_bot, update_raw=False)
        
        #Sv values are updated, but not the underlying raw power samples
        >>> data.update_raw_samples('Sv', channels=1)
        
        #Now raw samples are updated as well and we're set to write a new file
        >>> data.save(suffix='tri_corrected')
        '''
        
        calibration = self.fill_default_transceiver_calibration(channels)
        
        if from_type in ['Sp', 'sp', 'Sv', 'sv']:
            if from_type in ['Sp', 'Sv']:
                linear = False
            else:
                linear = True
                
            raw_type = 'power'
            
        elif from_type in ['p_angles', 'e_angles', 'i_angles']:
            raw_type = 'angle'
            
        else:
            raise NameError('Unknown data type %s' % from_type)

        for channel, cal in list(calibration.items()):
            
            channel_data = self.get_channel(channel)

            eba             = cal['equivalent_beam_angle']
            tvg_correction  = cal['tvg_correction']                    
            gain            = cal['gain']
            alongship_offset = cal['angle_offset_alongship']
            alongship_sensitivity = cal['angle_sensitivity_alongship']
            
            athwartship_offset = cal['angle_offset_athwartship']
            athwartship_sensitivity = cal['angle_sensitivity_athwartship']
            
                    
            pulse_length_groups = channel_data.groupby('pulse_length')
            
            for pulse_length, group in pulse_length_groups:
                
                if 'sa_correction' not in cal:
                    uS_pulse_length = int(round(pulse_length,6) * 1e6)
                    sa_correction = cal['sa_correction_table'][uS_pulse_length]
                
                else:
                    sa_correction = cal['sa_correction']
                                   
                for row_index, row in group.iterrows():
                
                    #Skip pings with no power values    
                    if pd.np.all(pd.isnull(row[from_type])):
                        continue
                    
                    if from_type in ['Sv', 'sv']:  
                        #calculate raw power from Sv
                        result = unit_conversion.Sv_to_power(data=row, gain=gain, eba=eba,
                            sa_correction=sa_correction, calibration=cal,
                            tvg_correction=tvg_correction, linear=linear,
                            raw=True).astype('int16')
                    
                    elif from_type in ['Sp', 'sv']:
                        #calculate rawopower from Sp
                        result = unit_conversion.Sp_to_power(data=row, gain=gain,
                            tvg_correction=tvg_correction, calibration=calibration, 
                            linear=linear, raw=True).astype('int16')                           
                    
                    elif from_type == 'p_angles':
     
                        #Convert physical to indexed values           
                        alongship_indexed = unit_conversion.physical_to_indexed_angle(row['p_angles']['alongship'],
                            sensitivity=alongship_sensitivity, offset=alongship_offset).astype('uint8')
                        
                        athwartship_indexed = unit_conversion.physical_to_indexed_angle(row['p_angles']['athwartship'],
                            sensitivity=athwartship_sensitivity, offset=athwartship_offset).astype('uint8')                          
                        
                        result = pd.np.empty((len(row['angle']),), dtype='uint16')
                        
                        result[:] = (athwartship_indexed << 8) | alongship_indexed 
    
                    elif from_type == 'e_angles':
                        #Convert physical to indexed values           
                        alongship_indexed = unit_conversion.electrical_to_indexed_angle(row['e_angles']['alongship']).astype('uint8')                   
                        athwartship_indexed = unit_conversion.electrical_to_indexed_angle(row['e_angles']['athwartship']).astype('uint8')                          
                        
                        result = pd.np.empty((len(row['angle']),), dtype='uint16')
                        
                        result[:] = (athwartship_indexed << 8) | alongship_indexed 
                        
                    elif from_type == 'i_angles':
                        alongship_indexed = row['i_angles']['alongship'].astype('uint8')                   
                        athwartship_indexed = row['i_angles']['athwartship'].astype('uint8')                          
                        
                        result = pd.np.empty((len(row['angle']),), dtype='uint16')
                        result[:] = (athwartship_indexed << 8) | alongship_indexed
                        
                    else:
                        raise NameError('Unknown quantity %s' % from_type)
                 
                    #Insert into DataFrame
                    channel_data[raw_type][row_index][:] = result
    
    def correct_triangle_wave(self, channels=None, stomp_spikes=True,
                              upper_sample_bound=2, num_samples=2, 
                              min_r_squared=None, fit_guess=None,
                              fit_only=False):
        '''
        :param channels:  Channel names or index numbers to correct
        :type channels: list or None

        :param stomp_spikes:  Attempt to remove large jumps in raw power
            likely to be caused by processing errors.
        :type stomp_spikes: bool

        :param upper_sample_bound:  Sample number to take as upper bound of ringdown range
        :type upper_sample_bound: int

        :param num_samples:  Number of samples to include in ringdown
        :type num_samples:  int

        :param min_r_squared:  Minimum allowed value for R²
        :type min_r_squared:  float

        :param fit_guess:  Initial guess for triangle-wave fitting
        :type fit_guess: dict

        :param fit_only:  Only estimate triangle wave parameters.  Do not correct data.
        :type fit_only: bool

        :returns: dict
        '''           
        
        
        if channels is None:
            channels_ = list(self.config['transceivers'].keys())
    
        else:
            channels_ = []
            for channel in channels:
                if isinstance(channel, str):
                    channel = self.get_channel_number_from_id(channel)
           
                elif isinstance(channel, (int, float)):
                    if channel not in self.config['transceivers']:
                        raise ValueError('Channel #%d not in dataset' %(channel))
                else:
                    raise ValueError('Expected string or number for channel')
                
                channels_.append(channel)

        if fit_guess is None:
            fit_guess_ = {}
    
        else:
            fit_guess_ ={}
            for channel, guess in list(fit_guess.items()):
                if isinstance(channel, str):
                    channel = self.get_channel_number_from_id(channel)
           
                elif isinstance(channel, (int, float)):
                    if channel not in self.config['transceivers']:
                        raise ValueError('Channel #%d not in dataset' %(channel))
                else:
                    raise ValueError('Expected string or number for channel')
                
                fit_guess_[channel] = guess                
        
        fit_results = {}

        for channel in channels_:
            channel_id = self.config['transceivers'][channel]['channel_id']

            try:
                ping_counts = self.data.xs(channel, level='channel')['count']
            except KeyError:
                log.warning('No pings available for channel %d:%s', channel, channel_id)
                continue

            num_pings = len(ping_counts)
            max_sample = ping_counts.max()
            data_size = num_pings * max_sample
            
            if data_size == 0:
                log.warning('Channel %d:%s contains no data!', channel, channel_id)
                continue
            
            ringdown = self.to_array('power', channel=channel, drop_zero_range=False, max_depth=10)
            
            fit_results[channel] = triwave.correct_triwave(ringdown, stomp_spikes=stomp_spikes,
                        ringdown_upper_bound=upper_sample_bound, num_samples=num_samples,
                        fit_guess=fit_guess_.get(channel, None),
                        fit_only=True)
            
            del ringdown

            if (min_r_squared is not None) and \
                fit_results[channel]['r_squared'] < min_r_squared:
                log.warning('    Fit for channel #%d below minimum R^2:  %.4f', fit_results[channel]['r_squared'])
                continue
            
            
            log.info('    Fit for channel #%d:  a=%.3f, C=%.3f, k=%.3f, R^2=%.3f', channel,
                        fit_results[channel]['amplitude'], fit_results[channel]['amplitude_offset'],
                        fit_results[channel]['period_offset'], fit_results[channel]['r_squared'])
            
            if not fit_only:
                generated_triangle_offset = triwave.general_triangle(pd.np.arange(num_pings),
                        A=fit_results[channel]['amplitude'], M=2721.0, 
                        k = fit_results[channel]['period_offset'], C=0,
                        dtype='float32')
                
                
                blocksize = int(5e6 / max_sample)
                log.debug('  Using blocksize of %d to adjust power', blocksize)
                channel_timestamps = self.data.xs(channel, level='channel')['reduced_timestamp']
                

                for indx in range(0, num_pings, blocksize):
                    first_timestamp = channel_timestamps.iloc[indx]
                    
                    if indx+blocksize >= num_pings:
                        last_timestamp  = channel_timestamps.iloc[-1]
                    else:
                        last_timestamp = channel_timestamps.iloc[indx+blocksize-1]
                
                    power = self.to_array('power', channel=channel, drop_zero_range=False,
                                          first_ping_time=first_timestamp, last_ping_time=last_timestamp)

                    power[:] = power - pd.np.repeat(pd.np.reshape(generated_triangle_offset[indx:indx+blocksize], (1, -1)), power.shape[0], axis=0)
                
                    self.update_from_array(power, update_raw=False)
                
        return fit_results
    
    def remove_empty_pings(self, channels=None):
        '''

        Removes individual pings with 0 samples.
        '''
        if self.data is None:
            raise ValueError('No sample data available')

        pings_per_channel = self.data.groupby('channel').size()
        if channels is not None:
            if isinstance(channels, tuple):
                channels = list(channels)

            if isinstance(channels, list):
                for indx, channel in enumerate(channels):
                    if isinstance(channel, str):
                        channels[indx] = self.get_channel_number_from_id(channel)
                    else:
                        channels[indx] = int(channel)

            if isinstance(channels, str):
                channels = [self.get_channel_number_from_id(channel)]

            else:
                channels = [int(channels)]

        else:
            channels = list(self.config['transceivers'].keys())

        zero_length_pings = self.data['count'] == 0

        if zero_length_pings.sum() == 0:
            log.debug('No empty pings found.')
            return {}

        pings_removed = {}
        for channel_num in self.data.channel.unique():
            if channel_num in channels:
                channel_zero_length_pings = (self.data.channel == channel_num) & zero_length_pings
                num_zero_length_pings = channel_zero_length_pings.sum()
                if num_zero_length_pings > 0:
                    if num_zero_length_pings == pings_per_channel[channel_num]:
                        self.remove_channel(channel=channel_num, renumber_channels=False)
                        pings_removed[channel_num] = num_zero_length_pings
                    else:
                        log.debug('Channel %d contains %d zero-length pings...', channel_num, channel_zero_length_pings.sum())
                        pings_removed[channel_num] = num_zero_length_pings
                        self.data = self.data.loc[~channel_zero_length_pings]
                        zero_length_pings = self.data['count'] == 0

                    zero_length_pings = self.data['count'] == 0

        return pings_removed

    def remove_empty_channels(self, renumber_channels=False):
        '''
        :returns: list
        
        Removes channels with ping information but no sample data from dataset.
        
        Returns a list of transceiver channel_id strings for channels removed
        or None if no channels were removed
        '''
        
        if self.data is None:
            return
        
        channels_removed = []
        for channel_id in [x['channel_id'] for x in list(self.config['transceivers'].values())]:
            
            channel_num = self.get_channel_number_from_id(channel_id)
            ping_counts = self.data.xs(channel_num, level='channel')['count']
            num_pings = len(ping_counts)
            max_samples = ping_counts.max()
            
            if num_pings * max_samples == 0:
                log.info('Channel %d:%s is empty, removing from dataset', channel_num, channel_id)
                self.remove_channel(channel_num, renumber_channels=renumber_channels)
                channels_removed.append(channel_id)
                
        if len(channels_removed) == 0:
            return None
        else:
            return channels_removed

    def remove_channel(self, channel, renumber_channels=False):
        '''
        :param channel: channel to remove
        :type channel: int or str
        
        Removes all data associated with the channel.  Channel may be
        either a int channel index or a string channel_id
        
        Channel indicies are remapped post-removal.  For example,
        if the original dataset contains channels 1 and 2, and you remove
        channel 1, the new object will map channel 2 -> 1:
        
            original:  channel 1: 38khz, channel 2: 120khz
                    remove channel 1
            new:       channel 1: 120khz
        '''
        if isinstance(channel, str):
            channel = self.get_channel_number_from_id(channel)
            
        channel = int(channel)
        if channel not in self.config['transceivers']:
            raise ValueError('Channel number %d not in transceiver list' %(channel))

        #Convoluted list comprehension maps channels w/ the following logic
        #if the old channel != channel to remove:
        #    if the old channel < the channel to be removed:
        #       new channel = old channel, return tuple (x, x)
        #    if the old channel > the channel to be removed:
        #       new channel = old channel - 1, return (x, x-1)
         
        new_channel_map = [(x, x) if x < channel else (x, x-1) for x in list(self.config['transceivers'].keys()) if x != channel] 
        new_channel_map = dict(new_channel_map)
        
        log.debug('New channel map:  %s', new_channel_map)
        
        #Remove channel from config & cal
        if renumber_channels:
            del self.config['transceivers'][channel]
            try:
                del self.calibration_params[channel]
            except KeyError:
                pass
                      
        new_bottom_indxs = []
        for old_channel in sorted(new_channel_map.keys()):
            new_bottom_indxs.append(old_channel-1)
            new_channel = new_channel_map[old_channel]
            
            #If no channel remapping necessary, go on to the next pair
            if not renumber_channels or (old_channel == new_channel):
                continue
            
            #Otherwise, shift config & cal
            self.config['transceivers'][new_channel] = self.config['transceivers'].pop(old_channel)
            try:
                self.calibration_params[new_channel] = self.calibration_params.pop(old_channel)
            except KeyError:
                pass
            
        #Remove data rows
        if self.data is not None:
            log.debug('Removing channel %d from data', channel)
            self.data = self.data.loc[self.data.channel != channel]
            
            #Remap channels in data
            if not renumber_channels:
                for old_channel, new_channel in list(new_channel_map.items()):
                    if old_channel != new_channel:
                        log.debug('Remapping channel #%d -> #%d', old_channel, new_channel)
                        self.data.channel.loc[self.data.channel == old_channel] = new_channel
  
                self.data.reset_index(drop=True, inplace=True)
                self.data.set_index(['channel', 'reduced_timestamp'], inplace=True, drop=False)
                self.data.sort_index(axis=0, by=['channel', 'reduced_timestamp'], inplace=True)

        #remap bottom depths & reflectivity
        if (self.bottom is not None) and renumber_channels:
            log.debug('Remapping bottom data to indicies %s', new_bottom_indxs)
            self.bottom.depth = self.bottom.depth.apply(lambda x: x[new_bottom_indxs])
            self.bottom.reflectivity = self.bottom.reflectivity.apply(lambda x: x[new_bottom_indxs])
            self.bottom.transceiver_count = len(new_bottom_indxs)
                          
    def to_array(self, data_type, channel, first_ping_time=None, last_ping_time=None,
                 min_depth=None, max_depth=None, reference=None, 
                 reference_unit=None, drop_zero_range=True,
                 dtype=None):
        '''
        :param data_type:  Data to return.
        :type data_type: str
        
        :param first_ping_time:  Ignore all data before this time.
        :type first_ping_time: str or datetime.datetime
        
        :param last_ping_time: Ignore all data after this time.
        :type last_ping_time:  str or datetime.datetime
        
        :param min_depth:  Minimum depth for data
        :type min_depth: float
        
        :param max_depth: Maximum depth for data
        :type max_depth: float
        
        :param reference:  Reference to align data against
        :type reference: str or array
        
        :param reference_unit:  Units for provided reference
        :type reference_unit: str
        
        :param drop_zero_range: Drops the 0th sample of each ping
        :type drop_zero_range: bool
        
        
        data_type:  A string matching one of the following
        
            'power'         Raw indexed power as recorded           
            'Sv'            Log-domain 
            'sv'            Linear-domain
            'Sp'            Log-domain 
            'sp'            Linear-domain
            
            'i_angle'       Raw indexed angle as recorded
            'e_angle'       Electric angle
            'p_angle'       Physical angle
            
        reference_unit: one of {'sample', 'range', 'depth'}
        
        drop_zero_range:
            Echoview silently drops the 0th range sample when displaying and
            analysing echograms ('sample 0' as counted in Echoview is actually
            the second sample, sample 1, in the ping data).  By default, 
            Echolab attempts to replicate this behavior, but you can disable it
            by passing drop_zero_range=False.
            
            
        Returns a :class:`echolab.AxesArray.AxesArray` object with some
        pertanent meta-information:
        
        :param reference:  May be a :class:`pandas.Series` object, an array,
            a constant scalar, or one of the predefined string values:
            
            -  'face'    No data alignment performed (or, aligned to transducer face)
            -  'bottom'  Data is aligned to bottom values
            -  'surface' Data is aligned to surface (includes transducer draft)
               
        keys in the .info dictonary:
            data_type:            type of data, 'sv', 'Sv', etc.
            meters_per_sample:    sample thickness
            sample_interval:      sample interval in seconds
            sound_velocity:       sound velocity in m/s
            transceiver_info:     copy of the transceiver config
            
        the .axes list will be populted by two vectors:
            .axes[0] will contain a record array w/ fields relating to samples
                range:         range from reference in meters
                sample:        sample number from reference
                
            .axes[1] will also be a record array w/ fields relating to pings:
                reduced_timestamp:     timestamp of each ping
                reference:             range reference used to create array
                ping:                  ping number
                offset:                sample offset from original data offset
                                       in ping
                count:                 number of samples after 'offset' contain
                                       data
                shift:                 location of first sample in 
                                       .axes[0]['sample'] units
                transducer_depth:      depth of transducer face in meters
                surface:               range of surface from reference.  Can
                                       be negative if reference = 'surface' 
                                       (which is really the first sample)
                                       and the transducer_depth =/= 0
                
            .axes[1] may also have the optional fields if the corresponding
            quantitites have been interpolated previously:
                lat:                   ping latitude
                lon:                   ping longitude
                distance:              vessel distance in nmi
                bottom:                range of bottom return
        
        TO GET THE LOCATION OF THE FIRST VALID SAMPLE FOR EACH PING:
            calculate the first sample offset:
                .axes[1]['shift'] - .axes[0][0]['sample']
        '''
        #TODO:  Assert data product is available
        
        if isinstance(channel, str):
            channel = self.get_channel_number_from_id(channel)
                        
        elif isinstance(channel, (int, float)):
            if channel not in self.config['transceivers']:
                raise ValueError('Channel #%d not in dataset' %(channel))
        else:
            raise ValueError('Expected string or number for channel')


        info_columns = ['offset', 'count', 'sound_velocity', 'sample_interval',
                        'transducer_depth', 'file_ping']
        
        for field in ['lat', 'lon', 'distance', 'bottom']:
            if field in self.data.columns:
                log.debug('  Found %s ping data...', field)
                info_columns.append(field)
                
        ping_info = self.get_channel(channel)[info_columns]
        
        #Override transducer depth if set in calibration_params
        try:
            ping_info.transducer_depth = self.calibration_params[channel]['transducer_depth']
            log.debug('  Using transducer depth set in calibration')
        except KeyError:
            pass

        #Override sound speed if set in calibration_params
        try:
            ping_info.sound_velocity = self.calibration_params[channel]['sound_velocity']
            log.debug('  Using sound velocity set in calibration')
        except KeyError:
            pass

        #Assert sample rate is constant
        if ping_info['sample_interval'].nunique() > 1:
            raise ValueError('Multiple values for sample_interval present in data.')
        else:
            sample_interval = ping_info.iloc[0]['sample_interval']
        
        if ping_info['sound_velocity'].nunique() > 1:
            raise ValueError('Multiple values for sound_velocity present in data.')
        else:
            sound_velocity = ping_info.iloc[0]['sound_velocity']
        
        meters_per_sample = sound_velocity / 2.0 * sample_interval
                 
        #Plan:
        #    Figure rectangluar dimensions
        #         number of pings   = number of pings between last and first ping times
        #         number of samples = max(max depth in data, max_depth) - min(min_depth_in_data, 0)
        #                                 converted to samples
        #
        #    Create empty ndarray of final dimensions
        #    Calculate optimal sample # to aling pings to based on reference
        #    For each ping in data
        #        insert into corresponding ndarray column at the correct span
        #        of rows
        
        #    Create x and y unit vectors
        #         

        #Truncate in time        
        if first_ping_time is not None:
            first_ping_time = pd.to_datetime(first_ping_time, errors='raise', utc=True)

        if last_ping_time is not None:
            last_ping_time = pd.to_datetime(last_ping_time, errors='raise', utc=True)
        
        if first_ping_time is not None and last_ping_time is not None:
            ping_info = ping_info.loc[(ping_info.index >= first_ping_time) & (ping_info.index <= last_ping_time)]
            
        elif first_ping_time is not None:
            ping_info = ping_info.loc[ping_info.index >= first_ping_time]
       
        elif last_ping_time is not None:
            ping_info = ping_info.loc[ping_info.index <= last_ping_time]
           
            
        #Check passed reference
        #No reference given -> default to 'face'
        if reference is None:
            reference = 'face'
            
        if isinstance(reference, str):
            if reference.lower() == 'bottom':
                if 'bottom' not in self.data.columns:
                    self.interpolate_ping_bottom_range()
                reference = self.get_channel(channel)['bottom']
                ping_info['bottom'] = reference
                reference_unit = 'range'
            
            elif reference.lower() == 'face':
                reference = pd.Series(0, index=ping_info.index)
                reference_unit = 'sample'

            elif reference.lower() == 'surface':
                reference = -ping_info.transducer_depth
                reference_unit = 'range'
                
            else:
                raise ValueError('Reference: %s is not a valid reference.' %(reference))
            
        elif pd.np.isscalar(reference):
            reference = pd.Series(reference, index=ping_info.index)
            
        elif isinstance(reference, pd.Series):
            #If not all reference index values are contained in the data
            if not ping_info.index.intersection(reference.index).equals(ping_info.index):
                raise ValueError('reference/data index mismatch')
        
        elif len(reference) == ping_info.shape[0]:
            reference = pd.Series(reference, index=ping_info.index)
            
        else:
            raise ValueError('Unable to create reference series')
            
        #Check passed reference unit
        if reference_unit is None:
            reference_unit = 'sample'
        
        elif isinstance(reference_unit, str):
            reference_unit = reference_unit.lower()
            if reference_unit.lower() not in ['range', 'depth', 'sample']:
                raise ValueError("reference_unit must be one of {'range' | 'depth' | 'sample'}")

       
        
        #At this point we have:
        #    a refernce as a pd.Series 
        #    a reference unit as a string.  
        
        
        #drop_shift is a boolean-like flag indicating which pings should be
        #shifted by one to drop the 0th sample.  If  drop_zero_range is True,
        #all pings with offset=0 will be treated as if offset=1

        if drop_zero_range:
            ping_info['drop_shift'] = ping_info['offset'].apply(lambda x: 1 if x == 0 else 0)
        else:
            ping_info['drop_shift'] = 0               
        
        #Calculate the sample # where this vector intersects each ping.        
        if reference_unit == 'sample':
            reference = reference - (ping_info['offset'] + ping_info['drop_shift'])
        
        elif reference_unit == 'range':
            reference = reference / meters_per_sample - (ping_info['offset'] + ping_info['drop_shift'])

        elif reference_unit == 'depth':
            reference = (reference - ping_info['transducer_depth']) / meters_per_sample - (ping_info['offset'] + ping_info['drop_shift'])
              
        else:
            raise RuntimeError('Illegal reference unit %s, should have been caught earlier' % (reference_unit))
        
        
        #Convert to ints
        reference = reference.apply(lambda x: int(x))
       
        #Now we have a reference line as a pd.Series of sample # values
 
        #The shift series:  Sample shift away from reference mean for each ping.
        #We will be shifting each ping by this amount for alignment
        #ie.:  mean reference = 50, reference for this ping = 45
        #      offset = 50-45 = 5
        #      shift ping by 5, brings #45 -> #50
        
        reference_mean  = int(reference.mean())
        shift_series = reference.apply(lambda x: reference_mean - x).apply(lambda x: int(x))

        #Calculate pre_shift.  Excessive shifts may bring samples above the 'surface' represented by sample #0.
        min_shift    = shift_series.min()

        if min_shift < 0:
            pre_shift = -min_shift
        else:
            pre_shift    = 0

        surface_sample_offset = -ping_info.transducer_depth / meters_per_sample - (ping_info['offset'] + ping_info['drop_shift']) - reference
    
        #Get bottom offsets    
        if 'bottom' in ping_info.columns:
            bottom_sample_offset = ping_info['bottom'] / meters_per_sample - (ping_info['offset'] + ping_info['drop_shift']) - reference
            bottom_sample_offset = bottom_sample_offset.astype('int32')
        
        
        #Update the reference
        reference = reference + shift_series - reference_mean            
        
        #Calculate final array dimensions
        min_data_depths = (pre_shift + shift_series + ping_info['offset'] + ping_info['drop_shift']) * meters_per_sample + ping_info['transducer_depth']
        max_data_depths = min_data_depths + (ping_info['count'] - ping_info['drop_shift']) * meters_per_sample 
        
        min_data_depth = min_data_depths.min()
        max_data_depth = max_data_depths.max()
        
        if min_depth is not None and min_data_depth < min_depth:
            min_data_depth = min_depth
            
        if max_depth is not None and max_data_depth > max_depth:
            max_data_depth = max_depth
       
        #These are the final dimensions
        num_samples = int(pd.np.ceil( (max_data_depth - min_data_depth) / meters_per_sample ))
        num_pings   = ping_info.shape[0]
        
        
        #Setting up axis vectors...
        y_axes_dtype_fields = [('sample', pd.np.int), ('range', pd.np.float)]
        
        y_axes = pd.np.empty((num_samples,), dtype=y_axes_dtype_fields)
        y_axes['sample'][:] = pd.np.arange(num_samples) - pre_shift - reference_mean
        y_axes['range'][:]  = y_axes['sample'] * meters_per_sample
        
             
        x_axes_dtype_fields = [('reduced_timestamp', pd.np.object_), ('reference', pd.np.float), 
                        ('ping', pd.np.int), ('offset', pd.np.int), ('count', pd.np.int),
                        ('shift', pd.np.int), ('transducer_depth', pd.np.float),
                        ('surface', pd.np.float)]
        
        if 'lat' in ping_info.columns:
            x_axes_dtype_fields.append(('lat', pd.np.float))

            
        if 'lon' in ping_info.columns:
            x_axes_dtype_fields.append(('lon', pd.np.float))

            
        if 'distance' in ping_info.columns:
            x_axes_dtype_fields.append(('distance', pd.np.float))

        
        if 'bottom' in ping_info.columns:
            x_axes_dtype_fields.append(('bottom', pd.np.float))

            

        x_axes       = pd.np.zeros((num_pings,), dtype=pd.np.dtype(x_axes_dtype_fields))

        x_axes['reduced_timestamp'] = ping_info.index.to_pydatetime()
        x_axes['ping'][:]      = pd.np.arange(num_pings) 
        x_axes['reference'][:] = (reference * meters_per_sample).values
        x_axes['surface'][:] = (surface_sample_offset * meters_per_sample).values
        x_axes['transducer_depth'][:] = ping_info.transducer_depth.values
        
        
        if 'lat' in ping_info.columns:
            x_axes['lat'] = ping_info['lat'].values
            
        if 'lon' in self.data.columns:
            x_axes['lon'] = ping_info['lon'].values
            
        if 'distance' in self.data.columns:
            x_axes['distance'] = ping_info['distance'].values

        if 'bottom' in self.data.columns:
            x_axes['bottom'][:] = (bottom_sample_offset * meters_per_sample).values

        #Create rectangular array
        #Grab the datatype -- needed for record arrays produced for angle units
        #which contain both 'alongship' and 'athwartship'
        data_df = self.get_channel(channel)[data_type]
        
        if dtype is None:
            data_dtype = data_df[0].dtype
        else:
            data_dtype = dtype
        
        data_array = AxesArray(pd.np.empty((num_samples, num_pings), dtype=data_dtype),
                               axes=[y_axes, x_axes])
        
        #Set the whole array as masked initially, we'll be overwriting
        #with samples later
        data_array[:, :] = pd.np.ma.masked
        
        ping_num = 0
        for ping_tstamp, ping in ping_info.iterrows():
            
            #Find upper/lower array/data bounds
            shift = shift_series.loc[ping_tstamp]
            transducer_depth = ping['transducer_depth']
            drop_shift = int(ping['drop_shift'])
            
            #Adjust offset & count by 1 if we've dropped the first sample
            offset = int(ping['offset']) + drop_shift
            count = int(ping['count']) - drop_shift
            
            ping_start_depth = (pre_shift + shift + offset) * meters_per_sample + transducer_depth
            ping_stop_depth  = ping_start_depth + count * meters_per_sample

            
            if ping_start_depth < min_data_depth:
                data_lb = int((min_data_depth - ping_start_depth) / meters_per_sample)
                offset += data_lb
                count -= data_lb
                array_lb = 0
            else:
                data_lb = 0 + drop_shift
                #need to account for the possible extra shift due to 'drop_shift'
                #here
                array_lb = (pre_shift + shift + offset - drop_shift)            


            array_ub = array_lb + count
            
            if array_ub > num_samples:
                array_ub = num_samples
                data_ub  = data_lb + (array_ub - array_lb)
                count = array_ub - array_lb
            else:
                data_ub  = None
            
            data_array.axes[1][ping_num]['offset'] = data_lb
            data_array.axes[1][ping_num]['shift']  = data_array.axes[0]['sample'][array_lb]
#            data_array.axes[1][ping_num]['shift']  = array_lb
            data_array.axes[1][ping_num]['count']  = count

            #Should really only get count == 0 as a minimum, but this catches
            #all cases.  Either way, the ping is empty or invalid.. should
            #we throw an error for count < 0?  It's a bug in logic.
            if count < 1:
                ping_num += 1
                continue
            
            #Insert values            
            data_array[array_lb:array_ub, ping_num] = data_df.loc[ping_tstamp][data_lb:data_ub]
            ping_num += 1
        
        
        #Add transceiver info         
        if data_array.info is None:
            data_array.info = dict(data_type=data_type)
        else:
            data_array.info.update({'data_type':data_type})

        transceiver = self.config['transceivers'][channel].copy()

        #Remove some fields we don't care about
        for key in ['dir_x', 'dir_y', 'dir_z', 'pos_x', 
                    'pos_y', 'pos_z', 'pulse_length_table',
                    'sa_correction_table', 'sa_correction_table',
                    'spare1', 'spare2', 'spare3', 'spare4',
                    'gain_table']:
            _ = transceiver.pop(key, None)

        #Insert calibration info 
        calibration = self.calibration_params.get(channel, {})
        transceiver.update(calibration)
        
        data_array.info.update(dict(meters_per_sample=meters_per_sample,
                                    sound_velocity=sound_velocity,
                                    sample_interval=sample_interval,
                                    transceiver_info=transceiver))
        return data_array
    
    
    def fill_default_transceiver_calibration(self, channels=None, **kwargs):
        '''
        :param channels:  Desired channels to perform calcs on
        :type channels: int, str or list
        

        The following parameters are not available per-ping, but are
        at a transceiver-level:
            sa_correction
            equivalent_beam_angle
            gain
            tvg_correction (not a transceiver quantity, but used in some calcs)
        
        
        This function sets these parameters if they are not provided
        for the user-specified `calibration` dictionary
        
        sa_correction:
            A dictionary is added under the key: `sa_correction_table`
            with values from the transceiver's sa_correction_table vector
            keyed to the transceiver's pulse_length_table scaled to 
            microseconds.
            
            For calculations, each ping's pulse_length is used to get back
            the correct value of sa_correction
            
        equivalent_beam_angle:
            The transceiver's equivalent_beam_angle entry
            
        gain:
            The transceiver's gain entry
            
        tvg_correction:
            Defaults to 2
            
            
        Returns a new dictionary of calibration values.  Default values
        are inserted for any value missing in self.calibration_params
        for the desired channel.  
        
        The new dictionary will be keyed by channel index number.
        '''
        if channels is None:
            channels = list(self.config['transceivers'].keys())
        
        elif isinstance(channels, str):
            channels = [channels]
        
        elif isinstance(channels, (int, float)):
            channels = [channels]
            
        elif not isinstance(channels, list):
            raise TypeError('Expected string or int or list of channels')
        
        for indx in range(len(channels)):
            if isinstance(channels[indx], str):
                channel = self.get_channel_number_from_id(channels[indx])
                log.debug('Matched channel ID: %s to channel number %d', channels[indx],
                            channel)
                channels[indx] = channel
                
            elif isinstance(channels[indx], (float, int)):
                if int(channels[indx]) not in self.config['transceivers']:
                    raise ValueError('Channel %d not in transceiver config.' %(channels[indx]))
                else:
                    channels[indx] = int(channels[indx])
                    
            else:
                raise TypeError('Expected string or int')
        
        #If we've provided no calibration overrides...
#        if calibration is None:
#
#            calibration = {}
#            #For each channel, fill in defaults.           
#            for channel in channels:
#                transceiver = self.config['transceivers'][channel]
#               
#                uS_pulse_lengths = map(lambda x: int(x * 1e6), transceiver['pulse_length_table'])
#                
#                calibration[channel] = {}
#                calibration[channel]['eba'] = transceiver['equivalent_beam_angle']
#                calibration[channel]['sa_correction_table'] = \
#                    dict(zip(uS_pulse_lengths, transceiver['sa_correction_table']))         
#        
#                calibration[channel]['tvg_correction'] = 2
#
#                #The following have 1-to-1 mappings:
#                for key in ['gain', 'angle_offset_alongship', 'angle_offset_athwartship',
#                            'angle_sensitivity_alongship', 'angle_sensitivity_athwartship']:
#                    calibration[channel][key] = transceiver[key]
#                
#        elif isinstance(calibration, dict):
#            calibration = calibration.copy()
#            
#            for channel in calibration.keys():
#                if isinstance(channel, str):
#                    channel_num = self.get_channel_number_from_id(channel)
#                    calibration[channel_num] = calibration[channel]
#                    del calibration[channel]
#      
#        else:
#            raise TypeError("Expected dict or None for calibration")
        
        #Now, create a calibration dictionary for each desired channel
        #in following order preference:
        # 
        #  1) calibration values stored in self.calibration_params
        #  2) Default transceiver params
        calibration = {}
        for channel in channels:
            cal = calibration.setdefault(channel, {})
            set_cal = self.calibration_params.get(channel, {})
            
            cal.update(set_cal)
            
            transceiver = self.config['transceivers'][channel]
               
            if 'tvg_correction' not in cal:
                cal['tvg_correction'] = kwargs.get('tvg_correction', 2.0)
                
            if 'equivalent_beam_angle' not in cal:
                cal['equivalent_beam_angle'] = transceiver['equivalent_beam_angle']
            
            if 'sa_correction' not in cal:
                uS_pulse_lengths = [int(x * 1e6) for x in transceiver['pulse_length_table']]
                
                cal['sa_correction_table'] = \
                    dict(list(zip(uS_pulse_lengths, transceiver['sa_correction_table'])))
                    
            #The following have 1-to-1 mappings:
            for key in ['gain', 'angle_offset_alongship', 'angle_offset_athwartship',
                        'angle_sensitivity_alongship', 'angle_sensitivity_athwartship']:
                _ = calibration[channel].setdefault(key, transceiver[key])

        return calibration
            
        
    def Sv(self, channels=None, linear=False):
        '''
        :param channels:  Desired channels to perform calcs on
        :type channels:  int, str, list or None
        
        :param linear:  Calculate linear sv
        :type linear:  bool
        
        :param calibration:  User-set calibration values
        :type calibration: dict
        
        Calculates Sv or sv and appends it to the `data` DataFrame
        
        `calibration`:
            dictonary of user-defined calibration parameters.  If no calibration
            for a channel is defined, the defaults from the transceiver and
            individual pings are used
            
            keys for Sv calibration:
            
                sa_correction
                equivalent_beam_angle 
                gain
                tvg_correction (defaults to 2)
                absorption_coefficient
                sound_velocity
                frequency
                transmit_power
                pulse_length

            The following keys should be left unset unless you really know
            what you're doing:
                offset
                count
                sample_interval
        
        '''
        #Fill default values for transceivers if needed & convert
        #any string channel ID's to channel indexes
        calibration = self.fill_default_transceiver_calibration(channels, tvg_correction=2)                    
                        
        if linear:
            data_key = 'sv'
        else:
            data_key = 'Sv'

        if 'power' not in self.data:
            raise ValueError('Cannot calculate Sv:  Missing raw power data')
        #Remove existing column into the DataFrame if required
        if data_key in self.data:
            del self.data[data_key]
        
        #Group by channel and pulse length
        grouped = self.data.groupby(['channel', 'pulse_length'])

        result = {}              
        for (channel, pulse_length), group in grouped:
            
            #print("2951 group", group)
            #print("2949 channel", channel)
            #print("2950 pulse_length", pulse_length)
            #Skip channels not listed in calibration dictionary
            if channel not in calibration:               
                continue
            
            cal = calibration[channel]

            if 'sa_correction' not in cal:
                uS_pulse_length = int(round(pulse_length,6) * 1e6)
                sa_correction = cal['sa_correction_table'][uS_pulse_length]
                cal['sa_correction'] = sa_correction

            else:
                sa_correction = cal['sa_correction']
            
            eba             = cal['equivalent_beam_angle']
            tvg_correction  = cal['tvg_correction']                    
            gain            = cal['gain']
            

            for row_index, row in group.iterrows():
            
                #Skip pings with no power values
                #    This is now handled in unit_conversion
                #    Empty arrays produce empty arrays    
#                if pd.np.all(pd.isnull(row['power'])):
#                    continue
            
                #calculate Sv
                result[row_index] = [unit_conversion.power_to_Sv(data=row, gain=gain, eba=eba,
                    sa_correction=sa_correction, calibration=cal,
                    tvg_correction=tvg_correction, linear=linear,
                    raw=True)]


        new_df = pd.DataFrame.from_dict(result, orient='index')
        new_df.columns = [data_key]
        #print("raw_reader self.data.__dict__", self.data.__dict__)
        #print("type(raw_reader self.data.__dict__)", type(self.data.__dict__))
        print("raw_reader new_df.__dict__", new_df.__dict__)
        return self.data

        self.data = self.data.join(new_df, on=None, how='left')
        
          
    def Sp(self, channels=None, linear=False):
        '''
        :param channels:  Desired channels to perform calcs on
        :type channels:  int, str, list or None
        
        :param linear:  Calculate linear sv
        :type linear:  bool
        
        :param calibration:  User-set calibration values
        :type calibration: dict
        
        Calculates Sp or sp and appends it to the `data` DataFrame
        
        `calibration`:
            dictonary of user-defined calibration parameters.  If no calibration
            for a channel is defined, the defaults from the transceiver and
            individual pings are used
            
            keys for Sp calibration:
            
                sa_correction
                gain
                tvg_correction (defaults to 0)
                absorption_coefficient
                sound_velocity
                frequency
                transmit_power
                pulse_length

            The following keys should be left unset unless you really know
            what you're doing:
                offset
                count
                sample_interval
        
        '''
        #Fill default values for transceivers if needed & convert
        #any string channel ID's to channel indexes
        calibration = self.fill_default_transceiver_calibration(channels, tvg_correction=0)                    

        if 'power' not in self.data:
            raise ValueError('Cannot calculate Sp:  Missing raw power data')
                        
        if linear:
            data_key = 'sp'
        else:
            data_key = 'Sp'

        #Remove existing column into the DataFrame if required
        if data_key in self.data:
            del self.data[data_key]
        
        #Group by channel and pulse length
        grouped = self.data.groupby(['channel'])
        
        result = {}              
        for channel, group in grouped:
            
            #Skip channels not listed in calibration dictionary
            if channel not in calibration:               
                continue
            
            cal = calibration[channel]
            gain            = cal['gain']
            tvg_correction  = cal['tvg_correction']                    

            for row_index, row in group.iterrows():
            
                #Skip pings with no power values
                #    This is now handled in unit_conversion
                #    Empty arrays produce empty arrays    
#                if pd.np.all(pd.isnull(row['power'])):
#                    continue
            
                #calculate Sp
                result[row_index] = [unit_conversion.power_to_Sp(data=row, gain=gain,
                    tvg_correction=tvg_correction, calibration=calibration, 
                    linear=linear, raw=True)]
                
        new_df = pd.DataFrame.from_dict(result, orient='index')
        new_df.columns = [data_key]
        self.data = self.data.join(new_df, on=None, how='left')
                    
    
    def physical_angles(self, channels=None):
        '''
        :param channels:  Desired channels to perform calcs on
        :type channels:  int, str, list or None
               
        :param calibration:  User-set calibration values
        :type calibration: dict
        
        Calculates the physical alongship and athwartship angles
        and appends it to the `data` DataFrame w/ key 'p_angles'
        
        `calibration`:
            dictonary of user-defined calibration parameters.  If no calibration
            for a channel is defined, the defaults from the transceiver and
            individual pings are used
            
            keys for physical angle calibration:
            
                angle_offset_alongship
                angle_offset_athwartship
                angle_sensitivity_alongship
                angle_sensitivity_athwartship
        
        '''
        if 'angle' not in self.data:
            raise ValueError('Cannot calculate physical angles:  Missing raw angle data')
        
        #Fill default values for transceivers if needed & convert
        #any string channel ID's to channel indexes
        calibration = self.fill_default_transceiver_calibration(channels)                    
                        

        data_key = 'p_angles'

        #Remove existing column into the DataFrame if required
        if data_key in self.data:
            del self.data[data_key]
        
        #Group by channel and pulse length
        grouped = self.data.groupby(['channel'])
              
              
        angle_dtype = pd.np.dtype([('alongship', pd.np.float), ('athwartship', pd.np.float)])
        
        result = {}
        for channel, group in grouped:
            
            #Skip channels not listed in calibration dictionary
            if channel not in calibration:               
                continue
            
            cal = calibration[channel]

            alongship_offset = cal['angle_offset_alongship']
            alongship_sensitivity = cal['angle_sensitivity_alongship']
            
            athwartship_offset = cal['angle_offset_athwartship']
            athwartship_sensitivity = cal['angle_sensitivity_athwartship']                    

            
            for row_index, row in group.iterrows():
            
                #Skip pings with no power values    
                #Skip pings with no power values
                #    This is now handled in unit_conversion
                #    Empty arrays produce empty arrays    
#                if pd.np.all(pd.isnull(row['angle'])):
#                    continue

                #Get indexed angle values            
                alongship_indexed = (row['angle'] & 0xFF).astype('int8')
                athwartship_indexed = (row['angle'] >> 8).astype('int8')
                
                #Setup array
                angle_result = pd.np.empty((len(row['angle']),), dtype=angle_dtype)
                
                #Calculate physical angles
                angle_result['alongship'] = \
                    unit_conversion.indexed_to_physical_angle(alongship_indexed, 
                        sensitivity=alongship_sensitivity, offset=alongship_offset)
                    
                angle_result['athwartship'] = \
                    unit_conversion.indexed_to_physical_angle(athwartship_indexed, 
                        sensitivity=athwartship_sensitivity, offset=athwartship_offset)
                
                result[row_index] = [angle_result]                    

        new_df = pd.DataFrame.from_dict(result, orient='index')
        new_df.columns = [data_key]
        self.data = self.data.join(new_df, on=None, how='left')                    
    
    def electrical_angles(self, channels=None):
        '''
        :param channels:  Desired channels to perform calcs on
        :type channels:  int, str, list or None
               
        :param calibration:  User-set calibration values
        :type calibration: dict
        
        Calculates the electrical alongship and athwartship angles
        and appends it to the `data` DataFrame w/ key 'e_angles'
         
        '''
        if 'angle' not in self.data:
            raise ValueError('Cannot calculate electrical angles:  Missing raw angle data')
        #Fill default values for transceivers if needed & convert
        #any string channel ID's to channel indexes
        calibration = self.fill_default_transceiver_calibration(channels)                    
                        

        data_key = 'e_angles'

        #Remove existing column into the DataFrame if required
        if data_key in self.data:
            del self.data[data_key]
        
        #Group by channel and pulse length
        grouped = self.data.groupby(['channel'])
              
              
        angle_dtype = pd.np.dtype([('alongship', pd.np.float), ('athwartship', pd.np.float)])
        result = {}
        for channel, group in grouped:
            
            #Skip channels not listed in calibration dictionary
            if channel not in calibration:               
                continue
            
            for row_index, row in group.iterrows():
            
                #Skip pings with no power values
                #    This is now handled in unit_conversion
                #    Empty arrays produce empty arrays    
#                if pd.np.all(pd.isnull(row['angle'])):
#                    continue

                #Get indexed angle values            
                alongship_indexed = (row['angle'] & 0xFF).astype('int8')
                athwartship_indexed = (row['angle'] >> 8).astype('int8')
                
                #Setup array
                angle_result = pd.np.empty((len(row['angle']),), dtype=angle_dtype)
                
                #Calculate physical angles
                angle_result['alongship'] = \
                    unit_conversion.indexed_to_electrical_angle(alongship_indexed)
                    
                angle_result['athwartship'] = \
                    unit_conversion.indexed_to_electrical_angle(athwartship_indexed)
                                    
                result[row_index] =  [angle_result]
                
        new_df = pd.DataFrame.from_dict(result, orient='index')
        new_df.columns = [data_key]
        self.data = self.data.join(new_df, on=None, how='left')
    
    def indexed_angles(self, channels=None):
        '''
        :param channels:  Desired channels to perform calcs on
        :type channels:  int, str, list or None
               
        
        Calculates the indexed alongship and athwartship angles
        and appends it to the `data` DataFrame w/ key 'i_angles'
        

        '''
        if 'angle' not in self.data:
            raise ValueError('Cannot calculate indexed angles:  Missing raw angle data')

        #Fill default values for transceivers if needed & convert
        #any string channel ID's to channel indexes
        calibration = self.fill_default_transceiver_calibration(channels)                    

        data_key = 'i_angles'

        #Remove existing column into the DataFrame if required
        if data_key in self.data:
            del self.data[data_key]
        
        #Group by channel and pulse length
        grouped = self.data.groupby(['channel'])
              
              
        angle_dtype = pd.np.dtype([('alongship', pd.np.int8), ('athwartship', pd.np.int8)])
        result = {}
        #print("3258")
        #print("grouped", grouped)
        for channel, group in grouped:
            #print("channel, group", channel, group)
            
            #Skip channels not listed in calibration dictionary
            if channel not in calibration:               
                continue
            
            
            for row_index, row in group.iterrows():
                #print("row_index, row", row_index, row)
            
                #Skip pings with no power values
                #    This is now handled in unit_conversion
                #    Empty arrays produce empty arrays    
#                if pd.np.all(pd.isnull(row['angle'])):
#                    continue

                               
                #Setup array
                angle_result = pd.np.empty((len(row['angle']),), dtype=angle_dtype)
                
                #Get indexed angles
                angle_result['alongship'] = (row['angle'] & 0xFF).astype('int8')
                angle_result['athwartship'] = (row['angle'] >> 8).astype('int8')

                #print("angle_result", angle_result)
                      
                
                result[row_index] = [angle_result]              
                #print("result", result)

                
        new_df = pd.DataFrame.from_dict(result, orient='index')
        new_df.columns = [data_key]
        self.data = self.data.join(new_df, on=None, how='left')
