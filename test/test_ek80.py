'''


'''
import sys
sys.path.append('C:/Users/rick.towler/Work/AFSCGit/pyEcholab')

from echolab2.instruments import EK80

#  CW complex - full resolution (should be 32-bit samples)
#filename = 'C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw'

#  CW reduced (power/angle) - full resolution
#filename = 'C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004.raw'

#  CW extra reduced (power/angle) - downsampled
#filename = 'C:/EK80 Test Data/EK80/CW/further reduced/DY2000_EK80_Cal-D20200126-T062251.raw'

# CW EK60 on EK80 (power/angle)
#filename = 'C:/EK80 Test Data/EK80/CW/further reduced/DY2000_EK80_Cal-D20200126-T062251.raw'

# FM EK80
#filename = 'C:/EK80 Test Data/EK80/FM/DY1802_EK80-D20180301-T185940.raw'

filename = ['C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004.raw',
            'C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw']

ek80 = EK80.EK80()

# Use the read_raw method to read in a data file.
ek80.read_raw(filename)

print(ek80)

pass
