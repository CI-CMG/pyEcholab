# -*- coding: utf-8 -*-
"""Simple example showing the use of start/end time and ping
keyword arguments to ek80.read_raw()
"""

import numpy as np
from echolab2.instruments import EK80


raw_file = 'C:/EK Test Data/EK80/FM/FM_-_70_KHZ_2MS_CAL-Phase0-D20190531-T194722-0.raw'

start_time=np.datetime64('2019-05-31T19:48:35', 'ms')
end_time=np.datetime64('2019-05-31T19:55:00', 'ms')

start_ping = 250
end_ping = 259


print('Reading the raw file %s' % (raw_file))
ek80 = EK80.EK80()

# Read the whole file
ek80.read_raw(raw_file)
print(ek80)

# Read a time span
ek80.read_raw(raw_file, start_time=start_time, end_time=end_time)
print(ek80)

# Read a ping span
ek80.read_raw(raw_file, start_ping=start_ping, end_ping=end_ping)
print(ek80)



"""
Python 3.7.7 (tags/v3.7.7:d7c567b08f, Mar 10 2020, 10:41:24) [MSC v.1900 64 bit (AMD64)] on AKCSL2051-LN20, Standard
>>> Reading the raw file C:/EK80 Test Data/EK80/FM/FM_-_70_KHZ_2MS_CAL-Phase0-D20190531-T194722-0.raw
<class 'echolab2.instruments.EK80.EK80'> at 0x1fd58c1be48
    EK80 object contains data from 1 channel:
        EKA 240814-0F ES70-18CD :: complex-FM (500, 1270, 4)
    data start time: 2019-05-31T19:47:23.984
      data end time: 2019-05-31T19:57:35.329
    number of pings: 500

<class 'echolab2.instruments.EK80.EK80'> at 0x1fd58c1be48
    EK80 object contains data from 1 channel:
        EKA 240814-0F ES70-18CD :: complex-FM (315, 1270, 4)
    data start time: 2019-05-31T19:48:35.439
      data end time: 2019-05-31T19:54:59.349
    number of pings: 315

<class 'echolab2.instruments.EK80.EK80'> at 0x1ed2e28ed08
    EK80 object contains data from 1 channel:
        EKA 240814-0F ES70-18CD :: complex-FM (10, 1270, 4)
    data start time: 2019-05-31T19:53:40.119
      data end time: 2019-05-31T19:53:52.310
    number of pings: 10

"""
