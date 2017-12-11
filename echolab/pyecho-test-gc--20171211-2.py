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
pyechopath = "..\\..\\PyEcholab2-master\\echolab"
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
doTIMESPAN = True
doPINGSPAN =      True
doREADALL  = True

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
    ts = '2012-02-14 23:10:11.000'
    te = '2012-02-14 23:10:24.000'
    
    r = EK60Reader(start_time=ts, end_time=te)
    
    if not r: 
        print("r is EMPTY")
        
    r.raw_data
    for channel in r.raw_data:    
        print(r.raw_data[channel].frequency)
    
    for channel in r.raw_data:    
        print(r.raw_data[channel].ping_time)
    # RETURNS: Nothing
    
    

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

    if not r: 
        print("r is EMPTY")
    
    r.raw_data
    for channel in r.raw_data:
        print("Channel IDs [L111]")
    #    print(r.raw_data[channel])    # prints channel id
    #    print("Channel Frequencies [L113]")
    #    print(r.raw_data[channel].frequency)
   
    # RETURNS: Nothing
