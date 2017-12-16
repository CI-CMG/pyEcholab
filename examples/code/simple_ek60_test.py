# -*- coding: utf-8 -*-
"""

"""

from echolab2.instruments import EK60


# Data file
#filename = "../data/DY1706_EK60-D20170609-T005736.raw"
filename = "C:/Users/rick.towler/Documents/PyEcholab2/examples/data/DY1706_EK60-D20170609-T005736.raw"
#filename = "//AKC0SS-N086/RACE_Users/rick.towler/My Documents/AFSCGit/pyEcholab2_CI-CMG/examples/data/DY1706_EK60-D20170609-T005736.raw"
#filename = "/home/vagrant/dev/data/W070827-T140039.raw"
start_time = '2007-08-27 14:00:00'
end_time='2007-08-27 14:21:57'
n_data_points = 3

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 and  data sources
ek60 = EK60.EK60()

#  use the read_raw method to read in a data file
ek60.read_raw(filename)

#  print some basic info about our object
print(ek60)


