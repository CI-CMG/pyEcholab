 function data = plotEchoviewCSV_NEW(data,numfreq,ExportFolder)
%% Set title for figure 
files = data.file;
ind = strfind(files,'_to_');

if isempty(ind)
%     title = ({'Sv at 38 kHz',files, ['Data points removed: ' num2str(ceil(data.QC)) '%']});
    %%%%%%%%%% Needed for PC1201/PC1202, title text too long
%     ind2 = strfind(files,'-D');
%     if isempty(ind2)
        title = files;        
%     else
%         title = ({files(1:ind2(1)-1),files((ind2(1)+1):end)});
%     end

else
    title = ({[files(1:ind-1) ' to'], files((ind+4):end)});
%         title = ({'Sv at 38 kHz',[files(1:ind-1) ' to'], files((ind+4):end), ['Data points removed: ' num2str(ceil(data.QC)) '%']});
    %%%%%%%%%% Needed for PC1201/PC1202, title text too long
%     str1 = 'GU1406-EK60-GOM';
%     ind2 = strfind(files,'-D');
%     str2 = files(ind2(1)+1:ind(1)-1);
% % %     str3 = files(ind2(3)+1:end);
%     str3 = files(ind2(2)+1:end);
%     title = ({str1,[str2 ' to '], str3});
end

%% Set x axis title for figure
    dates = datenum(data.Ping_date);
    minDate = min(dates); maxDate = max(dates);

    if maxDate - minDate > 0
        xtitle = {'Time in UTC (hour:min)',[datestr(minDate) ' to ' datestr(maxDate)]};
    else
        xtitle = {'Time in UTC (hour:min)',datestr(minDate)};
    end

%% Set figure properties
%  create or raise figure
    disp(['Plotting ' files]);
    fh = figure(2);clf %
    height = 5; %7
    width = 9;  %12
    FigDim =[0.1 0 width height];   
    left_color = [0 0 0];
    right_color = [0 0 0];
    set(fh,'units','inches','position',FigDim,'Color','w', 'InvertHardCopy', 'off');
    set(fh, 'PaperUnits', 'inches','PaperSize', [width height], 'PaperPositionMode', 'manual', 'PaperPosition', [0 0 width height]);
    set(fh,'defaultAxesColorOrder',[left_color; right_color]);
        
%% Call plotting program
   if numfreq == 1       
       data.newData(data.newData == 2) = NaN;
       readEKRaw_SimpleEchogram(data.newData', data.newTime, ...
            data.newRange,'threshold',[-72 -34], 'Title', title, 'XLabel', ...  %%[-70 -34]
            xtitle, 'YLabel','Depth (m)','figure',fh);   
   else
            plotEchogram_EK60Multifreq(data.newData', data.newTime, ... 
            data.newRange, 'Title', title, 'XLabel', xtitle, 'YLabel','Depth (m)',...
            'NumFreq',numfreq,'figure',fh);    
   end

%% Plot bottom variables.     
    if ~isempty(data.Bottom) 
        hold on
    % Plot bottom   
        plot(data.Bottom(:,5),data.Bottom(:,3),'.k'); 
% % % %         plot(data.evlBottom.timestamp,data.evlBottom.bottom,'.r');
% % % %         y = moving(data.Bottom(:,3),3,'median');
% % % %         plot(data.Bottom(:,5),y,'.r')
        hold off
        maxDepth = max(data.Bottom(:,3));
        
    else
    % Plot estimated bottom from ETOPO1/GEBCO data
        hold on
        plot(data.PingDatenum,data.estBottom,'--','Color',[0.22 0.22 0.22],'LineWidth',1);  
        hold off
        maxDepth = max(data.estBottom);
    end  

%% Set Y axis scale based on a range of depths
    if maxDepth < 100
        ylim([0 104])
    elseif (maxDepth >= 100) && (maxDepth < 500)
        ylim([0 520])
    elseif (maxDepth >= 500) && (maxDepth < 1000)
        ylim([0 1049])
    elseif (maxDepth >=1000) && (maxDepth < 2500)
        ylim([0 2600])
    elseif (maxDepth >=2500) && (maxDepth < 5000)
        ylim([0 5200])
    else
        if ~isnan(maxDepth)
            ylim([0 (maxDepth+10)])
        end
    end    
    set(gca,'YDir','reverse');
    
%% Add NOAA logo
    file = 'NOAA_logo.png';
    addLogo(file, [-10,-10,50,50]);
    
%% Add day/night legend
    leg = 'day_night_legend.png';
    addLogo(leg, [0,65,75,45]);
    
%% Add sun cycle
    yyaxis right
    time = data.PingDatenum';
    one = ones(length(data.day),1);
    nights = abs(data.day-one);
    X=[time,fliplr(time)];
    Y=[nights',fliplr(zeros(1,length(nights)))];
    
    plot(time,one,'k')
    hold on
    fill(X,Y,[0.5 0.5 0.5],'EdgeColor','k')
    hold off
    ylim([0 25]);      

% % %     plot(data.PingDatenum,data.day);
% % %     ylim([-0.5 5]);
    set(gca,'YTick',0)
    set(gca,'YTickLabel','');
    
%% Save figure as png, close figure window
    imagename = [ExportFolder,'\', char(cellstr(files)),'.png']; %% char(cellstr(*)) added to remove white space after filename
    print(gcf,'-dpng','-r300',imagename) ;
    disp(['Saved ' files])
    close all;
    