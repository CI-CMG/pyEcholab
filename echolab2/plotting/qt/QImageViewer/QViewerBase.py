"""
QViewerBase is a PyQt widget which uses the Qt Graphics View system to display
"stuff" providing panning, zooming, and other features common to "stuff" display.
It also has methods for placing marks and lines/polygons and it handles the details
of transforming coordinates so you always work in intuitive coordinates.

QViewerBase is the base class which various child classes inherit from. These child
classes such as QImageViewer (used for viewing images), QMapViewer (used for viewing
maps) and QEchogramViewer (used for viewing echograms) are the classes that you
would use in your applications.


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

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from .QIVDimensionLine import QIVDimensionLine
from .QIVMarkerText import QIVMarkerText
from .QIVHudText import QIVHudText
from .QIVMarker import QIVMarker
from .QIVPolygon import QIVPolygon
from .QIVPolygonItem import QIVPolygonItem

class QViewerBase(QGraphicsView):

    #  define PyQt Signals
    mouseWheel = pyqtSignal(object, object)
    mouseRelease = pyqtSignal(object, 'QPointF', int, object, list)
    mousePress = pyqtSignal(object, 'QPointF', int, object, list)
    mouseMove = pyqtSignal(object, 'QPointF', object, list, list)
    rubberBand = pyqtSignal(object, 'QRect', list)
    keyRelease = pyqtSignal(object, object)
    keyPress = pyqtSignal(object, object)
    imageData = pyqtSignal('QImage')

    def __init__(self, parent=None, useGL=False, backgroundColor=[50,50,50]):
        super(QViewerBase, self).__init__(parent)

        #  define the default public properties
        self.autoWheelZoom = True
        self.doSelections = True
        self.zoomFactor = 1.15
        self.zoomLevel = 0
        self.minZoom = -2
        self.maxZoom = 20
        self.name = 'QViewerBase'
        self.defaultCursor = Qt.CrossCursor
        self.backgroundColor = QColor(50,50,50,255)
        self.stickyScale = (1, 1)

        #  define the default modifier keys
        self.panKey = Qt.Key_Alt
        self.rubberBandKey = Qt.Key_Shift
        self.selectAddKey = Qt.Key_Escape
        self.zoomKey = Qt.Key_Control

        #  define the default "private" properties
        self.leftBtnClicked = False
        self.glEnabled = False
        self.rotation = 0
        self.centerPoint = QPointF(0,0)
        self.lastPanPoint = QPoint(0,0)
        self.lastClickPoint = QPoint(0,0)
        self.currentKbKey = None
        self.panning = False
        self.isZooming = False
        self.__zooming=False
        self.dimensionLine = None
        self.rubberBandLine = None
        self.rubberBanding = False
        self.dimensioning = False
        self.doRubberBandSelection = False
        self.isSettingCtrPt = False
        self.selectionRadius = QPoint(1, 1)
        self.selectionArea = QRect(0, 0, 6, 6)
        self.selectedItems = []
        self.hudItems = []
        self.sceneItems = []

        #  enable mouse tracking
        self.setMouseTracking(True)

        #  set the default rendering hints
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform |
                            QPainter.TextAntialiasing)

        #  set up the OGL widget if enabled
        if useGL:
            self.setOpenGLRendering(True)

        #  create the scene
        self.createScene()


    def setName(self, name):
        """
        setName sets the name property of Q*Viewer
        """
        self.name = str(name)


    def setOpenGLRendering(self, enable):
        """
        setOpenGLRendering will enable or disable OpenGL rendering for the graphicsview window.
        OpenGL rendering will generally render complex scenes faster than the Qt software renderer.
        Note that if your graphics hardware doesn't support vertex and/or fragment shaders you
        will see error text in the console when rendering is enabled. This can be ignored.
        """

        if (enable and not self.glEnabled ):
            #  enable an OGL viewport widget
            self.glEnabled = True
            self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers| QGL.DirectRendering), self))
            self.setRenderHints(QPainter.HighQualityAntialiasing)
            self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
            self.update()
        elif (self.glEnabled  and not enable):
            #  enable a non OGL viewport widget
            self.setViewport(0)
            self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform |
                        QPainter.TextAntialiasing)
            self.update()
            self.glEnabled = False


    def setBackgroundColor(self, color, alpha=255):
        """
        setBackgroundColor will set the background color of the display widget (graphics window)
        """

        if (len(color) == 3):
            color.append(alpha)
        self.backgroundColor = QColor(color[0],color[1],color[2],color[3])
        self.setBackgroundBrush(QBrush(self.backgroundColor))


    def createScene(self):
        """
        Creates an empty scene with default grey pixmap "background"
        """
        #  create the graphics scene
        self.scene = QGraphicsScene()

        #  set the background color
        self.setBackgroundBrush(QBrush(self.backgroundColor))

        # create the image pixmap
        self.imgPixmap = QPixmap()

        #  add the pixmap to the scene and get the reference to the QGraphicsPixmapItem
        self.imgPixmapItem = self.scene.addPixmap(self.imgPixmap)

        #  set our scene...
        self.setScene(self.scene)
        self.sceneItems = []


    def removeScene(self):
        """
        removeScene removes and destroys the scene from the QGraphicsview. You
        must call createScene before attempting to draw anything. Usually you
        would simply call clearViewer().
        """
        del self.scene, self.imgPixmapItem


    def saveView(self, filename):
        """
        save the rendered *view* to a file. This is not the whole image, only the visible
        portion as rendered in the view. The resolution of the saved image will be the same
        as the window dimensions. You must provide the full path and file name. The image
        type will be inferred from the file extension. Typical values would be "jpg", "jpeg",
        or "png".
        """

        pixmap = self.grab();
        ok = pixmap.save(filename)
        if not ok:
            raise IOError('Unable to save image ' + filename)


    def saveImage(self, filename, width=None, height=None):
        """
        save the rendered scene to a file. This saves the entire image, marks, and lines
        regardless of the current view. The saved image resolution will be defined by the
        scene size but you can override that by passing a width and height. You must
        provide the full path and file name. The image type will be inferred from the file
        extension. Typical values would be "jpg", "jpeg", or "png".

        """

        if width is None:
            width = self.scene.width()
        if height is None:
            height = self.scene.height()

        #  create the empty image to render into and fill
        image = QImage(width, height,QImage.Format_ARGB32)
        image.fill(0)

        #  create the painter to render the image
        painter = QPainter(image)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        #  render it
        self.scene.render(painter)

        #TODO: Need to figure out how to apply "sticky" scaling from the view.
        #      Render to a hidden view that's the same size as the scene?

        #  and save
        ok = image.save(filename)
        if not ok:
            raise IOError('Unable to save image ' + filename)


    def clearViewer(self):
        """
        Clear the scene of the image and all marks.
        """

        self.removeScene()
        self.createScene()


    def setSelectionRadius(self, radius):
        """
        setSelectionRadius sets the radius (in pixels) of the selection area that is used to
        check for graphics items (marks) in the proximity of a click in the viewer. This allows
        for some slop when selecting items as the user doesn't have to directly hit the item.

        (The selection area is a rectangle so technically it sets the half-width and half-height
        of the selection rectangle but radius was easier to describe.)
        """

        if (radius < 1):
            radius = 1
        else:
            radius = int(round(radius))

        self.selectionArea = QRect(0, 0, radius*2, radius*2)
        self.selectionRadius = QPoint(radius, radius)


    def startDimensionLine(self, startPoint, endPoint=None, color=[245,10, 245],
                           thickness=1.5, alpha=255, linestyle='_', taillength=20):
        """
        Starts an interactive dimension line at the provided point. The point must be
        in image coordinates as type QPointF().

        This method is also called by addDimensionLine.

        startDimensionLine Arguments:

            startPoint - the starting location of the line object at QPointF()
            endPoint - the ending point of the line. You should not provide this
                       argument if you are starting an interactive dimension line.
            color - a 3 element list or tuple containing the RGB triplet
                    specifying the color of the line.
            thickness - A float specifying the thickness of the line.
            alpha - A integer specifying the opacity of the line. 0 is transparent
                    and 255 is solid.
            linestyle - '_' for solid, '-' for dashed, and '.' for dotted.
            taillength - a float specifying the length of the line "tails". The
                         tails are orthogonal lines centered at each end of the
                         dimension line. Set TailLength to 0 to disable the "tails"

        """

        if (not endPoint) or (startPoint == endPoint):
            #  the end point is not provided so we assume we're adding a dimension
            #  line interactively.
            self.dimensioning = True
            endPoint = startPoint

        #  create the dimension line
        dimensionLine = QIVDimensionLine(startPoint=startPoint, endPoint=endPoint, color=color,
                                thickness=thickness, alpha=alpha, linestyle=linestyle,
                                taillength=taillength, view=self)
        #  add it to our scene
        self.scene.addItem(dimensionLine)

        #  add it to our list of scene items
        self.sceneItems.append(dimensionLine)

        #  if this is an interactive operation store a reference to the line
        if (self.dimensioning):
            self.dimensionLine = dimensionLine

        return dimensionLine


    def endDimensionLine(self):
        """
        Ends and interactive dimension line. Returns a tuple containing the line
        coordinates and the line length.
        """

        #  unset our state variable and our reference to the line
        self.dimensioning = False
        dimensionLine = self.dimensionLine

        #  unset our internal reference to the line
        self.dimensionLine = None

        return dimensionLine


    def addDimensionLine(self, startpoint, endpoint, color=[245,10, 245], thickness=1.5,
                         alpha=255, linestyle='_', taillength=20):
        """
        Adds a dimension line running between the provided points. The points must be
        in image coordinates as type QPointF(). See startDimensionLine for more info.
        """

        dimLine = self.startDimensionLine(startPoint=startpoint, endPoint=endpoint, color=color,
                                thickness=thickness, alpha=alpha, linestyle=linestyle,
                                taillength=taillength)
        return dimLine


    def startRubberBand(self, point, color=[220,0,0], thickness=4.0, alpha=255,
            linestyle='=', fill=None, name='QIVRubberBand'):
        """
        Starts an interactive rubber band box selection at the provided point.
        The point must be in image coordinates as type QPointF(). This method does
        not use QRubberBand since it did not allow for fine control of it's visual
        properties and instead uses QIVPolygonItem.

        Note that by default rubber band box selection is enabled when <shift><left-click>
        dragging. This can be disabled by setting the rubberBandKey property to None.

        startRubberBand Arguments:

            point - the starting location of the rubberband object at QPointF()

            The other arguments are documented in the addPolygon method.

        """

        #  create the rubberband object
        self.rubberBandObj = QIVPolygonItem([], color=color, thickness=thickness,
                 alpha=alpha, linestyle=linestyle, fill=fill, name=name)

        #  set the origin
        self.rubberBandOrigin = point

        #  set the rubber band geometry
        self.rubberBandRect = QRectF(self.rubberBandOrigin, self.rubberBandOrigin)
        self.rubberBandObj.setGeometry(self.rubberBandRect)

        #  the the "am rubberbanding" state variable
        self.rubberBanding = True

        #  add it to our scene
        self.scene.addItem(self.rubberBandObj)

        #  add it to our list of scene items
        self.sceneItems.append(self.rubberBandObj)

        return self.rubberBandObj


    def endRubberBand(self, hide=True):
        """
        Ends rubber band selection that has been started with startRubberBand and
        returns the selection box as a QRectF.

        Set hide to false to keep the rubber band box displayed on the screen.
        """

        #  if we're "hiding" the rubber band box, remove it from the scene
        if (hide):
            self.removeItem(self.rubberBandObj)

        #  get the bounding rectangle as QRectF
        boxCoords = self.rubberBandRect

        #  reset our rubber band box state variables
        self.rubberBandObj = None
        self.rubberBandRect = None
        self.rubberBanding = False
        self.rubberBandOrigin = None

        return boxCoords


    def addText(self, position, text, size=10, font='helvetica', italics=False, weight=-1,
                color=[0,0,0], alpha=255, halign='left', valign='top', name='QIVText',
                selectable=False, movable=False):
        """
        Add text to the scene given the text and position. The function returns the reference
        to the QIVMarkerText object that is added to the scene.

              text (string)   - The text to add to the scene.
          position (QPointF)  - The position of the text anchor point in image units.
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

        #  check if we've been passed a opencv Point2f object for position
        if (position.__class__.__name__.lower() == 'point2f'):
            #  convert the Point2f object to a QPointF object
            position = QPointF(position.x, position.y)

        #  create a QIVMarkerText based on the input options
        textItem = QIVMarkerText(position, text, size=size, font=font,
                italics=italics, weight=weight, color=color, alpha=alpha, halign=halign,
                valign=valign, name=name, view=self, selectable=selectable, movable=movable)

        #  add the text directly to the scene
        self.scene.addItem(textItem)

        #  add it to our list of scene items
        self.sceneItems.append(textItem)

        return textItem


    def addPolygon(self, verts, color=[220,0,0], thickness=1.0, alpha=255,
            linestyle='=', fill=None, selectable=True, movable=False,
            selectThickness=2.0, selectColor=None, closed=True,
            name='QIVPolygon', noadd=False, isCosmetic=False):
        """
        Add an arbitrary polygon to the scene. Polygons can be open and unfilled,
        closed and unfilled, or closed and filled.

                verts (list)  - A list of [x,y] pairs or a list of QPointF objects. You
                                can also pass a QRectF or QRect object to draw a rectangle.
                color (list)  - A 3 element list or tuple containing the RGB triplet
                                specifying the color of the text.
            thickness (float) - A float specifying the line thickness. Note that thickness
                                is related to scale. The larger your scene is, the thicker
                                your lines will need to be to be visible when zoomed out.
                alpha (int)   - An integer specifying the opacity of the text. 0 is transparent
                                and 255 is solid.
            linestyle (string)- A character specifying the polygon outline style. "=" is a solid
                                line, "-" is a dashed line, and "." is a dotted line.
                 fill (list)  - Set to a 3 or 4 element list that specifys the RGBA color of the
                                polygon fill. If set to None, the polygon will not be filled.
           selectable (bool)  - Set to True to make the polygon selectable. If selectable the item
                                will be included in QImageView mousePressEvent and mouseReleaseEvent
                                events.
              movable (bool)  - Set to True to make the polygon movable. If movable the item
                                will be moved if it is selected and dragged.
               closed (bool)  - Set to True to draw closed polygons (meaning the last vertex will be
                                connected to the first) or False to draw unconnected polygons (also
                                known as paths.) If fill is set, the polygon will always be
                                closed since the fill will flood the path, though there will not be
                                an edge on the "open" part of the path.

                                While "open" unfilled polygons are visually the same as lines, they
                                differ in that the "hit box" for the polygon generated line is a
                                axially aligned box containing all of the vertices. A line added
                                via the "addLine" method will have a hit box that follows the line
                                path allowing for precise selection of the line.
                noadd (bool)  - Set this to true to create the polygon item but not add it to the
                                scene or internal list of items. This is only used internally by
                                some subclasses to allow them to group items before adding to the
                                scene.
        """

        #  create the polygon object
        polygon = QIVPolygon(verts, color=color, thickness=thickness,
                 alpha=alpha, linestyle=linestyle, fill=fill, selectable=selectable,
                 movable=movable, closed=closed, view=self, name=name,isCosmetic=isCosmetic)

        if (not noadd):
            #  add the polygon to the scene
            self.scene.addItem(polygon)

            #  and add it to our list of items
            self.sceneItems.append(polygon)

        return polygon


    def addLine(self, verts, color=[220,0,0], thickness=1.0, alpha=255,
            linestyle='=', selectable=True, movable=True, isCosmetic=False):
        """
        Add an arbitrary line to the scene.

                verts (list)  - A list of [x,y] pairs or a list of QPointF objects
                color (list)  - A 3 element list or tuple containing the RGB triplet
                                specifying the color of the text.
            thickness (float) - A float specifying the line thickness. Note that thickness
                                is related to scale. The larger your scene is, the thicker
                                your lines will need to be to be visible when zoomed out.
                alpha (int)   - An integer specifying the opacity of the text. 0 is transparent
                                and 255 is solid.
            linestyle (string)- A character specifying the polygon outline style. "=" is a solid
                                line, "-" is a dashed line, and "." is a dotted line.
           selectable (bool)  - Set to True to make the polygon selectable. If selectable the item
                                will be included in QImageView mousePressEvent and mouseReleaseEvent
                                events.
              movable (bool)  - Set to True to make the polygon movable. If movable the item
                                will be moved if it is selected and dragged.

        """

        #  addLine is just a simplified interface to addPolygon
        return QViewerBase.addPolygon(self, verts, color=color, thickness=thickness, alpha=alpha,
                    linestyle=linestyle, selectable=selectable, movable=movable,
                    closed=False, isCosmetic=isCosmetic)


    def addMark(self, position, style='+', color=[220,0,0], selectColor=[5,220,250],
                 size=1.0, thickness=1.0, selectThickness=2.0, alpha=255, name='QIVMarker',
                 selectable=True, movable=False, fill=None):
        """
        Add a marker to the scene. Position can be a list with an x,y pair or a
        OpenCV Point2f object defining the mark location. You can add marker text
        using the addText method.

        Marker Options:

               style (string) - "+" for a plus mark. "x" for an X mark, "d" for a diamond, "o" for circle.
                 color (list) - a 3 element list or tuple containing the RGB triplet
                                specifying the color or the mark.
           selectColor (list) - a 3 element list or tuple containing the RGB triplet
                                specifying the color the mark will change to when selected.
                 size (float) - a float value specifying the scaling factor. The value must
                                be greater than 0. Values less than 1 will shrink the marker
                                and values greater then 1 will grow it.
            thickness (float) - A float specifying the thickness of the marker's outline.
      selectThickness (float) - A float specifying the thickness of the marker's outline when selected.
              alpha (integer) - A integer specifying the opacity of the mark. 0 is transparent
                                and 255 is solid.
                name (string) - A string specifying the name associated with this mark. You
                                can use mark names to differentiate between your marks.
        """

        #  check if we've been passed a Point2f object
        if position.__class__.__name__.lower() == 'point2f':
            #  convert the Point2f object to QPointf object
            position = [position.x, position.y]

        markItem = QIVMarker(position, style=style, color=color, selectColor=selectColor,
                             size=size, thickness=thickness, selectThickness=selectThickness,
                             alpha=alpha, name=name, view=self, selectable=selectable,
                             movable=movable, fill=fill)

        #  add the mark to the scene
        self.scene.addItem(markItem)

        #  and add the mark to our internal list of items
        self.sceneItems.append(markItem)

        return markItem


    def getMarkCenter(self, mark):
        """
        Return the center of a mark in image units
        """

        return mark.mapToScene(mark.boundingRect().center())


    def resetView(self):
        """
            resetView sets the graphics view transformation matrix to the identity matrix.
            In other words, it resets the view to the default zoom and pan values.
        """

        self.zoomLevel = 0
        self.setTransform(QTransform())


    def fillExtent(self, verticalOnly=False, horizontalOnly=False, useScene=False):
        """
        Scale the scene so the image fits the viewport. If there is no base image,
        we scale using the scene. The latter comes into play when we're not using
        QImageViewer as an image viewer and are simply plotting primitives in the
        scene.
        """

        self.resetView()
        try:
            #  determine the scaling factors
            if (self.imgPixmap.width() > 0) and (not useScene):
                vScaleRatio = float(self.width() - 2) / float(self.imgPixmap.width())
                hScaleRatio = float(self.height() - 2) / float(self.imgPixmap.height())
            else:
                vScaleRatio = float(self.width() - 2) / float(self.scene.width())
                hScaleRatio = float(self.height() - 2) / float(self.scene.height())

            #  apply the scaling
            if (verticalOnly):
                #  vertical only
                self.scale(hScaleRatio, hScaleRatio)
            elif (horizontalOnly):
                #  horizontal only
                self.scale(vScaleRatio, vScaleRatio)
            else:
                #  scale to fit both vertical and horizontal extents
                scaleFactor = min(vScaleRatio, hScaleRatio)
                self.scale(scaleFactor, scaleFactor)

        except:
            #  the scene is empty, do nothing
            pass


    def zoomToRegion(self, regionRect):
        """
        zoomToRegion zooms the view to the rectangular region defined by the provided
        QRectF.
        """

        #  center the view at the center of the region
        self.centerOnPoint(regionRect.center())

        #  zoom so that we will display the entire region while maintaining aspect ratio.
        vScaleRatio = float(self.width() - 2) / float(regionRect.width())
        hScaleRatio = float(self.height() - 2) / float(regionRect.height())
        self.scale(min(vScaleRatio, hScaleRatio), min(vScaleRatio, hScaleRatio))


    def removeAllItems(self):
        """
        Remove all items in the scene.
        """

        if self.sceneItems:
            #  clear all the marks in the scene
            self.scene.clear()

            #  add our background pixmap back to the scene
            self.imgPixmapItem = self.scene.addPixmap(self.imgPixmap)

            #  clear the scene items list
            self.sceneItems = []

            #  update the viewport
            self.viewport().update()


    def removeItem(self, item):
        """
            removeItem removes the specified item (mark) from the scene.
        """
        #  remove this item from our list
        if item in self.sceneItems:
            self.sceneItems.remove(item)

            #  remove it from the scene
            self.scene.removeItem(item)

        #  update the viewport
        self.viewport().update()


    def zoomToPoint(self, point, zoomLevel):
        """
        Zooms the view to a point on the image given a point and a zoom level (int).
        Point can be a list containing the [x,y] location or a Point2f object.
        """

        inClass = point.__class__.__name__.lower()
        #  check if we've been passed an OpenCV Point2f object
        if inClass == 'point2f':
            #  convert the Point2f object to a simple list
            point = QPointF(point.x, point.y)

        #  check if we've been passed a list
        elif inClass == 'list':
            #  convert the Point2f object to a simple list
            point = QPointF(point[0], point[1])

        #  set the zoom level
        zoomLevel = self.__getZoomScaler(zoomLevel)
        if (zoomLevel == 0):
            return

        #  set the zooming property to disable updating internal center point
        #  when the scroll bars are moved by the centerOn method.
        self.isZooming = True

        #  center on our point
        self.centerPoint = point
        self.centerOn(self.centerPoint)

        #  zoom
        QGraphicsView.scale(self, zoomLevel, zoomLevel)
        self.isZooming = False


    def scale(self, x, y, sticky=False):
        """
        scales the scene. Set sticky to True to set a scaling ratio that persists
        between subsequent calls.
        """

        if sticky:
            self.stickyScale = (x, y)
            QGraphicsView.scale(self, x, y)
        else:
            QGraphicsView.scale(self, x * self.stickyScale[0], y * self.stickyScale[1])


    def zoomToMark(self, mark, zoomLevel):
        """
        Zooms the view so it is centered on a marker given the marker object and a
        zoom level.
        """

        #  get the center of the mark
        point = mark.mapToScene(mark.pos())

        #  and zoom to it
        self.zoomToPoint(point, zoomLevel)


    def centerOnMark(self, mark):
        """
        Centers the view on the provided mark.
        """

        #  get the center of the mark
        point = mark.mapToScene(mark.pos())

        #  and center the view on it
        self.centerOnPoint(point)


    def centerOnPoint(self, point):
        """
        Centers the view on the provided point. Point can be a list containing the
        [x,y] location or a Point2f object.
        """

        inClass = point.__class__.__name__.lower()
        #  check if we've been passed an OpenCV Point2f object
        if inClass == 'point2f':
            #  convert the Point2f object to a simple list
            point = QPointF(point.x, point.y)

        #  check if we've been passed a list
        elif inClass == 'list':
            #  convert the Point2f object to a simple list
            point = QPointF(point[0], point[1])

        self.isZooming = True
        self.centerPoint = point
        self.centerOn(self.centerPoint)
        self.isZooming = False


    def enterEvent(self, ev):
        """
        Change the cursor when the mouse enters the widget
        """
        self.setFocus(Qt.MouseFocusReason)
        self.__pointerLeftWidget = False
        self.setCursor(self.defaultCursor)
        QGraphicsView.enterEvent(self, ev)


    def leaveEvent(self, ev):
        """
        Change the cursor when the mouse leaves the widget
        """
        if (self.panning):
            #  don't immediately change pointer if we're panning
            self.__pointerLeftWidget = True
        else:
            self.setCursor(Qt.ArrowCursor)
            QGraphicsView.leaveEvent(self, ev)
            self.currentKbKey = None


    def mouseReleaseEvent(self, ev):
        """
        mouseReleaseEvent is called when the user releases the mouse button. Here we handle
        any "built-in" behaviors such as panning or auto-rubberband selection. If we're
        currently not in a built-in event we simply emit a mouse-up signal.
        """

        #  handle the built mouse events first

        #  panning...
        if self.panning and (ev.button() == Qt.LeftButton):
            #  we're done panning
            self.leftBtnClicked = False
            self.setCursor(Qt.OpenHandCursor)
            self.lastPanPoint = QPoint()

        #  "auto" rubber banding...
        elif self.rubberBandKey and self.rubberBanding:

            #  end the rubber band selection
            rubberBandRect = self.endRubberBand().toRect()

            #  check if the user selected anything
            if (rubberBandRect):
                items = self.items(rubberBandRect)

                #  filter the selected items
                items = self.filterSelectedItems(items)

                #  If we're handling selections deal with the selection states of our marks
                if self.doSelections:

                    for item in self.selectedItems:
                        item.setSelected(False)
                    for item in items:
                        item.setSelected(True)
                        self.selectedItems = items

                #  call the emit method - we don't directly emit here in case a child class
                #  wants to transform the data before emitting it.
                self.emitRubberbandSelection(rubberBandRect, items)

        else:
            #  This event isn't handled by automatically - emit a release event
            clickLocation = self.mapToScene(ev.pos())

            #  do a "sloppy selection" and return all items that intersect our
            #  selection rectangle. The selection rectangle is set by calling
            #  the setSelectionRadius method.

            #  move our selection rectangle into place - depending on the size of
            #  the selection area, this may not be centered on the click location
            areaLoc = ev.pos() - self.selectionRadius
            self.selectionArea.moveTo(areaLoc)

            #  check if the user clicked on anything - this will return a list of
            #  items that intersect the selection rectangle.
            items = self.items(self.selectionArea)

            #  filter the selection so we only return marks or text not associated
            #  with a mark.
            items = self.filterSelectedItems(items)

            #  call the emit method - we don't directly emit here in case a child class
            #  wants to transform the data before emitting it.
            self.emitReleaseEvent(clickLocation, ev.button(), self.currentKbKey, items)


    def getSelectedItems(self):
        return self.selectedItems


    def filterSelectedItems(self, items):
        '''
        filterSelectedItems removes graphics items from the provided list that we want to
        hide from the parent application. This includes the displayed image and any text labels
        and graphics primitives that are associated with a mark. All other items are unfiltered.
        '''

        #  remove the background image from the list
        try:
            items.remove(self.imgPixmapItem)
        except:
            #  no background image to remove
            pass

        #  remove items that have their ItemIsSelectable flag unset
        nItems = len(items)
        for x in range(nItems):
            if ((items[x].flags().__int__() & QGraphicsItem.ItemIsSelectable) == 0):
                items[x] = None

        #  then remove all items that are None
        items[:] = [item for item in items if not (item==None)]

        return items


    def mousePressEvent(self, ev):
        """
        """

        #  get the click location in image coordinates
        clickLocation = self.mapToScene(ev.pos())
        self.lastClickPoint = ev.pos()

        #  handle the built mouse events first

        #  panning...
        if self.panning and (ev.button() == Qt.LeftButton):
            #  we're panning
            self.leftBtnClicked = True
            self.setCursor(Qt.ClosedHandCursor)
            self.lastPanPoint = ev.pos()

        #  rubber banding...
        elif self.rubberBandKey and (self.currentKbKey == self.rubberBandKey) and (ev.button() == Qt.LeftButton):
            #  start a rubber band selection box
            self.rubberBandObj = self.startRubberBand(clickLocation)

        else:
            #  This event isn't handled by automatically - emit a click event

            #  do a "sloppy selection" and return all items that intersect our
            #  selection rectangle. The selection rectangle is set by calling
            #  the setSelectionRadius method.

            #  move our selection rectangle into place - depending on the size of
            #  the selection area, this may not be centered on the click location
            areaLoc = ev.pos() - self.selectionRadius
            self.selectionArea.moveTo(areaLoc)

            #  check if the user clicked on anything - this will return a list of
            #  items that intersect the selection rectangle. This list includes eveything.
            items = self.items(self.selectionArea)

            #  filter the selection so we only return selectable items.
            items = self.filterSelectedItems(items)

            #  if we're automagically handling selections, do it here
            if self.doSelections:
                if (self.selectAddKey and not (self.currentKbKey == self.selectAddKey)) or not items:
                    #  we're NOT adding items to our current set of selected items
                    #  deselect any selected items and clear our list
                    for item in self.selectedItems:
                        item.setSelected(False)
                    self.selectedItems = []

                #  add the currently selected item or items
                for item in items:
                    if (not item.isSelected()):
                        item.setSelected(True)
                        self.selectedItems.append(item)
                #  was trying to implement "toggle" selection where if an item is currently
                #  selected and we click it again it is deselected but this isn't working
                #  and I have to leave it for now...
