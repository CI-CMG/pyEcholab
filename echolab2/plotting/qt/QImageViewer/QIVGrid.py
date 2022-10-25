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

class QIVGrid(QGraphicsItemGroup):
    """
    Add a grid to the scene.
    
    
    THIS CLASS IS A BIT OF A MESS - It has 

          text (string)  - The text to add to the scene.
      position (QPointF) - The position of the text anchor point.
          size (int)     - The text size, in point size


         color (list)    - A 3 element list or tuple containing the RGB triplet
                           specifying the color of the text.
         alpha (int)     - An integer specifying the opacity of the text. 0 is transparent
                           and 255 is solid.

    """

    def __init__(self, layerVerts, layerLabels, intervalVerts, intervalLabels,
            color=[0,0,0], thickness=2.0, alpha=255, view=None, labelGrid=True,
            labelColor=[255,255,255], labelBackdrop=True, backdropColor=[0,0,0],
            backdropAlpha=150):
        super(QIVGrid, self).__init__()

        self.gridColor = color
        self.gridAlpha = alpha
        self.gridThickness = thickness
        self.view = view
        self.labels = []
        self.gridLines = []
        self.gridLabels = []
        self.intervalBounds = []
        self.layerBounds = []
        self.isCosmetic = True
        self.labelColor = labelColor
        self.labelBackdrop = labelBackdrop
        self.backdropColor = backdropColor
        self.backdropAlpha = backdropAlpha

        #  get the pen to paint the mark
        gridPen = self.getPen(self.gridColor, self.gridAlpha, '=', self.gridThickness)

        #  add the grid layer lines
        n_layers = int(len(layerVerts) / 2)
        for h in range(n_layers):
            i = h * 2
            j = i + 1
            
            gridLine = QGraphicsLineItem(layerVerts[i][0],layerVerts[i][1],
                    layerVerts[j][0],layerVerts[j][1])
            gridLine.setPen(gridPen)
            self.gridLines.append(gridLine)
            
            if h < n_layers - 1:
                self.layerBounds.append([layerVerts[i][1],layerVerts[j+1][1]])
            
            #  disable transforms for the marker and set the movable and selectable flags
            #self.markItem.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
            gridLine.setFlag(QGraphicsItem.ItemIsSelectable, False)
            gridLine.setFlag(QGraphicsItem.ItemIsMovable, False)
            
            self.addToGroup(gridLine)
            
            if labelGrid:
                #  now add the grid label
                labelPos = QPointF(layerVerts[i][0],layerVerts[i][1])
                labelOffset = QPointF(0.5,3)
                label = '%2.1f m' % (layerLabels[h])
                self.addLabel(label, labelPos, size=10, color=self.labelColor,
                        alpha=self.gridAlpha, halign='left', valign='top',
                        offset=labelOffset, isCosmetic=True,
                        drawBackdrop=self.labelBackdrop, name='gridLabel')
                        
        #  add the interval lines
        n_intervals = int(len(intervalVerts) / 2)
        for h in range(n_intervals):
            i = h * 2
            j = i + 1
            
            gridLine = QGraphicsLineItem(intervalVerts[i][0],intervalVerts[i][1],
                    intervalVerts[j][0],intervalVerts[j][1])
            gridLine.setPen(gridPen)
            self.gridLines.append(gridLine)
            
            if h < n_intervals - 1:
                self.intervalBounds.append([intervalVerts[i][0],intervalVerts[j+1][0]])
            
            
            #  disable transforms for the marker and set the movable and selectable flags

            gridLine.setFlag(QGraphicsItem.ItemIsSelectable, False)
            gridLine.setFlag(QGraphicsItem.ItemIsMovable, False)
            
            self.addToGroup(gridLine)
            
            #  add the label if needed (skip the first one since it obscures layer labels)
            if labelGrid and h > 0:
                #  now add the grid label
                labelPos = QPointF(intervalVerts[i][0],intervalVerts[i][1])
                labelOffset = QPointF(0,5)
                label = str(intervalLabels[h])
                self.addLabel(label, labelPos, size=10, color=self.labelColor,
                        alpha=self.gridAlpha, halign='left', valign='top',
                        offset=labelOffset, rotation=90,
                        isCosmetic=True, drawBackdrop=self.labelBackdrop,
                        name='gridLabel')

        #self.moveBy(0.5,0)

        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


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


    def clearLabels(self):
        '''
        clearLabels is a convenience method to clear all labels associated with this mark.
        '''
        self.removeLabel(self.labels)


    def getLabels(self):
        '''
        getLabels returns the list of labels associated with this mark
        '''
        return self.labels


    def addCellLabel(self, text, relative_position, interval, layer, **kwargs):
        
        abs_x = self.intervalBounds[interval][0] + ((self.intervalBounds[interval][1] -
                self.intervalBounds[interval][0]) * relative_position[0])
        abs_y = self.layerBounds[layer][0] + ((self.layerBounds[layer][1] -
                self.layerBounds[layer][0]) * relative_position[1])
        
        position = QPointF(abs_x, abs_y)
        
        self.addLabel(text, position, **kwargs)
        

    def addLabel(self, text, position, size=10, font='helvetica', italics=False, weight=-1,
                color=[0,0,0], alpha=255, halign='left', valign='top', name='gridLabel',
                offset=None, rotation=0, isCosmetic=False, drawBackdrop=False,
                backdropColor=[0,0,0], backdropAlpha=150):
        """
        Add a label to the gridline.

              text (string)   - The text to add to the dimension line.
          position (QPointF)
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
                                 valign=valign, view=self.view, rotation=rotation,
                                 isCosmetic=isCosmetic, drawBackdrop=drawBackdrop,
                                 backdropColor=backdropColor, backdropAlpha=backdropAlpha)

        #  add the label to our list of labels
        self.labels.append(textItem)
        self.addToGroup(textItem)


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


    def setGridColor(self, color):
        """
        Sets the marker color. Color is a 3 element list or tuple containing the RGB triplet.
        """

        #  change the marker brush color
        self.markColor = color
        if not self.selected:
            markPen = self.getPen(self.markColor, self.markAlpha, '=', self.markThickness)
            self.markItem.setPen(markPen)


    def setGridAlpha(self, alpha):
        """
        Set the alpha level (transparency) of the marker. Valid values
        are 0 (transparent) to 255 (solid)
        """

        #  change the mark's pen alpha
        self.markAlpha = alpha
        if not self.selected:
            markPen = self.getPen(self.markColor, self.markAlpha, '=', self.markThickness)
            self.markItem.setPen(markPen)


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

        if self.isCosmetic:
            pen.setCosmetic(True)

        return pen
