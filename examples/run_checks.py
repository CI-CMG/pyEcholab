# -*- coding: utf-8 -*-
"""

"""

from echolab2.instruments.EK60 import EK60
import pprint


run_nmea_check = 1
run_calibration_check = 1


def nmea_check():
  print("\n\n")
  print("Running nmea data check.")

  filenames = ["/home/vagrant/bak/data/EK60/PC1106-D20110830-T052815.raw"]
  r = EK60()
  r.read_raw(filenames)

  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(r.nmea_data)


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



#MAIN

if run_nmea_check:
  nmea_check()

if run_calibration_check:
  calibration_check()

