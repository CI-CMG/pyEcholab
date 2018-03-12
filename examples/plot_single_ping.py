# -*- coding: utf-8 -*-
"""
@author: rick.towler

This example plots a single ping as power for every channel in the specified raw file

NOTE! This example is reaching into the EK60RawData objects directly to pull out power.
This is only because we have not written the get_power method. If should be altered once
the get_power method is written.


"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from echolab2.instruments import EK60


#  specify the ping number to plot
ping_number = 100

#  define the path to the data file
raw_filename = "./data/EK60/DY1706_EK60-D20170609-T005736.raw"

#create an instance of our EK60 object
ek60 = EK60.EK60()

#  read in the .raw data file
print('Reading raw file %s' % (raw_filename))
ek60.read_raw(raw_filename)

#  print some info about the state of our EK60 object
print(ek60)

#  set up the colormap for plotting
color = iter(cm.rainbow(np.linspace(0, 1, len(ek60.channel_ids))))

#  create a figure
fig = plt.figure(figsize=(7,7))

#  plot power from the specified ping from all channels
for channel_id in ek60.channel_ids:

    #  get a reference to the raw_data for this channel
    raw_data = ek60.get_raw_data(channel_id=channel_id)

    #  get a color for this channel
    c = next(color)

    #  create a sample index so we can pass it as the Y axis in the figure
    #  so we plot the data up and down
    n_samples = len(raw_data.power[ping_number,:])
    yaxis = np.arange(n_samples)

    #  plot power
    plt.plot(raw_data.power[ping_number,:], yaxis, color=c, label=channel_id)

#  fancy up the figure
plt.gca().invert_yaxis()
plt.ylabel('Sample')
plt.xlabel('Power')
title = 'Ping %i' % (ping_number)
fig.suptitle(title, fontsize=14)
plt.legend()

#  and show
plt.show()




