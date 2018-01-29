# -*- coding: utf-8 -*-
"""
This is Chuck's personal testing script. It could well be in an unhappy
state. It's in the repo so I can access it at home and work without needing a
separate branch. You are happy to test this script but please don't change
it. thanks...Chuck
"""

import os
import re
from datetime import datetime, timedelta


class FileAggregator(object):
    """
    Class that returns an object containing an time sorted list of files with
    file name and datetime timestamp for use in batch processing of files. A
    list of lists with files aggregated by time interval is also available,
    """
    def __init__(self, source_dir, interval=60, extension='.raw',
                 regex='D\d{8}-T\d{6}', time_format='D%Y%m%d-T%H%M%S'):

        self.regex = regex
        self.format = time_format

        self.file_list = self.sort_files(source_dir, extension)
        self.file_bins = self.bin_files(interval)

    def _get_timestamp(self, item):
        """
        Parses date and time elements from filename for use in sorting based
        on time recorded in filename

        :param item: file path
        :return: timestamp: datetime timestamp
        """

        pattern = re.compile(self.regex, re.IGNORECASE)
        raw = pattern.search(item).group()
        timestamp = datetime.strptime(raw, self.format)

        return timestamp

    def sort_files(self, source_dir, extension):

        raw_files = []
        for files in os.walk(source_dir):
            for file in files[2]:
                raw_files.append(files[0] + os.sep + file)

        raw_list = [file for file in raw_files if
                    (os.path.splitext(file)[1] == extension)]

        file_list = []
        for file in raw_list:
            file_list.append((file, self._get_timestamp(file)))

        return sorted(file_list, key=lambda item: item[1])

    def bin_files(self, interval):
        delta = timedelta(minutes=interval)
        binned_files = []
        bin_start = self.file_list[0][1]
        current_bin = []
        for file in self.file_list:
            if file[1] < bin_start + delta:
                current_bin.append(file[0])
            else:
                binned_files.append(current_bin)
                current_bin = []
                bin_start = file[1]
                current_bin.append(file[0])
        # add last remaining bin of files
        binned_files.append(current_bin)

        return binned_files

