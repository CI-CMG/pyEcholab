# pyEcholab2

pyEcholab2 is a python package for reading, writing, processing, and plotting data from Simrad/Kongsberg sonar systems.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

pyEcholab2 requires Python 2.7 or Python 3.x. We recommend using an
[Anaconda](https://www.anaconda.com/download/) based Python
distribution

pyEcholab2 uses the following packages:  

&nbsp;&nbsp;**_Required_**
* [matplotlib](https://matplotlib.org/) for plotting echograms.
* [numpy](http://www.numpy.org/) for large, multi-dimensional arrays.
* [pytz](http://pytz.sourceforge.net/) for cross platform timezone calculations.

&nbsp;&nbsp;**_Optional_**
* [PyQT4](https://wiki.python.org/moin/PyQt4) for GUI applications (see [example](https://github.com/CI-CMG/PyEcholab2/blob/master/examples/qt_echogram_viewer.py)).
* [basemap](https://matplotlib.org/basemap/) for plotting on maps (only used in [nmea example](https://github.com/CI-CMG/PyEcholab2/blob/master/examples/nmea_example.py) and currently only works with matplotlib 1.5.0rc3, basemap 1.0.8, and pyproj 1.9.5.1).

### Installation

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Data
*Note that these files are not shared publicly and will need to be moved before making this project public.*
Data used for running the examples and verifying the results of the conversion and integration functions. Place new files for testing into the Test Data Directory

[Test Data Directory](https://drive.google.com/drive/u/0/folders/0BzfkO6wrXhxYOHVLOWVKUlJBYmc)

[Test Data](https://drive.google.com/open?id=1SYbK2eDGSEtrGbH4G82cw2aq-lklLxKS)

[Example Data](https://drive.google.com/open?id=1pwJ9fCetW1nG0BDVuuSL0zi3VxhWo9xX)


## Authors

* **Rick Towler** - _NOAA/NMFS, Alaska Fisheries Science Center_
* **Charles Anderson** - _Cooperative Institute for Research in Environmental Sciences (CIRES) located at  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;NOAA's National Centers for Environmental Information (NCEI)_
* **Veronica Martinez** - _CIRES located at NCEI_
* **Pamme Crandall** - _CIRES located at NCEI_

## License

This software is licensed under the MIT License - see the
[LICENSE](LICENSE) file for details

## Acknowledgments

* This work was funded by the National Marine Fisheries Service Office of Science and Technology.

## Contact
[wcd.info@noaa.gov](mailto:wcd.info@noaa.gov)