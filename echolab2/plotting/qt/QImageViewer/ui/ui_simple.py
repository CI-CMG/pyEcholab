# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\rick.towler\Work\AFSCGit\SurveyApps\MaceFunctions3\QImageViewer\example\ui\simple.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_simple(object):
    def setupUi(self, simple):
        simple.setObjectName("simple")
        simple.resize(919, 627)
        self.centralwidget = QtWidgets.QWidget(simple)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.ImageViewLeft = QImageViewer(self.centralwidget)
        self.ImageViewLeft.setObjectName("ImageViewLeft")
        self.horizontalLayout.addWidget(self.ImageViewLeft)
        self.ImageViewRight = QImageViewer(self.centralwidget)
        self.ImageViewRight.setObjectName("ImageViewRight")
        self.horizontalLayout.addWidget(self.ImageViewRight)
        simple.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(simple)
        self.statusbar.setObjectName("statusbar")
        simple.setStatusBar(self.statusbar)

        self.retranslateUi(simple)
        QtCore.QMetaObject.connectSlotsByName(simple)

    def retranslateUi(self, simple):
        _translate = QtCore.QCoreApplication.translate
        simple.setWindowTitle(_translate("simple", "Simple Zoom Example"))
#from QImageViewer.QImageViewer import QImageViewer
from QImageViewer import QImageViewer
