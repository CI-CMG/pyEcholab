# Example Code

This folder contains examples of how to use pyEcholab to read, write, process, and plot sonar data.  Both python (.py) and Jupyter Notebook (.ipynb) files are available for most examples.

## Get the Data
See the README in the examples/data folder for instructions on how to get test data to run these examples.


## Example Descriptions

* **simple_ek60**<br/>  Demonstrates simple file reading and plotting of EK60 data.

* **echogram_plotting**<br/>
Demonstrates plotting echograms. 


* **frequency_differencing**<br/>
Demonstrates the use of numeric and boolean operators on ProcessedData and Mask objects, how to use ProcessedData.zeros_like() method to subset the data, and how to use the ProcessedData.view() method to plot a subset of the data. 


* **heave_compensation**<br/>
Demonstrates the use of boolean operators to plot heave corrected data. It also provides an example of using the ProcessedData.view() method to plot a subset of the data.


* **insert_delete_tests**<br/>
Demonstrates manipulating the RawData and ProcessedData objects using the insert and delete methods. The primary purpose of this example is to verify basic operation of the insert and delete methods, but it also provides some simple examples of using index arrays with these methods.


* **mask_test**<br/>
Demonstrates the use of masks for modifying and thresholding data.  Specifically, it demonstrates processes such as creating masks, copying and changing values in a mask, and plotting masks.


* **plot_single_ping**<br/>
Demonstrates plotting a single ping as power for every channel in a specified raw file.


* **qt_echogram_viewer**<br/>
This script is used mainly to test the PyQt based plotting tools. These tools were originally developed for displaying images and were extended to work with echogram data.
NOTE: This code currently uses PyQt4 and is incompatible with Qt5.  The intention is to make the qt plotting tools compatible with Python3/Qt5 in the future.


* **read_bottom**<br/>
Demonstrates how to read raw and bot/out files to plot echograms of the data. 


* **align_pings_test**<br/>
Demonstrates AlignPings functionality, which is a class that takes a list of either raw data objects or processed data objects and aligns data by ping time.


* **nmea_example**<br/>
Module Requirements: Basemap module...


* **nmea_example_cartopy**<br/>
Demonstrates working with the nmea_data class and Cartopy package to plot tracklines on a map.  Requires installation of [Cartopy package](https://scitools.org.uk/cartopy/docs/v0.15/installing.html#installing) to run. 


* **plot_Sv_echograms_from_raw_file**<br/>
Demonstrates plotting an echogram of Sv for each channel of a raw EK60 file.


## Jupyter Notebooks

Jupyter Notebooks is a free, open source web application that supports placing live code, descriptive text, and visualizations all in one document. 
These documents are interactive, meaning that the code can be modified and run in the browser to see the results.  

To view these files, you will need to download jupyter notebooks.  If you have anaconda installed, as recommended for running pyEcholab, then Jupyter Notebooks
comes included.  

To run Jupyter Notebooks, type *jupyter notebook* in the terminal.  A web browser will open, showing your home directory.  Navigate to the 
the Jupyter Notebook files (.ipynb) on your machine from this browser and open them up.  Now you can run and modify the files in the browser.

There are also static versions of some of these jupyter notebook files in html format.  These show the code and their outputs in a static view.
To view these html files, download them to your computer and open it in a browser.

NCEI is working on hosting these files in a place that can be accessed without requiring a Jupyter Notebooks installation.



