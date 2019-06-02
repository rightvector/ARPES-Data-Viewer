'''
This module provides the visualization class for data by Mayavi.
'''

import os
os.environ['ETS_TOOLKIT'] = 'qt4'
os.environ['QT_API'] = 'pyqt5'
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from tvtk.pyface.api import DecoratedScene
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QMainWindow, QPushButton, QStyleFactory, QGroupBox, 
QDoubleSpinBox, QLabel, QRadioButton, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
import numpy as np


class CustomScene(MayaviScene):
    def _create_control(self, parent):
        # Create a panel as a wrapper of the scene toolkit control.  This
        # allows us to also add additional controls.
        self._panel = QMainWindow()

        # Add our toolbar to the panel.
        tbm = self._get_tool_bar_manager()
        self._tool_bar = tbm.create_tool_bar(self._panel)
        self._tool_bar.setMovable(False)
        self._panel.addToolBar(Qt.RightToolBarArea, self._tool_bar)

        # Create the actual scene content
        self._content = super(DecoratedScene, self)._create_control(self._panel)
        self._panel.setCentralWidget(self._content)

        return self._panel



class Visualization(HasTraits):
    scene = Instance(MlabSceneModel, ())

    # @on_trait_change('scene.activated')
    # def update_plot(self):
    #     self.scene.mlab.test_points3d()

    editor = SceneEditor(scene_class=CustomScene)
    item = Item('scene', editor=editor, height=250, width=300, show_label=False)

    # the layout of the dialog created
    view = View(item, resizable=True)


