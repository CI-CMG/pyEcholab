# -*- coding: utf-8 -*-
"""

"""

from matplotlib.pyplot import figure, show, subplots_adjust, get_cmap
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram



rawfiles = ['./data/EK60/DY1706_EK60-D20170625-T061707.raw','./data/EK60/DY1706_EK60-D20170625-T062521.raw']



#  create a matplotlib figure to plot our echograms on
fig = figure()

#  set some properties for the sub plot layout
subplots_adjust(left=0.075, bottom=.05, right=0.98, top=.93, wspace=None, hspace=0.5)

#  create an instance of the EK60 instrument.
ek60 = EK60.EK60()

#  read the data
ek60.read_raw(rawfiles)

raw_data_38 = ek60.get_rawdata(channel_number=2)

Sv = raw_data_38.get_sv(heave_correct=True)

angles = raw_data_38.get_physical_angles(heave_correct=True)


#  create another axes
ax_1 = fig.add_subplot(3,1,1)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_1, Sv, 'Sv', threshold=[-70,-34])
ax_1.set_title("Heave Compensated Sv")

angle_cmap = get_cmap('plasma')

#  create another axes
ax_1 = fig.add_subplot(3,1,2)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_1, angles, 'angles_alongship', cmap=angle_cmap)
ax_1.set_title("Heave Compensated angles_alongship")

#  create another axes
ax_2 = fig.add_subplot(3,1,3)
#  create an echogram which will display on our newly created axes
echogram_3 = echogram.echogram(ax_2, angles, 'angles_athwartship', cmap=angle_cmap)
ax_2.set_title("Heave Compensated angles_athwartship")


#  show our figure
show()


pass
