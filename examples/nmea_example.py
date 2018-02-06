# -*- coding: utf-8 -*-
"""

THIS EXAMPLE REQUIRES THE PYPROJ AND BASEMAP PACKAGES

These packages are available for windows here:

https://www.lfd.uci.edu/~gohlke/pythonlibs/

Download the files that match your Python version and install using pip.
You must install pyproj before basemap.

D:\temp>pip install pyproj-1.9.5.1-cp36-cp36m-win_amd64.whl
D:\temp>pip install basemap-1.1.0-cp36-cp36m-win_amd64.whl

"""

import numpy as np
from echolab2.instruments import EK60
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


def plot_trackline(lat, lon, raw_positions=None):
    """
    plot_trackline plots a series of lat/lons on a map. It tries to make a nice map,
    but it might fail. You get what you pay for.
    """

    #  determine the min/max coordinates and place in list that will contain our map boundaries.
    lat_bounds = [np.nanmin(lat),0,np.nanmax(lat)]
    lon_bounds = [np.nanmin(lon),0,np.nanmax(lon)]

    #  now calculate the rest of the expanded boundaries and mid-lines - this may or may not work
    #  well for your specific data.
    r = (lat_bounds[2] - lat_bounds[0]) / 2.0
    lat_bounds[1] = lat_bounds[0] + r
    lat_bounds[0] = lat_bounds[0] - (r * (0.5 / r))
    lat_bounds[2] = lat_bounds[2] + (r * (0.5 / r))

    r = (lon_bounds[2] - lon_bounds[0]) / 2.0
    lon_bounds[1] = lon_bounds[0] + r
    lon_bounds[0] = lon_bounds[0] - (r * (0.5 / r))
    lon_bounds[2] = lon_bounds[2] + (r * (0.5 / r))

    #  now create a map projection so we can plot this on a map
    map = Basemap(projection='lcc', lat_0 = lat_bounds[1], lon_0 = lon_bounds[1],
                  resolution = 'h', area_thresh = 0.1, llcrnrlon=lon_bounds[0],
                  llcrnrlat=lat_bounds[0], urcrnrlon=lon_bounds[2],
                  urcrnrlat=lat_bounds[2])

    #  decorate the map
    map.drawcoastlines()
    map.drawmapboundary(fill_color='aqua')
    map.fillcontinents(color='coral',lake_color='aqua')

    #  draw the parallels and meridians
    parallels = np.arange(round(lat_bounds[0],3),round(lat_bounds[2],3),0.5)
    map.drawparallels(parallels,labels=[False,True,True,False])
    meridians = np.arange(round(lon_bounds[0],3),round(lon_bounds[2],3),0.5)
    map.drawmeridians(meridians,labels=[True,False,False,True])

    #  convert our lat/lon values to x,y for plotting.
    x,y = map(lon, lat)

    #  and then plot
    map.plot(x, y, color='r', marker='d', markerfacecolor='None',
            markeredgecolor='r')

    #  if we've been given the raw positions, plot those as marks only
    if (raw_positions is not None):
        #  convert our raw lat/lon values to x,y for plotting.
        x,y = map(raw_positions[1], raw_positions[0])
        map.plot(x, y, linestyle='None', color='b', marker='x')

    #  show the map
    plt.show(block=True)


#  NOTE: We don't really have great data to plot tracklines since we mainly have
#        a bunch of data snippets. The files below work, but aren't going to win
#        any awards for cool maps. You will most likely have to zoom way in to
#        see anything.

#  specify a raw file or files for this example
rawfiles = ['./data/EK60/DY1706_EK60-D20170609-T005736.raw']

#  these files ship with the EK60 software and currently are not in our example data set
#rawfiles = ['./data/EK60/OfotenDemo-D20001214-T145902.raw',
#            './data/EK60/OfotenDemo-D20001214-T154020.raw',
#            './data/EK60/OfotenDemo-D20001214-T162003.raw',
#            './data/EK60/OfotenDemo-D20001214-T164709.raw']

#  these files are in our example dataset
rawfiles = ['./data/EK60/PC1106-D20110830-T034700.raw',
               './data/EK60/PC1106-D20110830-T044817.raw',
               './data/EK60/PC1106-D20110830-T052815.raw',
               './data/EK60/PC1106-D20110830-T053815.raw']

#  create an instance of the EK60 instrument. This is the top level object used
#  to interact with EK60 data sources
ek60 = EK60.EK60()

#  read our raw file
ek60.read_raw(rawfiles)

#  at this point you can print out some basic information about the nmea_data object
print(ek60.nmea_data)

#  and you can extract the data if you want. When calling get_datagrams, the default
#  behavior is to parse the data before returning it. pyecholab2 uses pynmea2 for
#  parsing NMEA data. get_datagrams returns a dictionary keyed by the requested datagram
#  type where the elements themselves are dictionaries that contain a 'time' field
#  and 'nmea_object' field. In the example here, we'll request GGA and VLW data
gga_vlw_data = ek60.nmea_data.get_datagrams(['GGA','VLW'])

