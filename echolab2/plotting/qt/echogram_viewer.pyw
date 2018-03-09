
import os
import numpy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from .ui import ui_echogram_viewer

class echogram_viewer(QMainWindow, ui_echogram_viewer.Ui_echogram_viewer):

    def __init__(self, p_data, plot_attribute='Sv', parent=None):
        super(echogram_viewer, self).__init__(parent)
        self.setupUi(self)

        self.echogramLabel = None

        #  connect the echogram signals
        self.connect(self.QEchogramViewer, SIGNAL("mousePressEvent"), self.echogramClick)
        self.connect(self.QEchogramViewer, SIGNAL("mouseReleaseEvent"), self.echogramUnClick)
        self.connect(self.QEchogramViewer, SIGNAL("mouseMoveEvent"), self.echogramMouseInWidget)

        #  restore the application state
        self.appSettings = QSettings('afsc.noaa.gov', 'echogram_viewer')
        size = self.appSettings.value('winsize', QSize(1000,600)).toSize()
        self.resize(size)
        position = self.appSettings.value('winposition', QPoint(5,5)).toPoint()
        self.move(position)

        #  set the base directory path - this is the full path to this application
        self.baseDir = reduce(lambda l,r: l + os.path.sep + r,
                              os.path.dirname(os.path.realpath(__file__)).split(os.path.sep))
        try:
            self.setWindowIcon(QIcon(self.baseDir + os.sep + 'resources/echoIcon.png'))
        except:
            pass


        self.update_echogram(p_data, plot_attribute)


    def echogramClick(self, imageObj, clickLoc, button, modifier, items):
        pass
#        if (items):
#            print("Picked:",items)


    def echogramUnClick(self, imageObj, clickLoc, button, modifier, items):
        pass


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


    def update_echogram(self, p_data, plot_attribute='Sv'):
        """
        update_echogram updates the echogram image using data from the provided
        processed_data object
        """

        #  clear out the echogram viewer
        self.QEchogramViewer.clearViewer()

        if hasattr(p_data, 'range'):
            y_axis = p_data.range
        else:
            y_axis = p_data.depth

        #  set the Echogram data
        self.QEchogramViewer.setEchogramFromArray(p_data.data, yaxis=y_axis,
                xaxis=p_data.ping_time)

        #  add the echogram HUD text
        self.echogramLabel = self.QEchogramViewer.addHudText(QPointF(0.99,0.995),
                '', color=[0,250,0], alpha=200, halign='right', valign='bottom')
        self.echogramLabel.setBackground([0,0,0], 250)

        #  fill the echogram window - vertical extent only
        self.QEchogramViewer.fillExtent(verticalOnly=True)


    def closeEvent(self, event):

        #  store the application size and position
        self.appSettings.setValue('winposition', self.pos())
        self.appSettings.setValue('winsize', self.size())

        event.accept()



