# coding=utf-8

#    National Oceanic and Atmospheric Administration
#    Alaskan Fisheries Science Center
#    Resource Assessment and Conservation Engineering
#    Midwater Assessment and Conservation Engineering

# THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
# AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
# IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
# OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED, AS TO
# THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.  THEY
# ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND DOCUMENTATION;
# OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

'''
.. module:: echolab2.instruments.echosounder

    :synopsis:  The top level interface for reading data files collected
                using scientific echosunders commonly used in fisheries
                stock assessment and research.


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assesment and Conservation Engineering Group (MACE)
|
| Authors:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

$Id$
'''

import os
from . import EK80
from . import EK60


SIMRAD_EK60 = 0
SIMRAD_EK80 = 1


def read(files, **kwargs):

    # if we're given a string, wrap it in a list
    if not isinstance(files, list):
            files = [files]

    obj_map = []
    data_objs = []

    # Work through list
    for index, item in enumerate(files):
        filename = os.path.normpath(item)

        # Determine what kind of data file we have
        data_type = check_filetype(filename)

        if data_type in obj_map:
            data_object = data_objs[obj_map.index(data_type)]
        else:
            if data_type == SIMRAD_EK60:
                # This is the first EK60 file - create the EK60 object
                obj_map.append(data_type)
                data_object = EK60.EK60()
                data_objs.append(data_object)
            elif data_type == SIMRAD_EK80:
                # This is the first EK80 file - create the EK80 object
                obj_map.append(data_type)
                data_object = EK80.EK80()
                data_objs.append(data_object)
            else:
                # We don't know what this is
                raise UnknownFormatError("Unknown file type encountered: " + filename)

        # Read the data file using the object for this data type
        data_object.append_raw(filename, **kwargs)

    return data_objs


def check_filetype(filename):

    # Read in the file header, this value can change if additional
    # instruments are introduced with larger headers.
    fh = open(filename, "rb")
    header = fh.read(8)
    fh.close()

    # Return the file type based on the header
    if header[4:8]==b'CON0':
        # Simrad EK60 style raw files start with P <BS> <NUL> <NUL> C O N 0
        return SIMRAD_EK60

    elif header[4:8]==b'XML0':
        # Simrad EK80 style raw files start with <DLE> p <NUL> <NUL> X M L 0
        return SIMRAD_EK80

    else:
       return -1



class UnknownFormatError(Exception):
    pass
