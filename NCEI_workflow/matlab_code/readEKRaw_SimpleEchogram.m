function [fh, ih] = readEKRaw_SimpleEchogram(data, x, y, varargin)
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
%          Colormap:    Set this parameter a N x 3 array defining the colormap
%                       to use for the echogram image.
%                           Default: Simrad EK500 Colormap
%
%  DisplayThreshold:    Set this parameter to a 2 element vector [low, high]
%                       specifying the values used in scaling the data for
%                       display.
%                           Default [-70, -34];
%
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

%   Rick Towler
%   National Oceanic and Atmospheric Administration
%   Alaska Fisheries Science Center
%   Midwater Assesment and Conservation Engineering Group
%   rick.towler@noaa.gov

%-

%  set default parameters
dThreshold = [-72 -36]; %[-70 -34];
yLabelText = 'Range (m)';
xLabelText = 'Ping';
pTitle = 'Echogram';
dataRGB = ek500();
fh = [];

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
        case 'colormap'
            ctSize = size(varargin{n + 1});
            if (ctSize(2) == 3) && (ctSize(1) < 256)
                dataRGB = varargin{n + 1};
            else
                warning('readEKRaw:ParameterError', ...
                    ['Colormap - Colormap must be an n x 3 array of ' ...
                    'RGB values where n < 256.']);
            end
        case 'title'
            pTitle = varargin{n + 1};
        case 'figure'
            fh = varargin{n + 1};
        otherwise
            warning('readEKRaw:ParameterError', ...
                ['Unknown property name: ' varargin{n}]);
    end
end

% scale data to byte values corresponding to color table entries
ctBot = 1;
ctTop = length(dataRGB);
ctRng = ctTop - ctBot;
    data = uint8(ceil((data - dThreshold(1)) / (dThreshold(2) - ...
        dThreshold(1)) * ctRng) + ctBot);

%  create or raise figure
if (isempty(fh))
    fh = figure();
else
    figure(fh);
end

%  create the echogram image
ih = image(x, y, data, 'CDataMapping', 'direct');
set(gca, 'XGrid', 'on', 'Units','pixels');

%  set figure properties
hrscb=['fp=get(gcbo,''Position''); ah=get(gcbo,''UserData'');' ...
    'p=[0,0,fp(3),fp(4)]; set(ah,''OuterPosition'',p);'];
set (fh, 'ResizeFcn', hrscb, 'Units','pixels', 'UserData', gca);

tmp = abs(dThreshold(1)) - abs(dThreshold(2));
tickMarks = dThreshold(1):tmp/4:dThreshold(2);

%  set the colormap
colormap(dataRGB);
colorbar('YTick',[0.5,3.5,6.5,9.5,12.5],'YTickLabel',{num2str(tickMarks(1)),num2str(tickMarks(2)),num2str(tickMarks(3)),num2str(tickMarks(4)),num2str(tickMarks(5))});

%  label
xlabel(xLabelText,'FontName','Times','FontSize',14);
ylabel(yLabelText,'FontName','Times','FontSize',14);
title(pTitle,'FontName','Times','FontSize',14,'Interpreter','none');
datetick
xlim([min(x) max(x)])

end

function rgb = ek500()
%  ek500 - return a 13x3 array of RGB values representing the Simrad EK500 color table

    rgb = [[255 255 255];
           [159 159 159];
           [095 095 095];
           [000 000 255];
           [000 000 127];
           [000 191 000];
           [000 127 000];
           [255 255 000];
           [255 127 000];
           [255 000 191];
           [255 000 000];
           [166 083 060];
           [120 060 040]];

   rgb = rgb / 255.;
   
end