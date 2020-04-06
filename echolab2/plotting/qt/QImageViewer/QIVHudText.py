from PyQt5.QtCore import *
from PyQt5.QtGui import *

class QIVHudText(QObject):
    """
    Add text to the scene given the text and position. The function returns
    the reference to the QGraphicsItem.

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

    def __init__(self, position, text, graphicsview, size=10, font='helvetica',
                 italics=False, weight=-1, color=[0,0,0], alpha=255, halign='left',
                 valign='top', normalized=True, parent=None):
        super(QIVHudText, self).__init__()

        self.__color = color
        self.__text = text
        self.__font = font
        self.__alpha = alpha
        self.__size = size
        self.__italics = italics
        self.__weight = weight
        self.__graphicsView = graphicsview
        self.__position = position
        self.__normalized = normalized
        self.__halign = halign
        self.__valign = valign

        #  create the font and brush
        self.__font = QFont(font, size, weight, italics)
        self.__pen = self.__getPen(self.__color, self.__alpha, '', 1)
        self.__backgroundBrush = None

        #  update the position values
        self.__updatePosition()


    def setText(self, text):
        """
        Set the text.
        """

        self.__text = text
        self.__updatePosition()


    def setBackground(self, color, alpha):

        if (color):
            self.__backgroundBrush = self.__getBrush(color, alpha)
        else:
            self.__backgroundBrush = None


    def setPosition(self, p1):
        """
        Set the text's anchor point. The point must be a QPointF object.
        """

        #  set the starting point
        self.__position = p1

        #  update the bounding rect
        self.__updatePosition()


    def setColor(self, color):
        """
        Sets the rubberband line color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line.
        """

        #  change the brush (text) color
        self.__color = color
        self.__pen.setColor(QColor(color[0], color[1], color[2], self.__alpha))


    def setAlpha(self, alpha):
        """
        Set the alpha level (transparency) of the text. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the brush (text) alpha
        self.__alpha = alpha
        self.__pen.setColor(QColor(self.__color[0], self.__color[1], self.__color[2], alpha))


    def boundingRect(self):
        """
        Returns a QRectF object that defines the bounding box for the text.
        """

        return QRectF(self.__boundingRect)


    def paint(self, painter):
        """
        Simple paint method that draws the text with the supplied painter.
        """

        #  calculate the text bounding box
        self.__updatePosition()

        #  draw the background if enabled
        if (self.__backgroundBrush):
            painter.setBrush(self.__backgroundBrush)
            painter.drawRect(self.boundingRect())
            painter.setBrush(Qt.NoBrush)

        #  draw the text
        painter.setFont(self.__font)
        painter.setPen(self.__pen)
        painter.drawText(self.position, self.__text)


    def __updatePosition(self):

        #  get the font metrics and calculate text width and height
        fontMetrics = QFontMetrics(self.__font)
        brWidth = fontMetrics.width(self.__text)
        brHeight = fontMetrics.height() + 1

        if self.__normalized:
            #  convert from normalized to viewport coordinates
            scenePos = QPointF(self.__graphicsView.viewport().size().width() * self.__position.x(),
                               self.__graphicsView.viewport().size().height() * self.__position.y())
        else:
            scenePos = self.__position

        #  calculate the horizontal position based on alignment
        if (self.__halign.lower() == 'center'):
            brX = round(scenePos.x() - (brWidth / 2.0))
        elif (self.__halign.lower() == 'right'):
            brX = round(scenePos.x() - brWidth)
        else:
            brX = round(scenePos.x())

        #  calculate the vertical position based on alignment
        if (self.__valign.lower() == 'center'):
            brY = round(scenePos.y() - (brHeight / 2.0))
        elif (self.__valign.lower() == 'bottom'):
            brY = round(scenePos.y() - brHeight)
        else:
            brY = round(scenePos.y())

        self.position = QPoint(brX, brY + brHeight - (2 * fontMetrics.descent()))
        self.__boundingRect = QRect(brX, brY, brWidth, brHeight)


    def __getBrush(self, color, alpha):

        brushColor = QColor(color[0], color[1], color[2], alpha)
        brush = QBrush(brushColor)

        return brush


    def __getPen(self, color, alpha, style, width):

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
