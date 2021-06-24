 # coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS
#  IS." THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES,
#  OFFICERS, EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED,
#  AS TO THE USEFULNESS OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE.
#  THEY ASSUME NO RESPONSIBILITY (1) FOR THE USE OF THE SOFTWARE AND
#  DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL SUPPORT TO USERS.

"""

| Original code developed by:  Nathan Lauffenburger  <nathan.lauffenburger@noaa.gov>
|                              Rick Towler   <rick.towler@noaa.gov>
| National Oceanic and Atmospheric Administration (NOAA)
| Alaska Fisheries Science Center (AFSC)
| Midwater Assessment and Conservation Engineering Group (MACE)
|
| Author:
|       Rick Towler             <rick.towler@noaa.gov>
|       Nate Lauffenburger      <nathan.lauffenburger@noaa.gov>
| Maintained by:
|       Rick Towler             <rick.towler@noaa.gov>
|       Nate Lauffenburger      <nathan.lauffenburger@noaa.gov>

"""

import numpy as np
from ..ping_data import ping_data
from ..processing import line
from ..processing import processed_data


class afsc_bot_detector(ping_data):
    """
    The afsc_bot_detector class implements a simple amplitude based bottom detection
    algorithm. It was written mainly as an example and will need to be developed further
    if you're looking for a robust bottom pick solution.

    To use, you instantiate an instance setting your bottom deteciton parameters,
    then call the detect method passing in a processed_data object containing the
    data you want a bottom pick from. The detect method will return a line object
    containing the bottom values. If your processed data object is range based, your
    bottom will be range based. If it is depth based, your bottom will be depth based.

    One big caveat of this detector is that it is range/depth agnostic and can also
    be applied to heave compensated data. This makes defining the "minimum detection
    range" problematic. Some thought shoud be put into how bottom detection should
    best be done with processed data objects when one wants to ultimately end up
    with data on a depth grid that may be heave compensated.

    Attributes:

        search_min -  the minimum range/depth that we'll consider searching for the max Sv. Set
                           this to a value that will put the search beyond the range of the ringdown.
        window_len -  the width of the Hanning window (smoothing window)
        backstep    - the backstep in the appropriate units. This value is subtracted from the
                          max Sv/sv and the result is used to specify the bounds of the echo envelope

    """

    def __init__(self, search_min=10, window_len=11, backstep=35, ratio_threshold=5):
        """Initializes afsc_bot_detector object and sets several internal properties.
        """
        super(afsc_bot_detector, self).__init__()

        #  specify the minimum range OR depth that we'll consider searching for the max Sv/sv. Set
        #  this to a value that will put the search beyond the range/depth of the ringdown.
        self.search_min = search_min

        #  specify the width of the Hanning window (smoothing window)
        self.window_len = window_len

        #  specify the backstep in the appropriate units. This value is subtracted from the max
        #  Sv/sv and the result is used to specify the bounds of the echo envelope we plot
        self.backstep = backstep
        
        # specify the maximum acceptible percent change in range/depth from ping to ping
        # for detecting false bottoms or drop outs.
        self.ratio_threshold=ratio_threshold

    def detect(self, p_data, search_max=9999):
        '''
        p_data - an instance of a processed data object that contains the data to
        perform the bottom detection on. The default parameters assume this will be an
        object that contains Sv data
        '''

        #  do a quick type check to make sure we have a processed_data object
        if not isinstance(p_data, processed_data.processed_data):
            raise TypeError('You must pass a ProcessedData object to this method.')

        #  get the vertical axis data and the type (range or depth) from the processed_data object.
        v_axis, v_axis_type = p_data.get_v_axis()

        #  create the line object we'll return - note here the use of empty_like which will create
        #  an empty (NaN) line with ping times that match the processed_data object.
        bot_line = line.empty_like(p_data)
        
        # initialize number for checking on large bottom changes due to false bottoms or drop outs
        bad_count=0
        last_good_samp=[]
        change_save=[]

        #  check if we have any data beyond our min_depth
        if not np.any(v_axis > self.search_min):
            #  there are no data beyond our minumum detection range - there is nothing to do
            return bot_line

        #  now iterate through our pings to perform a simple bottom detection
        this_ping = 0
        
        for ping in p_data:
                
            #  skip pings that don't have at least some samples with data
            if (not np.all(np.isnan(ping))):

                # determine indices in the vertical axis that satisfy the min and max search
                search_ind=np.logical_and(v_axis > self.search_min, v_axis < search_max)
                
                #  determine the maximum Sv beyond the specified minimum range
                max_Sv = np.nanmax(ping[search_ind])

                #  smooth ping
                hanning_window = np.hanning(self.window_len)
                smoothed_ping = np.convolve(hanning_window/hanning_window.sum(), ping, mode='same')

                #  determine the maximum Sv of the smoothed ping
                max_Sv_smoothed = np.nanmax(smoothed_ping[search_ind])

                #  get the sample number at the max (index)
                sample_max = np.nanargmax(smoothed_ping == max_Sv_smoothed)
                    
                #  calculate the threshold that will define the lower bound (in Sv) of our echo envelope.
                threshold = max_Sv - self.backstep

                #  get the echo envelope
                temp_data = self.get_echo_envelope(smoothed_ping, sample_max, threshold,
                        v_axis, search_ind, contiguous=True)
                        
                # check to see if this ping is within the bounds of maximum change
                # if it isn't, tag it as bad and continue until one appears within the percent change
                # once a ping within bounds is found, backfill with interpolated values from last to current
                if not this_ping:
                    last_good_samp=temp_data
                else:
                    min_samp=last_good_samp*(1-((bad_count+1)*self.ratio_threshold/np.float(100)))
                    max_samp=last_good_samp*(1+((bad_count+1)*self.ratio_threshold/np.float(100)))
                    if temp_data>min_samp and temp_data<max_samp:
                        if bad_count:
                            fix_range=np.arange(this_ping-bad_count, this_ping)
                            bot_line.data[fix_range]=np.interp(fix_range, [this_ping-bad_count-1, this_ping], [last_good_samp, temp_data])
                        last_good_samp=temp_data
                        bad_count=0                            
                    else:
                        bad_count += 1
                    
                
                # Compute the percent change of depth by ping for the last 5 pings if a variable backstep is choosen
                running_ave_size=5
                change_threshold=0.5
                ave_data=[]
                if this_ping>running_ave_size-1:
                    ave_data=np.append(bot_line.data[this_ping-running_ave_size:this_ping], temp_data)
                    change=-np.mean(np.diff(ave_data)*100/ave_data[0:-1])
                    change_save.append(change)
                    # If it is above threshold specified for change, apply an extra backstep
                    if abs(change)>change_threshold:
                        threshold = max_Sv - self.backstep*1
                        
                        #  get the echo envelope
                        temp_data = self.get_echo_envelope(smoothed_ping, sample_max, threshold,
                            v_axis, search_ind, contiguous=True)
                
                
                bot_line.data[this_ping]=temp_data
            #  increment the ping index
            this_ping += 1

        return bot_line,  change_save



    def get_echo_envelope(self, data, echo_peak, threshold,
            range_vector, search_ind, contiguous=True):
        '''
        get_echo_envelope calculates the near and far edges of an echo defined by
        the provided peak sample value and a threshold value. You must also provide
        the ping vector, sample vector, and range vector.

        '''
        #  calculate the lower search bound - usually you will at least want to avoid the ringdown and maximum search bound
        lower_bound = np.nanargmax(search_ind)

        if lower_bound == echo_peak:
            min_range = 0
        else:
            #  then find the lower bound of the envelope
            near_envelope_samples = (echo_peak - np.squeeze(np.where(data[echo_peak:lower_bound:-1] > threshold)))

            # Determine if there are any samples below the threshold within the near envelope.
            # If there is, choose the first one
            if contiguous:
                sample_diff = np.where(np.diff(near_envelope_samples) < -1)
                if (sample_diff[0].size > 0):
                    min_idx = np.min(sample_diff)
                    min_sample = near_envelope_samples[min_idx]
                else:
                    min_sample = near_envelope_samples[-1]
            else:
                min_sample = near_envelope_samples[-1]

            sv_diff=np.diff(data[near_envelope_samples])
            q_ind=near_envelope_samples[np.where(sv_diff>0)]-1
            #  and the next one
            previous_sample = min_sample - 1

            #  calculate the interpolated range for our near envelope edge
            min_range = np.interp(threshold, [data[previous_sample], data[min_sample]],
                                     [range_vector[previous_sample], range_vector[min_sample]])

        return min_range
