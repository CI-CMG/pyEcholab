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
from matplotlib.colors import LinearSegmentedColormap, Colormap


class echogram(object):
    '''
    The echogram class provides basic plotting functions to display
    echolab2 data objects using matplotlib.

    This code is quite fresh and

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


    def plot_line(self, line_obj, color=None, linestyle=None,
            linewidth=None):

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

        #  get the line's horizontal axis (time) as a float
        x_vals = line_obj.ping_time.astype('float')

        #  the echogram pixes are not centered on the grid so
        #  we need to shift them by 1/2 the ping interval in X
        half_ping_int = np.ediff1d(x_vals) / 2.0
        x_vals[0:-1] = x_vals[0:-1] + half_ping_int

        #  DO WE NEED TO SHIFT IN Y????

        #  and plot
        self.axes.plot(x_vals, line_obj.data, color=color,
            linestyle=linestyle, linewidth=linewidth,
            label=line_obj.name)


    def update(self):

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

        #  and get the horizontal axis (time) as a float
        time_axis = True
        xticks = self.data_object.ping_time.astype('float')

        #  check to make sure the values are sane - when NaT values are
        #  in our data we cannot easily plot using a time based axis so
        #  we'll switch to a sample based axis - numpy 1.14 has "isnat"
        if (np.any(xticks < 0)):
            #  there are some NaT's in there
            xticks = np.arange(self.data_object.ping_time.shape[0])
            time_axis = False

        #  plot the sample data
        self.axes_image = self.axes.imshow(echogram_data, cmap=self.cmap,
                vmin=threshold[0], vmax=threshold[1], aspect='auto',
                interpolation='none', extent=[xticks[0],xticks[-1],
                yticks[-1],yticks[0]], origin='upper')

        #  if we're plotting on a time axis, set the tick labels
        if (time_axis):
            #  get the tick locations as datetime64 objects
            x_tic_locs = self.axes.get_xticks().astype('datetime64[ms]')

            #  convert those to Python datetime objects
            x_tic_locs = x_tic_locs.astype('object')

            #  generate the list of tick label strings and get the date label
            #  while we're at it - we have to wrap
            ticklabels = [i.strftime("%H:%M:%S") for i in x_tic_locs]

            #  set the x axis ticklabels and label
            self.axes.set_xticklabels(ticklabels)
            self.axes.set_xlabel(x_tic_locs[0].strftime("%m-%d-%Y"))
        else:
            #  not a time axis, just set the xlabel
            self.axes.set_xlabel('ping number')

        #  set the Y axis label
        self.axes.set_ylabel(y_label)

        #  TODO:  the grid should be optional and at some point we will have
        #         a method to plot an integration grid which would disable the
        #         mpl grid.

        #  apply the grid
        self.axes.grid(True,color='k')
