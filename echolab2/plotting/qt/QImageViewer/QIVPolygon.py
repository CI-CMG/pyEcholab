"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .QIVPolygonItem import QIVPolygonItem
from .QIVMarkerText import QIVMarkerText

class QIVPolygon(QGraphicsItemGroup):
    """
    QIVPolygon implememts open and closed polygon items with simplified vertex
    labeling. The labels are implemented by QIVMarkerText, are non-scaling,
    and provide the ability to justify and offset labels from the vertex anchor.

    If you only need a simple polygon object without labeling, you can use
    QIVPolygonItem directly.

    If a polygon is specified as "open" the last vertex is not connected
    the first and the polygon cannot be filled. You can also think of open
    polygons as polylines. "Closed" polygons do have their last vertext connected
    to the first. Closed polygons can be filled by setting the fill keyword.

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
                 alpha=255, linestyle='=', fill=None, selectable=True,
                 movable=False, selectThickness=4.0, selectColor=None,
                 closed=True, view=None, parent=None, name='QIVPolygon',
                 isCosmetic=False):
        super(QIVPolygon, self).__init__(parent)

        self.name = name
        self.view = view
        self.polygon = None
        self.labels = []

        #  create the polygon item - note that we make the item non-selectable and non-movable
        #  since we want to select/move the "this" object (the QGraphicsItemGroup) and not the
        #  items contained in it.
        self.polygon = QIVPolygonItem(vertices,  color=color, thickness=thickness,
                 alpha=alpha, linestyle=linestyle, fill=fill, selectable=False,
                 selectThickness=selectThickness, selectColor=selectColor,
                 movable=False, closed=closed, parent=self, isCosmetic=isCosmetic)

        #  and add it to our item group
        self.addToGroup(self.polygon)

        #  now set selectable/movable flags for the itemgroup
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, movable)


    def getLabelsFromName(self, labelName):
        '''
        returns a list of QIVMarkerText references that share the name provided in the
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


    def addLabel(self, vertex, text, size=10, font='helvetica', italics=False, weight=-1,
                color=[0,0,0], alpha=255, halign='left', valign='top', name='QIVPolygonLabel',
                offset=None):
        """
        Add a label to the polygon at a specified vertex. Labels are children of the polygon.

            vertex (int)      - The 0 based vertex number to attach the label to.
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

        #  get the position given the vertex index
        position = self.polygon[vertex]

        #  create a QIVMarkerText associated with the provided mark/line
        textItem = QIVMarkerText(position, text, offset=offset, size=size, font=font, italics=italics,
                                 weight=weight, color=color, alpha=alpha, halign=halign,
                                 valign=valign, name=name, view=self.view)

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



    '''
    The following methods operate on the QIVPolygonItem object. See that
    class for calling details.
    '''

    def setColor(self, *args, **kwargs):
        self.polygon.setColor(*args, **kwargs)

    def setSelectColor(self, *args, **kwargs):
        self.polygon.setSelectColor(*args, **kwargs)

    def setFill(self, *args, **kwargs):
         self.polygon.setFill(*args, **kwargs)

    def setSelected(self, *args):
         self.polygon.setSelected(*args)

    def isSelected(self):
        return self.polygon.isSelected()

    def setThickness(self, *args):
        self.polygon.setThickness(*args)

    def setSelectThickness(self, *args):
        self.polygon.setSelectThickness(*args)

    def setAlpha(self, *args, **kwargs):
        self.polygon.setAlpha(*args, **kwargs)

