

#import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Colormap
import numpy as np


class echogram(object):
    '''
    This should probably be a matplotlib custom Axes or what I gather matplotlib calls
    "projections".

    https://matplotlib.org/examples/api/custom_projection_example.html
    '''


    def __init__(self, axes, data=None, threshold=None, cmap=None):

        self.axes = axes
        self.threshold = None

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
        self.cmap = self._simrad_cmap

        self.set_data(data)


    def set_data(self, data, update=True):
        if (isinstance(data, np.ndarray)):
            #  update our data property - make sure it's a float
            self.data = data.astype('float32')
            if update:
                self.update()


    def set_colormap(self, colormap, bad_data=None, update=True):
        if (isinstance(colormap, str)):
            colormap = Colormap(colormap)
        self.cmap = colormap
        if (bad_data):
            self.cmap.set_bad = bad_data
        if update:
            self.update()


    def set_threshold(self, threshold=[-70,-34], update=True):
        if (threshold):
            self.threshold = threshold
        else:
            self.threshold = None

        if update:
            self.update()


    def update(self, data=None, threshold=None):

        if (threshold):
            self.threshold = threshold

        if (not data):
            data = self.data

        if (self.threshold):
            threshold = self.threshold
        else:
            threshold = [np.nanmin(data),np.nanmax(data)]

        echodata = np.flipud(np.rot90(data,1))
        self.axes.imshow(echodata, cmap=self.cmap, vmin=threshold[0],
                vmax=threshold[1], aspect='auto')

