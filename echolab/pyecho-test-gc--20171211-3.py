# -*- coding: utf-8 -*-
"""
Test of pyEcholab

G Cutter 20171120
"""

#-------------------------------------------------------------
# Code and data directories
#-------------------------------------------------------------
import os
wd=os.getcwd()
print(os.getcwd())

# Coerce Local Working Directory
#pyechopath = "..\\..\\PyEcholab2-master\\echolab"
pyechopath = "C:\\pyEcholab\\dev\\PyEcholab2-master\\echolab"

os.chdir(pyechopath)
print(os.getcwd())

# Set path to data
datapath = "..\\test\\data\\"

#-------------------------------------------------------------
# Packages & imports
#-------------------------------------------------------------
import numpy as np
import sys
sys.path.insert(0, pyechopath)
import data_struct
from data_struct import EK60Reader
import raw_file
import parsers

#-------------------------------------------------------------
# Options
#-------------------------------------------------------------
doTIMESPAN = False
doPINGSPAN = True
doREADALL  = False
doPAMMES   = False

#-------------------------------------------------------------
# Checks
#-------------------------------------------------------------
npver = np.version.version
print( "numpy version = ", npver)

#-------------------------------------------------------------
# Data 
#-------------------------------------------------------------
#filename = str(datapath + "W070827-T140039.raw")
filename = str(datapath + "DY1201_EK60-D20120214-T231011.raw")

print("myfn = " + filename)

#-------------------------------------------------------------
# Processing 
#-------------------------------------------------------------
if(doREADALL):
    print("doREADALL")
    #-------------------------------------------------
    ## Read Raw File
    #------------------------------------------------- 
    r = EK60Reader()
    
    r.read_file(filename)
    
    if not r: 
        print("r is EMPTY")
        
    r.raw_data
    for channel in r.raw_data:
        print(r.raw_data[channel])  # prints channel id
        
        print(r.raw_data[channel].ping_time)
        
    # RETURNS: 
    #<data_struct.EK60RawData object at 0x000000000D385278>
    #<data_struct.EK60RawData object at 0x000000000D372940>
    #<data_struct.EK60RawData object at 0x000000000D372518>
    #<data_struct.EK60RawData object at 0x000000000D372748>
    #<data_struct.EK60RawData object at 0x000000000D372B70>


if(doTIMESPAN):
    print("doTIMESPAN")
    #-------------------------------------------------
    ## Read a file from start to end times (ts, te)
    #-------------------------------------------------
#    ts = '2012-02-14 23:10:11.000' # NO decimal seconds
#    te = '2012-02-14 23:10:24.000'
#    start_time = '2007-08-27 14:00:00' # Pamme's example timestring
#    end_time='2007-08-27 14:21:57'
    ts = '2012-02-14 23:10:11'
    te = '2012-02-14 23:10:24'
    
    r = EK60Reader(start_time=ts, end_time=te)
    
    r.read_file(filename)
        
    if not r: 
        print("r is EMPTY")
        
    r.raw_data
    for channel in r.raw_data:    
        print(r.raw_data[channel].frequency)
    
    for channel in r.raw_data:    
        print(r.raw_data[channel].ping_time)
    
    
    

if(doPINGSPAN):
    print("doPINGSPAN")
    #-------------------------------------------------
    ## Read a file from start to end times (ts, te)
    #-------------------------------------------------
    r = []
    
    pstart = 0 
    pend   = 5 #40
    
    # Does this work?
    r = EK60Reader(start_ping=pstart, end_ping=pend)

    r.read_file(filename)
    
    if not r: 
        print("r is EMPTY")
    
    r.raw_data
    for channel in r.raw_data:
        print("Channel IDs [L111]")
    #    print(r.raw_data[channel])    # prints channel id
    #    print("Channel Frequencies [L113]")
    #    print(r.raw_data[channel].frequency)
   

if(doPAMMES): 
    
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
