# -*- coding: utf-8 -*-
"""
ek60_test

This test reads data collected using EK60 GPTs recorded using ER60
version 2.2.0.

power, Sv, Sp/TS, and angle data from 5 frequencies are compared with the
same data exported from Echoview. Ranges and ping times are also compared.
The data are also written to disk, then the re-writen data is read and
the power and angle data is compared to Echoview to ensure that the write
method is working properly.

There are a few details to note about comparing data:

Echolab returns an additional sample at a sample index 0 when reading EK60
raw files. The range of this sample is -sample_thickness. Echoview discards
this sample so comparisons are made omitting this extra sample.

The echolab and Echoview values can differ by up to 0.2 dB in the first 10-15
samples. We don't care about this and start the comparison at the 15th sample.

The read/write/read cycle can result in differences in power values between
the original file and the newly written file of up to +-0.0118 dB which is the


When the test is passing:

Power values will match Echoview values
Sv and TS values will be within +-0.0001 dB of Echoview values
Angle values will be within +-0.0001 deg. of Echoview values
Range values will match
Ping time values will match
Rewritten power data will match original within +-0.0118 dB

"""

import os
import sys
import unittest
import unittest.runner
import itertools
import numpy as np
from echolab2.instruments import echosounder
from echolab2.processing import processed_data


# Set the max absolute differences allowed between echolab and echoview
# for certain data types. For CW data, power values should match but differences
# in the implementation of the conversion methods result in minor differences
convert_atol = 1e-04
rewrite_atol = 12e-03

# For Sv and TS values, pyEcholab and Echoview differ most in the first 13 samples
# or so and so we skip comparing them.
start_sample = 13

# Specify the data files for this test

# EK80 CW Complex 38 (3 sector) + 200 (1 sector)
in_file = './data/EK60_GPT_test.raw'
out_file = './data/test_write.raw'

# Echoview power, Sv, TS, and angles data exports of above raw file
ev_Sv_filename = {}
ev_Sv_filename[18000] = './data/EK60_GPT_test_EV-18.Sv.mat'
ev_Sv_filename[38000] = './data/EK60_GPT_test_EV-38.Sv.mat'
ev_Sv_filename[70000] = './data/EK60_GPT_test_EV-70.Sv.mat'
ev_Sv_filename[120000] = './data/EK60_GPT_test_EV-120.Sv.mat'
ev_Sv_filename[200000] = './data/EK60_GPT_test_EV-200.Sv.mat'

ev_TS_filename = {}
ev_TS_filename[18000] = './data/EK60_GPT_test_EV-18.ts.csv'
ev_TS_filename[38000] = './data/EK60_GPT_test_EV-38.ts.csv'
ev_TS_filename[70000] = './data/EK60_GPT_test_EV-70.ts.csv'
ev_TS_filename[120000] = './data/EK60_GPT_test_EV-120.ts.csv'
ev_TS_filename[200000] = './data/EK60_GPT_test_EV-200.ts.csv'

ev_power_filename = {}
ev_power_filename[18000] = './data/EK60_GPT_test_EV-18.power.csv'
ev_power_filename[38000] = './data/EK60_GPT_test_EV-38.power.csv'
ev_power_filename[70000] = './data/EK60_GPT_test_EV-70.power.csv'
ev_power_filename[120000] = './data/EK60_GPT_test_EV-120.power.csv'
ev_power_filename[200000] = './data/EK60_GPT_test_EV-200.power.csv'

ev_angles_filename = {}
ev_angles_filename[18000] = './data/EK60_GPT_test_EV-18.angles.csv'
ev_angles_filename[38000] = './data/EK60_GPT_test_EV-38.angles.csv'
ev_angles_filename[70000] = './data/EK60_GPT_test_EV-70.angles.csv'
ev_angles_filename[120000] = './data/EK60_GPT_test_EV-120.angles.csv'
ev_angles_filename[200000] = './data/EK60_GPT_test_EV-200.angles.csv'


