
"""

"""

# Packages
import os
from pyecholab.instruments import EK60





# Data file
#filename = "../data/DY1706_EK60-D20170609-T005736.raw"
#filename = "C:/Users/rick.towler/Documents/PyEcholab2/examples/data/DY1706_EK60-D20170609-T005736.raw"
filename = "//AKC0SS-N086/RACE_Users/rick.towler/My Documents/AFSCGit/pyEcholab2_CI-CMG/examples/data/DY1706_EK60-D20170609-T005736.raw"
#filename = "/home/vagrant/dev/data/W070827-T140039.raw"
start_time = '2007-08-27 14:00:00'
end_time='2007-08-27 14:21:57'
n_data_points = 3

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 and  data sources
ek60 = EK60.EK60()

ek60.read_raw(filename)


#print("r.raw_data", r.raw_data)
#for channel_id in r.raw_data:
#    print()
#    print("Channel_id", channel_id)
#    print("r.raw_data[channel_id]", r.raw_data[channel_id])
#    print("min ping time", min( r.raw_data[channel_id].ping_time))
#    print("max ping time", max( r.raw_data[channel_id].ping_time))
#    for attribute in r.raw_data[channel_id].__dict__.keys():
#        data = getattr(r.raw_data[channel_id], attribute)
#        if isinstance(data, list) or isinstance(data, np.ndarray):
#            print(attribute, data[0:n_data_points])
#        else:
#            print(attribute, data)
#
