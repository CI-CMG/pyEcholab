# -*- coding: utf-8 -*-
"""echogram_plotting_test.py demonstrates plotting echograms using fake data.

It is primarily intended to test the processed_data and echogram classes and
as of now it shows a slight vertical shift in the samples. The matplotlib
echogram is close, but has some issues. It needs help.

"""

import numpy as np
from matplotlib.pyplot import figure, show
from echolab2.processing import processed_data, line
from echolab2.plotting.matplotlib import echogram


# Define some basic properties of the fake data
test_data_pings = 100
test_data_samples = 100
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

# Set every other row to 10.0
data[:, 1::2] = 10.0

# Add the fake data to the ProcessedData object.
fake_Sv.add_data_attribute('range', ranges)
fake_Sv.add_data_attribute('ping_time', times.astype('datetime64[ms]'))
fake_Sv.add_data_attribute('data', data)

# Create a horizontal line that we'll draw every 5 meters
# to create a simple grid.
a_line = line.line(ping_time=np.array([times[0], times[-1]]),
        data=np.array([0, 0]), thickness=2.0, color=[0,0,0])
n_lines = int((ranges[-1] / (sample_thickness_m * 10)) + 0.5)

# Create a matplotlib figure to plot our echograms on.
fig_1 = figure()
eg = echogram.Echogram(fig_1, fake_Sv, threshold=[0, 15])
eg.axes.set_title("Echogram Plot Test")

# Now draw the horizontal lines
for i in range(n_lines):
    eg.plot_line(a_line, linewidth=1.0)
    a_line = a_line + (sample_thickness_m * 10)

# Display figure.
show()
