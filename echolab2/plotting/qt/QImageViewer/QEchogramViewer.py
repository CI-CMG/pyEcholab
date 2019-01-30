
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy
import datetime
from QViewerBase import QViewerBase


class QEchogramViewer(QViewerBase):

    def __init__(self, parent=None, useGL=False, backgroundColor=[50,50,50]):
        super(QEchogramViewer, self).__init__(parent, useGL=useGL,
                backgroundColor=backgroundColor)

        #  define the default public properties
        self.name = 'QEchogramViewer'

        self.threshold = [-70,-34]
        self.echogramData = None
        self.isIndexedData = False
        self.echogramAlphaMask = None
        self.yAxis = None
        self.xAxis = None

        #  the "time" axes are internal vectors that contain time converted to a serial date
        #  number expressed as the number of seconds from 1-1-1970 00:00:00 UTC.
        self.__xTimeAxis = None
        self.__yTimeAxis = None

        #  set the default SIMRAD EK500 color table (plus light gray)
        self.setColorTable()


    def setEchogramFromRawFile(self, filename):
        pass


    def setEchogramFromArray(self, echogramData, xaxis=None, yaxis=None, scale=True):
        """
        setEchogramFromArray sets the echogram data from a 2d numpy array containing
        Sv or Ts data. You can also specify 1d vectors representing the axes units,
        for example setting the y axis to a vector that maps sample (pixel) number to
        range and setting the x axis to a vector that maps ping number to time.

        Set scale to False if you are passing already scaled data meaning the data
        values map directly into the color map you are using. By default this class
        uses the Simrad color table (plus grey) which contains 14 elements (0-13). If
        scale is set to true, the data will be scaled to the color table indicies using
        the provided display thresholds.
        """

        #  set the echogram data
        self.echogramData =  numpy.flipud(numpy.rot90(echogramData,1)).copy()
        nSamples, nPings = self.echogramData.shape

        #  set the data type, indexed or not indexed
        self.isIndexedData = not scale;

        #  set the X axis values
        if (type(xaxis) is type(None)):
            self.xAxis = numpy.arange(nPings) + 1
        else:
            if (len(xaxis) == nPings):
                self.xAxis = xaxis

                #  check if this axis is time based and if so, serialize
                if (type(xaxis[0]) in (numpy.datetime64,)):
                    self.__xTimeAxis = self.serializeTime(xaxis)
                else:
                    self.__xTimeAxis = None
            else:
                raise ValueError('xaxis dimension must match echogram width.')

        #  set the Y axis values
        if (type(yaxis) is type(None)):
            self.yAxis = numpy.arange(nSamples) + 1
        else:
            if (len(yaxis) == nSamples):
                self.yAxis = yaxis

                #  check if this axis is time based and if so, serialize
                if (type(yaxis[0]) in (numpy.datetime64,)):
                    self.__yTimeAxis = self.serializeTime(yaxis)
                else:
                    self.__yTimeAxis = None

            else:
                raise ValueError('yaxis dimension must match echogram height.')

        #  update the echogram pixmap
        self.updateEchogram()


    def setThresholds(self, min, max):

        self.threshold = [min,max]

        #  update the echogram pixmap
        self.updateEchogram()


    def updateEchogram(self):

        #  make sure we have data to work with
        if (type(self.echogramData) is type(None)):
            #  nothing to do - no data to plot
            return

        if (self.isIndexedData == False):
            #  scale the data to the color table
            echoData = numpy.round((self.echogramData - self.threshold[0]) / (self.threshold[1] -
                                    self.threshold[0]) * self.__ctLength)

            badData = numpy.isnan(echoData)
            echoData[echoData < 0] = 0
            echoData[echoData > self.__ctLength-1] = self.__ctLength-1
            echoData[badData] = 14
            echoData = echoData.astype(numpy.uint8)

        #  create the image object from the echogram data
        image = QImage(echoData.data, echoData.shape[1], echoData.shape[0], echoData.shape[1],
                       QImage.Format_Indexed8)
        image.setColorTable(self.__colorTable)

        #  and convert to ARGB
        image = image.convertToFormat(QImage.Format_ARGB32)

        #  apply alpha mask
        if (self.echogramAlphaMask):
            image.setAlphaChannel(self.echogramAlphaMask)

        #  get a pixmap to display
        self.imgPixmap = QPixmap().fromImage(image)

        #  update the pixmap
        self.imgPixmapItem.setPixmap(self.imgPixmap)


    def addText(self, position, text, useXY=False, **kwargs):
        """
        Add text to the scene given the text and position. The function returns the reference
        to the QIVMarkerText object that is added to the scene.

        The x,y values should be provided in the units specified for the axes when the echogram was
        created. So, for example, if the X axis was defined with time values, you must pass x vertices
        that are datetime objects. If the y axis was defined with range values, you must pass y
        vertices that are in range units. This method will then transform the vertices to the underlying
        ping/sample coordinate system before plotting.

        If you set the useXY keyword to true, this method will not transform the coordinates. This can
        be used if you want to pass vertices as ping number, sample number pairs.

              text (string)   - The text to add to the scene.
          position (QPointF)  - The position of the text anchor point. If useXY is False, the
                                position must be in lon/lat. If useXY is True the position will
                                be in transformed x,y coordinates.
              size (int)      - The text size, in point size
              font (string)   - A string containing the font family to use. Either stick
                                to the basics with this (i.e. "times", "helvetica") or
                                consult the QFont docs.
           italics (bool)     - Set to true to italicise the font.
            weight (int)      - Set to an integer in the range 0-99. 50 is normal, 75 is bold.
             color (list)     - A 3 element list or tuple containing the RGB triplet
                                specifying the color of the text.
             alpha (int)      - An integer specifying the opacity of the text. 0 is transparent
                                and 255 is solid.
            halign (string)   - Set this value to set the horizontal anchor point. Values are:
                                   'left' - Sets the anchor to the left side of the text
                                   'center' - Sets the anchor to the middle of the text
                                   'right' - Sets the anchor to the right side of the text
            valign (string)   - Set this value to set the vertical anchor point. Values are:
                                   'top' - Sets the anchor to the top of the text
                                   'center' - Sets the anchor to the middle of the text
                                   'bottom' - Sets the anchor to the bottom of the text
            name (string)     - Set this to the name associated with the text object. The name
                                can be used to differentiate between your text objects.
        """

        if (not useXY):
            position = self.axesToPixels(position)

        return super(QEchogramViewer, self).addText(position, text, **kwargs)


    def addPolygon(self, verts, useXY=False, closed=False, **kwargs):
        """
        Add an arbitrary polygon to the echogram. This includes lines with more than 2 vertices
        such as bottom detection lines. Verts can be a list of x,y pairs or a list of Point2f objects
        defining the polygon.

        The x,y values should be provided in the units specified for the axes when the echogram was
        created. So, for example, if the X axis was defined with time values, you must pass x vertices
        that are datetime objects. If the y axis was defined with range values, you must pass y
        vertices that are in range units. This method will then transform the vertices to the underlying
        ping/sample coordinate system before plotting.

        If you set the useXY keyword to true, this method will not transform the coordinates. This can
        be used if you want to pass vertices as ping number, sample number pairs.

                color (list)  - A 3 element list or tuple containing the RGB triplet
                                specifying the color of the text.
            thickness (float) - A float specifying the line thickness. Note that thickness
                                is related to scale. The larger your scene is, the thicker
                                your lines will need to be to be visible when zoomed out.
                alpha (int)   - An integer specifying the opacity of the text. 0 is transparent
                                and 255 is solid.
            linestyle (string)- A character specifying the polygon outline style. "=" is a solid
                                line, "-" is a dashed line, and "." is a dotted line.
                 fill (list)  - Set to a 3 or 4 element list that specifys the RGBA color of the
                                polygon fill. If set to None, the polygon will not be filled.
           selectable (bool)  - Set to True to make the polygon selectable. If selectable the item
                                will be included in QImageView mousePressEvent and mouseReleaseEvent
                                events.
              movable (bool)  - Set to True to make the polygon movable. If movable the item
                                will be moved if it is selected and dragged.
               closed (bool)  - Set to True to draw closed polygons (meaning the last vertex will be
                                connected to the first) or False to draw unconnected polygons (also
                                known as paths.) If fill is set, the polygon will always be
                                closed since the fill will flood the path, though there will not be
                                an edge on the "open" part of the path.

                                While "open" unfilled polygons are visually the same as lines, they
                                differ in that the "hit box" for the polygon generated line is a
                                axially aligned box containing all of the vertices. A line added
                                via the "addLine" method will have a hit box that follows the line
                                path allowing for precise selection of the line.
        """
        if (not useXY):
            verts = self.axesToPixels(verts)

        return super(QEchogramViewer, self).addPolygon(verts, closed=closed, **kwargs)


    def addLine(self, verts, useXY=False, **kwargs):
        """
        Add an arbitrary line to the scene. Verts can be a list of 2 x,y
        pairs (line start, line end) or a list of 2 Point2f objects defining
        the line.

        The x,y values should be provided in the units specified for the axes when the echogram was
        created. So, for example, if the X axis was defined with time values, you must pass x vertices
        that are datetime objects. If the y axis was defined with range values, you must pass y
        vertices that are in range units. This method will then transform the vertices to the underlying
        ping/sample coordinate system before plotting.

        If you set the useXY keyword to true, this method will not transform the coordinates. This can
        be used if you want to pass vertices as ping number, sample number pairs.

                color (list)  - A 3 element list or tuple containing the RGB triplet
                                specifying the color of the text.
            thickness (float) - A float specifying the line thickness. Note that thickness
                                is related to scale. The larger your scene is, the thicker
                                your lines will need to be to be visible when zoomed out.
                alpha (int)   - An integer specifying the opacity of the text. 0 is transparent
                                and 255 is solid.
            linestyle (string)- A character specifying the polygon outline style. "=" is a solid
                                line, "-" is a dashed line, and "." is a dotted line.
           selectable (bool)  - Set to True to make the polygon selectable. If selectable the item
                                will be included in QImageView mousePressEvent and mouseReleaseEvent
                                events.
              movable (bool)  - Set to True to make the polygon movable. If movable the item
                                will be moved if it is selected and dragged.

        """

        if (not useXY):
            verts = self.axesToPixels(verts)

        #return super(QEchogramViewer, self).addLine([verts[0][0], verts[0][1], verts[1][0], verts[1][1]], **kwargs)
        return super(QEchogramViewer, self).addLine(verts, **kwargs)


    def addMark(self, position, useXY=False, name='QEGMarker', **kwargs):
        """
        Add a marker to the echogram. Position must be a 2 element list/tuple as (x,y). The x,y values
        will be converted to ping,sample values and then plotted. You can add marker text using the
        marker's addLabel method.

        The x,y values should be provided in the units specified for the axes when the echogram was
        created. So, for example, if the X axis was defined with time values, you must pass x vertices
        that are datetime objects. If the y axis was defined with range values, you must pass y
        vertices that are in range units. This method will then transform the vertices to the underlying
        ping/sample coordinate system before plotting.

        If you set the useXY keyword to true, this method will not transform the coordinates. This can
        be used if you want to pass vertices as ping number, sample number pairs.


        Marker Options:

               style (string) - "+" for a plus mark. "x" for an X mark, "d" for a diamond, "o" for circle.
                 color (list) - a 3 element list or tuple containing the RGB triplet
                                specifying the color or the mark.
           selectColor (list) - a 3 element list or tuple containing the RGB triplet
                                specifying the color the mark will change to when selected.
                 size (float) - a float value specifying the scaling factor. The value must
                                be greater than 0. Values less than 1 will shrink the marker
                                and values greater then 1 will grow it.
            thickness (float) - A float specifying the thickness of the marker's outline.
      selectThickness (float) - A float specifying the thickness of the marker's outline when selected.
              alpha (integer) - A integer specifying the opacity of the mark. 0 is transparent
                                and 255 is solid.
                name (string) - A string specifying the name associated with this mark. You
                                can use mark names to differentiate between your marks.
        """

        #  check if we need to convert the points
        if (not useXY):
            position = self.axesToPixels(position)

        return super(QEchogramViewer, self).addMark(QPointF(position[0][0], position[0][1]), name=name, **kwargs)


    def centerOnPoint(self, point, useXY=False):
        """
        Centers the view on the provided point. Point can be a list containing the
        [x,y] location or a Point2f object.
        """

        #  convert point objects to list
        inClass = point.__class__.__name__.lower()
        #  check if we've been passed an OpenCV Point2f object
        if inClass == 'point2f':
            #  convert the Point2f object to a simple list
            point = [[point.x, point.y]]

        #  check if we've been passed an OpenCV Point2f object
        elif (inClass == 'qpointf') or (inClass == 'qpoint'):
            #  convert the Point2f object to a simple list
            point = [[point.x(), point.y()]]

        #  check if we need to convert the points
        if (not useXY):
            position = self.axesToPixels(point)

        return super(QEchogramViewer, self).centerOnPoint(QPointF(position[0][0], position[0][1]))


    def zoomToPoint(self, point, zoomLevel, useXY=False):
        """
        Zooms the view to a point on the image given a point and a zoom level (int).
        Point can be a list containing the [x,y] location or a Point2f object.
        """

        #  convert point objects to list
        inClass = point.__class__.__name__.lower()
        #  check if we've been passed an OpenCV Point2f object
        if inClass == 'point2f':
            #  convert the Point2f object to a simple list
            point = [[point.x, point.y]]

        #  check if we've been passed an OpenCV Point2f object
        elif (inClass == 'qpointf') or (inClass == 'qpoint'):
            #  convert the Point2f object to a simple list
            point = [[point.x(), point.y()]]

        #  check if we need to convert the points
        if (not useXY):
            position = self.axesToPixels(point)

        return super(QEchogramViewer, self).zoomToPoint(QPointF(position[0][0], position[0][1]))


    def pixelToAxes(self, pixel):
        """
        pixelToAxes converts the pixel value in the provided QPoint/QPointF to
        the nearest axes values
        """

        x = int(round(pixel.x()))
        y = int(round(pixel.y()))

        if ((self.xAxis.__class__.__name__.lower() == 'nonetype') or
            (self.yAxis.__class__.__name__.lower() == 'nonetype')):
            axesPoint = [None, None]
        elif (x < 0 or y < 0 or x >= len(self.xAxis) or y >= len(self.yAxis)):
            axesPoint = [None, None]
        else:
            axesPoint = [self.xAxis[x],self.yAxis[y]]

        return(axesPoint)


    def axesToPixels(self, axesVerts):
        '''
        axesToPixels converts from axes values to pixel values. axesVerts can be
        a list comprised of [x,y] tuples, or it can be a list of lists 2 elements
        long where the first list contains x locations and the second list
        contains y locations.

            axesVerts = [[1,2],[3,4],[5,6],[7,8],[9,10]]

              -or-

            axesVerts = [[1,3,5,7,9],[2,4,6,8,10]]

        Note that values are ALWAYS returned as a list of [x,y] tuples. This is because
        our parent's plotting methods accept vertices in this form.

        axesToPixels will convert the provided axes values to the closest pixel value.
        It does not interpolate between values.
        '''

        xIsTime = False
        yIsTime = False
        pixelPoints = []

        #  first determine what form our vertices are in
        if (len(axesVerts) > 1):
            #  we have been passed a list of [x,y] tuples

            #  check if we're dealing with time on any of our axes
            if (type(axesVerts[0][0]) in (datetime.datetime, numpy.datetime64)):
                xIsTime = True
            if (type(axesVerts[0][1]) in (datetime.datetime, numpy.datetime64)):
                yIsTime = True

            #  iterate thru the list of verts, converting to pixel values
            for verts in axesVerts:
                if (xIsTime):
                    #  serialize this vertex's time value and find closest match
                    xIdx = (numpy.abs(self.__xTimeAxis - self.serializeTime(verts[0]))).argmin()
                else:
                    #  find the closest match to this x value
                    xIdx = (numpy.abs(self.xAxis - verts[0])).argmin()
                if (yIsTime):
                    #  serialize this vertex's time value and find closest match
                    yIdx = (numpy.abs(self.__yTimeAxis - self.serializeTime(verts[1]))).argmin()
                else:
                    #  find the closest match to this y value
                    yIdx = (numpy.abs(self.yAxis - verts[1])).argmin()

                #  append this converted vertex to the list of verts to return
                pixelPoints.append([xIdx,yIdx])

        else:
            #  we have been passed a list of lists 2 elements long

            #  check if we're dealing with time on any of our axes
            if (type(axesVerts[0][0]) in (datetime.datetime, numpy.datetime64)):
                xIdx = (numpy.abs(self.__xTimeAxis - self.serializeTime(axesVerts[0][0]))).argmin()
            else:
                #  find the closest match to this x value
                xIdx = (numpy.abs(self.xAxis - axesVerts[0][0])).argmin()
            if (type(axesVerts[0][1]) in (datetime.datetime, numpy.datetime64)):
                #  serialize this vertex's time value and find closest match
                yIdx = (numpy.abs(self.__yTimeAxis - self.serializeTime(axesVerts[0][1]))).argmin()
            else:
                #  find the closest match to this y value
                yIdx = (numpy.abs(self.yAxis - axesVerts[0][1])).argmin()

                #  append this converted vertex to the list of verts to return
            pixelPoints.append([xIdx,yIdx])

        return pixelPoints


    def serializeTime(self, times):
        '''
        serializeTime converts a datetime.datetime object to a float containing
        the number of seconds from midnight on 1-1-1970. Serialized time is used
        internally to map time axes from time to a pixel value.
        '''

        #  convert datetime to numpy datetime64
        if (isinstance(times, datetime.datetime)):
            times = numpy.datetime64(times)

        epoch = numpy.datetime64('1970-01-01')
        serialTime = (times - epoch)
        return serialTime


    def emitPressEvent(self, clickLocation, button, currentKbKey, items):
        """
        emitPressEvent is overridden in this class to convert pixel values to axis
        values.
        """
        #  convert the press point to echogram coordinates
        convertedLocation = self.pixelToAxes(clickLocation)

        #  emit the mousePressEvent signal
        self.emit(SIGNAL("mousePressEvent"), self, convertedLocation, button, currentKbKey, items)


    def emitMouseMoveEvent(self, location, currentKbKey, draggedItems, items):
        """
        emitPressEvent is overridden in this class to convert pixel values to axis
        values.
        """
        #  convert the mouse location to echogram coordinates
        convertedLocation = self.pixelToAxes(location)

        #  emit the mouseMoveEvent signal
        self.emit(SIGNAL("mouseMoveEvent"), self, convertedLocation, currentKbKey, draggedItems, items)


    def emitReleaseEvent(self, clickLocation, button, currentKbKey, items):
        """
        emitReleaseEvent is overridden in this class to convert pixel values to axis
        values.
        """
        #  convert the release point to echogram coordinates
        convertedLocation = self.pixelToAxes(clickLocation)

        #  emit the mouseReleaseEvent signal
        self.emit(SIGNAL("mouseReleaseEvent"), self, convertedLocation, button, currentKbKey, items)


    def emitRubberbandSelection(self, rubberBandRect, items):
        """
        emitPressemitRubberbandSelection Event is overridden in this class to convert
        pixel values to axis values.
        """
        #  convert the rubberband rectangle to a 2 element list containing the top left and
        #  bottom right points in the echogram coordinates
        topLeft = self.pixelToAxes(rubberBandRect.topLeft())
        bottomRight = self.pixelToAxes(rubberBandRect.bottomRight())
        convertedRect = [topLeft, bottomRight]

        #  emit the rubberband selection signal
        self.emit(SIGNAL("rubberBandSelection"), self, convertedRect, items)


    def getColorTable(self):
        return self.colorTable


    def setColorTable(self, colorTable=None, ctLen=None):
        """
        Set the echogram color table to the list of RGB tuples provided
        """


        if colorTable:
            #  color table is provided
            self.colorTable = colorTable
        else:
            #  no color table provided
            #  set the default SIMRAD EK500 color table (plus light gray)
            self.colorTable = [(255,255,255),
                               (159,159,159),
                               (95,95,95),
                               (0,0,255),
                               (0,0,127),
                               (0,191,0),
                               (0,127,0),
                               (255,255,0),
                               (255,127,0),
                               (255,0,191),
                               (255,0,0),
                               (166,83,60),
                               (120,60,40),
                               (200,200,200)]
            #  we've added a custom "no data" color at 14 so set
            #  the internal length used for scaling data to 13
            ctLen = 13

        #  allow for custom color table lengths
        if ctLen == None:
            self.__ctLength = len(self.colorTable)
        else:
            self.__ctLength = ctLen


        #  set the internal color table
        self.__colorTable = []
        for c in self.colorTable:
            self.__colorTable.append(QColor(c[0],c[1],c[2]).rgb())




