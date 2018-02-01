function hPanel = addLogo(filename, pixelPosition, hContainer)
% addLogo - adds the specified logo image at the specified container pixel position
%

% Syntax:
%           hPanel = addLogo(filename,pixelPosition,hContainer)
%
% Description:
%
%           addLogo(filename) adds the image specified by filename to the
%           top-left position in the current figure.
%
%           All the standard image types recognised in modern browsers (HTML)
%           are accepted, including GIF, JPG and PNG. Animated GIFs and
%           transparent images are also accepted. Note that transparent images
%           will show the container's background, but not any axes or control
%           that lie between the container and the image.
%
%           addLogo(filename,pixelPosition) adds the image to the current
%           figure, at the position specified by pixelPosition. Both relative
%           and absolute positions are supported, as well as image resizing.
%
%           addLogo(filename,pixelPosition,hContainer) adds the image to the
%           specified container, which is a handle to a figure/panel/etc.
%
% Inputs:
%         - filename (mandatory): name of logo image file (full or relative path)
%         - pixelPosition (optional): position in parent container: [X,Y,W,H]
%                 default value = [1,0,0,0], i.e. top-left corner of container
%                 empty pixelPosition ([]) means to use the default value (=[1,0,0,0])
%                 X value can be <=0, meaning left from container's right edge
%                 Y value can be <=0, meaning below container's top edge
%                 Width/Height values are optional (default=0)
%                 Width/Height values can be 0, meaning the image's actual width/height
%                 Width/Height values can be negative, meaning resized from image size
%                 Width/Height values can be positive, meaning resized to specified size
%                 [1,0,0,0] = top-left     corner of container (default value)
%                 [1,1,0,0] = bottom-left  corner of container
%                 [0,0,0,0] = top-right    corner of container
%                 [0,1,0,0] = bottom-right corner of container
%         - hContainer (optional): handle to parent container. default=gcf
%
% Outputs:
%         - hPanel - handle to panel containing the image (can be resized/deleted/etc.)
%                    (the child JLabel handle is provided in hPanel's UserData property)
%
% Example:
%           addLogo('image.jpg');          % add image at top-left of current figure
%           addLogo('image.jpg',[]);             % same as above
%           addLogo('image.jpg',[1,0]);          % same as above
%           addLogo('image.jpg',[1,0,0,0],gcf);  % same as above
%
%           addLogo('logo.png',[0,1]);     % add image at bottom-right of current figure
%           addLogo('logo.png',[90,230]);        % add image at position X=90, Y=230
%           addLogo('logo.png',[90,230,50,85]);  % add 50x85 resized image at 90,230
%
%           addLogo('abc.gif',[-10,-10,50,85]);  % add 50x85 resized image at top-right
%
%           addLogo('abc.gif',[],hPanel);  % add at top-left of containing hPanel
%
% Technical Description:
%           See http://UndocumentedMatlab.com/blog/displaying-animated-gifs
%
% Bugs and suggestions:
%    Please send to Yair Altman (altmany at gmail dot com)
%
% Limitations:
%    In some cases Matlab may require the containing figure to be visible for addLogo to work.
%    This is not always the case, so check this issue on your specific platform/application.
%
% Change log:
%    2013-06-27: First version posted on <a href="http://www.mathworks.com/matlabcentral/fileexchange/authors/27420">MathWorks File Exchange</a>
%    2013-07-02: Fix for files on current folder

% License to use and modify this code is granted freely to all interested, as long as the original author is
% referenced and attributed as such. The original author maintains the right to be solely associated with this work.

% Programmed and Copyright by Yair M. Altman: altmany(at)gmail.com
% $Revision: 1.02 $  $Date: 2013/07/02 16:04:31 $

    % Process input args
    if nargin<1,  error('Missing filename');  end
    if nargin<2 || isempty(pixelPosition),  pixelPosition = [1,0,0,0];  end
    if nargin<3,  hContainer = gcf;  end

    % Process image file
    [imgWidth, imgHeight, filename] = processImageFile(filename);
    
    % Process position
    pixelPosition = processPosition(hContainer, pixelPosition, imgWidth, imgHeight);

    % Create an HTML JLabel
    htmlStr = sprintf('<html><img src="file:/%s" width="%d" height="%d">', filename, pixelPosition(3:4));
    jLabel = javax.swing.JLabel(htmlStr);
    try jLabel = javaObjectEDT(jLabel); catch, end  % does not work on old Matlab releases

    % Align the background color with the container's (useful for transparent images)
    try
        color = get(hContainer,'Color');
    catch
        color = get(hContainer,'BackgroundColor');
    end
    colors = num2cell(color);
    jLabel.setBackground(java.awt.Color(colors{:}));

    % Display in parent container
    [hjLabel,hPanelContainer] = javacomponent(jLabel, pixelPosition, hContainer);
    set(hPanelContainer,'UserData',hjLabel, 'Units','normalized', 'BackgroundColor',color);
    drawnow;

    % Return containing panel, if requested
    if nargout
        hPanel = hPanelContainer;
    end
    
end  % addLogo

% Process image file (search full/relative path), return image size
function [imgWidth,imgHeight,filename] = processImageFile(filename)
    % Search for the file, get the full pathname if exists on path
    f = which(filename);
    if ~isempty(f)
        filename = f;
    elseif ~exist(filename,'file')  % Fix for files on current folder
        error([filename ' file was not found']);
    end
    
    % File found - load it to get the image size
    image = javax.swing.ImageIcon(filename);
    imgWidth  = image.getIconWidth;
    imgHeight = image.getIconHeight;

    % Sanity check
    if imgWidth<1 || imgHeight<1
        error(['Could not read ' filename ' as an image file']);
    end    
end  % processImageFile

% Process position, return absolute pixel position in parent container
function pixelPosition = processPosition(hContainer, pixelPosition, imgWidth, imgHeight)
    % Get the parent container's pixel position
    parentPos = getpixelposition(hContainer);

    % Pad with 0 values
    pixelPosition(end+1:4) = 0;

    % Process Width
    w = pixelPosition(3);
    if w <= 0
        w = imgWidth + w;
    end

    % Process Height
    h = pixelPosition(4);
    if h <= 0
        h = imgHeight + h;
    end

    % Process X
    x = pixelPosition(1);
    if x <= 0
        x = parentPos(3) + x - w;
    end

    % Process Y
    y = pixelPosition(2);
    if y <= 0
        y = parentPos(4) + y - h;
    end

    pixelPosition = [x, y, w, h];
end  % processPosition