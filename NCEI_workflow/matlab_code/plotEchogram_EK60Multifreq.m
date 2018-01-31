function [fh, ih] = plotEchogram_EK60Multifreq(data, x, y, varargin)
% readEKRaw_SimpleEchogram - create a simple echogram figure
%   [fh, ih] = readEKRaw_SimpleEchogram(data, x, y, varargin) creates a figure
%   of an echogram given data (usually Sv), X (ping number) and y (range).
%
%   This is a simple function intended mainly to be used by the readEKRaw
%   library examples.  Development on a proper plotting package is underway.
%
%   REQUIRED INPUT:
%              data:    The data to plot.  A N x M matrix of typically Sv or
%                       Sp data.
%
%                 x:    A vector of length M containing the corresponding ping
%                       number or time for each ping in data.
%
%                 y:    A vector of length N containing the corresponding range
%                       or depth for each sample in data.
%
%
%   OPTIONAL PARAMETERS:
%            Figure:    Set this parameter to a number or handle ID specifying
%                       the figure to plot the echogram into.  If a non-existant
%                       figure number is passed, a new figure is created.  If an
%                       existing figure is passed, the contents of that figure
%                       are replaced with the echogram.
%                           Default: [];
%
%             Title:    Set this parameter to a string defining the figure
%                       title.
%                           Default: 'Echogram'
%
%            XLabel:    Set this parameter to a string defining the X axis
%                       label.
%                           Default: 'Ping'
%
%            YLabel:    Set this parameter to a string defining the Y axis
%                       label.
%                           Default: 'Range (m)'
%
%            NumFreq:   Set this parameter to identify how many frequences
%                       were included in the EK60 data. This is used to set 
%                       the colormap and legend labels
%

%   Rick Towler/Carrie Wall

%-
%  set default parameters
yLabelText = 'Depth (m)';
xLabelText = 'Time';
pTitle = 'Echogram';
frequencies = 5;

for n = 1:2:length(varargin)
    switch lower(varargin{n})
        case 'xlabel'
            xLabelText = varargin{n + 1};
        case 'ylabel'
            yLabelText = varargin{n + 1};
        case {'displaythreshold' 'threshold'}
            if (length(varargin{n + 1}) == 2)
                dThreshold = varargin{n + 1};
            else
                warning('readEKRaw:ParameterError', ...
                    ['Threshold - Incorrect number of arguments. ' ...
                    'Using defaults.']);
            end
        case 'title'
            pTitle = varargin{n + 1};
        case 'figure'
            fh = varargin{n + 1};
        case 'numfreq'
            frequencies = varargin{n+1};
        otherwise
            warning('readEKRaw:ParameterError', ...
                ['Unknown property name: ' varargin{n}]);
    end
end
% scrsz = get(0,'ScreenSize');
% fh = figure('Position',[10 50 scrsz(3)-20 scrsz(4)/1.35]); 

[RGB,~] = EK60JechColorScale(frequencies);

%  set the colormap
colormap(RGB);

%  create the echogram image
ih = image(x, y, data, 'CDataMapping', 'direct');

% [~,ih] = contourf(x, y, data,size(RGB,1));
% set(ih,'edgecolor',none);
% set(ih,'LineWidth',0.1);
set(gca, 'XGrid', 'on', 'Units','pixels');
set(gca,'FontName','Times','FontSize',14);

%  label
xlabel(xLabelText,'FontName','Times','FontSize',14);
ylabel(yLabelText,'FontName','Times','FontSize',14);
title(pTitle,'FontName','Times','FontSize',14,'Interpreter','none');
datetick
xlim([min(x) max(x)])

% %Plot colorbar or colorbar lables
% lcolorbar(labels,'FontName','Times','FontSize',7); 
end

