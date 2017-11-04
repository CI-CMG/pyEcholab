# coding=utf-8
'''
.. module:: echolab.nmea

    :synopsis: Class definitions for NMEA strings

Custom parsers for NMEA telegrams

NMEA objects are basically dictionaries extened with a few helper functions
for parsing/packing and checking data values.  Not all possible NMEA strings
have provided NMEA objects -- but creating new objects should not be hard.

All NMEA objects subclass NMEABase which provides the machinery.  A comprehensive
list of possible NMEA strings can be found in the NMEA.txt file in the doc directory
of this package.

Additional NMEA standards may be found at http://www.nmea.org, including
http://www.nmea.org/Assets/100108_nmea_0183_sentences_not_recommended_for_new_designs.pdf

which contains definitions for depreciated NMEA sentences (such as ZTA found
in SIMRAD's example Ofoten data)

Basic guidelines for subclassing off NMEABase:

    1.  Your class should be a three-letter upperclass name (DTM, GLL, etc.)
    2.  Copy the example from NMEA.txt for your docstring
    3.  try to stay consistant in naming your fields
    4.  DON'T list 'checksum' in the nmea_fields list
    5.  make sure `nmea_type` == class_name


DEFINED NMEA CODES:

['DBS', 'DTM', 'HDG', 'HDM', 'HDT', 'GGA', 'GLL', 'GSA', 'MTW', 'RMB', 'RMC', 
'RME', 'RMM', 'SHR', 'TDS', 'TPT', 'VHW', 'VLW', 'VTG', 'VTG_OLD', 'ZDA', 'ZTA',
'ZTG']
  

| Zac Berkowitz <zachary.berkowitz@noaa.gov>
| National Oceanic and Atmospheric Administration
| Alaska Fisheries Science Center
| Midwater Assesment and Conservation Engineering Group

$Id$
'''
from math import log10, ceil
from warnings import warn
from functools import reduce
__all__ = ['DBS', 'DTM', 'HDG', 'HDM', 'HDT', 'GGA', 'GLL', 'GSA', 'MTW',
           'RMB', 'RMC', 'RME',
           'RMM', 'SHR', 'TDS', 'TPT', 'VHW', 'VLW', 'VTG', 'VTG_OLD',
           'ZDA', 'ZTA', 'ZTG']

class NMEABase(dict):
    '''
    Base NMEA class.  Subclass for specific NMEA strings to access attributes
    directly.
    
    
    Basic guidelines for subclassing off NMEABase:

    1.  Your class should be a three-letter upperclass name (DTM, GLL, etc.)
    2.  Copy the example from NMEA.txt for your docstring
    3.  try to stay consistant in naming your fields
    4.  DON'T list 'checksum' in the nmea_fields list
    5.  make sure `nmea_type` == class_name
    6.  make sure `super` calls your new class    
    '''
    
#    nmea_type = None
#    nmea_fields = []

    def __init__(self, nmea_fields = [], append_crlf = False, append_checksum = True, drop_empty=False):

        dict.__init__(self)
        self.nmea_fields = nmea_fields
        self.__auto_checksum_update = False
        self.__append_crlf = append_crlf
        self.__append_checksum = append_checksum
        self.__drop_empty = drop_empty

        self['head'] = ''
        self['checksum'] = ''
        
        for field in nmea_fields:
            self[field] = ''

    def __str__(self):
        return self.pack()

    def __setitem__(self, name, value):
        
        dict.__setitem__(self, name, value)
        if self.auto_checksum_update and name != 'checksum':
            self.update_checksum()
            

    def parse(self, nmea_message):
        '''
        Parses fields from a NMEA string

        :param nmea_message:  NMEA string to parse
        :type nmea_message:  str

        :raises TypeError: If nmea_message is not the proper type
        :returns: None
        '''
        self.__auto_checksum_update = False
        nmea_string, chksum_sep, checksum = nmea_message.strip('\r\n\x00').partition('*')

        fields = nmea_string.split(',')

        num_nmea_fields = min(len(fields) - 1, len(self.nmea_fields))

        self['head'] =  fields[0]
        
        if num_nmea_fields == 0:
            _, _, raw_nmea = nmea_message.partition(',')
            self.__setitem__('raw_nmea', raw_nmea)
        else:
            for k in range(num_nmea_fields):
                name = self.nmea_fields[k]
                val  = fields[k + 1]

                #Order of type conversions:  int -> float -> str
                converted = False
                try:
                    self[name] = int(val)
                    covnerted = True

                except ValueError:
                    pass

                if converted:
                    continue

                try:
                    self[name] = float(val)
                    converted = True
                
                except ValueError:
                    pass

                if converted:
                    continue

                self[name] = val

            
            if checksum == '':
                self.append_checksum = False
            else:
                self.append_checksum = True
    
        self['checksum'] =  checksum
        self.auto_checksum_update = True

    def pack(self):
        '''
        Packs the fields of a NMEA object into a string suitable for transmission
        
        :returns:  str
        '''

        nmea_string = self.__getitem__('head') + ',' 
        
        if self.nmea_fields != []:
            fields = [str(self.get(x, '')) for x in self.nmea_fields]
            
            if self.drop_empty:
                fields = [x for x in fields if x != '']

            #If the last field is empty we need to append dummy item
            if fields[-1] == '':
                fields.append('')

        else:
            fields = [self['raw_nmea']]

        nmea_string += ','.join(fields)
        
        checksum = self.get('checksum', '')
        
        if self.append_checksum:
            nmea_message = '*'.join([nmea_string, checksum])
        else:
            nmea_message = nmea_string

        if self.append_crlf:
            return nmea_message + '\r\n'
        else:
            return nmea_message

    def calc_checksum(self):
        '''
        Calculates the propper checksum value based on current data

        :returns: str containing hex checksum
        '''

        nmea_message = self.pack()
        nmea_string = nmea_message.partition('*')[0]
        nmea_data = nmea_string.partition('$')[-1]

