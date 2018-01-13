# -*- coding: utf-8 -*-
"""

"""

from instruments.EK60 import EK60
import pprint


run_nmea_check = 1
run_calibration_check = 0
run_sv_check = 0


def nmea_check():
  print("\n\n")
  print("Running nmea data check.")

  filenames = ["/home/vagrant/bak/data/EK60/PC1106-D20110830-T052815.raw"]
  r = EK60()
  r.read_raw(filenames)

  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(r.nmea_data)

  processed_data_obj = r.raw_data['GPT  38 kHz 0090720346b4 1-1 ES38'].get_power()
  processed_data_obj = r.nmea_data.get_interpolate(processed_data_obj)
  
  print("interpolated latitude")
  print("processed_data_obj.latitude")
  pp.pprint(processed_data_obj.latitude)



def calibration_check():
  print("\n\n")
  print("Running calibration data check.")
  filenames = ["/home/vagrant/bak/data/EK60/PC1106-D20110830-T052815.raw"]
  r = EK60()
  r.read_raw(filenames)

  c = r.calibration_data['GPT 120 kHz 009072058cb4 3-1 ES120']

  print("\n")
  print("Calibration Data")
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(vars(c))

  raw_data = r.raw_data['GPT 120 kHz 009072058cb4 3-1 ES120']

  #append calibration data with raw object.
  c.from_raw_data(raw_data)

  print("\n")
  print("Calibration Data with Appended Raw Data")
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(vars(c))


def sv_check():
  filenames = ["/home/vagrant/bak/data/EK60/PC1106-D20110830-T052815.raw"]
  r = EK60()
  r.read_raw(filenames)
  c = r.calibration_data['GPT 120 kHz 009072058cb4 3-1 ES120']
  svcalc = r.raw_data['GPT  38 kHz 0090720346b4 1-1 ES38'].get_sv(calibration=c)


  print("\n")
  print("sv Data")
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(svcalc)



#MAIN

if run_nmea_check:
  nmea_check()

if run_calibration_check:
  calibration_check()

if run_sv_check:
  sv_check()
