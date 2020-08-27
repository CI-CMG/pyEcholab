
import os
import functools
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import  pyqtSlot
from .ui import ui_echogram_viewer

class echogram_viewer(QtWidgets.QMainWindow, ui_echogram_viewer.Ui_echogram_viewer):

    def __init__(self, p_data, plot_attribute='Sv', parent=None):
        super(echogram_viewer, self).__init__(parent)
        self.setupUi(self)

        self.echogramLabel = None

        #  connect the echogram signals
        self.QEchogramViewer.mousePress.connect(self.echogramClick)
        self.QEchogramViewer.mouseMove.connect(self.echogramMouseInWidget)
        self.QEchogramViewer.mouseRelease.connect(self.echogramUnClick)

        #  restore the application state
        self.appSettings = QtCore.QSettings('afsc.noaa.gov', 'echogram_viewer')
        size = self.appSettings.value('winsize', QtCore.QSize(1000,600))
        position = self.appSettings.value('winposition', QtCore.QPoint(5,5))

        #  et the virtual screen size
        screen = QtWidgets.QApplication.primaryScreen()
        v_screen_size = screen.availableVirtualSize()

        #  check if our last window size is too big for our current screen
        if (size.width() > v_screen_size.width()):
            size.setWidth(v_screen_size.width() - 50)
        if (size.height() > v_screen_size.height()):
            size.setHeight(v_screen_size.height() - 50)

        #  now check if our last position is at least on our current desktop
        #  if it is off the screen we just throw it up at 0
        if (position.x() > size.width() - 50):
            position.setX(0)
        if (position.y() > size.height() - 50):
            position.setY(0)

        #  now move and resize the window
        self.move(position)
        self.resize(size)

        #  set the base directory path - this is the full path to this application
        self.baseDir = functools.reduce(lambda l,r: l + os.path.sep + r,
                os.path.dirname(os.path.realpath(__file__)).split(os.path.sep))
        try:
            self.setWindowIcon(QtWidgets.QIcon(self.baseDir + os.sep + 'resources/echoIcon.png'))
        except:
            pass

        self.update_echogram(p_data, plot_attribute)


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
        self.echogramLabel = self.QEchogramViewer.addHudText(QtCore.QPointF(0.99,0.995),
                '', color=[0,250,0], alpha=200, halign='right', valign='bottom')
        self.echogramLabel.setBackground([0,0,0], 250)

        #  fill the echogram window - vertical extent only
        self.QEchogramViewer.fillExtent(verticalOnly=True)



    def add_line(self, line, **kwargs):

        self.QEchogramViewer.addLine([line.ping_time, line.data], **kwargs)

    def closeEvent(self, event):

        #  store the application size and position
        self.appSettings.setValue('winposition', self.pos())
        self.appSettings.setValue('winsize', self.size())

        event.accept()



