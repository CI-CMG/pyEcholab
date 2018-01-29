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

        self.missing = self._find_difference(channels, longest)

        if auto:
            if mode == 'pad':
                # create empyty 1-ping object to insert
                fill = self._create_fill(value=None)
                print(fill)

            elif mode == 'trim':
                pass
            else:
                raise ValueError('"{0}" is not a valid ping time alignment '
                                 'mode,'.format(mode))

        # print(channels[longest].ping_time[missing - 1], channel.ping_time[
        #     missing - 1])
        # print(channels[longest].ping_time[missing], channel.ping_time[missing])
        # print(channels[longest].ping_time[missing + 1],
        #       channel.ping_time[missing + 1])



    def _find_difference(self, channels, longest):
        missing = []
        for channel in channels:
            matched = np.searchsorted(channels[longest].ping_time,
                                      channel.ping_time)
            this_missing = (np.delete(np.arange(np.alen(channels[longest].
                                                   ping_time)), matched))
            missing.append(this_missing)
        return missing

    def _create_fill(self, value):

        fill = FillObject(value)

        return fill


class FillObject(sample_data):
    def __init__(self, value):
        super(FillObject, self).__init__()


    def __str__(self):
        msg = str(vars(self))
        return msg



