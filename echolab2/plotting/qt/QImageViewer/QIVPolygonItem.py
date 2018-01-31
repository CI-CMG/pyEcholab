"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class QIVPolygonItem(QGraphicsItem):

    """
    QIVPolygonItem implements open and closed QGraphicsview polygon items with accurate
    selection "hit boxes". This class is primarily used by QIVPolygon to provide
    polygon objects with simplified vertex labeling.


    QIVPolygon Arguments:


        color - a 3 element list or tuple containing the RGB triplet
                specifying the color polygon OR an instrance of QColor()
        thickness - A float specifying the thickness of the line.
        alpha - A integer specifying the opacity of the line. 0 is transparent
                and 255 is solid.
        linestyle - '=' for solid, '-' for dashed, and '.' for dotted.

    """

    def __init__(self, vertices,  color=[220,10,10], thickness=1.0,
                 alpha=255, linestyle='=', fill=None, selectable=True, movable=False,
                 closed=True, parent=None, name='QIVPolygonItem'):
        super(QIVPolygonItem, self).__init__(parent)

        self.thickness = thickness
        self.alpha = alpha
        self.linestyle = linestyle
        self.closed = closed
        self.name = name

        #  create the pen
        self.pen = self.getPen(color, self.alpha, self.linestyle, self.thickness)

        #  set our color
        self.setColor(color, update=False)

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
        for v in vertices:
            if (v.__class__.__name__.lower() == 'qpointf'):
                self.polygon.append(v)
            else:
                self.polygon.append(QPointF(v[0], v[1]))

        #  set the selectable and movable flags
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, movable)


    def __getitem__(self, key):
        """
        reimplemented getter for the polygon's indicies.
        """

        return self.polygon[key]


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


    def invertColor(self, invert, update=True):

        if (invert):
            invertedColor = self.color.toHsv()
            hue = invertedColor.hsvHue() - 180
            if hue < 0:
                hue = hue + 360
            invertedColor.setHsv(hue, invertedColor.saturation(),invertedColor.value(), self.alpha)
            self.pen.setColor(invertedColor)
        else:
            self.pen.setColor(self.color)

        #  schedule a re-paint
        if (update):
            self.update()


    def setWidth(self, width):
        """
        Sets the width of the polygon outline.
        """

        #  change the pen width
        self.width = width
        self.pen.setWidthF(width)

        #  ensure that QGraphicsView knows we're changing our bounding rect
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

        return pen