#        checksum = 0
#        for c in nmea_data:
#            checksum ^= ord(c)

        checksum = reduce(lambda x,y: x ^ ord(y), nmea_data, 0)
        return '%02X' % (checksum)

    def update_checksum(self):
        '''
        Recalculates and updates the checksum value for this NMEA message
        '''
        checksum_value = self.calc_checksum()
        self['checksum'] = checksum_value

    def is_valid(self):
        '''
        Compares the provided checksum value against the value
        calculated off the current data.  Returns True if the provided
        checksum matches the calculated value, False otherwise (or if 
        no checksum provided in the first place)
        '''
        checksum = self.get('checksum', '')
        if checksum == '':
            return False

        if checksum != self.calc_checksum():
            return False
        else:
            return True

    @property
    def talker_id(self):
        '''
        Returns the Talker ID of the NMEA data (First two characters after '$' mark)
        '''
        return self['head'][1:3]

    @property
    def nmea_type(self):
        '''
        Returns the NMEA type (last three characters of the NMEA header)
        '''
        return self['head'][3:]

    @property
    def auto_checksum_update(self):
        '''
        Enable/Disable automatic checksum updating.  Disabling before muliple changes may
        improve performance
        
        .. note:: Automatic checksum updating is currently DISABLED due to
            recursion issues.  Enabling this flag has no effect.
        '''
        return self.__auto_checksum_update

    @auto_checksum_update.setter
    def auto_checksum_update(self, bool_):
        self.__auto_checksum_update = bool_

    @property
    def append_crlf(self):
        '''
        Append a carridge return + line feed control string to the end of the NMEA message
        '''
        return self.__append_crlf

    @append_crlf.setter
    def append_crlf(self, bool_):
        self.__append_crlf = bool_

    @property
    def append_checksum(self):
        '''
        Append the checksum value to the NMEA string
        '''
        return self.__append_checksum
        
    @append_checksum.setter
    def append_checksum(self, bool_):
        self.__append_checksum = bool_


    @property
    def drop_empty(self):
        '''
        Drop empty fields completely from string representation
        
        | i.e. '$GPGLL,5350.546,N,16635.007,W,,,*51'
        | becomes: 'GPGLL,5350.546,N,16635.007,W*7D'
        '''
        return self.__drop_empty
    
    @drop_empty.setter
    def drop_empty(self, bool_):
        self.__drop_empty = bool_

    def calc_decimal_degrees(self):

        for field in ['latitude', 'longitude']:
            if field not in self:
                continue

            dec_field = 'dec_' + field

            d_, _, m_ = str(self[field]).partition('.')
            d = int(d_[:-2])
            m = d_[-2:] + '.' + m_
            
            dd = d + float(m) / 60.0
        
                
            self[dec_field] = dd

    def update_from_dec_degrees(self):

        for field in ['dec_latitude', 'dec_longitude']:
            if field not in self:
                continue

            new_field = field[4:]
            #d, m = REGEX.search(self[field]).groups()

            dd = float(self[field])          
            d = int(dd)
            dm = dd - d 
            
            m = round(60.0 * dm, 4)
                        
            self[new_field] = '{0:d}{1:6.4f}'.format(d, m)