#                    else:
#                        item.setSelected(False)
#                        try:
#                            self.selectedItems.remove(item)
#                        except:
#                            pass


            #  call the emit method - we don't directly emit here in case a child class
            #  wants to transform the data before emitting it.
            self.emitPressEvent(clickLocation, ev.button(), self.currentKbKey, items)


    def mouseMoveEvent(self, ev):

        if self.rubberBanding:

            #  we're rubberbanding, update the rubberband object

            #  clamp the mouse position to the viewport
            p2 = QPoint()
            p2.setX(max(0, min(self.viewport().width(), ev.pos().x())))
            p2.setY(max(0, min(self.viewport().height(), ev.pos().y())))

            #  convert from viewport to scene(image) coordinates
            p2 = QPointF(self.mapToScene(p2))

            #  update the geometry - adjust vertex order based on relative location
            #  to ensure consistent vertex ordering (needed for labeling)
            rloc = p2 - self.rubberBandOrigin
            if (rloc.x() > 0 and rloc.y() > 0):
                self.rubberBandRect.setTopLeft(self.rubberBandOrigin)
                self.rubberBandRect.setBottomRight(p2)
            elif (rloc.x() < 0 and rloc.y() > 0):
                self.rubberBandRect.setTopLeft(QPointF(p2.x(),self.rubberBandOrigin.y()))
                self.rubberBandRect.setBottomRight(QPointF(self.rubberBandOrigin.x(),p2.y()))
            elif (rloc.x() >0 and rloc.y() < 0):
                self.rubberBandRect.setTopLeft(QPointF(self.rubberBandOrigin.x(),p2.y()))
                self.rubberBandRect.setBottomRight(QPointF(p2.x(),self.rubberBandOrigin.y()))
            else:
                self.rubberBandRect.setTopLeft(p2)
                self.rubberBandRect.setBottomRight(self.rubberBandOrigin)
            self.rubberBandObj.setGeometry(self.rubberBandRect)


        elif self.dimensionLine:
            #  update the dimension line

            #  clamp the mouse position to the viewport
            p2 = QPoint()
            p2.setX(max(0, min(self.viewport().width(), ev.pos().x())))
            p2.setY(max(0, min(self.viewport().height(), ev.pos().y())))

            #  convert from viewport to scene(image) coordinates
            p2 = QPointF(self.mapToScene(p2))

            #  update the end-point
            self.dimensionLine.setP2(p2)

        elif self.panning:
            #  we're panning - track the movement and set the center point
            if not self.lastPanPoint.isNull():
                #print("lastPan:"+str(self.mapToScene(self.lastPanPoint)) + "  thisPan:" +
                #        str(self.mapToScene(ev.pos())))
                delta = self.mapToScene(self.lastPanPoint) - self.mapToScene(ev.pos())
                #print("delta:"+str(delta))
                self.lastPanPoint = ev.pos()
                self.setCenterPoint(self.centerPoint + delta)

        else:
            #  if we're allowing the dragging of selected marks - move them
            draggedItems = []
            if (self.selectedItems):
                #  check if we're holding the left mouse button down
                if (ev.buttons() & Qt.LeftButton):
                    #  calculate the mouse delta

                    p2 = QPoint()
                    p2.setX(max(0, min(self.viewport().width(), ev.pos().x())))
                    p2.setY(max(0, min(self.viewport().height(), ev.pos().y())))

                    delta = self.mapToScene(self.lastClickPoint) - self.mapToScene(p2)
                    self.lastClickPoint = p2

                    #  move the selected marks - but only marks that are movable
                    draggedItems = []
                    for item in self.selectedItems:
                        if ((item.flags().__int__() & QGraphicsItem.ItemIsMovable) > 0):
                            item.moveBy(-delta.x(), -delta.y())
                            draggedItems.append(item)


            #  check if the user moused over anything
            areaLoc = ev.pos() #- self.selectionRadius
            self.selectionArea.moveTo(areaLoc)

            #  check if the user moused over anything - this will return a list of
            #  items that intersect the selection rectangle. This list includes eveything.
            items = self.items(self.selectionArea)

            #  filter the selection so we only return selectable items.
            items = self.filterSelectedItems(items)

            #  call the emit method - we don't directly emit here in case a child class
            #  wants to transform the data before emitting it.
            self.emitMouseMoveEvent(self.mapToScene(ev.pos()), self.currentKbKey, draggedItems, items)


    """
    The following four emit* methods can be overridden in child classes to first transform
    the pixel locations they emit by default to something that is context specific. An example
    would be emitting a time and range from QEchogramViewer instead of a pixel location.

    Note that you will then need to override various add* methods so you convert these values
    back to pixel values before calling the parent method.
    """

    def emitPressEvent(self, clickLocation, button, currentKbKey, items):
        """
        emitPressEvent emits the standard mousePressEvent signal. Override this method
        in your child class if you first want to transform your coordinates in some way before
        emitting them.
        """
        #  emit the mousePressEvent signal
        self.mousePress.emit(self, clickLocation, button, currentKbKey, items)


    def emitMouseMoveEvent(self, location, currentKbKey, draggedItems, items):
        """
        emitMouseMoveEvent emits the standard mouseMoveEvent signal. Override this method
        in your child class if you first want to transform your coordinates in some way before
        emitting them.
        """
        #  emit the mouseMoveEvent signal
        self.mouseMove.emit(self, location, currentKbKey, draggedItems, items)


    def emitReleaseEvent(self, clickLocation, button, currentKbKey, items):
        """
        emitReleaseEvent emits the standard mouseReleaseEvent signal. Override this method
        in your child class if you first want to transform your coordinates in some way before
        emitting them.
        """
        #  emit the mouseReleaseEvent signal
        self.mouseRelease.emit(self, clickLocation, button, currentKbKey, items)


    def emitRubberbandSelection(self, rubberBandRect, items):
        """
        emitRubberbandSelection emits the standard rubberBandSelection signal. Override this method
        in your child class if you first want to transform your coordinates in some way before
        emitting them.
        """
        #  emit the rubberband selection signal
        self.rubberBand.emit(self, rubberBandRect, items)


    def keyPressEvent(self, ev):
        """
        Event handler for keyboard key press events
        """

        self.currentKbKey = ev.key()

        if (ev.key() == self.panKey):
            #  enable Pan mode
            self.panning = True
            #  set the cursor to the hand to indicate pan/zoom mode
            if self.leftBtnClicked:
                self.setCursor(Qt.ClosedHandCursor)
            else:
                self.setCursor(Qt.OpenHandCursor)
        elif (ev.key() == self.selectAddKey):
            #  set the cursor to the arrow with "+"
            self.setCursor(Qt.DragCopyCursor)
        elif (ev.key() == self.zoomKey):
            #  enable zoom mode
            self.__zooming = True
        else:
            self.keyPress.emit(self, ev)


    def keyReleaseEvent(self, ev):
        """
        Event handler for keyboard key release events
        """
        self.currentKbKey = None

        if (ev.key() == self.panKey):
            #  disable Pan/Zoom mode
            self.panning = False
            if self.__pointerLeftWidget:
                #  we've left the widget - reset the cursor to the standard arrow
                self.setCursor(Qt.ArrowCursor)
            else:
                self.setCursor(self.defaultCursor)
        elif (ev.key() == self.selectAddKey):
            #  disable selection add mode
            if self.__pointerLeftWidget:
                #  we've left the widget - reset the cursor to the standard arrow
                self.setCursor(Qt.ArrowCursor)
            else:
                self.setCursor(self.defaultCursor)
        elif  (ev.key() == self.zoomKey):
            #  disable zoom mode
            self.__zooming = False
        else:
            self.keyRelease.emit(self, ev)



    def wheelEvent(self, ev):
        """
        Event handler for mouse wheel events. If autoWheelZoom is set we assume
        wheel events zoom. If it is set to false we emit the wheelEvent signal.
        """

        #  Check if we're in auto Zoom mode
        if self.__zooming:
            #  we're zooming
            if (ev.angleDelta().y() > 0):
                self.zoom(ev.pos(), 1)
            else:
                self.zoom(ev.pos(), -1)

        else:
            #  not zooming - pass wheel event on
            self.mouseWheel.emit(self, ev)


    def rotate(self, point, rotation):
        """
        rotate rotates the scene about the *center* of the view.
        """

        self.rotation = self.rotation + rotation

        #  get the point before the rotation
        ptBeforeScale = self.mapToScene(point)

        #  rotate the view
        QGraphicsView.translate(self, point.x(), point.y())
        QGraphicsView.rotate(self, rotation)
        QGraphicsView.translate(self, -point.x(), -point.y())

        #  counter rotate the selection point
        t = QTransform()
        t.rotate(-rotation)
        ptAfterScale = t.map(ptBeforeScale)

        #  calculate the offset and update
        offset = ptBeforeScale - ptAfterScale
        newCenter = self.centerPoint - offset
        self.setCenterPoint(newCenter)


    def zoom(self, point, zoomLevel):
        """
        Provides a smooth zoom for interactive mouse zooming. This method
        tracks both the view center and the given mouse pointer location
        anchoring the image under the mouse pointer.
        """

        #  get the point before the scale
        ptBeforeScale = self.mapToScene(point)

        #  set the zoom level
        zoomScalar = self.__getZoomScaler(zoomLevel)
        if (zoomScalar == 0):
            return

        #  scale the scene
        QGraphicsView.scale(self, zoomScalar, zoomScalar)

        #  get the point after the scale
        ptAfterScale = self.mapToScene(point)

        #  calculate the offset and update
        offset = ptAfterScale - ptBeforeScale
        newCenter = self.centerPoint - offset
        self.setCenterPoint(newCenter)


    def scrollContentsBy(self, x, y):
        """
        The scrollContentsBy method is overridden so that we can handle moving the
        current center point (area of interest) when the user manually scrolls the
        viewport.
        """

        if not (self.panning or self.__zooming or self.isSettingCtrPt):
            #  move the current center point if the user manually scrolls
            ptBeforeScale = self.mapToScene(self.centerPoint.toPoint())
            QGraphicsView.scrollContentsBy(self, x, y)
            ptAfterScale = self.mapToScene(self.centerPoint.toPoint())
            offset = ptBeforeScale - ptAfterScale
            self.centerPoint = self.centerPoint - offset
        else:
            #  we're already adjusting the center point when we zoom so just
            #  pass this on to the parent method
            QGraphicsView.scrollContentsBy(self, x, y)

        #  we have to manually update the viewport if we have HUD items so
        #  they draw properly.
        if self.hudItems:
            self.viewport().update()



    def addHudText(self, position, text, size=10, font='helvetica', italics=False, weight=-1,
                color=[0,0,0], alpha=255, halign='left', valign='top', normalized=True):
        """
        Add text to the scene given the text and position. The function returns
        the reference to the QGraphicsSimpleTextItem.

          position (QPointF) - The position of the text anchor point.
              text (string)  - The text to add to the scene.
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

        #  create a simpleTextItem based on the input options
        textItem = QIVHudText(position, text, self, size=size, font=font,
                              italics=italics, weight=weight, color=color, alpha=alpha,
                              halign=halign, valign=valign, normalized=normalized,
                              parent=self)

        self.hudItems.append(textItem)

        return textItem


    def removeHudItem(self, hudItem):
        """
        Removes a specified HUD graphics item from the view
        """

        #  SHOULD ADD EXCEPTION HANDLING
        try:
            self.hudItems.remove(hudItem)
        except:
            pass


    def removeAllHudItems(self):
        """
        removeAllHudItems removes all HUD elements from the view
        """
        self.hudItems = []


    def drawForeground(self, painter, rect):
        """
        drawForeground is called when drawing the scene and is responsible for
        painting the HUD elements.
        """
        if self.hudItems:
            hudPainter = QPainter(self.viewport())
            for item in self.hudItems:
                item.paint(hudPainter)
            hudPainter.end()


    def setCenterPoint(self, point):
        '''
        setCenterPoint sets the center point of the scene in the view. It's primary function
        is to constrain the setting of the center point such that when zooming near the
        edge of an image

        This method DOES NOT WORK WITH ROTATED SCENES. I haven't figured out the

        '''

        self.isSettingCtrPt = True

        #  clamp if we're not rotated
        if (self.rotation == 0):

            #  the visible area in scene units
            visibleArea = self.mapToScene(self.rect()).boundingRect()

            #  the size of the scene
            sceneBounds = self.sceneRect()

            #  determine the clamping bounding box
            boundX = visibleArea.width() / 2.0
            widthBound = [boundX, sceneBounds.width() - boundX]
            boundY =  visibleArea.height() / 2.0
            heightBound = [boundY, sceneBounds.height() - boundY]

            #  and clamp
            if (point.x() < widthBound[0]):
                point.setX(widthBound[0])
            if (point.x() > widthBound[1]):
                point.setX(widthBound[1])
            if (point.y() < heightBound[0]):
                point.setY(heightBound[0])
            if (point.y() > heightBound[1]):
                point.setY(heightBound[1])

        #  and update the center point
        self.centerPoint = point
        self.centerOn(self.centerPoint)

        self.isSettingCtrPt = False


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


    def __getZoomScaler(self,zoomLevel):
        """
        Calculate the zoom scaling factor, clamping if needed. Also maintains
        the internal zoom level value.
        """

        if (zoomLevel == 0):
            zoomLevel = 0
        elif (zoomLevel > 0):
            if (self.zoomLevel + zoomLevel <= self.maxZoom):
                #  we're not at maximum
                self.zoomLevel = self.zoomLevel + zoomLevel
            elif (self.zoomLevel < self.maxZoom):
                #  we'll exceed max zoom - clamp to max
                zoomLevel = self.maxZoom - self.zoomLevel
                self.zoomLevel = self.maxZoom
            else:
                #  we're at maximum zoom
                zoomLevel = 0
        else:
            if (self.zoomLevel + zoomLevel >= self.minZoom):
                #  we're not at min
                self.zoomLevel = self.zoomLevel + zoomLevel
            elif (self.zoomLevel > self.minZoom):
                #  we'll exceed min zoom - clamp to min
                zoomLevel = self.minZoom - self.zoomLevel
                self.zoomLevel = self.minZoom
            else:
                #  we're at minimum zoom
                zoomLevel = 0

        #  calculate the scaling factor
        if (zoomLevel != 0):
            zoomLevel = self.zoomFactor ** zoomLevel

        return zoomLevel


