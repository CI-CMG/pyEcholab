


from matplotlib.colors import LinearSegmentedColormap, Colormap
import numpy as np


class echogram(object):
    '''
    This is becoming less of a mess, but it still needs a lot of work...

    '''


    def __init__(self, axes, data_object=None, data_attribute=None, threshold=None,
            cmap=None):

        #  the attribute keyword only needs to be used when you are plotting data from
        #  raw_data objects (which you normally shouldn't need to do.) When attribute
        #  is None, we assume that we're working with a processed_data object which
        #  stores the sample data in the "data" attribute.

        self.axes = axes
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

        self.set_data(data_object, data_attribute=data_attribute)


    def set_data(self, data_object, data_attribute=None, update=True):
        if (data_attribute):
            self.data_attribute = data_attribute
        else:
            self.data_attribute = None
        self.data_object = data_object

        if (hasattr(self.data_object, 'range')):
            self.y_label_attribute = 'range'
        elif (hasattr(self.data_object, 'depth')):
            self.y_label_attribute = 'depth'
        else:
            self.y_label_attribute = None

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


    def update(self, data_object=None, data_attribute=None, threshold=None):

        #  update attributes if required
        if (threshold):
            self.threshold = threshold

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

        #  transform the data so it looks right with imshow
        echodata = np.flipud(np.rot90(data,1))

        #  determine the vertical extent of the data
        if (hasattr(self.data_object, self.y_label_attribute)):
            yticks = getattr(self.data_object, self.y_label_attribute)
        else:
            #  we don't have a valid axis - just use sample number
            yticks = np.arange(echodata.shape[0])

        #  plot the sample data
        self.axes_image = self.axes.imshow(echodata, cmap=self.cmap, vmin=threshold[0],
                vmax=threshold[1], aspect='auto', interpolation='none',
                extent=[0,echodata.shape[1],yticks[-1],yticks[0]])

        #  when setting the axis labels we are being lazy and letting matplotlib decide
        #  on a suitable label spacing. We could probably do this ourselves and save the
        #  effort of setting any locations outside of our data range


        #  set the x axis labels
        xticks = self.data_object.ping_time
        #  convert the locations to ints so we can use them to index into ping_time
        x_tic_locs = self.axes.get_xticks().astype('int')
        #  xticks are sometimes outside the range of our data - find ones that are
        bad_locs = (x_tic_locs < 0) | (x_tic_locs >= echodata.shape[1])
        #  and set those to 0
        x_tic_locs[bad_locs] = 0
        #  build a list of tick labels. there are a couple of good tricks here
        #  first convert our datetime64 to numpy type 'object' which converts them
        #  to Python datetime objects. We can then use the datetime.strftime method
        #  to format them. We then convert this list into a numpy array of python
        #  string objects so we can use our bad_locs index array to set the bad
        #  labels to an empty string
        label_objs = xticks[x_tic_locs].astype('object')
        ticklabels = np.array([i.strftime("%H:%M:%S")
            for i in label_objs], dtype='object')
        ticklabels[bad_locs] = ''
        #  lastly set the labels
        self.axes.set_xticklabels(ticklabels)
        self.axes.set_xlabel(label_objs[0].strftime("%m-%d-%Y"))


        if (hasattr(self.data_object, self.y_label_attribute)):
            self.axes.set_ylabel(self.y_label_attribute + ' (m)')
        else:
            self.axes.set_ylabel('sample')

        #  apply the grid
        self.axes.grid(True,color='k')