class DBS(NMEABase):
    '''
    DBS - Depth Below Surface
    
    
            1   2 3   4 5   6 7
            |   | |   | |   | |
     $--DBS,x.x,f,x.x,M,x.x,F*hh<CR><LF>
    
    
    Field Number: 
    
    1. Depth, feet
    2. f = feet
    3. Depth, meters
    4. M = meters
    5. Depth, Fathoms
    6. F = Fathoms
    7. Checksum
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['depth_feet', 'depth_feet_ind', 
                       'depth_meters', 'depth_meters_ind',
                       'depth_fathoms', 'depth_fathoms_ind']
        
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)

        if nmea_string is not None:
            self.parse(nmea_string)
            
class DTM(NMEABase):
    '''
    === DTM - Datum Reference ===

    ------------------------------------------------------------------------------
              1  2  3   4  5   6  7  8    9
              |  |  |   |  |   |  |  |    |
     $ --DTM,ref,x,llll,c,llll,c,aaa,ref*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number: 

    1. Local datum code.  
    2. Local datum subcode.  May be blank.
    3. Latitude offset (minutes)
    4. N or S 
    5. Longitude offset (minutes)
    6. E or W
    7. Altitude offset in meters
    8. Datum name. What's usually seen here is "W84", the standard
       WGS84 datum used by GPS.
    9. Checksum.
    '''



#    nmea_type = 'DTM'

    def __init__(self, nmea_string):
        nmea_fields = ['datum_code', 'datum_subcode', 'lat_offset', 'lat_direction',
                   'lon_offset', 'lon_direction', 'alt_offset', 'datum_name']

        NMEABase.__init__(self, nmea_fields=nmea_fields,
                                  append_crlf = False, append_checksum = True)


        if nmea_string is not None:
            self.parse(nmea_string)

class HDG(NMEABase):
    '''
    === HDG - Heading - Deviation & Variation ===

    ------------------------------------------------------------------------------
            1   2   3 4   5 6
            |   |   | |   | |
     $--HDG,x.x,x.x,a,x.x,a*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number: 

    1. Magnetic Sensor heading in degrees
    2. Magnetic Deviation, degrees
    3. Magnetic Deviation direction, E = Easterly, W = Westerly
    4. Magnetic Variation degrees
    5. Magnetic Variation direction, E = Easterly, W = Westerly
    6. Checksum
    '''


#    nmea_type = 'HDG'

    def __init__(self, nmea_string):
        nmea_fields = ['mag_heading_deg', 'mag_dev_deg', 'mag_dev_dir',
                   'mag_var_deg', 'mag_var_dir']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                                  append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)
class HDM(NMEABase):
    '''
    === HDM - Heading - Magnetic ===

    Vessel heading in degrees with respect to magnetic north produced by
    any device or system producing magnetic heading.

    ------------------------------------------------------------------------------
            1   2 3
            |   | |
     $--HDM,x.x,M*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number: 

    1. Heading Degrees, magnetic
    2. M = magnetic
    3. Checksum
    '''


#    nmea_type = 'HDM'

    def __init__(self, nmea_string):
        nmea_fields = ['mag_heading_deg', 'mag_indicator']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                                  append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)
class HDT(NMEABase):
    '''
    === HDT - Heading - True ===

    Actual vessel heading in degrees true produced by any device or system
    producing true heading.

    ------------------------------------------------------------------------------
            1   2 3
            |   | |
     $--HDT,x.x,T*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number: 

    1. Heading Degrees, true
    2. T = True
    3. Checksum
    '''
    

#    nmea_type = 'HDT'

    def __init__(self, nmea_string):
        NMEABase.__init__(self, nmea_fields = ['true_heading_deg', 'true_indicator'],
                append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

class GGA(NMEABase):
    '''
    === GGA - Global Positioning System Fix Data ===

    Time, Position and fix related data for a GPS receiver.

    ------------------------------------------------------------------------------
                                                          
               1         2    3     4    5 6  7  8   9  10 11 12 13  14  15
               |         |    |     |    | |  |  |   |  |  |  |  |   |   |    
     $--GGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number:
    1. Universal Time Coordinated (UTC)
    2. Latitude
    3. N or S (North or South)
    4. Longitude
    5. E or W (East or West)
    6. GPS Quality Indicator,
         - 0 - fix not available,
         - 1 - GPS fix,
         - 2 - Differential GPS fix
               (values above 2 are 2.3 features)
         - 3 = PPS fix
         - 4 = Real Time Kinematic
         - 5 = Float RTK
         - 6 = estimated (dead reckoning)
         - 7 = Manual input mode
         - 8 = Simulation mode
    7. Number of satellites in view, 00 - 12
    8. Horizontal Dilution of precision (meters)
    9. Antenna Altitude above/below mean-sea-level (geoid) (in meters)
    10. Units of antenna altitude, meters
    11. Geoidal separation, the difference between the WGS-84 earth
         ellipsoid and mean-sea-level (geoid), "-" means mean-sea-level
         below ellipsoid
    12. Units of geoidal separation, meters
    13. Age of differential GPS data, time in seconds since last SC104
         type 1 or 9 update, null field when DGPS is not used
    14. Differential reference station ID, 0000-1023
    15. Checksum
    
    
    Set decimal_degrees = True after parsing to convert to decimal degrees
    notation.
    
    NOTE:  Using GGA.pack() or str(GGA) ALWAYS uses degrees and minutes (NOT
    decimal degrees), converting if necessary before packing.
    '''


#    nmea_type = 'GGA'

    def __init__(self, nmea_string):
        NMEABase.__init__(self, nmea_fields = ['UTC', 'latitude', 'lat_direction', 'longitude', 'lon_direction',
        'gps_qual', 'num_sat', 'hor_dilution', 'ant_alt', 'alt_units', 'geoid_sep',
        'geoid_units', 'diff_age', 'diff_station'], append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

class GGAdd(GGA):
    '''
    === GGA - Global Positioning System Fix Data (Decimal Degrees) ===

    Time, Position and fix related data for a GPS receiver. (NOT OFFICALLY SUPPORTED)

    ------------------------------------------------------------------------------
                                                          11
            1         2       3 4        5 6 7  8   9  10 |  12 13  14   15
            |         |       | |        | | |  |   |   | |   | |   |    |
     $--GGA,hhmmss.ss,llll.ll,a,yyyyy.yy,a,x,xx,x.x,x.x,M,x.x,M,x.x,xxxx*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number:
    1. Universal Time Coordinated (UTC)
    2. Latitude
    3. N or S (North or South)
    4. Longitude
    5. E or W (East or West)
    6. GPS Quality Indicator,
         - 0 - fix not available,
         - 1 - GPS fix,
         - 2 - Differential GPS fix
               (values above 2 are 2.3 features)
         - 3 = PPS fix
         - 4 = Real Time Kinematic
         - 5 = Float RTK
         - 6 = estimated (dead reckoning)
         - 7 = Manual input mode
         - 8 = Simulation mode
    7. Number of satellites in view, 00 - 12
    8. Horizontal Dilution of precision (meters)
    9. Antenna Altitude above/below mean-sea-level (geoid) (in meters)
    10. Units of antenna altitude, meters
    11. Geoidal separation, the difference between the WGS-84 earth
         ellipsoid and mean-sea-level (geoid), "-" means mean-sea-level
         below ellipsoid
    12. Units of geoidal separation, meters
    13. Age of differential GPS data, time in seconds since last SC104
         type 1 or 9 update, null field when DGPS is not used
    14. Differential reference station ID, 0000-1023
    15. Checksum
    
    This is exactly the same as GGA, but latitude and longitude are in decimal
    degrees instead of DDDMM.MMMMM format.
    '''    

    #REGEX = re.compile(r'([0-9]{1,3})([0-9]{2}\.[0-9]+)')
    
    def parse(self, nmea_message):
        GGA.parse(self, nmea_message)
        
        for field in ['latitude', 'longitude']:
            #d, m = REGEX.search(self[field]).groups()
            d_, _, m_ = self[field].partition('.')
            
            d = int(d_[:-2])
            m = int(d_[-2:]) + float(m_)/(10**ceil(log10(float(m_))))
            
            dd = d + m / 60.0
            
            self[field] = str(dd)

    
class GLL(NMEABase):
    '''
    === GLL - Geographic Position - Latitude/Longitude ===

    ------------------------------------------------------------------------------
               1    2     3    4    5      6 7  8
               |    |     |    |    |      | |  |
     $--GLL,llll.ll,a,yyyyy.yy,a,hhmmss.ss,a,m,*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number: 

    1. Latitude
    2. N or S (North or South)
    3. Longitude
    4. E or W (East or West)
    5. Universal Time Coordinated (UTC)
    6. Status A - Data Valid, V - Data Invalid
    7. FAA mode indicator (NMEA 2.3 and later)
    8. Checksum
    '''

    def __init__(self, nmea_string=None):
        NMEABase.__init__(self, nmea_fields = ['latitude', 'lat_direction', 
                'longitude', 'lon_direction', 'UTC', 'status', 'faa_mode'],
                            append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)


class GNS(NMEABase):
    '''
    === GNS - Fix data ===

    ------------------------------------------------------------------------------
           1         2       3 4        5 6    7  8   9   10  11  12  13
           |         |       | |        | |    |  |   |   |   |   |   |
    $--GNS,hhmmss.ss,llll.ll,a,yyyyy.yy,a,c--c,xx,x.x,x.x,x.x,x.x,x.x*hh
    ------------------------------------------------------------------------------

    Field Number:

    1. UTC
    2. Latitude
    3. N or S (North or South)
    4. Longitude
    5. E or W (East or West)
    6. Mode indicator
    7. Total number of satelites in use,00-99
    8. HDROP
    9. Antenna altitude, meters, re:mean-sea-level(geoid.
    10. Goeidal separation meters
    11. Age of diferential data
    12. Differential reference station ID
    13. CRC
    '''

#    nmea_type = 'GLL'

    def __init__(self, nmea_string):
        NMEABase.__init__(self, nmea_fields = ['UTC', 'latitude', 'lat_direction', 
                'longitude', 'lon_direction', 'status', 'faa_mode', 'num_satellite',
                'antenna_alt', 'geoid_sep', 'diff_age', 'diff_station'],
                            append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

    #     self._decimal_degrees = False
    
    # @property
    # def decimal_degrees(self):
    #     return self._decimal_degrees
#    
#    @property
#    def degrees(self):
#        if self.decimal_degrees:
#            return map(lambda x: int(float(x)), [self['latitude'], self['longitude']])
#        else:
#            return [x.partition('[0][:-2] for x ]
#     @decimal_degrees.setter
#     def decimal_degrees(self, bool_):
#         if bool_ == self.decimal_degrees:
#             return

#         #Disable automatic checksum updates for conversion -- causes
#         #infinite recursion otherwise through .pack()
#         orig_chksum_update_bool = self.auto_checksum_update
#         self.auto_checksum_update = False        
        
#         if bool_:
#             for field in ['latitude', 'longitude']:
#                 #d, m = REGEX.search(self[field]).groups()
#                 d_, _, m_ = self[field].partition('.')
                
#                 d = int(d_[:-2])
#                 if abs(d) > 360:
#                     raise ValueError('Invalid decimal degrees value:  %d' % d)
# #                m = int(d_[-2:]) + float(m_)/(10**ceil(log10(float(m_))))
#                 m = d_[-2:] + '.' + m_
                
#                 dd = d + float(m) / 60.0
            
                    
#                 self[field] = str(dd)
#         else:
#             for field in ['latitude', 'longitude']:
#                 #d, m = REGEX.search(self[field]).groups()
#                 dd = float(self[field])
                
#                 d = int(dd)
#                 dm = dd - d 
                
#                 m = round(60.0 * dm, 4)
                            
#                 self[field] = '{0:d}{1:6.4f}'.format(d, m)

#         self._decimal_degrees = bool_
#         self.auto_checksum_update = orig_chksum_update_bool
            
#     def pack(self):                  
#         if self.decimal_degrees:
#             self.decimal_degrees = False
#             ret_str = NMEABase.pack(self)
#             self.decimal_degrees = True
        
#         else:
#             ret_str =  NMEABase.pack(self)
            
#         return ret_str

#     def calc_checksum(self):
#         if self.decimal_degrees:
#             raise ValueError('Checksum calculations disabled while using decimal degrees')
        
#         else:
#             return NMEABase.calc_checksum(self)

class GSA(NMEABase):
    '''
    === GSA - GPS DOP and active satellites ===
    
    ------------------------------------------------------------------------------
        1 2 3                        14 15  16  17  18
        | | |                         |  |   |   |   |
     $--GSA,a,a,x,x,x,x,x,x,x,x,x,x,x,x,x,x,x.x,x.x,x.x*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Selection mode: M=Manual, forced to operate in 2D or 3D, A=Automatic, 3D/2D
    2. Mode (1 = no fix, 2 = 2D fix, 3 = 3D fix)
    3. ID of 1st satellite used for fix
    4. ID of 2nd satellite used for fix
    5. ID of 3rd satellite used for fix
    6. ID of 4th satellite used for fix
    7. ID of 5th satellite used for fix
    8. ID of 6th satellite used for fix
    9. ID of 7th satellite used for fix
    10. ID of 8th satellite used for fix
    11. ID of 9th satellite used for fix
    12. ID of 10th satellite used for fix
    13. ID of 11th satellite used for fix
    14. ID of 12th satellite used for fix
    15. PDOP
    16. HDOP
    17. VDOP
    18. Checksum
    '''
    
    def __init__(self, nmea_string):
        NMEABase.__init__(self, nmea_fields = ['selection_mode', 'mode',
                'satellite_ids', 'pdop', 'hdop', 'vdop'], append_crlf = False, 
                 append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)
        
    def parse(self, nmea_message):
        '''
        Parses fields from a NMEA string

        :param nmea_message:  NMEA string to parse
        :type nmea_message:  str

        :raises TypeError: If nmea_message is not the proper type
        :returns: None
        '''
        self.__auto_checksum_update = False
        nmea_string, chksum_sep, checksum = nmea_message.strip('\r\n\x00').partition('*')

        fields = nmea_string.split(',')

        #num_nmea_fields = len(fields) - 1
        num_nmea_fields = min(len(fields) - 1, len(self.nmea_fields))
#        if self.nmea_type != fields[0][-3:]:
#            raise TypeError('NMEA type %s does not match %s' % (fields[0], self.nmea_type))
#        else:
#            self.__setitem__('head', fields[0])

        self.__setitem__('head', fields[0])
        
        if num_nmea_fields == 0:
            _, _, raw_nmea = nmea_message.partition(',')
            self.__setitem__('raw_nmea', raw_nmea)
        else:
            self.__setitem__('selection_mode', fields[1])
            self.__setitem__('mode', fields[2])
            
            satellite_ids = []
            for satellite_id in fields[3:15]:
                if satellite_id == '':
                    satellite_ids.append(None)
                else:
                    satellite_ids.append(int(satellite_id))
            self.__setitem__('satellite_ids', satellite_ids)
            self.__setitem__('pdop', fields[15])
            self.__setitem__('hdop', fields[16])                    
            self.__setitem__('vdop', fields[17])
            
            
            if checksum == '':
                self.append_checksum = False
            else:
                self.append_checksum = True
    
        self.__setitem__('checksum', checksum)
        self.__auto_checksum_update = True

    def pack(self):
        '''
        Packs the fields of a NMEA object into a string suitable for transmission
        
        :returns:  str
        '''

        nmea_string = self.__getitem__('head') + ',' 
        
        if self.nmea_fields != []:
            fields = [self.get('selection_mode'), self.get('mode')]
            for id in self.get('satellite_ids'):
                if id is None:
                    str_id = ''
                else:
                    str_id = '{0:02d}'.format(id)
                    
                fields.append(str_id)
                
            fields.extend([self.get('pdop'), self.get('hdop'), self.get('vdop')]) 

            #Ignore drop empty, we can have empty sattelite ids
#            if self.drop_empty:
#                fields = filter(lambda x: x != '', fields)
        
        else:
            fields = [self.__getitem__('raw_nmea')]

        nmea_string += ','.join(fields)
        
        checksum = self.get('checksum', '')
        
        if self.append_checksum:
            nmea_message = '*'.join([nmea_string, checksum])
        else:
            nmea_message = nmea_string

        if self.append_crlf:
            return nmea_message + '\r\n'
        else:
            return nmea_message

class GSV(NMEABase):
    '''
    === GSV - Satellites in view ===
    
    These sentences describe the sky position of a UPS satellite in view.
    Typically they're shipped in a group of 2 or 3.
    
    ------------------------------------------------------------------------------
        1 2 3 4 5 6 7     n
        | | | | | | |     |
     $--GSV,x,x,x,x,x,x,x,...*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. total number of GSV messages to be transmitted in this group
    2. 1-origin number of this GSV message  within current group
    3. total number of satellites in view (leading zeros sent)
    4. satellite PRN number (leading zeros sent)
    5. elevation in degrees (00-90) (leading zeros sent)
    6. azimuth in degrees to true north (000-359) (leading zeros sent)
    7. SNR in dB (00-99) (leading zeros sent)
       more satellite info quadruples like 4-7
       n) checksum
    
    Example:
        $GPGSV,3,1,11,03,03,111,00,04,15,270,00,06,01,010,00,13,06,292,00*74
        $GPGSV,3,2,11,14,25,170,00,16,57,208,39,18,67,296,40,19,40,246,00*74
        $GPGSV,3,3,11,22,42,067,42,24,14,311,43,27,05,244,00,,,,*4D
    
    Some GPS receivers may emit more than 12 quadruples (more than three
    GPGSV sentences), even though NMEA-0813 doesn't allow this.  (The
    extras might be WAAS satellites, for example.) Receivers may also
    report quads for satellites they aren't tracking, in which case the
    SNR field will be null; we don't know whether this is formally allowed
    or not.
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['num_msgs', 'current_msg', 'num_satellites',
                   'satellite_info']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)

        if nmea_string is not None:
            self.parse(nmea_string)
        
    
    def parse(self, nmea_message):
        '''
        Parses fields from a NMEA string

        :param nmea_message:  NMEA string to parse
        :type nmea_message:  str

        :raises TypeError: If nmea_message is not the proper type
        :returns: None
        '''
        self.__auto_checksum_update = False
        nmea_string, chksum_sep, checksum = nmea_message.strip('\r\n\x00').partition('*')

        fields = nmea_string.split(',')

        #num_nmea_fields = len(fields) - 1
        num_nmea_fields = min(len(fields) - 1, len(self.nmea_fields))
