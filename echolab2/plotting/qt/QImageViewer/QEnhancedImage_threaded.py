

import os
import cv2
import numpy as np
import qimage2ndarray
from PyQt4 import QtGui
from PyQt4.QtCore import *

class QEnhancedImage(QObject):

    def __init__(self, maxQueued=3):

        super(QEnhancedImage, self).__init__()

        #  define the default public properties
        self.sourceData = None
        self.enhancedData = None
        self.imageData = None
        self.enableBrightnessContrast = False
        self.brightness = 0.0
        self.autoContrast = False
        self.autoContrastTileSize = 31
        self.autoContrastClipLimit = 3.0
        self.manualContrast = True
        self.contrast = 0.0
        self.enableColorCorrection = False
        self.autoWhiteBalance = False
        self.autoLevelsColorCorrection = False
        self.autoLevelsSaturationLimit = 0.01
        self.adaptiveColorCorrection = False
        self.adaptiveColorTileSize = 31
        self.adaptiveColorClipLimit = 3.0
        self.manualColor = True
        self.colorCorrection = [0.0,0.0,0.0]
        self.isColor = False
        self.transform = QtGui.QMatrix()
        self.enhancementsEnabled = False
        self.subsampleIdx = None
        self.maxQueued = maxQueued
        self.queuedImages = []
        self.contrastCLAHE = None
        self.colorCLAHE = None


    def startProcessing(self):

        print("NUNYA")

        #  create the Contrast Limited Adaptive Histogram Equalization (CLAHE) objects
        self.contrastCLAHE = cv2.createCLAHE(clipLimit=self.autoContrastClipLimit,
                tileGridSize=(self.autoContrastTileSize, self.autoContrastTileSize ))
        self.colorCLAHE = cv2.createCLAHE(clipLimit=self.adaptiveColorClipLimit,
                tileGridSize=(self.adaptiveColorTileSize,self.adaptiveColorTileSize))

        #  start a timer event to load the help image
        self.queueTimer = QTimer(self)
        self.connect(self.queueTimer, SIGNAL("timeout()"), self.processQueue)
        self.queueTimer.start(10)


    def stopProcessing(self):

        self.queueTimer.stop()
        self.contrastCLAHE = None
        self.colorCLAHE = None
        self.queuedImages = []

        self.emit(SIGNAL("finished"))


    def processQueue(self):
        """
        slot called to load a new image.

        type can be:
            'file'
            'qpixmap'
            'qimage'
            'mat'
        """

        if (len(self.queuedImages) > 0):

            image, type = self.queuedImages.pop(0)

            type = str(type).lower()
            if (type == 'file'):
                self.loadFile(image)
            elif (type == 'qpixmap'):
                self.fromQPixmap(image)
            elif (type == 'qimage'):
                self.fromQImage(image)
            elif (type == 'mat'):
                self.fromMat(image)
            else:
                pass


    def loadImage(self, image, type):

        #  trim our queue if required
        if ((self.maxQueued > 0) and (len(self.queuedImages) > self.maxQueued)):
            self.queuedImages.pop(0)

        #  add this image to the queue to process
        self.queuedImages.append([image, type])


    def loadFile(self, filename):
        """
        read an image from disk using OpenCv
        """
        #  unset the imageData property
        self.imageData = None

        #  read the image data into our "source" array which stores the original unmodified data
        filename = os.path.normpath(str(filename))
        self.sourceData = cv2.imread(str(filename), cv2.IMREAD_UNCHANGED)

        try:
            #  determine if this is a color or mono image
            if (len(self.sourceData.shape) == 3):
                self.isColor = True
            else:
                self.isColor = False

        except:
            self.emit(SIGNAL("imageError"), 'Unable to load ' + str(filename))

        #  generate our pixmap of this image
        self.updateImage()


    def fromQPixmap(self, pixmap):
        """
        Set the image to the provided QPixmap
        """

        #  convert to a QImage and then call fromQImage
        self.fromQImage(pixmap.toImage())

        #  the call to fromQImage will update the image so we don't need to do that here


    def fromQImage(self, image):
        """
        Set the image to the provided QImage
        """
        self.imageData = None
        self.sourceData = qimage2ndarray.byte_view(image)

        #  determine if this is a color or mono image
        if (len(self.sourceData.shape) == 3):
            self.isColor = True
        else:
            self.isColor = False

        #  generate our pixmap of this image
        self.updateImage()


    def fromMat(self, imageData, normalize=False):
        """
        Set the image based on data from a numpy matrix. The first dimension of the
        maxtrix represents the vertical image axis; the optional third dimension is
        supposed to contain 1-4 channels
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
        #  create an image from the provided numpy array
        image = qimage2ndarray.array2qimage(imageData, normalize=normalize)

        #  convert it back to a numpy array in a form we're comfortable with
        self.fromQImage(image)

        #  the call to fromQImage will update the image so we don't need to do that here


    def setSubsampleRect(self, qrect, alpha=50):
        '''
        setSubsampleRect accepts a QRect that defines an area of the image that will
        have the opacity (alpha) set to 255 (fully opaque). The opacity for the rest
        of the image will be set to the value specified by the "alpha" keyword.

        Call the method passing None for the QRect to disable this.

        This method has been used to only show portions of an image to an analyst when
        target density is high and the analyst is only sampling a portion of the image.
        '''

        #  set the alpha value used for the areas on non-interest
        self.subsampleAlpha = np.clip(int(alpha), 0, 255)

        #  make sure we've been passed a QRect object
        if (qrect.__class__.__name__.lower() == 'qrect'):
            #  set the subsampling indices
            self.subsampleIdx = [qrect.topLeft().y(),
                                 qrect.bottomLeft().y(),
                                 qrect.topLeft().x(),
                                 qrect.topRight().x()]
        else:
            self.subsampleIdx = None

        #  reset the imageData property to force processing
        self.imageData = None


    def setContrast(self, contrast):

        if (contrast < 0):
            self.contrast = 0.0
        else:
            self.contrast = float(contrast)
        self.imageData = None


    def setBrightness(self, brightness):

        self.brightness = float(brightness)
        self.imageData = None


    def setColorCorrection(self, R=0.0, G=0.0, B=0.0):

        #  store color correction values as BGR
        self.colorCorrection = [float(B), float(G), float(R)]
        self.imageData = None


    def setAdaptiveParameters(self, clipLimit=1.0, tileSize=(16,16)):
        """
        creates a new Contrast Limited Adaptive Histogram Equalization (CLAHE)
        object with the given clip limit and tile size. CLAHE is used for
        histogram equilization of the image.
        """
        self.CLAHE = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileSize)


    def setParameters(self, params):
        """
        setParameters updates the internal color correction parameters from the parameter
        structure returned from the GUI image adjustments dialog.
        """

        self.enableBrightnessContrast = params['BrightnessContrastEnabled']
        self.brightness = params['Brightness']
        self.autoContrast = params['AutoContrast']

        if (params['AutoBCClipLimit'] != self.autoContrastClipLimit):
                #  only update these parameters on change
                self.autoContrastClipLimit = params['AutoBCClipLimit']

                #  create a new CLAHE object with these parms
                self.contrastCLAHE = cv2.createCLAHE(clipLimit=self.autoContrastClipLimit,
                    tileGridSize=(self.autoContrastTileSize, self.autoContrastTileSize ))

        self.manualContrast = params['ManualContrast']
        self.contrast = params['Contrast']
        self.enableColorCorrection = params['ColorCorrectionEnabled']
        #  white balance is a new parameter so handle cases where we open old deployments without the key
        if ('AutoWhiteBalance' in params.keys()):
            self.autoWhiteBalance = params['AutoWhiteBalance']
        else:
            self.autoWhiteBalance = params['AutoLevels']
        self.autoLevelsColorCorrection = params['AutoLevels']
        self.autoLevelsSaturationLimit = params['AutoLevelsSatLimit']
        self.adaptiveColorCorrection = params['AdaptiveEq']

        if (params['AutoCCClipLimit'] != self.adaptiveColorClipLimit):
                #  only update these parameters on change
                self.adaptiveColorClipLimit = params['AutoCCClipLimit']

                #  create a new CLAHE object with these parms
                self.colorCLAHE = cv2.createCLAHE(clipLimit=self.adaptiveColorClipLimit,
                tileGridSize=(self.adaptiveColorTileSize,self.adaptiveColorTileSize))

        self.manualColor = params['ManualColor']
        self.colorCorrection = [float(params['B']),float(params['G']),float(params['R'])]

        #  lastly set the enhancementsEnabled flag
        self.enhancementsEnabled = self.enableBrightnessContrast or self.enableColorCorrection

        #  assume that something has changed and set imageData to None to force an update
        self.imageData = None


    def getParameters(self):
        """
        getParameters  returns a dict containing all of the adjustment parameters.
        This is primarily used to save the object's state and/or populate the
        GUI control panel
        """

        params = {}

        params['BrightnessContrastEnabled'] = self.enableBrightnessContrast
        params['Brightness'] = self.brightness
        params['AutoContrast'] = self.autoContrast
        params['AutoBCClipLimit'] = self.autoContrastClipLimit
        params['ManualContrast'] = self.manualContrast
        params['Contrast'] = self.contrast
        params['ColorCorrectionEnabled'] = self.enableColorCorrection
        params['AutoWhiteBalance'] = self.autoWhiteBalance
        params['AutoLevels'] = self.autoLevelsColorCorrection
        params['AutoLevelsSatLimit'] = self.autoLevelsSaturationLimit
        params['AdaptiveEq'] = self.adaptiveColorCorrection
        params['AutoCCTileSize'] = self.adaptiveColorTileSize
        params['AutoCCClipLimit'] = self.adaptiveColorClipLimit
        params['ManualColor'] = self.manualColor
        params['B'] = self.colorCorrection[0]
        params['G'] = self.colorCorrection[1]
        params['R'] = self.colorCorrection[2]

        return params


    def updateImage(self):
        '''
        updateImage creates a copy of the current image, applies corrections
        (if any) and then converts the image to a QImage and emits it. The receiver
        usually will convert this to a pixmap for display.
        '''

        #  check if we have already processed this data
        if (self.imageData is None):
            #  first make sure we have some data to process
            if (self.sourceData is None):
                return

            #  get our source data
            self.imageData = np.copy(self.sourceData)

            #  for backward compatibility, set the enhancedData property - we used to
            #  not store this data by default but we do now so just get a reference to it
            self.enhancedData = self.imageData

            #  apply contrast and brightness corrections
            if (self.enableBrightnessContrast):
                if (self.manualContrast):
                    #  if manual corrections are applied just set the state var because these
                    #  are done at the same time manual color corrections are done
                    doManualCorrections = True
                else:
                    self.imageData = self.doAutoContrast(self.imageData)
                    doManualCorrections = False

                #  check if we need to apply brightness
                if (self.brightness != 0):
                    doManualCorrections = True
            else:
                doManualCorrections = False

            #  apply color corrections
            if (self.enableColorCorrection and self.isColor):
                if (self.autoWhiteBalance):
                    self.imageData = self.white_balance(self.imageData)

                if (self.manualColor):
                    #  if manual corrections are applied just set the state var because these
                    #  are done at the same time manual brightness and contrast are done
                    doManualCorrections = True
                else:
                    self.imageData = self.doAutoColorBalance(self.imageData)

            #  if needed, apply the "manual" corrections
            if (doManualCorrections):
                self.imageData = self.applyManualCorrections(self.imageData)

            #  apply subsampling mask if needed
            if (self.subsampleIdx):
                self.imageData = self.applySubsamplingRect(self.imageData)

        #  convert our image data into a QImage - swap the B&R channels so the OpenCV BGR data
        #  is converted to RGB for display by Qt.
        qimage = qimage2ndarray.array2qimage(self.imageData).rgbSwapped()

        #  transform the image if needed
        if (not self.transform.isIdentity()):
            qimage = qimage.transformed(self.transform)

        #  emit the processed image data as a QImage
        self.emit(SIGNAL("imageData"), qimage)


    def applySubsamplingRect(self, imageData):
        '''
        applySubsamplingRect modifies the alpha value of the image so that pixels *not*
        in the specified subsampling rectangle are made transparent to de-emphasize them.
        '''

        #  get the image dimensions
        dims = imageData.shape

        #  check if we need to create an alpha channel
        if (self.isColor):
            if (dims[2] == 3):
                #  image doesn't have an alpha cannel - add it
                imageData = np.dstack((imageData, np.full((dims[0],dims[1]), self.subsampleAlpha,
                        imageData.dtype)))
            #  and set the alpha channel index
            d = 3
        else:
            if (imageData.ndim == 2):
                #  image doesn't have an alpha cannel - add it
                imageData = np.dstack((imageData, np.full(dims, self.subsampleAlpha,
                        imageData.dtype)))
            #  and set the alpha channel index
            d = 1

        #  clamp the subsampled indices to the image size
        ystart = max(0, min(dims[0], self.subsampleIdx[0]))
        yend = max(0, min(dims[0], self.subsampleIdx[1]))
        xstart = max(0, min(dims[1], self.subsampleIdx[2]))
        xend = max(0, min(dims[1], self.subsampleIdx[3]))

        #  and set the opacity for our subsampled region
        imageData[ystart:yend, xstart:xend, d] = 255

        return imageData


    def doAutoColorBalance(self, imageData):
        """
        automagically balance color by applying histogram equilization to the
        image channels.
        """

        #  apply suto white balance
        if (self.autoLevelsColorCorrection):

            #  perform "simplest color balance" adapted from:
            #  http://web.stanford.edu/~sujason/ColorBalancing/simplestcb.html

            halfSatLimit = self.autoLevelsSaturationLimit / 2.0
            tempChan = np.zeros(shape=imageData[:,:,0].shape)

            #  loop through each image channel
            for i in range(3):
                #  flatten out the image and sort all values from low to high
                flat = imageData[:,:,i].reshape(1,imageData[:,:,i].size)
                flat = cv2.sort(flat, cv2.SORT_EVERY_ROW + cv2.SORT_ASCENDING)

                #  determine the bounds of our saturation limit in intensity values
                lowBound = flat[0,int(np.floor(flat.shape[1] * halfSatLimit))]
                highBound = flat[0,int(np.ceil(flat.shape[1] * (1.0 - halfSatLimit)))]

                #  set all pixels below/above those limits to those bounds
                imageData[:,:,i][imageData[:,:,i] < lowBound] = lowBound
                imageData[:,:,i][imageData[:,:,i] > highBound] = highBound

                #  now normalize the channel
                tempChan = cv2.normalize(imageData[:,:,i], tempChan, 0, 255, cv2.NORM_MINMAX)

                #  and replace the existing data
                imageData[:,:,i] = tempChan

        elif (self.adaptiveColorCorrection):

            #  perform adaptive auto color using Contrast Limited Adaptive Histogram Equalization
            imageData[:,:,0] = self.colorCLAHE.apply(imageData[:,:,0])
            imageData[:,:,1] = self.colorCLAHE.apply(imageData[:,:,1])
            imageData[:,:,2] = self.colorCLAHE.apply(imageData[:,:,2])

        return imageData


    def doAutoContrast(self, imageData):
        """
        doAutoContrast perform adaptive auto contrast using Contrast Limited Adaptive
        Histogram Equalization
        """

        if (self.isColor):
            #  convert to LAB and normalize the Luminance channel
            imageData = cv2.cvtColor(imageData, cv2.COLOR_BGR2LAB)
            imageData[:,:,0] = self.contrastCLAHE.apply(imageData[:,:,0])
            #  and convert back to BGR
            imageData = cv2.cvtColor(imageData, cv2.COLOR_LAB2BGR)
        else:
            #  for mono images simply normalize the single channel
            imageData[:,:] = self.contrastCLAHE.apply(imageData[:,:])

        return imageData


    def applyManualCorrections(self, imageData):

        #  convert image array to float
        imageData = imageData.astype(float)

        #  apply contrast ajustment
        if (self.manualContrast and self.contrast != 0.0):
            luminance = np.mean(imageData)
            contrastImage = (imageData - luminance) * self.contrast
            imageData = imageData + contrastImage

        #  and brightness
        if (self.brightness != 0):
            imageData = imageData + self.brightness

        #  and color correction
        if (self.isColor and self.manualColor and any(self.colorCorrection)):
            #  apply corrections to individual color channels
            for i in range(3):
                if (self.colorCorrection[i] != 0):
                    imageData[:,:,i] = imageData[:,:,i] + self.colorCorrection[i]

        #  clamp the values
        np.clip(imageData, 0, 255, imageData)

        #  convert back to int
        imageData = imageData.astype(int)

        return imageData


    def white_balance(self, imageData):
        '''
        Automatic white balance from:
        https://stackoverflow.com/questions/46390779/automatic-white-balancing-with-grayworld-assumption
        '''

        result = cv2.cvtColor(imageData, cv2.COLOR_BGR2LAB)
        avg_a = np.average(result[:, :, 1])
        avg_b = np.average(result[:, :, 2])
        result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
        result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
        imageData = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)

        return imageData


    def denoiseImage(self, imageData):

        if (self.isColor):
            imageData = cv2.fastNlMeansDenoisingColored(imageData,None,3,3,7,21)
        else:
            imageData = cv2.fastNlMeansDenoising(imageData,None,3,7,21)

        return imageData
