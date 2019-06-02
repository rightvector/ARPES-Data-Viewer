'''
MainWindow Module
'''

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QPushButton, QAction, QFileDialog, QSplitter)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon
from databrowser import DataBrowser
from dataprocessor import DataProcessor
from imageviewer import ImageViewer
from visualization3D import MYWidget
import Data
from IgorIO import IgorPackedFile2Data, Data2IgorPackedFile
import os


class MainWindow(QMainWindow):
    '''
    MainWindow class
    '''
    def __init__(self, App):
        super(MainWindow, self).__init__()
        self.App = App
        self.splitterPos = 0
        self.initCompleteFlag = False
        self.signal = resizeSignal()
        self.setGeometry(300, 100, 900, 900)
        self.setWindowIcon(QIcon("./image/mainwin.ico"))
        self.initUI()
        self.signal.resize.connect(self.ImageViewer.resizeEvent_wrapper)
        
    def initUI(self):
        #Menu
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.openAct = QAction('&Open', self)
        self.openAct.setShortcut('Ctrl+O')
        self.openAct.setIcon(QIcon("./image/open.ico"))
        self.saveAct = QAction('&Save', self)
        self.saveAct.setShortcut('Ctrl+S')
        self.saveAct.setIcon(QIcon("./image/save.ico"))
        self.importAct = QAction('&Import Data', self)
        self.importAct.setShortcut('Ctrl+I')
        self.importAct.setIcon(QIcon("./image/import.ico"))
        self.exportAct = QAction('&Export Data', self)
        self.exportAct.setShortcut('Ctrl+E')
        self.exportAct.setIcon(QIcon("./image/export.ico"))
        self.exportAct.setEnabled(False)
        self.exitAct = QAction('&Exit', self)
        self.exitAct.setIcon(QIcon("./image/exit.ico"))
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.importAct)
        self.fileMenu.addAction(self.exportAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.importAct.triggered.connect(self.OnImport)
        self.exportAct.triggered.connect(self.OnExport)
        self.exitAct.triggered.connect(self.close)

        #Data Browser
        self.DataBrowser = DataBrowser(self)

        #Process Region Expansion button
        self.PRButton = QPushButton(">")
        self.PRButton.setFixedSize(20, 80)
        self.PRButton.setCheckable(True)
        self.PRButton.toggled.connect(self.showDataProcessor)

        #Data Processor
        self.DataProcessor = DataProcessor(self)

        #Image Viewer
        self.ImageViewer = ImageViewer(self)

        #Mayavi Region Expansion button
        self.MYButton = QPushButton(">")
        self.MYButton.setFixedSize(20, 80)
        self.MYButton.setCheckable(True)
        #self.MYButton.setEnabled(False)
        self.MYButton.toggled.connect(self.show3D)

        #Mayavi scene
        self.MYWidget = MYWidget(self)

        #Layout
        self.panel, self.splitter, self.Databox, self.DataWidget = self.WinLayout()
        QTimer.singleShot(10, lambda: self.splitter.moveSplitter(self.DataBrowser.minimumWidth(), 1))
        self.splitter.splitterMoved.connect(self.splitterMovedEvent)

        #center panel
        self.centralPanel = QWidget(self)
        self.centralPanel.setLayout(self.panel)
        
        self.setCentralWidget(self.centralPanel)
        self.setWindowTitle('ARPES Data Viewer -- By Wei Yao -- Ver 1.0')    
        self.show()
        self.initCompleteFlag = True

    def WinLayout(self):
        panel = QHBoxLayout()
        splitter = QSplitter()

        splitter.addWidget(self.DataBrowser)
        
        Databox = QHBoxLayout()
        Databox.addWidget(self.PRButton)
        Databox.addWidget(self.ImageViewer)
        Databox.addWidget(self.MYButton)
        DataWidget = QWidget()
        DataWidget.setLayout(Databox)
        splitter.addWidget(DataWidget)

        splitter.setStretchFactor(0,0)
        splitter.setStretchFactor(1,1)

        panel.addWidget(splitter)

        return panel, splitter, Databox, DataWidget

    def showDataProcessor(self, state):
        if state:
            self.Databox.insertWidget(0, self.DataProcessor)
            self.DataProcessor.show()
            self.resizeDataWidget(self.DataProcessor.width()+7, 'DP') #7 is for additional space due to using layout      
            self.PRButton.setText("<")
        else:
            self.Databox.takeAt(0)
            self.DataProcessor.hide()
            #wait for some events are processed in the event loop. 
            #https://stackoverflow.com/questions/28660960/resize-qmainwindow-to-minimal-size-after-content-of-layout-changes
            #This QTimer is used to wait for correct process of layout
            QTimer.singleShot(10, lambda: self.resizeDataWidget(-self.DataProcessor.width()-7, 'DP'))
            self.PRButton.setText(">")

    def show3D(self, state):
        if self.DataProcessor.isVisible():
            pos = 3
        else:
            pos = 2
        if state:
            self.Databox.insertWidget(pos, self.MYWidget)
            self.MYWidget.show()
            self.resizeDataWidget(self.MYWidget.width()+7, 'MY')
            self.MYButton.setText("<")
            self.MYWidget.setData(self.DataBrowser.DataList.currentItem().Data)
        else:
            self.Databox.takeAt(pos)
            self.MYWidget.hide()
            QTimer.singleShot(10, lambda: self.resizeDataWidget(-self.MYWidget.width()-7, 'MY'))
            self.MYButton.setText(">")

    def resizeDataWidget(self, dwidth, flag):
        if dwidth > 0:
            screen_width = QApplication.desktop().screenGeometry().width()
            if self.width()+dwidth+1 < screen_width:
                self.resize(self.width()+dwidth+1, self.height())
                self.resize(self.width()-1, self.height()) # to redraw the gui
            else:
                self.resize(screen_width, self.height())
        elif dwidth < 0:
            #This QTimer is used to wait for correct minimum width of datawidget
            if flag == 'DP':
                delay = 10
            elif flag == 'MY':
                delay = 30
            QTimer.singleShot(delay, lambda: self.resize(self.width()+dwidth, self.height()))

    def OnImport(self):
        filelist = QFileDialog.getOpenFileNames(self, "Import Data", ".", "Igor Packed Files(*.pxt; *.pxp);;ArPy Files(*.arpy);;Ig2Py Files(*.Ig2Py)")[0]
        if len(filelist) > 0:
            self.ImportData(filelist)

    def OnExport(self):
        name = self.DataBrowser.DataList.currentItem().Data.name
        savedfile = QFileDialog.getSaveFileName(self, "Export Data", name, "Igor Packed Files(*.pxt);;ArPy Files(*.arpy)")[0]
        if len(savedfile) > 0:
            self.ExportData(savedfile)
    
    def ImportData(self, filelist):
        for filepath in filelist:
            base = os.path.basename(filepath)
            ext = os.path.splitext(base)[1]
            if ext.lower() == ".ig2py":
                spec = Data.Ig2Py2Data(filepath)
                if spec != None:
                    self.NewData(spec)
            elif ext.lower() == ".arpy":
                spec = Data.ArPy2Data(filepath)
                if spec != None:
                    self.NewData(spec)
            elif ext.lower() == ".pxt":
                specList = IgorPackedFile2Data(filepath, True)
                for spec in specList:
                    self.NewData(spec)
            elif ext.lower() == ".pxp":
                specList = IgorPackedFile2Data(filepath, False)
                for spec in specList:
                    self.NewData(spec)

    def ExportData(self, savedfile):
        base = os.path.basename(savedfile)
        ext = os.path.splitext(base)[1]
        if ext == ".arpy":
            data = self.DataBrowser.DataList.currentItem().Data
            Data.Data2ArPy(data, savedfile)
        elif ext == ".pxt":
            #data = self.DataBrowser.DataList.currentItem().Data
            datalist = [item.Data for item in self.DataBrowser.DataList.selectedItems()]
            Data2IgorPackedFile(datalist, savedfile)

    def setData(self, data):
        self.DataProcessor.updateUI(data)
        self.ImageViewer.setData(data)
        if self.MYButton.isChecked():
            self.MYWidget.setData(data)
    
    def NewData(self, data):
        self.DataBrowser.DataList.addDataItem(data)

    def resizeEvent(self, event):
        if self.DataBrowser.width() < self.splitterPos:
            self.splitter.moveSplitter(self.splitterPos, 1)
        elif self.initCompleteFlag:
            self.signal.resize.emit()

    def splitterMovedEvent(self, pos, idx):
        self.splitterPos = pos
        if pos > self.DataBrowser.minimumWidth():
            if self.initCompleteFlag:
                self.signal.resize.emit()
        else:
            self.resize(self.width()+1, self.height())  # to redraw the gui
            self.resize(self.width()-1, self.height())

    def closeEvent(self, event):
        self.DataBrowser.DataList.noteWin.close()


class resizeSignal(QObject):
    resize = pyqtSignal()
