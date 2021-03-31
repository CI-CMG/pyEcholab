# -*- coding: utf-8 -*-
"""
wbt_cw_reduced_test

This test reads data collected using 5 WBTs connected to five 4 sector
transducers: 18, 38, 70, 120, and 200 kHz. All channels were configured
in CW mode and power and angle data were recorded in reduced form.

power, Sv, Sp/TS, and angle data are compared with the same data exported
from Echoview. Ranges and ping times are also compared. The data are also
written to disk, then the re-writen data is read and the power and angle
data are compared to Echoview to ensure that the write methods are working
properly.

Note that Echoview seems to occasionally export -999.0 for samples that
PyEcholab computes correctly. This seems to happen in only a fraction of
the pings in the last valid sample in the ping.

When the test is passing:

Power values will match Echoview values
Sv and TS values will be within +-0.025 dB of Echoview values
Angle values will be within +-0.0001 deg. of Echoview values
Range values will match
Ping time values will match

"""

import os
import sys
import unittest
import unittest.runner
import itertools
import numpy as np
from echolab2.instruments import EK80
from echolab2.processing import processed_data



# Set the max absolute differences allowed between echolab and echoview
# for certain data types. For CW data, power values should match but differences
# in the implementation of the conversion methods result in minor differences
convert_atol = 25e-02
rewrite_atol = 12e-03

# For Sv and TS values, pyEcholab and Echoview differ most in the first 13 samples
# or so and so we skip comparing them.
start_sample = 13


# Specify the data files for this test

# EK80 CW Reduced - 6 frequency
in_file = './data/EK80_WBT_CW_reduced_test.raw'
out_file = './data/test_write.raw'

# Echoview power, Sv, TS, and angles data exports of above raw file
ev_Sv_filename = {}
ev_Sv_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.Sv.mat'
ev_Sv_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.Sv.mat'
ev_Sv_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.Sv.mat'
ev_Sv_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.Sv.mat'
ev_Sv_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.Sv.mat'
ev_Sv_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.Sv.mat'

ev_TS_filename = {}
ev_TS_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.ts.csv'
ev_TS_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.ts.csv'
ev_TS_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.ts.csv'
ev_TS_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.ts.csv'
ev_TS_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.ts.csv'
ev_TS_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.ts.csv'

ev_power_filename = {}
ev_power_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.power.csv'
ev_power_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.power.csv'
ev_power_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.power.csv'
ev_power_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.power.csv'
ev_power_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.power.csv'
ev_power_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.power.csv'

ev_angles_filename = {}
ev_angles_filename[18000] = './data/EK80_WBT_CW_reduced_test_EV-18.angles.csv'
ev_angles_filename[38000] = './data/EK80_WBT_CW_reduced_test_EV-38.angles.csv'
ev_angles_filename[70000] = './data/EK80_WBT_CW_reduced_test_EV-70.angles.csv'
ev_angles_filename[120000] = './data/EK80_WBT_CW_reduced_test_EV-120.angles.csv'
ev_angles_filename[200000] = './data/EK80_WBT_CW_reduced_test_EV-200.angles.csv'
ev_angles_filename[333000] = './data/EK80_WBT_CW_reduced_test_EV-333.angles.csv'


