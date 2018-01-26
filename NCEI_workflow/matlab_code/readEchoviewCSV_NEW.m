function data = readEchoviewCSV_NEW(numfreq,Folders,start)

for i = start:length(Folders.Files)     
    filename = fullfile(Folders.FileFolder,Folders.Files(i).name);
    disp(['Processing: ' filename])
    tt = strfind(filename,'FileNameList');
    if sum(tt) > 0
        disp(['Skipped: ' filename])
        continue
    end
% % % %     info = dir(filename);
% % % %     % check for file size above a 1000 MB limit or less than 6 KB.     
% % % %     if info.bytes>1000000000 || info.bytes<=6000 
% % % %         disp('Skipped file')
% % % %         continue
% % % %     end      

	%% Read data file (including data matrix) exported from Echoview
try
    data = importEchoviewCSVfile(filename,'readALL',1);
catch
    try
        data = importEchoviewCSVfile(filename,'readALL',1);
    catch
        EK60_REPROCESS_ByHour_catchTrap('filename',filename);
        data = importEchoviewCSVfile(filename,'readALL',1);
    end
end
    if isempty(data)
        continue
    end

    [~,data.file,~]=fileparts(filename);
    bottomfile = [Folders.FileFolder '\Bottom\' data.file '.csv'];

    if exist(bottomfile, 'file') ~= 2
        error('File not found: %s.', bottomfile);
        data.Bottom = [];
    else
	%% Read bottom file exported from Echoview
        data.Bottom = importEchoviewBottomfile(bottomfile);   
    end

	% Calculate the bottom using ETOPO1/GEBCO data            
    if isempty(data.Bottom)
        data.estBottom = findBottom(data);
    else
        data.estBottom = zeros(length(data.Latitude),1);
        data.estBottom(data.estBottom == 0) = NaN;
    end
    
    [r,c]=size(data.data);
    if c ~= max(data.Sample_count);
        data.data=data.data(:,1:max(data.Sample_count));
    end
    
	%% set PingDatenum
    tmp3 = [char(data.Ping_date) char(data.Ping_time)];
    data.PingDatenum = datenum(tmp3,'yyyy-mm-ddHH:MM:SS');
    
	%% Set no data values
    noDataValue = 2;
    data.data(data.data == 0) = noDataValue;
    data.data(data.data == -9.900000000000000e+37) = noDataValue;
    data.data(data.data == -999) = noDataValue;
    data.data(isnan(data.data)) = noDataValue;

	%% Calculate depth range for the data    
    data.Range = min(data.Range_start):max(data.Range_stop)/max(data.Sample_count):max(data.Range_stop);
    
 %% Account for varying delta T so that bottom line matches up with Sv output    
    % Identify delta T that is less than or equal to 0, replace with value with a median
    % delta T
    tmpBottomTime = diff(data.PingDatenum);
    ind = find(tmpBottomTime <=0);
    if ~isempty(ind) 
        for k = 1:length(ind)
            if ind(k) ~= 1
                data.PingDatenum(ind(k)) = data.PingDatenum(ind(k)-1)+(data.PingDatenum(ind(k)+1)-data.PingDatenum(ind(k)-1))/2;
            else
                data.PingDatenum(ind(k)) = data.PingDatenum(ind(k)+1)-(data.PingDatenum(ind(k)+2)-data.PingDatenum(ind(k)+1))/2;
            end
        end
    end
    
    % account for files that have multiple 0s in a row close to the
    % beginning or the end of the array
    tmpBottomTime = diff(data.PingDatenum);
    ind = find(tmpBottomTime <=0);
    if ~isempty(ind)
        if ind(end) <= 5  % close to the beginning
            k = ind(end);
            time_span = data.PingDatenum(k+2)-data.PingDatenum(ind(1));
            interval = time_span/length(ind);
            while k ~= 0
                data.PingDatenum(k) = data.PingDatenum(k+1)-interval;
                k = k-1;
            end
        end
        if ind(end) >= (length(data.PingDatenum)-5) % close to the end
            k = ind(1);
            time_span = data.PingDatenum(ind(end)-data.PingDatenum(k-2));
            interval = time_span/length(ind);
            while k ~= length(data.PingDatenum)
                data.PingDatenum(k) = data.PingDatenum(k-1)+interval;
                k = k+1;
            end
        end
    end
    
    data.newRange = linspace(min(data.Range),max(data.Range),max(data.Sample_count)*2);
    data.tmpData = zeros(r,max(data.Sample_count)*2);
    % Interpolate new data with the new linearly spaced depth intervals 
    for n = 1:r
        if data.Range_start(n) == data.Range_stop(n);
            range = data.Range_start(n):data.Range_stop(n-1)/max(data.Sample_count):data.Range_stop(n-1);
        else
            range = data.Range_start(n):data.Range_stop(n)/max(data.Sample_count):data.Range_stop(n);
        end
        if length(range) < max(data.Sample_count)
            range(max(data.Sample_count)) = data.Range_stop(n);
        elseif length(range) > max(data.Sample_count)
            range = range(1:max(data.Sample_count));
        end
        data.tmpData(n,:) = interp1(range,data.data(n,:),data.newRange,'nearest','extrap');
    end

    data.newTime = linspace(min(data.PingDatenum),max(data.PingDatenum),r*2);
    data.newData = zeros(r*2,max(data.Sample_count)*2);
 % Interpolate new data with the new linearly spaced timestamp 
        for m = 1:max(data.Sample_count)*2
            data.newData(:,m) = interp1(data.PingDatenum,data.tmpData(:,m),data.newTime,'nearest','extrap');
        end
  % Calculate sun     
    data.sun=zeros(length(data.PingDatenum),2);
    for itvl=1:length(data.PingDatenum)
        data.sun(itvl,:)=suncycle(data.Latitude(itvl), data.Longitude(itvl), data.PingDatenum(itvl));
    end
    hour = mod(data.PingDatenum,1) * 24;
    day = xor(min(data.sun,[],2) < hour & hour < max(data.sun,[],2), ...
        data.sun(:,1) > data.sun(:,2));
    data.day = day;
        
 
    %% Plot the data 
    try         
        data = plotEchoviewCSV_NEW(data,numfreq,Folders.ExportFolder);
    catch
%         data.newData = data.data; 
%         data.newTime = data.PingDatenum;
%         data.newRange = data.Range;       
%         data = plotEchoviewCSV_NEW(data,numfreq,Folders.ExportFolder);
        disp(['Issue with plotting: ' filename])
        return
    end 
end

%% subfunctions
function estBottom = findBottom(data)
try
    HH=evalin('base','HH');
    LAT=evalin('base','LAT');
    LON=evalin('base','LON');
catch
    % Load GEBCO bathy data
    disp('Loading GEBCO30 bathy data')
    load('D:\CODE AND EV TEMPLATES\MATLAB\GEBCO30.mat');
    assignin('base','HH',HH);
    assignin('base','LAT',LAT);
    assignin('base','LON',LON);
end

estBottom = zeros(length(data.Latitude),1);

data.Longitude = (abs(data.Longitude))*-1;

for m = 1:length(data.Latitude)
    if data.Latitude(m) ~= 999 || data.Longitude(m) ~= -999
        indLat = find(LAT >= data.Latitude(m));
        indLon = find(LON >= data.Longitude(m));
        if data.Latitude(m) > 0
            row = indLat(length(indLat));
        else
            row = indLat(1);
        end
        if data.Longitude(m) > 0
            col = indLon(length(indLon));
        else
            col = indLon(1);
        end
        estBottom(m) = HH(row,col);
    else
        data.Latitude(m) = NaN;
        data.Longitude(m) = NaN;
    end
end

estBottom = abs(estBottom);
estBottom(estBottom == 0) = NaN;

function result = NanMIN(input)
    ind = ~isnan(input);
    result = min(input(ind));
    
function result2 = NanMAX(input)
    ind = ~isnan(input);
    result2 = max(input(ind));