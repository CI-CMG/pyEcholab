# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS."  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""

| Developed by:  Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assessment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler   <rick.towler@noaa.gov>
| Maintained by:
|       Rick Towler   <rick.towler@noaa.gov>

"""

import numpy as np
from matplotlib import figure, axes
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap, Colormap


class Echogram(object):
    """This class generates echogram plots.

    The Echogram class provides basic plotting functions to display
    echolab2 data objects using matplotlib.

    In matplotlib there are 3 methods for displaying 2d bitmap data: imshow,
    pcolor, and pcolormesh.  For echograms of any size, imshow is the only
    option.  The one downside of imshow is that when the extents are specified
    by the user, the pixels no longer are centered on the underlying grid.
    Instead (taking the x axis as an example), the left edge of the left most
    column defines the start of the grid and the right edge of the right most
    column defines the end of the grid. This is not that noticeable until you
    plot data on top of the echogram.  Data plotted on the echogram is shifted
    1/2 "ping" left on the left most extent, is matched correctly in the
    center of the echogram, and is shifted 1/2 ping right on the right most
    extent.  This seems like a small amount, but things like bottom detection
    lines definitely do not line up correctly.

    As a result, the axes values of data being plotted on the echogram need
    to be adjusted to align with the underlying data.  Currently this is being
    done for the X axis, but not yet for the Y axis.  This issue needs to be
    examined further.

    Attributes:
        figure: A figure for displaying echogram plots.
        axes: An axis of the plot.
        data_object: A PingData or ProcessedData object.
        data_attribute: An attribute of the PingData object.
        threshold: Plot upper and lower display thresholds.
        _simrad_color_table: A list of tuples based on the default SIMRAD
            EK500 color table, plus grey for no data.
        _simrad_cmap: Defines a simrad colormap for the plot.
        cmap (str or Colormap instance):  A string or Colormap instance for
            the plot.
        y_label_attribute: A string of the vertical axis attribute.  Either
            "range" or "depth".
    """

    def __init__(self, mpl_container, data_object, data_attribute=None,
                 threshold=None, cmap=None):
        """Initializes the Echogram class.

        Args:
            mpl_container: A figure or axis (or None if creating a figure
                from scratch).
            data_object (object): A PingData or ProcessedData object.
            data_attribute (str): An attribute of the PingData object.
            threshold (list): lower and upper thresholds.
            cmap (str or Colormap instance):  A colormap for the plot.

        Raises:
            ValueError: a figure or subplot wasn't passed in.
        """

        # Determine what matplotlib container we have.  We must be passed
        # a figure or axes or None.  If we're passed a figure, we assume we're
        # rendering to the "active" axes.  If passed None, we create a figure.
        if mpl_container is None:
            self.figure = figure()
            self.axes = self.figure.gca()
        elif isinstance(mpl_container, figure.Figure):
            self.figure = mpl_container
            self.axes = mpl_container.gca()
        elif isinstance(mpl_container, axes._subplots.Subplot):
            self.figure = None
            self.axes = mpl_container
        else:
            raise ValueError("You must pass either a matplotlib figure or " +
                             "subplot specifying where the echogram will be "
                             "rendered.")

        # Store a reference to our ping_data or ProcessedData object.
        self.data_object = data_object

        # The data attribute is only required when plotting ping_data objects.
        # If not provided, we assume we're plotting a processed_data object
        # whose data attribute is "data".
        if data_attribute:
            if not hasattr(self.data_object, data_attribute):
                raise ValueError("The data_attribute : " + data_attribute +
                                 "does not exist in the data_object provided.")
            else:
                data_attribute = getattr(self.data_object, data_attribute)
                self.data_attribute = data_attribute
        else:
            self.data_attribute = data_object.data

        # Store the display thresholds.
        self.threshold = threshold

        # Set the default SIMRAD EK500 color table plus grey for NoData.
        self._simrad_color_table = [(1, 1, 1),
                                    (0.6235, 0.6235, 0.6235),
                                    (0.3725, 0.3725, 0.3725),
                                    (0, 0, 1),
                                    (0, 0, 0.5),
                                    (0, 0.7490, 0),
                                    (0, 0.5, 0),
                                    (1, 1, 0),
                                    (1, 0.5, 0),
                                    (1, 0, 0.7490),
                                    (1, 0, 0),
                                    (0.6509, 0.3255, 0.2353),
                                    (0.4705, 0.2353, 0.1568)]
        self._simrad_cmap = (LinearSegmentedColormap.from_list
                             ('Simrad', self._simrad_color_table))
        self._simrad_cmap.set_bad(color='grey')

        if cmap is None:
            self.cmap = self._simrad_cmap
        else:
            if type(cmap) is str:
                self.cmap = plt.get_cmap(cmap)
            else:
                self.cmap = cmap
        self.cmap.set_bad(color='grey')

        # Determine the vertical axis attribute.
        if hasattr(self.data_object, 'range'):
            self.y_label_attribute = 'range'
        elif hasattr(self.data_object, 'depth'):
            self.y_label_attribute = 'depth'
        else:
            # It's neither range nor depth so we'll just plot sample number.
            self.y_label_attribute = None

        self.update()


    def set_colormap(self, colormap, bad_data='grey', update=True):
        """Sets a colormap.

        Args:
            colormap (str): A color scheme for plotting.
            bad_data (str): The color to use for bad data values.  Needs to
                be a matplotlib color name.
            update (bool): Set to True to update the plot.
        """

        if isinstance(colormap, str):
            colormap = Colormap(colormap)
        self.cmap = colormap
        if bad_data:
            self.cmap.set_bad(color=bad_data)
        if update:
            self.update()


    def set_threshold(self, threshold=[-70,-34], update=True):
        """Sets a upper and lower threshold.

        Args:
            threshold (list): A two element list of upper and lower thresholds.
            update (bool): Set to True to update the plot.
        """

        if threshold:
            self.threshold = threshold
        else:
            self.threshold = None

        if update:
            self.update()



    def _adjust_xdata(self, x_data):
        """Shifts x axis data when displaying data with imshow.

        This method shifts the x axis data such that the values are centered
        on the sample pixel's x axis. When using the extents keyword with
        imshow, the pixels are no longer centered on the underlying grid.
        This method should be used to shift x axis values of data that is
        being plotted on top of an echogram.

        Args:
            x_data (array): A numpy array of x axis data to be shifted.

        Returns:
            An array, adj_x, of shifted data.
        """

        # Determine the number of pings.
        n_pings = x_data.shape[0]

        # Determine the 1/2 median ping interval.
        ping_ints = np.ediff1d(self.data_object.ping_time.astype('float'))
        ping_int = np.nanmedian(ping_ints) / 2.0

        adj_x = np.empty(n_pings, dtype='float')
        mid = int((float(n_pings)/ 2.0) + 0.5)
        adj_x[0:mid] = x_data[0:mid] + ((np.arange(
            mid, dtype='float')[::-1] / mid) * ping_int)
        adj_x[mid:] = x_data[mid:] - ((np.arange(
            n_pings-mid, dtype='float') / mid) * ping_int)

        return adj_x


    def add_colorbar(self, fig, units='dB'):
        """
        add_colorbar adds a colorbar on the right side of the echogram in the provided
        figure.
        """
        cb = fig.colorbar(self.axes_image)
        cb.set_label(units)


    def _adjust_ydata(self, y_data):
        """Shifts y axis data when displaying data with imshow.

        This method shifts the y axis data such that the values are centered
        on the sample pixel's y axis.  When using the extents keyword with
        imshow the pixels are no longer centered on the underlying grid.
        This method should be used to shift y axis values of data that is
        being plotted on top of an echogram.

        NOTE: I think this is correct, but I have not tested it fully.

        Args:
            y_data (array): A numpy array of y axis data to be shifted.

        Returns:
            An array, adj_y, of shifted data.
        """

        # Determine the 1/2 sample thickness.
        half_samp = self.data_object.sample_thickness / 2.0

        # Create the return array.
        adj_y = np.empty(y_data.shape[0], dtype='float')

        # Get the y axis limits and the limits midpoint.
        y_limits = self.axes.set_ylim()
        mid = (y_limits[0] - y_limits[1]) / 2.0

        # Set all values at the midpoint without change.
        adj_y[y_data == mid] = y_data[y_data == mid]

        # In the steps below, the signs are reversed from what you would think
        # they should be. This is (I am assuming) because were reversing the
        # Y axis when setting the extents to imshow.

        # Identify all values less than the midpoint and subtract 1/2 sample
        # thickness * 1 - % of midpoint.
        adj_idx = y_data < mid
        adj_y[adj_idx] = y_data[adj_idx] + \
                (1.0 - (y_data[adj_idx] / mid)) * half_samp
        # Identify all values greater than the midpoint and add 1/2 sample
        # thickness * % of full range.
        adj_idx = y_data > mid
        adj_y[adj_idx] = y_data[adj_idx] - \
                (y_data[adj_idx] / y_limits[0]) * half_samp

        return adj_y


    def plot_line(self, line_obj, color=None, linestyle=None, linewidth=None):
        """Plots an echolab2 Line object on the echogram.

        Args:
            line_obj (Line obj.): An instance of a PyEcholab Line object.
            color (list): Defines the colors of the plot lines.
            linestyle (str): Defines the style of the plot lines.
            linewidth (float): Defines the width of the plot lines.
        """

        if color is None:
            color = line_obj.color
        if linestyle is None:
            linestyle = line_obj.linestyle
        if linewidth is None:
            linewidth = line_obj.linewidth

        # Get the line's horizontal axis (time) as a float.
        xticks = line_obj.ping_time.astype('float')

        # Adjust the x locations so they are centered on the pings.
        xticks = self._adjust_xdata(xticks)

        # Adjust the y locations.
        y_adj = self._adjust_ydata(line_obj.data)
        y_adj = line_obj.data

        # Plot the data.
        self.axes.plot(xticks, y_adj, color=color, linestyle=linestyle,
                       linewidth=linewidth, label=line_obj.name)


    def update(self):
        """Updates the plot."""

        # This is a custom tick formatter for datetime64 values as floats.
        def format_datetime(x, pos=None):
            try:
                dt = x.astype('datetime64[ms]').astype('object')
                tick_label = dt.strftime("%H:%M:%S")
            except:
                tick_label = ''

            return tick_label

        # Get the thresholds if we have been given one.
        if self.threshold:
            threshold = self.threshold
        else:
            # Just use the min/max if we don't have thresholds.
            threshold = [np.nanmin(self.data_attribute),
                         np.nanmax(self.data_attribute)]

        # Transform the data so it looks right with imshow.
        echogram_data = np.flipud(np.rot90(self.data_attribute, 1))

        # Determine the vertical extent of the data and the y label.
        if self.y_label_attribute is None:
            # We don't have a valid axis.  Just use sample number.
            yticks = np.arange(echogram_data.shape[0])
            y_label = 'sample'
        elif hasattr(self.data_object, self.y_label_attribute):
            yticks = getattr(self.data_object, self.y_label_attribute)
            y_label = self.y_label_attribute + ' (m)'
        else:
            # We don't have a valid axis.  Just use sample number.
            yticks = np.arange(echogram_data.shape[0])
            y_label = 'sample'

        # The x ticks are the pings times as serial time.
        xticks = self.data_object.ping_time.astype('float')

        # Plot the sample data.
        self.axes_image = self.axes.imshow(
            echogram_data, cmap=self.cmap, vmin=threshold[0], vmax=threshold[
                1], aspect='auto', interpolation='none', extent=[
                xticks[0], xticks[-1], yticks[-1], yticks[0]], origin='upper')

        # Set our custom x-axis formatter.
        self.axes.xaxis.set_major_formatter(ticker.FuncFormatter(
            format_datetime))

        # Set the x axis label to the month-day-year of the first.
        # datetime64 we have in the data. This will fail if there are no
        # valid times so we'll not label the axis if that happens.
        try:
            x = self.axes.get_xticks()[0]
            dt = x.astype('datetime64[ms]').astype('object')

            x_label = dt.strftime("%m-%d-%Y")
        except:
            x_label = ''
        self.axes.set_xlabel(x_label)

        # Set the Y axis label.
        self.axes.set_ylabel(y_label)

        #  TODO:  the grid should be optional and at some point we will have
        #         a method to plot an integration grid which would disable the
        #         mpl grid.

        # Apply the grid.
        self.axes.grid(True, color='k')

        # There seems to be a bug in matplotlib where extra white space is
        # added to the figure around the echogram if other elements are
        # plotted on the echogram even if their data ranges fall *within* the
        # echogram.  This doesn't happen when we use ping number as the x axis,
        # but we don't want to use ping number because everything we plot on
        # the echogram would have to be mapped to ping number.  Weirdly, what
        # solves the issue is calling set_xlim/set_ylim without arguments
        # which should only return the current limits, but seems to fix this
        # issue.
        self.axes.set_xlim()
        self.axes.set_ylim()

