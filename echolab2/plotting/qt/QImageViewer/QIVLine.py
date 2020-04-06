"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

import math
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class QMVStick(QGraphicsItem):

    """
    QMVStick Arguments:


        color - a 3 element list or tuple containing the RGB triplet
                specifying the color of the line or mline.
        thickness - A float specifying the thickness of the line.
        alpha - A integer specifying the opacity of the line. 0 is transparent
                and 255 is solid.
        linestyle - '=' for solid, '-' for dashed, and '.' for dotted.

    """

    def __init__(self, location, magnitude, scale, angle=90.0, color=[220,10,10], thickness=2.0,
                 alpha=255, linestyle='=', view=None, parent=None, name='QMVStick'):
        super(QMVStick, self).__init__(parent)

        self.color = color
        self.thickness = thickness
        self.alpha = alpha
        self.linestyle = linestyle
        self.sticks = []
        self.scale = float(scale)
        self.minPenWidth = 0.2
        self.maxPenWidth = 10.0
        self.view = view
        self.name = name
        self.selectionOffset = 1

        #  store the stick magnitude
        self.magnitude = magnitude

        #  create the pen
        self.pen = self.getPen(self.color, self.alpha, self.linestyle, self.thickness)

        #  create the stick
        #  plot p1 as the location
        p1 = QPointF(location[0],location[1])
        #  plot p2 as a point just off the location
        p2 = QPointF(location[0],location[1]+1)
        self.stick = QLineF(p1, p2)
        #  set the angle
        self.stick.setAngle(float(angle))
        #  and now set the proper length (this moves p2)
        self.stick.setLength(self.magnitude / self.scale)
        #  update the selection polygon
        self.updateSelectionPolygon()

        #  set the selectable and movable flags
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


    def setAngle(self, angle):
        """
        Set the angle of the stick
        """

        #  and update the stick
        self.stick.setAngle(float(angle))

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.updateSelectionPolygon()
        self.prepareGeometryChange()


    def setScale(self, scale):
        """
        Set the stick scale.
        """

        #  update the stick scale
        self.scale = float(scale)

        #  and update the stick
        self.stick.setLength(self.magnitude / self.scale)

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.updateSelectionPolygon()
        self.prepareGeometryChange()


    def setColor(self, color, update=True):
        """
        Sets the dimension line color. Color is a 3 element list or tuple containing
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
        Sets the width of the dimension line. Note that this value will
        be constrained to the minPenWidth and maxPenWidth properties of the
        object.
        """

        #  change the pen width
        self.width = width
        self.pen.setWidthF(width)

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.updateSelectionPolygon()
        self.prepareGeometryChange()


    def setAlpha(self, alpha, update=True):
        """
        Set the alpha leven (transparency) of the dimension line. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the pen alpha
        self.alpha = alpha
        penColor = QColor(self.color[0], self.color[1], self.color[2], alpha)
        self.pen.setColor(penColor)

        #  schedule a re-paint
        if (update):
            self.update()


    def updateSelectionPolygon(self):
        """
        updateSelectionPolygon creates a tight bounding box around the line
        regardless of the lines angle which allows proper selection when the
        line is rotated. This method must be called when the items's geometry
        changes.
        """

        halfLineThick = self.thickness / 2.0
        radAngle = self.stick.angle() * math.pi / 180.0
        dx = halfLineThick * math.sin(radAngle)
        dy = self.thickness * math.cos(radAngle)
        offset1 = QPointF(dx, dy)
        offset2 = QPointF(-dx, -dy)
        self.selectionPolygon = QPolygonF([self.stick.p1() + offset1,
                                           self.stick.p1() + offset2,
                                           self.stick.p2() + offset2,
                                           self.stick.p2() + offset1])


    def boundingRect(self):
        """
        Returns a QRectF object that defines the bounding box for the stick.
        """

        return self.selectionPolygon.boundingRect()


    def shape(self):
        """
        reimplementation of QGraphicsViewItem::Shape() that returns a properly
        rotated selection polygon as the shape. Without this, the standard
        bounding box is used which grows as the sticks are rotated making it
        impossible to select items when the angle is not 0,90,180,270.
        """

        #  create a QPainterPath and add our selection polygon to it
        path = QPainterPath()
        path.addPolygon(self.selectionPolygon)

        return path


    def paint(self, painter, option, widget):
        """
        Reimplemented method which draws the stick and modifies the
        line thickness based on the QGraphicsView zoom level.
        """

        #lod = option.levelOfDetailFromTransform(painter.worldTransform())

#        penWidth = max(self.minPenWidth, min(self.maxPenWidth,
#                       self.thickness/self.view.transform().m11()))
#
#        self.pen.setWidthF(penWidth)

        #  set the painter pen
        painter.setPen(self.pen)

        #  draw the stick
        painter.drawLine(self.stick)

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





