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
filename = "..\\test\\data\\W070827-T140039.raw"

# Processing 
d = EK60Reader().read_file(filename)
data_objects = EK60Reader().read_file(filename)
channel = 1
for key, value in vars(data_objects[channel]).items():
    print(key,value)

