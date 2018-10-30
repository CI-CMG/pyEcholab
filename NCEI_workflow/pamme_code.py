#!/usr/bin/ev python
# coding=utf-8

"""
Simple code to convert Echoview .csv export file to PyEcholab processed
data objects.
"""

import os
import ast
import time
import numpy as np
import matplotlib.image as mpimg
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from datetime import timedelta, datetime
from matplotlib.cbook import get_sample_data
from configparser import ConfigParser
from matplotlib.pyplot import figure, show, subplots_adjust
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

from NCEI_workflow.csv2pdo_echogram_image import PlotData
from NCEI_workflow.csv2pdo_echogram_image import
from NCEI_workflow.utils.timer import timethis
from echolab2.plotting.matplotlib.echogram import echogram


class EchogramImage(object):
    def __init__(self, input_file=None, output_image_dir=None,
                 y_label='Depth (m)'):
        config_file = 'echogram_image.conf'
        self.config = ConfigParser()
        self.config.read(config_file)
        self.color_table = ast.literal_eval(
            self.config.get('plotting', 'color_table'))
        self.file_data = None
        self.bottom_file_data = None
        self.data.sun = None
        self.echogram_figure = None
        self.multiply = None
        self.cmap = None
        self.input_file = input_file
        self.figure = None
        self.ax_1 = None
        self.y_label = y_label
        self.logo_file = 'NCEI_workflow/NOAA_logo_sm.png'
        if input_file is not None:
            bottom_data_dir = self.config.get('default', 'bottom_data_dir')
            self.bottom_input_file = os.path.dirname(
                input_file) + '/' + bottom_data_dir + '/' + os.path.basename(
                input_file)
            print("self.bottom_input_file", self.bottom_input_file)

        if input_file is None:
            if self.config.get('debug', 'debug'):
                self.input_file = self.config.get('default', 'test_file')
                self.bottom_input_file = self.config.get('default',
                                                         'bottom_test_file')
            else:
                raise SystemExit('No input_file specified.')

        if output_image_dir is None:
            if self.config.get('default', 'output_image_dir'):
                self.output_image_dir = self.config.get('default',
                                                        'output_image_dir')
            else:
                raise SystemExit('No output_image_dir specified.')

        self.output_image_file = self.output_image_dir + '/' + \
                                 os.path.basename(self.input_file).split('.')[0]

    @timethis
    def process_echoview_csv(self):
        """Read file data into data object.
        Process data.
        Plot data.
        """
        print(self.input_file)
        self.file_data = self.read_file(self.input_file)
        self.generate_data()
        self.plot_echoviewcsv_new()

    def read_file(self, filename):
        """Read file data."""
        file_data = None

        with open(filename, 'r', encoding='utf-8-sig') as fid:
            first_line = True
            file_data = fid.readlines()
        return file_data

    def generate_data(self):
        """Process file data."""
        self.import_echoview_csv_file()
        self.import_echoview_bottom_file()
        self.get_suncycle_data()

    def find_bottom(self, data=None):

        try:
            HH = evalin('base', 'HH')
            LAT = evalin('base', 'LAT')
            LON = evalin('base', 'LON')
        finally:
            pass

        estBottom = zeros(length(data.Latitude), 1)
        data.Longitude = copy(dot((abs(data.Longitude)), - 1))
        for m in arange(1, length(data.Latitude)).reshape(-1):
            if data.Latitude(m) != 999 or data.Longitude(m) != - 999:
                indLat = find(LAT >= data.Latitude(m))
                indLon = find(LON >= data.Longitude(m))
                if data.Latitude(m) > 0:
                    row = indLat[length(indLat)]
                else:
                    row = indLat[1]
                if data.Longitude(m) > 0:
                    col = indLon[length(indLon)]
                else:
                    col = indLon[1]
                estBottom[m] = HH[row, col]
            else:
                data.Latitude[m] = NaN
                data.Longitude[m] = NaN

        estBottom = abs(estBottom)
        estBottom[estBottom == 0] = NaN

    def import_echoview_csv_file(self):
        """Import numeric data from a text file as column vectors.
        from Chuck's csv2pdo
        """

        ping_count = len(self.file_data) - 1
        sample_count = int(self.file_data[1].split(',')[12])

        self.data.create_arrays(ping_count, sample_count)

        column_index = {}
        first_line = True
        for line in self.file_data:
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
                self.data.append_ping(ping_data, column_index)

    def plot_echoviewcsv_new(self):
        """from csv2pdo.py
        add logic from plotEchoviewCSV_NEW.m
        matplot lib uses 0-1 instead of 0-255 for color values so convert
        """
        self.generate_cmap()

        #  create a matplotlib figure to plot our echograms on
        self.figure = figure()

        #  set some properties for the sub plot layout
        subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93,
                        wspace=None,
                        hspace=None)
        self.ax_1 = self.figure.add_subplot(1, 1, 1)

        #  create an echogram to plot up the raw sample data
        echogram_plot = echogram(self.ax_1, self.data, data_attribute='values',
                                 cmap=self.cmap)
        echogram_plot.set_colormap(self.cmap, bad_data='green')
        plt.colorbar(echogram_plot.axes_image)

        self.add_day_night_bar()
        self.add_title()
        self.add_labels()
        self.add_logo()
        self.figure.tight_layout()

        self.save_image_file()
        self.ax_1.off
        show()

    def add_logo(self):
        if not os.path.isfile(self.logo_file):
            print("not a file")
            return

        image = plt.imread(self.logo_file)
        ax = plt.axes([0.5, 0.93, 0.9, 0.06],
                      frameon=False)  # [left, bottom, width, height])
        ax.imshow(image)
        ax.axis('off')  # get rid of the ticks and ticklabels

    def add_day_night_bar(self):

        # Set plot data.
        bar_height = 30
        n_pings = len(self.data.ping_time)
        plot_data = np.zeros((bar_height, n_pings, 3))
        daytime = self.data.daytime

        # Set the RGB values for each pixel.
        plot_data[:, daytime == 1] = [1, 1, 1]
        plot_data[:, daytime == 0] = [150, 150, 150]

        # Set axis ticks.
        # xticks = self.data.ping_time.astype('float')
        # main_plot_y_range = self.data.sample_count[-1]
        # yticks = main_plot_y_range - range(bar_height)

        # Plot the data.
        self.axes_image = self.ax_1.imshow(plot_data, cmap='binary',
                                           aspect='auto', interpolation='none',
                                           extent=[xticks[0], xticks[-1],
                                                   yticks[-1], yticks[0]],
                                           origin='upper')

        self.add_day_night_legend()

    def add_day_night_legend(self):
        white_patch = mpatches.Patch(color='white', label='Day')
        white_patch.set_edgecolor('black')
        black_patch = mpatches.Patch(color='grey', label='Night')
        black_patch.set_edgecolor('black')
        plt.legend(handles=[white_patch, black_patch], loc=4,
                   bbox_to_anchor=(1.25, -.2), frameon=False)

    def generate_cmap(self):
        mat_table = self.convert_color_table(self.color_table)
        n_colors = len(mat_table)
        self.cmap = LinearSegmentedColormap.from_list('Carrie', mat_table,
                                                      n_colors)

    def convert_color_table(self, color_table):
        mat_table = []
        for value in self.color_table:
            new_value = (np.round(value[0] / 255, decimals=4),
                         np.round(value[1] / 255, decimals=4),
                         np.round(value[2] / 255, decimals=4))
            mat_table.append(new_value)
        return mat_table

    def add_title(self):
        filename_arr = self.input_file.split('/')[-1][:-4].split('_')
        title = filename_arr[0] + ' ' + filename_arr[1] + ' ' + filename_arr[2]
        self.ax_1.set_title(title)

    def add_labels(self):
        """Add plot labels."""
        dates = self.data.ping_time
        min_date = min(dates)
        max_date = max(dates)
        min_day = min_date.astype('datetime64[D]')
        max_day = max_date.astype('datetime64[D]')
        if max_day - min_day > np.timedelta64(0):
            self.ax_1.set_xlabel(
                'Time in UTC (hour:min)' + '\n' + min_day.astype(
                    datetime).strftime("%d-%b-%Y") + \
                ' to ' + max_day.astype(datetime).strftime("%d-%b-%Y"))
        else:
            self.ax_1.set_xlabel(
                'Time in UTC (hour:min)' + '\n' + min_day.astype(
                    datetime).strftime("%d-%b-%Y"))

        self.ax_1.set_ylabel(self.y_label)

    def save_image_file(self):
        """Write image file."""
        if not os.path.exists(self.output_image_dir):
            os.makedirs(self.output_image_dir)

        self.figure.savefig(self.output_image_file, bbox_inches='tight')

    def get_suncycle_data(self):
        """returns the Time of SunRise, SunSet, Solar Altitude and Radiation."""

        self.data.daytime = np.empty((len(self.data.ping_time)))

        # Calculate sun
        for idx in range(len(self.data.ping_time)):
            self.data.daytime[idx] = self.suncycle(self.data.latitude[idx],
                                                   self.data.longitude[idx],
                                                   self.data.ping_time[idx])

        ##FIXME talk to Carrie about this.
        # hour=np.dot((self.data.ping_time % 1),24)
        # day=np.logical_xor(min(self.data.sun,[],2) < np.logical_and(hour,hour) < max(self.data.sun,[],2),self.data.sun(np.arange(),1) > self.data.sun(np.arange(),2))
        # self.data.day = day

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

        # print("sun_date", sun_date)
        # print("time", time)
        # m = 1
        # dt=1 /n
        # time = time + np.dot(dt, np.arange(0,n)).reshape(1,-1) - lon / 360

        # time = np.array([[176.325]])
        dec, jd, azm, rad = self.soradna(lat, lon, time,
                                         sun_date.astype('datetime64[Y]'))
        # NOTE azm is off by a bit at the beginning, dec is okay, jd is okay, rad is okay
        print("rad", rad)
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

    def import_echoview_bottom_file(self):
        # IMPORTFILE Import numeric data from a text file as a matrix.
        #   BOTTOM = IMPORTFILE(FILENAME) Reads data from text file FILENAME for
        #   the default selection.

        ## Initialize variables.
        delimiter = ','
        startRow = 2

        ## Format string for each line of text:
        formatSpec = '%s%s%f%f%f%f%f%f%f%f%f%[^\\n\\r]'

        ## Read columns of data according to format string.
        # This call is based on the structure of the file used to generate this
        # code. If an error occurs for a different file, try regenerating the code
        # from the Import Tool.
        # dataArray=textscan(fd,formatSpec,'Delimiter',delimiter,'EmptyValue',NaN,'HeaderLines',startRow - 1,'ReturnOnError',false)

        self.bottom_file_data = self.read_file(self.bottom_input_file)

        # print("bottom_file_data: ", self.bottom_file_data)
        print("bottom_file_data length: ", len(self.bottom_file_data))

    def plot_echoview_csv_new_old(self, data=None, number_frequencies=None,
                                  ExportFolder=None):

        ## Set title for figure
        files = data.file
        ind = strfind(files, '_to_')
        # FIXME Ignore the next 4 lines. low priority See notes.
        # if isempty(ind):
        #    title=copy(files)
        # else:
        #    title=(cellarray([cat(files[1:ind - 1],' to'),files[(ind + 4):end()]]))
        #         title = ({'Sv at 38 kHz',[files(1:ind-1) ' to'], files((ind+4):end), ['Data points removed: ' num2str(ceil(data.QC)) '#']});
        ########## Needed for PC1201/PC1202, title text too long
        #     str1 = 'GU1406-EK60-GOM';
        #     ind2 = strfind(files,'-D');
        #     str2 = files(ind2(1)+1:ind(1)-1);
        # # #     str3 = files(ind2(3)+1:end);
        #     str3 = files(ind2(2)+1:end);
        #     title = ({str1,[str2 ' to '], str3});

        ## Set x axis title for figure
        dates = datenum(data.Ping_date)
        minDate = min(dates)
        maxDate = max(dates)
        if maxDate - minDate > 0:
            xtitle = cellarray(['Time in UTC (hour:min)',
                                cat(datestr(minDate), ' to ',
                                    datestr(maxDate))])
        else:
            xtitle = cellarray(['Time in UTC (hour:min)', datestr(minDate)])

        ## Set figure properties
        #  create or raise figure
        # disp(cat('Plotting ',files))
        # fh=figure(2)
        # clf
        # height=5
        #
        # width=9
        #
        # FigDim=matlabarray(cat(0.1,0,width,height))
        # left_color=matlabarray(cat(0,0,0))
        # right_color=matlabarray(cat(0,0,0))
        # set(fh,'units','inches','position',FigDim,'Color','w','InvertHardCopy','off')
        # set(fh,'PaperUnits','inches','PaperSize',cat(width,height),'PaperPositionMode','manual','PaperPosition',cat(0,0,width,height))
        # set(fh,'defaultAxesColorOrder',cat([left_color],[right_color]))

        ## Call plotting program
        # FIXME On hold for now
        # if number_frequencies == 1:
        #    data.newData[data.newData == 2]=NaN
        #    readEKRaw_SimpleEchogram(data.newData.T,data.newTime,data.newRange,'threshold',cat(- 72,- 34),'Title',title,'XLabel',xtitle,'YLabel','Depth (m)','figure',fh)
        # else:
        #    plotEchogram_EK60Multifreq(data.newData.T,data.newTime,data.newRange,'Title',title,'XLabel',xtitle,'YLabel','Depth (m)','NumFreq',number_frequencies,'figure',fh)

        ## Plot bottom variables.
        if logical_not(isempty(data.Bottom)):
            hold('on')
            # Plot bottom
            plot(data.Bottom(arange(), 5), data.Bottom(arange(), 3), '.k')
            # # # #         plot(data.evlBottom.timestamp,data.evlBottom.bottom,'.r');
            # # # #         y = moving(data.Bottom(:,3),3,'median');
            # # # #         plot(data.Bottom(:,5),y,'.r')
            hold('off')
            maxDepth = max(data.Bottom(arange(), 3))
        else:
            # Plot estimated bottom from ETOPO1/GEBCO data
            hold('on')
            plot(data.PingDatenum, data.estBottom, '--', 'Color',
                 cat(0.22, 0.22, 0.22), 'LineWidth', 1)
            hold('off')
            maxDepth = max(data.estBottom)

        ## Set Y axis scale based on a range of depths
        if maxDepth < 100:
            ylim(cat(0, 104))
        else:
            if (maxDepth >= 100) and (maxDepth < 500):
                ylim(cat(0, 520))
            else:
                if (maxDepth >= 500) and (maxDepth < 1000):
                    ylim(cat(0, 1049))
                else:
                    if (maxDepth >= 1000) and (maxDepth < 2500):
                        ylim(cat(0, 2600))
                    else:
                        if (maxDepth >= 2500) and (maxDepth < 5000):
                            ylim(cat(0, 5200))
                        else:
                            if logical_not(isnan(maxDepth)):
                                ylim(cat(0(maxDepth + 10)))

        set(gca, 'YDir', 'reverse')
        ## Add NOAA logo
        file = 'NOAA_logo.png'
        addLogo(file, cat(- 10, - 10, 50, 50))
        ## Add day/night legend
        leg = 'day_night_legend.png'
        addLogo(leg, cat(0, 65, 75, 45))
        ## Add sun cycle
        yyaxis('right')
        time = data.PingDatenum.T
        one = ones(length(data.day), 1)
        nights = abs(data.day - one)
        X = matlabarray(cat(time, fliplr(time)))
        Y = matlabarray(cat(nights.T, fliplr(zeros(1, length(nights)))))
        plot(time, one, 'k')
        hold('on')
        fill(X, Y, cat(0.5, 0.5, 0.5), 'EdgeColor', 'k')
        hold('off')
        ylim(cat(0, 25))
        # # #     plot(data.PingDatenum,data.day);
        # # #     ylim([-0.5 5]);
        set(gca, 'YTick', 0)
        set(gca, 'YTickLabel', '')
        ## Save figure as png, close figure window
        imagename = matlabarray(
            cat(ExportFolder, '\\', char(cellstr(files)), '.png'))

        print_(gcf, '-dpng', '-r300', imagename)
        disp(cat('Saved ', files))
        close_('all')

    def read_ek_raw_simple_echogram(self, data=None, x=None, y=None,
                                    varargin=None):

        #   [fh, ih] = readEKRaw_SimpleEchogram(data, x, y, varargin) creates a figure
        #   of an echogram given data (usually Sv), X (ping number) and y (range).
        #   This is a simple function intended mainly to be used by the readEKRaw
        #   library examples.  Development on a proper plotting package is underway.
        #
        #   REQUIRED INPUT:
        #              data:    The data to plot.  A N x M matrix of typically Sv or
        #                       Sp data.
        #
        #                 x:    A vector of length M containing the corresponding ping
        #                       number or time for each ping in data.
        #
        #                 y:    A vector of length N containing the corresponding range
        #                       or depth for each sample in data.
        #
        #
        #   OPTIONAL PARAMETERS:
        #          Colormap:    Set this parameter a N x 3 array defining the colormap
        #                       to use for the echogram image.
        #                           Default: Simrad EK500 Colormap
        #
        #  DisplayThreshold:    Set this parameter to a 2 element vector [low, high]
        #                       specifying the values used in scaling the data for
        #                       display.
        #                           Default [-70, -34];
        #
        #            Figure:    Set this parameter to a number or handle ID specifying
        #                       the figure to plot the echogram into.  If a non-existant
        #                       figure number is passed, a new figure is created.  If an
        #                       existing figure is passed, the contents of that figure
        #                       are replaced with the echogram.
        #                           Default: [];
        #
        #             Title:    Set this parameter to a string defining the figure
        #                       title.
        #                           Default: 'Echogram'
        #
        #            XLabel:    Set this parameter to a string defining the X axis
        #                       label.
        #                           Default: 'Ping'
        #
        #            YLabel:    Set this parameter to a string defining the Y axis
        #                       label.
        #                           Default: 'Range (m)'
        #
        #   Rick Towler
        #   National Oceanic and Atmospheric Administration
        #   Alaska Fisheries Science Center
        #   Midwater Assesment and Conservation Engineering Group
        #   rick.towler@noaa.gov
        # -

        #  set default parameters
        dThreshold = matlabarray(cat(- 72, - 36))

        yLabelText = 'Range (m)'
        xLabelText = 'Ping'
        pTitle = 'Echogram'
        dataRGB = ek500()
        fh = matlabarray([])
        for n in arange(1, length(varargin), 2).reshape(-1):
            if 'xlabel' == lower(varargin[n]):
                xLabelText = varargin[n + 1]
            else:
                if 'ylabel' == lower(varargin[n]):
                    yLabelText = varargin[n + 1]
                else:
                    if cellarray(['displaythreshold', 'threshold']) == lower(
                            varargin[n]):
                        if (length(varargin[n + 1]) == 2):
                            dThreshold = varargin[n + 1]
                        else:
                            warning('readEKRaw:ParameterError', cat(
                                'Threshold - Incorrect number of arguments. ',
                                'Using defaults.'))
                    else:
                        if 'colormap' == lower(varargin[n]):
                            ctSize = size(varargin[n + 1])
                            if (ctSize[2] == 3) and (ctSize[1] < 256):
                                dataRGB = varargin[n + 1]
                            else:
                                warning('readEKRaw:ParameterError', cat(
                                    'Colormap - Colormap must be an n x 3 array of ',
                                    'RGB values where n < 256.'))
                        else:
                            if 'title' == lower(varargin[n]):
                                pTitle = varargin[n + 1]
                            else:
                                if 'figure' == lower(varargin[n]):
                                    fh = varargin[n + 1]
                                else:
                                    warning('readEKRaw:ParameterError',
                                            cat('Unknown property name: ',
                                                varargin[n]))

        # scale data to byte values corresponding to color table entries
        ctBot = 1
        ctTop = length(dataRGB)
        ctRng = ctTop - ctBot
        data = uint8(ceil(
            dot((data - dThreshold[1]) / (dThreshold[2] - dThreshold[1]),
                ctRng)) + ctBot)

        #  create or raise figure
        if (isempty(fh)):
            fh = figure()
        else:
            figure(fh)

        #  create the echogram image
        ih = image(x, y, data, 'CDataMapping', 'direct')
        set(gca, 'XGrid', 'on', 'Units', 'pixels')

        #  set figure properties
        hrscb = matlabarray(
            cat('fp=get(gcbo,\'Position\'); ah=get(gcbo,\'UserData\');',
                'p=[0,0,fp(3),fp(4)]; set(ah,\'OuterPosition\',p);'))
        set(fh, 'ResizeFcn', hrscb, 'Units', 'pixels', 'UserData', gca)
        tmp = abs(dThreshold[1]) - abs(dThreshold[2])
        tickMarks = arange(dThreshold[1], dThreshold[2], tmp / 4)

        #  set the colormap
        colormap(dataRGB)
        colorbar('YTick', cat(0.5, 3.5, 6.5, 9.5, 12.5), 'YTickLabel',
                 cellarray([num2str(tickMarks[1]), num2str(tickMarks[2]),
                            num2str(tickMarks[3]), num2str(tickMarks[4]),
                            num2str(tickMarks[5])]))

        #  label
        xlabel(xLabelText, 'FontName', 'Times', 'FontSize', 14)
        ylabel(yLabelText, 'FontName', 'Times', 'FontSize', 14)
        title(pTitle, 'FontName', 'Times', 'FontSize', 14, 'Interpreter',
              'none')
        datetick
        xlim(cat(min(x), max(x)))

        return fh, ih

    def plot_echogram_ek_60_multifreq(self, data=None, x=None, y=None,
                                      varargin=None):

        #   [fh, ih] = readEKRaw_SimpleEchogram(data, x, y, varargin) creates a figure
        #   of an echogram given data (usually Sv), X (ping number) and y (range).

        #   This is a simple function intended mainly to be used by the readEKRaw
        #   library examples.  Development on a proper plotting package is underway.

        #   REQUIRED INPUT:
        #              data:    The data to plot.  A N x M matrix of typically Sv or
        #                       Sp data.

        #                 x:    A vector of length M containing the corresponding ping
        #                       number or time for each ping in data.

        #                 y:    A vector of length N containing the corresponding range
        #                       or depth for each sample in data.

        #   OPTIONAL PARAMETERS:
        #            Figure:    Set this parameter to a number or handle ID specifying
        #                       the figure to plot the echogram into.  If a non-existant
        #                       figure number is passed, a new figure is created.  If an
        #                       existing figure is passed, the contents of that figure
        #                       are replaced with the echogram.
        #                           Default: [];

        #             Title:    Set this parameter to a string defining the figure
        #                       title.
        #                           Default: 'Echogram'

        #            XLabel:    Set this parameter to a string defining the X axis
        #                       label.
        #                           Default: 'Ping'

        #            YLabel:    Set this parameter to a string defining the Y axis
        #                       label.
        #                           Default: 'Range (m)'

        #            NumFreq:   Set this parameter to identify how many frequences
        #                       were included in the EK60 data. This is used to set
        #                       the colormap and legend labels

        #   Rick Towler/Carrie Wall

        # -
        #  set default parameters
        yLabelText = 'Depth (m)'
        xLabelText = 'Time'
        pTitle = 'Echogram'
        frequencies = 5
        for n in arange(1, length(varargin), 2).reshape(-1):
            if 'xlabel' == lower(varargin[n]):
                xLabelText = varargin[n + 1]
            else:
                if 'ylabel' == lower(varargin[n]):
                    yLabelText = varargin[n + 1]
                else:
                    if cellarray(['displaythreshold', 'threshold']) == lower(
                            varargin[n]):
                        if (length(varargin[n + 1]) == 2):
                            dThreshold = varargin[n + 1]
                        else:
                            warning('readEKRaw:ParameterError', cat(
                                'Threshold - Incorrect number of arguments. ',
                                'Using defaults.'))
                    else:
                        if 'title' == lower(varargin[n]):
                            pTitle = varargin[n + 1]
                        else:
                            if 'figure' == lower(varargin[n]):
                                fh = varargin[n + 1]
                            else:
                                if 'numfreq' == lower(varargin[n]):
                                    frequencies = varargin[n + 1]
                                else:
                                    warning('readEKRaw:ParameterError',
                                            cat('Unknown property name: ',
                                                varargin[n]))

        # scrsz = get(0,'ScreenSize');
        # fh = figure('Position',[10 50 scrsz(3)-20 scrsz(4)/1.35]);

        rgb = self.config.get('plotting', 'rgb' + frequencies)
        converted_rgb = self.convert_color_table(rgb)
        #  set the colormap
        colormap(converted_rgb)

        #  create the echogram image
        ih = image(x, y, data, 'CDataMapping', 'direct')

        # [~,ih] = contourf(x, y, data,size(RGB,1));
        # set(ih,'edgecolor',none);
        # set(ih,'LineWidth',0.1);
        set(gca, 'XGrid', 'on', 'Units', 'pixels')
        set(gca, 'FontName', 'Times', 'FontSize', 14)

        #  label
        xlabel(xLabelText, 'FontName', 'Times', 'FontSize', 14)
        ylabel(yLabelText, 'FontName', 'Times', 'FontSize', 14)
        title(pTitle, 'FontName', 'Times', 'FontSize', 14, 'Interpreter',
              'none')
        datetick
        xlim(cat(min(x), max(x)))

        # #Plot colorbar or colorbar lables
        # lcolorbar(labels,'FontName','Times','FontSize',7);
        return fh, ih


if __name__ == '__main__':
    image = EchogramImage()
    image.get_suncycle_data()