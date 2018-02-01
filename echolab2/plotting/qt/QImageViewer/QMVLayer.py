"""
Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class QMVLayer(QGraphicsItemGroup):
    """

    """

    def __init__(self, parent, name='QMVLayer', selectable=False, movable=False):
        super(QMVLayer, self).__init__(parent)

        self.name = name
        self.setFlag(QGraphicsItem.ItemIsSelectable, selectable)
        self.setFlag(QGraphicsItem.ItemIsMovable, movable)
