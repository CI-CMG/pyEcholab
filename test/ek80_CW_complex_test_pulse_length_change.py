# -*- coding: utf-8 -*-
"""
ek80_CW_complex_test_pulse_length_change


"""

import unittest
import numpy
from echolab2.instruments import EK80
from echolab2.processing import processed_data



# EK80 CW Complex 3 sectors
in_files = ['./data/SD_alaska_2019-Phase0-D20190516-T030157-0.raw']
ev_csv_filename = 'C:/EK80 Test Data/Saildrone/SD_alaska_2019-Phase0-D20190516-T030157-0-38kHz.angles.csv'


ev_Sv_filename = {}
ev_Sv_filename['Echoview Sv - 38 kHz'] = 'SD_alaska_2019-Phase0-D20190516-T030157-0-38kHz-Sv.mat'
ev_Sv_filename['Echoview Sv - 200 kHz'] = 'SD_alaska_2019-Phase0-D20190516-T030157-0-200kHz-Sv.mat'

ev_Ts_filename = {}
ev_Ts_filename['Echoview TS - 38 kHz'] = 'SD_alaska_2019-Phase0-D20190516-T030157-0-38kHz.ts.csv'
ev_Ts_filename['Echoview TS - 200 kHz'] = 'SD_alaska_2019-Phase0-D20190516-T030157-0-200kHz.ts.csv'

ev_power_filename = {}
ev_power_filename['Echoview power - 38 kHz'] = 'SD_alaska_2019-Phase0-D20190516-T030157-0-38kHz.power.csv'
ev_power_filename['Echoview power - 200 kHz'] = 'SD_alaska_2019-Phase0-D20190516-T030157-0-200kHz.power.csv'


class wbt_mini_cw_complex_3sector_conversions_test(unittest.TestCase):


    def setUpClass(self):


        self.ek80 = EK80.EK80()
        self.ek80.read_raw(in_files)



    def test_default_widget_size(self):
        self.assertEqual(self.widget.size(), (50,50),
                         'incorrect default size')

    def test_widget_resize(self):
        self.widget.resize(100,150)
        self.assertEqual(self.widget.size(), (100,150),
                         'wrong size after resize')


ek80 = EK80.EK80()
ek80.read_raw(in_files)
print(ek80)

channels = list(ek80.raw_data.keys())
raw_data = ek80.raw_data[channels[0]][0]

angles_along, angles_athwart = raw_data.get_physical_angles()

ev_angles_along, ev_angles_athwart = processed_data.read_ev_csv(channels[0],
        0, ev_csv_filename, data_type='angles')

print(angles_along[0,20:40]-ev_angles_along[0,20:40])
print(angles_athwart[0,20:40]-ev_angles_athwart[0,20:40])

print(np.max(np.abs(angles_athwart-ev_angles_athwart)))

print()
