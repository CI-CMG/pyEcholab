'''
read_ek80_datagrams.py

This script uses util.simrad_raw_file.RawSimradFile to read
data files written by the EK80 application and extract various
datagrams for you to explore.

The script shows you how to extract the datagrams. You can
extend as you see fit.

'''

from util.simrad_raw_file import RawSimradFile



def compare_dicts(a, b):

    for ak in a.keys():
        try:
            if (b[ak] != a[ak]):
                print(ak + ": a = " + str(a[ak]) + "    b = " + str(b[ak]))
        except:
            print("b does not contain key " + ak)




#  CW complex - full resolution (should be 32-bit samples)
#filename = 'C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw'

#  CW reduced (power/angle) - full resolution
#filename = 'C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004.raw'

#  CW extra reduced (power/angle) - downsampled
#filename = 'C:/EK80 Test Data/EK80/CW/further reduced/DY2000_EK80_Cal-D20200126-T062251.raw'

# CW EK60 on EK80 (power/angle)
filename = 'C:/EK80 Test Data/EK80/CW/further reduced/DY2000_EK80_Cal-D20200126-T062251.raw'

# FM EK80
#filename = 'C:/EK80 Test Data/EK80/FM/DY1802_EK80-D20180301-T185940.raw'



#  explore datagrams from various file types
if (1):

    #  open the file
    fid =  RawSimradFile(filename, 'r')

    #  first datagram is a config datagram
    config_datagram = fid.read(1)

    #  pick out the other initial datagrams
    filters = []
    nmea = []
    datagram = fid.read(1)
    while (datagram['type'] != 'RAW3'):
        if (datagram['type'] == 'FIL1'):
            filters.append(datagram)
        if (datagram['type'] == 'XML0'):
            if (datagram['subtype'] == 'parameter'):
                parameter_datagram = datagram
            if (datagram['subtype'] == 'environment'):
                environment_datagram = datagram
        if (datagram['type'] == 'NME0'):
            nmea.append(datagram)
        datagram = fid.read(1)

    #  grab one raw datagram
    raw_datagram = datagram

    #  print the contents
    print("CONFIG DATAGRAM\n")
    print(config_datagram)
    print("\n\nFILTER DATA\n")
    print(filters)
    print("\n\nNMEA\n")
    print(nmea)
    print("\n\nENVIRONMENT DATAGRAM\n")
    print(environment_datagram)
    print("\n\nPARAMETER DATAGRAM\n")
    print(parameter_datagram)
    print("\n\nRAW DATAGRAM\n")
    print(raw_datagram)


    fid.close()

#  display the first hundred datagram times and types
elif(1):

    #  open the file
    fid =  RawSimradFile(filename, 'r')

    for i in range(100):
        #  first datagram is a config datagram
        datagram = fid.read(1)

        if (datagram['type'] == 'XML0'):
            print(datagram['timestamp'], datagram['type'], datagram['subtype'])
        elif (datagram['type'] == 'NME0'):
            print(datagram['timestamp'], datagram['type'], datagram['nmea_type'])
        elif (datagram['type'].startswith('RAW')):
            if datagram['type'] == 'RAW0':
                print(datagram['timestamp'], datagram['type'], "channel:", datagram['channel'])
            else:
                print(datagram['timestamp'], datagram['type'], "channel:", datagram['channel_id'])
        else:
            print(datagram['timestamp'], datagram['type'])


    fid.close()


print('end')


