'''


'''
import sys
sys.path.append('C:/Users/rick.towler/Work/AFSCGit/pyEcholab')

from matplotlib.pyplot import figure, show
from echolab2.instruments import EK80
from echolab2.plotting.matplotlib import echogram

#  CW complex - full resolution (should be 32-bit samples)
#filename = 'C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw'

#  CW reduced (power/angle) - full resolution
#filename = 'C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004.raw'

#  CW extra reduced (power/angle) - downsampled
#filename = 'C:/EK80 Test Data/EK80/CW/further reduced/DY2000_EK80_Cal-D20200126-T062251.raw'

# CW EK60 on EK80 (power/angle)
#filename = 'C:/EK80 Test Data/EK80/CW/further reduced/DY2000_EK80_Cal-D20200126-T062251.raw'

# FM EK80
filename = 'C:/EK80 Test Data/EK80/FM/DY1802_EK80-D20180301-T185940.raw'

#filename = ['C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004.raw',
#            'C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw']

# Daildrone
#filename = 'C:/EK80 Test Data/Saildrone/SD_alaska_2019-Phase0-D20190516-T030157-0.raw'

ek80 = EK80.EK80()

# Use the read_raw method to read in a data file.
ek80.read_raw(filename)

# The EK80 class dispenses with the transceiver number from EK60
# data is keyed by channel ID. The channel_ids property contains the
# unique channel IDs from the data that was read.
print(ek80.channel_ids)



# The EK80 object stores the data from each of these channels in the
# raw_data attribute. This attribute is a dictionary keyed by channel ID.
# I know that with my test files the 2nd channel is the 38 kHz and I'll
# get the raw data for that channel.
raw_38 = ek80.raw_data[ek80.channel_ids[1]][0]


# For the same channel ID, EK80 data files can store various types of data
# (power, angle, power/angle, and complex) and to more efficiently store
# these data the raw_data class will only contain 1 data type. This means
# that if you read files that contain different data types for the same
# channel, there will be multiple raw_data objects in our list.

# print out the data types
for raw_data in raw_38:
    print(raw_data.datatype)

#  extract the first data type
raw_data = raw_38[0]

calibration = raw_data.get_calibration()

Sv = raw_data.get_Sv(calibration=calibration)

fig = figure()
eg = echogram.Echogram(fig, Sv, threshold=[-70,-34])
eg.axes.set_title("EK80 Sv")

# Show our figure.
show()

print(ek80)

pass
