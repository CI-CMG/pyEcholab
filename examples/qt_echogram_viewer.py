
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from echolab2.instruments import EK60
from echolab2.plotting.qt import echogram_viewer


#  specify some raw files that have heave data and transducer depth in the raw data
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw','./data/EK60/DY1706_EK60-D20170625-T062521.raw']
rawfiles = ['./data/EK60/W070827-T140039.raw']

#  create an instance of the EK60 instrument.
ek60 = EK60.EK60()

#  read the data
ek60.read_raw(rawfiles)

#  get the 38 kHz raw data
raw_data_38 = ek60.get_rawdata(channel_number=2)

#  get a processed_data object containing the heave corrected Sv on a depth grid
heave_corrected_Sv = raw_data_38.get_sv(heave_correct=True)


#  create an application instance
app = QApplication([])

#  create the main application window
window = echogram_viewer.echogram_viewer(heave_corrected_Sv)
window.show()

#  start event processing
app.exec_()