function [rgb,labels] = EK60JechColorScale(frequencies)
switch frequencies
    case 3
        rgb = [[187 187 187];    % 1 - % Changed
               [255 255 255];    % 2  
               [000 000 255];    % 3               
               [128 128 255];    % 4
               [255 255 255];    % 5
               [255 255 255];    % 6
               [255 000 000];    % 7
               [255 128 128];    % 8        
               [255 255 255];    % 9
               [219 050 219];    % 10 
               [255 094 255]];    % 11
           labels = {'18 kHz','','38 kHz','18+38 kHz','','','120 kHz','18+120 kHz','','38+120 kHz','18+38+120 kHz'};
   
    case 4
        rgb = [[187 187 187];    % 1 - % Changed
               [255 255 255];    % 2  
               [000 000 255];    % 3               
               [128 128 255];    % 4
               [255 255 255];    % 5
               [255 255 255];    % 6
               [255 000 000];    % 7
               [255 128 128];    % 8        
               [255 255 255];    % 9
               [219 050 219];    % 10 
               [255 094 255];    % 11         
               [255 255 255];    % 12
               [255 255 000];    % 13
               [255 255 128];    % 14 
               [255 255 255];    % 15 
               [000 255 000];    % 16
               [128 255 128];    % 17
               [255 255 255];    % 18
               [255 255 255];    % 19
               [255 120 000];    % 20  
               [255 156 066];    % 21            
               [255 255 255];    % 22
               [125 000 125];    % 23
               [183 000 183]];   % 24
           labels = {'18 kHz','','38 kHz','18+38 kHz','','','120 kHz','18+120 kHz','','38+120 kHz','18+38+120 kHz','','200 kHz','18+200 kHz','','38+200 kHz','18+38+200 kHz','','','120+200 kHz','18+120+200 kHz','','38+120+200 kHz','18+38+120+200 kHz'};
           
    case 5
        rgb = [[187 187 187];    % 1 - % Changed
               [255 255 255];    % 2  
               [000 000 255];    % 3               
               [128 128 255];    % 4
               [255 255 255];    % 5
               [255 255 255];    % 6
               [255 000 000];    % 7
               [255 128 128];    % 8        
               [255 255 255];    % 9
               [219 050 219];    % 10 
               [255 094 255];    % 11         
               [255 255 255];    % 12
               [255 255 000];    % 13
               [255 255 128];    % 14 
               [255 255 255];    % 15 
               [000 255 000];    % 16
               [128 255 128];    % 17
               [255 255 255];    % 18
               [255 255 255];    % 19
               [255 120 000];    % 20  
               [255 156 066];    % 21            
               [255 255 255];    % 22
               [125 000 125];    % 23
               [183 000 183];    % 24
               [255 255 255];    % 25
               [255 255 255];    % 26
               [255 255 255];    % 27
               [255 255 255];    % 28
               [081 081 081];    % 29
               [116 109 112];    % 30 - % Changed
               [255 255 255];    % 31
               [000 000 106];    % 32
               [000 000 149];    % 33
               [255 255 255];    % 34
               [255 255 255];    % 35
               [121 000 000];    % 36
               [185 000 000];    % 37
               [255 255 255];    % 38
               [045 000 045];    % 39
               [074 000 074];    % 40
               [255 255 255];    % 41
               [151 151 000];    % 42
               [206 206 000];    % 43
               [255 255 255];    % 44
               [000 066 000];    % 45
               [000 138 000];    % 46
               [255 255 255];    % 47
               [255 255 255];    % 48
               [128 064 000];    % 49
               [215 107 000];    % 50
               [255 255 255];    % 51
               [000 230 230];    % 52
               [185 255 255]];    % 53               
            labels = {'18 kHz','','38 kHz','18+38 kHz','','','120 kHz','18+120 kHz','','38+120 kHz','18+38+120 kHz','','200 kHz','18+200 kHz','','38+200 kHz','18+38+200 kHz','','','120+200 kHz','18+120+200 kHz','','38+120+200 kHz','18+38+120+200 kHz','','','','','70 kHz','18+70 kHz','','38+70 kHz','18+38+70 kHz','','','70+120 kHz','18+70+120 kHz','','38+70+120 kHz','18+38+70+120 kHz','','70+200 kHz','18+70+200 kHz','','38+70+200 kHz','18+38+70+200 kHz','','','70+120+200 kHz','18+70+120+200 kHz','','38+70+120+200 kHz','18+38+70+120+200 kHz'};
end
       rgb = rgb / 255.;    
end