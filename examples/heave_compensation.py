# -*- coding: utf-8 -*-
"""

"""
import numpy as np
from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram


#  specify some raw files that have heave data and transducer depth in the raw data
rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw','./data/EK60/DY1706_EK60-D20170625-T062521.raw']

#  create a matplotlib figure to plot our echograms on
fig = figure()

#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

#  create an instance of the EK60 instrument.
ek60 = EK60.EK60()

#  read the data
ek60.read_raw(rawfiles)

#  get the 38 kHz raw data
raw_data_38 = ek60.get_rawdata(channel_number=2)

#  get a processed_data object containing the heave corrected Sv on a depth grid
heave_corrected_Sv = raw_data_38.get_sv(heave_correct=True)

#  extract a portion of the data to plot "zoomed in". We can slice processed_data objects
#  like numpy arrays. Note that slicing returns a view into the various attributes.
#  IT DOES NOT RETURN A COPY.
subset_Sv = heave_corrected_Sv[0:100,0:100]
#subset_Sv.Sv[:,80:100] = np.nan

#  create an axes
ax_1 = fig.add_subplot(2,1,1)
#  create an echogram which will display on our heave corrected data
echogram_1 = echogram.echogram(ax_1, heave_corrected_Sv, 'Sv', threshold=[-70,-34])
ax_1.set_title("heave compensated Sv on depth grid")

#  create another axes
ax_2 = fig.add_subplot(2,1,2)
#  create an echogram which will display the Sv data on a range grid
echogram_2 = echogram.echogram(ax_2, subset_Sv, 'Sv', threshold=[-70,-34])
ax_2.set_title("zoomed heave compensated Sv on depth grid")

#  show our figure
show()


pass
