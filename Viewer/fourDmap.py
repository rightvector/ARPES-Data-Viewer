'''
4D Map Viewer Module
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
from Viewer.Selector import Selector
from Viewer.colormap import CustomComboBox
import glob, os, copy
import numpy as np



class fourDmap(QWidget):
    def __init__(self, viewer):
        super(fourDmap, self).__init__()
        self.data = Spectrum()
        self.viewer = viewer
        self.spec_aspect = "auto"
        self.map_aspect = "auto"

        #init view
        self.fig = Figure(figsize=(3, 3), dpi=150)
        gs = GridSpec(3, 6, figure=self.fig)
        self.ax_Spec = self.fig.add_subplot(gs[1:3, 1:3])
        self.ax_XDC = self.fig.add_subplot(gs[0, 1:3])
        self.ax_YDC = self.fig.add_subplot(gs[1:3, 0])
        self.ax_Speccmap = self.fig.add_subplot(gs[0, 0])
        self.ax_Map = self.fig.add_subplot(gs[1:3, 3:5])
        self.ax_ZDC = self.fig.add_subplot(gs[0, 3:5])
        self.ax_TDC = self.fig.add_subplot(gs[1:3, 5])
        self.ax_Mapcmap = self.fig.add_subplot(gs[0, 5])
        self.fig.subplots_adjust(top=0.96, bottom=0.08, left=0.1, right=0.9, wspace=0.15, hspace=0.15)
        self.ax_Spec.tick_params(direction='inout', labelsize=8.5, labelleft=False)
        self.ax_XDC.tick_params(axis='x', labelsize=8.5, labelbottom=False)
        self.ax_XDC.tick_params(axis='y', labelsize=8.5, left=False, labelleft=False)
        self.ax_YDC.tick_params(axis='x', labelsize=8.5, bottom=False, labelbottom=False)
        self.ax_YDC.tick_params(axis='y', labelsize=8.5)
        self.ax_Map.tick_params(direction='inout', labelsize=8.5, labelleft=False)
        self.ax_ZDC.tick_params(axis='x', labelsize=8.5, labelbottom=False)
        self.ax_ZDC.tick_params(axis='y', labelsize=8.5, left=False, labelleft=False)
        self.ax_TDC.tick_params(axis='x', labelsize=8.5, bottom=False, labelbottom=False)
        self.ax_TDC.tick_params(axis='y', labelsize=8.5, left=False, labelleft=False, right=True, labelright=True)
        self.ax_YDC.invert_xaxis()
        self.setTickLabelFont(self.ax_Spec, "Comic Sans MS")
        self.setTickLabelFont(self.ax_XDC, "Comic Sans MS")
        self.setTickLabelFont(self.ax_YDC, "Comic Sans MS")
        self.setTickLabelFont(self.ax_Map, "Comic Sans MS")
        self.setTickLabelFont(self.ax_ZDC, "Comic Sans MS")
        self.setTickLabelFont(self.ax_TDC, "Comic Sans MS")
        x0, y0, width, height = self.ax_Speccmap.get_position().bounds
        nheight = height*0.2
        ny0 = y0+height*0.5*(1-0.2)
        self.ax_Speccmap.set_position([x0, ny0, width, nheight])
        self.ax_Speccmap.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
        self.ax_Speccmap.set_title("CMap", {'fontsize': 8}, fontname="Comic Sans Ms")
        x0, y0, width, height = self.ax_Mapcmap.get_position().bounds
        nheight = height*0.2
        ny0 = y0+height*0.5*(1-0.2)
        self.ax_Mapcmap.set_position([x0, ny0, width, nheight])
        self.ax_Mapcmap.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
        self.ax_Mapcmap.set_title("CMap", {'fontsize': 8}, fontname="Comic Sans Ms")
        self.gradient = np.vstack((np.linspace(0, 1, 256), np.linspace(0, 1, 256)))
        self.XDCLine = Line2D(np.array([0]), np.array([0]), color="blue", linewidth=1, animated=True, solid_joinstyle="round")
        self.YDCLine = Line2D(np.array([0]), np.array([0]), color="blue", linewidth=1, animated=True, solid_joinstyle="round")
        self.ZDCLine = Line2D(np.array([0]), np.array([0]), color="red", linewidth=1, animated=True, solid_joinstyle="round")
        self.TDCLine = Line2D(np.array([0]), np.array([0]), color="red", linewidth=1, animated=True, solid_joinstyle="round")
        self.ax_XDC.add_line(self.XDCLine)
        self.ax_YDC.add_line(self.YDCLine)
        self.ax_ZDC.add_line(self.ZDCLine)
        self.ax_TDC.add_line(self.TDCLine)
        
        # canvas
        self.canvas = FigureCanvas(self.fig)
        self.fig.patch.set_facecolor("None")
        self.canvas.setStyleSheet("background-color:transparent;")
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.GetBbox()

        #cursor
        self.SpecXline1 = self.ax_Spec.axhline(self.ax_Spec.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75) 
        self.SpecYline1 = self.ax_Spec.axvline(self.ax_Spec.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.SpecXline2 = self.ax_Spec.axhline(self.ax_Spec.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  
        self.SpecYline2 = self.ax_Spec.axvline(self.ax_Spec.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.MapXline1 = self.ax_Map.axhline(self.ax_Map.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75) 
        self.MapYline1 = self.ax_Map.axvline(self.ax_Map.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.MapXline2 = self.ax_Map.axhline(self.ax_Map.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  
        self.MapYline2 = self.ax_Map.axvline(self.ax_Map.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  
        self.XDCCursor = self.ax_XDC.axvline(self.ax_XDC.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.YDCCursor = self.ax_YDC.axhline(self.ax_YDC.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.ZDCCursor = self.ax_ZDC.axvline(self.ax_ZDC.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.TDCCursor = self.ax_TDC.axhline(self.ax_TDC.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)

        #selector
        self.selector_Spec = Selector(self.ax_Spec, self.canvas)
        self.selector_Map = Selector(self.ax_Map, self.canvas)
        self.cid_keypress = self.canvas.mpl_connect('key_press_event', self.OnKeyPress)
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.OnPress)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.OnRelease)

        #contextMenu
        self.contextMenu = QMenu(self)
        self.CropAction = self.contextMenu.addAction("Crop")
        self.CropAction.setIcon(QIcon("./image/crop.ico"))
        #self.CropAction.triggered.connect(self.crop)
        self.RestoreAction = self.contextMenu.addAction("Restore")
        self.RestoreAction.setIcon(QIcon("./image/restore.ico"))
        #self.RestoreAction.triggered.connect(self.viewer.Win.DataProcessor.tab_single.RestoreData)
        self.SelectMenu = self.contextMenu.addMenu("Select")
        self.SelectMenu.setIcon(QIcon("./image/select.ico"))
        self.SelectX = self.SelectMenu.addAction("X Range")
        #self.SelectX.triggered.connect(self.setSelectionRange)
        self.SelectY = self.SelectMenu.addAction("Y Range")
        #self.SelectY.triggered.connect(self.setSelectionRange)
        self.SelectXY = self.SelectMenu.addAction("XY Area")
        #self.SelectXY.triggered.connect(self.setSelectionRange)
        self.SelectZ = self.SelectMenu.addAction("Z Range")
        #self.SelectZ.triggered.connect(self.setSelectionRange)
        self.SelectT = self.SelectMenu.addAction("T Range")
        #self.SelectT.triggered.connect(self.setSelectionRange)
        self.SelectZT = self.SelectMenu.addAction("ZT Area")
        #self.SelectZT.triggered.connect(self.setSelectionRange)
        self.outputMenu = self.contextMenu.addMenu("Output")
        self.outputMenu.setIcon(QIcon("./image/output.ico"))
        self.Spec_action = self.outputMenu.addAction("Spectrum")
        #self.Spec_action.triggered.connect(self.outputData)
        self.Map_action = self.outputMenu.addAction("Map")
        #self.Map_action.triggered.connect(self.outputData)
        self.XDC_action = self.outputMenu.addAction("XDC")
        self.YDC_action = self.outputMenu.addAction("YDC")
        self.ZDC_action = self.outputMenu.addAction("ZDC")
        self.TDC_action = self.outputMenu.addAction("TDC")

        #init Tool
        self.toolPanel = QGroupBox("Coordinate System")
        self.toolPanel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolPanel.setCheckable(True)
        self.toolPanel.setChecked(False)
        self.toolPanel.setStyle(QStyleFactory.create('Fusion'))
        self.toolPanel.toggled.connect(self.begincursor)
        self.X = QDoubleSpinBox()
        self.X.setFixedWidth(85)
        self.X.setDecimals(6)
        self.X.setRange(-1, 1)
        self.X.setSingleStep(0.01)
        self.X.setKeyboardTracking(False)
        self.X.setStyle(QStyleFactory.create('Fusion'))
        self.X.setValue(-1)
        self.X.valueChanged.connect(self.setValueFromSpinBox)
        self.XLabel = QLabel("X:")
        self.XLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Y = QDoubleSpinBox()
        self.Y.setFixedWidth(85)
        self.Y.setDecimals(6)
        self.Y.setRange(-1, 1)
        self.Y.setSingleStep(0.01)
        self.Y.setKeyboardTracking(False)
        self.Y.setStyle(QStyleFactory.create('Fusion'))
        self.Y.setValue(-1)
        self.Y.valueChanged.connect(self.setValueFromSpinBox)
        self.YLabel = QLabel("Y:")
        self.YLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Z = QDoubleSpinBox()
        self.Z.setFixedWidth(85)
        self.Z.setDecimals(6)
        self.Z.setRange(-1, 1)
        self.Z.setSingleStep(0.01)
        self.Z.setKeyboardTracking(False)
        self.Z.setStyle(QStyleFactory.create('Fusion'))
        self.Z.setValue(-1)
        self.Z.valueChanged.connect(self.setValueFromSpinBox)
        self.ZLabel = QLabel("Z:")
        self.ZLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.T = QDoubleSpinBox()
        self.T.setFixedWidth(85)
        self.T.setDecimals(6)
        self.T.setRange(-1, 1)
        self.T.setSingleStep(0.01)
        self.T.setKeyboardTracking(False)
        self.T.setStyle(QStyleFactory.create('Fusion'))
        self.T.setValue(-1)
        self.T.valueChanged.connect(self.setValueFromSpinBox)
        self.TLabel = QLabel("T:")
        self.TLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
        self.TSlider = QSlider(Qt.Horizontal)
        self.TSlider.setRange(0, 10000)
        self.TSlider.setStyle(QStyleFactory.create('Fusion'))
        self.TSlider.sliderMoved.connect(self.setValueFromSlider)
        self.TSLabel = QLabel("T:")
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
        self.TSlice = QSpinBox()
        self.TSlice.setRange(1, 10000)
        self.TSlice.setSingleStep(2)
        self.TSlice.setFixedWidth(50)
        self.TSlice.setKeyboardTracking(False)
        self.TSlice.setStyle(QStyleFactory.create('Fusion'))
        self.TSlice.valueChanged.connect(self.setSlice)
        self.TSliceLabel = QLabel("Slice:")
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
        hbox_tool.addWidget(self.TLabel)
        hbox_tool.addWidget(self.T)
        hbox_tool.addStretch(1)
        hbox_tool.addWidget(self.IntLabel)
        hbox_tool.addWidget(self.Int)
        hbox_tool.addStretch(2)
        hbox2_tool = QHBoxLayout()
        hbox2_tool.addWidget(self.XSLabel, 0)
        hbox2_tool.addWidget(self.XSlider, 1)
        hbox2_tool.addWidget(self.XSliceLabel, 0)
        hbox2_tool.addWidget(self.XSlice, 0)
        hbox2_tool.addWidget(self.ZSLabel, 0)
        hbox2_tool.addWidget(self.ZSlider, 1)
        hbox2_tool.addWidget(self.ZSliceLabel, 0)
        hbox2_tool.addWidget(self.ZSlice, 0)
        hbox3_tool = QHBoxLayout()
        hbox3_tool.addWidget(self.YSLabel, 0)
        hbox3_tool.addWidget(self.YSlider, 1)
        hbox3_tool.addWidget(self.YSliceLabel, 0)
        hbox3_tool.addWidget(self.YSlice, 0)
        hbox3_tool.addWidget(self.TSLabel, 0)
        hbox3_tool.addWidget(self.TSlider, 1)
        hbox3_tool.addWidget(self.TSliceLabel, 0)
        hbox3_tool.addWidget(self.TSlice, 0)
        vbox_tool = QVBoxLayout()
        vbox_tool.addLayout(hbox_tool)
        vbox_tool.addLayout(hbox2_tool)
        vbox_tool.addLayout(hbox3_tool)
        self.toolPanel.setLayout(vbox_tool)

        #color scale
        self.colorPanel = QGroupBox("Color Scale")
        self.colorPanel.setFixedHeight(100)
        self.colorPanel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.Speccmapmenu = CustomComboBox()
        self.Speccmapmenu.setFixedWidth(120)
        self.Speccmapmenu.setStyle(QStyleFactory.create('Fusion'))
        self.Speccmapmenu.setCurrentText("twilight")
        self.Speccmapmenu.currentIndexChanged.connect(self.changeSpeccmapbyindex)
        self.revSpeccmap = QCheckBox("R")
        self.revSpeccmap.stateChanged.connect(self.reverseSpeccmap)
        self.SpecGammaLabel = QLabel("Spec Gamma:")
        self.SpecGammaLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.SpecGamma = QDoubleSpinBox()
        self.SpecGamma.setFixedWidth(100)
        self.SpecGamma.setDecimals(3)
        self.SpecGamma.setRange(0.05, 20)
        self.SpecGamma.setSingleStep(0.01)
        self.SpecGamma.setValue(1)
        self.SpecGamma.setKeyboardTracking(False)
        self.SpecGamma.valueChanged.connect(self.setGammaFromSpecSpinBox)
        self.SpecGamma.setStyle(QStyleFactory.create('Fusion'))
        self.SpecGSlider = QSlider(Qt.Horizontal)
        self.SpecGSlider.setRange(1000000*np.log(0.05), 1000000*np.log(20))
        self.SpecGSlider.setValue(0)
        self.SpecGSlider.sliderMoved.connect(self.setGammaFromSpecSlider)
        self.SpecGSlider.setStyle(QStyleFactory.create('Fusion'))
        hbox_Speccmap = QHBoxLayout()
        hbox_Speccmap.addWidget(self.Speccmapmenu)
        hbox_Speccmap.addWidget(self.SpecGammaLabel)
        hbox_Speccmap.addWidget(self.SpecGamma)
        hbox_Speccmap.addWidget(self.SpecGSlider)
        hbox_Speccmap.addWidget(self.revSpeccmap)
        self.Mapcmapmenu = CustomComboBox()
        self.Mapcmapmenu.setFixedWidth(120)
        self.Mapcmapmenu.setStyle(QStyleFactory.create('Fusion'))
        self.Mapcmapmenu.setCurrentText("twilight")
        self.Mapcmapmenu.currentIndexChanged.connect(self.changeMapcmapbyindex)
        self.revMapcmap = QCheckBox("R")
        self.revMapcmap.stateChanged.connect(self.reverseMapcmap)
        self.MapGammaLabel = QLabel("Map  Gamma:")
        self.MapGammaLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.MapGamma = QDoubleSpinBox()
        self.MapGamma.setFixedWidth(100)
        self.MapGamma.setDecimals(3)
        self.MapGamma.setRange(0.05, 20)
        self.MapGamma.setSingleStep(0.01)
        self.MapGamma.setValue(1)
        self.MapGamma.setKeyboardTracking(False)
        self.MapGamma.valueChanged.connect(self.setGammaFromMapSpinBox)
        self.MapGamma.setStyle(QStyleFactory.create('Fusion'))
        self.MapGSlider = QSlider(Qt.Horizontal)
        self.MapGSlider.setRange(1000000*np.log(0.05), 1000000*np.log(20))
        self.MapGSlider.setValue(0)
        self.MapGSlider.sliderMoved.connect(self.setGammaFromMapSlider)
        self.MapGSlider.setStyle(QStyleFactory.create('Fusion'))
        hbox_Mapcmap = QHBoxLayout()
        hbox_Mapcmap.addWidget(self.Mapcmapmenu)
        hbox_Mapcmap.addWidget(self.MapGammaLabel)
        hbox_Mapcmap.addWidget(self.MapGamma)
        hbox_Mapcmap.addWidget(self.MapGSlider)
        hbox_Mapcmap.addWidget(self.revMapcmap)
        vbox_colorPanel = QVBoxLayout()
        vbox_colorPanel.addLayout(hbox_Speccmap)
        vbox_colorPanel.addLayout(hbox_Mapcmap)
        self.colorPanel.setLayout(vbox_colorPanel)
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
        #self.selector.set_visible(False)
        self.data = data
        self.Spec = data.data[:,:,0,0]
        self.Map = data.data[0,0,:,:]
        self.XDC = data.data[:,0,0,0]
        self.YDC = data.data[0,:,0,0]
        self.ZDC = data.data[0,0,:,0]
        self.TDC = data.data[0,0,0,:]
        self.X.disconnect()
        self.Y.disconnect()
        self.Z.disconnect()
        self.T.disconnect()
        self.X.setRange(data.xmin, data.xmax)
        self.X.setSingleStep(data.xstep)
        self.Y.setRange(data.ymin, data.ymax)
        self.Y.setSingleStep(data.ystep)
        self.Z.setRange(data.zmin, data.zmax)
        self.Z.setSingleStep(data.zstep)
        self.T.setRange(data.tmin, data.tmax)
        self.T.setSingleStep(data.tstep)
        self.X.valueChanged.connect(self.setValueFromSpinBox)
        self.Y.valueChanged.connect(self.setValueFromSpinBox)
        self.Z.valueChanged.connect(self.setValueFromSpinBox)
        self.T.valueChanged.connect(self.setValueFromSpinBox)
        self.XSlice.setRange(1, self.data.dimension[0])
        self.YSlice.setRange(1, self.data.dimension[1])
        self.ZSlice.setRange(1, self.data.dimension[2])
        self.TSlice.setRange(1, self.data.dimension[3])
        self.initialCoordinate()
        self.updatecolorscale(self.getcurrentcmap('Spec'), 'Spec')
        self.updatecolorscale(self.getcurrentcmap('Map'), 'Map')
        self.updateAxesPosition(True)
        self.colorPanel.setEnabled(True)

    def setTickLabelFont(self, ax, font):
        for tick in ax.get_xticklabels():
            tick.set_fontname(font)
        for tick in ax.get_yticklabels():
            tick.set_fontname(font)

    def initialCoordinate(self):
        newX = 0
        if self.data.xmin*self.data.xmax < 0:
            newX = 0
        else:
            newX = (self.data.xmin+self.data.xmax)/2
        if round(newX, 6) == self.X.value():
            self.X.valueChanged.emit(newX)
        else:
            self.X.setValue(newX)
        newY = 0
        if self.data.ymin*self.data.ymax < 0:
            newY = 0
        else:
            newY = (self.data.ymin+self.data.ymax)/2          
        if round(newY, 6) == self.Y.value():
            self.Y.valueChanged.emit(newY)
        else:
            self.Y.setValue(newY)
        newZ = 0
        if self.data.zmin*self.data.zmax < 0:
            newZ = 0
        else:
            newZ = (self.data.zmin+self.data.zmax)/2       
        if round(newZ, 6) == self.Z.value():
            self.Z.valueChanged.emit(newZ)
        else:
            self.Z.setValue(newZ)
        newT = 0
        if self.data.tmin*self.data.tmax < 0:
            newT = 0
        else:
            newT = (self.data.tmin+self.data.tmax)/2       
        if round(newT, 6) == self.T.value():
            self.T.valueChanged.emit(newT)
        else:
            self.T.setValue(newT)

    def GetBbox(self):
        self.Specbbox = self.ax_Spec.get_window_extent()
        self.Mapbbox = self.ax_Map.get_window_extent()
        self.XDCbbox = self.ax_XDC.get_window_extent()
        self.YDCbbox = self.ax_YDC.get_window_extent()
        self.ZDCbbox = self.ax_ZDC.get_window_extent()
        self.TDCbbox = self.ax_TDC.get_window_extent()

    def GetWhiteBackground(self):
        self.GetBbox()
        self.ax_XDC.redraw_in_frame()
        self.canvas.blit(self.XDCbbox)
        self.ax_YDC.redraw_in_frame()
        self.canvas.blit(self.YDCbbox)
        self.ax_ZDC.redraw_in_frame()
        self.canvas.blit(self.ZDCbbox)
        self.ax_TDC.redraw_in_frame()
        self.canvas.blit(self.TDCbbox)
        self.background_XDC = self.canvas.copy_from_bbox(self.XDCbbox)
        self.background_YDC = self.canvas.copy_from_bbox(self.YDCbbox)
        self.background_ZDC = self.canvas.copy_from_bbox(self.ZDCbbox)
        self.background_TDC = self.canvas.copy_from_bbox(self.TDCbbox)
        self.background_Spec = self.canvas.copy_from_bbox(self.Specbbox)
        self.background_Map = self.canvas.copy_from_bbox(self.Mapbbox)

    def setValueFromSpinBox(self, value):
        if self.sender() == self.X:
            self.setXYValue(value, self.Y.value(), True)
        elif self.sender() == self.Y:
            self.setXYValue(self.X.value(), value, True)
        elif self.sender() == self.Z:
            self.setZTValue(value, self.T.value(), True)
        elif self.sender() == self.T:
            self.setZTValue(self.Z.value(), value, True)

    def setValueFromSlider(self, value):
        if self.sender() == self.XSlider:
            self.X.valueChanged.disconnect()
            xvalue = value*(self.X.maximum()-self.X.minimum())/10000+self.X.minimum()
            self.setXYValue(xvalue, self.Y.value(), False)
            self.X.setValue(xvalue)
            self.X.valueChanged.connect(self.setValueFromSpinBox)
        elif self.sender() == self.YSlider:
            self.Y.valueChanged.disconnect()
            yvalue = value*(self.Y.maximum()-self.Y.minimum())/10000+self.Y.minimum()
            self.setXYValue(self.X.value(), yvalue, False)
            self.Y.setValue(yvalue)
            self.Y.valueChanged.connect(self.setValueFromSpinBox)
        elif self.sender() == self.ZSlider:
            self.Z.valueChanged.disconnect()
            zvalue = value*(self.Z.maximum()-self.Z.minimum())/10000+self.Z.minimum()
            self.setZTValue(zvalue, self.T.value(), False)
            self.Z.setValue(zvalue)
            self.Z.valueChanged.connect(self.setValueFromSpinBox)
        elif self.sender() == self.TSlider:
            self.T.valueChanged.disconnect()
            tvalue = value*(self.T.maximum()-self.T.minimum())/10000+self.T.minimum()
            self.setZTValue(self.Z.value(), tvalue, False)
            self.T.setValue(tvalue)
            self.T.valueChanged.connect(self.setValueFromSpinBox)

    def setXYValue(self, xvalue, yvalue, moveslider):
        if moveslider:
            self.XSlider.setValue((xvalue-self.X.minimum())/(self.X.maximum()-self.X.minimum())*10000)
            self.YSlider.setValue((yvalue-self.Y.minimum())/(self.Y.maximum()-self.Y.minimum())*10000)
        half_wid_xnum = (self.XSlice.value()-1)/2
        half_wid_ynum = (self.YSlice.value()-1)/2
        self.SpecYline1.set_xdata(xvalue-self.data.xstep*half_wid_xnum)
        self.SpecYline2.set_xdata(xvalue+self.data.xstep*half_wid_xnum)
        self.XDCCursor.set_xdata(xvalue)
        self.SpecXline1.set_ydata(yvalue-self.data.ystep*half_wid_ynum)
        self.SpecXline2.set_ydata(yvalue+self.data.ystep*half_wid_ynum)
        self.YDCCursor.set_ydata(yvalue)
        self.Map = self.get_Map(xvalue, yvalue)
        self.XDC = self.get_XDC(yvalue)
        self.YDC = self.get_YDC(xvalue)
        self.ZDC = self.get_ZDC(self.T.value())
        self.TDC = self.get_TDC(self.Z.value())
        self.plotMap(self.getcurrentcmap('Map'), True)
        self.plotXDC()
        self.plotYDC()
        self.plotZDC()
        self.plotTDC()
        self.plotArtist()
        self.setIntensity()

    def setZTValue(self, zvalue, tvalue, moveslider):
        if moveslider:
            self.ZSlider.setValue((zvalue-self.Z.minimum())/(self.Z.maximum()-self.Z.minimum())*10000)
            self.TSlider.setValue((tvalue-self.T.minimum())/(self.T.maximum()-self.T.minimum())*10000)
        half_wid_znum = (self.ZSlice.value()-1)/2
        half_wid_tnum = (self.TSlice.value()-1)/2
        self.MapYline1.set_xdata(zvalue-self.data.zstep*half_wid_znum)
        self.MapYline2.set_xdata(zvalue+self.data.zstep*half_wid_znum)
        self.ZDCCursor.set_xdata(zvalue)
        self.MapXline1.set_ydata(tvalue-self.data.tstep*half_wid_tnum)
        self.MapXline2.set_ydata(tvalue+self.data.tstep*half_wid_tnum)
        self.TDCCursor.set_ydata(tvalue)
        self.Spec = self.get_Spec(zvalue, tvalue)
        self.ZDC = self.get_ZDC(tvalue)
        self.TDC = self.get_TDC(zvalue)
        self.XDC = self.get_XDC(self.Y.value())
        self.YDC = self.get_YDC(self.X.value())
        self.plotSpec(self.getcurrentcmap('Spec'), True)
        self.plotXDC()
        self.plotYDC()
        self.plotZDC()
        self.plotTDC()
        self.plotArtist()
        self.setIntensity()

    def setSlice(self, value):
        if self.sender() == self.XSlice:
            if value % 2 == 0:
                self.XSlice.setValue(value-1)
            else:
                if value == 1:
                    self.SpecYline2.set_visible(False)
                else:
                    self.SpecYline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.SpecYline1.set_xdata(self.X.value()-self.data.xstep*half_wid_num)
                self.SpecYline2.set_xdata(self.X.value()+self.data.xstep*half_wid_num)
                self.Map = self.get_Map(self.X.value(), self.Y.value())
                self.YDC = self.get_YDC(self.X.value())
                self.ZDC = self.get_ZDC(self.T.value())
                self.TDC = self.get_TDC(self.Z.value())
                self.plotMap(self.getcurrentcmap('Map'), True)
                self.plotYDC()
                self.plotZDC()
                self.plotTDC()
                self.plotArtist()
                self.setIntensity()
        elif self.sender() == self.YSlice:
            if value % 2 == 0:
                self.YSlice.setValue(value-1)
            else:
                if value == 1:
                    self.SpecXline2.set_visible(False)
                else:
                    self.SpecXline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.SpecXline1.set_ydata(self.Y.value()-self.data.ystep*half_wid_num)
                self.SpecXline2.set_ydata(self.Y.value()+self.data.ystep*half_wid_num)
                self.Map = self.get_Map(self.X.value(), self.Y.value())
                self.XDC = self.get_XDC(self.Y.value())
                self.ZDC = self.get_ZDC(self.T.value())
                self.TDC = self.get_TDC(self.Z.value())
                self.plotMap(self.getcurrentcmap('Map'), True)
                self.plotXDC()
                self.plotZDC()
                self.plotTDC()
                self.plotArtist()
                self.setIntensity()
        elif self.sender() == self.ZSlice:
            if value % 2 == 0:
                self.ZSlice.setValue(value-1)
            else:
                if value == 1:
                    self.MapYline2.set_visible(False)
                else:
                    self.MapYline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.MapYline1.set_xdata(self.Z.value()-self.data.zstep*half_wid_num)
                self.MapYline2.set_xdata(self.Z.value()+self.data.zstep*half_wid_num)
                self.Spec = self.get_Spec(self.Z.value(), self.T.value())
                self.XDC = self.get_XDC(self.Y.value())
                self.YDC = self.get_YDC(self.X.value())
                self.TDC = self.get_TDC(self.Z.value())
                self.plotSpec(self.getcurrentcmap('Spec'), True)
                self.plotXDC()
                self.plotYDC()
                self.plotTDC()
                self.plotArtist()
                self.setIntensity()
        elif self.sender() == self.TSlice:
            if value % 2 == 0:
                self.TSlice.setValue(value-1)
            else:
                if value == 1:
                    self.MapXline2.set_visible(False)
                else:
                    self.MapXline2.set_visible(True)
                half_wid_num = (value-1)/2
                self.MapXline1.set_ydata(self.T.value()-self.data.tstep*half_wid_num)
                self.MapXline2.set_ydata(self.T.value()+self.data.tstep*half_wid_num)
                self.Spec = self.get_Spec(self.Z.value(), self.T.value())
                self.XDC = self.get_XDC(self.Y.value())
                self.YDC = self.get_YDC(self.X.value())
                self.ZDC = self.get_ZDC(self.T.value())
                self.plotSpec(self.getcurrentcmap('Spec'), True)
                self.plotXDC()
                self.plotYDC()
                self.plotZDC()
                self.plotArtist()
                self.setIntensity()

    def scale2pnt(self, value, scale):
        return (np.abs(scale - value)).argmin()

    def setIntensity(self):
        intensity = self.get_intensity(self.X.value(), self.Y.value(), self.Z.value(), self.T.value())
        if np.isnan(intensity):
            self.Int.setText("NaN")
        elif np.abs(intensity) >= 0.01:
            self.Int.setText("%.2f" % intensity)
        else:
            self.Int.setText("%.2e" % intensity)

    def get_intensity(self, xvalue, yvalue, zvalue, tvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        zidx = self.scale2pnt(zvalue, self.data.zscale)
        tidx = self.scale2pnt(tvalue, self.data.tscale)
        half_wid_xnum = int((self.XSlice.value()-1)/2)
        half_wid_ynum = int((self.YSlice.value()-1)/2)
        half_wid_znum = int((self.ZSlice.value()-1)/2)
        half_wid_tnum = int((self.TSlice.value()-1)/2)
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
        if tidx < half_wid_tnum:
            tminidx = 0
        else:
            tminidx = tidx-half_wid_tnum
        tmaxidx = tidx+half_wid_tnum+1
        return self.data.data[xminidx:xmaxidx, yminidx:ymaxidx, zminidx:zmaxidx, tminidx:tmaxidx].sum()

    def get_Spec(self, zvalue, tvalue):
        zidx = self.scale2pnt(zvalue, self.data.zscale)
        tidx = self.scale2pnt(tvalue, self.data.tscale)
        if self.ZSlice.value() == 1 and self.TSlice.value() == 1:
            return self.data.data[:, :, zidx, tidx]
        else:
            half_wid_znum = int((self.ZSlice.value()-1)/2)
            half_wid_tnum = int((self.TSlice.value()-1)/2)
            zidx_max = zidx+half_wid_znum+1
            tidx_max = tidx+half_wid_tnum+1
            if zidx < half_wid_znum:
                zidx_min = 0
            else:
                zidx_min = zidx-half_wid_znum
            if tidx < half_wid_tnum:
                tidx_min = 0
            else:
                tidx_min = tidx-half_wid_tnum
            array = self.data.data[:, :, zidx_min:zidx_max, tidx_min:tidx_max]
            array = np.sum(array, axis=2)
            array = np.sum(array, axis=2)
            return array

    def get_Map(self, xvalue, yvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        if self.XSlice.value() == 1 and self.YSlice.value() == 1:
            return self.data.data[xidx, yidx, :, :]
        else:
            half_wid_xnum = int((self.XSlice.value()-1)/2)
            xidx_max = xidx+half_wid_xnum+1
            if xidx < half_wid_xnum:
                xidx_min = 0
            else:
                xidx_min = xidx-half_wid_xnum
            half_wid_ynum = int((self.YSlice.value()-1)/2)
            yidx_max = yidx+half_wid_ynum+1
            if yidx < half_wid_ynum:
                yidx_min = 0
            else:
                yidx_min = yidx-half_wid_ynum
            array = self.data.data[xidx_min:xidx_max, yidx_min:yidx_max, :, :]
            array = np.sum(array, axis=0)
            array = np.sum(array, axis=0)
            return array

    def get_XDC(self, yvalue):
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        if self.YSlice.value() == 1:
            return self.Spec[:, yidx]
        else:
            half_wid_ynum = int((self.YSlice.value()-1)/2)
            if yidx < half_wid_ynum:
                ystart = 0
            else:
                ystart = yidx - half_wid_ynum
            yend = yidx + half_wid_ynum + 1
            array = self.Spec[:, ystart:yend]
            return np.sum(array, axis=1)

    def get_YDC(self, xvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        if self.XSlice.value() == 1:
            return self.Spec[xidx, :]
        else:
            half_wid_xnum = int((self.XSlice.value()-1)/2)
            if xidx < half_wid_xnum:
                xstart = 0
            else:
                xstart = xidx - half_wid_xnum
            xend = xidx + half_wid_xnum + 1
            array = self.Spec[xstart:xend, :]
            return np.sum(array, axis=0)

    def get_ZDC(self, tvalue):
        tidx = self.scale2pnt(tvalue, self.data.tscale)
        if self.TSlice.value() == 1:
            return self.Map[:, tidx]
        else:
            half_wid_tnum = int((self.TSlice.value()-1)/2)
            if tidx < half_wid_tnum:
                tstart = 0
            else:
                tstart = tidx - half_wid_tnum
            tend = tidx + half_wid_tnum + 1
            array = self.Map[:, tstart:tend]
            return np.sum(array, axis=1)

    def get_TDC(self, zvalue):
        zidx = self.scale2pnt(zvalue, self.data.zscale)
        if self.ZSlice.value() == 1:
            return self.Map[zidx, :]
        else:
            half_wid_znum = int((self.ZSlice.value()-1)/2)
            if zidx < half_wid_znum:
                zstart = 0
            else:
                zstart = zidx - half_wid_znum
            zend = zidx + half_wid_znum + 1
            array = self.Map[zstart:zend, :]
            return np.sum(array, axis=0)

    def getcurrentcmap(self, which):
        linearIndex = np.linspace(0, 1, 256)
        if which == 'Spec':
            cmap_str = self.Speccmapmenu.currentText()
            if self.revSpeccmap.checkState() == Qt.Checked:
                cmap_str += "_r"
            nonlinearIndex = np.power(linearIndex, self.SpecGamma.value())
        elif which == 'Map':
            cmap_str = self.Mapcmapmenu.currentText()
            if self.revMapcmap.checkState() == Qt.Checked:
                cmap_str += "_r"
            nonlinearIndex = np.power(linearIndex, self.MapGamma.value())
        raw_cmap = cm.get_cmap(cmap_str, 256)
        new_cmap = ListedColormap(raw_cmap(nonlinearIndex))
        return new_cmap

    def updatecolorscale(self, cmap, which):
        if which == 'Spec':
            for img in self.ax_Speccmap.get_images():
                img.remove()
            self.Speccmapimage = self.ax_Speccmap.imshow(self.gradient, cmap=cmap, origin="lower", aspect="auto")
            self.ax_Speccmap.redraw_in_frame()
            self.canvas.blit(self.ax_Speccmap.bbox)
        elif which == 'Map':
            for img in self.ax_Mapcmap.get_images():
                img.remove()
            self.Mapcmapimage = self.ax_Mapcmap.imshow(self.gradient, cmap=cmap, origin="lower", aspect="auto")
            self.ax_Mapcmap.redraw_in_frame()
            self.canvas.blit(self.ax_Mapcmap.bbox)

    def changeSpeccmapbyindex(self, index):
        self.updatecolorscale(self.getcurrentcmap('Spec'), 'Spec')
        self.plotSpec(self.getcurrentcmap('Spec'), True)
        self.plotArtist()

    def changeMapcmapbyindex(self, index):
        self.updatecolorscale(self.getcurrentcmap('Map'), 'Map')
        self.plotMap(self.getcurrentcmap('Map'), True)
        self.plotArtist()

    def setGammaFromSpecSpinBox(self, value):
        self.updatecolorscale(self.getcurrentcmap('Spec'), 'Spec')
        self.plotSpec(self.getcurrentcmap('Spec'), True)
        self.plotArtist()
        self.SpecGSlider.setValue(1000000*np.log(value))

    def setGammaFromSpecSlider(self, value):
        self.SpecGamma.setValue(np.exp(value/1000000))

    def setGammaFromMapSpinBox(self, value):
        self.updatecolorscale(self.getcurrentcmap('Map'), 'Map')
        self.plotMap(self.getcurrentcmap('Map'), True)
        self.plotArtist()
        self.MapGSlider.setValue(1000000*np.log(value))

    def setGammaFromMapSlider(self, value):
        self.MapGamma.setValue(np.exp(value/1000000))

    def reverseSpeccmap(self, state):
        self.updatecolorscale(self.getcurrentcmap('Spec'), 'Spec')
        self.plotSpec(self.getcurrentcmap('Spec'), True)
        self.plotArtist()

    def reverseMapcmap(self, state):
        self.updatecolorscale(self.getcurrentcmap('Map'), 'Map')
        self.plotMap(self.getcurrentcmap('Map'), True)
        self.plotArtist()

    def begincursor(self, on):
        if on:
            self.SpecXline1.set_visible(True)
            self.SpecYline1.set_visible(True)
            self.MapXline1.set_visible(True)
            self.MapYline1.set_visible(True)
            if self.XSlice.value() > 1:
                self.SpecYline2.set_visible(True)
            if self.YSlice.value() > 1:
                self.SpecXline2.set_visible(True)
            if self.ZSlice.value() > 1:
                self.MapYline2.set_visible(True)
            if self.TSlice.value() > 1:
                self.MapXline2.set_visible(True)
            self.XDCCursor.set_visible(True)
            self.YDCCursor.set_visible(True)
            self.ZDCCursor.set_visible(True)
            self.TDCCursor.set_visible(True)
            self.plotXDC()
            self.plotYDC()
            self.plotZDC()
            self.plotArtist()
            self.cid_mouse = self.canvas.mpl_connect('motion_notify_event', self.navigate)
            self.cid_key = self.canvas.mpl_connect('key_press_event', self.navigate)
        else:
            self.SpecXline1.set_visible(False)
            self.SpecYline1.set_visible(False)
            self.MapXline1.set_visible(False)
            self.MapYline1.set_visible(False)
            self.SpecXline2.set_visible(False)
            self.SpecYline2.set_visible(False)
            self.MapXline2.set_visible(False)
            self.MapYline2.set_visible(False)
            self.XDCCursor.set_visible(False)
            self.YDCCursor.set_visible(False)
            self.ZDCCursor.set_visible(False)
            self.TDCCursor.set_visible(False)
            self.plotXDC()
            self.plotYDC()
            self.plotZDC()
            self.plotArtist()
            self.canvas.mpl_disconnect(self.cid_mouse)
            self.canvas.mpl_disconnect(self.cid_key)

    def navigate(self, event):
        if event.inaxes == self.ax_Spec and event.key == "control":
            self.setXYValue(event.xdata, event.ydata, True)
            self.X.valueChanged.disconnect()
            self.Y.valueChanged.disconnect()
            self.X.setValue(event.xdata)
            self.Y.setValue(event.ydata)
            self.X.valueChanged.connect(self.setValueFromSpinBox)
            self.Y.valueChanged.connect(self.setValueFromSpinBox)
        if event.inaxes == self.ax_Map and event.key == "control":
            self.setZTValue(event.xdata, event.ydata, True)
            self.Z.valueChanged.disconnect()
            self.T.valueChanged.disconnect()
            self.Z.setValue(event.xdata)
            self.T.setValue(event.ydata)
            self.Z.valueChanged.connect(self.setValueFromSpinBox)
            self.T.valueChanged.connect(self.setValueFromSpinBox)

    def OnPress(self, event):
        if (event.inaxes == self.ax_Spec or event.inaxes == self.ax_Map) and event.button == 1:
            if event.inaxes == self.ax_Spec:
                selector0 = self.selector_Spec
            elif event.inaxes == self.ax_Map:
                selector0 = self.selector_Map
            if not selector0.visible: #draw selector from nothing
                selector0.moving_state = "draw"
                selector0.origin = (event.xdata, event.ydata)
                self.cid_drawRS = self.canvas.mpl_connect('motion_notify_event', self.OnDrawRS)
            else:
                dist = selector0.nearestCorner(event.x, event.y)
                if dist < 10:
                    selector0.moving_state = "moveHandle"
                    selector0.origin = (event.xdata, event.ydata)
                    self.cid_moveHandle = self.canvas.mpl_connect('motion_notify_event', self.OnMoveHandle)
                else:
                    if selector0.isinRegion(event.xdata, event.ydata): #move the selector
                        selector0.moving_state = "move"
                        selector0.origin = (event.xdata, event.ydata)
                        self.cid_moveRS = self.canvas.mpl_connect('motion_notify_event', self.OnMoveRS)
                    else:          #clear the selector
                        selector0.set_visible(False)
                        self.plotArtist()

    def OnDrawRS(self, event):
        if (event.inaxes == self.ax_Spec or event.inaxes == self.ax_Map) and event.button == 1:
            if event.inaxes == self.ax_Spec:
                selector0 = self.selector_Spec
            elif event.inaxes == self.ax_Map:
                selector0 = self.selector_Map
            if event.xdata != selector0.origin[0] and event.ydata != selector0.origin[1]:
                selector0.set_visible(True)
                selector0.resize(selector0.origin[0], selector0.origin[1], event.xdata, event.ydata)
                self.plotArtist()

    def OnMoveRS(self, event):
        if (event.inaxes == self.ax_Spec or event.inaxes == self.ax_Map) and event.button == 1:
            if event.inaxes == self.ax_Spec:
                selector0 = self.selector_Spec
            elif event.inaxes == self.ax_Map:
                selector0 = self.selector_Map
            xmin, ymin, xmax, ymax = selector0.region
            selector0.resize(xmin+event.xdata-selector0.origin[0], ymin+event.ydata-selector0.origin[1], xmax+event.xdata-selector0.origin[0], ymax+event.ydata-selector0.origin[1])
            self.plotArtist()
            selector0.origin = (event.xdata, event.ydata)

    def OnMoveHandle(self, event):
        if (event.inaxes == self.ax_Spec or event.inaxes == self.ax_Map) and event.button == 1:
            if event.inaxes == self.ax_Spec:
                selector0 = self.selector_Spec
            elif event.inaxes == self.ax_Map:
                selector0 = self.selector_Map
            xmin, ymin, xmax, ymax = selector0.region
            if selector0.active_handle == 0:
                selector0.resize(xmin+event.xdata-selector0.origin[0], ymin+event.ydata-selector0.origin[1], xmax, ymax)
            elif selector0.active_handle == 1:
                selector0.resize(xmin, ymin+event.ydata-selector0.origin[1], xmax, ymax)
            elif selector0.active_handle == 2:
                selector0.resize(xmin, ymin+event.ydata-selector0.origin[1], xmax+event.xdata-selector0.origin[0], ymax)
            elif selector0.active_handle == 3:
                selector0.resize(xmin, ymin, xmax+event.xdata-selector0.origin[0], ymax)
            elif selector0.active_handle == 4:
                selector0.resize(xmin, ymin, xmax+event.xdata-selector0.origin[0], ymax+event.ydata-selector0.origin[1])
            elif selector0.active_handle == 5:
                selector0.resize(xmin, ymin, xmax, ymax+event.ydata-selector0.origin[1])
            elif selector0.active_handle == 6:
                selector0.resize(xmin+event.xdata-selector0.origin[0], ymin, xmax, ymax+event.ydata-selector0.origin[1])
            elif selector0.active_handle == 7:
                selector0.resize(xmin+event.xdata-selector0.origin[0], ymin, xmax, ymax)
            self.plotArtist()
            selector0.origin = (event.xdata, event.ydata)

    def OnRelease(self, event):
        if event.inaxes == self.ax_Spec or event.inaxes == self.ax_Map:
            if event.inaxes == self.ax_Spec:
                selector0 = self.selector_Spec
            elif event.inaxes == self.ax_Map:
                selector0 = self.selector_Map
            if event.button == 1:
                if selector0.moving_state == "draw":
                    self.canvas.mpl_disconnect(self.cid_drawRS)
                elif selector0.moving_state == "move":
                    self.canvas.mpl_disconnect(self.cid_moveRS)
                elif selector0.moving_state == "moveHandle":
                    self.canvas.mpl_disconnect(self.cid_moveHandle)
            if event.button == 3:
                if selector0.visible and selector0.isinRegion(event.xdata, event.ydata):
                    self.CropAction.setEnabled(True)
                    self.SelectMenu.setEnabled(True)
                    if event.inaxes == self.ax_Spec:
                        #self.CropAction.triggered.connect(lambda: self.crop('Spec'))
                        self.SelectX.setEnabled(True)
                        self.SelectY.setEnabled(True)
                        self.SelectXY.setEnabled(True)
                        self.SelectZ.setEnabled(False)
                        self.SelectT.setEnabled(False)
                        self.SelectZT.setEnabled(False)
                    elif event.inaxes == self.ax_Map:
                        #self.CropAction.triggered.connect(lambda: self.crop('Map'))
                        self.SelectX.setEnabled(False)
                        self.SelectY.setEnabled(False)
                        self.SelectXY.setEnabled(False)
                        self.SelectZ.setEnabled(True)
                        self.SelectT.setEnabled(True)
                        self.SelectZT.setEnabled(True)
                else:
                    self.CropAction.setEnabled(False)
                    self.SelectMenu.setEnabled(False)
                self.showContextMenu()
        else:
            if event.button == 3:
                self.CropAction.setEnabled(False)
                self.SelectMenu.setEnabled(False)
                self.showContextMenu()

    def OnKeyPress(self, event):
        if event.key == 'ctrl+a':
            if self.toolPanel.isChecked():
                self.toolPanel.setChecked(False)
            else:
                self.toolPanel.setChecked(True)

    def showContextMenu(self):       
        self.contextMenu.move(QCursor.pos())
        self.contextMenu.show()

    def plotSpec(self, cmap, useblit):
        for img in self.ax_Spec.get_images():
            img.remove()
        self.Specimg = self.ax_Spec.imshow(self.Spec.T, cmap=cmap, origin="lower", extent=(self.data.xmin-0.5*self.data.xstep, self.data.xmax+0.5*self.data.xstep, self.data.ymin-0.5*self.data.ystep, self.data.ymax+0.5*self.data.ystep), aspect=self.spec_aspect, interpolation='none')
        visible_flag = self.selector_Spec.visible
        self.selector_Spec.set_visible(False)
        if useblit:
            self.ax_Spec.redraw_in_frame()
            self.canvas.blit(self.Specbbox)
        else:
            pass
        self.background_Spec = self.canvas.copy_from_bbox(self.Specbbox) #this line makes sure that the background will be updated when user change color map
        self.selector_Spec.set_visible(visible_flag)

    def plotMap(self, cmap, useblit):
        for img in self.ax_Map.get_images():
            img.remove()
        self.Mapimg = self.ax_Map.imshow(self.Map.T, cmap=cmap, origin="lower", extent=(self.data.zmin-0.5*self.data.zstep, self.data.zmax+0.5*self.data.zstep, self.data.tmin-0.5*self.data.tstep, self.data.tmax+0.5*self.data.tstep), aspect=self.map_aspect, interpolation='none')
        visible_flag = self.selector_Map.visible
        self.selector_Map.set_visible(False)
        if useblit:
            self.ax_Map.redraw_in_frame()
            self.canvas.blit(self.Mapbbox)
        else:
            pass
        self.background_Map = self.canvas.copy_from_bbox(self.Mapbbox) #this line makes sure that the background will be updated when user change color map
        self.selector_Map.set_visible(visible_flag)

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
        self.ax_YDC.set_xbound(lower=minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_YDC.set_ybound(lower=self.data.ymin-self.data.ystep*0.5, upper=self.data.ymax+self.data.ystep*0.5)

    def plotZDC(self):
        self.resetZDC()
        self.canvas.restore_region(self.background_ZDC)
        self.ax_ZDC.draw_artist(self.ZDCLine)
        self.ax_ZDC.draw_artist(self.ZDCCursor)
        self.canvas.blit(self.ZDCbbox)

    def resetZDC(self):
        mask = np.isnan(self.ZDC)
        self.ZDCLine.set_data(self.data.zscale[~mask], self.ZDC[~mask])
        if len(self.ZDC[~mask]) > 1:
            minvalue = min(self.ZDC[~mask])
            maxvalue = max(self.ZDC[~mask])
            if minvalue == maxvalue:
                minvalue = minvalue - 0.5
                maxvalue = maxvalue + 0.5
        else:
            minvalue = 0
            maxvalue = 1
        self.ax_ZDC.set_ybound(lower=minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_ZDC.set_xbound(lower=self.data.zmin-self.data.zstep*0.5, upper=self.data.zmax+self.data.zstep*0.5)

    def plotTDC(self):
        self.resetTDC()
        self.canvas.restore_region(self.background_TDC)
        self.ax_TDC.draw_artist(self.TDCLine)
        self.ax_TDC.draw_artist(self.TDCCursor)
        self.canvas.blit(self.TDCbbox)

    def resetTDC(self):
        mask = np.isnan(self.TDC)
        self.TDCLine.set_data(self.TDC[~mask], self.data.tscale[~mask])
        if len(self.TDC[~mask]) > 1:
            minvalue = min(self.TDC[~mask])
            maxvalue = max(self.TDC[~mask])
            if minvalue == maxvalue:
                minvalue = minvalue - 0.5
                maxvalue = maxvalue + 0.5
        else:
            minvalue = 0
            maxvalue = 1
        self.ax_TDC.set_xbound(lower=minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_TDC.set_ybound(lower=self.data.tmin-self.data.tstep*0.5, upper=self.data.tmax+self.data.tstep*0.5)

    def plotArtist(self):
        self.canvas.restore_region(self.background_Spec)
        for line in self.ax_Spec.get_lines():
            self.ax_Spec.draw_artist(line)
        for artist in self.selector_Spec.artist:
            self.ax_Spec.draw_artist(artist)
        self.canvas.blit(self.Specbbox)
        self.canvas.restore_region(self.background_Map)
        for line in self.ax_Map.get_lines():
            self.ax_Map.draw_artist(line)
        for artist in self.selector_Map.artist:
            self.ax_Map.draw_artist(artist)
        self.canvas.blit(self.Mapbbox)

    def updateAxesPosition(self, useDraw):
        x_Spec, y_Spec, w_Spec, h_Spec = self.ax_Spec.get_position().bounds
        x_Map, y_Map, w_Map, h_Map = self.ax_Map.get_position().bounds
        x_XDC, y_XDC, w_XDC, h_XDC = self.ax_XDC.get_position().bounds
        x_YDC, y_YDC, w_YDC, h_YDC = self.ax_YDC.get_position().bounds
        x_ZDC, y_ZDC, w_ZDC, h_ZDC = self.ax_ZDC.get_position().bounds
        x_TDC, y_TDC, w_TDC, h_TDC = self.ax_TDC.get_position().bounds
        self.ax_XDC.set_position([x_Spec, y_XDC, w_Spec, h_XDC])
        self.ax_YDC.set_position([x_YDC, y_Spec, w_YDC, h_Spec])
        self.ax_ZDC.set_position([x_Map, y_ZDC, w_Map, h_ZDC])
        self.ax_TDC.set_position([x_TDC, y_Map, w_TDC, h_Map])
        visible_Spec_flag = self.selector_Spec.visible
        visible_Map_flag = self.selector_Map.visible
        self.selector_Spec.set_visible(False)
        self.selector_Map.set_visible(False)
        if useDraw:
            self.canvas.draw()
        self.GetWhiteBackground()
        self.selector_Spec.set_visible(visible_Spec_flag)
        self.selector_Map.set_visible(visible_Map_flag)
        self.plotXDC()
        self.plotYDC()
        self.plotZDC()
        self.plotTDC()
        self.plotArtist()

    def resizeEvent_wrapper(self):
        self.updateAxesPosition(False)