
"""
This example is used mainly to test the PyQt based plotting tools.
These tools were originally developed for displaying images and were
extended to work with echogram data.

Controls:
    <CTRL> + Mouse Wheel zooms in.out
    <ALT> + Click and drag will pan


WARNING: This code currently uses PyQt4 and is incompatible with Qt5

The plan is to make the qt plotting tools compatible with Python3/Qt5
but they currently only work in Python2/PyQt4.

"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from echolab2.instruments import EK60
from echolab2.plotting.qt import echogram_viewer


#  specify a raw file. This file is big, it takes a bit to load and display
rawfiles = ['./data/ES60/L0059-D20140518-T181425-ES60.raw']

#  create an instance of the EK60 instrument.
ek60 = EK60.EK60()

#  read the data
ek60.read_raw(rawfiles)

#  get the 38 kHz raw data
raw_data_38 = ek60.get_raw_data(channel_number=1)

#  get Sv
Sv_38 = raw_data_38.get_Sv()

#  create an application instance
app = QApplication([])

#  create the main application window
window = echogram_viewer.echogram_viewer(Sv_38)
window.show()

#  start event processing
app.exec_()
