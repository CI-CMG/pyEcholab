
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .ui import ui_imageAdjustmentsDlg_simple

class imageAdjustmentsDlg_simple(QDialog, ui_imageAdjustmentsDlg_simple.Ui_imageAdjustmentsDlg):

    imageAdjustments = pyqtSignal(object)

    def __init__(self, cameraName=None, parent=None):
        #  initialize the GUI
        super(imageAdjustmentsDlg_simple, self).__init__(parent)
        self.setupUi(self)

        self.camera = ''
        self.initialState = None
        self.updatingState = False

        #  set the title if provided
        if (cameraName):
            self.camera = cameraName
            self.setWindowTitle("Image Adjustments:" + cameraName)

        #  set up signals for the brightness and contrast controls
        self.gbBrightnessContrast.clicked.connect(self.stateChanged)
        self.bcAutomatic.clicked.connect(self.setBCMode)
        self.bcManual.clicked.connect(self.setBCMode)
        self.pbBCReset.clicked.connect(self.resetBandC)
        self.bcClipLimit.valueChanged[int].connect(self.stateChanged)
        self.contrastSlider.valueChanged[int].connect(self.stateChanged)
        self.brightnessSlider.valueChanged[int].connect(self.stateChanged)

        #  set up signals for the color correction controls
        self.gbColorCorrection.clicked.connect(self.stateChanged)
        self.pbColorReset.clicked.connect(self.resetColor)
        self.cbAWB.clicked.connect(self.stateChanged)
        self.ccManual.clicked.connect(self.setCCMode)
        self.redSlider.valueChanged[int].connect(self.stateChanged)
        self.greenSlider.valueChanged[int].connect(self.stateChanged)
        self.blueSlider.valueChanged[int].connect(self.stateChanged)

        #  set up the apply/cancel signals
        self.pbCancel.clicked.connect(self.cancelClicked)
        self.pbApply.clicked.connect(self.applyClicked)

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
        setCCMode is called when one of the color correction radio buttons are clicked.
        It enables/disables GUI controls based on what is clicked and then emits the
        state changed signal.
        """

        #  enable/disable controls accordingly
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
             self.imageAdjustments.emit(self.getState())


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
        self.updatingState = False

        #  and emit the new state
        self.stateChanged()


    def setState(self, state):
        """
        setState sets the state of our GUI elements given a state dictionary
        """

        #  save the initial state so if the user cancels the dialog we can restore it
        self.initialState = self.getState()

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
        self.cbAWB.setChecked(state['AutoWhiteBalance'])
        self.ccManual.setChecked(state['ManualColor'])
        self.redSlider.setValue(state['R'])
        self.greenSlider.setValue(state['G'])
        self.blueSlider.setValue(state['B'])
        self.setCCMode()

        self.updatingState = False

        #  and emit our state signal
        self.stateChanged()


    def getState(self):
        """
        getState creates a dict containing the states of our dialog elements.
        Note that we still maintain the additional fields used by the "non simple"
        version of this dialog for compatibility reasons.
        """

        #  construct the state dictionary
        state = {'BrightnessContrastEnabled':self.gbBrightnessContrast.isChecked(),
                 'Brightness':self.brightnessSlider.value(),
                 'AutoContrast':self.bcAutomatic.isChecked(),
                 'AutoBCClipLimit':float(self.bcClipLimit.value()) / 10.,
                 'ManualContrast':self.bcManual.isChecked(),
                 'Contrast':float(self.contrastSlider.value()) / 100.,
                 'ColorCorrectionEnabled':self.gbColorCorrection.isChecked(),
                 'AutoWhiteBalance':self.cbAWB.isChecked(),
                 'AutoLevels':False,
                 'AutoLevelsSatLimit':0.006,
                 'AdaptiveEq':False,
                 'AutoCCClipLimit':3.,
                 'ManualColor':self.ccManual.isChecked(),
                 'R':self.redSlider.value(),
                 'G':self.greenSlider.value(),
                 'B':self.blueSlider.value()
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
