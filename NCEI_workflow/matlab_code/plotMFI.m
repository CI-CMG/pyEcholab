
function result = plotMFI()

% RootFolder = 'F:\ICES ANALYSIS\44th Parallel\MFI_NEW';
RootFolder = 'C:\Users\cwall\Documents\MFI_NEW';
Folders.FileFolder   = uigetdir(RootFolder, 'Where are the csv files that you wish to use?');
Folders.Files        = dir(fullfile(Folders.FileFolder,'*points*.csv')); 
Folders.ExportFolder = uigetdir(RootFolder, 'Where do you want to save the export image?'); 

maxRange = 50;
maxDist = 0.2;

for i = 1:length(Folders.Files) 
    file = fullfile(Folders.FileFolder,Folders.Files(i).name);
    
    [path,filename,~]=fileparts(file);
    ind1 = strfind(filename,'.');
    exportFile = filename(1:ind1(1)-1);
    ind2 = strfind(path,'\');
    exportFolder = path(ind2(end)+1:end);
    
    
    data = readEchoviewGeorefCSVs(file);
    data.sv(data.sv == -999) = NaN;
    data.sv(data.sv == 0) = NaN;
%     data.sv(data.sv < -70) = NaN;
    
    depthMin = 0;
    depthMax = max(data.Depth);   
    depthInterval = depthMin:maxRange:depthMax;
    
    depthMatrix = NaN(length(data.sv),length(depthInterval));
    depthMode = NaN(length(depthInterval),1);
    count1 = 0;
    count2 = 0;
    for j = 1:length(depthInterval)
        tmp = data.Depth >= depthMin+maxRange*count1 & data.Depth < depthMin+maxRange*j;
        rows = length(data.sv(tmp));
        depthMatrix(1:rows,j) = data.sv(tmp);
        depthMode(j) = mode(data.sv(tmp));
        count1 = count1 +1;
    end
    fh=figure(3); clf
    height = 3; 
    width = 8; 
    FigDim =[0.1 0 width height];   
    set(fh,'units','inches','position',FigDim,'Color','w', 'InvertHardCopy', 'off');
    set(fh, 'PaperUnits', 'inches','PaperSize', [width height], 'PaperPositionMode', 'manual', 'PaperPosition', [0 0 width height]);
    subplot(1,2,1)
    boxplot(depthMatrix,'label',depthInterval,'plotstyle','compact','outliersize',2,'symbol','.','orientation','horizontal')
    ylabel('Depth (m)','FontName','Times','FontSize',16);
    xlabel('Sv (dB)','FontName','Times','FontSize',16);
    xlim([-85 -30]);
    set(gca,'xtick',[-80,-70,-60,-50,-40,-30]);
    set(gca,'xticklabel',{'-80','-70','-60','-50','-40','-30'});
    set(gca,'ydir','reverse')
    set(gca,'fontsize',16,'fontname','Times')    
    
    lonMin = floor(min(data.Longitude));
    lonMax = ceil(max(data.Longitude));   
    lonInterval = lonMin:maxDist:lonMax;
    
    lonMatrix = NaN(length(data.sv),length(lonInterval));
    
    lonMode = NaN(length(lonInterval),1);
    
    for k = 1:length(lonInterval)
        tmp = data.Longitude >= lonMin+maxDist*count2 & data.Longitude < lonMin+maxDist*k;
        try
            rows = length(data.sv(tmp));
            lonMatrix(1:rows,k) = data.sv(tmp);
            lonMode(k) = mode(data.sv(tmp));
        catch
            rows = length(data.sv);
            lonMatrix(1:rows,k) = data.sv;
            lonMode(k) = mode(data.sv);
        end
        
        count2 = count2 + 1;
    end
    subplot(1,2,2),boxplot(lonMatrix,'labels',lonInterval,'plotstyle','compact','outliersize',2,'symbol','.')
    xlabel('Longitude (W)','FontName','Times','FontSize',16);
    ylim([-85 -30]);
    set(gca,'fontsize',16,'fontname','Times')
    
    result.depthMatrix = depthMatrix;
%     result.lonMatrix = lonMatrix; 
    result.depthMode = depthMode;
%     result.lonMode = lonMode;
    
    imagename = [Folders.ExportFolder,'\',exportFolder,'_',exportFile,'.png']; %% char(cellstr(*)) added to remove white space after filename
    print(gcf,'-dpng','-r600',imagename) ;
    disp(['Saved ' imagename])
    
%     ff=figure(56); 
%     height = 3; 
%     width = 8; 
%     FigDim =[0.1 0 width height];   
%     set(ff,'units','inches','position',FigDim,'Color','w', 'InvertHardCopy', 'off');
%     set(ff, 'PaperUnits', 'inches','PaperSize', [width height], 'PaperPositionMode', 'manual', 'PaperPosition', [0 0 width height]);
%     subplot(1,2,1),plot(depthInterval,depthMode,'-o')
%     ylim([0 11.5])
%     xlim([depthMin depthMax])
%     xlabel('Depth (m)','FontName','Times','FontSize',16);
%     hold on
% %     ax = gca;
% %     ax.ytick = [1,3,4,7,8,10,11];
% %     ax.yticklabel = {'18 kHz','38 kHz','18+38 kHz','120 kHz','18+120 kHz','38+120 kHz','18+38+120 kHz'};
%         
%     set(gca,'fontsize',16,'fontname','Times')
%         
%     subplot(1,2,2),plot(lonInterval,lonMode,'-x')
%     ylim([0 11.5])
%     xlim([lonMin lonMax])
%     xlabel('Longitude (W)','FontName','Times','FontSize',16);
%     set(gca,'fontsize',16,'fontname','Times')  
%     hold on
%     bx = gca;
%     bx.ytick = [1,3,4,7,8,10,11];
%     ax.yticklabel = { };
end
    

function data = readEchoviewGeorefCSVs(filename, startRow, endRow)
%% Initialize variables.
delimiter = ',';
if nargin<=2
    startRow = 2;
    endRow = inf;
end

formatSpec = '%f%f%f%f%f%f%[^\n\r]';

%% Open the text file.
fileID = fopen(filename,'r');

dataArray = textscan(fileID, formatSpec, endRow(1)-startRow(1)+1, 'Delimiter', delimiter, 'EmptyValue' ,NaN,'HeaderLines', startRow(1)-1, 'ReturnOnError', false);
for block=2:length(startRow)
    frewind(fileID);
    dataArrayBlock = textscan(fileID, formatSpec, endRow(block)-startRow(block)+1, 'Delimiter', delimiter, 'EmptyValue' ,NaN,'HeaderLines', startRow(block)-1, 'ReturnOnError', false);
    for col=1:length(dataArray)
        dataArray{col} = [dataArray{col};dataArrayBlock{col}];
    end
end

%% Close the text file.
fclose(fileID);

%% Allocate imported array to column variable names
data.Latitude = dataArray{:, 2};
data.Longitude = dataArray{:, 3};
data.Altitude = dataArray{:, 4};
data.Depth = dataArray{:, 5};
data.sv = dataArray{:, 6};