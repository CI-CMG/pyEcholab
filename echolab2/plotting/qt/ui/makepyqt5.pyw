#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import os
import platform
import stat
import sys

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


__version__ = "2.0.0"


class OptionsForm(QDialog):

    def __init__(self, parent=None):
        super(OptionsForm, self).__init__(parent)

        settings = QSettings('afsc.noaa.gov','makepyqt5')
        pyuic5Label = QLabel("pyuic5")
        self.pyuic5Label = QLabel(settings.value("pyuic5", PYUIC5))
        self.pyuic5Label.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        pyuic5Button = QPushButton("py&uic5...")
        pyrcc5Label = QLabel("pyrcc5")
        self.pyrcc5Label = QLabel(settings.value("pyrcc5", PYRCC5))
        self.pyrcc5Label.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        pyrcc5Button = QPushButton("pyr&cc5...")
        pylupdate5Label = QLabel("pylupdate5")
        self.pylupdate5Label = QLabel(settings.value("pylupdate5",PYLUPDATE5))
        self.pylupdate5Label.setFrameStyle(QFrame.StyledPanel|
                                           QFrame.Sunken)
        pylupdate5Button = QPushButton("py&lupdate5...")
        lreleaseLabel = QLabel("lrelease")
        self.lreleaseLabel = QLabel(settings.value("lrelease","lrelease"))
        self.lreleaseLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        lreleaseButton = QPushButton("l&release...")

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|
                                     QDialogButtonBox.Cancel)

        layout = QGridLayout()
        layout.addWidget(pyuic5Label, 0, 0)
        layout.addWidget(self.pyuic5Label, 0, 1)
        layout.addWidget(pyuic5Button, 0, 2)
        layout.addWidget(pyrcc5Label, 1, 0)
        layout.addWidget(self.pyrcc5Label, 1, 1)
        layout.addWidget(pyrcc5Button, 1, 2)
        layout.addWidget(pylupdate5Label, 2, 0)
        layout.addWidget(self.pylupdate5Label, 2, 1)
        layout.addWidget(pylupdate5Button, 2, 2)
        layout.addWidget(lreleaseLabel, 3, 0)
        layout.addWidget(self.lreleaseLabel, 3, 1)
        layout.addWidget(lreleaseButton, 3, 2)
        layout.addWidget(buttonBox, 4, 0, 1, 3)
        self.setLayout(layout)

        pyuic5Button.clicked.connect(lambda: self.setPath("pyuic5"))
        pyrcc5Button.clicked.connect(lambda: self.setPath("pyrcc5"))
        pylupdate5Button.clicked.connect(lambda: self.setPath("pylupdate5"))
        lreleaseButton.clicked.connect(lambda: self.setPath("lrelease"))
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.setWindowTitle("Make PyQt - Tool Paths")


    def accept(self):
        settings = QSettings('afsc.noaa.gov','makepyqt5')
        settings.setValue("pyuic5", self.pyuic5Label.text())
        settings.setValue("pyrcc5", self.pyrcc5Label.text())
        settings.setValue("pylupdate5",self.pylupdate5Label.text())
        settings.setValue("lrelease", self.lreleaseLabel.text())
        QDialog.accept(self)


    def setPath(self, tool):
        if tool == "pyuic5":
            label = self.pyuic5Label
        elif tool == "pyrcc5":
            label = self.pyrcc5Label
        elif tool == "pylupdate5":
            label = self.pylupdate5Label
        elif tool == "lrelease":
            label = self.lreleaseLabel
        path = QFileDialog.getOpenFileName(self, "Make PyQt - Set Tool Path", label.text())
        if path:
            label.setText(QDir.toNativeSeparators(path[0]))


