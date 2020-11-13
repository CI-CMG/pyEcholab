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

'''
chan_data['angle_sensitivity_athwartship']=999.999
chan_data['sa_correction']=np.array([1.,2,3,4,5])
chan_data['beam_width_alongship']=789.123
chan_data['impedance']=12345
'''

# EK80 CW Complex
#in_files = ['C:/EK80 Test Data/Saildrone/SD_alaska_2019-Phase0-D20190516-T030157-0.raw']

# EK80 FM
in_files = ['C:/EK80 Test Data/EK80/FM/FM_-_70_KHZ_2MS_CAL-Phase0-D20190531-T194722-0.raw']



#  specify the output path AND file name header
out_file = 'C:/Temp_EK_Test/EK-Raw-Write-Test'

# Create an instance of the EK60 instrument. The EK60 class represents a
# collection of synchronous "ping" data, asynchronous data like GPS, motion,
# and annotation datagrams, and general attributes about this data.
ek80 = EK80.EK80()

# Use the read_raw method to read in our list of data files.
ek80.read_raw(in_files)

# Print some basic info about our object.
print(ek80)

channels = list(ek80.raw_data.keys())
raw_data = ek80.raw_data[channels[0]][0]
raw_data.resize(raw_data.n_pings, raw_data.n_samples + 50)

power = raw_data.get_power()

out_files = ek80.write_raw(out_file, overwrite=True, strip_padding=False)

print(out_files)

print()
