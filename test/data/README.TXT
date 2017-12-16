
This directory contains test data files used in verifying pyEcholab's
operation.

There are two MATLAB scripts that were used to create the source data
for this test.

create_raw_test_file.m reads a portion of a raw file and writes it to
disk effectively shortening the file.

test_data.raw was created using this script.


create_test_data.m reads the test source file, converts power and angle
data using the calibration parameters contained within the raw file and
then writes these data to disk. The script is run once for each channel.
The test data file in this directory contained data from two channels
and two output files were created: 

echolab_data_38kHz.mat
echolab_data_120kHz.mat

The variables in the file are:

power
sv
sv_linear
sp
sp_linear
alongship
alongship_e
athwartship
athwartship_e
ping_number
range
frequency
raw_file (input file name)
cal_parms (readEKRaw calibration parameters structure)

These values can be read in Python using PyTables or h5py.


This directory also contains Echoview .ev files used to create the
integration test data along with the integration export files. Once this
code settles down I will document these files in detail here.