# coding=utf-8

"""
Simple code to convert Echoview .csv export files to PyEcholab processed
data objects.
"""
import numpy as np
from echolab2.plotting.matplotlib.multifrequency_plotting import MultifrequencyPlot
from echolab2.processing.line import Line

# Make fake data to test plot colors.
def make_fake():
    fake_data = np.empty([2120, 2120], dtype=np.int)

    j = 1
    for i in range(39, 2120, 40):
        #     print(i, j)
        fake_data[i - 39:i + 1, :] = j
        j += 1

    return fake_data


# NOTE!! This is NOT the true MultifrequencyPlot class code!!!! This is just
# for testing plotting with imported .csv files created by
# Carrie!!!!!!!!!!!!!!!!!!!!!!!!!
class MultifrequencyData(object):

    def __init__(self, n_pings, n_samples):

        self.n_pings = -1
        self.n_samples = n_samples
        self.latitude = np.empty(n_pings, dtype=np.float)
        self.longitude = np.empty(n_pings, dtype=np.float)
        self.ping_time = np.empty(n_pings, dtype='datetime64[ms]')
        self.depth = np.empty(n_samples, dtype=np.float)
        self.data = np.empty((n_pings, n_samples), dtype=np.int)
        self.data_attributes = ['ping_time', 'depth']


    def append_ping(self, ping_data, column_index):

        def _get_time(ping_data):
            date = ping_data[column_index['Ping_date']].strip()
            time = ping_data[column_index['Ping_time']].strip()
            mils = float(ping_data[column_index['Ping_milliseconds']].strip())
            return np.datetime64('{0}T{1}.{2}'.format(date, time, int(mils)))

        self.n_pings += 1
        this_ping = self.n_pings
        self.ping_time[this_ping] = _get_time(ping_data)
        self.longitude[this_ping] = ping_data[column_index['Longitude']].strip()
        self.latitude[this_ping] = ping_data[column_index['Latitude']].strip()
        value_data = [int(float(value)) for value in ping_data[len(
            column_index):]]
        value_data = [value if value >= 0 else 2 for value in value_data]
        self.data[this_ping, :] = value_data

    def __str__(self):
        """
        Reimplemented string method that provides some basic info about the
        PlotData object
        """
        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the ProcessedData instance
        n_pings = len(self.ping_time)
        if n_pings > 0:
            msg = msg + "              sample count: {0}\n".\
                format(self.n_samples)

            msg = msg + "           number of pings: {0}\n" .\
                format(n_pings)
            msg = msg + "           data start time: {0}\n". \
                format(self.ping_time[0])
            msg = msg + "             data end time: {0}\n" \
                .format(str(self.ping_time[n_pings - 1]))
            if hasattr(self, 'data'):
                n_pings, n_samples = self.data.shape
                msg = msg + "   values array dimensions: ({0}, " \
                            "{1})\n".format(n_pings, n_samples)
                msg = msg + "values array unique values: {0}".format(
                    np.unique(self.data))
        else:
            msg = msg + "  ProcessedData object contains no data\n"

        return msg

def get_bottom(bottom_file):

    def _get_time(ping_data):
        date = ping_data[column_index['Ping_date']].strip()
        time = ping_data[column_index['Ping_time']].strip()
        mils = float(ping_data[column_index['Ping_milliseconds']].strip())
        return np.datetime64('{0}T{1}.{2}'.format(date, time, int(mils)))

    with open(bottom_file, 'r', encoding='utf-8-sig') as fid:
        first_line = True
        raw_bottom = fid.readlines()

        ping_count = len(raw_bottom) - 1

        bottom_pings = np.empty(ping_count, dtype='datetime64[ms]')
        bottom_data = np.empty(ping_count, dtype=np.float32)

        this_ping = -1
        for index, line in enumerate(raw_bottom):
            # The file's first line contains the column names for everything but
            # the data values. Create dictionary used as index in append ping
            # method of PlotData class
            if first_line:
                column_list = line.split(',')
                for position, item in enumerate(column_list):
                    column_index[item.strip()] = position
                first_line = False
            else:
                if this_ping <= ping_count:
                    this_ping = index - 1
                    ping_data = line.split(',')

                    bottom_pings[this_ping] = _get_time(ping_data)
                    bottom_data[this_ping] = float(ping_data[column_index[
                        'Depth']].strip())

    return bottom_data, bottom_pings


csv_file = 'data/SaKe2015-D20150626-T060353_to_SaKe2015-D20150626-T065817.csv'
bottom_file = csv_file.replace('data/', 'data/bottom_csv/')

logo = 'data/NOAA_logo_sm.png'



# populate PlotData instance with data from .csv file
with open(csv_file, 'r', encoding='utf-8-sig') as fid:
    first_line = True
    raw_data = fid.readlines()

    ping_count = len(raw_data)-1
    sample_count = int(raw_data[1].split(',')[12])

    data = MultifrequencyData(ping_count, sample_count)

    column_index = {}
    for line in raw_data:
        # The file's first line contains the column names for everything but
        # the data values. Create dictionary used as index in append ping
        # method of PlotData class
        if first_line:
            column_list = line.split(',')
            for position, item in enumerate(column_list):
                column_index[item.strip()] = position
            first_line = False

        else:
            ping_data = line.split(',')
            data.append_ping(ping_data, column_index)


# Replace 0 with 2 to make empty spots plot white.
data.data[data.data == 0] = 2

# Populate the depth values.
max_depth = int((ping_data[column_index['Depth_stop']].split('.')[0]))
for i in range(0, 1000):
    data.depth[i] = (max_depth / sample_count * i)

# Create a matching bottom Line object
bottom_values, bottom_times = get_bottom(bottom_file)
bottom = Line(ping_time=bottom_times, data=bottom_values, color=[0, 0, 0],
              name='Bottom', linewidth=2.0)

# Get the depth value for the bottom of the plot rtange (max bottom depth +
# 50 meters. Then get the number os samples above that value.
plot_bottom = max(bottom_values)+50
new_n_samples = np.where(data.depth <= plot_bottom)[0].shape[0]


# Create instance of MultifrequencyPlot
plot = MultifrequencyPlot(logo=logo)
print(logo)
# Get title from csv file name'
title = csv_file.split('/')[-1].split('.')[0].replace('_', ' ')


plot.plot(data, title=title, bottom=bottom, testing=True)