#        if self.nmea_type != fields[0][-3:]:
#            raise TypeError('NMEA type %s does not match %s' % (fields[0], self.nmea_type))
#        else:
#            self.__setitem__('head', fields[0])

        self.__setitem__('head', fields[0])
        
        if num_nmea_fields == 0:
            _, _, raw_nmea = nmea_message.partition(',')
            self.__setitem__('raw_nmea', raw_nmea)
        else:
            self.__setitem__('num_msgs', fields[1])
            self.__setitem__('current_msg', fields[2])
            self.__setitem__('num_satellites', fields[3])
            
            
            num_satellites = len(fields[4:])/4
            satellite_info = []
            for k in range(1, num_satellites + 1):
                prn = fields[4*k]
                elevation = fields[4*k + 1]
                azimuth = fields[4*k+ + 2]
                snr = fields[4*k + 3]
                
                satellite_info.append(dict(prn=prn,
                                           elevation_deg=elevation,
                                           azimuth_deg=azimuth,
                                           snr_db=snr))
            
            self.__setitem__('satellite_info', satellite_info)    
            if checksum == '':
                self.append_checksum = False
            else:
                self.append_checksum = True
    
        self.__setitem__('checksum', checksum)
        self.__auto_checksum_update = True

    def pack(self):
        '''
        Packs the fields of a NMEA object into a string suitable for transmission
        
        :returns:  str
        '''

        nmea_string = self.__getitem__('head') + ',' 
        
        if self.nmea_fields != []:
            fields = [self.get('num_msgs'), self.get('current_msg'),
                      self.get('num_satellites')]
            
            for s in self.get('satellite_info'):
                fields.extend([s['prn'], s['elevation_deg'], s['azimuth_deg'],
                            s['snr_db']])

            #Ignore drop empty, we can have empty sattelite ids
