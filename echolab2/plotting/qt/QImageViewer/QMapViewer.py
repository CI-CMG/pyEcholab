
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyproj
import cPickle as pickle
from QViewerBase import QViewerBase
from QMVLayer import QMVLayer
import QMVTools
from QMVStickPlot import QMVStickPlot



class QMapViewer(QViewerBase):

    def __init__(self, parent=None, useGL=False, backgroundColor=[50,50,50], projection=None):
        super(QMapViewer, self).__init__(parent, useGL=useGL,
                backgroundColor=backgroundColor)

        #  define the default public properties
        self.name = 'QMapViewer'
        self.baseLayer = None

        #  check if we need to create the default projection
        if (projection == None):
            projection = pyproj.Proj(proj='aea',zone=3,ellps='WGS84', lon_0='160w')

        #  set the projection
        self.setProjection(projection)


    def setProjection(self, projection):
        """
        setProjection will set the pyProj projection object the QMapViewer uses to transform
        the lat/lon positions to x,y values suitable for plotting. Setting the projection
        will clear the scene of all items.
        """

        #  update the internal projection
        self.projection = projection

        #  clear and reset the scene since the projection has changed
        self.removeAllItems()


    def removeAllItems(self):
        """
        removeAllItems will remove all items currently in the scene.
        """

        #  destroy the base layer
        if (self.baseLayer):
            self.scene.destroyItemGroup(self.baseLayer)

        #  call the parent method
        super(QMapViewer, self).removeAllItems()

        #  define/reset some properties
        self.layers = []
        self.layerBounds = None
        self.layerScalar = None

        #  add the base layer
        self.baseLayer = self.scene.createItemGroup([])


    def removeLayer(self, layer):
        """
        removeLayer removes the specified layer from the scene.
        """
        #  remove this layer from our list
        if layer in self.layers:
            self.layers.remove(item)

            #  remove it from the scene
            self.scene.removeItem(layer)

        #  update the viewport
        self.viewport().update()


    def addPickledLayer(self, filename, objects=[], name='layer', **kwargs):
        """
        addPickledLayer loads a map layer from a pickle file. Pickle files are files that
        contain ABP (already been processed) map data which has been transformed to plot nicely
        in the QGraphicsView system. Pickled layers can be created from shapefiles using the
        functions in QImageViewer.shapeTools
        """

        #  read the pickle file
        data = self.readPickledLayer(filename)

        #  add the layer
        return self.addPolygonLayer(data, name=name, objects=objects, **kwargs)


    def readPickledLayer(self, filename):
        """
        readPickledLayer simply reads a piclked layer file. These files are generated using the
        QImageViewer.shapeTools functions and a script like mapDataPickler.py.
        """

        #  read in the pickled layer data
        with open(filename, 'rb') as input:
            data = pickle.load(input)

        return data


    def addPolygonLayer(self, data, name='layer', objects=[], **kwargs):
        """
        addPolygonLayer adds a layer to the map given the mapData dict.
        """

        #  first check if this layer is compatible with existing layers
        if (self.layerBounds):
            if (self.layerBounds != data['globalBounds']):
                #  bounds are different - this will not plot correctly with existing layers
                raise Exception('Layer bounds do not match existing map bounds. Cannot add layer.')
        else:
            #  no bounds yet, set them
            self.layerBounds = data['globalBounds']
        #  next check that the scaling is the same
        if (self.layerScalar):
            if (self.layerScalar != data['scaler']):
                #  scale is different - this will not plot correctly with existing layers
                raise Exception('Layer scaling does not match existing map scale. Cannot add layer.')
        else:
            #  no bounds yet, set them
            self.layerScalar = data['scaler']

        #  create a layer
        layer = QMVLayer(self.baseLayer, name=name)

        #  add it to our list of layers
        self.layers.append(layer)

        #  determine how may polygon elements we've been given
        nPolygons = len(data['polygons'])

        #  loop through the objects, adding them to the layer if we're supposed to
        for i in range(nPolygons):
            if (len(objects) == 0):
                #  no object data provided - plot all objects
                polyItem = super(QMapViewer, self).addPolygon(data['polygons'][i], noadd=True, **kwargs)
                layer.addToGroup(polyItem)
            else:
                #  list of object(s) passed - filter by that list
                if (data['object'][i] in objects):
                    polyItem = super(QMapViewer, self).addPolygon(data['polygons'][i], noadd=True, **kwargs)
                    layer.addToGroup(polyItem)

        return layer


    def addSticks(self, locations, magnitudes, scale, **kwargs):
        """
        Add a stick plot

                        scale  -
                        color  - a 3 element list or tuple containing the RGB triplet
                                 specifying the color of the line or mline.
                    thickness  - A float specifying the thickness of the line.
                        alpha  - A integer specifying the opacity of the line. 0 is transparent
                                 and 255 is solid.
                    linestyle  - '=' for solid, '-' for dashed, and '.' for dotted.

        """


        #  transform the lon/lat locations into x,y coords
        locations, b = QMVTools.convertCoords(locations, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        #  create the sticks object
        stickObj = QMVStickPlot(locations, magnitudes, scale, **kwargs)

        #  add the stick directly to the scene
        self.scene.addItem(stickObj)

        #  and add it to our list of scene items
        self.sceneItems.append(stickObj)

        return stickObj



    def addText(self, position, text, useXY=False, **kwargs):
        """
        Add text to the scene given the text and position. The function returns the reference
        to the QIVMarkerText object that is added to the scene.

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
            position, b = QMVTools.convertCoords(position, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        return super(QMapViewer, self).addText(position, text, **kwargs)


    def addPolygon(self, verts, useXY=False, **kwargs):
        """
        Add an arbitrary polygon to the scene. Verts can be a list of x,y
        pairs or a list of Point2f objects defining the polygon.

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
        """

        if (not useXY):
            verts, b = QMVTools.convertCoords(verts, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        return super(QMapViewer, self).addPolygon(verts, **kwargs)


    def addLine(self, verts, useXY=False, **kwargs):
        """

        """

        if (not useXY):
            verts, b = QMVTools.convertCoords(verts, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        return super(QMapViewer, self).addLine(verts, **kwargs)


    def addMark(self, position, useXY=False, name='QMVMarker', **kwargs):
        """
        Add a marker to the scene. Position must be a 2 element list/tuple as [lon, lat]. The lon,lat
        values will be converted to x,y values using the existing projection. You can pass x,y values
        that will be used directly you specify the useXY keyword. You can add marker text  using the
        marker's addLabel method.

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
            position, b = QMVTools.convertCoords(position, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        return super(QMapViewer, self).addMark(position, name=name, **kwargs)


    def getMarkCenter(self, mark):
        """
        Return the center of a mark in lat/lon units
        """

        xyCoords = mark.mapToScene(mark.boundingRect().center())

        #  need to convert cartesian to lat/lon
        #TODO: figure out what the reverse method is
        lonLat = self.projection.SOMEMETHOD(xyCoords)

        return lonLat


    def zoomToPoint(self, point, zoomLevel, useXY=False):

        #  check if we've been passed converted coords
        if (not useXY):
            #  transform the lon/lat locations into x,y coords
            point, b = QMVTools.convertCoords(point, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        super(QMapViewer, self).zoomToPoint(point, zoomLevel)


    def zoomToRegion(self, regionRect, useXY=False):
        """
        zoomToRegion zooms the view to the rectangular region defined by the provided
        QRectF. The coordinates of the QRectF should be in lon/lat unless the useXY
        keyword is set.
        """

        #  check if we've been passed converted coords
        if (not useXY):
            #  transform the upper left lon/lat locations into x,y coords
            point = regionRect.topLeft()
            point, b = QMVTools.convertCoords(point, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)
            topLeft = QPointF(point[0], point[1])

            #  transform the lower right lon/lat locations into x,y coords
            point = regionRect.bottomRight()
            point, b = QMVTools.convertCoords(point, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)
            bottomRight = QPointF(point[0], point[1])

            #  create the QRectF with transformed coords
            regionRect = QRectF(topLeft, bottomRight)

        #  call the parect method
        super(QMapViewer, self).zoomToRegion(regionRect)



    def centerOnPoint(self, point, useXY=False):
        """
        Centers the view on the provided point. Point should be a list/tuple
        containing a lon/lat pair.
        """

        #  check if we've been passed converted coords
        if (not useXY):
            #  transform the lon/lat locations into x,y coords
            point, b = QMVTools.convertCoords(point, self.projection, self.layerScalar,
                    dataBounds=self.layerBounds)

        super(QMapViewer, self).centerOnPoint(point)


