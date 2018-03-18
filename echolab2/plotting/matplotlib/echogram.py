# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS IS."
#  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES, OFFICERS,
#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED, AS TO THE USEFULNESS
#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE. THEY ASSUME NO RESPONSIBILITY
#  (1) FOR THE USE OF THE SOFTWARE AND DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL
#  SUPPORT TO USERS.

"""


| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assesment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import numpy as np
from matplotlib import figure, axes
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap, Colormap


class echogram(object):
    '''
    The echogram class provides basic plotting functions to display
    echolab2 data objects using matplotlib.

    This code is quite fresh and needs testing and further development.

    '''

    def __init__(self, mpl_container, data_object, data_attribute=None,
            threshold=None, cmap=None):
        """

        """

        #  determine what matplotlib container we have - we must be passed
        #  a figure or axes or None. If we're passed a figure, we assume we're
        #  rendering to the "active" axes. If None, we create a figure.
        if (mpl_container is None):
            self.figure = figure()
            self.axes = self.figure.gca()
        elif (isinstance(mpl_container, figure.Figure)):
            self.figure = mpl_container
            self.axes = mpl_container.gca()
        elif (isinstance(mpl_container, axes._subplots.Subplot)):
            self.figure = None
            self.axes = mpl_container
        else:
            raise ValueError("You must pass either a matplotlib figure or " +
                    "subplot specifying where the echogram will be rendered.")

        #  store a reference to our raw_data or processed_data object
        self.data_object = data_object

        #  the data attribute is only required when plotting raw_data objects.
        #  if not provided we assume we're plotting a processed_data object
        #  whose data attribute is "data"
        if (data_attribute):
            if (not hasattr(self.data_object, data_attribute)):
                raise ValueError("The data_attribute : " + data_attribute +
                    " does not exist in the data_object provided.")
            else:
                data_attribute = getattr(self.data_object, data_attribute)
                self.data_attribute = data_attribute
        else:
            self.data_attribute = data_object.data

        #  store the display thresholds
        self.threshold = threshold

        #  set the default SIMRAD EK500 color table plus grey for NoData
        self._simrad_color_table = [(1,1,1),
                                    (0.6235,0.6235,0.6235),
                                    (0.3725,0.3725,0.3725),
                                    (0,0,1),
                                    (0,0,0.5),
                                    (0,0.7490,0),
                                    (0,0.5,0),
                                    (1,1,0),
                                    (1,0.5,0),
                                    (1,0,0.7490),
                                    (1,0,0),
                                    (0.6509,0.3255,0.2353),
                                    (0.4705,0.2353,0.1568)]
        self._simrad_cmap = LinearSegmentedColormap.from_list('Simrad',  self._simrad_color_table)
        self._simrad_cmap.set_bad(color='grey')

        if (cmap is None):
            self.cmap = self._simrad_cmap
        else:
            self.cmap = cmap
            self.cmap.set_bad(color='grey')

        #  determine the vertical axes attribute
        if (hasattr(self.data_object, 'range')):
            self.y_label_attribute = 'range'
        elif (hasattr(self.data_object, 'depth')):
            self.y_label_attribute = 'depth'
        else:
            #  neither range nor depth so we'll just plot sample number
            self.y_label_attribute = None

        self.update()


    def set_colormap(self, colormap, bad_data='grey', update=True):
        if (isinstance(colormap, str)):
            colormap = Colormap(colormap)
        self.cmap = colormap
        if (bad_data):
            self.cmap.set_bad(color=bad_data)
        if update:
            self.update()


    def set_threshold(self, threshold=[-70,-34], update=True):
        if (threshold):
            self.threshold = threshold
        else:
            self.threshold = None

        if update:
            self.update()

    def _adjust_xdata(self, x_data):
        """
        _adjust_xdata shifts the x axis data such that the values are centered
        on the sample pixel's x axis. When using the extents keyword with imshow
        the pixels are no longer centered on the underlying grid. This method

        """

        n_pings = x_data.shape[0]
        adj_x = np.empty(n_pings, dtype='float')
        mid = int((float(n_pings)/ 2.0) + 0.5)
        adj_x[0:mid] = x_data[0:mid] + ((np.arange(mid,
                dtype='float')[::-1] / mid) * 0.5)
        adj_x[mid:] = x_data[mid:] - ((np.arange(mid,
                dtype='float') / mid) * 0.5)

        return adj_x


    def plot_line(self, line_obj, color=None, linestyle=None,
            linewidth=None):
        """
        plot_line plots an echolab2 line object on the echogram.

        """

        if (color is None):
            color = line_obj.color
        if (linestyle is None):
            linestyle = line_obj.linestyle
        if (linewidth is None):
            linewidth = line_obj.linewidth

        #  check if the line's time vector matches our data
        if (not np.array_equal(line_obj.ping_time,
                self.data_object.ping_time)):
            #  it doesn't interp a copy of the provided line
            interp_line = line_obj.empty_like()
            interp_line.interpolate(self.data_object.ping_time)
            line_obj = interp_line

        #  generate a ping number vector for x axis indexing
        xticks = np.arange(line_obj.ping_time.shape[0], dtype=
                self.data_object.sample_dtype)
        xticks = self._adjust_xdata(xticks)

        #  DO WE NEED TO SHIFT IN Y????

        #  and plot
        self.axes.plot(xticks, line_obj.data, color=color,
            linestyle=linestyle, linewidth=linewidth,
            label=line_obj.name)


    def update(self):
        """

        """

        #  this is a custom tick formatter for datetime64 values as floats
        def format_datetime(x, pos=None):
            try:
                x = np.clip(int(x + 0.5), 0, self.data_object.ping_time.shape[0] - 1)
                dt = self.data_object.ping_time[x].astype('object')
                tick_label = dt.strftime("%H:%M:%S")
            except:
                tick_label = ''

            return tick_label


        #  get the thresholds if we have been given one
        if (self.threshold):
            threshold = self.threshold
        else:
            #  or just use the min/max if we don't have thresholds
            threshold = [np.nanmin(self.data_attribute),
                         np.nanmax(self.data_attribute)]

        #  transform the data so it looks right with imshow
        echogram_data = np.flipud(np.rot90(self.data_attribute,1))

        #  determine the vertical extent of the data and the y label
        if (self.y_label_attribute is None):
            #  we don't have a valid axis - just use sample number
            yticks = np.arange(echogram_data.shape[0])
            y_label = 'sample'
        elif (hasattr(self.data_object, self.y_label_attribute)):
            yticks = getattr(self.data_object, self.y_label_attribute)
            y_label = self.y_label_attribute + ' (m)'
        else:
            #  we don't have a valid axis - just use sample number
            yticks = np.arange(echogram_data.shape[0])
            y_label = 'sample'

        #  generate a ping number vector for x axis indexing
        n_pings = self.data_object.ping_time.shape[0]
        xticks = np.arange(n_pings, dtype='float')

        #  plot the sample data
        self.axes_image = self.axes.imshow(echogram_data, cmap=self.cmap,
                vmin=threshold[0], vmax=threshold[1], aspect='auto',
                interpolation='none', extent=[xticks[0],xticks[-1],
                yticks[-1],yticks[0]], origin='upper')

        #  set our custom x-axis formatter
        self.axes.xaxis.set_major_formatter(ticker.FuncFormatter(format_datetime))

        #  set the x axis label to the month-day-year of the first
        #  valid datetime64 we have in the data. This will fail if there
        #  are no valid times so we'll not label the axis if that happens
        try:
            x = self.axes.get_xticks()[0]
            x = np.clip(int(x + 0.5), 0, self.data_object.ping_time.shape[0] - 1)
            dt = self.data_object.ping_time[x].astype('object')
            x_label = dt.strftime("%m-%d-%Y")
        except:
            x_label = ''
        self.axes.set_xlabel(x_label)

        #  set the Y axis label
        self.axes.set_ylabel(y_label)

        #  TODO:  the grid should be optional and at some point we will have
        #         a method to plot an integration grid which would disable the
        #         mpl grid.

        #  apply the grid
        self.axes.grid(True,color='k')