class Form(QMainWindow):

    def __init__(self):
        super(Form, self).__init__(None)

        pathLabel = QLabel("Path:")
        self.pathLabel = QLabel(sys.argv[1] \
                if len(sys.argv) > 1 and os.access(sys.argv[1], os.F_OK) \
                else os.getcwd())
        self.pathLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.pathLabel.setToolTip("The relative path; all actions will "
                "take place here,<br>and in this path's subdirectories "
                "if the Recurse checkbox is checked")
        self.pathButton = QPushButton("&Path...")
        self.pathButton.setToolTip(self.pathLabel.toolTip().replace(
                "The", "Sets the"))
        self.recurseCheckBox = QCheckBox("&Recurse")
        self.recurseCheckBox.setToolTip("Clean or build all the files "
                "in the path directory,<br>and all its subdirectories, "
                "as deep as they go.")
        self.transCheckBox = QCheckBox("&Translate")
        self.transCheckBox.setToolTip("Runs <b>PYLUPDATE5</b> on all "
                "<tt>.py</tt> and <tt>.pyw</tt> files in conjunction "
                "with each <tt>.ts</tt> file.<br>Then runs "
                "<b>lrelease</b> on all <tt>.ts</tt> files to produce "
                "corresponding <tt>.qm</tt> files.<br>The "
                "<tt>.ts</tt> files must have been created initially by "
                "running <b>PYLUPDATE5</b><br>directly on a <tt>.py</tt> "
                "or <tt>.pyw</tt> file using the <tt>-ts</tt> option.")
        self.debugCheckBox = QCheckBox("&Dry Run")
        self.debugCheckBox.setToolTip("Shows the actions that would "
                "take place but does not do them.")
        self.logBrowser = QTextBrowser()
        self.logBrowser.setLineWrapMode(QTextEdit.NoWrap)
        self.buttonBox = QDialogButtonBox()
        menu = QMenu(self)
        toolsAction = menu.addAction("&Tool paths...")
        aboutAction = menu.addAction("&About")
        moreButton = self.buttonBox.addButton("&More",
                QDialogButtonBox.ActionRole)
        moreButton.setMenu(menu)
        moreButton.setToolTip("Use <b>More-&gt;Tool paths</b> to set the "
                "paths to the tools if they are not found by default")
        self.buildButton = self.buttonBox.addButton("&Build",
                QDialogButtonBox.ActionRole)
        self.buildButton.setToolTip("Runs <b>PYUIC5</b> on all "
                "<tt>.ui</tt> "
                "files and <b>PYRCC5</b> on all <tt>.qrc</tt> files "
                "that are out-of-date.<br>Also runs <b>PYLUPDATE5</b> "
                "and <b>lrelease</b> if the Translate checkbox is "
                "checked.")
        self.cleanButton = self.buttonBox.addButton("&Clean",
                QDialogButtonBox.ActionRole)
        self.cleanButton.setToolTip("Deletes all <tt>.py</tt> files that "
                "were generated from <tt>.ui</tt> and <tt>.qrc</tt> "
                "files,<br>i.e., all files matching <tt>qrc_*.py</tt> "
                " and <tt>ui_*.py.")
        quitButton = self.buttonBox.addButton("&Quit",
                QDialogButtonBox.RejectRole)

        topLayout = QHBoxLayout()
        topLayout.addWidget(pathLabel)
        topLayout.addWidget(self.pathLabel, 1)
        topLayout.addWidget(self.pathButton)
        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.recurseCheckBox)
        bottomLayout.addWidget(self.transCheckBox)
        bottomLayout.addWidget(self.debugCheckBox)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self.buttonBox)
        layout = QVBoxLayout()
        layout.addLayout(topLayout)
        layout.addWidget(self.logBrowser)
        layout.addLayout(bottomLayout)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        aboutAction.triggered.connect(self.about)
        toolsAction.triggered.connect(self.setToolPaths)
        self.pathButton.clicked.connect(self.setPath)
        self.buildButton.clicked.connect(self.build)
        self.cleanButton.clicked.connect(self.clean)
        quitButton.clicked.connect(self.close)

        self.setWindowTitle("Make PyQt")


    def about(self):
        QMessageBox.about(self, "About Make PyQt5",
                """<b>Make PyQt5</b> v %s
                <p>Copyright &copy; 2007 Qtrac Ltd. 
                All rights reserved.
                <p>This application, modified to work with PyQt5, can be used to build PyQt
                applications.
                It runs pyuic5, pyrcc5, pylupdate5, and lrelease as
                required, although pylupdate5 must be run directly to
                create the initial .ts files.
                <p>Python %s - Qt %s - PyQt %s on %s""" % (
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))


    def setPath(self):
        path = QFileDialog.getExistingDirectory(self,
                "Make PyQt - Set Path", self.pathLabel.text())
        if path:
            self.pathLabel.setText(QDir.toNativeSeparators(path))


    def setToolPaths(self):
        dlg = OptionsForm(self)
        dlg.exec_()


    def build(self):
        self.updateUi(False)
        self.logBrowser.clear()
        recurse = self.recurseCheckBox.isChecked()
        path = self.pathLabel.text()
        self._apply(recurse, self._build, path)
        if self.transCheckBox.isChecked():
            self._apply(recurse, self._translate, path)
        self.updateUi(True)


    def clean(self):
        self.updateUi(False)
        self.logBrowser.clear()
        recurse = self.recurseCheckBox.isChecked()
        path = self.pathLabel.text()
        self._apply(recurse, self._clean, path)
        self.updateUi(True)


    def updateUi(self, enable):
        for widget in (self.buildButton, self.cleanButton,
                self.pathButton, self.recurseCheckBox,
                self.transCheckBox, self.debugCheckBox):
            widget.setEnabled(enable)
        if not enable:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        else:
            QApplication.restoreOverrideCursor()
            self.buildButton.setFocus()


    def _apply(self, recurse, function, path):
        if not recurse:
            function(path)
        else:
            for root, dirs, files in os.walk(path):
                for dir in sorted(dirs):
                    function(os.path.join(root, dir))


    def _build(self, path):
        settings = QSettings('afsc.noaa.gov','makepyqt5')
        pyuic5 = settings.value("pyuic5", PYUIC5)
        pyrcc5 = settings.value("pyrcc5", PYRCC5)
        prefix = self.pathLabel.text()
        if not prefix.endswith(os.sep):
            prefix += os.sep
        failed = 0
        process = QProcess()
        for name in os.listdir(path):
            source = os.path.join(path, name)
            target = None
            if source.endswith(".ui"):
                target = os.path.join(path,
                                    "ui_" + name.replace(".ui", ".py"))
                command = pyuic5
            elif source.endswith(".qrc"):
                target = os.path.join(path,
                                    "qrc_" + name.replace(".qrc", ".py"))
                command = pyrcc5
            if target is not None:
                if not os.access(target, os.F_OK) or (
                   os.stat(source)[stat.ST_MTIME] > \
                   os.stat(target)[stat.ST_MTIME]):
                    args = ["-o", target, source]
                    msg = "converted <font color=darkblue>" + source + \
                          "</font> to <font color=blue>" + target + \
                          "</font>"
                    if self.debugCheckBox.isChecked():
                        msg = "<font color=green># " + msg + "</font>"
                    else:
                        process.start(command, args)
                        if not process.waitForFinished(2 * 60 * 1000):
                            msg = "<font color=red>FAILED: %s</font>" % \
                                command
                            failed += 1
                    self.logBrowser.append(msg.replace(prefix, ""))
                else:
                    self.logBrowser.append("<font color=green>"
                            "# %s is up-to-date</font>" % \
                            source.replace(prefix, ""))
                QApplication.processEvents()
        if failed:
            QMessageBox.information(self, "Make PyQt - Failures",
                    "Try manually setting the paths to the tools "
                    "using <b>More-&gt;Tool paths</b>")


    def _clean(self, path):
        prefix = self.pathLabel.text()
        if not prefix.endswith(os.sep):
            prefix += os.sep
        deletelist = []
        for name in os.listdir(path):
            target = os.path.join(path, name)
            source = None
            if target.endswith(".py") or target.endswith(".pyc") or \
               target.endswith(".pyo"):
                if name.startswith("ui_") and not name[-1] in "oc":
                    source = os.path.join(path, name[3:-3] + ".ui")
                elif name.startswith("qrc_"):
                    if target[-1] in "oc":
                        source = os.path.join(path, name[4:-4] + ".qrc")
                    else:
                        source = os.path.join(path, name[4:-3] + ".qrc")
                elif target[-1] in "oc":
                    source = target[:-1]
                if source is not None:
                    if os.access(source, os.F_OK):
                        if self.debugCheckBox.isChecked():
                            self.logBrowser.append("<font color=green>"
                                    "# delete %s</font>" % \
                                    target.replace(prefix, ""))
                        else:
                            deletelist.append(target)
                    else:
                        self.logBrowser.append("<font color=darkred>"
                                "will not remove "
                                "'%s' since `%s' not found</font>" % (
                                target.replace(prefix, ""),
                                source.replace(prefix, "")))
        if not self.debugCheckBox.isChecked():
            for target in deletelist:
                self.logBrowser.append("deleted "
                        "<font color=red>%s</font>" % \
                        target.replace(prefix, ""))
                os.remove(target)
                QApplication.processEvents()


    def _translate(self, path):
        prefix = self.pathLabel.text()
        if not prefix.endswith(os.sep):
            prefix += os.sep
        files = []
        tsfiles = []
        for name in os.listdir(path):
            if name.endswith((".py", ".pyw")):
                files.append(os.path.join(path, name))
            elif name.endswith(".ts"):
                tsfiles.append(os.path.join(path, name))
        if not tsfiles:
            return
        settings = QSettings()
        pylupdate5 = settings.value("pylupdate5", PYLUPDATE5)
        lrelease = settings.value("lrelease", LRELEASE)
        process = QProcess()
        failed = 0
        for ts in tsfiles:
            qm = ts[:-3] + ".qm"
            command1 = pylupdate5
            args1 = files + ["-ts", ts]
            command2 = lrelease
            args2 = ["-silent", ts, "-qm", qm]
            msg = "updated <font color=blue>%s</font>" % \
                    ts.replace(prefix, "")
            if self.debugCheckBox.isChecked():
                msg = "<font color=green># %s</font>" % msg
            else:
                process.start(command1, args1)
                if not process.waitForFinished(2 * 60 * 1000):
                    msg = "<font color=red>FAILED: %s</font>" % command1
                    failed += 1
            self.logBrowser.append(msg)
            msg = "generated <font color=blue>%s</font>" % \
                    qm.replace(prefix, "")
            if self.debugCheckBox.isChecked():
                msg = "<font color=green># %s</font>" % msg
            else:
                process.start(command2, args2)
                if not process.waitForFinished(2 * 60 * 1000):
                    msg = "<font color=red>FAILED: %s</font>" % command2
                    failed += 1
            self.logBrowser.append(msg)
            QApplication.processEvents()
        if failed:
            QMessageBox.information(self, "Make PyQt - Failures",
                    "Try manually setting the paths to the tools "
                    "using <b>More-&gt;Tool paths</b>")


app = QApplication(sys.argv)
PATH = app.applicationDirPath()
PYUIC5 = os.path.join(PATH, "pyuic5")
PYRCC5 = os.path.join(PATH, "pyrcc5")
PYLUPDATE5 = os.path.join(PATH, "pylupdate5")
LRELEASE = "lrelease"
if platform.system() == "Windows":
    PYUIC5 = PYUIC5.replace("/", "\\") + ".bat"
    PYRCC5 = PYRCC5.replace("/", "\\") + ".exe"
    PYLUPDATE5 = PYLUPDATE5.replace("/", "\\") + ".exe"
app.setApplicationName("Make PyQt")
form = Form()
form.show()
app.exec_()


