
import os
import functools
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import  pyqtSlot
from .ui import ui_echogram_viewer

class echogram_viewer(QtWidgets.QMainWindow, ui_echogram_viewer.Ui_echogram_viewer):

    def __init__(self, p_data=None, plot_attribute='Sv', h_scale=None, parent=None, maxZoom=40):
        super(echogram_viewer, self).__init__(parent)
        self.setupUi(self)

        self.echogramLabel = None
        if h_scale:
            self.h_scale = h_scale
        else:
            self.h_scale = 4.0

        self.QEchogramViewer.maxZoom = maxZoom

        #  connect the echogram signals
        self.QEchogramViewer.mousePress.connect(self.echogramClick)
        self.QEchogramViewer.mouseMove.connect(self.echogramMouseInWidget)
        self.QEchogramViewer.mouseRelease.connect(self.echogramUnClick)

        #  set the base directory path - this is the full path to this application
        self.baseDir = functools.reduce(lambda l,r: l + os.path.sep + r,
                os.path.dirname(os.path.realpath(__file__)).split(os.path.sep))
        try:
            self.setWindowIcon(QtWidgets.QIcon(self.baseDir + os.sep + 'resources/echoIcon.png'))
        except:
            pass

        if p_data:
            self.update_echogram(p_data, plot_attribute)


    def update_echogram(self, p_data, plot_attribute='Sv', h_scale=None):
        """
        update_echogram updates the echogram image using data from the provided
        processed_data object
        """
        #  clear out the echogram viewer
        self.QEchogramViewer.clearViewer()

        if h_scale:
            self.h_scale = h_scale

        if hasattr(p_data, 'range'):
            y_axis = p_data.range
        else:
            y_axis = p_data.depth

        #  set the Echogram data
        self.QEchogramViewer.setEchogramFromArray(p_data.data, yaxis=y_axis,
                xaxis=p_data.ping_time)

        #  add the echogram HUD text
        self.echogramLabel = self.QEchogramViewer.addHudText(QtCore.QPointF(0.99,0.995),
                '', color=[0,250,0], alpha=200, halign='right', valign='bottom')
        self.echogramLabel.setBackground([0,0,0], 250)

        #TODO: scaling should be done in QEchogramViewer since is is applicable
        #      to all echograms, not just ones created with this simple app.

        #  scale the echogram, setting the sticky keyword to True to keep this
        #  relative scale when zooming. Echograms tend to look a bit better when
        #  scaled horizontally. Here we apply a "sticky" horizontal scaling which
        #  will maintain the scaling when zooming.
        self.QEchogramViewer.scale(self.h_scale, 1, sticky=True)

        #  fill the echogram window - vertical extent only
        self.QEchogramViewer.fillExtent(verticalOnly=True)


    def save_image(self, filename, **kwargs):
        '''
        save_image saves the echogram image including any marks, lines, etc. This
        saves the full echogram, regardless of the current view at the resolution of
        the echogram. You can specify a width and height if you want to override the
        default resolution.
        '''
        self.QEchogramViewer.saveImage(filename, **kwargs)


    def save_view(self, filename, **kwargs):
        '''
        save_image saves the current view of the echogram image including any marks,
        lines, etc. The view is what is rendered on screen in the current window and
        the resolution is always the size of the current view.

        This is a work in progress, currently the
        '''
        self.QEchogramViewer.saveImage(filename, **kwargs)


    def add_line(self, line, **kwargs):
        '''
        Add a echolab2.processing.line object to the echogram. The color
        style, and width of the line is defined in the line object.
        '''

        #  add the cosmetic properties to the arguments.
        kwargs = dict(kwargs, color=line.color, linestyle=line.linestyle,
                thickness=line.thickness)

        line = self.QEchogramViewer.addLine([line.ping_time, line.data],
                **kwargs)

        return line
        

    def zoom_to_depth(self, start_depth, end_depth):
        self.QEchogramViewer.zoomToDepth(start_depth, end_depth)

    def add_grid(self, grid, **kwargs):
        '''
        Add a echolab2.processing.grid object to the echogram. The color
        style, and width of the line is defined in the grid object.
        '''
        grid=self.QEchogramViewer.addGrid(grid, **kwargs)
        
        return grid


    def closeEvent(self, event):
        # add cleanup here...
        
        event.accept()


#    def resizeEvent(self, event):
#        self.QEchogramViewer.fillExtent(verticalOnly=True)


    @pyqtSlot(object, object, int, object, list)
    def echogramClick(self, imageObj, clickLoc, button, modifier, items):
        pass
#        if (items):
#            print("Picked:",items)


    @pyqtSlot(object, object, int, object, list)
    def echogramUnClick(self, imageObj, clickLoc, button, modifier, items):
        pass


    @pyqtSlot(object, object, object, list, list)
    def echogramMouseInWidget(self, imageObj, location, modifier, draggedItems, items):

#        if (items):
#            print("Dragged:", items)

        if (location[0] != None):
            #  update the depth/time at cursor label
            locationString = 'Depth: %.2fm    Time: %s  ' % (location[1],
                    location[0].tolist().strftime('%m/%d/%Y %H:%M:%S'))
            self.echogramLabel.setText(locationString)

            #  force a redraw of the echogram so the label is refreshed
            self.QEchogramViewer.viewport().update()


