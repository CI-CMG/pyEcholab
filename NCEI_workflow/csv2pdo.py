# coding=utf-8

"""
Simple code to convert Echoview .csv export files to PyEcholab processed
data objects.
"""
import numpy as np
from matplotlib.pyplot import figure, show, subplots_adjust
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

from echolab2.plotting.matplotlib import echogram
from echolab2.sample_data import sample_data


class PlotData(sample_data):
    def __init__(self,):
        super(PlotData, self).__init__()

        # Change sample data type to int8 for these values
        self.sample_dtype = 'int8'

        # Create attributes for class
        self.sample_count = None
        self.latitude = None
        self.longitude = None
        self.depth_start = None
        self.depth_stop = None
        self.range_start = None
        self.range_stop = None
        self.values = None

    def append_ping(self, ping_data, column_index):

        def _get_time(ping_data):
            date = ping_data[column_index['Ping_date']].strip()
            time = ping_data[column_index['Ping_time']].strip()
            mils = float(ping_data[column_index['Ping_milliseconds']].strip())
            return np.datetime64('{0}T{1}.{2}'.format(date, time, int(mils)))

        self.n_pings += 1
        this_ping = self.n_pings

        self.ping_time[this_ping] = _get_time(ping_data)
        self.ping_number[this_ping] = ping_data[column_index['Ping_index']]
        self.sample_count[this_ping] = ping_data[column_index['Sample_count']]
        self.latitude[this_ping] = ping_data[column_index['Latitude']]
        self.longitude[this_ping] = ping_data[column_index['Longitude']]
        self.depth_start[this_ping] = float(ping_data[column_index[
            'Depth_start']])
        self.depth_stop = float(ping_data[column_index['Depth_stop']])
        self.range_start = float(ping_data[column_index['Range_start']])
        self.range_stop = float(ping_data[column_index['Range_stop']])

        value_data = [int(float(value)) for value in ping_data[len(
            column_index):]]
        value_data = [value if value >= 0 else -99 for value in value_data]
        self.values[this_ping, :] = value_data

    def create_arrays(self, n_pings, n_samples, initialize=True):
        """
        create_arrays is a method that initializes the data
        arrays.
        """
        #  first, create uninitialized arrays
        self.n_samples = n_samples
        self.ping_time = np.empty(n_pings, dtype='datetime64[s]')
        self.ping_number = np.empty(n_pings, np.int32)
        self.sample_count = np.empty(n_pings, np.uint32)
        self.latitude= np.empty(n_pings, np.float32)
        self.longitude = np.empty(n_pings, np.float32)
        self.depth_start = np.empty(n_pings, np.float32)
        self.depth_stop = np.empty(n_pings, np.float32)
        self.range_start = np.empty(n_pings, np.float32)
        self.range_stop = np.empty(n_pings, np.float32)
        self.values = np.empty((n_pings, n_samples), dtype=self.sample_dtype,
                              order='C')

        #  check if we should initialize them
        if initialize:
            self.ping_time.fill(np.datetime64('1970'))
            self.ping_number.fill(0)
            self.sample_count.fill(0)
            self.latitude.fill(np.nan)
            self.longitude.fill(np.nan)
            self.depth_start.fill(0)
            self.depth_stop.fill(0)
            self.range_start.fill(0)
            self.range_stop.fill(0)
            self.values.fill(np.nan)

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
                format(self.sample_count[0])
            msg = msg + "           longitude range: {0} - {1}\n".\
                format(np.min(self.longitude), np.max(self.longitude))
            msg = msg + "            latitude range: {0} - {1}\n".\
                format(np.min(self.latitude), np.max(self.latitude))
            msg = msg + "               depth range: {0} - {1}\n".\
                format(np.min(self.depth_start), np.max(self.depth_stop))
            msg = msg + "               range range: {0} - {1}\n". \
                format(np.min(self.range_start), np.max(self.range_stop))
            msg = msg + "           data start time: {0}\n".\
                format(self.ping_time[0])
            msg = msg + "             data end time: {0}\n"\
                .format(self.ping_time[n_pings-1])
            msg = msg + "           number of pings: {0}\n" .\
                format(n_pings)
            if hasattr(self, 'values'):
                n_pings, n_samples = self.values.shape
                msg = msg + "   values array dimensions: ({0}, " \
                            "{1})\n".format(n_pings, n_samples)
                msg = msg + "values array unique values: {0}".format(
                    np.unique(self.values))
        else:
            msg = msg + "  ProcessedData object contains no data\n"

        return msg


csv_file = 'data/SaKe2015-D20150626-T060353_to_SaKe2015-D20150626-T065817.csv'

data = PlotData()

# populate PlotData instance with data from .csv file
with open(csv_file, 'r', encoding='utf-8-sig') as fid:
    first_line = True
    raw_data = fid.readlines()
    ping_count = len(raw_data)-1
    sample_count = int(raw_data[1].split(',')[12])

    data.create_arrays(ping_count, sample_count)

    column_index = {}
    for line in raw_data:
        # the file's first line contains the column names for everything but
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

print(data)

# Create custom colormap for plotting
color_table = [(187, 187, 187),
               (255, 255, 255),  
               (000, 0, 255),               
               (128, 128, 255),
               (255, 255, 255),
               (255, 255, 255),
               (255, 0, 0),
               (255, 128, 128),        
               (255, 255, 255),
               (219, 50, 219), 
               (255, 94, 255),         
               (255, 255, 255),
               (255, 255, 0),
               (255, 255, 128), 
               (255, 255, 255), 
               (000, 255, 0),
               (128, 255, 128),
               (255, 255, 255),
               (255, 255, 255),
               (255, 120, 0),  
               (255, 156, 66),            
               (255, 255, 255),
               (125, 0, 125),
               (183, 0, 183),
               (255, 255, 255),
               (255, 255, 255),
               (255, 255, 255),
               (255, 255, 255),
               (81, 81, 81),
               (116, 109, 112),
               (255, 255, 255),
               (0, 0, 106),
               (0, 0, 149),
               (255, 255, 255),
               (255, 255, 255),
               (121, 0, 0),
               (185, 0, 0),
               (255, 255, 255),
               (45, 0, 45),
               (74, 0, 74),
               (255, 255, 255),
               (151, 151, 0),
               (206, 206, 0),
               (255, 255, 255),
               (0, 66, 0),
               (0, 138, 0),
               (255, 255, 255),
               (255, 255, 255),
               (128, 64, 0),
               (215, 107, 0),
               (255, 255, 255),
               (0, 230, 230),
               (185, 255, 255)]

# matplot lib uses 0-1 instead of 0-255 for color values so convert
mat_table = []
for value in color_table:
    new_value = (round(value[0]/255, 4), round(value[1]/255, 4),
                 round(value[2]/255, 4))
    mat_table.append(new_value)

n_colors = len(mat_table)
print(n_colors)
cmap = LinearSegmentedColormap.from_list('Carrie', mat_table, n_colors)
cmap.set_bad(color='green')


#  create a matplotlib figure to plot our echograms on
fig = figure()
#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None,
                hspace=None)

ax_1 = fig.add_subplot(3,1,1)
#  create an echogram to plot up the raw sample data
echogram_2 = echogram.echogram(ax_1, data, 'values', cmap=cmap)

ax_1.set_title(csv_file.split('/')[-1][:-4])

show()
