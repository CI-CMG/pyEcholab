# coding=utf-8

"""
Time align pings
"""
import numpy as np
from ..sample_data import sample_data

class AlignPings(object):
    def __init__(self, channels, mode='pad', auto=True):

        # Get list of ping_time sizes
        sizes = np.zeros(len(channels), 'uint64')

        try:
            for index, channel in enumerate(channels):
                sizes[index] = channel.ping_time.shape[0]
        except Exception:
            raise TypeError(' "{0}" does not contain ping_time attribute. '
                            'Check the objects you are trying to time '
                            'align.'.format(channel))

        longest = sizes.argmax()
        shortest = sizes.argmin()
        self._find_extra(channels, shortest)

        if auto:
            if mode == 'pad':
                missing = self._find_missing(channels, longest)
            elif mode == 'trim':
                extras = self._find_extra(channels, shortest)
                self._delete_extras(channels, extras)

            else:
                raise ValueError('"{0}" is not a valid ping time alignment '
                                 'mode,'.format(mode))

    @staticmethod
    def _find_missing(channels, longest):
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
        for index, channel in enumerate(channels):
            for ping in extras[index]:
                channel.delete(ping, ping)


    def _create_fill(self, value):

        fill = FillObject(value)

        return fill


class FillObject(sample_data):
    def __init__(self, value):
        super(FillObject, self).__init__()


    def __str__(self):
        msg = str(vars(self))
        return msg



