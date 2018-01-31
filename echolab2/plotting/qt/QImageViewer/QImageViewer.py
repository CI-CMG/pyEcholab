"""
QImageViewer is a PyQt widget which displays images and provides panning, zooming,
and other features common to image display. It also has methods for placing marks
and it handles the details of transforming coordinates so you always work in
image coordinates.

Public Properties

  doSelections - Set this property to True to have QImageViewer handle selections.

                 Default = True


 autoWheelZoom - Set this property to True to have QImageViewer zoom on mouse wheel
                 events and False to not. If this value is set to false,
                 QImageViewer will emit mouse wheel events. It will NOT emit these
                 events if it is set to True.

                 Default = True


 defaultCursor - Set this to the cursor that will be active when the pointer
                 is in the widget. The widget will automatically change the
                 cursor to Qt.ArrowCursor when the pointer moves out of the
                 widget.

                 Default = Qt.CrossCursor


    zoomFactor - set this to the zoom factor applied to each mouse
                 wheel click. Reasonable values are > 1 and < 2.

                 Default = 1.15


     zoomLevel - This property contains the current zoom level. DO NOT SET THIS.


       minZoom - Set this to the minimum allowed zoom level. This only applies
                 to mouse wheel zooming. You are responsible for passing sane
                 values to the manual zoom method.

                 Default = 0


       maxZoom - Set this to the maximum allowed zoom level. This only applies
                 to mouse wheel zooming. You are responsible for passing sane
                 values to the manual zoom method.

                 Default = 20


          name - Set this to a unique string to identify events from this object.
                 This is most useful when multiple objects are used in the same
                 application.

                 Default = "QImageViewer"


        panKey - Set this to the Qt Key Constant representing the keyboard key
                 that will be used as the modifier to enable pan mode. Set
                 to None to disable pan mode.For specific implementation
                 requirements you can disable this feature and handle this in
                 your application.

                 Default = Qt.Key_Alt (Alt key)


 rubberBandKey - Set this to the Qt Key Constant representing the keyboard key
                 that will be used as the modifier to enable rubber band selection
                 mode. Set to None to disable rubber band mode. For specific
                 implementation requirements you can disable this feature and handle
                 this in your application.

                 Note that this only implements the standard rubber band selection
                 box. If you wish to use the "line" or "mline" rubber band like tools
                 you will need to implement them yourself using the mousePressEvent
                 and mouseReleaseEvent signals and calling startRubberBand and
                 endRubberBand yourself in your mouse event handlers.

                 Default = Qt.Key_Shift (Shift key)


  selectAddKey - Set this to the Qt Key Constant representing the keyboard key
                 that will be used as the modifier to enable adding items to the current
                 set of selected items.

                 Default = Qt.Key_Control  (Control key)

Public Methods

  <INSERT DOCUMENTATION HERE>


Signals

    mouseReleaseEvent - (object, click location (QPointF), mouse button (int), keyboard modifier (int), items (list of QGraphicsItem))
      mousePressEvent - (object, click location (QPointF), mouse button (int), keyboard modifier (int), items (list of QGraphicsItem))
       mouseMoveEvent - (object, mouse pointer position (QPointF), keyboard modifier (int), draggedMarks (list))
  rubberBandSelection - (object, selection rectangle in image units (QRectF), items (list of QGraphicsItem))
        keyPressEvent - (object, keyboard event structure)
      keyReleaseEvent - (object, keyboard event structure)
           wheelEvent - (object, mouse event structure) (NOT EMITTED IF autoWheelZoom == True)



Rick Towler
Midwater Assessment and Conservation Engineering
NOAA Alaska Fisheries Science Center
rick.towler@noaa.gov

"""

import os
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *
from QViewerBase import QViewerBase
from QEnhancedImage import QEnhancedImage
from imageAdjustmentsDlg import imageAdjustmentsDlg