#            if self.drop_empty:
#                fields = filter(lambda x: x != '', fields)
        
        else:
            fields = [self.__getitem__('raw_nmea')]

        nmea_string += ','.join(fields)
        
        checksum = self.get('checksum', '')
        
        if self.append_checksum:
            nmea_message = '*'.join([nmea_string, checksum])
        else:
            nmea_message = nmea_string

        if self.append_crlf:
            return nmea_message + '\r\n'
        else:
            return nmea_message   

class MTW(NMEABase):
    '''
    === MTW - Mean Temperature of Water ===
    
    ------------------------------------------------------------------------------
            1   2 3
            |   | | 
     $--MTW,x.x,C*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Degrees
    2. Unit of Measurement, Celcius
    3. Checksum
    
    [GLOBALSAT] lists this as "Meteorological Temperature of Water", which
    is probably incorrect.
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['temp_degrees', 'unit']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)
        
        if nmea_string is not None:
            self.parse(nmea_string)

class RMB(NMEABase):
    '''
    === RMB - Recommended Minimum Navigation Information ===
    
    To be sent by a navigation receiver when a destination waypoint is active.
    
    ------------------------------------------------------------------------------
                                                                 14
            1 2   3 4    5    6       7 8        9 10  11  12  13|  15
            | |   | |    |    |       | |        | |   |   |   | |   |
     $--RMB,A,x.x,a,c--c,c--c,llll.ll,a,yyyyy.yy,a,x.x,x.x,x.x,A,m,*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Status, A= Active, V = Void
    2. Cross Track error - nautical miles
    3. Direction to Steer, Left or Right
    4. TO Waypoint ID
    5. FROM Waypoint ID
    6. Destination Waypoint Latitude
    7. N or S
    8. Destination Waypoint Longitude
    9. E or W
    10. Range to destination in nautical miles
    11. Bearing to destination in degrees True
    12. Destination closing velocity in knots
    13. Arrival Status, A = Arrival Circle Entered
    14. FAA mode indicator (NMEA 2.3 and later)
    15. Checksum
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['status', 'cross_track_error', 'direction_to_steer',
                   'to_waypoint_id', 'from_waypoint_id', 
                   'destination_latitude', 'lat_direction', 
                   'destination_longitude', 'lon_direction', 
                   'range_to_destination_nm', 'bearing_to_destination_deg',
                   'closing_velocity_knots', 'arrival_status',
                   'faa_mode']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)  
        if nmea_string is not None:
            self.parse(nmea_string)


