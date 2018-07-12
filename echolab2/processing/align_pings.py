# coding=utf-8

"""
Class that takes a list of either raw data objects or processed dat objects 
and aligns data by ping time. The self.longest and self.shortest of the data objects (
number of pings) is used to either pad short objects with NaN  value "pings" 
or delete long objects to length of short object by deleting pings not found 
in short object.

"""
import numpy as np
from .processed_data import ProcessedData


class AlignPings(object):
    def __init__(self, channels, mode='pad'):
        """
        Class runs on initialization and passing of list of channels to
        align. Self.longest and self.shortest give access to the channel with
        the longest and shortest ping count. Self.missing is an array of
        arrays of ping missing in shorter objects. Self.extras is an array or
        arrays of pings on longer objects not found in shortest object

        Args:
            channels: list of data objects. these must by channels from
                      the same reader instance
            mode: either 'pad' for align by padding or 'delete' for align by
                  removing pings

        Returns: None
        """

        self.details = {}

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
            if self._need_alignment(self.missing):
                self._pad_pings(channels, self.missing, self.longest)
        elif mode == 'delete':
            # find extra pings in longer objects and delete pings
            self.extras = self._find_extra(channels, self.shortest)
            if self._need_alignment(self.extras):
                self._delete_extras(channels, self.extras)
        else:
            raise ValueError('"{0}" is not a valid ping time alignment '
                             'mode,'.format(mode))

        self.get_details(channels, mode)

    def get_details(self, channels, mode):
        """
        Helper method to create an details attribute that contains details of
        aligning process.

        Args:
            channels: List of processed data objects
            mode: operation mode, 'pad or 'delete

        Returns: None

        """
        if mode == 'pad':
            counts = self.missing
        elif mode == 'delete':
            counts = self.extras

        for index, channel in enumerate(channels):
            percent = round((len(counts[index])/channel.n_pings)*100, 2)
            if percent > 0 and mode == 'pad':
                self.details[channel.channel_id[0]] = {'added pings':
                                                       self.missing[index],
                                                       'percent': percent}
            elif percent > 0 and mode == 'delete':
                self.details[channel.channel_id[0]] = {'deleted pings':
                                                       self.extras[index],
                                                       'percent': percent}

    @staticmethod
    def _find_missing(channels, longest):
        """
        Based on ping times, for each channel find the pings that are missing
        relative to the longest channel. Channels with matching ping time
        arrays will return an empty array for that channel

        Args:
            channels: list of sample data objects=, one for each channel
            longest: sample data object of chanel with most pings

        Returns: array of arrays containing missing ping times
        """

        missing = []
        for channel in channels:
            matched = np.searchsorted(channels[longest].ping_time,
                                      channel.ping_time)
            this_missing = (np.delete(np.arange(np.alen(channels[longest].
                                                        ping_time)), matched))

            # to get ping time of missing pings, use index of missing ping
            # numbers and pull time from longest channel
            pings = np.take(channels[longest].ping_time, this_missing)

            missing.append(pings)

        return missing
    
    @staticmethod
    def _find_extra(channels, shortest):
        """
        Based on ping times, for each channel find the pings that are in channel
        but not in the shortest channel. Channels with matching ping time
        arrays will return an empty array for that channel

        Args:
            channels: list of sample data objects=, one for each channel
            shortest: sample data object of chanel with fewest pings

        Returns: array of arrays containing extra pings
        """

        extras = []
        for channel in channels:
            matched = np.searchsorted(channel.ping_time, channels[
                                          shortest].ping_time)

            this_extras = np.delete(np.arange(np.alen(channel.ping_time)),
                                    matched)
            # to get ping time of extra pings, use index of extras to get
            # ping time from channel.ping_time
            pings = np.take(channel.ping_time, this_extras)

            extras.append(pings)

        return extras

    @staticmethod
    def _need_alignment(array_list):
        """
        Determine if there are any channels that have extra or missing pings.
        Return true when first non-zero array is hit. Otherwise return false
        because there is nothing to align.

        Args:
            array_list: List of arrays, one for each channel, that are either
                        empty or contain the ping times or extra or missing
                        pings.

        Returns: True or False

        """
        for array in array_list:
            if array.size > 0:
                return True

        return False

    @staticmethod
    def _delete_extras(channels, extras):
        """
        Iterate through list of channels and use channel's (sample data
        object) delete method to delete extra pings from long channels
        .
        Args:
            channels: list of sample data objects=, one for each channel
            extras: array of arrays containing extra pings to be deleted
                    from channels

        Returns: none

        """

        for index, channel in enumerate(channels):
            for ping in extras[index]:
                channel.delete(start_time=ping, end_time=ping)

    def _pad_pings(self, channels, missing, longest):
        """
        Iterate through list of channels. If channel is short and needs to be
        padded. Create a 1-ping long object to use as a pad and use
        channel's insert method to insert pad.

        Args:
            channels: list of sample data objects=, one for each channel
            missing: array of arrays containing missing pings to be padded
                     into shorter channels
            longest: channel sample data object from longest
                     channel. Used to set ping time for padding ping

        Returns: None
        """
        for index, channel in enumerate(channels):
            if len(missing[index]) > 0:
                fill = channels[index].empty_like(n_pings=1, empty_times=True)
                for ping in missing[index]:
                    fill.ping_time[0] = ping
                    idx = np.where(channels[longest].ping_time == ping)[0][0]
                    insert_time = channels[longest].ping_time[idx-1]
                    channel.insert(fill, ping_time=insert_time)
