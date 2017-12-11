#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Test of pyEcholab
G Cutter 20171120
"""

# Packages
import numpy as np
# file from local archive ../PyEcholab2-master/echolab/data_struct
from data_struct import EK60Reader


# Options

# Checks
npver = np.version.version
print( "numpy version = ", npver)

# Data file
#filename = "..\\test\\data\\W070827-T140039.raw"
filename = "/home/vagrant/dev/data/W070827-T140039.raw"
start_time = '2007-08-27 14:00:00'
end_time='2007-08-27 14:21:57'
n_data_points = 3


# Processing 
r = EK60Reader(start_time=start_time, end_time=end_time)
r.read_file(filename)
print("r.raw_data", r.raw_data)
for channel_id in r.raw_data:
    print()
    print("Channel_id", channel_id)
    print("r.raw_data[channel_id]", r.raw_data[channel_id])
    print("min ping time", min( r.raw_data[channel_id].ping_time)) 
    print("max ping time", max( r.raw_data[channel_id].ping_time))
    for attribute in r.raw_data[channel_id].__dict__.keys():
        data = getattr(r.raw_data[channel_id], attribute)
        if isinstance(data, list) or isinstance(data, np.ndarray):
            print(attribute, data[0:n_data_points])
        else:
            print(attribute, data)