class MYWidget(QWidget):
    def __init__(self, Win):
        super(MYWidget, self).__init__()
        self.Win = Win
        self.setFocusPolicy(Qt.ClickFocus)
        self.box = QVBoxLayout()

        #scaling factor
        self.scalingFactor_groupbox = QGroupBox("Scaling Factor")
        self.scalingFactor_groupbox.setEnabled(False)
        self.xScalingFactor = QDoubleSpinBox()
        self.xScalingFactor.setStyle(QStyleFactory.create('Fusion'))
        self.xScalingFactor.setDecimals(3)
        self.xScalingFactor.setRange(0.001, 1000)
        self.xScalingFactor.setValue(1)
        self.xScalingFactor.setKeyboardTracking(False)
        self.xScalingFactor.valueChanged.connect(self.changeScalingFactor)
        self.yScalingFactor = QDoubleSpinBox()
        self.yScalingFactor.setStyle(QStyleFactory.create('Fusion'))
        self.yScalingFactor.setDecimals(3)
        self.yScalingFactor.setRange(0.001, 1000)
        self.yScalingFactor.setValue(1)
        self.yScalingFactor.setKeyboardTracking(False)
        self.yScalingFactor.valueChanged.connect(self.changeScalingFactor)
        self.zScalingFactor = QDoubleSpinBox()
        self.zScalingFactor.setStyle(QStyleFactory.create('Fusion'))
        self.zScalingFactor.setDecimals(3)
        self.zScalingFactor.setRange(0.001, 1000)
        self.zScalingFactor.setValue(1)
        self.zScalingFactor.setKeyboardTracking(False)
        self.zScalingFactor.valueChanged.connect(self.changeScalingFactor)
        self.equalXYscaling = QCheckBox("Equal Proportion")
        self.equalXYscaling.stateChanged.connect(self.equalProportion)
        hbox_SF = QHBoxLayout()
        hbox_SF.addStretch(2)
        hbox_SF.addWidget(QLabel("X:"))
        hbox_SF.addWidget(self.xScalingFactor)
        hbox_SF.addWidget(QLabel("Y:"))
        hbox_SF.addWidget(self.yScalingFactor)
        hbox_SF.addWidget(self.equalXYscaling)
        hbox_SF.addStretch(1)
        hbox_SF.addWidget(QLabel("Z:"))
        hbox_SF.addWidget(self.zScalingFactor)
        hbox_SF.addStretch(2)
        self.scalingFactor_groupbox.setLayout(hbox_SF)
        self.box.addWidget(self.scalingFactor_groupbox)

        #3D data parameters
        hbox_3d_title = QHBoxLayout()
        self.volume_check = QRadioButton("Volume")
        self.volume_check.setStyle(QStyleFactory.create('Fusion'))
        self.volume_check.setChecked(True)
        self.volume_check.setEnabled(False)
        self.volume_check.toggled.connect(self.change3Dmode)
        self.isosurf_check = QRadioButton("Iso-Surface")
        self.isosurf_check.setStyle(QStyleFactory.create('Fusion'))
        self.isosurf_check.setEnabled(False)
        hbox_3d_title.addStretch(1)
        hbox_3d_title.addWidget(self.volume_check)
        hbox_3d_title.addStretch(2)
        hbox_3d_title.addWidget(self.isosurf_check)
        hbox_3d_title.addStretch(1)
        self.box.addLayout(hbox_3d_title)
        hbox_3d_widget = QHBoxLayout()
        self.volume_groupbox = QGroupBox()
        hbox_3d_volume = QHBoxLayout()
        self.lowpoint = QDoubleSpinBox()
        self.lowpoint.setStyle(QStyleFactory.create('Fusion'))
        self.lowpoint.setDecimals(3)
        self.lowpoint.setRange(0, 1)
        self.lowpoint.setValue(0)
        self.lowpoint.setKeyboardTracking(False)
        self.lowpoint.valueChanged.connect(self.changeVolumeCmp)
        self.highpoint = QDoubleSpinBox()
        self.highpoint.setStyle(QStyleFactory.create('Fusion'))
        self.highpoint.setDecimals(3)
        self.highpoint.setRange(0, 1)
        self.highpoint.setValue(1)
        self.highpoint.setKeyboardTracking(False)
        self.highpoint.valueChanged.connect(self.changeVolumeCmp)
        hbox_3d_volume.addWidget(QLabel("Vmin:"))
        hbox_3d_volume.addWidget(self.lowpoint)
        hbox_3d_volume.addWidget(QLabel("Vmax:"))
        hbox_3d_volume.addWidget(self.highpoint)
        self.volume_groupbox.setLayout(hbox_3d_volume)
        self.volume_groupbox.setEnabled(False)
        self.iso_groupbox = QGroupBox()
        hbox_3d_iso = QHBoxLayout()
        self.isovalue = QDoubleSpinBox()
        self.isovalue.setStyle(QStyleFactory.create('Fusion'))
        self.isovalue.setDecimals(4)
        self.isovalue.setRange(0, 1)
        self.isovalue.setKeyboardTracking(False)
        self.isovalue.valueChanged.connect(self.changeIsoValue)
        self.isoLabel = QLabel("Iso-Value:")
        self.isoLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hbox_3d_iso.addStretch(1)
        hbox_3d_iso.addWidget(self.isoLabel)
        hbox_3d_iso.addWidget(self.isovalue)
        hbox_3d_iso.addStretch(1)
        self.iso_groupbox.setLayout(hbox_3d_iso)
        self.iso_groupbox.setEnabled(False)
        hbox_3d_widget.addWidget(self.volume_groupbox)
        hbox_3d_widget.addWidget(self.iso_groupbox)
        self.box.addLayout(hbox_3d_widget)


        #visualization ui 
        self.visualization = Visualization()
        self.ui = self.visualization.edit_traits(parent=self, kind='subpanel').control
        self.box.addWidget(self.ui)
        
        self.setLayout(self.box)
        self.setFixedWidth(500)

    def setData(self, Data):
        self.data = Data
        self.visualization.scene.mlab.clf()
        xSF = self.xScalingFactor.value()
        ySF = self.yScalingFactor.value()
        zSF = self.zScalingFactor.value()
        if Data is not None:
            self.scalingFactor_groupbox.setEnabled(True)
            if Data.dims == 2:
                self.Enable3DWidget(False)
                self.source = self.visualization.scene.mlab.pipeline.array2d_source(Data.data)
                self.warp = self.visualization.scene.mlab.pipeline.warp_scalar(self.source)
                self.normals = self.visualization.scene.mlab.pipeline.poly_data_normals(self.warp)
                self.surface = self.visualization.scene.mlab.pipeline.surface(self.normals, extent=(0,xSF,0,ySF,0,zSF))
                self.outline = self.visualization.scene.mlab.pipeline.outline(self.normals, color=(0,0,0), extent=(0,xSF,0,ySF,0,zSF))
                self.outline.actor.property.line_width = 1.5
            elif Data.dims == 3:
                self.Enable3DWidget(True)
                minv = Data.data[~np.isnan(Data.data)].min()
                maxv = Data.data[~np.isnan(Data.data)].max()
                self.source = self.visualization.scene.mlab.pipeline.scalar_field(Data.data)
                if self.volume_check.isChecked():
                    self.volume = self.visualization.scene.mlab.pipeline.volume(self.source, vmin=minv, vmax=maxv)
                    self.outline = self.visualization.scene.mlab.pipeline.outline(self.volume, color=(0,0,0))
                    self.outline.actor.property.line_width = 1.5
                    self.source.spacing = np.array([xSF, ySF, zSF])
                    self.lowpoint.valueChanged.disconnect()
                    self.highpoint.valueChanged.disconnect()
                    self.lowpoint.setRange(minv, maxv)
                    self.lowpoint.setValue(minv)
                    self.highpoint.setRange(minv, maxv)
                    self.highpoint.setValue(maxv)
                    self.lowpoint.valueChanged.connect(self.changeVolumeCmp)
                    self.highpoint.valueChanged.connect(self.changeVolumeCmp)
                if self.isosurf_check.isChecked():
                    self.isosurface = self.visualization.scene.mlab.pipeline.iso_surface(self.source, contours=[(minv+maxv)/2,])
                    self.outline = self.visualization.scene.mlab.pipeline.outline(self.isosurface, color=(0,0,0))
                    self.outline.actor.property.line_width = 1.5
                    self.isovalue.valueChanged.disconnect()
                    self.isovalue.setRange(minv, maxv)
                    self.isovalue.setValue((minv+maxv)/2)
                    self.isovalue.valueChanged.connect(self.changeIsoValue)
                if self.equalXYscaling.isChecked():
                    self.equalProportion(2)
        else:
            self.scalingFactor_groupbox.setEnabled(False)

    def changeScalingFactor(self, value):
        if self.sender() == self.xScalingFactor:
            xSF = value
            ySF = self.yScalingFactor.value()
            zSF = self.zScalingFactor.value()
            if self.data.dims == 2 or 3:
                spacing = self.source.spacing
                spacing[0] = xSF
                self.source.spacing = np.array(spacing)
        elif self.sender() == self.yScalingFactor:
            xSF = self.xScalingFactor.value()
            ySF = value
            zSF = self.zScalingFactor.value()
            if self.data.dims == 2 or 3:
                spacing = self.source.spacing
                spacing[1] = ySF
                self.source.spacing = np.array(spacing)
        elif self.sender() == self.zScalingFactor:
            xSF = self.xScalingFactor.value()
            ySF = self.yScalingFactor.value()
            zSF = value
            if self.data.dims == 2:
                normal = self.warp.filter.normal
                normal[2] = zSF
                self.warp.filter.normal = np.array(normal)
            if self.data.dims == 3:
                spacing = self.source.spacing
                spacing[2] = zSF
                self.source.spacing = np.array(spacing)

    def equalProportion(self, state):
        if state == 2:
            xSF = self.xScalingFactor.value()
            ySF = xSF*self.data.ystep/self.data.xstep
            self.yScalingFactor.setValue(ySF)
            self.xScalingFactor.setEnabled(False)
            self.yScalingFactor.setEnabled(False)
        elif state == 0:
            self.xScalingFactor.setEnabled(True)
            self.yScalingFactor.setEnabled(True)

    def change3Dmode(self, state):
        if state:
            self.volume_groupbox.setEnabled(True)
            self.iso_groupbox.setEnabled(False)
        else:
            self.volume_groupbox.setEnabled(False)
            self.iso_groupbox.setEnabled(True)
        self.setData(self.data)

    def changeVolumeCmp(self, value):
        self.source.children[0].children[:] = []
        if self.sender() == self.lowpoint:
            self.volume = self.visualization.scene.mlab.pipeline.volume(self.source, vmin=value)
        if self.sender() == self.highpoint:
            self.volume = self.visualization.scene.mlab.pipeline.volume(self.source, vmax=value)
        self.outline = self.visualization.scene.mlab.pipeline.outline(self.volume, color=(0,0,0))
        self.outline.actor.property.line_width = 1.5

    def changeIsoValue(self, value):
        self.source.children[0].children[:] = []
        self.isosurface = self.visualization.scene.mlab.pipeline.iso_surface(self.source, contours=[value,])
        self.outline = self.visualization.scene.mlab.pipeline.outline(self.isosurface, color=(0,0,0))
        self.outline.actor.property.line_width = 1.5

    def Enable3DWidget(self, state):
        self.volume_check.setEnabled(state)
        self.isosurf_check.setEnabled(state)
        if state:
            if self.volume_check.isChecked():
                self.volume_groupbox.setEnabled(True)
            else:
                self.iso_groupbox.setEnabled(True)
        else:
            self.volume_groupbox.setEnabled(False)
            self.iso_groupbox.setEnabled(False)