%create_raw_test_file.m
%
%  A script that reads in a portion of a raw file and then writes that
%  data to disk creating a shortened raw file that we'll use for testing. 
%
%   REQUIRES:   readEKRaw toolbox
%

%   Rick Towler
%   NOAA Alaska Fisheries Science Center
%   Midwater Assesment and Conservation Engineering Group
%   rick.towler@noaa.gov

%-


%  define paths to the source file and output file
raw_file = 'C:\Program Files (x86)\Simrad\Scientific\ER60\Examples\Survey\OfotenDemo-D20001214-T145902.raw';
raw_out = 'test_data.raw';

%  read in raw file up to and including ping 430 - must set RawNMEA
%  keyword so we get the original NMEA strings in the output file.
pingRange = [1, 1, 430];
[header, rawData] = readEKRaw(raw_file, 'PingRange', pingRange, 'RawNMEA', ...
    true);

%  write a .raw file that comprises just pings 1-430
writeEKRaw(raw_out, header, rawData);
