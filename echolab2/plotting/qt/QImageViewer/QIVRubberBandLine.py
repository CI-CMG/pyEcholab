"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *

class QIVRubberBandLine(QGraphicsItemGroup):

    def __init__(self, startpoint=None, endpoint=None, color=[240,240,240], thickness=2.0,
                 alpha=255, linestyle='_', taillength=20, usetails=False, parent=None):
        super(QIVRubberBandLine, self).__init__()

        self.labels = []

        self.rubberBandLine = rubberBandLine(startpoint=startpoint,
                            endpoint=endpoint, color=color, thickness=thickness,
                            alpha=alpha, linestyle=linestyle, taillength=taillength,
                            usetails=usetails, parent=parent)
        self.addToGroup(self.rubberBandLine)


    def pos(self):
        '''
        pos overrides QGraphicsItemGroup's pos method and returns the position of the
        middle of the line (in image coordinates)
        '''
        return self.rubberBandLine.mainLine.pointAt(0.5)


    def length(self):
        return self.rubberBandLine.mainLine.length()


    def getLine(self):
        """
        Returns the QLineF object defining the rubberband line.
        """

        return self.rubberBandLine.mainLine


    def removeLabel(self, label=None, labelName=None):
        '''
        removeLabel removes a marker label given the label reference or labelName.
        If neither the label reference or name is provided ALL LABELS ARE REMOVED.
        Also note that if the label name is provided, all labels with that name
        will be removed.
        '''

        try:

            if label:
                #  remove label by reference
                self.labels.remove(label)
                self.removeFromGroup(label)

            elif labelName:
                #  remove label by name
                i=[]
                #  find label(s) given the label name
                for l in range(len(self.labels)):
                    if (label.name[l] == labelName):
                        i.append(l)
                #  remove any labels with that name
                for l in i:
                    label = self.labels.pop(l)
                    self.removeFromGroup(label)

            else:
                #  ---- REMOVE ALL LABELS ----
                for label in self.labels:
                    self.removeFromGroup(label)
                self.labels = []

        except:
            #  we'll silently ignore any errors for now
            pass


    def getLabels(self):
        '''
        getLabels returns the list of labels associated with this mark
        '''
        return self.labels


    def addLabel(self, label):
        '''
        addLabel adds a label to this mark
        '''

        #  first set this text's
        label.setMarkerLabel(True)
        self.labels.append(label)
        self.addToGroup(label)


    def clearLabels(self):
        '''
        clearLabels is a convenience method to clear all labels associated with this mark.
        '''
        self.removeLabel()


    '''
    The following methods wrap the rubberBandLine class methods
    '''

    def setPoints(self, p1, p2):
        self.rubberBandLine.setPoints(p1, p2)

    def setP1(self, p1):
        self.rubberBandLine.setP1(p1)

    def setP2(self, p2):
        self.rubberBandLine.setP2(p2)

    def setColor(self, color):
        self.rubberBandLine.setColor(color)

    def setAlpha(self, alpha):
        self.rubberBandLine.setAlpha(alpha)

    def setWidth(self, width):
        self.rubberBandLine.setWidth(width)


