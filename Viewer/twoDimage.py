'''
2D Image Viewer Module
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
from matplotlib.widgets import RectangleSelector
import numpy as np
import scipy.interpolate as ip
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QPushButton, QGroupBox, QSpinBox,
QDoubleSpinBox, QLabel, QSizePolicy, QSlider, QFormLayout, QFrame, QStyleFactory, QComboBox, QCheckBox, QMenu)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QCursor
from Data import Spectrum
from Viewer.Selector import Selector
from Viewer.colormap import CustomComboBox
import glob, os, copy


class twoDimage(QWidget):
    def __init__(self, viewer):
        super(twoDimage, self).__init__()
        self.data = Spectrum()
        self.viewer = viewer
        self.aspect = "auto"

        #init Image
        self.fig = Figure(figsize=(5, 3), dpi=150)
        gs = GridSpec(3, 3, figure=self.fig)
        self.ax_XDC = self.fig.add_subplot(gs[0, 0:2]) # X Distribution Curve
        self.ax_Spec = self.fig.add_subplot(gs[1:, 0:2]) # Spectrum
        self.ax_YDC = self.fig.add_subplot(gs[1:, -1]) # Y Distribution Curve
        self.lx1 = self.ax_Spec.axhline(self.ax_Spec.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  # the horiz line 1
        self.ly1 = self.ax_Spec.axvline(self.ax_Spec.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  # the vert line 1
        self.lx2 = self.ax_Spec.axhline(self.ax_Spec.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  # the horiz line 2
        self.ly2 = self.ax_Spec.axvline(self.ax_Spec.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  # the vert line 2
        self.vl = self.ax_XDC.axvline(self.ax_XDC.get_xbound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)
        self.hl = self.ax_YDC.axhline(self.ax_YDC.get_ybound()[0], visible=False, animated=True, color='k', linestyle='--', linewidth=0.75)  # the horiz line
        self.ax_cmap = self.fig.add_subplot(gs[0, 2]) # color bar
        self.gradient = np.vstack((np.linspace(0, 1, 256), np.linspace(0, 1, 256)))
        self.setTickLabelFont(self.ax_Spec, "Comic Sans MS")
        self.setTickLabelFont(self.ax_XDC, "Comic Sans MS")
        self.setTickLabelFont(self.ax_YDC, "Comic Sans MS")
        self.ax_Spec.set_axisbelow(False)
        self.ax_Spec.tick_params(direction='inout', labelsize=8.5)
        self.ax_XDC.tick_params(axis='x', labelsize=8.5, labelbottom=False)
        self.ax_XDC.tick_params(axis='y', which='both', left=False, labelleft=False)
        self.ax_YDC.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
        self.ax_YDC.tick_params(axis='y', labelsize=8.5, labelleft=False)
        self.fig.subplots_adjust(top=0.96, bottom=0.08, left=0.1, right=0.96, wspace=0.15, hspace=0.15)
        x0, y0, width, height = self.ax_cmap.get_position().bounds
        nheight = height*0.2
        ny0 = y0+height*0.5*(1-0.2)
        self.ax_cmap.set_position([x0, ny0, width, nheight])
        self.ax_cmap.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)
        self.ax_cmap.set_title("Color Scale", {'fontsize': 10}, fontname="Comic Sans Ms")
        self.fig.patch.set_facecolor("None")
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.XDCLine = Line2D(np.array([0]), np.array([0]), color="blue", linewidth=1, animated=True, solid_joinstyle="round")
        self.YDCLine = Line2D(np.array([0]), np.array([0]), color="blue", linewidth=1, animated=True, solid_joinstyle="round")
        self.ax_XDC.add_line(self.XDCLine)
        self.ax_YDC.add_line(self.YDCLine)
        self.selector = Selector(self.ax_Spec, self.canvas)
        self.cid_press = self.canvas.mpl_connect('button_press_event', self.OnPress)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.OnRelease)
        self.cid_keypress = self.canvas.mpl_connect('key_press_event', self.OnKeyPress)
        #self.cid_scroll = self.canvas.mpl_connect('scroll_event', self.OnExpand)

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
        self.XDC_action = self.outputMenu.addAction("XDC")
        self.YDC_action = self.outputMenu.addAction("YDC")

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
        self.X.valueChanged.connect(self.setValueFromSpinBox)
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
        self.Y.valueChanged.connect(self.setValueFromSpinBox)
        self.YLabel = QLabel("Y:")
        self.YLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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
        self.XSlice = QSpinBox()
        self.XSlice.setRange(1, 10000)
        self.XSlice.setSingleStep(2)
        self.XSlice.setKeyboardTracking(False)
        self.XSlice.setStyle(QStyleFactory.create('Fusion'))
        self.XSlice.valueChanged.connect(self.setSlice)
        self.XSliceLabel = QLabel("Slice:")
        self.YSlice = QSpinBox()
        self.YSlice.setRange(1, 10000)
        self.YSlice.setSingleStep(2)
        self.YSlice.setKeyboardTracking(False)
        self.YSlice.setStyle(QStyleFactory.create('Fusion'))
        self.YSlice.valueChanged.connect(self.setSlice)
        self.YSliceLabel = QLabel("Slice:")
        hbox_tool = QHBoxLayout()
        hbox_tool.addStretch(2)
        hbox_tool.addWidget(self.XLabel)
        hbox_tool.addWidget(self.X)
        hbox_tool.addStretch(1)
        hbox_tool.addWidget(self.YLabel)
        hbox_tool.addWidget(self.Y)
        hbox_tool.addStretch(1)
        hbox_tool.addWidget(self.IntLabel)
        hbox_tool.addWidget(self.Int)
        hbox_tool.addStretch(2)
        hbox2_tool = QHBoxLayout()
        hbox2_tool.addWidget(self.XSLabel)
        hbox2_tool.addWidget(self.XSlider)
        hbox2_tool.addWidget(self.XSliceLabel)
        hbox2_tool.addWidget(self.XSlice)
        hbox3_tool = QHBoxLayout()
        hbox3_tool.addWidget(self.YSLabel)
        hbox3_tool.addWidget(self.YSlider)
        hbox3_tool.addWidget(self.YSliceLabel)
        hbox3_tool.addWidget(self.YSlice)
        vbox_tool = QVBoxLayout()
        vbox_tool.addLayout(hbox_tool)
        vbox_tool.addLayout(hbox2_tool)
        vbox_tool.addLayout(hbox3_tool)
        self.toolPanel.setLayout(vbox_tool)

        #color scale
        self.colorPanel = QGroupBox("Color Scale")
        self.colorPanel.setFixedHeight(105)
        self.colorPanel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmapmenu = CustomComboBox()
        self.cmapmenu.setFixedWidth(120)
        self.cmapmenu.setStyle(QStyleFactory.create('Fusion'))
        self.cmapmenu.setCurrentText("twilight")
        self.cmapmenu.currentIndexChanged.connect(self.changecmapbyindex)
        self.Vmin = QDoubleSpinBox()
        self.Vmin.setFixedWidth(100)
        self.Vmin.setRange(-1e15, 1e15)
        self.Vmin.setDecimals(4)
        self.Vmin.setKeyboardTracking(False)
        self.Vmin.valueChanged.connect(self.setDynamicRange)
        self.Vmin.setStyle(QStyleFactory.create('Fusion'))
        self.VminLabel = QLabel("Min:")
        self.VminLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.Vmax = QDoubleSpinBox()
        self.Vmax.setFixedWidth(100)
        self.Vmax.setRange(-1e15, 1e15)
        self.Vmax.setDecimals(4)
        self.Vmax.setKeyboardTracking(False)
        self.Vmax.valueChanged.connect(self.setDynamicRange)
        self.Vmax.setStyle(QStyleFactory.create('Fusion'))
        self.VmaxLabel = QLabel("Max:")
        self.VmaxLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.resetVrange = QPushButton("Re")
        self.resetVrange.setFixedWidth(25)
        self.resetVrange.clicked.connect(self.resetDynamicRange)
        self.resetVrange.setStyle(QStyleFactory.create('Fusion'))
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
        hbox1_cmap = QHBoxLayout()
        hbox1_cmap.addWidget(self.cmapmenu)
        hbox1_cmap.addStretch(1)
        hbox1_cmap.addWidget(self.VminLabel)
        hbox1_cmap.addWidget(self.Vmin)
        hbox1_cmap.addStretch(1)
        hbox1_cmap.addWidget(self.VmaxLabel)
        hbox1_cmap.addWidget(self.Vmax)
        hbox1_cmap.addStretch(1)
        hbox1_cmap.addWidget(self.resetVrange)
        hbox2_cmap = QHBoxLayout()
        hbox2_cmap.addWidget(self.GammaLabel)
        hbox2_cmap.addWidget(self.Gamma)
        hbox2_cmap.addWidget(self.GSlider)
        hbox2_cmap.addWidget(self.revcmap)
        vbox_cmap = QVBoxLayout()
        vbox_cmap.addLayout(hbox1_cmap)
        vbox_cmap.addLayout(hbox2_cmap)
        self.colorPanel.setLayout(vbox_cmap)
        self.colorPanel.setEnabled(False)

        #Layout
        box = QVBoxLayout()
        box.addWidget(self.toolPanel)
        box.addWidget(self.canvas)
        box.addWidget(self.colorPanel)
        self.setLayout(box)

    def loaddata(self, data):
        self.canvas.draw()
        self.selector.set_visible(False)
        self.data = data
        self.GetWhiteBackground()
        self.X.setRange(data.xmin, data.xmax)
        self.X.setSingleStep(data.xstep)
        self.Y.setRange(data.ymin, data.ymax)
        self.Y.setSingleStep(data.ystep)
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
        if data.data[~np.isnan(data.data)].max() > 0:
            self.Vmax.setValue(data.data[~np.isnan(data.data)].max())
            self.Vmin.setValue(data.data[~np.isnan(data.data)].min())
        else:
            self.Vmin.setValue(data.data[~np.isnan(data.data)].min())
            self.Vmax.setValue(data.data[~np.isnan(data.data)].max())
        self.XSlice.setRange(1, self.data.dimension[0])
        self.YSlice.setRange(1, self.data.dimension[1])
        self.plotimage(data, self.getcurrentcmap(), self.Vmin.value(), self.Vmax.value(), False)
        self.updatecolorscale(self.getcurrentcmap(), False)
        self.updateAxesPosition(True)
        self.colorPanel.setEnabled(True)

    def setValueFromSlider(self, value):
        if self.sender() == self.XSlider:
            self.X.setValue(value*(self.X.maximum()-self.X.minimum())/10000+self.X.minimum())
        elif self.sender() == self.YSlider:
            self.Y.setValue(value*(self.Y.maximum()-self.Y.minimum())/10000+self.Y.minimum())

    def setValueFromSpinBox(self, value):
        if self.sender() == self.X:
            self.XSlider.setValue((value-self.X.minimum())/(self.X.maximum()-self.X.minimum())*10000)
            half_wid_num = (self.XSlice.value()-1)/2
            self.ly1.set_xdata(value-self.data.xstep*half_wid_num)
            self.ly2.set_xdata(value+self.data.xstep*half_wid_num)
            self.vl.set_xdata(value)
            self.YDC = self.get_YDC(value)
            self.resetYDC()
            self.plotYDC(True, True)
            self.plotXDC(True, True)
        elif self.sender() == self.Y:
            self.YSlider.setValue((value-self.Y.minimum())/(self.Y.maximum()-self.Y.minimum())*10000)
            half_wid_num = (self.YSlice.value()-1)/2
            self.lx1.set_ydata(value-self.data.ystep*half_wid_num)
            self.lx2.set_ydata(value+self.data.ystep*half_wid_num)
            self.hl.set_ydata(value)
            self.XDC = self.get_XDC(value)
            self.resetXDC()
            self.plotXDC(True, True)
            self.plotYDC(True, True)
        self.plotArtist()
        self.setIntensity()

    def setIntensity(self):
        intensity = self.get_intensity(self.X.value(), self.Y.value())
        if np.isnan(intensity):
            self.Int.setText("NaN")
        elif np.abs(intensity) >= 0.01:
            self.Int.setText("%.2f" % intensity)
        else:
            self.Int.setText("%.2e" % intensity)
    
    def setSlice(self, value):
        if self.sender() == self.XSlice:
            if value % 2 == 0:
                self.XSlice.setValue(value-1)
            else:
                if value == 1:
                    self.ly2.set_visible(False)
                else:
                    self.ly2.set_visible(True)
                half_wid_num = (self.XSlice.value()-1)/2
                self.ly1.set_xdata(self.X.value()-self.data.xstep*half_wid_num)
                self.ly2.set_xdata(self.X.value()+self.data.xstep*half_wid_num)
                self.plotArtist()
                self.YDC = self.get_YDC(self.X.value())
                self.resetYDC()
                self.plotYDC(True, True)
        if self.sender() == self.YSlice:
            if value % 2 == 0:
                self.YSlice.setValue(value-1)
            else:
                if value == 1:
                    self.lx2.set_visible(False)
                else:
                    self.lx2.set_visible(True)
                half_wid_num = (self.YSlice.value()-1)/2
                self.lx1.set_ydata(self.Y.value()-self.data.ystep*half_wid_num)
                self.lx2.set_ydata(self.Y.value()+self.data.ystep*half_wid_num)
                self.plotArtist()
                self.XDC = self.get_XDC(self.Y.value())
                self.resetXDC()
                self.plotXDC(True, True)
        self.setIntensity()

    def setDynamicRange(self, value):
        if self.sender() == self.Vmin:
            if value <= self.Vmax.value():
                self.plotimage(self.data, self.getcurrentcmap(), value, self.Vmax.value(), True)
            else:
                self.plotimage(self.data, self.getcurrentcmap(), self.Vmax.value(), self.Vmax.value(), True)
        elif self.sender() == self.Vmax:
            if value >= self.Vmin.value():
                self.plotimage(self.data, self.getcurrentcmap(), self.Vmin.value(), value, True)
            else:
                self.plotimage(self.data, self.getcurrentcmap(), self.Vmin.value(), self.Vmin.value(), True)

    def resetDynamicRange(self):
        self.Vmin.setValue(self.data.data[~np.isnan(self.data.data)].min())
        self.Vmax.setValue(self.data.data[~np.isnan(self.data.data)].max())
    
    def setTickLabelFont(self, ax, font):
        for tick in ax.get_xticklabels():
            tick.set_fontname(font)
        for tick in ax.get_yticklabels():
            tick.set_fontname(font)
        
    def scale2pnt(self, value, scale):
        return (np.abs(scale - value)).argmin()

    def get_intensity(self, xvalue, yvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        half_wid_xnum = int((self.XSlice.value()-1)/2)
        half_wid_ynum = int((self.YSlice.value()-1)/2)
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
        return self.data.data[xminidx:xmaxidx, yminidx:ymaxidx].sum()

    def get_XDC(self, yvalue):
        yidx = self.scale2pnt(yvalue, self.data.yscale)
        half_wid_num = int((self.YSlice.value()-1)/2)
        if yidx < half_wid_num:
            yminidx = 0
        else:
            yminidx = yidx-half_wid_num
        ymaxidx = yidx+half_wid_num+1
        array = self.data.data[:, yminidx:ymaxidx]
        return np.sum(array, axis=1)

    def get_YDC(self, xvalue):
        xidx = self.scale2pnt(xvalue, self.data.xscale)
        half_wid_num = int((self.XSlice.value()-1)/2)
        if xidx < half_wid_num:
            xminidx = 0
        else:
            xminidx = xidx-half_wid_num
        xmaxidx = xidx+half_wid_num+1
        array = self.data.data[xminidx:xmaxidx, :]
        return np.sum(array, axis=0)

    def getcurrentcmap(self):
        cmap_str = self.cmapmenu.currentText()
        if self.revcmap.checkState() == Qt.Checked:
            cmap_str += "_r"
        raw_cmap = cm.get_cmap(cmap_str, 256)
        linearIndex = np.linspace(0, 1, 256)
        nonlinearIndex = np.power(linearIndex, self.Gamma.value())
        new_cmap = ListedColormap(raw_cmap(nonlinearIndex))
        return new_cmap

    def setGammaFromSpinBox(self, value):
        self.updatecolorscale(self.getcurrentcmap(), True)
        self.plotimage(self.data, self.getcurrentcmap(), self.Vmin.value(), self.Vmax.value(), True)
        self.GSlider.setValue(1000000*np.log(value))

    def setGammaFromSlider(self, value):
        self.Gamma.setValue(np.exp(value/1000000))

    def reversecmap(self, state):
        self.updatecolorscale(self.getcurrentcmap(), True)
        self.plotimage(self.data, self.getcurrentcmap(), self.Vmin.value(), self.Vmax.value(), True)
    
    def changecmapbyindex(self, index):
        self.updatecolorscale(self.getcurrentcmap(), True)
        self.plotimage(self.data, self.getcurrentcmap(), self.Vmin.value(), self.Vmax.value(), True)
    
    def updatecolorscale(self, cmap, removeflag):
        if removeflag:
            for img in self.ax_cmap.get_images():
                img.remove()
        self.cmapimage = self.ax_cmap.imshow(self.gradient, cmap=cmap, origin="lower", aspect="auto")
        self.ax_cmap.redraw_in_frame()
        self.canvas.blit(self.ax_cmap.bbox)

    def begincursor(self, on):
        if on:
            self.lx1.set_visible(True)
            self.ly1.set_visible(True)
            if self.YSlice.value() > 1:
                self.lx2.set_visible(True)
            if self.XSlice.value() > 1:
                self.ly2.set_visible(True)
            self.vl.set_visible(True)
            self.hl.set_visible(True)
            self.plotArtist()
            self.plotXDC(True, True)
            self.plotYDC(True, True)
            self.cid_mouse = self.canvas.mpl_connect('motion_notify_event', self.navigate)
            self.cid_key = self.canvas.mpl_connect('key_press_event', self.navigate)
        else:
            self.lx1.set_visible(False)
            self.ly1.set_visible(False)
            self.lx2.set_visible(False)
            self.ly2.set_visible(False)
            self.vl.set_visible(False)
            self.hl.set_visible(False)
            self.plotXDC(True, False)
            self.plotYDC(True, False)
            self.plotArtist()
            self.canvas.mpl_disconnect(self.cid_mouse)
            self.canvas.mpl_disconnect(self.cid_key)

    def navigate(self, event):
        if event.inaxes == self.ax_Spec and event.key == "control":
            self.X.setValue(event.xdata)
            self.Y.setValue(event.ydata)
        
    def OnPress(self, event):
        if event.inaxes == self.ax_Spec and event.button == 1:
            if not self.selector.visible: #draw selector from nothing
                self.selector.moving_state = "draw"
                self.selector.origin = (event.xdata, event.ydata)
                self.cid_drawRS = self.canvas.mpl_connect('motion_notify_event', self.OnDrawRS)
            else:
                dist = self.selector.nearestCorner(event.x, event.y)
                if dist < 10:
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

    def OnDrawRS(self, event):
        if event.inaxes == self.ax_Spec and event.button == 1:
            if event.xdata != self.selector.origin[0] and event.ydata != self.selector.origin[1]:
                self.selector.set_visible(True)
                self.selector.resize(self.selector.origin[0], self.selector.origin[1], event.xdata, event.ydata)
                self.plotArtist()

    def OnMoveRS(self, event):
        if event.inaxes == self.ax_Spec and event.button == 1:
            xmin, ymin, xmax, ymax = self.selector.region
            self.selector.resize(xmin+event.xdata-self.selector.origin[0], ymin+event.ydata-self.selector.origin[1], xmax+event.xdata-self.selector.origin[0], ymax+event.ydata-self.selector.origin[1])
            self.plotArtist()
            self.selector.origin = (event.xdata, event.ydata)

    def OnMoveHandle(self, event):
        if event.inaxes == self.ax_Spec and event.button == 1:
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
        if event.inaxes == self.ax_Spec:
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
        else:
            if event.button == 3:
                self.CropAction.setEnabled(False)
                self.SelectMenu.setEnabled(False)
                self.showContextMenu()

    def showContextMenu(self):       
        self.contextMenu.move(QCursor.pos())
        self.contextMenu.show()

    def crop(self):
        x0, y0, x1, y1 = self.selector.region
        self.viewer.Win.DataProcessor.tab_single.setSelectXYRange(x0, x1, y0, y1, True)
        self.selector.set_visible(False)
        self.plotArtist()
        self.viewer.Win.DataProcessor.tab_single.crop2D.clicked.emit()

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
        

    def outputData(self):
        if self.sender() == self.XDC_action:
            pass
        elif self.sender() == self.YDC_action:
            pass

    def OnKeyPress(self, event):
        if event.key == 'ctrl+a':
            if self.toolPanel.isChecked():
                self.toolPanel.setChecked(False)
            else:
                self.toolPanel.setChecked(True)

    def GetWhiteBackground(self):
        self.ax_XDC.redraw_in_frame()
        self.canvas.blit(self.ax_XDC.get_window_extent())
        self.ax_YDC.redraw_in_frame()
        self.canvas.blit(self.ax_YDC.get_window_extent())
        self.background_XDC = self.canvas.copy_from_bbox(self.ax_XDC.get_window_extent())
        self.background_YDC = self.canvas.copy_from_bbox(self.ax_YDC.get_window_extent())
        self.background_Spec = self.canvas.copy_from_bbox(self.ax_Spec.get_window_extent())

    def plotArtist(self):
        self.canvas.restore_region(self.background_Spec)
        for line in self.ax_Spec.get_lines():
            self.ax_Spec.draw_artist(line)
        for artist in self.selector.artist:
            self.ax_Spec.draw_artist(artist)
        self.canvas.blit(self.ax_Spec.get_window_extent())
    
    def plotimage(self, data, cmap, vmin, vmax, useblit):
        for img in self.ax_Spec.get_images():
            img.remove()
        self.twoDspec = self.ax_Spec.imshow(data.data.T, cmap=cmap, vmin=vmin, vmax=vmax, origin="lower", extent=(data.xmin-0.5*data.xstep, data.xmax+0.5*data.xstep, data.ymin-0.5*data.ystep, data.ymax+0.5*data.ystep), aspect=self.aspect, interpolation='none')
        self.setTickLabelFont(self.ax_Spec, "Comic Sans MS")
        visible_flag = self.selector.visible
        self.selector.set_visible(False)
        if useblit:
            self.refreshimage()
        else:
            pass
        self.background_Spec = self.canvas.copy_from_bbox(self.ax_Spec.get_window_extent()) #this line makes sure that the background will be updated when user change color map
        self.selector.set_visible(visible_flag)
        self.plotArtist()

    def refreshimage(self):
        self.ax_Spec.redraw_in_frame()
        self.canvas.blit(self.ax_Spec.get_window_extent())

    def plotXDC(self, useblit, usecursor):
        if useblit:
            self.canvas.restore_region(self.background_XDC)
            self.ax_XDC.draw_artist(self.XDCLine)
            if usecursor:
                self.ax_XDC.draw_artist(self.vl)
            self.canvas.blit(self.ax_XDC.get_window_extent())
        else:
            self.canvas.draw()

    def plotYDC(self, useblit, usecursor):      
        if useblit:
            self.canvas.restore_region(self.background_YDC)
            self.ax_YDC.draw_artist(self.YDCLine)
            if usecursor:
                self.ax_YDC.draw_artist(self.hl)
            self.canvas.blit(self.ax_YDC.get_window_extent())
        else:
            self.canvas.draw()

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
        self.ax_XDC.set_ybound(lower= minvalue-0.01*(maxvalue-minvalue), upper=maxvalue+0.01*(maxvalue-minvalue))
        self.ax_XDC.set_xbound(lower=self.data.xmin-self.data.xstep*0.5, upper=self.data.xmax+self.data.xstep*0.5)

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

    def changeAspect(self, state):
        if state:
            self.aspect = "equal"
        else:
            self.aspect = "auto"
        self.ax_Spec.set_aspect(self.aspect)
        self.updateAxesPosition(True)

    def updateAxesPosition(self, useDraw):
        x_Spec, y_Spec, w_Spec, h_Spec = self.ax_Spec.get_position().bounds
        x_XDC, y_XDC, w_XDC, h_XDC = self.ax_XDC.get_position().bounds
        x_YDC, y_YDC, w_YDC, h_YDC = self.ax_YDC.get_position().bounds
        self.ax_XDC.set_position([x_Spec, y_XDC, w_Spec, h_XDC])
        self.ax_YDC.set_position([x_YDC, y_Spec, w_YDC, h_Spec])
        visible_flag = self.selector.visible
        self.selector.set_visible(False)
        if useDraw:
            self.canvas.draw()
        self.GetWhiteBackground()
        self.selector.set_visible(visible_flag)
        self.plotArtist()
        self.plotXDC(True, True)
        self.plotYDC(True, True)

    def resizeEvent_wrapper(self):
        self.updateAxesPosition(False)

