# coding=utf-8
"""
Chuck Anderson NCEI
"""
import numpy as np


class AlignPings(object):
    def __init__(self, channels, mode='pad'):
        """
        Aligns pings across data objects passed into the class

        Class runs on initialization and passing of list of channels to
        align. Self.longest and self.shortest give access to the channel with
        the longest and shortest ping count. Self.missing is an array of
        arrays of ping missing in shorter objects. Self.extras is an array or
        arrays of pings on longer objects not found in shortest object

        Args:
            channels (list): List of sample data objects. These must by
            channels from the same reader instance.
            mode (str): Either 'pad' for align by padding or 'delete' for
                align by removing pings.
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
            self._pad_pings(channels, self.missing)
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
        Find pings in channels that are missing relative to teh channel with
        the most pings.

        Based on ping times, for each channel find the pings that are missing
        relative to the longest channel. Channels with matching ping time
        arrays will return an empty array for that channel

        :param channels: list of sample data objects=, one for each channel
        :param longest: sample data object of chanel with most pings
        :return: array of arrays containing missing pings

        Args:
            channels (list):  List of sample data objects that was passed
                into class.
            longest (int): Index in channels for channel with the most pings.

        Returns: A list of Numpy arrays containing missing pings.

        """
        missing = []
        for channel in channels:
            matched = np.searchsorted(channels[longest].ping_time,
                                      channel.ping_time)
            this_missing = (np.delete(np.arange(np.alen(channels[longest].
                                                        ping_time)), matched))
            missing.append(this_missing)
        return missing
    
    @staticmethod
    def _find_extra(channels, shortest):
        """
        Find pings in channels that are not found in the channel with the
        fewest pings.

        Based on ping times, for each channel find the pings that are in channel
        but not in the shortest channel. Channels with matching ping time
        arrays will return an empty array for that channel

        Args:
            channels (list):  List of sample data objects that was passed
                into class.
            shortest (int): Index in channels for channel with the fewest
                pings.

        Returns:  A list of Numpy arrays containing extra pings.

        """
        extras = []
        for channel in channels:
            matched = np.searchsorted(channel.ping_time, channels[
                                          shortest].ping_time)

            this_extras = np.delete(np.arange(np.alen(channel.ping_time)),
                                    matched)
            extras.append(this_extras)
        return extras

    @staticmethod
    def _delete_extras(channels, extras):
        """
        Delete extra pings from long channels.

        Iterate through list of channels and use channel's (sample data
        object) delete method to delete extra pings from long channels.

        Args:
            channels (list):  List of sample data objects that was passed
                into class.
            extras (list): A list of Numpy arrays containing extra pings.

        """
        for index, channel in enumerate(channels):
            channel.delete(index_array=extras[index])

    def _pad_pings(self, channels, missing):
        """
        Insert empty pings into short channels.

        Iterate through list of channels. If channel is short and needs to be
        padded. Create a 1-ping long object to use as a pad and use
        channel's insert method to insert pad.

        Args:
            channels (list): List of sample data objects that was passed
                into class.
            missing (list): A list of Numpy arrays containing extra pings.
        """
        for index, channel in enumerate(channels):
            if len(missing[index]) > 0:
                times = channels[self.longest].ping_time[missing[index]]
                fill = channels[index].empty_like(times.size)
                fill.ping_time[0:] = times
                channel.insert(fill, index_array=missing[index])