class rubberBandLine(QGraphicsItem):

    """
    Starts a rubberband line at the provided point. The point must be type QPointF()

    Rubberband Arguments:

        startpoint - the starting location of the rubberband object as QPointF()
        color - a 3 element list or tuple containing the RGB triplet
                specifying the color of the line or mline.
        thickness - A float specifying the thickness of the line.
        alpha - A integer specifying the opacity of the line. 0 is transparent
                and 255 is solid.
        linestyle - '_' for solid, '-' for dashed, and '.' for dotted.
        usetails - set to True to creates a 'measuring line' with two smaller
                   lines running orthoginal to the rubberband line on either end
                   of the line.
        taillength - set this to a integer specifying the length of the tails
                     in pixels
    """

    def __init__(self, startpoint=None, endpoint=None, color=[240,240,240], thickness=2.0,
                 alpha=255, linestyle='_', taillength=20, usetails=False, parent=None):
        super(rubberBandLine, self).__init__()

        self.color = color
        self.thickness = thickness
        self.alpha = alpha
        self.linestyle = linestyle
        self.taillength = taillength / 2
        self.usetails = usetails
        self.startPoint = startpoint
        self.endPoint = endpoint
        self.labels = []
        self.minPenWidth = 0.2
        self.maxPenWidth = 10.0

        #  create the pen
        self.pen = self.getPen(self.color, self.alpha, self.linestyle, self.thickness)
        #  make it cosmetic so it's thickness doesn't change with zoom
        self.pen.setCosmetic(True)

        #  set start and/or end points if none are given
        if (self.startPoint == None):
            #  if we have been given no starting point we set the start and end
            #  to 0,0 and hide the line
            self.hide()
            self.startPoint = QPointF(0,0)
            self.endPoint = QPointF(0,0)
        if (self.endPoint == None):
            #  if we have no end point, we set it to the start point
            self.endPoint = self.startPoint

        #  create the main line
        self.mainLine = QLineF(self.startPoint, self.endPoint)

        #  create the tail lines (if applicable)
        self.tailLines = []
        if (self.usetails):
            for i in range(4):
                self.tailLines.append(QLineF())
            self.updateTails()


    def setPoints(self, p1, p2):
        """
        Set the rubberband line's start and end points. The points must be a QPointF object.
        """

        #  set the start and end points
        self.startPoint = p1
        if (p2 == None):
            p2 = p1
        self.endPoint = p2

        #  create the new lines
        self.mainLine.setPoints(self.startPoint, self.endPoint)
        if (self.usetails):
            self.updateTails()

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.prepareGeometryChange()


    def setP1(self, p1):
        """
        Set the rubberband line's start point. The point must be a QPointF object.
        """

        #  set the starting point
        self.startPoint = p1

        #  create the new lines
        self.mainLine.setPoints(self.startPoint, self.endPoint)
        if (self.usetails):
            self.updateTails()

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.prepareGeometryChange()


    def setP2(self, p2):
        """
        Set the rubberband line's end point. The point must be a QPointF object.
        """

        #  set the ending point
        self.endPoint = p2

        #  create the new lines
        self.mainLine.setPoints(self.startPoint, self.endPoint)
        if (self.usetails):
            self.updateTails()

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.prepareGeometryChange()


    def setColor(self, color):
        """
        Sets the rubberband line color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line.
        """

        #  change the pen color
        self.color = color
        penColor = QColor(color[0], color[1], color[2], self.alpha)
        self.pen.setColor(penColor)


    def setWidth(self, width):
        """
        Sets the width of the rubberband line. Note that this value will
        be constrained to the minPenWidth and maxPenWidth properties of the
        object.
        """

        #  change the pen width
        self.width = width
        self.pen.setWidthF(width)

        #  ensure that QGraphicsView knows we're changing our bounding rect
        self.prepareGeometryChange()


    def setAlpha(self, alpha):
        """
        Set the alpha leven (transparency) of the rubberband line. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the pen alpha
        self.alpha = alpha
        penColor = QColor(self.color[0], self.color[1], self.color[2], alpha)
        self.pen.setColor(penColor)


    def getLine(self):
        """
        Returns the QLineF object defining the rubberband line.
        """

        return self.mainLine


    def boundingRect(self):
        """
        Returns a QRectF object that defines the bounding box for the rubberband line.
        """

        halfLineThick = self.thickness / 2.0
        if (self.usetails):
            p1 = QPointF()
            p1.setX(min(self.tailLines[0].x1(), self.tailLines[1].x1(), self.tailLines[2].x1(),
                        self.tailLines[3].x1(), self.tailLines[0].x2(), self.tailLines[1].x2(),
                        self.tailLines[2].x2(), self.tailLines[3].x2()) - halfLineThick)
            p1.setY(min(self.tailLines[0].y1(), self.tailLines[1].y1(), self.tailLines[2].y1(),
                        self.tailLines[3].y1(), self.tailLines[0].y2(), self.tailLines[1].y2(),
                        self.tailLines[2].y2(), self.tailLines[3].y2()) - halfLineThick)
            p2 = QPointF()
            p2.setX(max(self.tailLines[0].x1(), self.tailLines[1].x1(), self.tailLines[2].x1(),
                        self.tailLines[3].x1(), self.tailLines[0].x2(), self.tailLines[1].x2(),
                        self.tailLines[2].x2(), self.tailLines[3].x2()) + halfLineThick)
            p2.setY(max(self.tailLines[0].y1(), self.tailLines[1].y1(), self.tailLines[2].y1(),
                        self.tailLines[3].y1(), self.tailLines[0].y2(), self.tailLines[1].y2(),
                        self.tailLines[2].y2(), self.tailLines[3].y2()) + halfLineThick)
        else:
            p1 = QPointF()
            p1.setX(min(self.mainLine.x1(), self.mainLine.x2()) - halfLineThick)
            p1.setY(min(self.mainLine.y1(), self.mainLine.y2()) - halfLineThick)
            p2 = QPointF()
            p2.setX(max(self.mainLine.x1(), self.mainLine.x2()) + halfLineThick)
            p2.setY(max(self.mainLine.y1(), self.mainLine.y2()) + halfLineThick)

        return QRectF(p1, p2)



    def paint(self, painter, option, widget):
        """
        Reimplemented method which draws the rubberband line.
        """

        #self.pen.setWidthF(penWidth)
        painter.setPen(self.pen)

        painter.drawLine(self.mainLine)
        if (self.usetails):
            for line in self.tailLines:
                painter.drawLine(line)


    def getPen(self, color, alpha, style, width):
        """
        Returns a pen set to the color, style, thickness and alpha level provided.
        """

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


    def updateTails(self):
        """
        Updates the "tails" on the measuring line rubberband object. The tails
        are short lines orthogonal to the main rubberband line on each end of
        the line.
        """

        if self.tailLines:
            self.tailLines[0].setP1(self.mainLine.p1())
            self.tailLines[0].setAngle(self.mainLine.angle() + 90)
            self.tailLines[0].setLength(self.taillength)
            self.tailLines[1].setP1(self.mainLine.p1())
            self.tailLines[1].setAngle(self.mainLine.angle() + 270)
            self.tailLines[1].setLength(self.taillength)
            self.tailLines[2].setP1(self.mainLine.p2())
            self.tailLines[2].setAngle(self.mainLine.angle() + 90)
            self.tailLines[2].setLength(self.taillength)
            self.tailLines[3].setP1(self.mainLine.p2())
            self.tailLines[3].setAngle(self.mainLine.angle() + 270)
            self.tailLines[3].setLength(self.taillength)
