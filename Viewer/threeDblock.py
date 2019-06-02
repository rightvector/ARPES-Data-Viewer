'''
3D Block Viewer Module
'''

import matplotlib
matplotlib.use('qt5Agg')
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NTBar)
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import NullFormatter
from matplotlib.lines import Line2D
from matplotlib import cm
from matplotlib.colors import ListedColormap
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QDoubleSpinBox, QSpinBox, QSlider, 
QSizePolicy, QStyleFactory, QFrame, QPushButton, QComboBox, QCheckBox, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QCursor
from Data import Spectrum
from Viewer.Selector import Selector3D
from Viewer.colormap import CustomComboBox
import glob, os, copy
import numpy as np


class threeDblock(QWidget):
    def __init__(self, viewer):
        super(threeDblock, self).__init__()
        self.data = Spectrum()
        self.viewer = viewer
        self.aspect = "auto"

        #init block view
        self.fig = Figure(figsize=(3, 3), dpi=150)
        gs = GridSpec(11, 11, figure=self.fig)
        self.ax_Xcut = self.fig.add_subplot(gs[:3, 2:8])  # 1st argument is for row, 2nd argument is for column
        self.ax_Ycut = self.fig.add_subplot(gs[3:9, 8:])
        self.ax_Zcut = self.fig.add_subplot(gs[3:9, 2:8])
        self.ax_YDC = self.fig.add_subplot(gs[3:9, :2])
        self.ax_XDC = self.fig.add_subplot(gs[9:, 2:8])
        self.ax_ZDC1 = self.fig.add_subplot(gs[:3, :2])
        self.ax_ZDC2 = self.fig.add_subplot(gs[9:, 8:])
        self.ax_cmap = self.fig.add_subplot(gs[:3, 8:])
        self.fig.subplots_adjust(top=0.96, bottom=0.08, left=0.1, right=0.96, wspace=0.2, hspace=0.2)
        #self.ax_Xcut.xaxis.set_major_formatter(NullFormatter())
        #self.ax_Xcut.yaxis.set_major_formatter(NullFormatter())
        self.ax_Xcut.tick_params(direction='inout', labelsize=8.5, labelleft=False, labelbottom=False) # no tick label
        #self.ax_Ycut.xaxis.set_major_formatter(NullFormatter())
        #self.ax_Ycut.yaxis.set_major_formatter(NullFormatter())
        self.ax_Ycut.tick_params(direction='inout', labelsize=8.5, labelleft=False, labelbottom=False)
        #self.ax_Zcut.xaxis.set_major_formatter(NullFormatter())
        #self.ax_Zcut.yaxis.set_major_formatter(NullFormatter())
        self.ax_Zcut.tick_params(direction='inout', labelsize=8.5, labelleft=False, labelbottom=False)
        self.ax_XDC.tick_params(axis='x', labelsize=8.5)
        self.ax_XDC.tick_params(axis='y', which='both', left=False, labelleft=False)  # set no tick and tick label
        self.ax_YDC.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
        self.ax_YDC.tick_params(axis='y', labelsize=8.5)
        self.ax_ZDC1.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
        self.ax_ZDC1.tick_params(axis='y', labelsize=8.5)
        self.ax_ZDC2.tick_params(axis='x', labelsize=8.5)
        self.ax_ZDC2.tick_params(axis='y', which='both', left=False, labelleft=False)
        self.ax_YDC.invert_xaxis()
        self.ax_ZDC1.invert_xaxis()
        x0, y0, width, height = self.ax_cmap.get_position().bounds
        nheight = height*0.2
        ny0 = y0+height*0.5*(1-0.2)
        self.ax_cmap.set_position([x0, ny0, width, nheight])
        self.ax_cmap.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
        self.ax_cmap.set_title("Color Scale", {'fontsize': 10}, fontname="Comic Sans Ms")
        self.gradient = np.vstack((np.linspace(0, 1, 256), np.linspace(0, 1, 256)))
        self.setTickLabelFont(self.ax_Xcut, "Comic Sans MS")
        self.setTickLabelFont(self.ax_Ycut, "Comic Sans MS")
        self.setTickLabelFont(self.ax_Zcut, "Comic Sans MS")
        self.setTickLabelFont(self.ax_XDC, "Comic Sans MS")
        self.setTickLabelFont(self.ax_YDC, "Comic Sans MS")
        self.setTickLabelFont(self.ax_ZDC1, "Comic Sans MS")
        self.setTickLabelFont(self.ax_ZDC2, "Comic Sans MS")
        self.canvas = FigureCanvas(self.fig)
        self.fig.patch.set_facecolor("None")
        self.canvas.setStyleSheet("background-color:transparent;")
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.GetBbox()
        self.XDCLine = Line2D(np.array([0]), np.array([0]), color="blue", linewidth=1, animated=True, solid_joinstyle="round")
        self.YDCLine = Line2D(np.array([0]), np.array([0]), color="red", linewidth=1, animated=True, solid_joinstyle="round")
        self.ZDCLine1 = Line2D(np.array([0]), np.array([0]), color="green", linewidth=1, animated=True, solid_joinstyle="round")
        self.ZDCLine2 = Line2D(np.array([0]), np.array([0]), color="green", linewidth=1, animated=True, solid_joinstyle="round")
        self.ax_XDC.add_line(self.XDCLine)
        self.ax_YDC.add_line(self.YDCLine)
        self.ax_ZDC1.add_line(self.ZDCLine1)
        self.ax_ZDC2.add_line(self.ZDCLine2)
        self.cid_scroll = self.canvas.mpl_connect('scroll_event', self.OnClimb)
        self.cid_keypress = self.canvas.mpl_connect('key_press_event', self.OnKeyPress)
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.OnPress)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.OnRelease)

        #cursor
        self.ZcutXline1 = self.ax_Zcut.axhline(self.ax_Zcut.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75) 
        self.ZcutYline1 = self.ax_Zcut.axvline(self.ax_Zcut.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.ZcutXline2 = self.ax_Zcut.axhline(self.ax_Zcut.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  
        self.ZcutYline2 = self.ax_Zcut.axvline(self.ax_Zcut.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  
        self.XcutXline1 = self.ax_Xcut.axhline(self.ax_Xcut.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  
        self.XcutYline1 = self.ax_Xcut.axvline(self.ax_Xcut.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.XcutXline2 = self.ax_Xcut.axhline(self.ax_Xcut.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.XcutYline2 = self.ax_Xcut.axvline(self.ax_Xcut.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.YcutXline1 = self.ax_Ycut.axhline(self.ax_Ycut.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.YcutYline1 = self.ax_Ycut.axvline(self.ax_Ycut.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.YcutXline2 = self.ax_Ycut.axhline(self.ax_Ycut.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.YcutYline2 = self.ax_Ycut.axvline(self.ax_Ycut.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.XDCCursor = self.ax_XDC.axvline(self.ax_XDC.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.YDCCursor = self.ax_YDC.axhline(self.ax_YDC.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.ZDC1Cursor = self.ax_ZDC1.axhline(self.ax_ZDC1.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.ZDC2Cursor = self.ax_ZDC2.axvline(self.ax_ZDC2.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)

        #selector
        self.selector = Selector3D(self.ax_Zcut, self.ax_Xcut, self.ax_Ycut, self.canvas)

        #contextMenu
        self.contextMenu = QMenu(self)
        self.CropAction = self.contextMenu.addAction("Crop")
        self.CropAction.setIcon(QIcon("./image/crop.ico"))
        self.CropAction.triggered.connect(self.crop)
        self.RestoreAction = self.contextMenu.addAction("Restore")
        self.RestoreAction.setIcon(QIcon("./image/restore.ico"))
        self.RestoreAction.triggered.connect(self.viewer.Win.DataProcessor.tab_single.RestoreData)
        self.SelectMenu = self.contextMenu.addMenu("Select")
        self.SelectMenu.setIcon(QIcon("./image/select.ico"))
        self.SelectX = self.SelectMenu.addAction("X Range")
        self.SelectX.triggered.connect(self.setSelectionRange)
        self.SelectY = self.SelectMenu.addAction("Y Range")
        self.SelectY.triggered.connect(self.setSelectionRange)
        self.SelectXY = self.SelectMenu.addAction("XY Area")
        self.SelectXY.triggered.connect(self.setSelectionRange)
        self.outputMenu = self.contextMenu.addMenu("Output")
        self.outputMenu.setIcon(QIcon("./image/output.ico"))
        self.zcut_action = self.outputMenu.addAction("Z Plane")
        self.zcut_action.triggered.connect(self.outputData)
        self.xcut_action = self.outputMenu.addAction("X Plane")
        self.xcut_action.triggered.connect(self.outputData)
        self.ycut_action = self.outputMenu.addAction("Y Plane")
        self.ycut_action.triggered.connect(self.outputData)
        self.XDC_action = self.outputMenu.addAction("XDC")
        self.YDC_action = self.outputMenu.addAction("YDC")
        self.ZDC_action = self.outputMenu.addAction("ZDC")
        
        #init Tool
        self.toolPanel = QGroupBox("Coordinate System")
        self.toolPanel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolPanel.setCheckable(True)
        self.toolPanel.setChecked(False)
        self.toolPanel.setStyle(QStyleFactory.create('Fusion'))
        self.toolPanel.toggled.connect(self.begincursor)
        self.X = QDoubleSpinBox()
        self.X.setFixedWidth(100)
        self.X.setDecimals(6)
        self.X.setRange(-1, 1)
        self.X.setSingleStep(0.01)
        self.X.setKeyboardTracking(False)
        self.X.setStyle(QStyleFactory.create('Fusion'))
        self.X.setValue(-1)
        self.X.valueChanged.connect(self.setXYValueFromSpinBox)
        self.XLabel = QLabel("X:")
        self.XLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Y = QDoubleSpinBox()
        self.Y.setFixedWidth(100)
        self.Y.setDecimals(6)
        self.Y.setRange(-1, 1)
        self.Y.setSingleStep(0.01)
        self.Y.setKeyboardTracking(False)
        self.Y.setStyle(QStyleFactory.create('Fusion'))
        self.Y.setValue(-1)
        self.Y.valueChanged.connect(self.setXYValueFromSpinBox)
        self.YLabel = QLabel("Y:")
        self.YLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Z = QDoubleSpinBox()
        self.Z.setFixedWidth(100)
        self.Z.setDecimals(6)
        self.Z.setRange(-1, 1)
        self.Z.setSingleStep(0.01)
        self.Z.setKeyboardTracking(False)
        self.Z.setStyle(QStyleFactory.create('Fusion'))
        self.Z.setValue(-1)
        self.Z.valueChanged.connect(self.setZValueFromSpinBox)
        self.ZLabel = QLabel("Z:")
        self.ZLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.IntLabel = QLabel("Count:")
        self.IntLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Int = QLabel("0")
        self.Int.setFont(font)
        self.Int.setMinimumWidth(100)
        self.Int.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.Int.setStyleSheet("QLabel {background-color: white;}")
        self.Int.setFrameStyle(QFrame.Panel)
        self.XSlider = QSlider(Qt.Horizontal)
        self.XSlider.setRange(0, 10000)
        self.XSlider.setStyle(QStyleFactory.create('Fusion'))
        self.XSlider.sliderMoved.connect(self.setValueFromSlider)
        self.XSLabel = QLabel("X:")
        self.YSlider = QSlider(Qt.Horizontal)
        self.YSlider.setRange(0, 10000)
        self.YSlider.setStyle(QStyleFactory.create('Fusion'))
        self.YSlider.sliderMoved.connect(self.setValueFromSlider)
        self.YSLabel = QLabel("Y:")
        self.ZSlider = QSlider(Qt.Horizontal)
        self.ZSlider.setRange(0, 10000)
        self.ZSlider.setStyle(QStyleFactory.create('Fusion'))
        self.ZSlider.sliderMoved.connect(self.setValueFromSlider)
        self.ZSLabel = QLabel("Z:")
        self.XSlice = QSpinBox()
        self.XSlice.setRange(1, 10000)
        self.XSlice.setSingleStep(2)
        self.XSlice.setFixedWidth(50)
        self.XSlice.setKeyboardTracking(False)
        self.XSlice.setStyle(QStyleFactory.create('Fusion'))
        self.XSlice.valueChanged.connect(self.setSlice)
        self.XSliceLabel = QLabel("Slice:")
        self.YSlice = QSpinBox()
        self.YSlice.setRange(1, 10000)
        self.YSlice.setSingleStep(2)
        self.YSlice.setFixedWidth(50)
        self.YSlice.setKeyboardTracking(False)
        self.YSlice.setStyle(QStyleFactory.create('Fusion'))
        self.YSlice.valueChanged.connect(self.setSlice)
        self.YSliceLabel = QLabel("Slice:")
        self.ZSlice = QSpinBox()
        self.ZSlice.setRange(1, 10000)
        self.ZSlice.setSingleStep(2)
        self.ZSlice.setFixedWidth(50)
        self.ZSlice.setKeyboardTracking(False)
        self.ZSlice.setStyle(QStyleFactory.create('Fusion'))
        self.ZSlice.valueChanged.connect(self.setSlice)
        self.ZSliceLabel = QLabel("Slice:")
        hbox_tool = QHBoxLayout()
        hbox_tool.addStretch(2)
        hbox_tool.addWidget(self.XLabel)
        hbox_tool.addWidget(self.X)
        hbox_tool.addStretch(1)
        hbox_tool.addWidget(self.YLabel)
        hbox_tool.addWidget(self.Y)
        hbox_tool.addStretch(1)
        hbox_tool.addWidget(self.ZLabel)
        hbox_tool.addWidget(self.Z)
        hbox_tool.addStretch(1)
        hbox_tool.addWidget(self.IntLabel)
        hbox_tool.addWidget(self.Int)
        hbox_tool.addStretch(2)
        hbox2_tool = QHBoxLayout()
        hbox2_tool.addWidget(self.XSLabel, 0)
        hbox2_tool.addWidget(self.XSlider, 1)
        hbox2_tool.addWidget(self.XSliceLabel, 0)
        hbox2_tool.addWidget(self.XSlice, 0)
        hbox2_tool.addWidget(self.YSLabel, 0)
        hbox2_tool.addWidget(self.YSlider, 1)
        hbox2_tool.addWidget(self.YSliceLabel, 0)
        hbox2_tool.addWidget(self.YSlice, 0)
        hbox3_tool = QHBoxLayout()
        hbox3_tool.addWidget(self.ZSLabel)
        hbox3_tool.addWidget(self.ZSlider)
        hbox3_tool.addWidget(self.ZSliceLabel)
        hbox3_tool.addWidget(self.ZSlice)
        vbox_tool = QVBoxLayout()
        vbox_tool.addLayout(hbox_tool)
        vbox_tool.addLayout(hbox2_tool)
        vbox_tool.addLayout(hbox3_tool)
        self.toolPanel.setLayout(vbox_tool)

        #color scale
        self.colorPanel = QGroupBox("Color Scale")
        self.colorPanel.setFixedHeight(80)
        self.colorPanel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmapmenu = CustomComboBox()
        self.cmapmenu.setFixedWidth(120)
        self.cmapmenu.setStyle(QStyleFactory.create('Fusion'))
        self.cmapmenu.setCurrentText("twilight")
        self.cmapmenu.currentIndexChanged.connect(self.changecmapbyindex)
        self.revcmap = QCheckBox("R")
        self.revcmap.stateChanged.connect(self.reversecmap)
        self.GammaLabel = QLabel("Gamma:")
        self.GammaLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Gamma = QDoubleSpinBox()
        self.Gamma.setFixedWidth(100)
        self.Gamma.setDecimals(3)
        self.Gamma.setRange(0.05, 20)
        self.Gamma.setSingleStep(0.01)
        self.Gamma.setValue(1)
        self.Gamma.setKeyboardTracking(False)
        self.Gamma.valueChanged.connect(self.setGammaFromSpinBox)
        self.Gamma.setStyle(QStyleFactory.create('Fusion'))
        self.GSlider = QSlider(Qt.Horizontal)
        self.GSlider.setRange(1000000*np.log(0.05), 1000000*np.log(20))
        self.GSlider.setValue(0)
        self.GSlider.sliderMoved.connect(self.setGammaFromSlider)
        self.GSlider.setStyle(QStyleFactory.create('Fusion'))
        hbox_cmap = QHBoxLayout()
        hbox_cmap.addWidget(self.cmapmenu)
        hbox_cmap.addWidget(self.GammaLabel)
        hbox_cmap.addWidget(self.Gamma)
        hbox_cmap.addWidget(self.GSlider)
        hbox_cmap.addWidget(self.revcmap)
        self.colorPanel.setLayout(hbox_cmap)
        self.colorPanel.setEnabled(False)

        #Layout
        box = QVBoxLayout()
        box.addWidget(self.toolPanel, 0)
        box.addWidget(self.canvas, 1)
        box.addWidget(self.colorPanel, 0)
        self.setLayout(box)

    def loaddata(self, data):
        self.canvas.draw()
        self.GetWhiteBackground()
        self.selector.set_visible(False)
        self.data = data
        self.Zcut = data.data[:,:,0]
        self.Xcut = data.data[:,0,:]
        self.Ycut = data.data[0,:,:]
        self.ZDC = data.data[0,0,:]
        self.XDC = data.data[:,0,0]
        self.YDC = data.data[0,:,0]
        self.X.disconnect()
        self.Y.disconnect()
        self.Z.disconnect()
        self.X.setRange(data.xmin, data.xmax)
        self.X.setSingleStep(data.xstep)
        self.Y.setRange(data.ymin, data.ymax)
        self.Y.setSingleStep(data.ystep)
        self.Z.setRange(data.zmin, data.zmax)
        self.Z.setSingleStep(data.zstep)
        self.X.valueChanged.connect(self.setXYValueFromSpinBox)
        self.Y.valueChanged.connect(self.setXYValueFromSpinBox)
        self.Z.valueChanged.connect(self.setZValueFromSpinBox)
        self.XSlice.setRange(1, self.data.dimension[0])
        self.YSlice.setRange(1, self.data.dimension[1])
        self.ZSlice.setRange(1, self.data.dimension[2])
        newX = 0
        if data.xmin*data.xmax < 0:
            newX = 0
        else:
            newX = (data.xmin+data.xmax)/2
        if round(newX, 6) == self.X.value():
            self.X.valueChanged.emit(newX)
        else:
            self.X.setValue(newX)
        newY = 0
        if data.ymin*data.ymax < 0:
            newY = 0
        else:
            newY = (data.ymin+data.ymax)/2          
        if round(newY, 6) == self.Y.value():
            self.Y.valueChanged.emit(newY)
        else:
            self.Y.setValue(newY)
        newZ = 0
        if data.zmin*data.zmax < 0:
            newZ = 0
        else:
            newZ = (data.zmin+data.zmax)/2       
        if round(newZ, 6) == self.Z.value():
            self.Z.valueChanged.emit(newZ)
        else:
            self.Z.setValue(newZ)
        self.updatecolorscale(self.getcurrentcmap())
        self.updateAxesPosition(True)
        self.colorPanel.setEnabled(True)

    def setValueFromSlider(self, value):
        if self.sender() == self.XSlider:
            self.X.valueChanged.disconnect()
            xvalue = value*(self.X.maximum()-self.X.minimum())/10000+self.X.minimum()
            self.setXYValue(xvalue, self.Y.value(), False)
            self.X.setValue(xvalue)
            self.X.valueChanged.connect(self.setXYValueFromSpinBox)
        elif self.sender() == self.YSlider:
            self.Y.valueChanged.disconnect()
            yvalue = value*(self.Y.maximum()-self.Y.minimum())/10000+self.Y.minimum()
            self.setXYValue(self.X.value(), yvalue, False)
            self.Y.setValue(yvalue)
            self.Y.valueChanged.connect(self.setXYValueFromSpinBox)
        elif self.sender() == self.ZSlider:
            self.Z.setValue(value*(self.Z.maximum()-self.Z.minimum())/10000+self.Z.minimum())

    def setZValueFromSpinBox(self, value):
        self.ZSlider.setValue((value-self.Z.minimum())/(self.Z.maximum()-self.Z.minimum())*10000)
        half_wid_num = (self.ZSlice.value()-1)/2
        self.XcutXline1.set_ydata(value-self.data.zstep*half_wid_num)
        self.XcutXline2.set_ydata(value+self.data.zstep*half_wid_num)
        self.YcutYline1.set_xdata(value-self.data.zstep*half_wid_num)
        self.YcutYline2.set_xdata(value+self.data.zstep*half_wid_num)
        self.ZDC1Cursor.set_ydata(value)
        self.ZDC2Cursor.set_xdata(value)
        self.Zcut = self.get_Zcut(value)
        self.XDC = self.get_XDC(self.Y.value())
        self.YDC = self.get_YDC(self.X.value())
        self.plotZcut(self.getcurrentcmap(), True)
        self.plotXDC()
        self.plotYDC()
        self.plotZDC()
        self.plotArtist()
        self.setIntensity()

    def setXYValueFromSpinBox(self, value):
        if self.sender() == self.X:
            self.setXYValue(value, self.Y.value(), True)
        elif self.sender() == self.Y:
            self.setXYValue(self.X.value(), value, True)

    def setXYValue(self, xvalue, yvalue, moveslider):
        if moveslider:
            self.XSlider.setValue((xvalue-self.X.minimum())/(self.X.maximum()-self.X.minimum())*10000)
            self.YSlider.setValue((yvalue-self.Y.minimum())/(self.Y.maximum()-self.Y.minimum())*10000)
        half_wid_xnum = (self.XSlice.value()-1)/2
        half_wid_ynum = (self.YSlice.value()-1)/2
        self.ZcutYline1.set_xdata(xvalue-self.data.xstep*half_wid_xnum)
        self.ZcutYline2.set_xdata(xvalue+self.data.xstep*half_wid_xnum)
        self.XcutYline1.set_xdata(xvalue-self.data.xstep*half_wid_xnum)
        self.XcutYline2.set_xdata(xvalue+self.data.xstep*half_wid_xnum)
        self.XDCCursor.set_xdata(xvalue)
        self.ZcutXline1.set_ydata(yvalue-self.data.ystep*half_wid_ynum)
        self.ZcutXline2.set_ydata(yvalue+self.data.ystep*half_wid_ynum)
        self.YcutXline1.set_ydata(yvalue-self.data.ystep*half_wid_ynum)
        self.YcutXline2.set_ydata(yvalue+self.data.ystep*half_wid_ynum)
        self.YDCCursor.set_ydata(yvalue)
        self.Xcut = self.get_Xcut(yvalue)
        self.Ycut = self.get_Ycut(xvalue)
        self.XDC = self.get_XDC(yvalue)
        self.YDC = self.get_YDC(xvalue)
        self.ZDC = self.get_ZDC(xvalue)
        self.plotXcut(self.getcurrentcmap(), True)
        self.plotYcut(self.getcurrentcmap(), True)
        self.plotYDC()
        self.plotZDC()
        self.plotXDC()
        self.plotArtist()
        self.setIntensity()

    def setSlice(self, value):
        if self.sender() == self.ZSlice:
            if value % 2 == 0:
                self.ZSlice.setValue(value-1)
            else:
                if value == 1:
                    self.XcutXline2.set_visible(False)
                    self.YcutYline2.set_visible(False)
                else:
                    self.XcutXline2.set_visible(True)
                    self.YcutYline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.XcutXline1.set_ydata(self.Z.value()-self.data.zstep*half_wid_num)
                self.XcutXline2.set_ydata(self.Z.value()+self.data.zstep*half_wid_num)
                self.YcutYline1.set_xdata(self.Z.value()-self.data.zstep*half_wid_num)
                self.YcutYline2.set_xdata(self.Z.value()+self.data.zstep*half_wid_num)
                self.Zcut = self.get_Zcut(self.Z.value())
                self.XDC = self.get_XDC(self.Y.value())
                self.YDC = self.get_YDC(self.X.value())
                self.plotZcut(self.getcurrentcmap(), True)
                self.plotXDC()
                self.plotYDC()
                self.plotArtist()
                self.setIntensity()
        elif self.sender() == self.XSlice:
            if value % 2 == 0:
                self.XSlice.setValue(value-1)
            else:
                if value == 1:
                    self.ZcutYline2.set_visible(False)
                    self.XcutYline2.set_visible(False)
                else:
                    self.ZcutYline2.set_visible(True)
                    self.XcutYline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.ZcutYline1.set_xdata(self.X.value()-self.data.xstep*half_wid_num)
                self.ZcutYline2.set_xdata(self.X.value()+self.data.xstep*half_wid_num)
                self.XcutYline1.set_xdata(self.X.value()-self.data.xstep*half_wid_num)
                self.XcutYline2.set_xdata(self.X.value()+self.data.xstep*half_wid_num)
                self.Ycut = self.get_Ycut(self.X.value())
                self.YDC = self.get_YDC(self.X.value())
                self.ZDC = self.get_ZDC(self.X.value())
                self.plotYcut(self.getcurrentcmap(), True)
                self.plotYDC()
                self.plotZDC()
                self.plotArtist()
                self.setIntensity()
        elif self.sender() == self.YSlice:
            if value % 2 == 0:
                self.YSlice.setValue(value-1)
            else:
                if value == 1:
                    self.ZcutXline2.set_visible(False)
                    self.YcutXline2.set_visible(False)
                else:
                    self.ZcutXline2.set_visible(True)
                    self.YcutXline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.ZcutXline1.set_ydata(self.Y.value()-self.data.ystep*half_wid_num)
                self.ZcutXline2.set_ydata(self.Y.value()+self.data.ystep*half_wid_num)
                self.YcutXline1.set_ydata(self.Y.value()-self.data.ystep*half_wid_num)
                self.YcutXline2.set_ydata(self.Y.value()+self.data.ystep*half_wid_num)
                self.Xcut = self.get_Xcut(self.Y.value())
                self.XDC = self.get_XDC(self.Y.value())
                self.ZDC = self.get_ZDC(self.X.value())
                self.plotXcut(self.getcurrentcmap(), True)
                self.plotXDC()
                self.plotZDC()
                self.plotArtist()
                self.setIntensity()

    def scale2pnt(self, value, scale):
        return (np.abs(scale - value)).argmin()

    def setTickLabelFont(self, ax, font):
        for tick in ax.get_xticklabels():
            tick.set_fontname(font)
        for tick in ax.get_yticklabels():
            tick.set_fontname(font)

    def setIntensity(self):
        intensity = self.get_intensity(self.X.value(), self.Y.value(), self.Z.value())
        if np.isnan(intensity):
            self.Int.setText("NaN")
        elif np.abs(intensity) >= 0.01:
            self.Int.setText("%.2f" % intensity)
        else:
            self.Int.setText("%.2e" % intensity)

    def get_intensity(self, xvalue, yvalue, zvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        zidx = self.scale2pnt(zvalue, self.data.zscale)
        half_wid_xnum = int((self.XSlice.value()-1)/2)
        half_wid_ynum = int((self.YSlice.value()-1)/2)
        half_wid_znum = int((self.ZSlice.value()-1)/2)
        if xidx < half_wid_xnum:
            xminidx = 0
        else:
            xminidx = xidx-half_wid_xnum
        xmaxidx = xidx+half_wid_xnum+1
        if yidx < half_wid_ynum:
            yminidx = 0
        else:
            yminidx = yidx-half_wid_ynum
        ymaxidx = yidx+half_wid_ynum+1
        if zidx < half_wid_znum:
            zminidx = 0
        else:
            zminidx = zidx-half_wid_znum
        zmaxidx = zidx+half_wid_znum+1
        return self.data.data[xminidx:xmaxidx, yminidx:ymaxidx, zminidx:zmaxidx].sum()
    
    def get_Zcut(self, zvalue):
        zidx = self.scale2pnt(zvalue, self.data.zscale)
        if self.ZSlice.value() == 1:
            return self.data.data[:, :, zidx]
        else:
            half_wid_num = int((self.ZSlice.value()-1)/2)
            if zidx < half_wid_num:
                array = self.data.data[:, :, 0:zidx+half_wid_num+1]
            else:
                array = self.data.data[:, :, zidx-half_wid_num:zidx+half_wid_num+1]
            return np.sum(array, axis=2)

    def get_Xcut(self, yvalue):
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        if self.YSlice.value() == 1:
            return self.data.data[:, yidx, :]
        else:
            half_wid_num = int((self.YSlice.value()-1)/2)
            if yidx < half_wid_num:
                array = self.data.data[:, 0:yidx+half_wid_num+1, :]
            else:
                array = self.data.data[:, yidx-half_wid_num:yidx+half_wid_num+1, :]
            return np.sum(array, axis=1)

    def get_Ycut(self, xvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        if self.XSlice.value() == 1:
            return self.data.data[xidx, :, :]
        else:
            half_wid_num = int((self.XSlice.value()-1)/2)
            if xidx < half_wid_num:
                array = self.data.data[0:xidx+half_wid_num+1, :, :]
            else:
                array = self.data.data[xidx-half_wid_num:xidx+half_wid_num+1, :, :]
            return np.sum(array, axis=0)

    def get_XDC(self, yvalue):
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        if self.YSlice.value() == 1:
            return self.Zcut[:, yidx]
        else:
            half_wid_ynum = int((self.YSlice.value()-1)/2)
            if yidx < half_wid_ynum:
                ystart = 0
            else:
                ystart = yidx - half_wid_ynum
            yend = yidx + half_wid_ynum + 1
            array = self.Zcut[:, ystart:yend]
            return np.sum(array, axis=1)

    def get_YDC(self, xvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        if self.XSlice.value() == 1:
            return self.Zcut[xidx, :]
        else:
            half_wid_xnum = int((self.XSlice.value()-1)/2)
            if xidx < half_wid_xnum:
                xstart = 0
            else:
                xstart = xidx - half_wid_xnum
            xend = xidx + half_wid_xnum + 1
            array = self.Zcut[xstart:xend, :]
            return np.sum(array, axis=0)

    def get_ZDC(self, xvalue):  # the ZDC is obtained from Xcut. It is equivalent to obtain from Ycut
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        if self.XSlice.value() == 1:
            return self.Xcut[xidx, :]
        else:
            half_wid_xnum = int((self.XSlice.value()-1)/2)
            if xidx < half_wid_xnum:
                xstart = 0
            else:
                xstart = xidx - half_wid_xnum
            xend = xidx + half_wid_xnum + 1
            array = self.Xcut[xstart:xend, :]
            return np.sum(array, axis=0)

    def GetBbox(self):
        self.Zcutbbox = self.ax_Zcut.get_window_extent()
        self.Xcutbbox = self.ax_Xcut.get_window_extent()
        self.Ycutbbox = self.ax_Ycut.get_window_extent()
        self.XDCbbox = self.ax_XDC.get_window_extent()
        self.YDCbbox = self.ax_YDC.get_window_extent()
        self.ZDC1bbox = self.ax_ZDC1.get_window_extent()
        self.ZDC2bbox = self.ax_ZDC2.get_window_extent()

    def GetWhiteBackground(self):
        self.GetBbox()
        self.ax_XDC.redraw_in_frame()
        self.canvas.blit(self.XDCbbox)
        self.ax_YDC.redraw_in_frame()
        self.canvas.blit(self.YDCbbox)
        self.ax_ZDC1.redraw_in_frame()
        self.canvas.blit(self.ZDC1bbox)
        self.ax_ZDC2.redraw_in_frame()
        self.canvas.blit(self.ZDC2bbox)
        self.background_XDC = self.canvas.copy_from_bbox(self.XDCbbox)
        self.background_YDC = self.canvas.copy_from_bbox(self.YDCbbox)
        self.background_ZDC1 = self.canvas.copy_from_bbox(self.ZDC1bbox)
        self.background_ZDC2 = self.canvas.copy_from_bbox(self.ZDC2bbox)
        self.background_Zcut = self.canvas.copy_from_bbox(self.Zcutbbox)
        self.background_Xcut = self.canvas.copy_from_bbox(self.Xcutbbox)
        self.background_Ycut = self.canvas.copy_from_bbox(self.Ycutbbox)

    def getcurrentcmap(self):
        cmap_str = self.cmapmenu.currentText()
        if self.revcmap.checkState() == Qt.Checked:
            cmap_str += "_r"
        raw_cmap = cm.get_cmap(cmap_str, 256)
        linearIndex = np.linspace(0, 1, 256)
        nonlinearIndex = np.power(linearIndex, self.Gamma.value())
        new_cmap = ListedColormap(raw_cmap(nonlinearIndex))
        return new_cmap

    def updatecolorscale(self, cmap):
        for img in self.ax_cmap.get_images():
            img.remove()
        self.cmapimage = self.ax_cmap.imshow(self.gradient, cmap=cmap, origin="lower", aspect="auto")
        self.ax_cmap.redraw_in_frame()
        self.canvas.blit(self.ax_cmap.bbox)

    def setGammaFromSpinBox(self, value):
        self.updatecolorscale(self.getcurrentcmap(), True)
        self.plotZcut(self.getcurrentcmap(), True)
        self.plotXcut(self.getcurrentcmap(), True)
        self.plotYcut(self.getcurrentcmap(), True)
        self.plotArtist()
        self.GSlider.setValue(1000000*np.log(value))

    def setGammaFromSlider(self, value):
        self.Gamma.setValue(np.exp(value/1000000))

    def changecmapbyindex(self, index):
        self.updatecolorscale(self.getcurrentcmap(), True)
        self.plotZcut(self.getcurrentcmap(), True)
        self.plotXcut(self.getcurrentcmap(), True)
        self.plotYcut(self.getcurrentcmap(), True)
        self.plotArtist()

    def reversecmap(self, state):
        self.updatecolorscale(self.getcurrentcmap(), True)
        self.plotZcut(self.getcurrentcmap(), True)
        self.plotXcut(self.getcurrentcmap(), True)
        self.plotYcut(self.getcurrentcmap(), True)
        self.plotArtist()

    def begincursor(self, on):
        if on:
            self.ZcutXline1.set_visible(True)
            self.ZcutYline1.set_visible(True)
            self.XcutXline1.set_visible(True)
            self.XcutYline1.set_visible(True)
            self.YcutXline1.set_visible(True)
            self.YcutYline1.set_visible(True)
            if self.YSlice.value() > 1:
                self.ZcutXline2.set_visible(True)
                self.YcutXline2.set_visible(True)
            if self.XSlice.value() > 1:
                self.ZcutYline2.set_visible(True)
                self.XcutYline2.set_visible(True)
            if self.ZSlice.value() > 1:
                self.XcutXline2.set_visible(True)
                self.YcutYline2.set_visible(True)
            self.XDCCursor.set_visible(True)
            self.YDCCursor.set_visible(True)
            self.ZDC1Cursor.set_visible(True)
            self.ZDC2Cursor.set_visible(True)
            self.plotXDC()
            self.plotYDC()
            self.plotZDC()
            self.plotArtist()
            self.cid_mouse = self.canvas.mpl_connect('motion_notify_event', self.navigate)
            self.cid_key = self.canvas.mpl_connect('key_press_event', self.navigate)
        else:
            self.ZcutXline1.set_visible(False)
            self.ZcutYline1.set_visible(False)
            self.XcutXline1.set_visible(False)
            self.XcutYline1.set_visible(False)
            self.YcutXline1.set_visible(False)
            self.YcutYline1.set_visible(False)
            self.ZcutXline2.set_visible(False)
            self.YcutXline2.set_visible(False)
            self.ZcutYline2.set_visible(False)
            self.XcutYline2.set_visible(False)
            self.XcutXline2.set_visible(False)
            self.YcutYline2.set_visible(False)
            self.XDCCursor.set_visible(False)
            self.YDCCursor.set_visible(False)
            self.ZDC1Cursor.set_visible(False)
            self.ZDC2Cursor.set_visible(False)
            self.plotXDC()
            self.plotYDC()
            self.plotZDC()
            self.plotArtist()
            self.canvas.mpl_disconnect(self.cid_mouse)
            self.canvas.mpl_disconnect(self.cid_key)

    def navigate(self, event):
        if event.inaxes == self.ax_Zcut and event.key == "control":
            self.setXYValue(event.xdata, event.ydata, True)
            self.X.valueChanged.disconnect()
            self.Y.valueChanged.disconnect()
            self.X.setValue(event.xdata)
            self.Y.setValue(event.ydata)
            self.X.valueChanged.connect(self.setXYValueFromSpinBox)
            self.Y.valueChanged.connect(self.setXYValueFromSpinBox)

    def OnPress(self, event):
        if event.inaxes == self.ax_Zcut and event.button == 1:
            if not self.selector.visible: #draw selector from nothing
                self.selector.moving_state = "draw"
                self.selector.origin = (event.xdata, event.ydata)
                self.cid_drawRS = self.canvas.mpl_connect('motion_notify_event', self.OnDrawRS)
            else:
                dist = self.selector.nearestCorner(event.x, event.y)
                if dist < 10:  # resize the selector
                    self.selector.moving_state = "moveHandle"
                    self.selector.origin = (event.xdata, event.ydata)
                    self.cid_moveHandle = self.canvas.mpl_connect('motion_notify_event', self.OnMoveHandle)
                else:
                    if self.selector.isinRegion(event.xdata, event.ydata): #move the selector
                        self.selector.moving_state = "move"
                        self.selector.origin = (event.xdata, event.ydata)
                        self.cid_moveRS = self.canvas.mpl_connect('motion_notify_event', self.OnMoveRS)
                    else:          #clear the selector
                        self.selector.set_visible(False)
                        self.plotArtist()
        if event.inaxes == self.ax_Xcut and event.button == 1 and self.selector.visible:
            if self.selector.isinXRegion(event.xdata):
                self.selector.moving_state = "movex"
                self.selector.origin = (event.xdata, event.ydata)
                self.cid_moveRSX = self.canvas.mpl_connect('motion_notify_event', self.OnMoveRSX)
            else:
                self.selector.set_visible(False)
                self.plotArtist()
        if event.inaxes == self.ax_Ycut and event.button == 1 and self.selector.visible:
            if self.selector.isinYRegion(event.ydata):
                self.selector.moving_state = "movey"
                self.selector.origin = (event.xdata, event.ydata)
                self.cid_moveRSY = self.canvas.mpl_connect('motion_notify_event', self.OnMoveRSY)
            else:
                self.selector.set_visible(False)
                self.plotArtist()

    def OnDrawRS(self, event):
        if event.inaxes == self.ax_Zcut and event.button == 1:
            if event.xdata != self.selector.origin[0] and event.ydata != self.selector.origin[1]:
                self.selector.set_visible(True)
                self.selector.resize(self.selector.origin[0], self.selector.origin[1], event.xdata, event.ydata)
                self.plotArtist()

    def OnMoveRS(self, event):
        if event.inaxes == self.ax_Zcut and event.button == 1:
            xmin, ymin, xmax, ymax = self.selector.region
            self.selector.resize(xmin+event.xdata-self.selector.origin[0], ymin+event.ydata-self.selector.origin[1], xmax+event.xdata-self.selector.origin[0], ymax+event.ydata-self.selector.origin[1])
            self.plotArtist()
            self.selector.origin = (event.xdata, event.ydata)

    def OnMoveRSX(self, event):
        if event.inaxes == self.ax_Xcut and event.button == 1:
            xmin, ymin, xmax, ymax = self.selector.region
            self.selector.resize(xmin+event.xdata-self.selector.origin[0], ymin, xmax+event.xdata-self.selector.origin[0], ymax)
            self.plotArtist()
            self.selector.origin = (event.xdata, event.ydata)

    def OnMoveRSY(self, event):
        if event.inaxes == self.ax_Ycut and event.button == 1:
            xmin, ymin, xmax, ymax = self.selector.region
            self.selector.resize(xmin, ymin+event.ydata-self.selector.origin[1], xmax, ymax+event.ydata-self.selector.origin[1])
            self.plotArtist()
            self.selector.origin = (event.xdata, event.ydata)

    def OnMoveHandle(self, event):
        if event.inaxes == self.ax_Zcut and event.button == 1:
            xmin, ymin, xmax, ymax = self.selector.region
            if self.selector.active_handle == 0:
                self.selector.resize(xmin+event.xdata-self.selector.origin[0], ymin+event.ydata-self.selector.origin[1], xmax, ymax)
            elif self.selector.active_handle == 1:
                self.selector.resize(xmin, ymin+event.ydata-self.selector.origin[1], xmax, ymax)
            elif self.selector.active_handle == 2:
                self.selector.resize(xmin, ymin+event.ydata-self.selector.origin[1], xmax+event.xdata-self.selector.origin[0], ymax)
            elif self.selector.active_handle == 3:
                self.selector.resize(xmin, ymin, xmax+event.xdata-self.selector.origin[0], ymax)
            elif self.selector.active_handle == 4:
                self.selector.resize(xmin, ymin, xmax+event.xdata-self.selector.origin[0], ymax+event.ydata-self.selector.origin[1])
            elif self.selector.active_handle == 5:
                self.selector.resize(xmin, ymin, xmax, ymax+event.ydata-self.selector.origin[1])
            elif self.selector.active_handle == 6:
                self.selector.resize(xmin+event.xdata-self.selector.origin[0], ymin, xmax, ymax+event.ydata-self.selector.origin[1])
            elif self.selector.active_handle == 7:
                self.selector.resize(xmin+event.xdata-self.selector.origin[0], ymin, xmax, ymax)
            self.plotArtist()
            self.selector.origin = (event.xdata, event.ydata)

    def OnRelease(self, event):
        if event.inaxes == self.ax_Zcut:
            if event.button == 1:
                if self.selector.moving_state == "draw":
                    self.canvas.mpl_disconnect(self.cid_drawRS)
                elif self.selector.moving_state == "move":
                    self.canvas.mpl_disconnect(self.cid_moveRS)
                elif self.selector.moving_state == "moveHandle":
                    self.canvas.mpl_disconnect(self.cid_moveHandle)
            if event.button == 3:
                if self.selector.visible and self.selector.isinRegion(event.xdata, event.ydata):
                    self.CropAction.setEnabled(True)
                    self.SelectMenu.setEnabled(True)
                else:
                    self.CropAction.setEnabled(False)
                    self.SelectMenu.setEnabled(False)
                self.showContextMenu()
        elif event.inaxes == self.ax_Xcut:
            if event.button == 1 and self.selector.moving_state == "movex":
                self.canvas.mpl_disconnect(self.cid_moveRSX)
        elif event.inaxes == self.ax_Ycut:
            if event.button == 1 and self.selector.moving_state == "movey":
                self.canvas.mpl_disconnect(self.cid_moveRSY)
        else:
            if event.button == 3:
                self.CropAction.setEnabled(False)
                self.SelectMenu.setEnabled(False)
                self.showContextMenu()

    def OnClimb(self, event):
        if event.inaxes == self.ax_Zcut:
            self.Z.setValue(self.Z.value()+event.step*self.data.zstep*self.data.data.shape[2]*0.02)

    def OnKeyPress(self, event):
        if event.key == 'ctrl+a':
            if self.toolPanel.isChecked():
                self.toolPanel.setChecked(False)
            else:
                self.toolPanel.setChecked(True)

    def showContextMenu(self):       
        self.contextMenu.move(QCursor.pos())
        self.contextMenu.show()

    def outputData(self):
        if self.sender() == self.zcut_action:
            data = Spectrum(self.data.name+"_Z", self.Zcut, self.data.xscale, self.data.yscale, spacemode=self.data.spacemode, energyAxis=self.data.energyAxis)
        elif self.sender() == self.xcut_action:
            data = Spectrum(self.data.name+"_X", self.Xcut, self.data.xscale, self.data.zscale, spacemode=self.data.spacemode, energyAxis=self.data.energyAxis)
        elif self.sender() == self.ycut_action:
            data = Spectrum(self.data.name+"_Y", self.Ycut, self.data.yscale, self.data.zscale, spacemode=self.data.spacemode, energyAxis=self.data.energyAxis)
        self.viewer.Win.NewData(data)

    def crop(self):
        x0, y0, x1, y1 = self.selector.region
        self.viewer.Win.DataProcessor.tab_single.setSelectXYRange(x0, x1, y0, y1, True)
        self.selector.set_visible(False)
        self.plotArtist()
        self.viewer.Win.DataProcessor.tab_single.crop3D.clicked.emit()

    def setSelectionRange(self):
        x0, y0, x1, y1 = self.selector.region
        if self.sender() == self.SelectX:
            self.viewer.Win.DataProcessor.tab_single.setSelectXRange(x0, x1)
        elif self.sender() == self.SelectY:
            self.viewer.Win.DataProcessor.tab_single.setSelectYRange(y0, y1)
        elif self.sender() == self.SelectXY:
            self.viewer.Win.DataProcessor.tab_single.setSelectXYRange(x0, x1, y0, y1, True)
        self.selector.set_visible(False)
        self.plotArtist()

    def plotZcut(self, cmap, useblit):
        for img in self.ax_Zcut.get_images():
            img.remove()
        self.Zcutimg = self.ax_Zcut.imshow(self.Zcut.T, cmap=cmap, origin="lower", extent=(self.data.xmin-0.5*self.data.xstep, self.data.xmax+0.5*self.data.xstep, self.data.ymin-0.5*self.data.ystep, self.data.ymax+0.5*self.data.ystep), aspect=self.aspect, interpolation='none')
        visible_flag = self.selector.visible
        self.selector.set_visible(False)
        if useblit:
            self.ax_Zcut.redraw_in_frame()
            self.canvas.blit(self.Zcutbbox)
        else:
            pass
        self.background_Zcut = self.canvas.copy_from_bbox(self.Zcutbbox) #this line makes sure that the background will be updated when user change color map
        self.selector.set_visible(visible_flag)

    def plotXcut(self, cmap, useblit):
        for img in self.ax_Xcut.get_images():
            img.remove()
        self.Xcutimg = self.ax_Xcut.imshow(self.Xcut.T, cmap=cmap, origin="lower", extent=(self.data.xmin-0.5*self.data.xstep, self.data.xmax+0.5*self.data.xstep, self.data.zmin-0.5*self.data.zstep, self.data.zmax+0.5*self.data.zstep), aspect="auto", interpolation='none')
        visible_flag = self.selector.visible
        self.selector.set_visible(False)
        if useblit:
            self.ax_Xcut.redraw_in_frame()
            self.canvas.blit(self.Xcutbbox)
        else:
            pass
        self.background_Xcut = self.canvas.copy_from_bbox(self.Xcutbbox) #this line makes sure that the background will be updated when user change color map
        self.selector.set_visible(visible_flag)

    def plotYcut(self, cmap, useblit):
        for img in self.ax_Ycut.get_images():
            img.remove()
        self.Ycutimg = self.ax_Ycut.imshow(self.Ycut, cmap=cmap, origin="lower", extent=(self.data.zmin-0.5*self.data.zstep, self.data.zmax+0.5*self.data.zstep, self.data.ymin-0.5*self.data.ystep, self.data.ymax+0.5*self.data.ystep), aspect="auto", interpolation='none')
        visible_flag = self.selector.visible
        self.selector.set_visible(False)
        if useblit:
            self.ax_Ycut.redraw_in_frame()
            self.canvas.blit(self.Ycutbbox)
        else:
            pass
        self.background_Ycut = self.canvas.copy_from_bbox(self.Ycutbbox) #this line makes sure that the background will be updated when user change color map
        self.selector.set_visible(visible_flag)

    def plotXDC(self):
        self.resetXDC()
        self.canvas.restore_region(self.background_XDC)
        self.ax_XDC.draw_artist(self.XDCLine)
        self.ax_XDC.draw_artist(self.XDCCursor)
        self.canvas.blit(self.XDCbbox)

    def resetXDC(self):
        mask = np.isnan(self.XDC)
        self.XDCLine.set_data(self.data.xscale[~mask], self.XDC[~mask])
        if len(self.XDC[~mask]) > 1:
            minvalue = min(self.XDC[~mask])
            maxvalue = max(self.XDC[~mask])
            if minvalue == maxvalue:
                minvalue = minvalue - 0.5
                maxvalue = maxvalue + 0.5
        else:
            minvalue = 0
            maxvalue = 1
        self.ax_XDC.set_ybound(lower=minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_XDC.set_xbound(lower=self.data.xmin-self.data.xstep*0.5, upper=self.data.xmax+self.data.xstep*0.5)

    def plotYDC(self):
        self.resetYDC()
        self.canvas.restore_region(self.background_YDC)
        self.ax_YDC.draw_artist(self.YDCLine)
        self.ax_YDC.draw_artist(self.YDCCursor)
        self.canvas.blit(self.YDCbbox)

    def resetYDC(self):
        mask = np.isnan(self.YDC)
        self.YDCLine.set_data(self.YDC[~mask], self.data.yscale[~mask])
        if len(self.YDC[~mask]) > 1:
            minvalue = min(self.YDC[~mask])
            maxvalue = max(self.YDC[~mask])
            if minvalue == maxvalue:
                minvalue = minvalue - 0.5
                maxvalue = maxvalue + 0.5
        else:
            minvalue = 0
            maxvalue = 1
        self.ax_YDC.set_xbound(lower= minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_YDC.set_ybound(lower=self.data.ymin-self.data.ystep*0.5, upper=self.data.ymax+self.data.ystep*0.5)

    def plotZDC(self):
        self.resetZDC()
        self.canvas.restore_region(self.background_ZDC1)
        self.ax_ZDC1.draw_artist(self.ZDCLine1)
        self.ax_ZDC1.draw_artist(self.ZDC1Cursor)
        self.canvas.blit(self.ZDC1bbox)
        self.canvas.restore_region(self.background_ZDC2)
        self.ax_ZDC2.draw_artist(self.ZDCLine2)
        self.ax_ZDC2.draw_artist(self.ZDC2Cursor)
        self.canvas.blit(self.ZDC2bbox)

    def resetZDC(self):
        mask = np.isnan(self.ZDC)
        self.ZDCLine1.set_data(self.ZDC[~mask], self.data.zscale[~mask])
        self.ZDCLine2.set_data(self.data.zscale[~mask], self.ZDC[~mask])
        if len(self.ZDC[~mask]) > 1:
            minvalue = min(self.ZDC[~mask])
            maxvalue = max(self.ZDC[~mask])
            if minvalue == maxvalue:
                minvalue = minvalue - 0.5
                maxvalue = maxvalue + 0.5
        else:
            minvalue = 0
            maxvalue = 1
        self.ax_ZDC1.set_xbound(lower= minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_ZDC1.set_ybound(lower=self.data.zmin-self.data.zstep*0.5, upper=self.data.zmax+self.data.zstep*0.5)
        self.ax_ZDC2.set_ybound(lower= minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_ZDC2.set_xbound(lower=self.data.zmin-self.data.zstep*0.5, upper=self.data.zmax+self.data.zstep*0.5)

    def plotArtist(self):
        self.canvas.restore_region(self.background_Zcut)
        for line in self.ax_Zcut.get_lines():
            self.ax_Zcut.draw_artist(line)
        for artist in self.selector.artistz:
            self.ax_Zcut.draw_artist(artist)
        self.canvas.blit(self.Zcutbbox)
        self.canvas.restore_region(self.background_Xcut)
        for line in self.ax_Xcut.get_lines():
            self.ax_Xcut.draw_artist(line)
        for artist in self.selector.artistx:
            self.ax_Xcut.draw_artist(artist)
        self.canvas.blit(self.Xcutbbox)
        self.canvas.restore_region(self.background_Ycut)
        for line in self.ax_Ycut.get_lines():
            self.ax_Ycut.draw_artist(line)
        for artist in self.selector.artisty:
            self.ax_Ycut.draw_artist(artist)
        self.canvas.blit(self.Ycutbbox)

    def changeAspect(self, state):
        if state:
            self.aspect = "equal"
        else:
            self.aspect = "auto"
        self.ax_Zcut.set_aspect(self.aspect)
        self.updateAxesPosition(True)

    def updateAxesPosition(self, useDraw):
        x_Zcut, y_Zcut, w_Zcut, h_Zcut = self.ax_Zcut.get_position().bounds
        x_Xcut, y_Xcut, w_Xcut, h_Xcut = self.ax_Xcut.get_position().bounds
        x_Ycut, y_Ycut, w_Ycut, h_Ycut = self.ax_Ycut.get_position().bounds
        x_XDC, y_XDC, w_XDC, h_XDC = self.ax_XDC.get_position().bounds
        x_YDC, y_YDC, w_YDC, h_YDC = self.ax_YDC.get_position().bounds
        self.ax_Xcut.set_position([x_Zcut, y_Xcut, w_Zcut, h_Xcut])
        self.ax_XDC.set_position([x_Zcut, y_XDC, w_Zcut, h_XDC])
        self.ax_Ycut.set_position([x_Ycut, y_Zcut, w_Ycut, h_Zcut])
        self.ax_YDC.set_position([x_YDC, y_Zcut, w_YDC, h_Zcut])
        visible_flag = self.selector.visible
        self.selector.set_visible(False)
        if useDraw:
            self.canvas.draw()
        self.GetWhiteBackground()
        self.selector.set_visible(visible_flag)
        self.plotXDC()
        self.plotYDC()
        self.plotZDC()
        self.plotArtist()

    def resizeEvent_wrapper(self):
        self.updateAxesPosition(False)
        
