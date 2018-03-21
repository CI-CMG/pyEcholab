# -*- coding: utf-8 -*-
"""
This is an example exercising the masks.
"""

from matplotlib.pyplot import figure, show, subplots_adjust
from echolab2.instruments import EK60
from echolab2.plotting.matplotlib import echogram
from echolab2.processing import mask


#  read in some data
rawfiles = ['./data/EK60/PC1106-D20110830-T052815.raw',
            './data/EK60/PC1106-D20110830-T053815.raw']

ek60 = EK60.EK60()
ek60.read_raw(rawfiles)

#  get a reference to the raw_data object
raw_data_38 = ek60.get_raw_data(channel_number=2)
print(raw_data_38)

#  get a processed_data object containing Sv
Sv = raw_data_38.get_Sv()
print(Sv)

#  create a copy of Sv to compare against the copy we will manipulate
orig_Sv = Sv.copy()

#  create a couple of masks. Masks come in two types. "Ping" masks are 1d masks
#  that apply to all samples in a ping while "sample" masks are 2d and apply
#  to the individual sample data elements.

#  mask objects are comprised of either a 2d or 1d boolean array and 1 or 2 1d arrays
#  containing the axes for the array. When applying masks, the axes are checked
#  against the axes of the object you're applying the mask to and they must be the
#  same. Because of this, most of the time you will create a mask that is "like" an
#  existing processed data object which results in the mask array being sized
#  correctly for the processed_data object and the axes are copied from the
#  processed_data object and thus are the same.

#  the default behavior of the constructor is to create a sample mask so we'll
#  create a sample mask that is like our "Sv" processed_data object.
sample_mask = mask.mask(like=Sv)
print(sample_mask)

#  masks are by default created with all elements set to "False". You can use the
#  value keyword of the constructor to set it to True if you so desire.

#  create a ping mask like Sv - setting all values to True
ping_mask = mask.mask(like=Sv, type='ping', value=True)
print(ping_mask)

#  masks can be used on their own to present data (though mask plotting isn't
#  implemented yet) or more commonly used as a logical index array to operate on
#  specific samples in a processed_data object. Since mask plotting isn't
#  implemented we'll focus on the second, more common use.

#  At the most basic level, setting mask elements to True will specify that
#  an operation occurs on that element. For example, if we wanted to set
#  a block of samples between sample 50 and 800 from ping 20-500 to -999
#  we could set those mask values to True and then use the mask to "index"
#  into our processed_data object Sv
sample_mask.mask[20:500, 50:800] = True

#  now use the mask to set these samples to -999
Sv[sample_mask] = -999

#  and display the results
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98,
        top=.90, wspace=None, hspace=0.5)

#  plot up the original data
ax1 = fig.add_subplot(2,1,1)
eg = echogram.echogram(ax1, orig_Sv, threshold=[-70,-34])
ax1.set_title("Original Sv Data")

#  and the data we just modified
ax2 = fig.add_subplot(2,1,2)
eg = echogram.echogram(ax2, Sv, threshold=[-70,-34])
ax2.set_title('Modified Sv data')

#  show the results
show()

#  but that's not really how you would use a mask since you can
#  set rectangular regions directly by slicing the processed_data
#  object. Thresholding is a more realistic example of using a
#  mask.

#  using Python comparison operators with processed_data objects
#  will return masks so thresholding is as simple as using <, >
#  <=, >=, etc.

Sv = orig_Sv.copy()

#  The comparison operators work on scalars - create 3 masks each
#  with a different threshold
mask_1 = Sv < -70
mask_3 = Sv > -25

#  you can apply boolean operators to masks as well which also
#  returns a mask. Just make sure you group the operations
#  properly.
mask_2 = (Sv >= -50) & (Sv <= -25)

#  instead of using the masks to set values in the original Sv
#  object let's create a processed_data object that is a copy
#  of Sv with the sample data set to zeros
synth_data = Sv.zeros_like()

#  now set the values in our new processed_data object
synth_data[mask_1] = 0
synth_data[mask_2] = 10
synth_data[mask_3] = 15

#  and display the results
fig = figure()
subplots_adjust(left=0.075, bottom=.05, right=0.98,
        top=.90, wspace=None, hspace=0.5)

#  plot up the original data
ax1 = fig.add_subplot(2,1,1)
eg = echogram.echogram(ax1, orig_Sv, threshold=[-70,-34])
ax1.set_title("Original Sv Data")

#  and the data we just modified
ax2 = fig.add_subplot(2,1,2)
eg = echogram.echogram(ax2, synth_data, threshold=[0,20])
ax2.set_title('Threshold results')

#  show the results
show()

