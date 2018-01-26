

#import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.colors import LinearSegmentedColormap, Colormap
import numpy as np


class echogram(object):
    '''
    This should probably be a matplotlib custom Axes or what I gather matplotlib calls
    "projections".

    https://matplotlib.org/examples/api/custom_projection_example.html
    '''


    def __init__(self, axes, data_object=None, attribute='Sv',
                 threshold=None, cmap=None):

        self.axes = axes
        self.threshold = threshold

        #  set the default SIMRAD EK500 color table plus grey for NoData
        self._simrad_color_table = [ (1,1,1),
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

        self.set_data(data_object, attribute=attribute)


    def set_data(self, data_object, attribute='Sv', update=True):
        if (hasattr(data_object, attribute)):
            self.data_object = data_object
            self.attribute = attribute

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


    def update(self, data_object=None, attribute=None, threshold=None,
            x_label_attribute='ping_time', y_label_attribute='range'):

        #  update attributes if required
        if (threshold):
            self.threshold = threshold
        if (data_object):
            self. set_data(data_object, attribute=attribute, update=False)

        #  check if we have the data we're being asked to plot
        if (not hasattr(self.data_object, self.attribute)):
            #  we don't have any data to plot
            return

        #  get a reference to that data
        data = getattr(self.data_object, self.attribute)

        #  set the threshold
        if (self.threshold):
            threshold = self.threshold
        else:
            threshold = [np.nanmin(data),np.nanmax(data)]

        #  transform the data so it looks
        echodata = np.flipud(np.rot90(data,1))#.astype('float32')

        #  plot the sample data
        self.axes_image = self.axes.imshow(echodata, cmap=self.cmap, vmin=threshold[0],
                vmax=threshold[1], aspect='auto', interpolation='none')


        #  THE AXES LABELING BELOW DOESN'T WORK
        if (0):

            #  update the axes
            if (hasattr(self.data_object, x_label_attribute)):
                tick_labels = getattr(self.data_object, x_label_attribute)
                tic_locs = self.axes.get_xticks()
                tic_locs = tic_locs[ np.logical_and(tic_locs >= 0, tic_locs <= tick_labels.shape[0])].astype('uint32')
                tick_labels = tick_labels[tic_locs]
                self.axes.set_xticklabels(tick_labels)

            if (hasattr(self.data_object, y_label_attribute)):

                tick_labels = getattr(self.data_object, y_label_attribute)

                tic_locs = np.arange(0, tick_labels.shape[0], 25)
                tick_labels = tick_labels[tic_locs]

                self.axes.set_yticklabels(tick_labels)
                self.axes.yaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1f'))

