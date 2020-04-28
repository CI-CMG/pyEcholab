# -*- coding: utf-8 -*-
"""


@author: rick.towler

This is a simple script to plot up the differences between pyEcholab outputs
and outputs created by the MATLAB based echolab toolbox using a common raw file
as input.



"""
import sys
sys.path.append('C:/Users/rick.towler/Work/AFSCGit/pyEcholab')

from echolab2.instruments import EK80
import echolab2.processing.processed_data as processed_data
from echolab2.plotting.matplotlib import echogram
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.pyplot import figure, show


#  define the paths to the reference data files
raw_filename = 'C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004.raw'
ev_Sv_filename = 'C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004-38kHz-Sv.mat'
ev_Ts_filename = 'C:/EK80 Test Data/EK80/CW/reduced/DY2000_EK80_Cal-D20200126-T061004-38kHz-Ts.ts.csv'

#raw_filename = 'C:/EK80 Test Data/EK60/DY1803-D20180312-T212915.raw'
#ev_filename = 'C:/EK80 Test Data/EK60/DY1803-D20180312-T212915-38kHz-Sv.mat'


#  read in the .raw data file
print('Reading the raw file %s' % (raw_filename))
ek80 = EK80.EK80()
ek80.read_raw(raw_filename)

#  get the 38kHz data
raw_38 = ek80.raw_data[ek80.channel_ids[0]]
#  take the first data type
raw_data = raw_38[0]

#  get a cal object populated with params from the raw_data object
calibration = raw_data.get_calibration()

#  convert to Sv
ek80_Sv = raw_data.get_Sv(calibration=calibration)

#  and convert to Ts
ek80_Ts = raw_data.get_Sp(calibration=calibration)

fig = figure()
eg = echogram.Echogram(fig, ek80_Sv, threshold=[-70,-34])
eg.axes.set_title("Echolab2 Sv")


fig5 = figure()
eg5 = echogram.Echogram(fig5, ek80_Ts, threshold=[-70,-34])
eg5.axes.set_title("Echolab2 Ts")




#  read in the echoview data - we can read .mat files exported
#  from EV 7+ directly into a processed_data object
ev_Sv_data = processed_data.read_ev_mat('EV Sv 38 kHz', 38000., ev_Sv_filename)

#  we can also read in .csv formatted files
ev_Ts_data = processed_data.read_ev_csv('EV Ts 38 kHz', 38000., ev_Ts_filename)

fig2 = figure()
eg2 = echogram.Echogram(fig2, ev_Sv_data, threshold=[-70,-34])
eg2.axes.set_title("Echoview Sv")

fig6 = figure()
eg6 = echogram.Echogram(fig6, ev_Ts_data, threshold=[-70,-34])
eg6.axes.set_title("Echoview Ts")

#  compute the difference of these data
diff = ek80_Sv - ev_Sv_data
fig3 = figure()
eg3 = echogram.Echogram(fig3, diff, threshold=[-1,1])
eg3.axes.set_title("Sv Difference")

#  compute the difference of these data
diff = ek80_Ts - ev_Ts_data
fig4 = figure()
eg4 = echogram.Echogram(fig4, diff, threshold=[-1,1])
eg4.axes.set_title("Ts Difference")

# Show our figures.
show()



#ev_ping = ev_data['Data_values'][10,:]
#fig = plt.plot(np.arange(ev_ping.shape[0]), ev_ping, label='Echoview', color='blue', linewidth=2)
#fig = plt.plot(np.arange(echolab2_Sv.data[10,1:].shape[0]), echolab2_Sv.data[10,1:], label='pyEcholab2', color='red')
#plt.legend()
#plt.show(block=True)