class QImageViewer(QViewerBase):

    def __init__(self, parent=None, useGL=False, backgroundColor=[50,50,50]):
        super(QImageViewer, self).__init__(parent, useGL=useGL,
                backgroundColor=backgroundColor)

        #  set the default name
        self.name = 'QImageViewer'

        #  create an "enhanced image" object which will load images and apply
        #  adjustments before display. Also create the dialog that allows the
        #  user to adjust these settings
        self.image = QEnhancedImage()

        self.adjustmentDialog = imageAdjustmentsDlg()
        try:
            self.adjustmentDialog.setWindowIcon(QIcon('resources' + os.sep + 'equalizer.png'))
        except:
            pass
        self.connect(self.adjustmentDialog, SIGNAL('imageAdjustments(PyQt_PyObject)'), self.imageAdjusted)

        #  pass a reference to the adjustments dialog to the image
        self.image.adjustmentsDialog = self.adjustmentDialog

        #  set up the context menu signal
        self.enableContextMenu()


    def enableContextMenu(self):
        """
        enableContextMenu enables the QImageViewer custom context menu
        """
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.showContextMenu);


    def disableContextMenu(self):
        """
        disableContextMenu disables the QImageViewer custom context menu
        """
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.disconnect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.showContextMenu);


    def imageAdjusted(self, parameters):
        """
        imageAdjusted is a slot called when the user alters parameters on the
        image adjustments dialog. The slot updates the image properties and
        requests a new pixmap with these adjustments applied.
        """

        #  pass the new image adjustment parameters to the "enhanced" image object
        self.image.setParameters(parameters)

        #  get a pixmap to display
        self.imgPixmap = self.image.toPixmap()

        #  update the pixmap
        self.imgPixmapItem.setPixmap(self.imgPixmap)


    def setRotation(self, rotation):
        """
        setRotation  sets the image rotation in degrees. Images are rotated
        prior to display.
        """
        #  ignore non numeric input
        try:
            self.image.transform.rotate(float(rotation))
        except:
            pass


    def setScale(self, sx, sy):
        """
        setScale scales the image coordinate system by the provided scalars sx and sy.
        """
        #  ignore non numeric input
        try:
            self.image.transform.scale(float(sx), float(sy))
        except:
            pass


    def setSubsampleRect(self, qrectangle, alpha=50):
        """
        setSubsampleRect will cause the image area *outside* of the rectangle defined by
        the provided QRect to be rendered with the alpha value provided by the "alpha"
        keyword.

        This method can be used to present a subsection of an image to an analyst for
        subsampling within an image if target densities are too high.
        """

        self.image.setSubsampleRect(qrectangle, alpha)


    def resetTransform(self):
        """
        resetTransform resets the rotation and scaling transform
        """
        self.image.transform.reset()


    def showContextMenu(self, pos):
        """
        showContextMenu shows the context menu when someone right clicks on the viewer
        """

        menu = QMenu(self)
        action = QAction('Adjust image properties...', self)
        self.connect(action, SIGNAL('triggered()'), self.showAdjustmentsDialog)
        menu.addAction(action)
        menu.exec_(self.mapToGlobal(pos));


    def showAdjustmentsDialog(self):
        """
        showAdjustmentsDialog displays the image adjustment dialog allowing the user
        to alter color/contrast/brightness of the image
        """
        adjustmentParms = self.image.getParameters()
        self.adjustmentDialog.setState(adjustmentParms)
        self.adjustmentDialog.show()


    def setName(self, name):
        """
        setName sets the name property of QImageViewer and its associated image adjustment dialog
        """
        self.name = str(name)
        self.adjustmentDialog.setName(name)


    def setImageFromFile(self, filename):
        """
        Set the QImageViewer image to the image specified by the provided filename.
        """

        #  load the image
        self.image.load(filename)
        self.imgPixmap = self.image.toPixmap()

        #  update the pixmap
        self.imgPixmapItem.setPixmap(self.imgPixmap)

        #  set the scene bounds - we never want the scene to grow bigger than our image
        p2 = QPointF(self.imgPixmap.width(), self.imgPixmap.height())
        self.scene.setSceneRect(QRectF(QPointF(0,0), p2))

        #  center the image in the viewport
        self.setCenterPoint(p2 / 2)


    def setImageFromPixmap(self, pixmap):
        """
        Set the QImageViewer image to the provided QPixmap
        """

        self.image.fromQPixmap(pixmap)
        self.imgPixmap = self.image.toPixmap()

        #  update the pixmap
        self.imgPixmapItem.setPixmap(self.imgPixmap)

        #  set the scene bounds - we never want the scene to grow bigger than our image
        p2 = QPointF(self.imgPixmap.width(), self.imgPixmap.height())
        self.scene.setSceneRect(QRectF(QPointF(0,0), p2))

        #  center the image in the viewport
        self.setCenterPoint(p2 / 2)


    def setImageFromImage(self, image):
        """
        Set the QImageViewer image to the provided QImage
        """

        self.image.fromQImage(image)
        self.imgPixmap = self.image.toPixmap()

        #  update the pixmap
        self.imgPixmapItem.setPixmap(self.imgPixmap)

        #  set the scene bounds - we never want the scene to grow bigger than our image
        p2 = QPointF(self.imgPixmap.width(), self.imgPixmap.height())
        self.scene.setSceneRect(QRectF(QPointF(0,0), p2))

        #  center the image in the viewport
        self.setCenterPoint(p2 / 2)


    def setImageFromMat(self, imageData, normalize=False):
        """
        Set the QImageViewer image based on data from a numpy matrix. The first
        dimension of the maxtrix represents the vertical image axis; the optional
        third dimension is supposed to contain 1-4 channels
        The parameter normalize can be used to normalize an image value range to 0..255:
            normalize = (nmin,nmax):
                scale and clip image values from nmin..nmax to 0..255
            normalize = nmax:
                lets nmin default to zero, i.e. scale & clip the range 0..nmax to 0..255
            normalize = True:
                scale image values to 0..255 (same as passing (array.min(), array.max()))

        If array contains masked values, the corresponding pixels will be transparent
        in the result. Thus, the result will be of QImage.Format_ARGB32 if the input
        already contains an alpha channel (i.e. has shape (H,W,4)) or if there are
        masked pixels, and QImage.Format_RGB32 otherwise.
        """

        self.image.fromMat(imageData, normalize=normalize)
        self.imgPixmap = self.image.toPixmap()

        #  update the pixmap
        self.imgPixmapItem.setPixmap(self.imgPixmap)

        #  set the scene bounds - we never want the scene to grow bigger than our image
        p2 = QPointF(self.imgPixmap.width(), self.imgPixmap.height())
        self.scene.setSceneRect(QRectF(QPointF(0,0), p2))

        #  center the image in the viewport
        self.setCenterPoint(p2 / 2)
