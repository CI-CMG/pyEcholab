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

class QIVMarker(QGraphicsItemGroup):
    """
    Add text to the scene given the text and position. The function returns
    the reference to the QGraphicsItem. The text font size scales inversely
    with the views scale, that is it shrinks when you zoom in.

          text (string)  - The text to add to the scene.
      position (QPointF) - The position of the text anchor point.
          size (int)     - The text size, in point size

        weight (int)     - Set to an integer in the range 0-99. 50 is normal, 75 is bold.
         color (list)    - A 3 element list or tuple containing the RGB triplet
                           specifying the color of the text.
         alpha (int)     - An integer specifying the opacity of the text. 0 is transparent
                           and 255 is solid.

    """

    def __init__(self, position, style='+', color=[240,0,0], selectColor=[5,220,250],
                 size=1.0, thickness=1.0, selectThickness=2.0, alpha=255, name='QIVMark',
                 view=None, selectable=True, movable=False, fill=None):
        super(QIVMarker, self).__init__()

        self.name = name
        self.markColor = color
        self.selectColor = selectColor
        self.markAlpha = alpha
        self.markThickness = thickness
        self.selectThickness = selectThickness
        self.selected = False
        self.position = position
        self.view = view
        self.labels = []

        #  check if we've been passed a valid fill
        self.markFill = None
        if (fill):
            if (len(fill) > 2):
                self.markFill = fill

        #  get the pen to paint the mark
        markPen = self.getPen(self.markColor, self.markAlpha, '=', self.markThickness)

        #  get the brush, if needed
        if (self.markFill):
            if (len(self.markFill) > 3):
                self.markAlpha = self.markFill[3]
            markBrush = self.getBrush(self.markFill, self.markAlpha)

        if (style.lower() == '+') or (style.lower() == 'x'):
            #  create a plus or x mark
            mark = QPolygonF()
            mark.append(QPointF(0,-5))
            mark.append(QPointF(0,5))
            mark.append(QPointF(0,0))
            mark.append(QPointF(-5,0))
            mark.append(QPointF(5,0))
            mark.append(QPointF(0,0))

            #  create the graphic primitive
            self.markItem = QGraphicsPolygonItem(mark)
            if style.lower() == 'x':
                #  x is just a plus rotated 45 degrees
                self.markItem.setRotation(45)

        elif (style.lower() == 'd'):
            #  create a diamond mark
            mark = QPolygonF()
            mark.append(QPointF(0,-5))
            mark.append(QPointF(-5,0))
            mark.append(QPointF(0,5))
            mark.append(QPointF(5,0))
            mark.append(QPointF(0,-5))
            #  bring it around again to fill in the top corner
            mark.append(QPointF(-5,0))

            #  create the graphic primitive
            self.markItem = QGraphicsPolygonItem(mark)

        elif (style.lower() == 'o'):
            #  create a circle
            mark = QRectF(-4, -4, 8, 8)

            #  create the graphic primitive
            self.markItem = QGraphicsEllipseItem(mark)

        #  set the pen, scale, and position
        self.markItem.setPen(markPen)
        self.markItem.setScale(size)
        self.markItem.setPos(position)
        if (self.markFill):
            self.markItem.setBrush(markBrush)

        #  disable transforms for the marker and set the movable and selectable flags
        self.markItem.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.markItem.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.markItem.setFlag(QGraphicsItem.ItemIsMovable, False)

        #  now set these properties for the itemgroup
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, movable)

        #  add the mark to our group
        self.addToGroup(self.markItem)


    def pos(self):
        '''
        pos overrides QGraphicsItemGroup's pos method and returns the position of the
        mark (in image coordinates)
        '''

        return self.mapToScene(QPointF(self.markItem.pos().toPoint()))


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


    def removeLabel(self, labels):
        '''
        removeLabel removes a marker label given the label reference or labelName.
        You can also pass a list of references or names. If the label name is provided,
        all labels with that name will be removed.
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
            #  we've been given a single item - check if it is a name or ref
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


    def removeAllLabels(self):
        '''
        removeAllLabels is a convenience method to clear all labels associated with this mark.
        '''
        self.removeLabel(self.labels)


    def getLabels(self):
        '''
        getLabels returns the list of labels associated with this mark
        '''
        return self.labels


    def addLabel(self, text, size=10, font='helvetica', italics=False, weight=-1,
                color=[0,0,0], alpha=255, halign='left', valign='top', name='QIVDimLabel',
                offset=None):
        """
        Add a label to the mark. Labels are children of the mark. Position is assumed to be
        the mark center.

              text (string)   - The text to add to the dimension line.
            offset (QPointF)  - An offset from your position. The units are pixels at the
                                image's native resolution. This gets muddled when used with
                                classes that transform coordinates, especially QMapViewer.
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

        #  get the marker position
        position = self.markItem.pos()

        #  create a QIVMarkerText associated with the provided mark/line
        textItem = QIVMarkerText(position, text, offset=offset, size=size, font=font, italics=italics,
                                 weight=weight, color=color, alpha=alpha, halign=halign,
                                 valign=valign, name=name, view=self.view)

        #  add the label to our list of labels
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


    def setColor(self, color):
        """
        Sets the marker color. Color is a 3 element list or tuple containing the RGB triplet.
        """

        #  change the marker brush color
        self.markColor = color
        if not self.selected:
            markPen = self.getPen(self.markColor, self.markAlpha, '=', self.markThickness)
            self.markItem.setPen(markPen)


    def setSelectColor(self, color):
        """
        Sets the marker color. Color is a 3 element list or tuple containing the RGB triplet.
        """

        #  change the mark's selection pen color
        self.selectColor = color
        if self.selected:
            markPen = self.getPen(self.selectColor, self.markAlpha, '=', self.selectThickness)
            self.markItem.setPen(markPen)


    def setAlpha(self, alpha):
        """
        Set the alpha level (transparency) of the marker. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the mark's pen alpha
        self.markAlpha = alpha
        if not self.selected:
            markPen = self.getPen(self.markColor, self.markAlpha, '=', self.markThickness)
            self.markItem.setPen(markPen)


    def setSelected(self, selected):
        '''
        setSelected sets this mark as being selected. It changes the marker pen color to
        the "selected" color and sets the "selected" property to true. We're not using Qt's
        built in selection handling for now so we're not calling the mark's "setSelected"
        method purposefully.
        '''

        if selected:
            markPen = self.getPen(self.selectColor, self.markAlpha, '=', self.selectThickness)
            self.markItem.setPen(markPen)
            self.selected = True
        else:
            markPen = self.getPen(self.markColor, self.markAlpha, '=', self.markThickness)
            self.markItem.setPen(markPen)
            self.selected = False


    def isSelected(self):
        '''
        isSelected returns true if this mark is selected, false if not.
        '''
        return self.selected


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


    def getBrush(self, color, alpha):

        brushColor = QColor(color[0], color[1], color[2], alpha)
        brush = QBrush(brushColor)

        return brush


    def setFill(self, color):
        """
        Sets the mark fill color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line or a QColor object.
        Set color to None to disable fill.
        """

        #  set the brush for filling the polygon
        if (color):
            #  check if we've been given a QColor object to use as fill
            if (fill.__class__.__name__.lower() == 'qcolor'):
                #  we have a QColor object
                self.markItem.setBrush(QBrush(color))
            else:
                #  must be a list - if alpha isn't explicitly supplied, use the outline value
                if (len(color) == 3):
                    fill.append(self.alpha)
                brush = QBrush(QColor(color[0], color[1], color[2], color[3]))
                self.markItem.setBrush(brush)
        else:
            #  None passed - means no fill
            self.markItem.setBrush(QBrush())


    def setThickness(self, thickness):
        '''
        setThickness sets the marks unselected line width
        '''
        #  update the thickness property
        self.markThickness = thickness

        #  call setSelected to update the pen depending on the select state
        self.setSelected(self.selected)


    def setSelectThickness(self, thickness):
        '''
        setSelectThickness sets the marks selected line width
        '''
        #  update the thickness property
        self.selectThickness = thickness

        #  call setSelected to update the pen depending on the select state
        self.setSelected(self.selected)

