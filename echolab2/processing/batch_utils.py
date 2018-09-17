# -*- coding: utf-8 -*-


import os
import re
from datetime import datetime, timedelta


class FileAggregator(object):
    """This class provides a time sorted list of files.

    This class returns an object containing a time sorted list of files with
    filename and datetime timestamp for use in batch processing of files. A
    list of lists with files aggregated by time interval is also available.

    Attributes:
        regex: A string pattern used to parse date and time information from
            a filename.
        format: A string datetime format the filename contains.
        file_list: A list of files.
        file_bins: A list of file lists based on a specified time interval.
    """
    def __init__(self, source_dir, interval=60, extension='.raw',
                 regex='D\d{8}-T\d{6}', time_format='D%Y%m%d-T%H%M%S'):

        self.pattern = re.compile(regex, re.IGNORECASE)
        self.format = time_format

        self.file_list = self.sort_files(source_dir, extension)
        self.file_bins = self.bin_files(interval)

    def _get_timestamp(self, item):
        """Parses the timestamp from files.

        This method parses date and time elements from the filename for use in
        sorting based on the time recorded in the filename.

        Args:
            item (str): The file path to be parsed.

        Return:
            The timestamp from the filename.
        """
        raw = self.pattern.search(item).group()
        timestamp = datetime.strptime(raw, self.format)

        return timestamp

    def sort_files(self, source_dir, extension):
        """Sorts files.

        This class sorts files in a specified directory based on timestamps
        parsed from filenames.

        Args:
            source_dir (str): The directory containing the files.
            extension (str): The file extension of the data files.

        Returns:
            A sorted list of files.
        """

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
        """Creates bins of files.

        This method bins files based on the time interval specified.  The start
        time of the file is used for this process.  The result is a list of
        file lists (bins).

        Args:
            interval (int): A number of minutes to bin the files by.

        Returns:
            A list of binned files.
        """
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
        # Add last remaining bin of files.
        binned_files.append(current_bin)

        return binned_files

