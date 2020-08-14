# -*- coding: utf-8 -*-
"""
"""
import numpy as np
from echolab2.instruments import EK60




# The descriptions below apply to reading these 2 files in the following order.
rawfiles = ['C:/Users/rick.towler/Work/AFSCGit/pyEcholab/examples/data/EK60/DY1201_EK60-D20120214-T231011.raw',
            'C:/Users/rick.towler/Work/AFSCGit/pyEcholab/examples/data/EK60/DY1706_EK60-D20170609-T005736.raw']


# Create an instance of the EK60 instrument. This is the top level object used
# to interact with EK60 and  data sources.
ek60 = EK60.EK60()

# Use the read_raw method to read in our list of data files. Assuming the
# data files haven't been changed above, the these files contain data from a
# 5 frequency EK60 system: 18, 38, 70, 120, and 200 kHz.
ek60.read_raw(rawfiles)

# Print some basic info about our object. As you will see, 10 channels are
# reported.  Each file has 5 channels, and are in fact, physically the same
# hardware.  The reason 10 channels are reported is because the transceiver
# installation order was changed in the ER60 software which changes the
# channel ID for that transceiver + transducer combination.
print(ek60)


ek60.write_raw('C:/temp/EK-Raw-Write-Test')

print()
