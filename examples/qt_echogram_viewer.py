
"""This a simple example showing how to use the PyQt based echogram_viewer
which is a high level interface to the AFSC QImageViewer library.

This example reads a .raw file, gets Sv, detects bottom, and plots the
echogram and the bottom line.

The data file contains 19066 pings so it is a good test of the pyEcholab
qt plotting libraries. You will need to zoom into the echogram to see the
bottom line. You can pan using the scroll bars or by holding <ALT> and
clicking and dragging.

The QImageViewer library Requires PyQt5.

Controls:

    <CTRL> + Mouse Wheel zooms in/out
    <ALT> + Click and drag will pan


"""

import sys
from PyQt5 import QtWidgets
from echolab2.instruments import EK60
from echolab2.plotting.qt import echogram_viewer
from echolab2.processing import afsc_bot_detector


def read_write_callback(filename, cumulative_pct, cumulative_bytes, userref):
    '''
    read_write_callback is a simple example of using the progress_callback
    functionality of the EK60.read_raw and EK60.write_raw methods.
    '''

    if cumulative_pct > 100:
        return

    if cumulative_pct == 0:
        sys.stdout.write(filename)

    if cumulative_pct % 4:
        sys.stdout.write('.')

    if cumulative_pct == 100:
        sys.stdout.write('  done!\n')



# Specify a raw file. This file is big, it takes a bit to load and display.
rawfiles = ['./data/ES60/L0059-D20140518-T181425-ES60.raw']

# Create an instance of the EK60 instrument.
ek60 = EK60.EK60()

# Read the data. -
print('Reading raw file:')
ek60.read_raw(rawfiles, progress_callback=read_write_callback,
        frequencies=38000)

# Get the 38 kHz raw data.
print('Getting Sv...')
raw_data = ek60.get_channel_data(frequencies=38000)
raw_data_38 = raw_data[38000][0]
print(raw_data_38)

# Get a calibration object - This returns a cal object that
# is populated with data from the .raw file. You can change
# the values as needed.
cal_obj = raw_data_38.get_calibration()
cal_obj.transducer_draft = 50

# Get Sv data.
Sv_38 = raw_data_38.get_Sv(calibration=cal_obj, return_depth=True)

# Ccreate an instance of our bottom detector and apply to our data.
# Note that our data is in depth and Sv so we provide a search
# min in depth and a backstep in Sv
print('Running bottom detector...')
bot_detector = afsc_bot_detector.afsc_bot_detector(search_min=2,
        backstep=35)
detected_bottom = bot_detector.detect(Sv_38)

#  set our bottom line cosmetic properties
detected_bottom.color = [225,200,0]
detected_bottom.thickness = 2


print('Plotting...')

# Create an application instance.
app = QtWidgets.QApplication([])

# Create the main application window and show it
eg_viewer = echogram_viewer.echogram_viewer()

#  show the application window
eg_viewer.show()

# Set the echogram data
eg_viewer.update_echogram(Sv_38)

# Add our bottom line
eg_viewer.add_line(detected_bottom)

#  save the echogram at full resolution. Curently this does not
#  include the horizontal scaling that is appled to the sample data
#  to reduce the vertical exaggeration of the echograms.
#eg_viewer.save_image('test.png')

# Start event processing.
app.exec_()
