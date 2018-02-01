
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui import ui_imageAdjustmentsDlg

class imageAdjustmentsDlg(QDialog, ui_imageAdjustmentsDlg.Ui_imageAdjustmentsDlg):

    def __init__(self, cameraName=None, parent=None):
        #  initialize the GUI
        super(imageAdjustmentsDlg, self).__init__(parent)
        self.setupUi(self)

        self.camera = ''
        self.initialState = None
        self.updatingState = False

        #  set the title if provided
        if (cameraName):
            self.camera = cameraName
            self.setWindowTitle("Image Adjustments:" + cameraName)

        #  set up signals for the brightness and contrast controls
        self.connect(self.gbBrightnessContrast, SIGNAL("clicked(bool)"), self.stateChanged)
        self.connect(self.bcAutomatic, SIGNAL("clicked()"), self.setBCMode)
        self.connect(self.bcClipLimit, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.bcManual, SIGNAL("clicked()"), self.setBCMode)
        self.connect(self.contrastSlider, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.brightnessSlider, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.pbBCReset, SIGNAL("clicked()"), self.resetBandC)

        #  set up signals for the color correction controls
        self.connect(self.gbColorCorrection, SIGNAL("clicked(bool)"), self.stateChanged)
        self.connect(self.ccSimpleBalance, SIGNAL("clicked()"), self.setCCMode)
        self.connect(self.ccSatLevel, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.ccAdaptive, SIGNAL("clicked()"), self.setCCMode)
        self.connect(self.ccClipLimit, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.ccManual, SIGNAL("clicked()"), self.setCCMode)
        self.connect(self.redSlider, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.greenSlider, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.blueSlider, SIGNAL("valueChanged(int)"), self.stateChanged)
        self.connect(self.pbColorReset, SIGNAL("clicked()"), self.resetColor)

        #  and any misc controls...
        self.connect(self.cbDenoise, SIGNAL("clicked()"), self.stateChanged)

        #  set up the apply/cancel signals
        self.connect(self.pbCancel, SIGNAL("clicked()"), self.cancelClicked)
        self.connect(self.pbApply, SIGNAL("clicked()"), self.applyClicked)

        #  set the initial GUI state
        self.setBCMode()
        self.setCCMode()


    def setBCMode(self):
        """
        setBCMode is called when one of the brightness/contrast radio buttons are clicked.
        It enables/disables GUI controls based on what is clicked and then emits the
        state changed signal.
        """

        #  enable/disable controls accordingly
        self.gbAutoBC.setEnabled(self.bcAutomatic.isChecked())
        self.gbManualBC.setEnabled(self.bcManual.isChecked())

        #  emit the state changed signal
        self.stateChanged()


    def setCCMode(self):
        """
        setCCMode is called when one of the coilor correction radio buttons are clicked.
        It enables/disables GUI controls based on what is clicked and then emits the
        state changed signal.
        """

        #  enable/disable controls accordingly
        self.gbAutoCC.setEnabled(self.ccSimpleBalance.isChecked())
        self.gbAdaptiveCC.setEnabled(self.ccAdaptive.isChecked())
        self.gbManualCC.setEnabled(self.ccManual.isChecked())

        #  emit the state changed signal
        self.stateChanged()


    def setName(self, name):
        """
        setName sets the window title name
        """
        self.camera = name
        self.setWindowTitle("Image Adjustments:" + name)


    def applyClicked(self):
        """
        applyClicked is called when the apply button is pressed.
        """
        self.accept()


    def enableColorCorrection(self, enable):
        if (enable):
            self.gbColorCorrection.setEnabled(True)
        else:
            self.gbColorCorrection.setEnabled(False)

    def stateChanged(self):
        """
        stateChanged is called when any control changes in the dialog. It emits the
        current state structure.
        """

        #  only emit state changes when we're not updating all of the settings at once
        if (not self.updatingState):
            self.emit(SIGNAL('imageAdjustments(PyQt_PyObject)'), self.getState())


    def resetBandC(self):
        """
        resetBandC resets the brightness and contrast settings to their default values.
        The default state is manual with no adjustments applied.
        """

        #  update the values
        self.updatingState = True
        self.contrastSlider.setValue(0)
        self.brightnessSlider.setValue(0)
        self.bcClipLimit.setValue(30)
        self.bcManual.setChecked(True)
        self.updatingState = False

        #  and emit the new state
        self.stateChanged()


    def resetColor(self):
        """
        resetColor resets the color correction settings to their default values.
        The default state is manual with no adjustments applied.
        """

        #  update the values
        self.updatingState = True
        self.redSlider.setValue(0)
        self.greenSlider.setValue(0)
        self.blueSlider.setValue(0)
        self.ccManual.setChecked(True)
        self.ccSatLevel.setValue(8)
        self.ccClipLimit.setValue(30)
        self.updatingState = False

        #  and emit the new state
        self.stateChanged()


    def setState(self, state):

        #  save the initial state so if the user cancels the dialog we can restore it
        self.initialState = self.getState()

        #  set the "updatingState" bool to ensure we don't emit any signals until
        #  we've set all of our properties
        self.updatingState = True

        #  update the contrast and brightness settings
        self.gbBrightnessContrast.setChecked(state['BrightnessContrastEnabled'])
        self.brightnessSlider.setValue(state['Brightness'])
        self.bcAutomatic.setChecked(state['AutoContrast'])
        self.bcClipLimit.setValue(int(round(state['AutoBCClipLimit'] * 10)))
        self.bcManual.setChecked(state['ManualContrast'])
        self.contrastSlider.setValue(int(round(state['Contrast'] * 100)))
        self.setBCMode()

        #  update the color settings
        self.gbColorCorrection.setChecked(state['ColorCorrectionEnabled'])
        self.ccSimpleBalance.setChecked(state['AutoLevels'])
        self.ccSatLevel.setValue(int(round(state['AutoLevelsSatLimit'] * 1000)))
        self.ccAdaptive.setChecked(state['AdaptiveEq'])
        self.ccClipLimit.setValue(int(round(state['AutoCCClipLimit'] * 10)))
        self.ccManual.setChecked(state['ManualColor'])
        self.redSlider.setValue(state['R'])
        self.greenSlider.setValue(state['G'])
        self.blueSlider.setValue(state['B'])
        self.setCCMode()

        #  and any misc settings
        self.cbDenoise.setChecked(state['Denoise'])

        #  now that we're done, unset the updating property
        self.updatingState = False

        #  and emit our state signal
        self.stateChanged()


    def getState(self):


        #  construct the state dictionary
        state = {'BrightnessContrastEnabled':self.gbBrightnessContrast.isChecked(),
                 'Brightness':self.brightnessSlider.value(),
                 'AutoContrast':self.bcAutomatic.isChecked(),
                 'AutoBCClipLimit':float(self.bcClipLimit.value()) / 10.,
                 'ManualContrast':self.bcManual.isChecked(),
                 'Contrast':float(self.contrastSlider.value()) / 100.,
                 'ColorCorrectionEnabled':self.gbColorCorrection.isChecked(),
                 'AutoLevels':self.ccSimpleBalance.isChecked(),
                 'AutoLevelsSatLimit':float(self.ccSatLevel.value()) / 1000.,
                 'AdaptiveEq':self.ccAdaptive.isChecked(),
                 'AutoCCClipLimit':float(self.ccClipLimit.value()) / 10.,
                 'ManualColor':self.ccManual.isChecked(),
                 'R':self.redSlider.value(),
                 'G':self.greenSlider.value(),
                 'B':self.blueSlider.value(),
                 'Denoise':self.cbDenoise.isChecked()
                 }

        return state


    def cancelClicked(self):
        #  restore the initial state of the dialog, this will also cause the imageAdjustments
        #  signal to be emitted which should restore the state of the image

        if (self.initialState):
            self.setState(self.initialState)
        self.reject()


if __name__ == "__main__":

    import sys
    app = QApplication(sys.argv)
    form = imageAdjustmentsDlg(cameraName='AB-1234GE_00_00_00_00_00_00')
    form.show()
    app.exec_()