class RMC(NMEABase):
    '''
    === RMC - Recommended Minimum Navigation Information ===

    ------------------------------------------------------------------------------
                                                              12
            1         2 3       4 5        6  7   8   9    10 11|  13
            |         | |       | |        |  |   |   |    |  | |   |
     $--RMC,hhmmss.ss,A,llll.ll,a,yyyyy.yy,a,x.x,x.x,xxxx,x.x,a,m,*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number:
    
    1. UTC Time
    2. Status, V=Navigation receiver warning A=Valid
    3. Latitude
    4. N or S
    5. Longitude
    6. E or W
    7. Speed over ground, knots
    8. Track made good, degrees true
    9. Date, ddmmyy
    10. Magnetic Variation, degrees
    11. E or W
    12. FAA mode indicator (NMEA 2.3 and later)
    13. Checksum
    
    A status of V means the GPS has a valid fix that is below an internal
    quality threshold, e.g. because the dilution of precision is too high 
    or an elevation mask test failed.
    '''
    

    
#    nmea_type = 'RMC'
    
    def __init__(self, nmea_string):
        nmea_fields = ['UTC', 'status', 'latitude', 'lat_direction', 'longitude',
                   'lon_direction', 'speed_ground_knots', 'track_deg_true',
                   'date', 'mag_var_deg', 'mag_var_dir', 'faa_mode']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)

        if nmea_string is not None:
            self.parse(nmea_string)

