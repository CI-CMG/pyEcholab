function data = importEchoviewCSVfile(filename,varargin)
%IMPORTFILE Import numeric data from a text file as column vectors.
%   data = IMPORTFILE(FILENAME) Reads data from text file FILENAME for the
%   default selection.
%   The structure data includes variables: VarName2,Distance_gps1,Distance_vl1,Ping_date1,Ping_time1,Ping_milliseconds1,Latitude1,Longitude1,Depth_start1,Depth_stop1,Range_start1,Range_stop1,Sample_count1
% Example:
%   data  = importfile('CWResultNew.linear.csv');
%% Initialize variables.
% delimiter = '';
delimiter = ',';
startRow = 2;
endRow = inf;
readAll = 0;

for n = 1:length(varargin)
    switch lower(varargin{n})
        case 'readall'
            readAll = varargin{n+1};
    end
end

%% Open the text file to read column vectors.
fileID = fopen(filename,'r');

%% Read line by line to determine number of 
tline = fgetl(fileID); % skip header
% tline = fgetl(fileID);
k=0;
    while ~feof(fileID)
       k=k+1;
       pairnum(k) = length(strfind(tline,','))+1;
       tline = fgetl(fileID);
    end
frewind(fileID);

if k >= 2

    %% Format string for vector columns
    formatSpec = '%f%f%f%s%s%f%f%f%f%f%f%f%f';
    for i = 1:max(pairnum)
        formatSpec = horzcat(formatSpec,'%*s');
    end 
    %% Format string for matrix
    formatSpec1 = '%*s%*s%*s%*s%*s%*s%*s%*s%*s%*s%*s%*s%*s';
    for i = 1:max(pairnum)
        formatSpec1 = horzcat(formatSpec1,'%f');
    end  

    %% Read columns of data according to format string. Create vector columns
    dataArray1 = textscan(fileID, formatSpec, endRow(1)-startRow(1)+1, 'Delimiter', delimiter, 'HeaderLines', startRow(1)-1, 'ReturnOnError', false);
    for block=2:length(startRow)
        frewind(fileID);
        dataArrayBlock1 = textscan(fileID, formatSpec, endRow(block)-startRow(block)+1, 'Delimiter', delimiter, 'HeaderLines', startRow(block)-1, 'ReturnOnError', false);
        for col=1:length(dataArray1)
            dataArray1{col} = [dataArray1{col};dataArrayBlock1{col}];
        end
    end  
    %% Close the text file.
    fclose(fileID);

    %% Open the text file to read data matrix.
    if readAll == 1
        fileID = fopen(filename,'r');
        %% Read columns of data according to format string. Create matrix
        dataArray = textscan(fileID, formatSpec1, endRow(1)-startRow(1)+1, 'Delimiter', delimiter, 'HeaderLines', startRow(1)-1, 'ReturnOnError', false);
        for block=2:length(startRow)
            frewind(fileID);
            dataArrayBlock = textscan(fileID, formatSpec, endRow(block)-startRow(block)+1, 'Delimiter', delimiter, 'HeaderLines', startRow(block)-1, 'ReturnOnError', false);
            for col=1:length(dataArray)
                dataArray{col} = [dataArray{col};dataArrayBlock{col}];
            end
        end

        %% Close the text file.
        fclose(fileID);
    end

    %% Allocate imported array to column variable names
    data.VarName = dataArray1{:,1};
    data.Distance_gps = dataArray1{:,2};
    data.Distance_vl = dataArray1{:,3};
    data.Ping_date = dataArray1{:,4};
    data.Ping_time = dataArray1{:,5};
    data.Ping_milliseconds = dataArray1{:,6};
    data.Latitude = dataArray1{:,7};
    data.Longitude = dataArray1{:,8};
    data.Depth_start = dataArray1{:,9};
    data.Depth_stop = dataArray1{:,10};
    data.Range_start = dataArray1{:,11};
    data.Range_stop = dataArray1{:,12};
    data.Sample_count = dataArray1{:,13};

    if readAll == 1; data.data = [dataArray{1:end-1}]; end
else
    data = []; %not enough data in the file. This file will be skipped
end



