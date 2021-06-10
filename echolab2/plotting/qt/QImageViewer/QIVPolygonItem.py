"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class QIVPolygonItem(QGraphicsItem):

    """
    QIVPolygonItem implements open and closed QGraphicsview polygon items with accurate
    selection "hit boxes". This class is primarily used by QIVPolygon to provide
    polygon objects with simplified vertex labeling.

    QIVPolygon Arguments:

        vertices - The polygon vertices as:
                    A list of QPoint or QpointF objects defining the vertices
                    A list of [x,y] pairs (i.e. [[x,y],[x,y],[x,y],...]
                    A QRect or QRectF object
        color - a 3 element list or tuple containing the RGB triplet
                specifying the outline color of the polygon
        thickness - A float specifying the outline thickness of the polygon.
        alpha - A integer specifying the opacity of the polygon. 0 is transparent
                and 255 is solid.
        linestyle - '=' for solid, '-' for dashed, and '.' for dotted.
        fill - a 3 element list or tuple containing the RGB triplet
                specifying the fill color of the polygon. Set to None for
                no fill.

    """

    def __init__(self, vertices,  color=[220,10,10], thickness=1.0,
                selectColor=None, alpha=255, linestyle='=', fill=None,
                selectable=False, selectThickness=2.0, movable=False,
                ignoresTransforms=False, closed=True, parent=None,
                name='QIVPolygonItem',isCosmetic=False):

        #  call the parent class init
        super(QIVPolygonItem, self).__init__(parent)

        #  set the initial props
        self.thickness = thickness
        self.alpha = alpha
        self.linestyle = linestyle
        self.closed = closed
        self.name = name
        self.selectThickness = selectThickness
        self.selected = False
        self.selectColor = selectColor
        self.color = color
        self.isCosmetic = isCosmetic

        #  create the pen
        self.pen = self.getPen(self.color, self.alpha, self.linestyle, self.thickness)

        #  set the brush for filling the polygon (if any)
        if (fill and self.closed):
            #  check if we've been given a QColor object to use as fill
            if (fill.__class__.__name__.lower() == 'qcolor'):
                #  we have a QColor object
                self.brush = QBrush(fill)
            else:
                #  must be a list - if alpha isn't explicitly supplied, use the outline value
                if (len(fill) == 3):
                    fill.append(alpha)
                self.brush = QBrush(QColor(fill[0], fill[1], fill[2], fill[3]))
        else:
            #  either no fill was specified or we're an open path
            self.brush = QBrush()

        #  create the polygon
        self.polygon = QPolygonF()

        #  and set the geometry
        self.setGeometry(vertices)

        #  set the selectable, movable and ignores transforms flags
        #  usually this object is part of a QGraphicsItemGroup so we don't
        #  want it to be selectable, nor movable and unlike marks, we usually
        #  want it to honor transforms and the defaults above reflect this.
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, movable)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, ignoresTransforms)


    def __getitem__(self, key):
        """
        reimplemented getter for the polygon's indicies.
        """

        return self.polygon[key]


    def setGeometry(self, vertices):
        """
        setGeometry sets the shape of the polygon to the geometry defined in geom.

            vertices - The polygon vertices as:
                    A list of QPoint or QpointF objects defining the vertices
                    A list of [x,y] pairs (i.e. [[x,y],[x,y],[x,y],...]
                    A QRect or QRectF object
        """

        self.polygon.clear()

        #  handle QRect and QRectF objects
        if ((vertices.__class__.__name__.lower() == 'qrectf') or
           (vertices.__class__.__name__.lower() == 'qrect')):
            #  append the QRect vertices to our polygon
            self.polygon.append(vertices.topLeft())
            self.polygon.append(vertices.topRight())
            self.polygon.append(vertices.bottomRight())
            self.polygon.append(vertices.bottomLeft())
            #  close the polygon
            self.polygon.append(vertices.topLeft())
        else:
            #  assume this is a list of verts of
            for v in vertices:
                if ((v.__class__.__name__.lower() == 'qpointf') or
                    (v.__class__.__name__.lower() == 'qpoint')):
                    self.polygon.append(v)
                else:
                    self.polygon.append(QPointF(v[0], v[1]))

        #  ensure that QGraphicsView knows we're changing our geometry
        self.prepareGeometryChange()


    def setColor(self, color, update=True):
        """
        Sets the polygon outline color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line or a QColor object.
        """

        if (color.__class__.__name__.lower() != 'qcolor'):
            #  change the pen color
            color = QColor(color[0], color[1], color[2], self.alpha)
        self.color = color
        self.pen.setColor(self.color)

        #  schedule a re-paint
        if (update):
            self.update()


    def setSelectColor(self, color):
        """
        Sets the polygon selected color. Color is a 3 element list or tuple containing the RGB triplet.
        """

        #  change the polygon's selection pen color - if color is None, we get the inverted
        #  outline color
        if (color is None):
            self.selectColor = self.getInvertedColor(self.color)
        else:
            self.selectColor = color
        if self.selected:
            self.pen = self.getPen(self.selectColor, self.markAlpha, self.linestyle,
                    self.selectThickness)


    def setFill(self, fill, update=True):
        """
        Sets the polygon fill color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line or a QColor object.

        This method has no effect for "open" polygons.
        """

        #  set the brush for filling the polygon
        if (self.closed):
            #  check if we've been given a QColor object to use as fill
            if (fill.__class__.__name__.lower() == 'qcolor'):
                #  we have a QColor object
                self.brush = QBrush(fill)
            else:
                #  must be a list - if alpha isn't explicitly supplied, use the outline value
                if (len(fill) == 3):
                    fill.append(self.alpha)
                self.brush = QBrush(QColor(fill[0], fill[1], fill[2], fill[3]))

        #  schedule a re-paint
        if (update):
            self.update()


    def setThickness(self, thickness):
        """
        Sets the line width of the unselected polygon outline.
        """

        #  change the unselected pen width
        self.thickness = thickness
        if (not self.selected):
            self.pen.setWidthF(self.thickness)

        #  check if our bounding box will change due to change in line thickness
        if (self.thickness != self.selectThickness):
            self.prepareGeometryChange()


    def setSelectThickness(self, thickness):
        """
        Sets the line width of the selected polygon outline.
        """

        #  change the selected pen width
        self.selectThickness = thickness
        if (self.selected):
            self.pen.setWidthF(self.selectThickness)

        #  check if our bounding box will change due to change in line thickness
        if (self.thickness != self.selectThickness):
            self.prepareGeometryChange()


    def setAlpha(self, alpha, update=True):
        """
        Set the alpha leven (transparency) of the polygon. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the pen alpha
        self.alpha = alpha
        penColor = QColor(self.color[0], self.color[1], self.color[2], alpha)
        self.pen.setColor(penColor)

        #  schedule a re-paint
        if (update):
            self.update()


    def setSelected(self, selected):
        '''
        setSelected sets this polygon as being selected. It changes the pen color to
        the "selected" color and sets the "selected" property to true. We're not using Qt's
        built in selection handling for now so we're not calling the polygon's "setSelected"
        method purposefully.
        '''

        if selected:
            #  if we don't have an explicit select color, invert the regular color
            if (self.selectColor is None):
                selectColor = self.getInvertedColor(self.color)
            else:
                selectColor = self.selectColor

            #  set the pen with the selection color
            self.pen = self.getPen(selectColor, self.alpha, self.linestyle,
                    self.selectThickness)
            self.selected = True
        else:
            self.pen = self.getPen(self.color, self.alpha, self.linestyle, self.thickness)
            self.selected = False

        #  check if our bounding box will change due to change in line thickness
        if (self.thickness != self.selectThickness):
            self.prepareGeometryChange()

        #  schedule a re-paint
        self.update()


    def isSelected(self):
        '''
        isSelected returns true if this mark is selected, false if not.
        '''
        return self.selected


    def getInvertedColor(self, color):
        '''
        getInvertedColor accepts an RGB triplet or QColor and returns a
        QColor object with the "inverted" color.
        '''

        if (color.__class__.__name__.lower().find('qcolor') == -1):
            invertedColor = QColor(color[0], color[1], color[2], self.alpha)
        else:
            invertedColor = color
        invertedColor = invertedColor.toHsv()
        hue = invertedColor.hsvHue() - 180
        if hue < 0:
            hue = hue + 360
        invertedColor.setHsv(hue, invertedColor.saturation(),invertedColor.value(),
                self.alpha)

        return invertedColor


    def boundingRect(self):
        """
        Returns a QRectF object that defines the axially aligned bounding box for
        the polygon.
        """

        return self.polygon.boundingRect()


    def shape(self):
        """
        reimplementation of QGraphicsViewItem::Shape() that returns a
        properly formed "hit box" for accurate polygon selection
        """

        #  create a painter path from our polygon
        path = QPainterPath()
        path.addPolygon(self.polygon)

        if (not self.closed):
            #  for open polygons we use QPainterPathStroker to create the painter path
            stroker = QPainterPathStroker()
            stroker.setWidth(self.thickness)
            path = stroker.createStroke(path)

        return path


    def paint(self, painter, option, widget):
        """
        Reimplemented method which draws the stick and modifies the
        line thickness based on the QGraphicsView zoom level.
        """

        #  set the painter pen
        painter.setPen(self.pen)

        if (self.closed):
            #  set the brush
            painter.setBrush(self.brush)

            #  draw a closed polygon
            painter.drawPolygon(self.polygon)
        else:
            #  draw an open polygon
            painter.drawPolyline(self.polygon)

        #  draw the selection bounding box (for debugging)
        #painter.setBrush(QBrush())
        #painter.drawPolygon(self.selectionPolygon)


    def getPen(self, color, alpha, style, width):
        """
        Returns a pen set to the color, style, thickness and alpha level provided.
        """

        #  return a pen

        #  check if we've already be passed a qcolor object
        if (color.__class__.__name__.lower().find('qcolor') == -1):
            penColor = QColor(color[0], color[1], color[2], alpha)
        else:
            penColor = color
        pen = QPen(penColor)
        pen.setWidthF(width)
        if style.lower() == '-':
            pen.setStyle(Qt.DashLine)
        elif style.lower() == '.':
            pen.setStyle(Qt.DotLine)
        else:
            pen.setStyle(Qt.SolidLine)

        #  If we're a "cosmetic" line (non-scaling) set the cosmetic
        #  property of the pen.
        if self.isCosmetic:
            pen.setCosmetic(True)

        return pen





