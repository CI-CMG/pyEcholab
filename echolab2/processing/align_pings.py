# coding=utf-8

"""
Class that takes a list of either raw data objects or processed dat objects 
and aligns data by ping time. The self.longest and self.shortest of the data objects (
number of pings) is used to either pad short objects with NaN  value "pings" 
or delete long objects to length of short object by deleting pings not found 
in short object.

"""
import numpy as np
from copy import deepcopy


class AlignPings(object):
    def __init__(self, channels, mode='pad'):
        """
        Class runs on initialization and passing of list of channels to
        align. Self.longest and self.shortest give access to the channel with
        the longest and shortest ping count. Self.missing is an array of
        arrays of ping missing in shorter objects. Self.extras is an array or
        arrays of pings on longer objects not found in shortest object

        :param channels: list of data objects. these must by channels from 
        the same reader instance
        :param mode: either 'pad' for align by padding or 'delete' for align by 
        removing pings
        """

        # Get list of ping_time sizes
        sizes = np.zeros(len(channels), 'uint64')
        try:
            for index, channel in enumerate(channels):
                sizes[index] = channel.ping_time.shape[0]
        except Exception:
            raise TypeError(' "{0}" do not contain a ping_time attribute. '
                            'Check the objects you are trying to time '
                            'align.'.format(channels))

        self.longest = sizes.argmax()
        self.shortest = sizes.argmin()

        if mode == 'pad':
            # find pings missing in shorter objects and pad shorter objects
            self.missing = self._find_missing(channels, self.longest)
            self._pad_pings(channels, self.missing, self.longest)
        elif mode == 'delete':
            # find extra pings in longer objects and delete pings
            self.extras = self._find_extra(channels, self.shortest)
            self._delete_extras(channels, self.extras)
        else:
            raise ValueError('"{0}" is not a valid ping time alignment '
                             'mode,'.format(mode))

    @staticmethod
    def _find_missing(channels, longest):
        """
        Based on ping times, for each channel find the pings that are missing
        relative to the longest channel. Channels with matching ping time
        arrays will return an empty array for that channel

        :param channels: list of sample data objects=, one for each channel
        :param longest: sample data object of chanel with most pings
        :return: array of arrays containing missing pings
        """
        missing = []
        for channel in channels:
            matched = np.searchsorted(channels[longest].ping_time,
                                      channel.ping_time)
            this_missing = (np.delete(np.arange(np.alen(channels[longest].
                                                        ping_time)), matched))

            pings = np.take(channel.ping_number, this_missing)
            missing.append(pings)

        return missing
    
    @staticmethod
    def _find_extra(channels, shortest):
        """
        Based on ping times, for each channel find the pings that are in channel
        but not in the shortest channel. Channels with matching ping time
        arrays will return an empty array for that channel

        :param channels: list of sample data objects=, one for each channel
        :param shortest: sample data object of chanel with fewest pings
        :return: array of arrays containing extra pings
        """
        extras = []
        for channel in channels:
            matched = np.searchsorted(channel.ping_time, channels[
                                          shortest].ping_time)

            this_extras = np.delete(np.arange(np.alen(channel.ping_time)),
                                    matched)

            pings = np.take(channel.ping_number, this_extras)
            extras.append(pings)

        return extras

    @staticmethod
    def _delete_extras(channels, extras):
        """
        Iterate through list of channels and use channel's (sample data
        object) delete method to delete extra pings from long channels.

        :param channels: list of sample data objects=, one for each channel
        :param extras: array of arrays containing extra pings to be deleted
        from channels
        :return: None
        """

        for index, channel in enumerate(channels):
            for ping in extras[index]:
                channel.delete(ping, ping)

    @staticmethod
    def _pad_pings(channels, missing, longest):
        """
        Iterate through list of channels. If channel is short and needs to be
        padded. Create a 1-ping long object to use as a pad and use
        channel's insert method to insert pad.

        :param channels: list of sample data objects=, one for each channel
        :param missing: array of arrays containing missing pings to be padded
        into shorter channels
        :param longest: channel sample data object from longest channel. Used
         to set ping time for padding ping
        :return: None
        """

        for index, channel in enumerate(channels):
            if len(missing[index]) > 0:
                fill = deepcopy(channel)
                fill.delete(2, )
                fill.nan_values(1, 1)
                for ping in missing[index]:
                    fill.ping_time[0] = channels[longest].ping_time[ping-1]
                    channel.insert(fill, ping_number=ping, insert_after=False)


