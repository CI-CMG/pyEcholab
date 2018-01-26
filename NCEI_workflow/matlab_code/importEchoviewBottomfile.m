function Bottom = importEchoviewBottomfile(filename)
%IMPORTFILE Import numeric data from a text file as a matrix.
%   BOTTOM = IMPORTFILE(FILENAME) Reads data from text file FILENAME for
%   the default selection.
%
% Example:
%   Bottom = importfile('Bottom.txt');

%% Initialize variables.
delimiter = ',';
startRow = 2;
%% Format string for each line of text:
formatSpec = '%s%s%f%f%f%f%f%f%f%f%f%[^\n\r]';

%% Open the text file.
fileID = fopen(filename,'r');

%% Read columns of data according to format string.
% This call is based on the structure of the file used to generate this
% code. If an error occurs for a different file, try regenerating the code
% from the Import Tool.
dataArray = textscan(fileID, formatSpec, 'Delimiter', delimiter, 'EmptyValue' ,NaN,'HeaderLines' ,startRow-1, 'ReturnOnError', false);

%% Close the text file.
fclose(fileID);

%% Allocate imported array to column variable names
Ping_date = dataArray{:, 1};
Ping_time = dataArray{:, 2};
Ping_milliseconds = dataArray{:, 3};
Latitude = dataArray{:, 4};
Longitude = dataArray{:, 5};
% Position_status = dataArray{:, 6};
Depth = dataArray{:, 7};
Line_status = dataArray{:, 8};
% Ping_status = dataArray{:, 9};
% Altitude = dataArray{:, 10};
% GPS_UTC_time = dataArray{:, 11};

tmp = strcat(Ping_date,Ping_time);
time_stamp = datenum(tmp,'yyyy-mm-ddHH:MM:SS');
% time_stamp = datenum(tmp,'m/dd/yyyyHH:MM:SS');
%% Create output variable
tmp = Line_status == 1;
if sum(tmp) >= 4
    Bottom(:,1) = Latitude(tmp);
    Bottom(:,2) = Longitude(tmp);
    Bottom(:,3) = Depth(tmp);
    Bottom(:,4) = Ping_milliseconds(tmp);
    Bottom(:,5) = time_stamp(tmp);       
else
    Bottom = [];
end