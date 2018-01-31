# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '\\AKC0SS-N086\RACE_Users\rick.towler\My Documents\AFSCGit\pyEcholab2_CI-CMG\echolab2\plotting\qt\ui\echogram_viewer.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_echogram_viewer(object):
    def setupUi(self, echogram_viewer):
        echogram_viewer.setObjectName(_fromUtf8("echogram_viewer"))
        echogram_viewer.resize(1000, 600)
        echogram_viewer.setMinimumSize(QtCore.QSize(0, 0))
        echogram_viewer.setMaximumSize(QtCore.QSize(9999, 9999))
        self.centralwidget = QtGui.QWidget(echogram_viewer)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.QEchogramViewer = QEchogramViewer(self.centralwidget)
        self.QEchogramViewer.setMinimumSize(QtCore.QSize(400, 400))
        self.QEchogramViewer.setObjectName(_fromUtf8("QEchogramViewer"))
        self.verticalLayout_4.addWidget(self.QEchogramViewer)
        echogram_viewer.setCentralWidget(self.centralwidget)
        self.statusBar = QtGui.QStatusBar(echogram_viewer)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        echogram_viewer.setStatusBar(self.statusBar)
        self.actionLoad = QtGui.QAction(echogram_viewer)
        self.actionLoad.setObjectName(_fromUtf8("actionLoad"))
        self.actionExit = QtGui.QAction(echogram_viewer)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionSet_EK60_Raw_data_path = QtGui.QAction(echogram_viewer)
        self.actionSet_EK60_Raw_data_path.setObjectName(_fromUtf8("actionSet_EK60_Raw_data_path"))

        self.retranslateUi(echogram_viewer)
        QtCore.QMetaObject.connectSlotsByName(echogram_viewer)

    def retranslateUi(self, echogram_viewer):
        echogram_viewer.setWindowTitle(_translate("echogram_viewer", "Qt Echogram Viewer", None))
        self.actionLoad.setText(_translate("echogram_viewer", "Load Deployment...", None))
        self.actionExit.setText(_translate("echogram_viewer", "Exit", None))
        self.actionSet_EK60_Raw_data_path.setText(_translate("echogram_viewer", "Set Echogram properties", None))

from echolab2.plotting.qt.QImageViewer.QEchogramViewer import QEchogramViewer