#  lets print out the time of the first GGA message and the parsed message data
print(gga_vlw_data['GGA']['time'][0])
print(gga_vlw_data['GGA']['data'][0])

#  As stated, by default the data is parsed so you can access that through the
#  pynmea2 attributes. Check out the pynema2 docs for more info:
#  https://github.com/Knio/pynmea2
print('Parsed pynema2 data:')
print('  Lat:', gga_vlw_data['GGA']['data'][0].latitude)
print('  Lon:', gga_vlw_data['GGA']['data'][0].longitude)

#  and do the same for VLW
print(gga_vlw_data['VLW']['time'][0])
print(gga_vlw_data['VLW']['data'][0])

#  now let's interpolate some data. First we need to get an instance of processed_data
#  since that will contain the time vector we're interpolating to. In this case we grab
#  Sv from the first channel we read.
raw_data = ek60.get_rawdata(channel_number=1)
Sv = raw_data.get_sv()

#  and now we call the interpolate method where we pass the processed_data object and
#  a NMEA message type. By default, we can only interpolate message types that have been
#  defined in the nmea_data class. These definitions are required since we need to be
#  told what actual fields to interpolate since we wouldn't want to and often can't
#  interpolate them all. (There is a keyword that allows you to specify these without
#  having them defined in the class but I am ignoring that right now.)
#
#  So, let's try to interpolate the RMC message which contains lat/lon.
ek60.nmea_data.interpolate(Sv, 'RMC')

#  check what we got:
print(Sv)

#  looks ok but...
print('"RMC" lat:', Sv.latitude[0:10])

#  Oh, it's all NaNs. This is because there wasn't any RMC data to interpolate.
#  That's OK though, 'cause we'll blow your mind with this one. Let's interpolate
#  again, using our 'position' meta-type. Meta-types allow us to specify multiple
#  message types that contain the same data so you don't need to know ahead of
#  time what position data is available. (Note that in the case where multiple
#  position types are available, the first one that covers a given time range will
#  be used.)
ek60.nmea_data.interpolate(Sv, 'position')

#  take a look at what we got:
print('"position" lat:', Sv.latitude[0:10])

#  that's better. There will probably still be a few NaNs since we often
#  get pings before we receive GPS data and those pings end up outside of
#  our interpolated data range.

#  OK, now I'm coming back to something I ignored above. I want to get the
#  non-interpolated lat and lon data so we can plot that on top of the
#  interpolated data to make sure we didn't introduce any boogies. The
#  get_datagrams() method accepts the "return_fields" keyword which, when
#  set to a list of pynmea2 object attribute names, will return arrays
#  of the data contained in those fields instead of returning the pynmea2
#  objects. This can save you a few steps. Once caveat, get_datagrams()
#  doesn't support meta-types so we need to do this manually (this may
#  change in a future version.)
raw_latlon_data = ek60.nmea_data.get_datagrams(['GGA','GLL'],
        return_fields=['latitude', 'longitude'])

#  when calling get_datagrams I still need to know where my data is coming
#  from because the returned dictionary is keyed by message type. With
#  the example files I have used above, none of them have GLL data so
#  my position data will be from the GGA messages. I'm going to extract
#  the raw lat/lon data into a couple of arrays:
raw_lat = raw_latlon_data['GGA']['latitude']
raw_lon = raw_latlon_data['GGA']['longitude']


#  Now let's create a map with the trackline and the raw lat/lon
#  plotted as X's on top of it.
plot_trackline(Sv.latitude[np.isfinite(Sv.latitude)],
               Sv.longitude[np.isfinite(Sv.longitude)],
               raw_positions=[raw_lat,raw_lon])


#  now I'll dive into some of the more specialized NMEA data
#  this code will only fully work with the PC1106 example files since
#  that data has POS-MV data in the raw files.

#  first try to interpolate the POS-MV attitude data. Do this by using the
#  "attitude" meta-type
ek60.nmea_data.interpolate(Sv, 'attitude')

fig = plt.figure()
plt.plot(Sv.ping_time, Sv.heave, color='g', label='heave')
plt.plot(Sv.ping_time, Sv.pitch, color='r', label='pitch')
plt.plot(Sv.ping_time, Sv.roll, color='c', label='roll')
title = 'Heave, Pitch, and Roll'
fig.suptitle(title, fontsize=14)
plt.legend()
plt.show()


#  next interpolate the speed data
ek60.nmea_data.interpolate(Sv, 'speed')

fig = plt.figure()
plt.plot(Sv.ping_time, Sv.spd_over_grnd_kts, color='c', label='Speed over ground')
title = 'Speed over gound in Knots'
fig.suptitle(title, fontsize=14)
plt.legend()
plt.show()


#  and lastly the distance traveled obtained using the SDVLW datagram
#  generated by the ER60 software.
ek60.nmea_data.interpolate(Sv, 'distance')

fig = plt.figure()
plt.plot(Sv.ping_time, Sv.trip_distance_nmi, color='c', label='distance (nmi)')
title = 'Distance travelled in nmi'
fig.suptitle(title, fontsize=14)
plt.legend()
plt.show()



