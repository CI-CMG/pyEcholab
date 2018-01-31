function data = processEchoviewCSV(numfreq,varargin) 
%% Examples when running this script
% To run the script, starting at the first file for a 2+ frequency sonar
% system.
%       data = processEchoviewCSV(5);
%
% Same scenario but for single frequency sonar:
%       data = processEchoviewCSV(1);
%
% To run the script, starting at a defined point for a 2+ frequency sonar.
% In this case at the 42nd file in the folder.
%       data = processEchoviewCSV(5,'fileStart',42);
%
% Same scenario but for single frequency sonar:
%       data = processEchoviewCSV(1,'fileStart',42);

%% Read input parameters
if isempty(numfreq)
    warning('processEchoviewCSV:ParameterError', ...
            'Need to include number of frequencies');
end

start = 1;

for n = 1:length(varargin)
    switch lower(varargin{n})
        case 'filestart'
            start = varargin{n+1};
    end
end

%% Find files and set output folders
RootFolder = 'D:\';
Folders.FileFolder   = uigetdir(RootFolder, 'Where are the csv files that you wish to use?');
Folders.Files        = dir(fullfile(Folders.FileFolder,'*.csv')); 
Folders.ExportFolder = uigetdir(RootFolder, 'Where do you want to save the export image?'); 

%% Go to program to reach each file
tic
data = readEchoviewCSV_NEW(numfreq,Folders,start);

[~,folder,~]=fileparts(Folders.FileFolder);
ind = strfind(folder,'_');
cruiseName = folder(1:ind-1);

thumbfolder = ['Z:\thumbnail\' cruiseName];
makethumbdirCSV(1024,7,Folders.ExportFolder,thumbfolder);
imagefolder = ['Z:\fullres\' cruiseName];
mkdir(imagefolder)
copyfile(Folders.ExportFolder,imagefolder);

disp('Done!');
b = toc;
disp(['Elapsed time: ' num2str(b/3600) ' hours'])