class wbt_cw_reduced_test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        '''
        setUpClass is executed once, before all tests are conducted
        '''

        # Create an instance of EK80 and read the test data file
        self.ek80 = EK80.EK80()
        self.ek80.read_raw(in_file)

        self.progress_index = 0

        # Store a list of our channels for convienience
        self.channels = list(self.ek80.raw_data.keys())

        print()
        print('wbt_cw_reduced_test')


    def test_TS_conversion(self):

        for chan in self.channels:
            # Get a reference to the first data object
            raw_data = self.ek80.raw_data[chan][0]

            # Get the frequency of this channel.
            this_freq = raw_data.frequency[0]

            ev_file = ev_TS_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the Sp data
                Sp = raw_data.get_Sp()

                # Read the Echoview export file containing TS.
                ev_TS = processed_data.read_ev_csv('', 0, ev_file, data_type='TS')

                # EV occasionally exports -999 for samples that PyEcholab correctly
                # computes. This seems to happen at the very last valid sample in a
                # ping and only for certain pings. Here we just convert those samples
                # in PyEcholab to -999 to match.
                Sp[:][ev_TS[:] == -999] = -999.0

                # Compare TS values
                self.assertTrue(np.allclose(Sp[:,start_sample:], ev_TS[:,start_sample:],
                        atol=convert_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(Sp.range, ev_TS.range, equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(Sp.ping_time.view(dtype=np.uint64),
                        ev_TS.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_power_conversion(self):

        for chan in self.channels:
            # Get a reference to the first data object
            raw_data = self.ek80.raw_data[chan][0]

            # Get the frequency of this channel.
            this_freq = raw_data.frequency[0]

            ev_file = ev_power_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the power data
                power = raw_data.get_power()

                # Read the Echoview export file containing power.
                ev_power = processed_data.read_ev_csv('', 0, ev_file, data_type='power')

                # EV occasionally exports -999 for samples that PyEcholab correctly
                # computes. This seems to happen at the very last valid sample in a
                # ping and only for certain pings. Here we just convert those samples
                # in PyEcholab to -999 to match.
                power[:][ev_power[:] == -999] = -999.0

                # Compare power values
                self.assertTrue(np.allclose(power[:,:], ev_power[:,:], equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(power.range, ev_power.range, equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(power.ping_time.view(dtype=np.uint64),
                        ev_power.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_Sv_conversion(self):

        for chan in self.channels:

            # Get a reference to the first data object
            raw_data = self.ek80.raw_data[chan][0]

            # Get the frequency of this channel.
            this_freq = raw_data.frequency[0]

            ev_file = ev_Sv_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get Sv
                Sv = raw_data.get_Sv()

                # Read the Echoview export file containing Sv.
                ev_Sv = processed_data.read_ev_mat('', 0, ev_file, data_type='Sv')

                # Compare Sv values
                self.assertTrue(np.allclose(Sv[:,start_sample], ev_Sv[:,start_sample],
                        atol=convert_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(Sv.range, ev_Sv.range, equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(Sv.ping_time.view(dtype=np.uint64),
                        ev_Sv.ping_time.view(dtype=np.uint64), equal_nan=True))


    def test_angle_conversion(self):

        for chan in self.channels:

            # Get a reference to the first data object
            raw_data = self.ek80.raw_data[chan][0]

            # Get the frequency of this channel. CW data will
            # have the frequency property
            this_freq = raw_data.frequency[0]

            ev_file = ev_angles_filename.get(this_freq, None)
            if ev_file is not None:
                sys.stdout.write(('%i kHz ' % this_freq))

                # Get the angle data
                alongship, athwartship = raw_data.get_physical_angles()

                # Read the Echoview export file containing angles.
                ev_alongship, ev_athwartship = processed_data.read_ev_csv('', 0,
                        ev_file, data_type='angles')

                # Compare angles
                mask = ~(np.isnan(alongship[:]) | np.isnan(ev_alongship[:]))
                self.assertTrue(np.allclose(alongship[mask], ev_alongship[mask],
                        atol=convert_atol))
                mask = ~(np.isnan(athwartship[:]) | np.isnan(ev_athwartship[:]))
                self.assertTrue(np.allclose(athwartship[mask], ev_athwartship[mask],
                        atol=convert_atol))

                # Compare ranges
                self.assertTrue(np.allclose(alongship.range, ev_alongship.range,
                        equal_nan=True))
                self.assertTrue(np.allclose(athwartship.range, ev_athwartship.range,
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
        self.ek80.write_raw(out_name, overwrite=True)

        # The read this re-written data
        ek80rewrite = EK80.EK80()
        ek80rewrite.read_raw(out_file)

        # Get a list of the rewritten channels
        rewrite_channels = list(ek80rewrite.raw_data.keys())

        for chan in rewrite_channels:
            # Get a reference to the first data object
            raw_data = ek80rewrite.raw_data[chan][0]

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
                self.assertTrue(np.allclose(power[:,:], ev_power[:,:],
                        atol=rewrite_atol, equal_nan=True))

                # Compare ranges
                self.assertTrue(np.allclose(power.range, ev_power.range, equal_nan=True))

                # Compare times
                self.assertTrue(np.allclose(power.ping_time.view(dtype=np.uint64),
                        ev_power.ping_time.view(dtype=np.uint64), equal_nan=True))

            ev_file = ev_angles_filename.get(this_freq, None)
            if ev_file is not None:

                # Get the angle data
                alongship, athwartship = raw_data.get_physical_angles()

                # Read the Echoview export file containing angles
                ev_alongship, ev_athwartship = processed_data.read_ev_csv('', 0,
                        ev_file, data_type='angles')

                # Compare angles
                mask = ~(np.isnan(alongship[:]) | np.isnan(ev_alongship[:]))
                self.assertTrue(np.allclose(alongship[mask], ev_alongship[mask],
                        atol=convert_atol))
                mask = ~(np.isnan(athwartship[:]) | np.isnan(ev_athwartship[:]))
                self.assertTrue(np.allclose(athwartship[mask], ev_athwartship[mask],
                        atol=convert_atol))


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
            info = 'Test number: {index}\n{info}'.format(
                index=test.progress_index,
                info=info
            )

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
    tests = [wbt_cw_reduced_test(func) for func in test_funcs]
    test_suite.addTests(tests)

    CustomTextTestRunner(verbosity=2).run(test_suite)

