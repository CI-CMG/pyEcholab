# -*- coding: utf-8 -*-
"""
The .idx file that usually accompanies Simrad .raw files contains
the time, lat, lon, distance, ping # since software start, and
the offset into the raw file to the data for that ping.

Be aware that it is possible that the .raw file will have fewer
pings than the .idx file. The ER60 software would ocassionally
write sections of garbage to the .raw file but would continue to
operate normally and maintain a valid .idx file. Any ping while
this was happening will be in the .idx file but not in the raw
file.

While there are a number of features and optimizations that could
be enabled by using this data, pyEcholab currently only supports
reading and parsing of the files.

This example shows how to extract the first 10 IDX datagrams from
the specified .idx file.
"""

from echolab2.instruments.util.simrad_raw_file import RawSimradFile

in_files = 'C:/EK80 Test Data/2015833-D20150205-T000316.idx'

#in_files = 'C:/EK80 Test Data/DY2003_EK80-D20200303-T020359.idx'

fid = RawSimradFile(in_files, 'r')
config = fid.read(1)

for i in range(10):
    idx_datagram = fid.read(1)
    print(idx_datagram)

print()
