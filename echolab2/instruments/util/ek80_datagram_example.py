'''
    Simple example showing the use of the simrad_raw_file.RawSimradFile
    class to inspect the basic format of datafiles recorded using the
    EK80 application.

    Users will normally use the EK80 class to access these data. This
    example simply shows how to access the datagrams at a low level
    for more esoteric applications.

'''
from echolab2.instruments.util.simrad_raw_file import RawSimradFile

#  full path to EK80 recorded .raw file
filename = 'C:/EK80 Test Data/EK80/CW/complex/DY1802_EK80-D20180301-T185940.raw'

#  open it for read
fid =  RawSimradFile(filename, 'r')

#  first datagram is a config datagram
config_datagram = fid.read(1)


#  the read method returns a dict which always contains the following keys:
#    ['type', 'low_date', 'high_date', 'timestamp', 'bytes_read']
print('Config datagram type: ' + config_datagram['type'])

#  the config datagram is an XML0 datagram. XML0 datagrans will have two
#  more keys: 'subtype' and one that is named after the subtype. The
#  subtype for the XML0 configuration datagram is "configuration" so
#  the config_datagram dict will have 'subtype' and 'configuration' as
#  the two additional keys.
print(config_datagram.keys())
print('XML0 datagram sub-type: ' + config_datagram['subtype'])

#  the config_datagram[config_datagram['subtype']] then contains the goods
#  which in our case will be a dict that contains the parsed XML data by .
#  channel_id The keys of this dict will be the channel ID's of the channels
#  contained in the data file.
channel_ids = list(config_datagram[config_datagram['subtype']].keys())
print(channel_ids)

#  Each channel's value itself will be a dict which contains all of the
#  channel and transducer data for that channel. Note that the
#  key names have been changed from the Kongsberg CamelCase to lowered with
#  "_" for spaces. This was done to fit with the PyEcholab naming convention.
#  print out the first channel's configuration dict keys
print('Configuration datagram keys for channel:' + channel_ids[0])
print(config_datagram[config_datagram['subtype']][channel_ids[0]].keys())


#  What comes next depends on the hardware used.
#
#  If any of the channels in the file are WBTs, the FIL1 datagrams would be next.
#
#  Then you get a bit of async data as NME0 and XML "environment" datagrams.
#
#  Then it settles into a pattern of:
#
#       One MRU0, followed by one XML "parameter" and RAW3 datagram per channel,
#       then async NME0 and XML "environment" datagrams.
#
#  I've only been working with a couple of EK80 on EK80 data files and
#  a couple EK60 on EK80 so I don't know how reliable that pattern is.

#  print out some info about the next 50 datagrams after the configuration header
for i in range(50):
    #  read a datagram
    datagram = fid.read(1)

    #  now print some info about it
    if (datagram['type'] == 'XML0'):
        #  XML datagrams have subtypes that define what they contain
        print(datagram['timestamp'], datagram['type'], datagram['subtype'])

    elif (datagram['type'] == 'NME0'):
        #  nmea data is unchanged from ER60 format
        print(datagram['timestamp'], datagram['type'], datagram['nmea_type'])
    elif (datagram['type'].startswith('RAW')):
        if datagram['type'] == 'RAW0':
            #  data recorded using EK60 software
            print(datagram['timestamp'], datagram['type'], "channel:", datagram['channel'])
        else:
            #  data recorded using EK80 software
            print(datagram['timestamp'], datagram['type'], "channel:", datagram['channel_id'])
    else:
        #  Other datagrams like MRU0 or FIL1
        print(datagram['timestamp'], datagram['type'])

print('end')


