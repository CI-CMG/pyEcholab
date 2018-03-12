

#import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap, Colormap
import numpy as np


class echogram(object):
    '''
    This should probably be a matplotlib custom Axes or what I gather matplotlib calls
    "projections".

    https://matplotlib.org/examples/api/custom_projection_example.html

    THIS IS SOME RAW CODE. It would be really great if someone picked this up
    and made it better.

    '''


    def __init__(self, axes, data_object=None, data_attribute=None, threshold=None,
            cmap=None, x_label_attribute='ping_time', y_label_attribute='range'):

        #  the attribute keyword only needs to be used when you are plotting data from
        #  raw_data objects (which you normally shouldn't need to do.) When attribute
        #  is None, we assume that we're working with a processed_data object which
        #  stores the sample data in the "data" attribute.

        self.axes = axes
        self.threshold = threshold
        self.x_label_attribute = x_label_attribute
        self.y_label_attribute = y_label_attribute

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

        self.set_data(data_object, data_attribute=data_attribute)


    def set_data(self, data_object, data_attribute=None, update=True):
        if (data_attribute):
            self.data_attribute = data_attribute
        else:
            self.data_attribute = None
        self.data_object = data_object

        if update:
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


    def update(self, data_object=None, data_attribute=None, threshold=None,
            x_label_attribute=None, y_label_attribute=None):

        #  update attributes if required
        if (threshold):
            self.threshold = threshold
        if (x_label_attribute):
            self.x_label_attribute = x_label_attribute
        if (y_label_attribute):
            self.y_label_attribute = y_label_attribute
        if (data_attribute):
            self.data_attribute = data_attribute
        if (data_object):
            self. set_data(data_object, data_attribute=data_attribute, update=False)

        #  get a reference to the data to plot.
        if (self.data_attribute):
            if (not hasattr(self.data_object, self.data_attribute)):
                #  we don't have any data to plot
                return
            else:
                data = getattr(self.data_object, self.data_attribute)
        else:
            data = self.data_object.data

        #  set the threshold
        if (self.threshold):
            threshold = self.threshold
        else:
            threshold = [np.nanmin(data),np.nanmax(data)]

        #  transform the data so it looks
        echodata = np.flipud(np.rot90(data,1))

        #  plot the sample data
        self.axes_image = self.axes.imshow(echodata, cmap=self.cmap, vmin=threshold[0],
                vmax=threshold[1], aspect='auto', interpolation='none')


        #  THE AXES LABELING BELOW DOESN'T WORK
        if (0):

            #  update the axes
            if (hasattr(self.data_object, x_label_attribute)):
                tick_labels = getattr(self.data_object, self.x_label_attribute)
                tic_locs = self.axes.get_xticks()
                tic_locs = tic_locs[ np.logical_and(tic_locs >= 0, tic_locs < tick_labels.shape[0])].astype('uint32')
                tick_labels = tick_labels[tic_locs]
                self.axes.set_xticklabels(tick_labels)

            if (hasattr(self.data_object, y_label_attribute)):

                tick_labels = getattr(self.data_object, self.y_label_attribute)

                tic_locs = np.arange(0, tick_labels.shape[0], 25)
                tick_labels = tick_labels[tic_locs]

                self.axes.set_yticklabels(tick_labels)
                self.axes.yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1f'))

