%create_test_data.m
%
%  A script that creates a test data set that can be used to verify
%  output of the pyEcholab package.
%
%   REQUIRES:   readEKRaw toolbox
%

%   Rick Towler
%   NOAA Alaska Fisheries Science Center
%   Midwater Assesment and Conservation Engineering Group
%   rick.towler@noaa.gov

%-

%  define path to the source file
raw_file = 'C:\Users\rick.towler\AFSCGit\pyEcholab\test\data\test_data.raw';

%  define the source channel and output file name - our test file has 2
%  channels and we run this once for each channel.
chan = 1;
matFile = 'C:\Users\rick.towler\AFSCGit\pyEcholab\test\data\echolab_data_38kHz.mat';

%  read in the raw file. Since pyEcholab drops the first sample
[header, rawData] = readEKRaw(raw_file);

%  extract calibration parameters from raw data structure
cal_parms = readEKRaw_GetCalParms(header, rawData);

%  convert power to Sv, sv, Sp, and sp
data = readEKRaw_Power2Sv(rawData, cal_parms, 'KeepPower', true);
data = readEKRaw_Power2Sv(data, cal_parms, 'Linear', true, ...
    'KeepPower', true);
data = readEKRaw_Power2Sp(data, cal_parms, 'KeepPower', true);
data = readEKRaw_Power2Sp(data, cal_parms, 'Linear', true, ...
    'KeepPower', true);

%  convert angle data
data = readEKRaw_ConvertAngles(data, cal_parms, ...
    'KeepElecAngles', true);

%  extract individual fields from the rawData structure so we can save them
power = data.pings(chan).power;
frequency = data.pings(chan).frequency(1);
sv = data.pings(chan).Sv;
sv_linear = data.pings(chan).sv;
sp = data.pings(chan).Sp;
sp_linear = data.pings(chan).sp;
alongship = data.pings(chan).alongship;
alongship_e = data.pings(chan).alongship_e;
athwartship = data.pings(chan).athwartship;
athwartship_e = data.pings(chan).athwartship_e;
ping_number = data.pings(chan).number;
range = data.pings(chan).range;

%  write these data to a mat file - set the MATLAB file version
%  to 7.3 to output HDF5 based files.
save(matFile, '-v7.3', 'range', 'power', 'sv', 'sv_linear', ...
    'sp', 'sp_linear', 'cal_parms', 'ping_number', 'raw_file', ...
    'alongship', 'alongship_e', 'athwartship', 'athwartship_e', ...
    'frequency');