class RMM(NMEABase):
    '''
    === PGRMM - Garmin Map Datum ===

    ------------------------------------------------------------------------------
             1   2
             |   |
     $PGRMM,ref*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number:
    
    1. Horizontal map datum (Usually WGS 84)
    2. Checksum
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['datum']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)    

        if nmea_string is not None:
            self.parse(nmea_string)
    
class RME(NMEABase):
    '''
    === PGRME - Garmin Estimated Error ===
    
    ------------------------------------------------------------------------------
            1  2  3  4  5  6  7
            |  |  |  |  |  |  |
     $PGRME,hhh,M,vvv,M,ttt,M*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Estimated horizontal position error (HPE), 
    2. M=meters
    3. Estimated vertical position error (VPE)
    4. M=meters
    5. Overall spherical equivalent position error
    6. M=meters
    7. Checksum
    
    Example: $PGRME,15.0,M,45.0,M,25.0,M*22
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['horiz_position_error', 'horiz_units', 
                       'vert_position_error', 'vert_units', 
                       'overall_error', 'overall_units']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)
        if nmea_string is not None:
            self.parse(nmea_string)
        
class RMT(NMEABase):
    '''
    === PGRME - Garmin Sensor Status ===
    
    ------------------------------------------------------------------------------
             1  2 3 4  5 6 7 8 9
             |  | | |  | | | | |
     $PGRMT,mmm,P,P,R,R,P,C,tt,R*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Product, model, and software version, 
    2. ROM Checksum test, (P=Pass, F=Fail)
    3. Receiver failure discrete, (P=Pass, F=Fail)
    4. Stored data lost, (R=retained, L=lost)
    5. Real-time clock lost, (R=retained, L=lost)
    6. Oscillator drift, (P=pass, F=excessive drift)
    7. Data collection, (C=collection, Null if not collecting)
    8. Sensor temperature in deg centigrade
    9. Sensor configuration data, (R=retained, L=lost)
    7. Checksum
    
    Example: $PGRME,15.0,M,45.0,M,25.0,M*22
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['model', 'rom_checksum_test', 
                       'receiver_test', 'stored_data', 
                       'clock_test', 'oscillator_test',
                       'data_collection', 'sensor_temp_c',
                       'sensor_config']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)
        if nmea_string is not None:
            self.parse(nmea_string)


class SHR(NMEABase):
    '''
    === PASHR - RT300 proprietary roll and pitch sentence ===
    
    ------------------------------------------------------------------------------
             1           2   3    4      5      6     7     8     9  10 11 12 
             |           |   |    |      |      |     |     |     |   | |  |
    $PASHR,hhmmss.sss,hhh.hh,T,rrr.rr,ppp.pp,xxx.xx,a.aaa,b.bbb,c.ccc,d,e*hh<CR><LF>
    ------------------------------------------------------------------------------
     
    Field number:
     
    1.  hhmmss.sss - UTC time
    2.  hhh.hh - Heading in degrees
    3.  T - flag to indicate that the Heading is True Heading (i.e. to True North)
    4.  rrr.rr - Roll Angle in degrees
    5.  ppp.pp - Pitch Angle in degrees
    6.  xxx.xx - Heave
    7.  a.aaa - Roll Angle Accuracy Estimate (Stdev) in degrees
    8.  b.bbb - Pitch Angle Accuracy Estimate (Stdev) in degrees
    9.  c.ccc - Heading Angle Accuracy Estimate (Stdev) in degrees
    10. d - Aiding Status
    11. e - IMU Status
    12. hh - Checksum
    
    [PASHR] describes this sentence as NMEA, though other sources say it is Ashtech 
    proprietary and describe a different format.
     
    Example: $PASHR,085335.000,224.19,T,-01.26,+00.83,+00.00,0.101,0.113,0.267,1,0*06
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['UTC', 'heading_deg', 'true_heading_ind',
                       'roll_deg', 'pitch_deg', 'heave',
                       'roll_deg_std', 'pitch_deg_std', 'heading_deg_std',
                       'aiding_status', 'imu_status']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)
        if nmea_string is not None:
            self.parse(nmea_string)

