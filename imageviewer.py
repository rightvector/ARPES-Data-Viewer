'''
ImageViewer module
'''

from PyQt5.QtWidgets import QWidget, QStackedLayout, QFrame, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from Viewer.twoDimage import twoDimage
from Viewer.threeDblock import threeDblock
from Viewer.fourDmap import fourDmap
import time


class ImageViewer(QWidget):
    def __init__(self, Win):
        super(ImageViewer, self).__init__()
        self.Win = Win
        self.signal = resizeSignal()
        self.signal.resize.connect(self.resizeEvent_wrapper)

        self.twoDimage = twoDimage(self)
        self.threeDblock = threeDblock(self)
        self.fourDmap = fourDmap(self)

        self.box = QStackedLayout()
        self.box.addWidget(QFrame())
        self.box.addWidget(QLabel("1D data"))
        self.box.addWidget(self.twoDimage)
        self.box.addWidget(self.threeDblock)
        self.box.addWidget(self.fourDmap)
        self.box.setCurrentIndex(0)

        self.keyflag = [False, False]
        self.setFocusPolicy(Qt.ClickFocus)

        self.setLayout(self.box)
        self.setMinimumSize(1, 500)

    def setData(self, data):
        if data == None:
            self.box.setCurrentIndex(0)
            self.setMinimumWidth(1)
        else:
            if data.dims == 1:
                self.box.setCurrentIndex(1)
                minWidth = 1
            elif data.dims == 2:
                self.box.setCurrentIndex(2)
                self.twoDimage.loaddata(data)
                minWidth = 480
            elif data.dims == 3:
                self.box.setCurrentIndex(3)
                self.threeDblock.loaddata(data)
                minWidth = 580
            elif data.dims == 4:
                self.box.setCurrentIndex(4)
                self.fourDmap.loaddata(data)
                minWidth = 640
            if self.width() < minWidth:
                self.Win.resize(self.Win.width()+minWidth-self.width(), self.Win.height())
            self.setMinimumWidth(minWidth)

    def resizeEvent_wrapper(self):
        if self.box.currentIndex() == 2:
            self.twoDimage.resizeEvent_wrapper()
        elif self.box.currentIndex() == 3:
            self.threeDblock.resizeEvent_wrapper()
        elif self.box.currentIndex() == 4:
            self.fourDmap.resizeEvent_wrapper()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyflag[0] = True
        if event.key() == Qt.Key_A:
            self.keyflag[1] = True
        if self.keyflag == [True, True]:
            if self.box.currentIndex() == 2:
                if self.twoDimage.toolPanel.isChecked():
                    self.twoDimage.toolPanel.setChecked(False)
                else:
                    self.twoDimage.toolPanel.setChecked(True)
            if self.box.currentIndex() == 3:
                if self.threeDblock.toolPanel.isChecked():
                    self.threeDblock.toolPanel.setChecked(False)
                else:
                    self.threeDblock.toolPanel.setChecked(True)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.keyflag[0] = False
        if event.key() == Qt.Key_A:
            self.keyflag[1] = False


class resizeSignal(QObject):
    resize = pyqtSignal()
