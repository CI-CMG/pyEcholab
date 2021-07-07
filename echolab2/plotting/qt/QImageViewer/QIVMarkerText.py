"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class QIVMarkerText(QGraphicsSimpleTextItem):
    """
    QIVMarkerText implements text objects that do not transform when zoomed.
    It also implements horizontal and vertical alignment for QGraphicsSimpleTextItem
    as well as the ability to specify an offset from the position, all of which
    scale correctly when zooming so the text stays properly anchored to the mark.

          text (string)  - The text to add to the scene.
      position (QPointF) - The position of the text anchor point.
          size (int)     - The text size, in point size
          font (string)  - A string containing the font family to use. Either stick
                           to the basics with this (i.e. "times", "helvetica") or
                           consult the QFont docs.
       italics (bool)    - Set to true to italicise the font.
        weight (int)     - Set to an integer in the range 0-99. 50 is normal, 75 is bold.
         color (list)    - A 3 element list or tuple containing the RGB triplet
                           specifying the color of the text.
         alpha (int)     - An integer specifying the opacity of the text. 0 is transparent
                           and 255 is solid.
        halign (string)  - Set this value to set the horizontal anchor point. Values are:
                              'left' - Sets the anchor to the left side of the text
                              'center' - Sets the anchor to the middle of the text
                              'right' - Sets the anchor to the right side of the text
        valign (string)  - Set this value to set the vertical anchor point. Values are:
                              'top' - Sets the anchor to the top of the text
                              'center' - Sets the anchor to the middle of the text
                              'bottom' - Sets the anchor to the bottom of the text
    """

    def __init__(self, position, text, offset=QPointF(0,0), size=10, font='helvetica', italics=False,
                 weight=-1, color=[0,0,0], alpha=255, halign='left', valign='bottom',
                 selectable=False, movable=False, name='MarkerText', view=None, rotation=0):

        super(QIVMarkerText, self).__init__(text)

        self.name = name
        self.isMarkerLabel = False
        self.color = color
        self.font = font
        self.size = size
        self.alpha = alpha
        #  check if the position was passed as a list
        if isinstance(position[0], list):
            #  it was, assume it is in the form [x,y]
            position = QPointF(position[0][0], position[0][1])
        self.position = position
        self.halign = halign
        self.valign = valign
        self.view = view
        self.offset = offset
        self.rotation = rotation

        #  set the movable and selectable flags
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, movable)

        #  create the font and pen
        self.font = QFont(font, size, weight, italics)
        self.pen = self.getPen(self.color, self.alpha, '', 1)

        #  and set our font
        self.setFont(self.font)

        #  set the text position
        self.setPos(self.position, 1)

        #  and the text
        self.setText(text)

        #  make sure our text is always on top
        self.setZValue(9999)


    def setPos(self, position, scale):
        '''
        setPos overrides the QGraphicsSimpleTextItem set position method and
        it alters the position based on the horizontal and vertical text alignment
        as well as the text offset from that mark and a scaling factor based on
        the view zoom level.
        '''

        #  check if the position was passed as a list
        if isinstance(position, list):
            #  it was, assume it is in the form [x,y]
            position = QPointF(position[0], position[1])

        #  determine the text's X and Y location based on the specified mark position, the text
        #  alignment, and the text offset.
        boundingRect = self.boundingRect()
        if (self.halign.lower() == 'center'):
            posX = (self.position.x() - ((boundingRect.width() / 2.0) * scale) +
                    (self.offset.x() * scale))
        elif (self.halign.lower() == 'right'):
            posX = (self.position.x() - (boundingRect.width() * scale) +
                    (self.offset.x() * scale))
        else:
            posX = self.position.x() + (self.offset.x() * scale)
        if (self.valign.lower() == 'center'):
            posY = (self.position.y() - ((boundingRect.height() / 2.0) * scale) +
                    (self.offset.y() * scale))
        elif (self.valign.lower() == 'bottom'):
            posY = (self.position.y() - (boundingRect.height() * scale) +
                    (self.offset.y() * scale))
        else:
            posY = self.position.y() + (self.offset.y() * scale)

        #  create a QPointF defining the position
        position = QPointF(posX, posY)

        #  call the parent method to update the text's position
        super(QIVMarkerText, self).setPos(position)


    def setColor(self, color):
        """
        Sets the text color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the text.
        """

        #  change the pen (text) color
        self.color = color
        self.pen = self.getPen(self.color, self.alpha, '', 1)

        #  schedule a redraw
        self.update()


    def setAlpha(self, alpha):
        """
        Set the alpha level (transparency) of the text. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the brush (text) alpha
        self.alpha = alpha
        self.pen = self.getPen(self.color, self.alpha, '', 1)

        #  schedule a redraw
        self.update()


    def paint(self, painter, option, widget):
        """
        Reimplemented paint method which alters the text position based on the QGraphicsView
        zoom level and then draws the text.
        """

        #  determine the scaling factor required to maintain correct text placement when zooming
        scale = 1.0 / self.view.transform().m11()

        #  set the scaled position of the text
        self.setPos(self.position, scale)

        #  set the painter font and brush
        painter.setFont(self.font)
        painter.setPen(self.pen)

        #  get the text bounding box
        boundingRect = self.boundingRect()

        #  draw the text
        painter.drawText(boundingRect.x(), boundingRect.y() + boundingRect.height(), self.text())

        #  draw the bounding box (for testing)
        #painter.setBrush(QBrush())
        #painter.drawRect(self.boundingRect())


    def getPen(self, color, alpha, style, width):

        #  return a pen
        penColor = QColor(color[0], color[1], color[2], alpha)
        pen = QPen(penColor)
        pen.setWidthF(width)
        if style.lower() == '-':
            pen.setStyle(Qt.DashLine)
        elif style.lower() == '.':
            pen.setStyle(Qt.DotLine)
        else:
            pen.setStyle(Qt.SolidLine)

        return pen
