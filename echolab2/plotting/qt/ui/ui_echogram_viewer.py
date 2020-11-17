# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rick.towler\Work\AFSCGit\pyEcholab\echolab2\plotting\qt\ui\echogram_viewer.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_echogram_viewer(object):
    def setupUi(self, echogram_viewer):
        echogram_viewer.setObjectName("echogram_viewer")
        echogram_viewer.resize(1000, 600)
        echogram_viewer.setMinimumSize(QtCore.QSize(0, 0))
        echogram_viewer.setMaximumSize(QtCore.QSize(9999, 9999))
        self.centralwidget = QtWidgets.QWidget(echogram_viewer)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.QEchogramViewer = QEchogramViewer(self.centralwidget)
        self.QEchogramViewer.setMinimumSize(QtCore.QSize(400, 400))
        self.QEchogramViewer.setObjectName("QEchogramViewer")
        self.verticalLayout_4.addWidget(self.QEchogramViewer)
        echogram_viewer.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(echogram_viewer)
        self.statusBar.setObjectName("statusBar")
        echogram_viewer.setStatusBar(self.statusBar)
        self.actionLoad = QtWidgets.QAction(echogram_viewer)
        self.actionLoad.setObjectName("actionLoad")
        self.actionExit = QtWidgets.QAction(echogram_viewer)
        self.actionExit.setObjectName("actionExit")
        self.actionSet_EK60_Raw_data_path = QtWidgets.QAction(echogram_viewer)
        self.actionSet_EK60_Raw_data_path.setObjectName("actionSet_EK60_Raw_data_path")

        self.retranslateUi(echogram_viewer)
        QtCore.QMetaObject.connectSlotsByName(echogram_viewer)

    def retranslateUi(self, echogram_viewer):
        _translate = QtCore.QCoreApplication.translate
        echogram_viewer.setWindowTitle(_translate("echogram_viewer", "Qt Echogram Viewer"))
        self.actionLoad.setText(_translate("echogram_viewer", "Load Deployment..."))
        self.actionExit.setText(_translate("echogram_viewer", "Exit"))
        self.actionSet_EK60_Raw_data_path.setText(_translate("echogram_viewer", "Set Echogram properties"))
from ..QImageViewer.QEchogramViewer import QEchogramViewer
