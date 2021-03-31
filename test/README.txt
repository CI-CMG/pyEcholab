These scripts compare PyEcholab data values with data exported from Echoview.
A few scripts plot up data generated using MATLAB code by Lars Nonboe Andersen
from Simrad. Scripts are written to test specific hardware, file format and data
types to ensure correct results.


The *_test.py scripts compare power, Sv, TS, angle, range, and time data with
data exported from Echoview while also verifying that the raw data can be written
correctly. The scripts output progress to the console and return 0 if they check out.
Typically "check out" means within a few hundreths of a dB. Check the individual
scripts for details. The plan would be to use these scripts for automated testing.

The *_plot.py scripts will plot the echograms and echogram differences between
the PyEcholab and EV data (and a few the MATLAB data) to visualize any differences.
These scripts are intended to be used to convince oneself that the raw data
conversions are correct. If you have access to Echoview, I suggest exporting your
own data and using one of these scripts as a template to check data from your
own systems.


