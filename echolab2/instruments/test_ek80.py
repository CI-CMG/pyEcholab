import xml.etree.ElementTree as ET
from util.simrad_raw_file import RawSimradFile



def compare_dicts(a, b):

    for ak in a.keys():
        try:
            if (b[ak] != a[ak]):
                print(ak + ": a = " + str(a[ak]) + "    b = " + str(b[ak]))
        except:
            print("b does not contain key " + ak)



#  simple script for developing the RawSimradFile EK80 parser

if (0):

    #  this is a CW file - EK60 on EK80
    filename = 'D:/Data/EK60 on EK80/D20180205-T233434.raw'
    fid =  RawSimradFile(filename, 'r')

    #  first datagram is a config datagram
    config_datagram = fid.read(1)

    #  THERE IS NO FIL0 datagrams in this file

    #  then there is a NME0 datagram
    NME0_datagram = fid.read(1)

    #  and environment
    environment_datagram= fid.read(1)

    #  and MRU0
    MRU0_datagram = fid.read(1)

    #  then the first param datagram
    param_datagram = fid.read(1)

    #  and the first RAW3 datagram
    RAW3_datagram = fid.read(1)



elif (0):

    #  this is a BB file - EK80 on EK80
    filename = 'D:/Data/EK80 on EK80/DY1801_EK80-D20180205-T200007.raw'
    fid =  RawSimradFile(filename, 'r')

    #  first datagram is a config datagram
    config_datagram = fid.read(1)

    #  then there are a bunch of FIL0 datagram
    FIL0_datagram_1 = fid.read(1)
    FIL0_datagram_2 = fid.read(1)
    FIL0_datagram_3 = fid.read(1)
    FIL0_datagram_4 = fid.read(1)
    FIL0_datagram_5 = fid.read(1)
    FIL0_datagram_6 = fid.read(1)
    FIL0_datagram_7 = fid.read(1)
    FIL0_datagram_8 = fid.read(1)
    FIL0_datagram_9 = fid.read(1)
    FIL0_datagram_10 = fid.read(1)

    #  then there is a NME0 datagram
    NME0_datagram = fid.read(1)

    #  and environment
    environment_datagram= fid.read(1)

    #  and MRU0
    MRU0_datagram = fid.read(1)

    #  then the first param datagram
    param_datagram = fid.read(1)

    #  and the first RAW3 datagram
    RAW3_datagram = fid.read(1)


elif (1):

    #  this is a CW file - EK60 on EK80
    filename = 'D:/Data/EK60 on EK80/D20180205-T233434.raw'
    fid =  RawSimradFile(filename, 'r')

    #  first datagram is a config datagram
    config_datagram_CW = fid.read(1)


    #  this is a CW file - EK60 on EK80
    filename = 'D:/Data/EK60 on EK80/D20180205-T233434.raw'
    fid =  RawSimradFile(filename, 'r')

    #  first datagram is a config datagram
    config_datagram_FM = fid.read(1)

    compare_dicts(config_datagram_CW, config_datagram_FM):


root = ET.fromstring(param_datagram)

if (root.tag.lower() == 'parameter'):

    for child in root:
        print(child.tag, child.attrib)

    for h in root.iter('Environment'):
        print(h.attrib)

    for cs in root.iter('ConfiguredSensors'):
        print(cs.attrib)

    for t in root.findall('ConfiguredSensors'):
        print(t[0].attrib)

#    for t in root.iter('Transceiver'):
#        print('')
#        print('T',t.attrib)
#        for c in t.iter('Channel'):
#            print('C',c.attrib)
#            for td in t.iter('Transducer'):
#                print('TD',td.attrib)
#                for t in root.iter('Transducers'):
#                    for c in t.iter('Transducer'):
#                        if (td.attrib['SerialNumber'] == c.attrib['TransducerSerialNumber']):
#                            print('TC',c.attrib)

    print('')

    for t in root.iter('Transducers'):
        for c in t.iter('Transducer'):
            print(c.attrib)


#    for t in root.findall('ConfiguredSensors'):
#        print(t[0].attrib)

print('end')


