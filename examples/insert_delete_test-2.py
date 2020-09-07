# -*- coding: utf-8 -*-
"""insert_delete_test-2.py tests er, insertion and deletion of data. It generates
a simple synthetic processed_data object and deletes and inserts a few pings
and displays the data along the way.

It is primarily intended to test the ping_data/raw_data/processed_data classes.

"""

import numpy as np
from matplotlib.pyplot import figure, show
from echolab2.processing import processed_data
from echolab2.plotting.matplotlib import echogram


# Define some basic properties of the fake data
test_data_pings = 10
test_data_samples = 20
sample_thickness_m = 0.5
ping_interval_ms = 1000.0

# Create the processed_data object and set a couple of attributes
fake_Sv = processed_data.processed_data('Fake Data', 120000, 'Sv')
fake_Sv.n_samples = test_data_samples
fake_Sv.n_pings = test_data_pings

# Create some fake data arrays.
ranges = np.arange(test_data_samples) * sample_thickness_m
times = (np.arange(test_data_pings) * ping_interval_ms) + \
        np.datetime64('2018-03-21T03:30:30', 'ms').astype('float')
data = np.zeros((test_data_pings, test_data_samples), dtype='float32')

# Set every other sample in a row to a value that is easy distinguish
for i in range(0,test_data_pings,2):
    data[i, 1::2] = (i+1) * 2
    data[i+1, 2::2] = (i+2) * 2

# Add the fake data to the processed_data object.
fake_Sv.add_data_attribute('range', ranges)
fake_Sv.add_data_attribute('ping_time', times.astype('datetime64[ms]'))
fake_Sv.add_data_attribute('data', data)

# Plot the original data
fig_1 = figure()
eg = echogram.Echogram(fig_1, fake_Sv, threshold=[0, 21])
eg.axes.set_title("Original Test Data")

# Now delete pings 6 and 9 (index 5 and 8)
fake_Sv.delete(index_array=[4,8])

# and plot the data now, after deleting the two pings
fig_2 = figure()
eg = echogram.Echogram(fig_2, fake_Sv, threshold=[0, 21])
eg.axes.set_title("Ping 5 and 9 deleted")

# now insert 2 empty pings at index 3 and 8. We use empty_like
# to generate the empty pings we're going to insert. We set the
# force keyword of the insert method to disable frequency and
# channel ID checks since that is not needed when inserting
# empty data.
insert_idx = [3,8]
fake_Sv.insert(fake_Sv.empty_like(len(insert_idx)), force=True,
        index_array=insert_idx)

# Now plot up the echogram showing the newly inserted empty pings
fig_3 = figure()
eg = echogram.Echogram(fig_3, fake_Sv, threshold=[0, 21])
eg.axes.set_title("Ping 4 and 9 inserted")


# Display figure.
show()
