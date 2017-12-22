

from matplotlib.colors import LinearSegmentedColormap
import numpy as np

class echogram(object):

    def __init__(self, threshold=[-70,-34]):

        self.threshold = threshold

        #  set the default SIMRAD EK500 color table plus grey for NoData
        self.colorTable = [(1,1,1),
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
                           (0.4705,0.2353,0.1568),
                           (0.7843,0.7843,0.7843)]

        #  set the color table length but subtract 1 since we don't
        #  want to include the grey value
        self._ctLength = len(self.colorTable) -1

        self.echogram_data = None

        self.cmap = LinearSegmentedColormap.from_list('Simrad', self.colorTable)

    def update_echogram(self, data, threshold=None):

        if threshold:
            self.threshold = threshold

        echodata = data.astype('float32')


        echodata = np.round((echodata - self.threshold[0]) / (self.threshold[1] -
                                self.threshold[0]) * self._ctLength)
        echodata[echodata < 0] = 0
        echodata[echodata > self._ctLength-1] = self._ctLength-1
        echoData = echodata.astype(np.uint8)

        self.echogram_data = np.rot90(echoData,3)
