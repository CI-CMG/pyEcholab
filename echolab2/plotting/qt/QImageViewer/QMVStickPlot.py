"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from QMVStick import QMVStick

class QMVStickPlot(QGraphicsItemGroup):

    """
    QMVStickPlot implements, er, stickplots for QMapviewer. This has primarily
    be tested and used in plotting backscatter by class.

    QMVStickPlot Arguments:


        color - a 3 element list or tuple containing the RGB triplet
                specifying the color of the line or mline.
        thickness - A float specifying the thickness of the line.
        alpha - A integer specifying the opacity of the line. 0 is transparent
                and 255 is solid.
        linestyle - '=' for solid, '-' for dashed, and '.' for dotted.

    """

    def __init__(self, locations, magnitudes, scale, classname='', stickids=None, angle=90.0,
                    color=[220,10,10], thickness=2.0, alpha=255, linestyle='=',
                    view=None, parent=None):
        super(QMVStickPlot, self).__init__(parent)

        self.sticks = []

        #  create the sticks
        nSticks = len(locations)
        for i in range(nSticks):
            #  if we've been given a list of ID's, get the ID text
            if (stickids):
                idText = stickids[i]
            else:
                idText = ''

            #  create a stick
            stick = QMVStick(locations[i], magnitudes[i], scale, angle=angle, color=color,
                    thickness=thickness, alpha=alpha, linestyle=linestyle, view=view,
                    parent=self, classname=classname, id=idText)

            #  add the stick to our list of sticks
            self.sticks.append(stick)
            self.addToGroup(stick)

        #  now set selectable/movable flags for the itemgroup
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)


    def setAngle(self, angle):
        """
        Set the angle of the sticks
        """

        for stick in self.sticks:
            stick.setAngle(angle)


    def setScale(self, scale):
        """
        Set the stick scale.
        """

        for stick in self.sticks:
            stick.setScale(scale)


    def setColor(self, color):
        """
        Sets the dimension line color. Color is a 3 element list or tuple containing
        the RGB triplet specifying the color of the line or a QColor object.
        """

        for stick in self.sticks:
            stick.setColor(color, update=False)

        self.update()


    def invertColor(self, invert):

        for stick in self.sticks:
            stick.invertColor(invert, update=False)

        self.update()


    def setWidth(self, width):
        """
        Sets the width of the dimension line. Note that this value will
        be constrained to the minPenWidth and maxPenWidth properties of the
        object.
        """

        for stick in self.sticks:
            stick.setWidth(width)

    def setAlpha(self, alpha):
        """
        Set the alpha leven (transparency) of the dimension line. Valid values
        are 0 (transparent) to 255 (solid)
        """

        for stick in self.sticks:
            stick.setAlpha(alpha, update=False)

        self.update()

