# -*- coding: utf-8 -*-
"""
@author: rick.towler

This example script plots a single ping as power for every channel in the
specified raw file.

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from echolab2.instruments import EK60


# Specify the ping number to plot.
ping_number = 100

# Define the path to the data file.
raw_filename = "./data/EK60/DY1706_EK60-D20170609-T005736.raw"

# Create an instance of our EK60 object.
ek60 = EK60.EK60()

# Read in the .raw data file.
print('Reading raw file %s' % (raw_filename))
ek60.read_raw(raw_filename)

# Print some info about the state of our EK60 object.
print(ek60)

# Set up the colormap for plotting.
color = iter(cm.rainbow(np.linspace(0, 1, len(ek60.channel_ids))))

# Create a matplotlib figure to plot our echograms on.
fig = plt.figure(figsize=(7, 7))

# Get references.

# Plot power from the specified ping from all channels.
for channel_id in ek60.channel_ids:

    # If we're working with channel IDs we can bypass the get_channel_data
    # method and access the raw_data attribute directly.
    raw_data = ek60.raw_data[channel_id]

    # Get the first data object for this channel
    raw_data = raw_data[0]

    # Get a color for this channel.
    c = next(color)

    # Create a sample index so we can pass it as the Y axis in the figure so
    # we plot the data up and down.
    n_samples = len(raw_data.power[ping_number, :])
    yaxis = np.arange(n_samples)

    # Get a processed_data object that contains "calibrated" power
    # data. Since we call it without specifying the "calibration"
    # keyword it will use the parameters from the .raw file when
    # applying the calibration.
    power = raw_data.get_power()
    yaxis = np.arange(power.n_samples)

    # Plot power.
    plt.plot(power[ping_number, :], yaxis, color=c, label=channel_id)

# Label the figure and set other display properties.
plt.gca().invert_yaxis()
plt.ylabel('Sample')
plt.xlabel('Power')
title = 'Ping %i' % (ping_number)
fig.suptitle(title, fontsize=14)
plt.legend()

# Display plot.
plt.show()




