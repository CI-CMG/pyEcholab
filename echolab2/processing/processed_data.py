# coding=utf-8

#     National Oceanic and Atmospheric Administration (NOAA)
#     Alaskan Fisheries Science Center (AFSC)
#     Resource Assessment and Conservation Engineering (RACE)
#     Midwater Assessment and Conservation Engineering (MACE)

#  THIS SOFTWARE AND ITS DOCUMENTATION ARE CONSIDERED TO BE IN THE PUBLIC DOMAIN
#  AND THUS ARE AVAILABLE FOR UNRESTRICTED PUBLIC USE. THEY ARE FURNISHED "AS IS."
#  THE AUTHORS, THE UNITED STATES GOVERNMENT, ITS INSTRUMENTALITIES, OFFICERS,
#  EMPLOYEES, AND AGENTS MAKE NO WARRANTY, EXPRESS OR IMPLIED, AS TO THE USEFULNESS
#  OF THE SOFTWARE AND DOCUMENTATION FOR ANY PURPOSE. THEY ASSUME NO RESPONSIBILITY
#  (1) FOR THE USE OF THE SOFTWARE AND DOCUMENTATION; OR (2) TO PROVIDE TECHNICAL
#  SUPPORT TO USERS.

'''

                      CLASS DESCRIPTION GOES HERE

'''

from ..data_container import data_container


class processed_data(data_container):
    '''
    The processed_data class contains
    '''

    def __init__(self, channel_id, frequency):

        super(processed_data, self).__init__()

        #  set the frequency and channel_id
        self.channel_id = channel_id
        self.frequency = frequency

        #  sample thickness is the vertical extent of the samples in meters
        #  it is calculated as thickness = sample interval(s) * sound speed(m/s) / 2
        #  you should not append processed data arrays with different sample thicknesses
        self.sample_thickness = 0

        #  sample offset is the number of samples the first row of data are offset away from
        #  the transducer face.
        self.sample_offset = 0




    def __str__(self):
        '''
        reimplemented string method that provides some basic info about the RawData object
        '''

        #  print the class and address
        msg = str(self.__class__) + " at " + str(hex(id(self))) + "\n"

        #  print some more info about the ProcessedData instance
        n_pings = len(self.ping_time)
        if (n_pings > 0):
            msg = msg + "                channel(s): ["
            for channel in self.channel_id:
                msg = msg + channel + ", "
            msg = msg[0:-2] + "]\n"
            msg = msg + "                 frequency: " + str(self.frequency)+ "\n"
            msg = msg + "           data start time: " + str(self.ping_time[0])+ "\n"
            msg = msg + "             data end time: " + str(self.ping_time[n_pings-1])+ "\n"
            msg = msg + "           number of pings: " + str(n_pings)+ "\n"
            if (hasattr(self, 'power')):
                n_pings,n_samples = self.power.shape
                msg = msg + ("    power array dimensions: (" + str(n_pings)+ "," +
                        str(n_samples) +")\n")
            if (hasattr(self, 'angles_alongship')):
                n_pings,n_samples = self.angles_alongship.shape
                msg = msg + ("    angle array dimensions: (" + str(n_pings)+ "," +
                        str(n_samples) +")\n")
        else:
            msg = msg + ("  ProcessedData object contains no data\n")

        return msg
