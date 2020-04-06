"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .QIVMarkerText import QIVMarkerText

class QIVDimensionLine(QGraphicsItemGroup):

    def __init__(self, startPoint=None, endPoint=None, color=[240,240,240], thickness=2.0,
                 alpha=255, linestyle='_', taillength=20, view=None):
        super(QIVDimensionLine, self).__init__()

        #  create a list to store our label references
        self.labels = []

        #  store a reference to our view to pass to any labels we may add
        self.view = view

        #  create the dimension line
        self.dimensionLine = dimensionLine(startPoint=startPoint, endPoint=endPoint, color=color,
                                    thickness=thickness, alpha=alpha, linestyle=linestyle,
                                    taillength=taillength, view=view)

        #  add the dimension line to our group
        self.addToGroup(self.dimensionLine)


    def p1(self):
        '''
        p1 returns the starting point of the dimension line
        '''
        return self.dimensionLine.startPoint


    def p2(self):
        '''
        p2 returns the ending point of the dimension line
        '''
        return self.dimensionLine.endPoint


    def getLength(self):
        '''
        getLength returns the length of the dimension line in pixels as a float
        '''
        return self.dimensionLine.mainLine.length()


    def getLine(self):
        """
        Returns the QLineF object defining the dimension line.
        """
        return self.dimensionLine.mainLine


    def getAngle(self):
        '''
        getAngle returns the angle of the dimension line.
        '''
        return self.dimensionLine.mainLine.angle()


    def addLabel(self, position, text, size=10, font='helvetica', italics=False, weight=-1,
                color=[0,0,0], alpha=255, halign='left', valign='top', name='QIVDimLabel',
                offset=None):
        """
        Add a label to the dimension line. Labels are children of the dimension line.

              text (string)   - The text to add to the dimension line.
          position (QPointF)  - The position of the text anchor point in image units.
            offset (QPointF)  - An offset from your position
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

        if (offset == None) or (offset == []):
            offset = QPointF(0,0)

        #  apply the text label offset
        position = position + offset

        #  create a QIVMarkerText associated with the provided mark/line
        textItem = QIVMarkerText(position, text, size=size, font=font, italics=italics,
                                 weight=weight, color=color, alpha=alpha, halign=halign,
                                 valign=valign, name=name, view=self.view)

        #  add the label to our
        #textItem.setMarkerLabel(True)
        self.labels.append(textItem)
        self.addToGroup(textItem)
        
        self.prepareGeometryChange()


    def setLabelText(self, labels, text):
        '''
        Sets the label text given the label reference or name and text.
        '''
        if (labels.__class__.__name__.lower() == 'list'):
            #  we've been given a list of label references or names
            for label in labels:
                if (label.__class__.__name__.lower() == 'str'):
                    #  assume this is a label name
                    labelRefs = self.getLabelsFromName(label)
                    for ref in labelRefs:
                        ref.setText(text)
                else:
                    #  assume this is a label reference
                    try:
                        label.setText(text)
                    except:
                        #  bad reference - not in our list of labels
                        pass
        else:
            #  we've been given
            if (labels.__class__.__name__.lower() == 'str'):
                #  assume this is a label name
                labelRefs = self.getLabelsFromName(labels)
                for ref in labelRefs:
                    ref.setText(text)
            else:
                #  assume this is a label reference
                try:
                    labels.setText(text)
                except:
                    #  bad reference - not in our list of labels
                    pass


    def getLabelsFromName(self, labelName):
        '''
        returns a list of QIVLabel references that share the name provided in the
        labelName argument.
        '''
        labelReferences = []
        #  find label(s) given the label name
        for label in self.labels:
            if (label.name == labelName):
                labelReferences.append(label)

        return labelReferences


    def removeLabels(self, labels):
        '''
        removeLabel removes a marker label given the label reference or labelName.
        If neither the label reference or name is provided ALL LABELS ARE REMOVED.
        Also note that if the label name is provided, all labels with that name
        will be removed.
        '''

        if (labels.__class__.__name__.lower() == 'list'):
            #  we've been given a list of label references or names
            for label in labels:
                if (label.__class__.__name__.lower() == 'str'):
                    #  assume this is a label name
                    labelRefs = self.getLabelsFromName(label)
                    for ref in labelRefs:
                        self.labels.remove(label)
                        self.removeFromGroup(label)
                else:
                    #  assume this is a label reference
                    try:
                        self.labels.remove(label)
                        self.removeFromGroup(label)
                    except:
                        #  bad reference - not in our list of labels
                        pass
        else:
            #  we've been given
            if (labels.__class__.__name__.lower() == 'str'):
                #  assume this is a label name
                labelRefs = self.getLabelsFromName(label)
                for ref in labelRefs:
                    self.labels.remove(label)
                    self.removeFromGroup(label)
            else:
                #  assume this is a label reference
                try:
                    self.labels.remove(label)
                    self.removeFromGroup(label)
                except:
                    #  bad reference - not in our list of labels
                    pass


    def setLabelVisible(self, labels, show):
        '''
        Sets the label visibility given the label reference or name and the
        visibility state.
        '''
        if (labels.__class__.__name__.lower() == 'list'):
            #  we've been given a list of label references or names
            for label in labels:
                if (label.__class__.__name__.lower() == 'str'):
                    #  assume this is a label name
                    labelRefs = self.getLabelsFromName(label)
                    for ref in labelRefs:
                        ref.setVisible(show)
                else:
                    #  assume this is a label reference
                    try:
                        label.setVisible(show)
                    except:
                        #  bad reference - not in our list of labels
                        pass
        else:
            #  we've been given
            if (labels.__class__.__name__.lower() == 'str'):
                #  assume this is a label name
                labelRefs = self.getLabelsFromName(labels)
                for ref in labelRefs:
                    ref.setVisible(show)
            else:
                #  assume this is a label reference
                try:
                    labels.setVisible(show)
                except:
                    #  bad reference - not in our list of labels
                    pass


    def showLabels(self, labels=None):
        """
        showLabels makes the provided label or labels visible. Labels can be
        a list of label references, a list of label names, or a single reference
        or name. If labels is None, all labels for this mark are visible.
        """

        if (labels == None):
            labels = self.labels

        self.setLabelVisible(labels, True)


    def hideLabels(self, labels=None):
        """
        hideLabels makes the provided label or labels invisible. Labels can be
        a list of label references, a list of label names, or a single reference
        or name. If labels is None, all labels for this mark are hidden.
        """

        if (labels == None):
            labels = self.labels

        self.setLabelVisible(labels, False)




    def clearLabels(self):
        '''
        clearLabels is a convenience method to clear all labels associated with this mark.
        '''
        self.removeLabel(self.labels)



    def getLabels(self):
        '''
        getLabels returns the list of labels associated with this line
        '''
        return self.labels


    '''
    The following methods wrap the dimensionLine class methods
    '''

    def setPoints(self, p1, p2):
        self.dimensionLine.setPoints(p1, p2)

    def setP1(self, p1):
        self.dimensionLine.setP1(p1)

    def setP2(self, p2):
        self.dimensionLine.setP2(p2)

    def setColor(self, color):
        self.dimensionLine.setColor(color)

    def setAlpha(self, alpha):
        self.dimensionLine.setAlpha(alpha)

    def setWidth(self, width):
        self.dimensionLine.setWidth(width)


class dimensionLine(QGraphicsItem):

    """
    Starts a dimension line at the provided point. The point must be type QPointF()

    dimensionLine Arguments:

        startpoint - the starting location of the dimension line as QPointF()
        endPoint - the ending point of the dimension line as QPointF()
        color - a 3 element list or tuple containing the RGB triplet
                specifying the color of the line or mline.
        thickness - A float specifying the thickness of the line.
        alpha - A integer specifying the opacity of the line. 0 is transparent
                and 255 is solid.
        linestyle - '_' for solid, '-' for dashed, and '.' for dotted.
        taillength - set this to a integer specifying the length of the tails
                     in pixels. If set to 0, the tails are disabled.
    """

    def __init__(self, startPoint=None, endPoint=None, color=[240,240,240], thickness=2.0,
                 alpha=255, linestyle='_', taillength=20, view=None):
        super(dimensionLine, self).__init__()

        self.color = color
        self.thickness = thickness
        self.alpha = alpha
        self.linestyle = linestyle
        self.taillength = taillength / 2
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.labels = []
        self.minPenWidth = 0.2
        self.maxPenWidth = 10.0

        self.view = view

        #  determine if we're drawing the tails
        if (taillength <= 0):
            self.usetails = False
        else:
            self.usetails = True

        #  create the pen
        self.pen = self.getPen(self.color, self.alpha, self.linestyle, self.thickness)

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

        #  set the selectable flags to false
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)


    def setPoints(self, p1, p2):
        """
        Set the dimension line's start and end points. The points must be a QPointF object.
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
        Set the dimension line's start point. The point must be a QPointF object.
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
        Set the dimension line's end point. The point must be a QPointF object.
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
        Sets the dimension line color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line.
        """

        #  change the pen color
        self.color = color
        penColor = QColor(color[0], color[1], color[2], self.alpha)
        self.pen.setColor(penColor)


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
        self.prepareGeometryChange()


    def setAlpha(self, alpha):
        """
        Set the alpha leven (transparency) of the dimension line. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the pen alpha
        self.alpha = alpha
        penColor = QColor(self.color[0], self.color[1], self.color[2], alpha)
        self.pen.setColor(penColor)


    def getLine(self):
        """
        Returns the QLineF object defining the dimension line.
        """

        return self.mainLine


    def boundingRect(self):
        """
        Returns a QRectF object that defines the bounding box for the dimension line.
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
        Reimplemented method which draws the dimension line and modifies the
        line thickness based on the QGraphicsView zoom level.
        """

        #lod = option.levelOfDetailFromTransform(painter.worldTransform())

        penWidth = max(self.minPenWidth, min(self.maxPenWidth,
                       self.thickness/self.view.transform().m11()))

        self.pen.setWidthF(penWidth)
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
        Updates the "tails" on the measuring line dimension object. The tails
        are short lines orthogonal to the main dimension line on each end of
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


