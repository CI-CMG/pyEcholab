# -*- coding: utf-8 -*-
"""
ek80_write_test.py

This script can be used to test the writing of EK80 data to .raw files. It will
read in one or more .raw files, write them to disk, then read the re-written
file and compare the original to the re-written file.

A successful round trip will result in data that differs no more than...

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


one_file = ['C:/EK80 Test Data/Saildrone/SD_alaska_2019-Phase0-D20190516-T030157-0.raw']

#one_file = ['C:/EK80 Test Data/EK80/FM/DY1802_EK80-D20180301-T185940.raw']
#one_file = ['C:/EK80 Test Data/EK80/CW/complex/DY2000_EK80_Cal-D20200126-T060729.raw']


#  specify the output path AND file name header
out_file = 'C:/Temp_EK_Test/EK-Raw-Write-Test'

# Create an instance of the EK60 instrument. The EK60 class represents a
# collection of synchronous "ping" data, asynchronous data like GPS, motion,
# and annotation datagrams, and general attributes about this data.
ek80 = EK80.EK80()

# Use the read_raw method to read in our list of data files.
ek80.read_raw(one_file)

# Print some basic info about our object.
print(ek80)


out_files = ek80.write_raw(out_file, overwrite=True)



print()
