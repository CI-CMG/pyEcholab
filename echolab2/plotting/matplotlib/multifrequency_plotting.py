# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     National Centers for Environmental Data (NCEI)
#     Centers for Coats, Oceans and Geophysics (CCOG)


# THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
# AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
# IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
# OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
# AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
# THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
# DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.
import os
import numpy as np
from textwrap import wrap
from datetime import timedelta, datetime
import matplotlib.pylab as plt
import matplotlib.dates as md
import matplotlib.patches as mpatches
from matplotlib.image import imread
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FuncFormatter
from echolab2.processing.ncei_multifrequency import MultifrequencyData


class MultifrequencyPlot(object):

    # Default color table for NCEI multifrequency plots (x, x, x) are RGB values
    # and the integer in the comment is the corresponding data value to be
    # mapped to that color.
    COLOR_TABLE = [(0.7333, 0.7333, 0.7333),  # 1
                   (1.0, 1.0, 1.0),  # 2
                   (0.0, 0.0, 1.0),  # 3
                   (0.502, 0.502, 1.0),  # 4
                   (1.0, 1.0, 1.0),  # 5
                   (1.0, 1.0, 1.0),  # 6
                   (1.0, 0.0, 0.0),  # 7
                   (1.0, 0.502, 0.502),  # 8
                   (1.0, 1.0, 1.0),  # 9
                   (0.8588, 0.1961, 0.8588),  # 10
                   (1.0, 0.3686, 1.0),  # 11
                   (1.0, 1.0, 1.0),  # 12
                   (1.0, 1.0, 0.0),  # 13
                   (1.0, 1.0, 0.502),  # 14
                   (1.0, 1.0, 1.0),  # 15
                   (0.0, 1.0, 0.0),  # 16
                   (0.502, 1.0, 0.502),  # 17
                   (1.0, 1.0, 1.0),  # 18
                   (1.0, 1.0, 1.0),  # 19
                   (1.0, 0.4706, 0.0),  # 20
                   (1.0, 0.6118, 0.2588),  # 21
                   (1.0, 1.0, 1.0),  # 22
                   (0.4902, 0.0, 0.4902),  # 23
                   (0.7176, 0.0, 0.7176),  # 24
                   (1.0, 1.0, 1.0),  # 25
                   (1.0, 1.0, 1.0),  # 25
                   (1.0, 1.0, 1.0),  # 27
                   (1.0, 1.0, 1.0),  # 28
                   (0.3176, 0.3176, 0.3176),  # 29
                   (0.4549, 0.4275, 0.4392),  # 30
                   (1.0, 1.0, 1.0),  # 31
                   (0.0, 0.0, 0.4157),  # 32
                   (0.0, 0.0, 0.5843),  # 33
                   (1.0, 1.0, 1.0),  # 34
                   (1.0, 1.0, 1.0),  # 35
                   (0.4745, 0.0, 0.0),  # 36
                   (0.7255, 0.0, 0.0),  # 37
                   (1.0, 1.0, 1.0),  # 38
                   (0.1765, 0.0, 0.1765),  # 39
                   (0.2902, 0.0, 0.2902),  # 40
                   (1.0, 1.0, 1.0),  # 41
                   (0.5922, 0.5922, 0.0),  # 42
                   (0.8078, 0.8078, 0.0),  # 43
                   (1.0, 1.0, 1.0),  # 44
                   (0.0, 0.2588, 0.0),  # 45
                   (0.0, 0.5412, 0.0),  # 46
                   (1.0, 1.0, 1.0),  # 47
                   (1.0, 1.0, 1.0),  # 48
                   (0.502, 0.251, 0.0),  # 49
                   (0.8431, 0.4196, 0.0),  # 50
                   (1.0, 1.0, 1.0),  # 51
                   (0.0, 0.902, 0.902),  # 52
                   (0.7255, 1.0, 1.0)]  # 53

    def __init__(self, output_dir=None, color_table=None, label_size=20,
                 font_family='serif', grid='x', tick_size=16, title_size=24,
                 logo=None):

        # Pass in font styling parameters
        self.label_size = label_size
        self.title_size = title_size
        self.family = font_family
        self.logo = logo

        # Create data object attribute. This is populated by plot method.
        self.data_object = None

        self.output_image_dir = None
        # Set output directory if provided.
        if output_dir:
            self.output_image_dir = output_dir

        # If a color table is provided normalize color table values to 0-1.
        # Otherwise use default color table.
        if color_table:
            color_table = self.color_convert(color_table)
        else:
            color_table = self.COLOR_TABLE

        # Create color map.
        self.cmap = ListedColormap(color_table)

        # # Create a matplotlib figure and aexes to plot.
        # self.fig, self.ax = plt.subplots(figsize=fig_size)
        self.fig = plt.figure(figsize=(18, 10), dpi=72)

        # self.ax = plt.gca()
        self.ax = plt.subplot(111)

    @staticmethod
    def color_convert(color_table):
        """ Create a matplotlib cmap from color_table)

        test whether the color table passed in is in 0-255 or 0-1 space. If in
        0-255 convert to 0-1.

        Args:
            color_table(list): a list of tuples representing color values.

        Returns:
            new_table(list): list of color tuples in 0-1 space.

        """
        new_table = []
        # Test if the color table passed in is in 0-254 or 0-1 color space.
        if max(max(color_table)) > 1:
            # We are in 0-255 space. divide each element by 255 to convert to 0-1
            # space.
            new_table = [(round(e[0] / 255, 4),
                          round(e[1] / 255, 4),
                          round(e[2] / 255, 4)) for e in color_table]
        else:
            new_table = color_table

        return new_table

    def plot(self, data_object, title=None, bottom=None,
             day_night=True, output=True, testing=False):

        self.data_object = data_object

        #  This is a custom tick formatter for datetime64 values as floats
        def format_datetime(x, pos=None):
            try:
                dt = x.astype('datetime64[ms]').astype('object')
                tick_label = dt.strftime("%H:%M")
            except:
                tick_label = ''

            return tick_label

        # Test if we are being passed a MultifrequencyData object, if not
        # return an error.
        if not testing:
            if not isinstance(data_object, MultifrequencyData):
                raise TypeError('MultifrequencyPlot only works with '
                                'MultifrequencyData objects')

        # Transform the data so it looks right with imshow.
        echogram_data = np.flipud(np.rot90(data_object.data, 1))

        # Determine the vertical extent of the data and the y label
        yticks = data_object.depth
        y_label = 'Depth (m)'

        # If bottom object is provided, set minimum y to 50 meters over max
        # depth and trim data to same depth extent for consistent plotting,
        # otherwise use full data extent.
        if bottom:
            max_depth = np.max(bottom.data) + 50
            max_index = np.argmax(self.data_object.depth > max_depth)
            echogram_data = echogram_data[:max_index, :]
        else:
            max_depth = yticks[-1]

        # The x ticks are the pings times as serial time.
        xticks = data_object.ping_time.astype('float')


        # Plot the sample data
        self.ax.imshow(echogram_data, cmap=self.cmap, aspect='auto',
                       extent=[xticks[0], xticks[-1], max_depth, yticks[0]],
                       origin='upper')

        # Set our custom x-axis formatter
        # self.ax.xaxis.set_major_formatter(FuncFormatter(format_datetime))
        self.ax.set_axis_off()

        # If title text is provided set title text to wrap is long and then
        # add title.
        if title:
            display_title = "\n".join(wrap(title, 50))
            self.ax.set_title(display_title, family=self.family,
                              size=self.title_size, weight='bold')

        # Plot logo image if a path to a logo image file was provided when
        # class instantiated.
        if self.logo:
            logo = imread(self.logo)
            height = logo.shape[1]
            width = logo.shape[0]
            x_pos = self.fig.bbox.xmax - width-20
            y_pos = self.fig.bbox.ymax - height-20
            self.fig.figimage(logo, x_pos, y_pos)

        # Add day/night bar ro plot. Also set zorder so the day/night bar
        # plots behind the ticks and grid lines.
        if day_night:
            self.get_suncycle_data()
            bar_axis = self.add_day_night_bar()
            # bar_z = bar_axis.get_zorder()
            # # self.ax.set_zorder(bar_z + 1.0)

        # There seems to be a bug in matplotlib where extra white space is
        # added to the figure around the echogram if other elements are
        # plotted on the echogram even if their data ranges fall *within* the
        # echogram. This doesn't happen when we use ping number as the x
        # axis but we don't want to use ping number becuase everything we
        # plot on the echogram would have to be mapped to ping number.
        # Weirdly what solves the issue is calling set_xlim/set_ylim without
        # arguments which should only return the current limits but seems to
        # fix this issue.
        # self.ax.set_xlim()
        # self.ax.set_ylim()

        # Add third axis on top
        tick_size = 16
        grid = 'x'
        print_x_ticks = data_object.ping_time.astype(
                                         'datetime64[ms]').astype('object')

        bounds = self.ax.get_position().bounds
        self.ax_3 = self.fig.add_axes([bounds[0], bounds[1], bounds[2], bounds[3]])
        self.ax_3.patch.set_visible(False)
        self.ax_3.set_xlim(print_x_ticks[0], print_x_ticks[-1])
        self.ax_3.set_ylim(max_depth, yticks[0])

        # Style the ticks.
        self.ax_3.tick_params('both', direction='in', length=5.0,
                              labelsize=tick_size)

        # Set major formatter for x (time) axis.
        xfmt = md.DateFormatter('%H:%M')
        self.ax_3.xaxis.set_major_formatter(xfmt)

        xlocator = md.MinuteLocator(byminute=[0, 10, 20, 30, 40, 50],
                                    interval=1)
        self.ax_3.xaxis.set_major_locator(xlocator)


        # Create the x axis labeel. If data are from same day, label lists
        # day-month-year, otherwise label has start and end date of data.
        try:
            s = self.ax.get_xticks()[0]
            e = self.ax.get_xticks()[1]
            ds = s.astype('datetime64[ms]').astype('datetime64[D]').astype(
                'object')
            de = e.astype('datetime64[ms]').astype('datetime64[D]').astype(
                'object')

            if ds != de:
                x_label = 'Time in UTC (hour:min)\n{} to {}'.format(
                            ds.strftime("%d-%b-%Y"), de.strftime("%d-%b-%Y"))
            else:
                x_label = 'Time in UTC (hour:min)\n{}'.format(ds.strftime(
                                                              "%d-%b-%Y"))
        except:
            x_label = ''

        # Set the axis labels.
        self.ax_3.set_xlabel(x_label, size=self.label_size, family=self.family)
        self.ax_3.set_ylabel(y_label,  size=self.label_size, family=self.family)

        # Apply grid to x axis
        # if grid:
        self.ax_3.grid(True, axis=grid, color='0.8')

        # Plot bottom line if provided.
        if bottom:
            self.plot_line(bottom, linewidth=3, color='black')

        # Export image if output=True.
        if output:
            file_name = title.replace(' ', '_')
            image_file_name = os.path.join(self.output_image_dir, file_name)
            self.save_image_file(image_file_name)

        plt.ion()
        plt.show()
        plt.pause(2)
        plt.close()

    def save_image_file(self, file_name):
        """Write image file."""
        if not os.path.exists(self.output_image_dir):
            os.makedirs(self.output_image_dir)

        self.fig.savefig(file_name)

    def plot_line(self, line_obj, color=None, linestyle=None,
                  linewidth=None):

        # self.data_object = line_obj
        """
        plot_line plots an echolab2 line object on the echogram.

        """

        if (color is None):
            color = line_obj.color
        if (linestyle is None):
            linestyle = line_obj.linestyle
        if (linewidth is None):
            linewidth = line_obj.linewidth

        #  get the line's horizontal axis (time) as a float
        xticks = line_obj.ping_time.astype('float')

        #  adjust the x locations so they are centered on the pings
        # xticks = self._adjust_xdata(xticks)

        #  adjust the y locations so they are
        # y_adj = self._adjust_ydata(line_obj.data)
        y_adj = line_obj.data

        #  and plot
        self.ax.plot(xticks, y_adj, color=color,
                       linestyle=linestyle, linewidth=linewidth,
                       label=line_obj.name)

    def _adjust_xdata(self, x_data):
        """
        _adjust_xdata shifts the x axis data such that the values are centered
        on the sample pixel's x axis. When using the extents keyword with imshow
        the pixels are no longer centered on the underlying grid. This method
        should be used to shift x axis values of data that is being plotted on
        top of an echogram.
        """

        #  determine the number of pings
        n_pings = x_data.shape[0]

        #  determine the 1/2 median ping interval
        ping_ints = np.ediff1d(self.data_object.ping_time.astype('float'))
        ping_int = np.nanmedian(ping_ints) / 2.0
        adj_x = np.empty(n_pings, dtype='float')

        mid = int((float(n_pings)/ 2.0) + 0.5)

        adj_x[0:mid] = x_data[0:mid] + ((np.arange(mid,
                                                   dtype='float')[::-1] / mid) * ping_int)
        adj_x[mid:] = x_data[mid:] - ((np.arange(mid,
                                                 dtype='float')[1::] / mid) *
                                      ping_int)

        return adj_x

    def _adjust_ydata(self, y_data):
        """
        _adjust_ydata shifts the y axis data such that the values are centered
        on the sample pixel's y axis. When using the extents keyword with imshow
        the pixels are no longer centered on the underlying grid. This method
        should be used to shift y axis values of data that is being plotted on
        top of an echogram.

        NOTE: I think this is correct, but I have not tested it fully.
        """

        #  determine the 1/2 sample thickness
        half_samp = self.data_object.sample_thickness / 2.0

        #  create the return array
        adj_y = np.empty(y_data.shape[0], dtype='float')

        #  get the y axis limits and the limits midpoint
        y_limits = self.axes.set_ylim()
        mid = (y_limits[0] - y_limits[1]) / 2.0

        #  set all values at the midpoint without change
        adj_y[y_data == mid] = y_data[y_data == mid]

        #  in the steps below, the signs are reversed from what you would
        #  think they should be. This is (I am assuming) because were
        #  reversing the Y axis when setting the extents to imshow.

        #  identify all values less than the midpoint and subtract
        #  1/2 sample thickness * 1 - % of midpoint
        adj_idx = y_data < mid
        adj_y[adj_idx] = y_data[adj_idx] + \
                         (1.0 - (y_data[adj_idx] / mid)) * half_samp
        #  identify all values greater than the midpoint and add
        #  1/2 sample thickness * % of full range
        adj_idx = y_data > mid
        adj_y[adj_idx] = y_data[adj_idx] - \
                         ((y_data[adj_idx] / y_limits[0])) * half_samp

        return adj_y

    def add_day_night_bar(self):

        # Set plot data.
        bar_height = 30
        n_pings = len(self.data_object.ping_time)
        plot_data = np.zeros((bar_height, n_pings, 3))
        daytime = self.data_object.daytime

        # Set the RGB values for each pixel.
        plot_data[:, daytime == 1] = [1, 1, 1]
        plot_data[:, daytime == 0] = [0.5, 0.5, 0.5]

        # # # Set axis ticks.
        # xticks = self.data_object.ping_time.astype('float')
        # yticks = self.data_object.depth

        # Get the bounds of current axes and set new axes to match lower left
        # corner and width  and set height to 0.3 of figure.
        bounds = self.ax.get_position().bounds

        ax_2 = self.fig.add_axes([bounds[0], bounds[1], bounds[2], 0.03])

        # Plot the day/night data and then turn off the axis so its ticks do
        # not plot.
        ax_2.imshow(plot_data, cmap='binary', aspect='auto',
                    interpolation='none')

        ax_2.set_axis_off()

        # Plot the legend
        self.add_day_night_legend()

        return ax_2

    def add_day_night_legend(self):
        white_patch = mpatches.Patch(color='white', label='Day')
        white_patch.set_edgecolor('black')
        black_patch = mpatches.Patch(color='grey', label='Night')
        black_patch.set_edgecolor('black')
        plt.legend(handles=[white_patch, black_patch], loc ='lower left',
                   bbox_to_anchor=(1, 0), frameon=False,
                   fontsize=self.label_size)

    def get_suncycle_data(self):
        """Returns the Time of SunRise, SunSet, Solar Altitude and Radiation."""

        self.data_object.daytime = np.empty((len(self.data_object.ping_time)))

        # Calculate sun
        for idx in range(len(self.data_object.ping_time)):
            self.data_object.daytime[idx] = self.suncycle(
                                                self.data_object.latitude[idx],
                                                self.data_object.longitude[idx],
                                                self.data_object.ping_time[idx])

        ##FIXME talk to Carrie about this.
        # hour=np.dot((self.data_object.ping_time % 1),24)
        # day=np.logical_xor(min(self.data_object.sun,[],2) < np.logical_and(hour,hour) < max(self.data_object.sun,[],2),self.data_object.sun(np.arange(),1) > self.data_object.sun(np.arange(),2))
        # self.data_object.day = day

        # try:
        #    data=plotEchoviewCSV_NEW(data,numfreq,Folders.ExportFolder)
        # finally:
        #    pass

    def suncycle(self, lat, lon, sun_date):

        n = np.int(24 * 3600 / 30)

        lon = lon - np.dot(360, np.floor((lon + 180) / 360))

        # Get time since the beginning of the year in days.
        time = (sun_date.astype('datetime64[D]') - sun_date.astype(
            'datetime64[Y]')).astype(int)
        fraction_of_day = ((sun_date.astype('datetime64[s]') - sun_date.astype(
            'datetime64[D]')) / np.timedelta64(1, 'D'))
        time += fraction_of_day
        time = np.array([[time]])

        # print("sun_date", sun_date)-
        # print("time", time)
        # m = 1
        # dt=1 /n
        # time = time + np.dot(dt, np.arange(0,n)).reshape(1,-1) - lon / 360

        # time = np.array([[176.325]])
        dec, jd, azm, rad = self.soradna(lat, lon, time,
                                         sun_date.astype('datetime64[Y]'))
        # NOTE azm is off by a bit at the beginning, dec is okay, jd is okay, rad is okay
        # print("rad", rad)
        if np.abs(rad) <= 1e-10:
            daytime = 0
        else:
            daytime = 1

        return daytime

        # SunRise/SunSet
        # rs = np.dot(np.nan,np.ones((m,2)))
        # zz=np.abs(rad) <= 1e-10
        # sz=sum(zz[:, 0])
        # ok=np.array([np.logical_and((0 < sz),(sz < n))], ndmin=1)
        ##FIXME It looks like this can only be a 1x1 array but the following code suggests that it could be bigger.
        # print("321 rs", rs)
        # if any(ok):
        #    nn=sum(ok)
        #    #ok=find(ok)
        #    ok = ok.astype(int)
        #    rs[ok,1]=sum(np.cumprod(zz[ok,:],1),2)
        #    rs[ok,2]=n - sum(np.cumprod(zz[ok,n:- 1:1],2),2) + 1
        #    rs[ok,:]=min(max(rs[ok,:],1),n)
        #    rs[ok,:]=time[ok[:,np.concatenate(1,1)] + np.dot((rs[ok,:] - 1),m)]
        #    rs[ok,:]=np.dot(24,(rs[ok,:] - np.floor(rs[ok,:])))
        #    rs[ok,:]=rs[ok,:] + np.dot(np.array(24 * dt, ndmin=2) / 2,(np.dot(ones(nn,1),np.array(1,- 1))))
        #
        # ok=(sz == n)
        # ok = np.array([ok]).reshape(-1,1)
        #
        # if any(ok):
        #    nn=np.array(sum(ok),dtype=int)
        #    ok = ok.astype(int)
        #    #rs[ok[0,0],:]=(np.dot(np.ones((nn[0],1)), np.array([24,0], ndmin=2)))
        #
        # ok=(sz == 0)
        # ok = np.array([ok]).reshape(-1,1)
        #
        # if any(ok):
        #    nn=sum(ok)
        #    ok = ok.astype(int)
        #    rs[ok,:]=(np.dot(np.ones((nn[0],1)),np.array([0, 24])))

        # return rs, time, dec, azm, alt, rad
        # return zz[:,0]

    def soradna(self, lat, lon, jd, y):
        """ SOradNA  computes no-sky solar radiation and solar altitude.

        [dec,azm,AlT,rad] = SOradNA1(lat,lon,day,Year)

        computes instantaneous values of solar declination, radiation and altitude
        from Position, yearday and Year.

        Assumes yd is either a column or row vector, the other input variables are
        scalars, OR yd is a scalar, the other inputs matrices.

        It is put together from expressions taken from Appendix E in the
        1978 edition of Almanac for Computers, Nautical Almanac Office, U.S.
        Naval Observatory. They are reduced accuracy expressions valid for the
        years 1800-2100. Solar declination computed from these expressions is
        accurate to at least 1'.

        The solar constant (1368.0 W/m^2) represents a mean of satellite measurements
        made over the last sunspot cycle (1979-1995)  taken from
        Coffey et al (1995), Earth System Monitor, 6, 6-10.
        """

        sc = 1368.0

        d2r = np.pi / 180

        m, n = np.asarray(jd).shape
        y = y.astype(
            'O').toordinal() - 1  # the number of days from January 0, 0000 gregorian
        jd = np.asanyarray(jd + y).reshape(-1, 1)  # returns arr of floats

        i = 0
        jul_date = jd
        jd = np.zeros([n, 6])
        for jd_rec in jul_date[:, 0]:
            # FIXME occassional one second differences as compared to matlab output
            jd[i, 0:6] = list((datetime.fromordinal(1) + timedelta(
                float(jd_rec))).timetuple())[0:6]
            i += 1

        # compute Universal Time in hours
        UT = jd[:, 3] + jd[:, 4] / 60 + jd[:, 5] / 3600

        # compute Julian ephemeris date in days (Day 1 is 1 Jan 4713 B.C.=-4712 Jan 1)

        # jd=np.dot(367,jd[:,1]) - np.fix(np.dot(7,(jd[:,1] + np.fix((jd[:,2] + 9) / 12))) / 4) + np.fix(np.dot(275,jd[:,2]) / 9) + jd[:,3] + 1721013 + UT / 24
        jd = np.dot(367, jd[:, 0]) - np.fix(
            np.dot(7, (jd[:, 0] + np.fix((jd[:, 1] + 9) / 12))) / 4) + np.fix(
            np.dot(275, jd[:, 1]) / 9) + jd[:, 2] + 1721013 + UT / 24

        # compute interval in Julian centuries since 1900
        jd = (jd - 2415020) / 36525

        # compute mean anomaly of the sun
        g = 358.475833 + np.dot(35999.04975, jd) - np.dot(0.00015, jd ** 2)

        # compute mean longitude of sun
        l = 279.696678 + np.dot(36000.76892, jd) + np.dot(0.000303, jd ** 2)

        # compute mean anomaly of Jupiter: 225.444651 + 2880 * jd + 154.906654 * jd;
        jp = 225.444651 + np.dot(3034.906654, jd)

        # compute mean anomaly of Venus
        vn = 212.603219 + np.dot(58517.803875, jd) + np.dot(0.001286, jd ** 2)

        # compute longitude of the ascending node of the moon's orbit
        nm = 259.183275 - np.dot(1934.142008, jd) + np.dot(0.002078, jd ** 2)
        g = np.dot((g - np.dot(360, np.fix(g / 360))), d2r)
        l = np.dot((l - np.dot(360, np.fix(l / 360))), d2r)
        jp = np.dot((jp - np.dot(360, np.fix(jp / 360))), d2r)
        vn = np.dot((vn - np.dot(360, np.fix(vn / 360))), d2r)
        nm = np.dot((nm - np.dot(360, np.fix(nm / 360)) + 360), d2r)

        # compute sun theta (THETA)
        dec = np.dot(+ 0.39793, np.sin(l)) - np.dot(4e-05, np.cos(l)) + np.dot(
            0.009999, np.sin(g - l)) + np.dot(0.003334, np.sin(g + l)) + np.dot(
            4.2e-05, np.sin(np.dot(2, g) + l)) - np.dot(1.4e-05, np.sin(
            np.dot(2, g) - l)) - np.multiply(np.dot(3e-05, jd),
                                             np.sin(g - l)) - np.multiply(
            np.dot(1e-05, jd), np.sin(g + l)) - np.multiply(
            np.dot(0.000208, jd), np.sin(l)) - np.dot(3.9e-05,
                                                      np.sin(nm - l)) - np.dot(
            1e-05, np.cos(g - l - jp))

        # compute sun rho
        rho = 1.000421 - np.dot(0.033503, np.cos(g)) - np.dot(0.00014, np.cos(
            np.dot(2, g))) + np.multiply(np.dot(8.4e-05, jd),
                                         np.cos(g)) - np.dot(3.3e-05, np.sin(
            g - jp)) + np.dot(2.7e-05, np.sin(np.dot(2, g) - np.dot(2, vn)))
        ### rho = 1 - 0.0335*np.sin( 2 * pi * (DayOfYear - 94)/365 )

        # compute declination: dec = np.anp.sin( THETA ./ np.sqrt(rho) );
        dec = dec / np.sqrt(rho)
        # compute equation of time (in seconds of time)

        jd = 276.697 + np.dot((np.dot(0.98564734, 36525)), jd)

        jd = np.dot((jd - np.dot(360, np.fix(jd / 360))), d2r)
        jd = np.dot(- 97.8, np.sin(jd)) - np.dot(431.3, np.cos(jd)) + np.dot(
            596.6, np.sin(np.dot(2, jd))) - np.dot(1.9, np.cos(
            np.dot(2, jd))) + np.dot(4.0, np.sin(np.dot(3, jd))) + np.dot(19.3,
                                                                          np.cos(
                                                                              np.dot(
                                                                                  3,
                                                                                  jd))) - np.dot(
            12.7, np.sin(np.dot(4, jd)))
        jd = jd / 3600
        # compute local hour angle (lHA)
        jd = jd + UT - 12
        jd = np.dot(15, jd) + lon
        jd = np.dot(jd, d2r)
        lat = np.dot(lat, d2r)
        # FIXME see smop core.py copy
        azm = np.copy(jd)

        # compute radius vector: RV = np.sqrt(rho);

        # compute solar altitude: np.sin(AlT) = np.sin(lat)*np.sin(dec) + ...
        #                                    np.cos(lat)*np.cos(dec)*np.cos(lHA)

        jd = np.dot(np.sin(lat), dec) + np.multiply(
            np.dot(np.cos(lat), np.sqrt(1 - dec ** 2)), np.cos(jd))
        # compute solar radiation outside atmosphere

        rad = np.multiply(np.multiply((sc / rho), jd), (jd > 0))

        dec = np.arcsin(dec)
        jd = np.arcsin(jd)
        int_ = np.floor(azm / np.pi) % 2

        azm = np.arctan(np.sin(azm) / (
                    np.multiply(np.sin(lat), np.cos(azm)) - np.multiply(
                np.cos(lat), np.tan(dec))))
        dec = dec / d2r
        azm = azm / d2r
        jd = jd / d2r
        azm = azm + np.dot(180, (1 - int_)) + np.dot(180, (azm < 0))

        dec = dec.reshape(-1, 1)
        azm = azm.reshape(-1, 1)
        jd = jd.reshape(-1, 1)
        rad = rad.reshape(-1, 1)

        return dec, jd, azm, rad