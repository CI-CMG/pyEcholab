import os
import fnmatch
import time
from echolab2.instruments import EK60


'''
This script was used to test performance gains from modifications to the
echolab2.instruments.util.raw_file module. The RawSimradFile class
uses a lot "seeking" which is extremely inefficient when working with
raw file I/O. I changed echolab2.instruments.util.raw_file to implement
io.BufferedReader which provides buffered access to an underlying raw
I/O stream. This allows seek calls to be generally serviced by the buffer
negating calls to the OS and reducing the overhead significantly.


Local (USB3 external drive) dataset size:
238 .raw files
11.5GB or 12,393,517,056 bytes


Python 2.7 results:

Buffered:
Read 294 total files in 570.463999271 seconds.
Average of 1.94035373902 seconds per file.

Buffered Local USB3 Drive:
Read 238 total files in 144.801000118 seconds.
Average of 0.608407563522 seconds per file.

Original Networked:
Read 294 total files in 784.030001402 seconds.
Average of 2.66676871225 seconds per file.

Original Local USB3 Drive:
Read 238 total files in 246.131000042 seconds.
Average of 1.03416386572 seconds per file.

Local:

i =  1.03416386572 - 0.608407563522
p = i / 1.03416386572 * 100
p = 41.16913347205206

Local performance increased 41% in Python 2.7

Networked:

i =  2.66676871225 - 1.94035373902
p = i / 2.66676871225 * 100
p = 27.239519118893174

Network performance increased 27% in Python 2.7


Python 3.6 results:

(I only tested local performance with Python 3.6)

Buffered Local USB3 Drive:
Read 238 total files in 144.88000178337097 seconds.
Average of 0.6087395032914746 seconds per file.

Original Local USB3 Drive:
Read 238 total files in 172.3149950504303 seconds.
Average of 0.7240125842455054 seconds per file.

Local:

i =  0.7240125842455054 - 0.6087395032914746
p = i / 0.7240125842455054 * 100
p = 15.92141952534665

Local performance increased 16% in Python 3.6



'''


inpath = 'U:/EK60/test/'
raw_files = os.listdir(inpath)
pattern = "*.raw"
elapsed = 0
n_files = 0
for file in raw_files:
    if fnmatch.fnmatch(file, pattern):
        ek60 = EK60.EK60()
        s = time.time()
        ek60.read_raw(inpath + file)
        e = time.time()
        elapsed = elapsed + (e-s)
        n_files = n_files + 1
        print('file: ' + file + '  Time (s):' + str(e-s))


print('Read ' + str(n_files) + ' total files in ' + str(elapsed) + ' seconds.')
print('Average of ' + str(elapsed/n_files) + ' seconds per file.')