class ek60_test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        '''
        setUpClass is executed once, before all tests are conducted
        '''

        # Use echosounder.read() to read the input file and return either an
        # EK60 or EK80 object depending on what type of file is read.
        ek_data = echosounder.read(in_file)

        # We know we are reading one file so we just grab the first object
        # returned by echosounder.read()
        self.ek_data = ek_data[0]

        self.progress_index = 0

        # Store a list of our channels for convienience
        self.channels = list(self.ek_data.raw_data.keys())

        print()
        print('ek60_test: ' + in_file)


    def test_TS_conversion(self):

        for chan in self.channels:
            # Get a reference to the first data object
            raw_data = self.ek_data.raw_data[chan][0]

            # Get the frequency of this channel.
            this_freq = raw_data.frequency[0]

            ev_file = ev_TS_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the Sp data
                Sp = raw_data.get_Sp()

                # Read the Echoview export file containing TS.
                ev_TS = processed_data.read_ev_csv('', 0, ev_file, data_type='TS')

                # Compare TS values from the start sample onwards
                self.assertTrue(np.allclose(Sp[:,start_sample:], ev_TS[:,start_sample-1:],
                        atol=convert_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(Sp.range[1:], ev_TS.range[:], equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(Sp.ping_time.view(dtype=np.uint64),
                        ev_TS.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_power_conversion(self):

        for chan in self.channels:
            # Get a reference to the first data object
            raw_data = self.ek_data.raw_data[chan][0]

            # Get the frequency of this channel.
            this_freq = raw_data.frequency[0]

            ev_file = ev_power_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the power data
                power = raw_data.get_power()

                # Read the Echoview export file containing power.
                ev_power = processed_data.read_ev_csv('', 0, ev_file, data_type='power')

                # Compare power values
                self.assertTrue(np.allclose(power[:,1:], ev_power[:,:], equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(power.range[1:], ev_power.range[:], equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(power.ping_time.view(dtype=np.uint64),
                        ev_power.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_Sv_conversion(self):

        for chan in self.channels:

            # Get a reference to the first data object
            raw_data = self.ek_data.raw_data[chan][0]

            # Get the frequency of this channel. CW data will
            # have the frequency property
            this_freq = raw_data.frequency[0]

            ev_file = ev_Sv_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get Sv
                Sv = raw_data.get_Sv()

                # Read the Echoview export file containing Sv.
                ev_Sv = processed_data.read_ev_mat('', 0, ev_file, data_type='Sv')

                # Compare Sv values
                self.assertTrue(np.allclose(Sv[:,start_sample:], ev_Sv[:,start_sample-1:], atol=convert_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(Sv.range[1:], ev_Sv.range[:], equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(Sv.ping_time.view(dtype=np.uint64),
                        ev_Sv.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_angle_conversion(self):

        for chan in self.channels:

            # Get a reference to the first data object
            raw_data = self.ek_data.raw_data[chan][0]

            # Get the frequency of this channel. CW data will
            # have the frequency property
            this_freq = raw_data.frequency[0]

            ev_file = ev_angles_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the angle data
                alongship, athwartship = raw_data.get_physical_angles()

                # Read the Echoview export file containing Sv.
                ev_alongship, ev_athwartship = processed_data.read_ev_csv('', 0,
                        ev_file, data_type='angles')

                # Compare alongship and athwartship angles
                self.assertTrue(np.allclose(alongship[:,1:], ev_alongship[:,:],
                        atol=convert_atol, equal_nan=True))
                self.assertTrue(np.allclose(athwartship[:,1:], ev_athwartship[:,:],
                        atol=convert_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(alongship.range[1:], ev_alongship.range,
                        equal_nan=True))
                self.assertTrue(np.allclose(athwartship.range[1:], ev_athwartship.range,
                        equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(alongship.ping_time.view(dtype=np.uint64),
                        ev_alongship.ping_time.view(dtype=np.uint64), equal_nan=True))
                self.assertTrue(np.allclose(athwartship.ping_time.view(dtype=np.uint64),
                        athwartship.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_write_raw(self):

        # Write the raw data to disk - provide a dict to map input filename
        # to output file name so we have full control of name.
        fname = os.path.split(in_file)[1]
        out_name = {fname:out_file}
        self.ek_data.write_raw(out_name, overwrite=True)

        # The read this re-written data
        ek_rewrite = echosounder.read(out_file)
        ek_rewrite = ek_rewrite[0]

        # Get a list of the rewritten channels
        rewrite_channels = list(ek_rewrite.raw_data.keys())

        for chan in rewrite_channels:
            # Get a reference to the first data object
            raw_data = ek_rewrite.raw_data[chan][0]

            # Get the frequency of this channel.
            this_freq = raw_data.frequency[0]

            ev_file = ev_power_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the power data
                power = raw_data.get_power()

                # Read the Echoview export file containing power.
                ev_power = processed_data.read_ev_csv('', 0, ev_file, data_type='power')

                # Compare power values
                self.assertTrue(np.allclose(power[:,1:], ev_power[:,:],
                        atol=rewrite_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(power.range[1:], ev_power.range, equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(power.ping_time.view(dtype=np.uint64),
                        ev_power.ping_time.view(dtype=np.uint64), equal_nan=True))

            ev_file = ev_angles_filename.get(this_freq, None)
            if ev_file is not None:

                # Get the angle data
                alongship, athwartship = raw_data.get_physical_angles()

                # Read the Echoview export file containing angles.
                ev_alongship, ev_athwartship = processed_data.read_ev_csv('', 0,
                        ev_file, data_type='angles')

                # Compare angles
                self.assertTrue(np.allclose(alongship[:,1:], ev_alongship[:,:],
                        atol=convert_atol, equal_nan=True))
                self.assertTrue(np.allclose(athwartship[:,1:], ev_athwartship[:,:],
                        atol=convert_atol, equal_nan=True))


'''
CustomTextTestResult and CustomTextTestRunner adapted from code provided by StackOverflow
user Ken 'Joey' Mosher (https://stackoverflow.com/users/2887603/ken-joey-mosher)

https://stackoverflow.com/questions/11532882/show-progress-while-running-python-unittest
'''
class CustomTextTestResult(unittest.runner.TextTestResult):
    """Extension of TextTestResult to support numbering test cases"""

    def __init__(self, stream, descriptions, verbosity):
        """Initializes the test number generator, then calls super impl"""

        self.test_numbers = itertools.count(1)

        return super(CustomTextTestResult, self).__init__(stream, descriptions, verbosity)


    def startTest(self, test):
        """Writes the test number to the stream if showAll is set, then calls super impl"""

        if self.showAll:
            progress = '[{0}/{1}] '.format(next(self.test_numbers), self.test_case_count)
            self.stream.write(progress)
            test.progress_index = progress

        return super(CustomTextTestResult, self).startTest(test)


    def _exc_info_to_string(self, err, test):
        """Gets an exception info string from super, and prepends 'Test Number' line"""

        info = super(CustomTextTestResult, self)._exc_info_to_string(err, test)

        if self.showAll:
            if hasattr(test, 'progress_index'):
                info = 'Test number: {index}\n{info}'.format(index=test.progress_index,
                        info=info)
            else:
                info = 'Error in Setup:\n{info}'.format(info=info)

        return info


class CustomTextTestRunner(unittest.runner.TextTestRunner):
    """Extension of TextTestRunner to support numbering test cases"""

    resultclass = CustomTextTestResult

    def run(self, test):
        """Stores the total count of test cases, then calls super impl"""

        self.test_case_count = test.countTestCases()
        return super(CustomTextTestRunner, self).run(test)

    def _makeResult(self):
        """Creates and returns a result instance that knows the count of test cases"""

        result = super(CustomTextTestRunner, self)._makeResult()
        result.test_case_count = self.test_case_count
        return result


if __name__ == "__main__":

    test_funcs = ['test_power_conversion', 'test_Sv_conversion', 'test_TS_conversion',
            'test_angle_conversion', 'test_write_raw']

    test_suite = unittest.TestSuite()
    tests = [ek60_test(func) for func in test_funcs]
    test_suite.addTests(tests)

    CustomTextTestRunner(verbosity=2).run(test_suite)