class TDS(NMEABase):
    '''
    === TDS - Trawl Door Spread Distance ===
    
    ------------------------------------------------------------------------------
             1  2 3
             |  | |
     $--TDS,x.x,M*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number)
    
    1. Distance between trawl doors
    2. Meters (0-300)
    3. Checksum.
    
    From [GLOBALSAT].  Shown with a "@II" leader rather than "$GP".
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['distance', 'unit']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)
        if nmea_string is not None:
            self.parse(nmea_string)
        
class TPT(NMEABase):
    '''
    === TPT - Trawl Position True ===
    
    ------------------------------------------------------------------------------
            1 2 3 4  5  6 7
            | | | |  |  | |
     $--TPT,x,M,y,P,z.z,M*hh,<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number:
    
    1. Horizontal range relative to target
    2. Meters (0-4000)
    3. True bearing to taget (ie. relative north).  Resolution is one degree.
    4. Separator
    5. Depth of trawl below the surface
    6. Meters (0-2000)
    7. Checksum
    
    From [GLOBALSAT]. Shown with a "@II" leader rather than "$GP".
    '''
    def __init__(self, nmea_string):
        nmea_fields = ['horiz_range', 'horiz_meters', 'bearing_deg_true',
                       'sep', 'depth', 'depth_meters']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf=False, append_checksum=True)

        if nmea_string is not None:
            self.parse(nmea_string)
        

class VHW(NMEABase):
    '''
    === VHW - Water speed and heading ===

    ------------------------------------------------------------------------------
            1   2 3   4 5   6 7   8 9
            |   | |   | |   | |   | |
     $--VHW,x.x,T,x.x,M,x.x,N,x.x,K*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number: 

    1. Degress True
    2. T = True
    3. Degrees Magnetic
    4. M = Magnetic
    5. Knots (speed of vessel relative to the water)
    6. N = Knots
    7. Kilometers (speed of vessel relative to the water)
    8. K = Kilometers
    9. Checksum

    [GLOBALSAT] describes a different format in which the first three
    fields are water-temperature measurements.  It's not clear which 
    is correct.
    '''



#    nmea_type = 'VHW'

    def __init__(self, nmea_string):
        nmea_fields = ['true_heading_deg', 'true_indicator', 'mag_heading_deg', 'mag_indicator',
                   'speed_water_knots', 'knots_indicator', 'speed_water_kph', 'kph_indicator']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                                  append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

class VLW(NMEABase):
    '''
    === VLW - Distance Traveled through Water ===

    ------------------------------------------------------------------------------
            1   2 3   4 5
            |   | |   | |
     $--VLW,x.x,N,x.x,N*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number:

    1. Total cumulative distance
    2. N = Nautical Miles
    3. Distance since Reset
    4. N = Nautical Miles
    5. Checksum
    '''


#    nmea_type = 'VLW'

    def __init__(self, nmea_string):
        nmea_fields = ['total_distance', 'total_distance_unit',
        'distance_since_reset', 'distance_since_reset_unit']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

class VTG(NMEABase):
    '''
    === VTG - Track made good and Ground speed ===

    ------------------------------------------------------------------------------
             1  2  3  4  5  6  7  8 9   10
             |  |  |  |  |  |  |  | |   |
     $--VTG,x.x,T,x.x,M,x.x,N,x.x,K,m,*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number:

    1. Track Degrees
    2. T = True
    3. Track Degrees
    4. M = Magnetic
    5. Speed Knots
    6. N = Knots
    7. Speed Kilometers Per Hour
    8. K = Kilometers Per Hour
    9. FAA mode indicator (NMEA 2.3 and later)
    10. Checksum
    '''



#    nmea_type = 'VTG'

    def __init__(self, nmea_string):
        nmea_fields = ['track_deg_true', 'true_field', 'track_deg_mag', 'mag_field',
                   'speed_ground_knots', 'knots_field', 'speed_ground_kph', 'kph_field', 'faa_mode']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

class VTG_OLD(NMEABase):
    '''
    Note: in some older versions of NMEA 0183, the sentence looks like this:

    ------------------------------------------------------------------------------
             1  2  3   4  5
             |  |  |   |  |
     $--VTG,x.x,x,x.x,x.x,*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number:

    1. True course over ground (degrees) 000 to 359
    2. Magnetic course over ground 000 to 359
    3. Speed over ground (knots) 00.0 to 99.9
    4. Speed over ground (kilometers) 00.0 to 99.9
    5. Checksum

    The two forms can be distinguished by field 2, which will be
    the fixed text 'T' in the newer form.  The new form appears
    to have been introduced with NMEA 3.01 in 2002.

    Some devices, such as those described in [GLOBALSAT], leave the
    magnetic-bearing fields 3 and 4 empty.
    '''

    
#    nmea_type = 'VTG'

    def __init__(self, nmea_string):
        nmea_fields = ['track_deg_true', 'track_deg_mag', 
                      'speed_ground_knots', 'speed_ground_kph']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                append_crlf = False, append_checksum = True)

        if nmea_string is not None:
            self.parse(nmea_string)

class ZDA(NMEABase):
    '''
    === ZDA - Time & Date - UTC, day, month, year and local time zone ===

    ------------------------------------------------------------------------------
            1         2  3  4    5  6  7
            |         |  |  |    |  |  |
     $--ZDA,hhmmss.ss,xx,xx,xxxx,xx,xx*hh<CR><LF>
    ------------------------------------------------------------------------------

    Field Number:

    1. UTC time (hours, minutes, seconds, may have fractional subsecond)
    2. Day, 01 to 31
    3. Month, 01 to 12
    4. Year (4 digits)
    5. Local zone description, 00 to +- 13 hours
    6. Local zone minutes description, apply same sign as local hours
    7. Checksum

    Example: $GPZDA,160012.71,11,03,2004,-1,00*7D
    '''


#    nmea_type = 'ZDA'

    def __init__(self, nmea_string):
        nmea_fields = ['UTC', 'day', 'month', 'year', 'local_tz_hour', 'local_tz_min']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                    append_crlf = False, append_checksum = True)
        if nmea_string is not None:
            self.parse(nmea_string)

class ZTA(NMEABase):
    '''
    === ZTA - UTC & Time to Destination Waypoint ===
    
    ------------------------------------------------------------------------------
            1         2         3    4
            |         |         |    |
     $--ZTG,hhmmss.ss,hhmmss.ss,c--c*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Universal Time Coordinated (UTC)
    2. Time Remaining
    3. Destination Waypoint ID
    4. Checksum
    
    *** NMEA STANDARDS RECCOMMEND USE OF THE ZTG CODE FOR THIS DATA ***
    '''
    
    nmea_fields = ['UTC', 'time_remaining', 'waypoint_id']
    nmea_type = 'ZTA'
    
    def __init__(self, nmea_string):
        NMEABase.__init__(self, append_crlf = False, append_checksum = True)
        if nmea_string is not None:
            self.parse(nmea_string)
        
class ZTG(NMEABase):
    '''
    === ZTG - UTC & Time to Destination Waypoint ===
    
    ------------------------------------------------------------------------------
            1         2         3    4
            |         |         |    |
     $--ZTG,hhmmss.ss,hhmmss.ss,c--c*hh<CR><LF>
    ------------------------------------------------------------------------------
    
    Field Number: 
    
    1. Universal Time Coordinated (UTC)
    2. Time Remaining
    3. Destination Waypoint ID
    4. Checksum
    '''
    
    
#    nmea_type = 'ZTG'
    
    def __init__(self, nmea_string):
        nmea_fields = ['UTC', 'time_remaining', 'waypoint_id']
        NMEABase.__init__(self, nmea_fields=nmea_fields,
                append_crlf = False, append_checksum = True)
        
        if nmea_string is not None:
            self.parse(nmea_string)
    