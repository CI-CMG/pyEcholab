# -*- coding: utf-8 -*-
"""
ek80_write_test.py

This script can be used to test the writing of EK80 data to .raw files. It will
read in one or more .raw files, write them to disk, then read the re-written
file and compare the original to the re-written file.

While significant effort was made to ensure the write_raw method creates sane files,
pyEcholab gives you a lot of flexibility when working with raw data and you can
quickly run into issues when combining data from different sources or modifying
data and writing the results.
"""

from echolab2.instruments import EK80
from echolab2.processing import processed_data



# EK80 CW Complex 3 sectors
in_files = ['C:/EK80 Test Data/Saildrone/SD_alaska_2019-Phase0-D20190516-T030157-0.raw']
ev_csv_filename = 'C:/EK80 Test Data/Saildrone/SD_alaska_2019-Phase0-D20190516-T030157-0-38kHz.angles.csv'

# EK80 FM
#in_files = ['C:/EK80 Test Data/EK80/FM/FM_-_70_KHZ_2MS_CAL-Phase0-D20190531-T194722-0.raw']

# EK80 CW 4 sectors
#in_files = ['C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw']
#ev_csv_filename = 'C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729-18kHz.angles.csv'

ek80 = EK80.EK80()
ek80.read_raw(in_files)
print(ek80)

channels = list(ek80.raw_data.keys())
raw_data = ek80.raw_data[channels[0]][0]

angles_along, angles_athwart = raw_data.get_physical_angles()

ev_angles_along, ev_angles_athwart = processed_data.read_ev_csv(channels[0],
        raw_data.frequency[0], ev_csv_filename, data_type='angles')

print(angles_along[0,20:40]-ev_angles_along[0,20:40])
print(angles_athwart[0,20:40]-ev_angles_athwart[0,20:40])


print()
