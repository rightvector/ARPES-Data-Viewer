'''
Data Processor Module
'''

from PyQt5.QtWidgets import (QWidget, QTabWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QLayout, QGroupBox, 
QPushButton, QCheckBox, QStyleFactory, QDoubleSpinBox, QSpinBox, QRadioButton, QFormLayout, QDialog, QProgressBar, 
QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPalette, QMovie, QColor
import Data
import numpy as np
import threading, time, os


#decorator
def process2D(func):
    '''
    Decorator for 2D process operation.
    '''
    def wrapper(*args):
        instance = args[0]
        if instance.singleData.dims == 2:
            func(*args)
        instance.Win.DataBrowser.InfoList.setProperty(instance.singleData.property)
        instance.Win.ImageViewer.twoDimage.selector.set_visible(False)
        instance.Win.setData(instance.singleData)
        instance.saveButton.setEnabled(True)
    return wrapper

def processGeneral(func):
    '''
    Decorator for General process operation.
    '''
    def wrapper(*args):
        instance = args[0]
        func(*args)
        instance.Win.DataBrowser.InfoList.setProperty(instance.singleData.property)
        instance.Win.setData(instance.singleData)
        instance.saveButton.setEnabled(True)
    return wrapper


def process3D(func):
    '''
    Decorator for 3D process operation with general thread.
    '''
    lock = threading.Lock()
    
    def targetFunc(dlg, s, *args):
        while not dlg.isVisible():
            pass
        dlg.activateWindow()
        func(*args)
        s.finished.emit()

    def wrapper(*args):
        instance = args[0]
        if instance.singleData.dims == 3:
            instance = args[0]
            dlg = waitingDialog(instance.Win)
            dlg.progress.setTextVisible(False)
            s = signal()
            s.finished.connect(dlg.close)
            t = threading.Thread(target=targetFunc, args=(dlg, s, *args))
            t.start()
            if t.isAlive():
                dlg.exec_()
        instance.Win.DataBrowser.InfoList.setProperty(instance.singleData.property)
        instance.Win.ImageViewer.threeDblock.selector.set_visible(False)
        instance.Win.setData(instance.singleData)
        instance.saveButton.setEnabled(True)
    return wrapper


def process3D_T(func):
    '''
    Decorator for 3D process operation with custom thread.
    '''
    def wrapper(*args):
        instance = args[0]
        if instance.singleData.dims == 3:
            result = func(*args)
        if result == QDialog.Accepted:
            instance.Win.DataBrowser.InfoList.setProperty(instance.singleData.property)
            instance.Win.ImageViewer.threeDblock.selector.set_visible(False)
            instance.Win.setData(instance.singleData)
            instance.saveButton.setEnabled(True)
    return wrapper


class DataProcessor(QTabWidget):
    def __init__(self, Win):
        super(DataProcessor, self).__init__()

        self.Win = Win

        self.tab_single = SingleTab(self.Win)
        self.tab_multiple = MultipleTab(self.Win)
        self.addTab(self.tab_single, "Single")
        self.addTab(self.tab_multiple, "Multiple")
        self.tab_single.setEnabled(False)
        self.tab_multiple.setEnabled(False)

        tabStyle = "QTabBar::tab:!selected {height: 30px; width: 80px;}  QTabBar::tab:selected {height: 30px; width: 80px;font-weight: bold;}"
        self.setStyleSheet(tabStyle)
        self.setStyle(QStyleFactory.create('Fusion'))

        self.setFocusPolicy(Qt.ClickFocus)
        self.setFixedWidth(250)

    def updateUI(self, data):
        self.tab_single.updateUI(data)
        self.tab_multiple.updateUI(data)


class SingleTab(QScrollArea):
    def __init__(self, Win):
        super(SingleTab, self).__init__()
        self.Win = Win
        self.singleData = Data.Spectrum()
        
        #Developer parameter
        self.core_num = int(os.cpu_count()/2)
        self.solver_max_iteration_step = 30
        self.solver_error = 1e-7
        self.DevWin = DevSettingDialog(self, self.core_num, self.solver_max_iteration_step, self.solver_error)

        self.box = QVBoxLayout()
        self.box.setSizeConstraint(QLayout.SetFixedSize)

        #general operation
        self.groupbox_general = QGroupBox("General Operation")
        self.groupbox_general.setFixedWidth(200)
        self.setvalue = QDoubleSpinBox()
        self.setvalue.setDecimals(6)
        self.setvalue.setRange(-10000, 10000)
        self.setButton = QPushButton("Set")
        self.setButton.setFixedWidth(50)
        self.setButton.clicked.connect(self.OnRemoveNaN)
        hbox_nan = QHBoxLayout()
        hbox_nan.addWidget(self.setvalue)
        hbox_nan.addWidget(self.setButton)
        vbox_general = QVBoxLayout()
        vbox_general.addWidget(QLabel("Remove NaN"))
        vbox_general.addLayout(hbox_nan)
        self.groupbox_general.setLayout(vbox_general)
        self.box.addWidget(self.groupbox_general)

        #general operation: Offset
        self.groupbox_offset = QGroupBox("General-Offset")
        self.groupbox_offset.setFixedWidth(200)
        self.xdecreaseButton = QPushButton("<")
        self.xdecreaseButton.setFixedSize(25, 25)
        self.xstep = QDoubleSpinBox()
        self.xstep.setDecimals(6)
        self.xstep.setRange(0, 10000)
        self.xincreaseButton = QPushButton(">")
        self.xincreaseButton.setFixedSize(25, 25)
        hbox_x = QHBoxLayout()
        hbox_x.addWidget(self.xdecreaseButton)
        hbox_x.addWidget(self.xstep)
        hbox_x.addWidget(self.xincreaseButton)
        self.ydecreaseButton = QPushButton("<")
        self.ydecreaseButton.setFixedSize(25, 25)
        self.ystep = QDoubleSpinBox()
        self.ystep.setDecimals(6)
        self.ystep.setRange(0, 10000)
        self.yincreaseButton = QPushButton(">")
        self.yincreaseButton.setFixedSize(25, 25)
        hbox_y = QHBoxLayout()
        hbox_y.addWidget(self.ydecreaseButton)
        hbox_y.addWidget(self.ystep)
        hbox_y.addWidget(self.yincreaseButton)
        self.zdecreaseButton = QPushButton("<")
        self.zdecreaseButton.setFixedSize(25, 25)
        self.zstep = QDoubleSpinBox()
        self.zstep.setDecimals(6)
        self.zstep.setRange(0, 10000)
        self.zincreaseButton = QPushButton(">")
        self.zincreaseButton.setFixedSize(25, 25)
        hbox_z = QHBoxLayout()
        hbox_z.addWidget(self.zdecreaseButton)
        hbox_z.addWidget(self.zstep)
        hbox_z.addWidget(self.zincreaseButton)
        self.tdecreaseButton = QPushButton("<")
        self.tdecreaseButton.setFixedSize(25, 25)
        self.tstep = QDoubleSpinBox()
        self.tstep.setDecimals(6)
        self.tstep.setRange(0, 10000)
        self.tincreaseButton = QPushButton(">")
        self.tincreaseButton.setFixedSize(25, 25)
        hbox_t = QHBoxLayout()
        hbox_t.addWidget(self.tdecreaseButton)
        hbox_t.addWidget(self.tstep)
        hbox_t.addWidget(self.tincreaseButton)
        self.xdecreaseButton.clicked.connect(self.offset)
        self.xincreaseButton.clicked.connect(self.offset)
        self.ydecreaseButton.clicked.connect(self.offset)
        self.yincreaseButton.clicked.connect(self.offset)
        self.zdecreaseButton.clicked.connect(self.offset)
        self.zincreaseButton.clicked.connect(self.offset)
        self.tdecreaseButton.clicked.connect(self.offset)
        self.tincreaseButton.clicked.connect(self.offset)
        vbox_offset = QVBoxLayout()
        vbox_offset.addWidget(QLabel("X-Axis Offset"))
        vbox_offset.addLayout(hbox_x)
        vbox_offset.addWidget(QLabel("Y-Axis Offset"))
        vbox_offset.addLayout(hbox_y)
        vbox_offset.addWidget(QLabel("Z-Axis Offset"))
        vbox_offset.addLayout(hbox_z)
        vbox_offset.addWidget(QLabel("T-Axis Offset"))
        vbox_offset.addLayout(hbox_t)
        self.groupbox_offset.setLayout(vbox_offset)
        self.box.addWidget(self.groupbox_offset)

        #general operation: Range Selection
        self.groupbox_range = QGroupBox("General-Range Selection")
        self.groupbox_range.setFixedWidth(200)
        self.xlow = QDoubleSpinBox()
        self.xlow.setDecimals(6)
        self.xlow.setRange(0, 1)
        self.xlow.setKeyboardTracking(False)
        self.xlow.valueChanged.connect(self.rangeValidator)
        self.xhigh = QDoubleSpinBox()
        self.xhigh.setDecimals(6)
        self.xhigh.setRange(0, 1)
        self.xhigh.setValue(1)
        self.xhigh.setKeyboardTracking(False)
        self.xhigh.valueChanged.connect(self.rangeValidator)
        self.ylow = QDoubleSpinBox()
        self.ylow.setDecimals(6)
        self.ylow.setRange(0, 1)
        self.ylow.setKeyboardTracking(False)
        self.ylow.valueChanged.connect(self.rangeValidator)
        self.yhigh = QDoubleSpinBox()
        self.yhigh.setDecimals(6)
        self.yhigh.setRange(0, 1)
        self.yhigh.setValue(1)
        self.yhigh.setKeyboardTracking(False)
        self.yhigh.valueChanged.connect(self.rangeValidator)
        self.zlow = QDoubleSpinBox()
        self.zlow.setDecimals(6)
        self.zlow.setRange(0, 1)
        self.zlow.setKeyboardTracking(False)
        self.zlow.valueChanged.connect(self.rangeValidator)
        self.zhigh = QDoubleSpinBox()
        self.zhigh.setDecimals(6)
        self.zhigh.setRange(0, 1)
        self.zhigh.setValue(1)
        self.zhigh.setKeyboardTracking(False)
        self.zhigh.valueChanged.connect(self.rangeValidator)
        self.tlow = QDoubleSpinBox()
        self.tlow.setDecimals(6)
        self.tlow.setRange(0, 1)
        self.tlow.setKeyboardTracking(False)
        self.tlow.valueChanged.connect(self.rangeValidator)
        self.thigh = QDoubleSpinBox()
        self.thigh.setDecimals(6)
        self.thigh.setRange(0, 1)
        self.thigh.setValue(1)
        self.thigh.setKeyboardTracking(False)
        self.thigh.valueChanged.connect(self.rangeValidator)
        self.rangeReset = QPushButton("Reset")
        self.rangeReset.clicked.connect(self.updateRange)
        label_range = QHBoxLayout()
        label_range.addStretch(4)
        label_range.addWidget(QLabel("Low"))
        label_range.addStretch(4)
        label_range.addWidget(QLabel("High"))
        label_range.addStretch(3)
        hbox_xrange = QHBoxLayout()
        hbox_xrange.addWidget(QLabel("X:"))
        hbox_xrange.addWidget(self.xlow)
        hbox_xrange.addWidget(self.xhigh)
        hbox_yrange = QHBoxLayout()
        hbox_yrange.addWidget(QLabel("Y:"))
        hbox_yrange.addWidget(self.ylow)
        hbox_yrange.addWidget(self.yhigh)
        hbox_zrange = QHBoxLayout()
        hbox_zrange.addWidget(QLabel("Z:"))
        hbox_zrange.addWidget(self.zlow)
        hbox_zrange.addWidget(self.zhigh)
        hbox_trange = QHBoxLayout()
        hbox_trange.addWidget(QLabel("T:"))
        hbox_trange.addWidget(self.tlow)
        hbox_trange.addWidget(self.thigh)
        vbox_range = QVBoxLayout()
        vbox_range.addLayout(label_range)
        vbox_range.addLayout(hbox_xrange)
        vbox_range.addLayout(hbox_yrange)
        vbox_range.addLayout(hbox_zrange)
        vbox_range.addLayout(hbox_trange)
        vbox_range.addWidget(self.rangeReset)
        self.groupbox_range.setLayout(vbox_range)
        self.box.addWidget(self.groupbox_range)

        #general merge
        self.groupbox_merge = QGroupBox("General-Merge")
        self.groupbox_merge.setFixedWidth(200)
        self.xnum = QSpinBox()
        self.xnum.setRange(1, 10000)
        self.ynum = QSpinBox()
        self.ynum.setRange(1, 10000)
        self.znum = QSpinBox()
        self.znum.setRange(1, 10000)
        self.tnum = QSpinBox()
        self.tnum.setRange(1, 10000)
        self.merge = QPushButton("Merge")
        self.merge.clicked.connect(self.OnMerge)
        hbox_xy = QHBoxLayout()
        hbox_xy.addWidget(QLabel("X:"))
        hbox_xy.addWidget(self.xnum)
        hbox_xy.addWidget(QLabel("Y:"))
        hbox_xy.addWidget(self.ynum)
        hbox_zt = QHBoxLayout()
        hbox_zt.addWidget(QLabel("Z:"))
        hbox_zt.addWidget(self.znum)
        hbox_zt.addWidget(QLabel("T:"))
        hbox_zt.addWidget(self.tnum)
        vbox_merge = QVBoxLayout()
        vbox_merge.addLayout(hbox_xy)
        vbox_merge.addLayout(hbox_zt)
        vbox_merge.addWidget(self.merge)
        self.groupbox_merge.setLayout(vbox_merge)
        self.box.addWidget(self.groupbox_merge)

        #general detector correction
        self.groupbox_detector = QGroupBox("General-Detector Correction")
        self.groupbox_detector.setFixedWidth(200)
        self.correctx = QPushButton("Balance X Direction")
        self.correctx.setToolTip("Please set proper <b>Y</b> range.")
        self.correcty = QPushButton("Balance Y Direction")
        self.correcty.setToolTip("Please set proper <b>X</b> range.")
        vbox_detector = QVBoxLayout()
        vbox_detector.addWidget(self.correctx)
        vbox_detector.addWidget(self.correcty)
        self.groupbox_detector.setLayout(vbox_detector)
        self.box.addWidget(self.groupbox_detector)

        #2D general operation
        self.groupbox_2D_general = QGroupBox("2D-General Operation")
        self.groupbox_2D_general.setFixedWidth(200)
        self.transposeButton = QPushButton("Transpose")
        self.transposeButton.clicked.connect(self.transpose2D)
        self.mirrorXButton = QPushButton("Mirror X")
        self.mirrorYButton = QPushButton("Mirror Y")
        self.mirrorXButton.clicked.connect(self.mirror2D)
        self.mirrorYButton.clicked.connect(self.mirror2D)
        self.normalXDCButton = QPushButton("Normal XDC")
        self.normalYDCButton = QPushButton("Normal YDC")
        self.normalXDCButton.clicked.connect(self.normal2D)
        self.normalYDCButton.clicked.connect(self.normal2D)
        self.crop2D = QPushButton("Crop")
        self.crop2D.clicked.connect(self.OnCropSpec)
        self.aspect = QCheckBox("Equal Proportion")
        self.aspect.stateChanged.connect(self.changeAspect2D)
        hbox_2D_mirror = QHBoxLayout()
        hbox_2D_mirror.addWidget(self.mirrorXButton)
        hbox_2D_mirror.addWidget(self.mirrorYButton)
        hbox_2D_normal = QHBoxLayout()
        hbox_2D_normal.addWidget(self.normalXDCButton)
        hbox_2D_normal.addWidget(self.normalYDCButton)
        hbox_2D_aspect = QHBoxLayout()
        hbox_2D_aspect.addStretch(1)
        hbox_2D_aspect.addWidget(self.aspect)
        hbox_2D_aspect.addStretch(1)
        vbox_2D_general = QVBoxLayout()
        vbox_2D_general.addWidget(self.transposeButton)
        vbox_2D_general.addLayout(hbox_2D_mirror)
        vbox_2D_general.addLayout(hbox_2D_normal)
        vbox_2D_general.addWidget(self.crop2D)
        vbox_2D_general.addLayout(hbox_2D_aspect)
        self.groupbox_2D_general.setLayout(vbox_2D_general)
        self.box.addWidget(self.groupbox_2D_general)

        #2D kspace conversion
        self.groupbox_2D_kspace = QGroupBox("2D-kspace Conversion")
        self.groupbox_2D_kspace.setFixedWidth(200)
        energyAxis_label = QLabel("Energy Axis:")
        energyAxis_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.xaxis_2D_energy = QRadioButton("X")
        self.yaxis_2D_energy = QRadioButton("Y")
        self.xaxis_2D_energy.setChecked(True)
        hbox_2D_EA = QHBoxLayout()
        hbox_2D_EA.addWidget(energyAxis_label)
        hbox_2D_EA.addWidget(self.xaxis_2D_energy, 1)
        hbox_2D_EA.addWidget(self.yaxis_2D_energy, 1)
        self.kspaceButton = QPushButton("To k-space")
        self.kspaceButton.clicked.connect(self.Tokspace2D)
        vbox_2D_kspace = QVBoxLayout()
        vbox_2D_kspace.addLayout(hbox_2D_EA)
        vbox_2D_kspace.addWidget(self.kspaceButton)
        self.groupbox_2D_kspace.setLayout(vbox_2D_kspace)
        self.box.addWidget(self.groupbox_2D_kspace)

        #3D general operation
        self.groupbox_3D_general = QGroupBox("3D-General Operation")
        self.groupbox_3D_general.setFixedWidth(200)
        self.transposeButton3D = QPushButton("Transpose")
        self.transposeButton3D.clicked.connect(self.transpose3D)
        self.YZXButton3D = QPushButton("X -> Z")
        self.ZXYButton3D = QPushButton("Y -> Z")
        self.YZXButton3D.clicked.connect(self.changeZAxis)
        self.ZXYButton3D.clicked.connect(self.changeZAxis)
        self.mirrorYButton3D = QPushButton("Mirror Y")
        self.mirrorXButton3D = QPushButton("Mirror X")
        self.mirrorYButton3D = QPushButton("Mirror Y")
        self.mirrorXButton3D.clicked.connect(self.mirror3D)
        self.mirrorYButton3D.clicked.connect(self.mirror3D)
        self.crop3D = QPushButton("Crop")
        self.crop3D.clicked.connect(self.OnCropSpec)
        self.aspect3D = QCheckBox("Equal Proportion")
        self.aspect3D.stateChanged.connect(self.changeAspect3D)
        hbox_3D_zaxis = QHBoxLayout()
        hbox_3D_zaxis.addWidget(self.YZXButton3D)
        hbox_3D_zaxis.addWidget(self.ZXYButton3D)
        hbox_3D_mirror = QHBoxLayout()
        hbox_3D_mirror.addWidget(self.mirrorXButton3D)
        hbox_3D_mirror.addWidget(self.mirrorYButton3D)
        hbox_3D_aspect = QHBoxLayout()
        hbox_3D_aspect.addStretch(1)
        hbox_3D_aspect.addWidget(self.aspect3D)
        hbox_3D_aspect.addStretch(1)
        vbox_3D_general = QVBoxLayout()
        vbox_3D_general.addWidget(self.transposeButton3D)
        vbox_3D_general.addLayout(hbox_3D_zaxis)
        vbox_3D_general.addLayout(hbox_3D_mirror)
        vbox_3D_general.addWidget(self.crop3D)
        vbox_3D_general.addLayout(hbox_3D_aspect)
        self.groupbox_3D_general.setLayout(vbox_3D_general)
        self.box.addWidget(self.groupbox_3D_general)

        #3D kspace conversion
        self.groupbox_3D_kspace = QGroupBox("3D-kspace Conversion")
        self.groupbox_3D_kspace.setFixedWidth(200)
        self.slit_h_3D = QRadioButton("Horizontal")
        self.slit_v_3D = QRadioButton("Vertical")
        self.slit_h_3D.setChecked(True)
        hbox_3D_slit = QHBoxLayout()     
        hbox_3D_slit.addWidget(self.slit_h_3D, 1)
        hbox_3D_slit.addWidget(self.slit_v_3D, 1)
        self.bias_3D = QDoubleSpinBox()
        self.bias_3D.setDecimals(6)
        self.bias_3D.setRange(-360, 360)
        self.biasLabel_3D = QLabel("Bias:")
        self.biasLabel_3D.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hbox_3D_bias = QHBoxLayout()
        hbox_3D_bias.addWidget(self.biasLabel_3D, 0)
        hbox_3D_bias.addWidget(self.bias_3D, 1)
        self.theta3DButton_3D = QPushButton("Theta Mapping")
        self.theta3DButton_3D.setToolTip('This applys <b>parallel calculation</b>. Make sure: <b>Energy</b> is along <b>Z</b> axis and <b>Sweeping direction</b> is along <b>Y</b> axis.')
        self.theta3DButton_3D.clicked.connect(self.Tokspace3D)
        self.azimuth3DButton_3D = QPushButton("Azimuth Mapping")
        self.azimuth3DButton_3D.setToolTip('Make sure: <b>Energy</b> is along <b>Z</b> axis and <b>Sweeping direction</b> is along <b>Y</b> axis.')
        self.iPot_3D = QDoubleSpinBox()
        self.iPot_3D.setDecimals(6)
        self.iPot_3D.setRange(-10000, 10000)
        self.iPotLabel_3D = QLabel("Inn. Potential:")
        self.iPotLabel_3D.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hbox_3D_ip = QHBoxLayout()
        hbox_3D_ip.addWidget(self.iPotLabel_3D, 0)
        hbox_3D_ip.addWidget(self.iPot_3D, 1)
        self.PE3DButton_3D = QPushButton("hv Mapping")
        self.PE3DButton_3D.setToolTip('Make sure: <b>Energy</b> is along <b>Z</b> axis, <b>Angle</b> is along <b>X</b> axis and <b>Photon Energy</b> is along <b>Y</b> axis.')
        self.kspace2DButton_3D = QPushButton("Non-kspace Mapping")
        self.kspace2DButton_3D.setToolTip('Make sure: <b>Energy</b> is along <b>X</b> axis and <b>Angle</b> is along <b>Y</b> axis.')
        vbox_3D_kspace = QVBoxLayout()
        vbox_3D_kspace.addWidget(QLabel("Slit Orientation:"))
        vbox_3D_kspace.addLayout(hbox_3D_slit)
        vbox_3D_kspace.addLayout(hbox_3D_bias)
        vbox_3D_kspace.addWidget(self.theta3DButton_3D)
        vbox_3D_kspace.addWidget(self.azimuth3DButton_3D)
        vbox_3D_kspace.addLayout(hbox_3D_ip)
        vbox_3D_kspace.addWidget(self.PE3DButton_3D)
        vbox_3D_kspace.addWidget(self.kspace2DButton_3D)
        self.groupbox_3D_kspace.setLayout(vbox_3D_kspace)
        self.box.addWidget(self.groupbox_3D_kspace)

        #Save & Restore Data
        self.saveButton = QPushButton("Save")
        self.saveButton.setEnabled(False)
        self.saveButton.clicked.connect(self.SaveData)
        self.restoreButton = QPushButton("Restore")
        self.restoreButton.clicked.connect(self.RestoreData)
        hbox_save_restore = QHBoxLayout()
        hbox_save_restore.addStretch(1)
        hbox_save_restore.addWidget(self.saveButton)
        hbox_save_restore.addWidget(self.restoreButton)
        hbox_save_restore.addStretch(1)
        self.box.addLayout(hbox_save_restore)

        #Developer Setting
        self.DevSetting = QCheckBox("Developer Setting")
        self.DevSetting.stateChanged.connect(self.OpenDevSetting)
        hbox_dev = QHBoxLayout()
        hbox_dev.addStretch(1)
        hbox_dev.addWidget(self.DevSetting)
        hbox_dev.addStretch(1)
        self.box.addLayout(hbox_dev)

        self.container = QWidget()
        self.container.setStyleSheet("background-color: 'white';")
        self.container.setStyle(QStyleFactory.create('Fusion'))
        self.container.setLayout(self.box)

        self.setWidget(self.container)
        self.setStyle(QStyleFactory.create('Fusion'))
        self.setStyleSheet("QScrollArea {background-color: 'white'; border: 0px}")

    def updateUI(self, data):
        if data == None:
            self.setEnabled(False)
        else:
            self.setEnabled(True)
            self.singleData = data
            if data.dims == 1:
                pass
            elif data.dims == 2:
                self.enable2Dwidget()
            elif data.dims == 3:
                self.enable3Dwidget()
            self.saveButton.setEnabled(not data.rawdataflag)
    
    def enable2Dwidget(self):
        self.ydecreaseButton.setEnabled(True)
        self.ystep.setEnabled(True)
        self.yincreaseButton.setEnabled(True)
        self.zdecreaseButton.setEnabled(False)
        self.zstep.setEnabled(False)
        self.zincreaseButton.setEnabled(False)
        self.tdecreaseButton.setEnabled(False)
        self.tstep.setEnabled(False)
        self.tincreaseButton.setEnabled(False)
        self.updateRange()
        self.ylow.setEnabled(True)
        self.yhigh.setEnabled(True)
        self.zlow.setEnabled(False)
        self.zhigh.setEnabled(False)
        self.tlow.setEnabled(False)
        self.thigh.setEnabled(False)
        self.ynum.setEnabled(True)
        self.znum.setEnabled(False)
        self.tnum.setEnabled(False)
        self.groupbox_detector.setEnabled(True)
        self.groupbox_2D_general.setEnabled(True)
        self.groupbox_2D_kspace.setEnabled(True)
        self.set2DEnergyAxis(self.singleData.energyAxis)
        self.groupbox_3D_general.setEnabled(False)
        self.groupbox_3D_kspace.setEnabled(False)

    def set2DEnergyAxis(self, energyAxis):
        if energyAxis != None:
            if energyAxis == 'X':
                self.xaxis_2D_energy.setChecked(True)
            else:
                self.yaxis_2D_energy.setChecked(True)
            self.xaxis_2D_energy.setEnabled(False)
            self.yaxis_2D_energy.setEnabled(False)
        else:
            self.xaxis_2D_energy.setEnabled(True)
            self.yaxis_2D_energy.setEnabled(True)

    def enable3Dwidget(self):
        self.ydecreaseButton.setEnabled(True)
        self.ystep.setEnabled(True)
        self.yincreaseButton.setEnabled(True)
        self.zdecreaseButton.setEnabled(True)
        self.zstep.setEnabled(True)
        self.zincreaseButton.setEnabled(True)
        self.tdecreaseButton.setEnabled(False)
        self.tstep.setEnabled(False)
        self.tincreaseButton.setEnabled(False)
        self.updateRange()
        self.ylow.setEnabled(True)
        self.yhigh.setEnabled(True)
        self.zlow.setEnabled(False)
        self.zhigh.setEnabled(False)
        self.tlow.setEnabled(False)
        self.thigh.setEnabled(False)
        self.ynum.setEnabled(True)
        self.znum.setEnabled(True)
        self.tnum.setEnabled(False)
        self.groupbox_detector.setEnabled(True)
        self.groupbox_2D_general.setEnabled(False)
        self.groupbox_2D_kspace.setEnabled(False)
        self.groupbox_3D_general.setEnabled(True)
        self.groupbox_3D_kspace.setEnabled(True)

    def updateRange(self):
        self.xlow.setRange(self.singleData.xmin, self.singleData.xmax)
        self.xlow.setSingleStep(self.singleData.xstep)
        self.xhigh.setRange(self.singleData.xmin, self.singleData.xmax)
        self.xhigh.setSingleStep(self.singleData.xstep)
        self.xlow.setValue(self.singleData.xmin)
        self.xhigh.setValue(self.singleData.xmax)
        if self.singleData.dims > 1:
            self.ylow.setRange(self.singleData.ymin, self.singleData.ymax)
            self.ylow.setSingleStep(self.singleData.ystep)
            self.yhigh.setRange(self.singleData.ymin, self.singleData.ymax)
            self.yhigh.setSingleStep(self.singleData.ystep)
            self.ylow.setValue(self.singleData.ymin)
            self.yhigh.setValue(self.singleData.ymax)
        if self.singleData.dims == 4:
            self.zlow.setRange(self.singleData.zmin, self.singleData.zmax)
            self.zlow.setSingleStep(self.singleData.zstep)
            self.zhigh.setRange(self.singleData.zmin, self.singleData.zmax)
            self.zhigh.setSingleStep(self.singleData.zstep)
            self.tlow.setRange(self.singleData.tmin, self.singleData.tmax)
            self.tlow.setSingleStep(self.singleData.tstep)
            self.thigh.setRange(self.singleData.tmin, self.singleData.tmax)
            self.thigh.setSingleStep(self.singleData.tstep)
            self.zlow.setValue(self.singleData.zmin)
            self.zhigh.setValue(self.singleData.zmax)
            self.tlow.setValue(self.singleData.tmin)
            self.thigh.setValue(self.singleData.tmax)

    def rangeValidator(self, value):
        if self.sender() == self.xlow:
            if value > self.xhigh.value():
                self.xlow.setValue(self.xhigh.value())
        if self.sender() == self.xhigh:
            if value < self.xlow.value():
                self.xhigh.setValue(self.xlow.value())
        if self.sender() == self.ylow:
            if value > self.yhigh.value():
                self.ylow.setValue(self.yhigh.value())
        if self.sender() == self.yhigh:
            if value < self.ylow.value():
                self.yhigh.setValue(self.ylow.value())
        if self.sender() == self.zlow:
            if value > self.zhigh.value():
                self.zlow.setValue(self.zhigh.value())
        if self.sender() == self.zhigh:
            if value < self.zlow.value():
                self.zhigh.setValue(self.zlow.value())
        if self.sender() == self.tlow:
            if value > self.thigh.value():
                self.tlow.setValue(self.thigh.value())
        if self.sender() == self.thigh:
            if value < self.tlow.value():
                self.thigh.setValue(self.tlow.value())

    def setSelectXRange(self, x0=0, x1=1):
        self.xlow.setValue(x0)
        self.xhigh.setValue(x1)

    def setSelectYRange(self, y0=0, y1=1):
        self.ylow.setValue(y0)
        self.yhigh.setValue(y1)
    
    def setSelectXYRange(self, x0=0, x1=1, y0=0, y1=1, cropSpec=True):
        if cropSpec:
            self.xlow.setValue(x0)
            self.xhigh.setValue(x1)
            self.ylow.setValue(y0)
            self.yhigh.setValue(y1)
        else:
            self.zlow.setValue(x0)
            self.zhigh.setValue(x1)
            self.tlow.setValue(y0)
            self.thigh.setValue(y1)

    @processGeneral
    def OnRemoveNaN(self, flag):
        mask = np.isnan(self.singleData.data)
        self.singleData.data[mask] = self.setvalue.value()
    
    @processGeneral
    def offset(self, flag):
        if self.sender() == self.xdecreaseButton:
            self.singleData.xscale -= self.xstep.value()
            self.singleData.xmin -= self.xstep.value()
            self.singleData.xmax -= self.xstep.value()           
        if self.sender() == self.xincreaseButton:
            self.singleData.xscale += self.xstep.value()
            self.singleData.xmin += self.xstep.value()
            self.singleData.xmax += self.xstep.value()           
        if self.sender() == self.ydecreaseButton:
            self.singleData.yscale -= self.ystep.value()
            self.singleData.ymin -= self.ystep.value()
            self.singleData.ymax -= self.ystep.value()           
        if self.sender() == self.yincreaseButton:
            self.singleData.yscale += self.ystep.value()
            self.singleData.ymin += self.ystep.value()
            self.singleData.ymax += self.ystep.value()          
        if self.sender() == self.zdecreaseButton:
            self.singleData.zscale -= self.zstep.value()
            self.singleData.zmin -= self.zstep.value()
            self.singleData.zmax -= self.zstep.value()          
        if self.sender() == self.zincreaseButton:
            self.singleData.zscale += self.zstep.value()
            self.singleData.zmin += self.zstep.value()
            self.singleData.zmax += self.zstep.value()
        if self.sender() == self.tdecreaseButton:
            self.singleData.tscale -= self.tstep.value()
            self.singleData.tmin -= self.tstep.value()
            self.singleData.tmax -= self.tstep.value()          
        if self.sender() == self.tincreaseButton:
            self.singleData.tscale += self.tstep.value()
            self.singleData.tmin += self.tstep.value()
            self.singleData.tmax += self.tstep.value()  
        self.singleData.writeProperty(False)    

    @processGeneral
    def OnCropSpec(self, flag):
        x0 = self.xlow.value()
        x1 = self.xhigh.value()
        y0 = self.ylow.value()
        y1 = self.yhigh.value()
        Data.crop(self.singleData, x0, x1, y0, y1)

    def OnMerge(self, flag):
        if self.singleData.dims == 1:
            pass
        elif self.singleData.dims == 2:
            self.Merge2D_wrapper()
        elif self.singleData.dims == 3:
            self.Merge3D_wrapper()

    @processGeneral
    def Merge2D_wrapper(self):
        xnum = self.xnum.value()
        ynum = self.ynum.value()
        Data.merge2D(self.singleData, xnum, ynum)

    @process3D
    def Merge3D_wrapper(self):
        xnum = self.xnum.value()
        ynum = self.ynum.value()
        znum = self.znum.value()
        Data.merge3D(self.singleData, xnum, ynum, znum)
    
    @process2D
    def transpose2D(self, flag):
        Data.transpose2D(self.singleData)
        self.set2DEnergyAxis(self.singleData.energyAxis)

    @process2D
    def mirror2D(self, flag):
        if self.sender() == self.mirrorXButton:
            Data.mirror2D(self.singleData, 'X')
        elif self.sender() == self.mirrorYButton:
            Data.mirror2D(self.singleData, 'Y')

    @process2D
    def normal2D(self, flag):
        if self.sender() == self.normalXDCButton:
            Data.normal2D(self.singleData, 'X')
        elif self.sender() == self.normalYDCButton:
            Data.normal2D(self.singleData, 'Y')

    @process2D
    def Tokspace2D(self, flag):
        if self.xaxis_2D_energy.isChecked():
            if Data.Tokspace2D(self.singleData, 'X') == 0:
                if self.singleData.energyAxis == None:
                    self.singleData.energyAxis = 'X'
        else:
            if Data.Tokspace2D(self.singleData, 'Y') == 0:
                if self.singleData.energyAxis == None:
                    self.singleData.energyAxis = 'Y'

    @process3D
    def transpose3D(self, flag):
        Data.transpose3D(self.singleData)
        #self.set2DEnergyAxis(self.singleData.energyAxis)

    @process3D
    def changeZAxis(self, flag):
        if self.sender() == self.YZXButton3D:
            Data.changeZAxis3D(self.singleData, 'X')
            #self.set2DEnergyAxis(self.singleData.energyAxis)
        elif self.sender() == self.ZXYButton3D:
            Data.changeZAxis3D(self.singleData, 'Y')
            #self.set2DEnergyAxis(self.singleData.energyAxis)

    @process3D
    def mirror3D(self, flag):
        if self.sender() == self.mirrorXButton3D:
            Data.mirror3D(self.singleData, 'X')
        elif self.sender() == self.mirrorYButton3D:
            Data.mirror3D(self.singleData, 'Y')

    @process3D_T
    def Tokspace3D(self, flag):
        dlg = waitingDialog(self.Win)
        dlg.progress.setValue(0)
        s = signal()
        s.progress.connect(dlg.progress.setValue)
        s.finished.connect(dlg.FinishedSlot)
        s.stoped.connect(dlg.StopedSlot)
        if self.sender() == self.theta3DButton_3D:
            if self.slit_h_3D.isChecked():
                t = Data.ThetaKspace3D(self.singleData, 'H', self.bias_3D.value(), dlg, self.core_num, self.solver_max_iteration_step, self.solver_error, os.getpid(), s)
            else:
                t = Data.ThetaKspace3D(self.singleData, 'V', self.bias_3D.value(), dlg, self.core_num, self.solver_max_iteration_step, self.solver_error, os.getpid(), s)
        t.start()
        return dlg.exec_()

    def changeAspect2D(self, state):
        if state == 2:
            self.Win.ImageViewer.twoDimage.changeAspect(True)
        elif state == 0:
            self.Win.ImageViewer.twoDimage.changeAspect(False)

    def changeAspect3D(self, state):
        if state == 2:
            self.Win.ImageViewer.threeDblock.changeAspect(True)
        elif state == 0:
            self.Win.ImageViewer.threeDblock.changeAspect(False)

    def OpenDevSetting(self, state):
        if state == 2:
            self.DevWin.exec_()
            self.DevSetting.setCheckState(0)

    def SaveData(self):
        self.singleData.Save()
        #self.Win.DataBrowser.InfoList.setProperty(self.singleData.property)
        #self.Win.ImageViewer.setData(self.singleData)
        self.saveButton.setEnabled(False)

    def RestoreData(self):
        self.singleData.Restore()
        self.Win.DataBrowser.InfoList.setProperty(self.singleData.property)
        self.Win.setData(self.singleData)
        self.saveButton.setEnabled(False)


class MultipleTab(QScrollArea):
    def __init__(self, Win):
        super(MultipleTab, self).__init__()

        self.Win = Win

        box = QVBoxLayout()
        box.setSizeConstraint(QLayout.SetFixedSize)

        self.label = QLabel("Process")
        box.addWidget(self.label)

        container = QWidget()
        container.setLayout(box)

        self.setWidget(container)
        self.setStyleSheet("QScrollArea {background-color:white; border: 0px}")

    def updateUI(self, data):
        if data == None:
            self.setEnabled(False)
        elif not self.Win.DataBrowser.DataList.SelectionMode:
            pass


class waitingDialog(QDialog):
    def __init__(self, parent):
        super(waitingDialog, self).__init__(parent=parent)
        self.resize(200, 200)
        self.setWindowFlags(Qt.ToolTip)
        palette = QPalette()
        palette.setColor(QPalette.Background, Qt.white)
        self.setPalette(palette)
        movie = QMovie("./image/waiting.gif")
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setMovie(movie)
        self.progress = QProgressBar()
        self.progress.setRange(0,1000)
        self.progress.setValue(1000)
        self.progress.setStyle(QStyleFactory.create('Fusion'))
        movie.start()
        box = QVBoxLayout()
        box.addWidget(label)
        box.addWidget(self.progress)
        self.setLayout(box)
        self.setWindowOpacity(0.85)

    def FinishedSlot(self):
        self.accept()

    def StopedSlot(self, value):
        self.reject()
        if value == 0:
            QMessageBox.information(None, "Error", "The Data scale may be wrong.", QMessageBox.Ok)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.position = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            newposition = event.globalPos()
            self.move(self.pos()+newposition-self.position)
            self.position = event.globalPos()


class DevSettingDialog(QDialog):
    def __init__(self, parent=None, core=6, mis=30, re=1e-7):
        super(DevSettingDialog, self).__init__(parent=parent)
        self.box = QVBoxLayout()
        self.parent = parent
        self.corenum = core
        self.mis = mis
        self.rel_error = re

        #parallel calculation
        self.para_group = QGroupBox("Parallel Calculation")
        self.coreLabel = QLabel("Core Number:")
        self.coreLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.core = QSpinBox()
        self.core.setFixedWidth(80)
        self.core.setRange(1, os.cpu_count())
        self.core.setValue(self.corenum)
        hbox_core = QHBoxLayout()
        hbox_core.addStretch(1)
        hbox_core.addWidget(self.coreLabel)
        hbox_core.addStretch(1)
        hbox_core.addWidget(self.core)
        vbox_para = QVBoxLayout()
        vbox_para.addLayout(hbox_core)
        self.para_group.setLayout(vbox_para)
        self.box.addWidget(self.para_group)

        #kspace solver parameters
        self.ks_solver_group = QGroupBox("k-space solver")
        self.max_iteration_step_label = QLabel("Max iteration step:")
        self.max_iteration_step_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.max_iteration_step = QSpinBox()
        self.max_iteration_step.setFixedWidth(80)
        self.max_iteration_step.setRange(1, 10000)
        self.max_iteration_step.setValue(self.mis)
        self.error_label = QLabel("Relative Error (*1e-7):")
        self.error_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.error = QDoubleSpinBox()
        self.error.setDecimals(5)
        self.error.setFixedWidth(80)
        self.error.setRange(0, 1e8)
        self.error.setValue(self.rel_error*1e7)
        hbox_mis = QHBoxLayout()
        hbox_mis.addStretch(1)
        hbox_mis.addWidget(self.max_iteration_step_label)
        hbox_mis.addStretch(1)
        hbox_mis.addWidget(self.max_iteration_step)
        hbox_error = QHBoxLayout()
        hbox_error.addStretch(1)
        hbox_error.addWidget(self.error_label)
        hbox_error.addStretch(1)
        hbox_error.addWidget(self.error)
        vbox_kspace = QVBoxLayout()
        vbox_kspace.addLayout(hbox_mis)
        vbox_kspace.addLayout(hbox_error)
        self.ks_solver_group.setLayout(vbox_kspace)
        self.box.addWidget(self.ks_solver_group)

        #setting button
        self.OKButton = QPushButton("Set")
        self.OKButton.clicked.connect(self.OnSet)
        self.CancelButton = QPushButton("Cancel")
        self.CancelButton.clicked.connect(self.OnCancel)
        hbox_setting = QHBoxLayout()
        hbox_setting.addStretch(1)
        hbox_setting.addWidget(self.OKButton)
        hbox_setting.addWidget(self.CancelButton)
        self.box.addLayout(hbox_setting)

        self.setWindowTitle("Developer Setting")
        self.setLayout(self.box)
        self.setFixedSize(300, self.minimumHeight())
        self.position = self.pos()

    def OnSet(self, flag):
        self.parent.core_num = self.core.value()
        self.parent.solver_max_iteration_step = self.max_iteration_step.value()
        self.parent.solver_error = self.error.value()*1e-7
        self.accept()

    def OnCancel(self, flag):
        self.core.setValue(self.parent.core_num)
        self.max_iteration_step.setValue(self.parent.solver_max_iteration_step)
        self.error.setValue(self.parent.solver_error*1e7)
        self.reject()

    def closeEvent(self, event):
        self.core.setValue(self.parent.core_num)
        self.max_iteration_step.setValue(self.parent.solver_max_iteration_step)
        self.error.setValue(self.parent.solver_error*1e7)


class signal(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    stoped = pyqtSignal(int)

