# -*- coding: utf-8 -*-
"""An example of using insert and delete methods on data objects.

This example script demonstrates manipulating the raw_data and ProcessedData
objects using the insert and delete methods. The primary purpose of this
example is to verify basic operation of the insert and delete methods,
but it also provides some simple and somewhat contrived examples of using
index arrays with these methods.

Note that the echogram class doesn't always handle ping times that are NaT
very well so the X axis doesn't always get labeled properly in this example.
"""

import numpy as np
from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


# Read in some data from files.
rawfiles = ['./data/EK60/DY1201_EK60-D20120214-T231011.raw']
ek60 = EK60.EK60()
ek60.read_raw(rawfiles)

# Get a reference to the raw_data object.
raw_data_38 = ek60.get_raw_data(channel_number=2)
print(raw_data_38)

# Insert synthetic data.  Create data where each ping is a constant value and
# the values change significantly from ping to ping so it is easy to
# distinguish the pings and verify (or not) that data is in the right place.
fake_data = np.arange(20) * 9.0 - 150.0
j = 0
for i in range(raw_data_38.n_pings):
    raw_data_38.power[i, :] = fake_data[j]
    j += 1
    if j == fake_data.shape[0]:
        j = 0

# Create a figure.
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None,
                hspace=0.5)

# Plot the synthetic power data.
ax = fig.add_subplot(3,1,1)
eg = echogram.echogram(ax, raw_data_38, data_attribute='power')
ax.set_title("Synthetic power - 136 pings")

# Now resize the data - "new" pings will be filled with existing data.
raw_data_38.resize(raw_data_38.n_pings+24, raw_data_38.n_samples)
print(raw_data_38)

# Plot the re-sized data.
ax2 = fig.add_subplot(3,1,2)
eg = echogram.echogram(ax2, raw_data_38, data_attribute='power')
ax2.set_title("Synthetic power resized to 160 pings (notice data is "
              "replicated)")


# Now insert empty data.  First create an index array containing the indices
# where we will insert the data.
insert_idx = np.array([20, 21, 22, 23, 40, 41, 42, 43, 60, 61, 62, 63, 80, 81,
                       82, 83, 100, 101, 102, 103, 120, 121, 122, 123])
# Insert the data.  Notice that if we call insert with the "object to insert"
# argument set to None, it will automagically insert "empty" data.
raw_data_38.insert(None, index_array=insert_idx)

# Plot the power with empty data.
ax3 = fig.add_subplot(3,1,3)
eg = echogram.echogram(ax3, raw_data_38, data_attribute='power')
ax3.set_title("Synthetic power resized to 160 pings with empty data inserted")

# Display the results.
show()


# Now convert this data to Sv in both ping order and time order and plot to
# show how "empty" pings will be moved to the beginning when data is
# displayed in time order.  If you need to avoid this, you must explicitly set
# appropriate pings times for your empty pings.

#Create a figure.
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None, hspace=0.5)

# Get the data in ping order and plot.
Sv = raw_data_38.get_Sv(time_order=False)
ax = fig.add_subplot(2,1,1)
eg = echogram.echogram(ax, Sv)
ax.set_title('Sythetic power converted to Sv shown in ping order.')

# Get the Sv data in time order and plot it.
Sv = raw_data_38.get_Sv()
ax = fig.add_subplot(2,1,2)
eg = echogram.echogram(ax, Sv)
ax.set_title('Sythetic power converted to Sv shown in time order.')

# Display the results.
show()


# Now delete the empty pings we inserted.
delete_idx = np.arange(raw_data_38.n_pings)[raw_data_38.ping_time ==
                                            np.datetime64('NaT')]
raw_data_38.delete(index_array=delete_idx)

# Create a matplotlib figure to plot our echograms on.
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.90, wspace=None,
                hspace=0.5)

# Plot the synthetic power data.
ax = fig.add_subplot(2,1,1)
eg = echogram.echogram(ax, raw_data_38, data_attribute='power')
ax.set_title("Synthetic power after delete - should be 136 pings")

# Get the Sv data in time order and plot it.
Sv = raw_data_38.get_Sv()
ax = fig.add_subplot(2,1,2)
eg = echogram.echogram(ax, Sv)
ax.set_title('Sythetic power after delete converted to Sv shown in time order.')

# Display the results.
show()

pass
