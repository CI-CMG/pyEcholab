

import shapefile
import cPickle as pickle
import numpy as np


def pickleShapefile(shapefile, pickleFile, projection, scaler, bounds=None):

    data = readShapefile(shapefile, projection, scaler, bounds=bounds)

    output = open(pickleFile, 'wb')
    pickle.dump(data, output)
    output.close()


def pickleMapLayer(data, globalBounds, style, pickleFile):

    data['globalBounds'] = globalBounds
    data['style'] = style

    output = open(pickleFile, 'wb')
    pickle.dump(data, output)
    output.close()


def transform(data, bounds):

    #  try to determine the dimensions of the data. We need to check if
    #  it is one long list of lon,lat values or if it is a list of long
    #  lists.
    try:
        if (len(data[0][0]) > 0):
            #  this must be a list of lists
            nPolys = len(data['polygons'])
        else:
            #  we can end up here if the first polygon is empty. I don't think
            #  this actually will happen after we convert coords but just in
            #  case we'll assume tit can.
            nPolys = len(data['polygons'])
    except:
        #  if we can't get a length of a double nested list, it must not be
        #  doubly nested.
        nPolys = 1

    data['bounds'][0] = data['bounds'][0] - bounds[0]
    data['bounds'][1] = data['bounds'][1] - bounds[1]

    for i in range(nPolys):
        xPoly = np.array(data['polygons'][i])
        xPoly[:,0] = xPoly[:,0] - bounds[0]
        xPoly[:,1] = xPoly[:,1] - bounds[1]

        data['polygons'][i] = zip(xPoly[:,0],xPoly[:,1])

    return data


def getGlobalBounds(bounds):
    """
    Given a list of bounds, getGlobalBounds returns the bounds that encompass all of the
    provided bounds.
    """
    dataBounds = [np.Inf, np.Inf, -np.Inf, -np.Inf]

    for bound in bounds:

        if (bound[0] < dataBounds[0]):
            dataBounds[0] = bound[0]
        if (bound[1] < dataBounds[1]):
            dataBounds[1] = bound[1]
        if (bound[2] > dataBounds[2]):
            dataBounds[2] = bound[2]
        if (bound[2] > dataBounds[3]):
            dataBounds[3] = bound[2]

    return dataBounds


def readShapefile(filename, projection, scaler, bounds=None):
    """
    readShapefile reads a shapefile, transforms the data into x,y coordinates using
    the provided pyproj transformation projection, and then forms it into a dictionary.

    """

    #  initialize some variables
    dataBounds = None
    data = {'object':[], 'polygons':[], 'scaler':scaler, 'bounds':[]}

    #  read the shapefile
    sfile = shapefile.Reader(filename)

    #  extract the elements of interest
    shapes = sfile.shapes()
    records = sfile.records()
    nShapes = len(shapes)

    #  iterate through the shapes and process
    for i in range(nShapes):

        #  convert the lat/lon data in the shapes
        xyData, dataBounds = convertCoords(shapes[i].points, projection, scaler,
                clipBounds=bounds, dataBounds=dataBounds, applyBounds=False)

        if (len(xyData) > 0):
            #  append the polygon data
            data['polygons'].append(xyData)
            #  append the object name/identifier
            data['object'].append(str(records[i][13]).strip())

    data['bounds'] = dataBounds

    return data


def convertCoords(data, projection, scaler, clipBounds=None, dataBounds=None,
        applyBounds=True):

    #  set dataBounds if not provided
    if (dataBounds == None):
        dataBounds = [np.Inf, np.Inf, -np.Inf, -np.Inf]
    #  set scaler if not provided
    if (scaler == None):
        scaler = 1.0

    #  convert our list if lists into a numpy array
    data = np.array(data)

    #  convert lat/lon to x,y values using the provided projection
    if (data.ndim > 1):
        x,y = projection(data[:,0], data[:,1])
    else:
        x,y = projection(data[0], data[1])

    #  apply the bounds
    if (clipBounds):
        #  convert the clipping bounds
        clipBounds = [projection(clipBounds[0][0],clipBounds[0][1]),
                      projection(clipBounds[1][0],clipBounds[1][1])]

        #  create the masks to clip values outside our bounds
        xgm = x > clipBounds[0][0]
        xlm = x < clipBounds[1][0]
        ygm = y > clipBounds[0][1]
        ylm = y < clipBounds[1][1]

        #  apply the masks
        x = x[xgm & xlm & ygm & ylm]
        y = y[xgm & xlm & ygm & ylm]

    #  if there is any data left after clipping, scale and get the bounds
    data = []
    if (len(x) > 0):
        #  transform the data so it is more QGraphicsView friendly. This entails
        #  dividing the x/y values to bring it into a reasonable range and flipping
        #  the y axis to align with QGraphicsView's coordinate system. The scalar will
        #  depend on the projection used.
        x = x / scaler
        y = y / -scaler

        if (applyBounds):
            #  apply the offset portion of the bounds to these coordinates
            x = x - dataBounds[0]
            y = y - dataBounds[1]
        else:
            #  determine the bounds of this object
            minX = np.amin(x)
            if (minX < dataBounds[0]):
                dataBounds[0] = minX
            minY = np.amin(y)
            if (minY < dataBounds[1]):
                dataBounds[1] = minY
            maxX = np.amax(x)
            width = maxX - minX
            if (width > dataBounds[2]):
                dataBounds[2] = width
            maxY = np.amax(y)
            height = maxY - minY
            if (height > dataBounds[3]):
                dataBounds[3] = height

        #  reform the converted data
        data = zip(x, y)

    return [data, dataBounds]
