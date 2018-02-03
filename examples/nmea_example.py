# -*- coding: utf-8 -*-
"""

"""

import sys
from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram




rawfiles = ['./data/EK60/DY1706_EK60-D20170609-T005736.raw']

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 data sources
ek60 = EK60.EK60()

#  read our raw file
ek60.read_raw(rawfiles)

gga = ek60.nmea_data.get_datagrams('GGA')

print(ek60)
