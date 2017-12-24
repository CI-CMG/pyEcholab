
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Colormap
import numpy as np


class echogram(object):
    '''
    This is a bit of a mess. I wanted to inherit from plt but that isn't straightforward.
    I realize now that this should probably inherit from matplotlib.image.AxesImage

    I'm leaving it as is for now since we can get echograms on the screen
    '''

    def __init__(self, data=None, threshold=[-70,-34], cmap=None):


        self.plotobj = None
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
        self.cmap = self._simrad_cmap

        self.set_data(data)



    def set_data(self, data):
        if (isinstance(data, np.ndarray)):
            #  update our data property - make sure it's a float
            self.data = data.astype('float32')
            self.update_echogram()


    def set_colormap(self, colormap, bad_data=None):
        if (isinstance(colormap, str)):
            colormap = Colormap(colormap)
        self.cmap = colormap
        if (bad_data):
            self.cmap.set_bad = bad_data
        self.update_echogram()


    def set_threshold(self, threshold=[-70,-34]):
        if (threshold):
            self.threshold = threshold
            self.update_echogram()

    def update_echogram(self):

        echodata = np.flipud(np.rot90(self.data,1))
        self.plotobj  = plt.imshow(echodata, cmap=self.cmap, vmin=self.threshold[0],
                vmax=self.threshold[1], aspect='auto')

