#!/Users/Ben/Code/anaconda2/envs/py3/bin/python

import sys
import py4DSTEM.process.utils.constants as ct
import py4DSTEM.file.sqlite.database as database
from PyQt5 import QtCore, QtWidgets, QtGui


# Set global style parameters
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

default_font = 'Times New Roman'

titleFont = QtGui.QFont()
titleFont.setFamily(default_font)
titleFont.setPointSize(12)
titleFont.setItalic(False)
titleFont.setBold(True)

sectionFont = QtGui.QFont()
sectionFont.setFamily(default_font)
sectionFont.setPointSize(12)
sectionFont.setItalic(False)
sectionFont.setBold(False)

normalFont = QtGui.QFont()
normalFont.setFamily(default_font)
normalFont.setPointSize(12)
normalFont.setItalic(False)
normalFont.setBold(False)

smallFont = QtGui.QFont()
smallFont.setFamily(default_font)
smallFont.setPointSize(10)
smallFont.setItalic(False)
smallFont.setBold(False)

control_panel_width=500


class ControlPanel(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # Container widget
        scrollableWidget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self)

        ############## Make sub-widgets ###############
        # Provide handles to connect to their widgets #
        ###############################################

        ########### Preprocessing sub-widget ##########
        # self.widget_LoadPreprocessSave = HideableWidget('Load, Preprocess, Save',LoadPreprocessSaveWidget())
        self.preprocessingTabs = PreprocessingTabs()
        # self.lineEdit_LoadFile = self.widget_LoadPreprocessSave.widget.lineEdit_LoadFile
        # self.pushButton_BrowseFiles = self.widget_LoadPreprocessSave.widget.pushButton_BrowseFiles
        self.spinBox_Nx = self.preprocessingTabs.reshapeTab.spinBox_Nx
        self.spinBox_Ny = self.preprocessingTabs.reshapeTab.spinBox_Ny
        self.spinBox_Bin_Real = self.preprocessingTabs.binTab.spinBox_Bin_Real
        self.spinBox_Bin_Diffraction = self.preprocessingTabs.binTab.spinBox_Bin_Diffraction
        self.pushButton_BinData = self.preprocessingTabs.binTab.pushButton_BinData
        self.checkBox_Crop_Real = self.preprocessingTabs.cropTab.checkBox_Crop_Real
        self.checkBox_Crop_Diffraction = self.preprocessingTabs.cropTab.checkBox_Crop_Diffraction
        self.pushButton_CropData = self.preprocessingTabs.cropTab.pushButton_CropData
        self.pushButton_EditFileMetadata = self.preprocessingTabs.editMetaTab.pushButton_EditFileMetadata
        self.pushButton_EditDirectoryMetadata = self.preprocessingTabs.editMetaTab.pushButton_EditDirectoryMetadata

        self.scalingTabs = ScalingTabs()
        self.buttonGroup_DiffractionMode = self.scalingTabs.diffractionSpaceTab.buttonGroup_DiffractionMode
        self.buttonGroup_realMode = self.scalingTabs.realSpaceTab.buttonGroup_RealMode

        self.detectorModeTabs = DetectorModeTabs()
        self.radioButton_Integrate = self.detectorModeTabs.diffractionSpaceTab.radioButton_Integrate
        self.radioButton_DiffX = self.detectorModeTabs.diffractionSpaceTab.radioButton_DiffX
        self.radioButton_DiffY = self.detectorModeTabs.diffractionSpaceTab.radioButton_DiffY
        self.radioButton_CoMX = self.detectorModeTabs.diffractionSpaceTab.radioButton_CoMX
        self.radioButton_CoMY = self.detectorModeTabs.diffractionSpaceTab.radioButton_CoMY
        self.buttonGroup_DetectorMode = self.detectorModeTabs.diffractionSpaceTab.buttonGroup_DetectorMode

        self.settingTabs = SettingTabs()
        self.checkBox_color = self.settingTabs.settingTab.color_checkbox
        self.checkBox_update = self.settingTabs.settingTab.update_checkbox

        self.detectorShapeTabs = DetectorShapeTabs()
        self.pushBtn_rect_diffractionSpace = self.detectorShapeTabs.diffractionSpaceTab.pushButton_RectDetector
        self.pushBtn_circ_diffractionSpace = self.detectorShapeTabs.diffractionSpaceTab.pushButton_CircDetector
        self.pushBtn_annular_diffractionSpace = self.detectorShapeTabs.diffractionSpaceTab.pushButton_AnnularDetector
        self.pushBtn_point_diffractionSpace = self.detectorShapeTabs.diffractionSpaceTab.pushButton_PointDetector
        self.pushBtn_rect_realSpace = self.detectorShapeTabs.realSpaceTab.pushButton_RectDetector
        self.pushBtn_circ_realSpace = self.detectorShapeTabs.realSpaceTab.pushButton_CircDetector
        self.pushBtn_annular_realSpace = self.detectorShapeTabs.realSpaceTab.pushButton_AnnularDetector
        self.pushBtn_point_realSpace = self.detectorShapeTabs.realSpaceTab.pushButton_PointDetector

        self.analysisTabs = AnalysisTabs()
        self.pushButton_LaunchStrain = self.analysisTabs.analysisTab.singleCrystal_pushbutton
        ####################################################
        ############## Create and set layout ###############
        ####################################################

        layout.addWidget(self.preprocessingTabs,2)
        layout.addWidget(self.scalingTabs,1)
        layout.addWidget(self.detectorModeTabs,1)
        layout.addWidget(self.settingTabs,0.5)
        layout.addWidget(self.detectorShapeTabs,2)
        layout.addWidget(self.analysisTabs,0.5)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        # layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        scrollableWidget.setLayout(layout)

        # Scroll Area Properties
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollableWidget)
        scrollArea.setFrameStyle(QtWidgets.QFrame.NoFrame)

        # Set the scroll area container to fill the layout of the entire ControlPanel widget
        vLayout = QtWidgets.QVBoxLayout(self)
        vLayout.addWidget(scrollArea)
        vLayout.setSpacing(0)
        vLayout.setContentsMargins(0,0,0,0)
        self.setLayout(vLayout)

        # Set geometry
        # self.setFixedHeight(600)
        # self.setFixedWidth(300)


############ Control panel sub-widgets ############

class PreprocessingTabs(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)

        self.reshapeTab = self.ReshapeTab()
        self.binTab = self.BinTab()
        self.cropTab = self.CropTab()
        self.editMetaTab = self.EditMetaTab()

        self.addTab(self.reshapeTab, " reshape ")
        self.addTab(self.binTab, " bin ")
        self.addTab(self.cropTab, " crop ")
        self.addTab(self.editMetaTab, " metadata edit ")

    class ReshapeTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.spinBox_Nx = QtWidgets.QSpinBox()
            self.spinBox_Ny = QtWidgets.QSpinBox()
            self.spinBox_Nx.setMinimum(1)
            self.spinBox_Ny.setMinimum(1)
            self.spinBox_Nx.setMaximum(1000000)
            self.spinBox_Ny.setMaximum(1000000)
            self.label_Nx = QtWidgets.QLabel("Nx")
            self.label_Ny = QtWidgets.QLabel("Ny")
            self.label_Reshape = QtWidgets.QLabel("Reshape  ")

            self.spinBox_Nx.setMaximumWidth(60)
            self.spinBox_Ny.setMaximumWidth(60)

            self.spinBox_Nx.setFont(normalFont)
            self.spinBox_Ny.setFont(normalFont)
            self.label_Nx.setFont(smallFont)
            self.label_Ny.setFont(smallFont)
            self.label_Reshape.setFont(normalFont)

            layout_Reshape_Nx = QtWidgets.QHBoxLayout()
            layout_Reshape_Nx.addWidget(self.label_Nx, 0, QtCore.Qt.AlignCenter)
            layout_Reshape_Nx.addWidget(self.spinBox_Nx, 1, QtCore.Qt.AlignCenter)
            layout_Reshape_Ny = QtWidgets.QHBoxLayout()
            layout_Reshape_Ny.addWidget(self.label_Ny, 0, QtCore.Qt.AlignCenter)
            layout_Reshape_Ny.addWidget(self.spinBox_Ny, 1, QtCore.Qt.AlignCenter)

            layout_Reshape_N = QtWidgets.QVBoxLayout()
            layout_Reshape_N.addLayout(layout_Reshape_Nx, 0)
            layout_Reshape_N.addLayout(layout_Reshape_Ny, 0)

            layout_Reshape = QtWidgets.QHBoxLayout()
            layout_Reshape.addWidget(self.label_Reshape, 4, QtCore.Qt.AlignCenter)
            layout_Reshape.addLayout(layout_Reshape_N, 5)
            # layout_Reshape.setContentsMargins(0,0,0,13)
            self.setLayout(layout_Reshape)

    class BinTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.spinBox_Bin_Real = QtWidgets.QSpinBox()
            self.spinBox_Bin_Diffraction = QtWidgets.QSpinBox()
            self.spinBox_Bin_Real.setMaximum(1000)
            self.spinBox_Bin_Diffraction.setMaximum(1000)
            self.pushButton_BinData = QtWidgets.QPushButton("Bin")

            self.spinBox_Bin_Real.setFont(normalFont)
            self.spinBox_Bin_Diffraction.setFont(normalFont)
            self.label_Bin_Q = QtWidgets.QLabel("Q ")
            self.label_Bin_R = QtWidgets.QLabel("R ")
            self.label_Bin_Q.setFont(smallFont)
            self.label_Bin_R.setFont(smallFont)
            self.pushButton_BinData.setFont(normalFont)

            layout_Bin_Diffraction = QtWidgets.QHBoxLayout()
            layout_Bin_Diffraction.addWidget(self.label_Bin_Q, 0, QtCore.Qt.AlignCenter)
            layout_Bin_Diffraction.addWidget(self.spinBox_Bin_Diffraction, 0, QtCore.Qt.AlignCenter)
            layout_Bin_Real = QtWidgets.QHBoxLayout()
            layout_Bin_Real.addWidget(self.label_Bin_R, 0, QtCore.Qt.AlignCenter)
            layout_Bin_Real.addWidget(self.spinBox_Bin_Real, 0, QtCore.Qt.AlignCenter)

            layout_Bin_SpinBoxes = QtWidgets.QVBoxLayout()
            layout_Bin_SpinBoxes.addLayout(layout_Bin_Diffraction)
            layout_Bin_SpinBoxes.addLayout(layout_Bin_Real)

            layout_Bin = QtWidgets.QHBoxLayout()
            layout_Bin.addLayout(layout_Bin_SpinBoxes, 2)
            layout_Bin.addWidget(self.pushButton_BinData, 1, QtCore.Qt.AlignCenter)
            # layout_Bin.setContentsMargins(10,0,0,0)
            self.setLayout(layout_Bin)

    class CropTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.checkBox_Crop_Real = QtWidgets.QCheckBox()
            self.checkBox_Crop_Diffraction = QtWidgets.QCheckBox()
            self.pushButton_CropData = QtWidgets.QPushButton("Crop")
            self.label_Crop_Q = QtWidgets.QLabel("Q ")
            self.label_Crop_R = QtWidgets.QLabel("R ")

            self.pushButton_CropData.setFont(normalFont)
            self.label_Crop_Q.setFont(smallFont)
            self.label_Crop_R.setFont(smallFont)

            layout_Crop_Diffraction = QtWidgets.QHBoxLayout()
            layout_Crop_Diffraction.addWidget(self.label_Crop_Q, 0, QtCore.Qt.AlignCenter)
            layout_Crop_Diffraction.addWidget(self.checkBox_Crop_Diffraction, 0, QtCore.Qt.AlignCenter)
            layout_Crop_Real = QtWidgets.QHBoxLayout()
            layout_Crop_Real.addWidget(self.label_Crop_R, 0, QtCore.Qt.AlignCenter)
            layout_Crop_Real.addWidget(self.checkBox_Crop_Real, 0, QtCore.Qt.AlignCenter)

            layout_Crop_CheckBoxes = QtWidgets.QVBoxLayout()
            layout_Crop_CheckBoxes.addLayout(layout_Crop_Diffraction)
            layout_Crop_CheckBoxes.addLayout(layout_Crop_Real)

            layout_Crop = QtWidgets.QHBoxLayout()
            layout_Crop.addLayout(layout_Crop_CheckBoxes)
            layout_Crop.addWidget(self.pushButton_CropData,alignment=QtCore.Qt.AlignCenter)
            layout_Crop.setSpacing(0)
            # layout_Crop.setContentsMargins(0,0,10,0)
            self.setLayout(layout_Crop)

    class EditMetaTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.pushButton_EditFileMetadata = QtWidgets.QPushButton("File")
            self.pushButton_EditDirectoryMetadata = QtWidgets.QPushButton("Directory")
            self.label_EditMetadata = QtWidgets.QLabel("Edit Metadata")

            self.pushButton_EditFileMetadata.setMaximumWidth(80)
            self.pushButton_EditDirectoryMetadata.setMaximumWidth(100)

            self.pushButton_EditFileMetadata.setFont(normalFont)
            self.pushButton_EditDirectoryMetadata.setFont(normalFont)
            self.label_EditMetadata.setFont(normalFont)

            layout_EditMetadata_Buttons = QtWidgets.QHBoxLayout()
            layout_EditMetadata_Buttons.addWidget(self.pushButton_EditDirectoryMetadata)
            layout_EditMetadata_Buttons.addWidget(self.pushButton_EditFileMetadata)

            layout_EditMetadata = QtWidgets.QVBoxLayout()
            layout_EditMetadata.addWidget(self.label_EditMetadata, 1, alignment=QtCore.Qt.AlignCenter)
            layout_EditMetadata.addLayout(layout_EditMetadata_Buttons, 1)

            self.setLayout(layout_EditMetadata)


class ScalingTabs(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)

        self.diffractionSpaceTab = self.DiffractionSpaceTab()
        self.realSpaceTab = self.RealSpaceTab()

        self.addTab(self.diffractionSpaceTab, " Diffraction Space ")
        self.addTab(self.realSpaceTab, " Real Space ")

    class DiffractionSpaceTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            diffraction_mode_widget_layout = QtWidgets.QVBoxLayout()

            self.radioButton_DP_Raw = QtWidgets.QRadioButton('Raw')
            self.radioButton_DP_Sqrt = QtWidgets.QRadioButton('Square Root')
            self.radioButton_DP_Log = QtWidgets.QRadioButton('Logartihm')
            self.radioButton_DP_EWPC = QtWidgets.QRadioButton('EWPC')

            diffraction_mode_widget_layout.addWidget(self.radioButton_DP_Raw)
            diffraction_mode_widget_layout.addWidget(self.radioButton_DP_Sqrt)
            diffraction_mode_widget_layout.addWidget(self.radioButton_DP_Log)
            diffraction_mode_widget_layout.addWidget(self.radioButton_DP_EWPC)

            self.buttonGroup_DiffractionMode = QtWidgets.QButtonGroup()
            self.buttonGroup_DiffractionMode.addButton(self.radioButton_DP_Raw)
            self.buttonGroup_DiffractionMode.addButton(self.radioButton_DP_Sqrt)
            self.buttonGroup_DiffractionMode.addButton(self.radioButton_DP_Log)
            self.buttonGroup_DiffractionMode.addButton(self.radioButton_DP_EWPC)

            self.buttonGroup_DiffractionMode.setId(self.radioButton_DP_Raw, 0)
            self.buttonGroup_DiffractionMode.setId(self.radioButton_DP_Sqrt, 1)
            self.buttonGroup_DiffractionMode.setId(self.radioButton_DP_Log, 2)
            self.buttonGroup_DiffractionMode.setId(self.radioButton_DP_EWPC, 3)

            self.setLayout(diffraction_mode_widget_layout)

    class RealSpaceTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            real_mode_widget_layout = QtWidgets.QVBoxLayout()

            self.radioButton_DP_Raw = QtWidgets.QRadioButton('Raw')
            self.radioButton_DP_Sqrt = QtWidgets.QRadioButton('Square Root')
            self.radioButton_DP_Log = QtWidgets.QRadioButton('Logartihm')
            self.radioButton_DP_EWPC = QtWidgets.QRadioButton('EWPC')

            real_mode_widget_layout.addWidget(self.radioButton_DP_Raw)
            real_mode_widget_layout.addWidget(self.radioButton_DP_Sqrt)
            real_mode_widget_layout.addWidget(self.radioButton_DP_Log)
            real_mode_widget_layout.addWidget(self.radioButton_DP_EWPC)

            self.buttonGroup_RealMode = QtWidgets.QButtonGroup()
            self.buttonGroup_RealMode.addButton(self.radioButton_DP_Raw)
            self.buttonGroup_RealMode.addButton(self.radioButton_DP_Sqrt)
            self.buttonGroup_RealMode.addButton(self.radioButton_DP_Log)
            self.buttonGroup_RealMode.addButton(self.radioButton_DP_EWPC)

            self.buttonGroup_RealMode.setId(self.radioButton_DP_Raw, 0)
            self.buttonGroup_RealMode.setId(self.radioButton_DP_Sqrt, 1)
            self.buttonGroup_RealMode.setId(self.radioButton_DP_Log, 2)
            self.buttonGroup_RealMode.setId(self.radioButton_DP_EWPC, 3)

            self.setLayout(real_mode_widget_layout)


class DetectorModeTabs(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)

        self.diffractionSpaceTab = self.DiffractionSpaceTab()

        self.addTab(self.diffractionSpaceTab, " Diffraction Space ")

    class DiffractionSpaceTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            # Detector mode
            detector_mode_widget = QtWidgets.QWidget()
            detector_mode_widget_layout = QtWidgets.QVBoxLayout()

            self.radioButton_Integrate = QtWidgets.QRadioButton('Integrate')
            self.radioButton_DiffX = QtWidgets.QRadioButton('Difference, X')
            self.radioButton_DiffY = QtWidgets.QRadioButton('Difference, Y')
            self.radioButton_CoMX = QtWidgets.QRadioButton('Center of Mass, X')
            self.radioButton_CoMY = QtWidgets.QRadioButton('Center of Mass, Y')

            self.radioButton_Integrate.setFont(normalFont)
            self.radioButton_DiffX.setFont(normalFont)
            self.radioButton_DiffY.setFont(normalFont)
            self.radioButton_CoMX.setFont(normalFont)
            self.radioButton_CoMY.setFont(normalFont)

            detector_mode_widget_layout.addWidget(self.radioButton_Integrate)
            detector_mode_widget_layout.addWidget(self.radioButton_DiffX)
            detector_mode_widget_layout.addWidget(self.radioButton_DiffY)
            detector_mode_widget_layout.addWidget(self.radioButton_CoMX)
            detector_mode_widget_layout.addWidget(self.radioButton_CoMY)
            # detector_mode_widget.setLayout(detector_mode_widget_layout)

            # Create detector mode button group
            self.buttonGroup_DetectorMode = QtWidgets.QButtonGroup()
            self.buttonGroup_DetectorMode.addButton(self.radioButton_Integrate)
            self.buttonGroup_DetectorMode.addButton(self.radioButton_DiffX)
            self.buttonGroup_DetectorMode.addButton(self.radioButton_DiffY)
            self.buttonGroup_DetectorMode.addButton(self.radioButton_CoMX)
            self.buttonGroup_DetectorMode.addButton(self.radioButton_CoMY)

            self.buttonGroup_DetectorMode.setId(self.radioButton_Integrate, ct.DetectorModeType.integrate)
            self.buttonGroup_DetectorMode.setId(self.radioButton_DiffX, ct.DetectorModeType.diffX)
            self.buttonGroup_DetectorMode.setId(self.radioButton_DiffY, ct.DetectorModeType.diffY)
            self.buttonGroup_DetectorMode.setId(self.radioButton_CoMX, ct.DetectorModeType.CoMX)
            self.buttonGroup_DetectorMode.setId(self.radioButton_CoMY, ct.DetectorModeType.CoMY)

            self.setLayout(detector_mode_widget_layout)


class DetectorShapeTabs(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)

        self.diffractionSpaceTab = self.DiffractionSpaceTab()
        self.realSpaceTab = self.RealSpaceTab()

        self.addTab(self.diffractionSpaceTab, "Diffraction Space")
        self.addTab(self.realSpaceTab, "Real Space")

    class DiffractionSpaceTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            detector_shape_button_group = QtWidgets.QWidget()
            detector_shape_button_layout = QtWidgets.QHBoxLayout()
            self.pushButton_RectDetector = QtWidgets.QPushButton('Rectangular')
            self.pushButton_CircDetector = QtWidgets.QPushButton('Circular')
            self.pushButton_AnnularDetector = QtWidgets.QPushButton('Annular')
            self.pushButton_PointDetector = QtWidgets.QPushButton('Pick')
            self.pushButton_RectDetector.setFont(normalFont)
            self.pushButton_CircDetector.setFont(normalFont)
            self.pushButton_AnnularDetector.setFont(normalFont)
            self.pushButton_PointDetector.setFont(normalFont)
            detector_shape_button_layout.addWidget(self.pushButton_RectDetector)
            detector_shape_button_layout.addWidget(self.pushButton_CircDetector)
            detector_shape_button_layout.addWidget(self.pushButton_AnnularDetector)
            detector_shape_button_layout.addWidget(self.pushButton_PointDetector)
            detector_shape_button_group.setLayout(detector_shape_button_layout)

            self.detector_shape_group = QtWidgets.QWidget()
            self.detector_shape_group_widget_layout = QtWidgets.QVBoxLayout()
            self.detector_shape_group.setLayout(self.detector_shape_group_widget_layout)
            # self.detector_shape_group_widget_layout.setContentsMargins(0, 20, 0, 20)
            self.detector_shape_group_widget_layout.addStretch(0)
            # Scroll Widget
            self.detector_shape_group_scrollable = QtWidgets.QWidget()
            self.detector_shape_group_scrollable.layout = QtWidgets.QVBoxLayout()
            self.detector_shape_group_scrollable.layout.addWidget(self.detector_shape_group)
            self.detector_shape_group_scrollable.setLayout(self.detector_shape_group_scrollable.layout)

            # Scroll Area Properties
            scrollArea = QtWidgets.QScrollArea()
            # scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            # scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            scrollArea.setWidgetResizable(True)
            scrollArea.setWidget(self.detector_shape_group)
            scrollArea.setFrameStyle(QtWidgets.QFrame.NoFrame)
            scrollArea.setContentsMargins(0,0,0,0)

            self.layout = QtWidgets.QVBoxLayout()
            self.layout.addWidget(detector_shape_button_group)
            self.layout.addWidget(scrollArea)
            self.setLayout(self.layout)
            self.layout.setSpacing(0)
            self.layout.setContentsMargins(0,0,0,0)

    class RealSpaceTab(DiffractionSpaceTab):
        pass


class SettingTabs(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)

        self.settingTab = self.SettingTab()

        self.addTab(self.settingTab, "Setting")

    class SettingTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.layout = QtWidgets.QVBoxLayout()
            self.setLayout(self.layout)
            self.color_checkbox = QtWidgets.QCheckBox("Color (only sum)")
            self.update_checkbox = QtWidgets.QCheckBox("real time update")
            self.layout.addWidget(self.color_checkbox)
            self.layout.addWidget(self.update_checkbox)


class DetectorShapeWidget(QtWidgets.QWidget):
    def __init__(self, shape:str, name:str=None):
        super().__init__()
        self.keyEvent_list = []
        self.enterEvent_list = []
        self.leaveEvent_list = []
        self.mouseReleaseEvent_list = []
        self.colorChangedEvent_list = []
        self.frame = QtWidgets.QFrame()
        self.frame_layout = QtWidgets.QVBoxLayout()
        self.frame.setLayout(self.frame_layout)
        self.frame_layout.setSpacing(0)
        self.frame_layout.setContentsMargins(5,5,5,5)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.layout.addWidget(self.frame)

        self.titlebar = QtWidgets.QFrame()
        self.titlebar_layout = QtWidgets.QHBoxLayout()
        self.titlebar_layout.setContentsMargins(0,0,0,0)
        self.titlebar.setLayout(self.titlebar_layout)

        # Hide Toggle #
        self.hide_checkBox = QtWidgets.QCheckBox()
        self.titlebar_layout.addWidget(self.hide_checkBox)

        # Shape Name #
        self.shapeName = QtWidgets.QLabel("Rectangular mask")
        self.shapeName.setFont(normalFont)
        self.shapeName.setAlignment(Qt.AlignLeft)
        self.titlebar_layout.addWidget(self.shapeName, 2)

        # More Settings CheckBox #
        self.moreSetting_checkBox = QtWidgets.QCheckBox()
        self.titlebar_layout.addWidget(self.moreSetting_checkBox, alignment=Qt.AlignRight)
        # Change hide/show checkboxes to triangles
        # self.titlebar.setStyleSheet(
        #     "background-color: #000000;"
        #     "QCheckBox::indicator {width:14;height: 14px;}"
        #     "QCheckBox::indicator:checked { image:url(./gui/icons/arrow_open.png)}"
        #     "QCheckBox::indicator:unchecked { image:url(./gui/icons/arrow_closed.png)}"
        # )

        # Color Button #
        self.colorButton = QtWidgets.QPushButton("color")
        self.colorButton.setObjectName("colorButton")
        self.titlebar_layout.addWidget(self.colorButton)
        self.colorDialog = QtWidgets.QColorDialog()

        # Del button #
        self.delButton = QtWidgets.QPushButton("Del")
        self.titlebar_layout.addWidget(self.delButton)

        self.frame_layout.addWidget(self.titlebar)

        self.bottom = QtWidgets.QWidget()
        self.bottomGridLayout = QtWidgets.QGridLayout()
        self.bottomGridLayout.setContentsMargins(0,0,0,10)
        self.bottom.setLayout(self.bottomGridLayout)
        self.frame_layout.addWidget(self.bottom)
        self.frame.setObjectName("frame")
        self.frame_layout.setSpacing(0)
        self.frame.setStyleSheet("QFrame#frame{border: 3px solid #444a4f;}")
                                 # "QFrame#frame:hover{border: 3px solid #FFFF00;}")


        # BottomGrid #
        self.firstLineLabel = QtWidgets.QLabel("x , y")
        self.firstLineLabel.setAlignment(Qt.AlignCenter)
        self.firstLineLabel.setMinimumWidth(100)

        self.firstLineText1 = QtWidgets.QDoubleSpinBox()
        self.firstLineText1.setMaximumHeight(25)
        self.firstLineText1.setAlignment(Qt.AlignCenter)
        self.firstLineText1.setMinimum(-1000)
        self.firstLineText1.setMaximum(2000)

        self.firstLineText2 = QtWidgets.QDoubleSpinBox()
        self.firstLineText2.setMaximumHeight(25)
        self.firstLineText2.setAlignment(Qt.AlignCenter)
        self.firstLineText2.setMinimum(-1000)
        self.firstLineText2.setMaximum(2000)

        self.secondLineLabel = QtWidgets.QLabel("")
        self.secondLineLabel.setMinimumWidth(100)
        self.secondLineLabel.setAlignment(Qt.AlignCenter)

        self.secondLineText1 = QtWidgets.QDoubleSpinBox()
        self.secondLineText1.setMinimum(1)
        self.secondLineText1.setMaximumHeight(25)
        self.secondLineText1.setAlignment(Qt.AlignCenter)

        self.secondLineText2 = QtWidgets.QDoubleSpinBox()
        self.secondLineText2.setMinimum(1)
        self.secondLineText2.setMaximumHeight(25)
        self.secondLineText2.setAlignment(Qt.AlignCenter)

        self.bottomGridLayout.addWidget(self.firstLineLabel, 0, 0)
        self.bottomGridLayout.addWidget(self.firstLineText1, 0, 1)
        self.bottomGridLayout.addWidget(self.firstLineText2, 0, 2)
        self.bottomGridLayout.addWidget(self.secondLineLabel, 1, 0)
        self.bottomGridLayout.addWidget(self.secondLineText1, 1, 1)
        self.bottomGridLayout.addWidget(self.secondLineText2, 1, 2)

        if name is None:
            if shape == ct.DetectorShape.rectangular:
                name = "Rectangular Detector"
            elif shape == ct.DetectorShape.circular:
                name = "Circular Detector"
            elif shape == ct.DetectorShape.circular:
                name = "Annular Detector"
            elif shape == ct.DetectorShape.point:
                name = "Point Detector"
        self.shapeName.setText(name)

        if shape == ct.DetectorShape.rectangular:
            self.secondLineLabel.setText("size X,Y")
        if shape == ct.DetectorShape.circular:
            self.firstLineLabel.setText("center x, y")
            self.secondLineLabel.setText("radius")
            self.secondLineText2.hide()
        if shape == ct.DetectorShape.annular:
            self.firstLineLabel.setText("center x, y")
            self.secondLineLabel.setText("out/inner rad")
        if shape == ct.DetectorShape.point:
            self.secondLineLabel.hide()
            self.secondLineText1.hide()
            self.secondLineText2.hide()



        self.bottom.setVisible(False)
        self.moreSetting_checkBox.stateChanged.connect(self.bottom.setVisible)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)

    def addKeyEvent(self, func):
        self.keyEvent_list.append(func)
    def addEnterEvent(self, func):
        self.enterEvent_list.append(func)
    def addLeaveEvent(self, func):
        self.leaveEvent_list.append(func)
    def addMouseReleaseEvent(self, func):
        self.mouseReleaseEvent_list.append(func)


    def keyReleaseEvent(self, a0: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(a0)
        if a0.key() in (QtCore.Qt.Key_Down,QtCore.Qt.Key_Up,QtCore.Qt.Key_Enter,QtCore.Qt.Key_Return):
            for func in self.keyEvent_list:
                func()
    def enterEvent(self, a0: QtCore.QEvent) -> None:
        super().enterEvent(a0)
        for func in self.enterEvent_list:
            func()
    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        super().leaveEvent(a0)
        for func in self.leaveEvent_list:
            func()
    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        super().mouseReleaseEvent(a0)
        for func in self.mouseReleaseEvent_list:
            func()

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        pass
    def focusInEvent(self, a0: QtGui.QFocusEvent) -> None:
        super().focusInEvent(a0)


class AnalysisTabs(QtWidgets.QTabWidget):
    def __init__(self):
        QtWidgets.QTabWidget.__init__(self)

        self.analysisTab = self.AnalysisTab()

        self.addTab(self.analysisTab, "analysis")

    class AnalysisTab(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            self.layout = QtWidgets.QHBoxLayout()
            self.setLayout(self.layout)
            self.singleCrystal_pushbutton = QtWidgets.QPushButton("Single Crystal")
            self.layout.addWidget(self.singleCrystal_pushbutton)

class SaveWidget(QtWidgets.QWidget):
    """
    Takes one argument - save_path - a string with a filename for the output file.
    """
    def __init__(self, save_path):
        QtWidgets.QWidget.__init__(self)

        # Label, Line Edit
        self.label_SaveAs = QtWidgets.QLabel("Save as: ")
        self.lineEdit_SavePath = QtWidgets.QLineEdit(save_path)
        self.pushButton_Execute = QtWidgets.QPushButton("Save")
        self.pushButton_Cancel = QtWidgets.QPushButton("Cancel")

        # Layout
        top_row = QtWidgets.QHBoxLayout()
        top_row.addWidget(self.label_SaveAs, stretch=0)
        top_row.addWidget(self.lineEdit_SavePath, stretch=5)

        bottom_row = QtWidgets.QHBoxLayout()
        bottom_row.addWidget(self.pushButton_Cancel,0,QtCore.Qt.AlignLeft)
        bottom_row.addWidget(self.pushButton_Execute,0,QtCore.Qt.AlignRight)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

        self.setLayout(layout)
        #self.setFixedWidth(260)
        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed))


class EditMetadataWidget(QtWidgets.QWidget):
    """
    Creates a widget for viewing and editing metadata. Must receive a DataCube object as an
    argument, to populate metadata fields.
    """
    def __init__(self, datacube):
        QtWidgets.QWidget.__init__(self)

        self.tab_microscope = self.make_tab(datacube.metadata.microscope)
        self.tab_sample = self.make_tab(datacube.metadata.sample)
        self.tab_user = self.make_tab(datacube.metadata.user)
        self.tab_calibration = self.make_tab(datacube.metadata.calibration)

        # Comments tab - make separately to create larger text box
        tab_comments_layout = QtWidgets.QVBoxLayout()
        for key,value in datacube.metadata.comments.items():
            current_comment = QtWidgets.QVBoxLayout()
            label = QtWidgets.QLabel(key)
            try:
                text = value.decode('utf-8')
            except AttributeError:
                text = str(value)
            textedit = QtWidgets.QPlainTextEdit(text)
            current_comment.addWidget(label,0,QtCore.Qt.AlignLeft)
            current_comment.addWidget(textedit)
            tab_comments_layout.addLayout(current_comment)
        self.tab_comments = QtWidgets.QWidget()
        self.tab_comments.setLayout(tab_comments_layout)

        # Add all tabs to TabWidget
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.tab_microscope,"Microscope")
        self.tabs.addTab(self.tab_sample,"Sample")
        self.tabs.addTab(self.tab_user,"User")
        self.tabs.addTab(self.tab_calibration,"Calibration")
        self.tabs.addTab(self.tab_comments,"Comments")

        # Excute
        self.pushButton_Save = QtWidgets.QPushButton("Save")
        self.pushButton_Cancel = QtWidgets.QPushButton("Cancel")

        layout_Execute = QtWidgets.QHBoxLayout()
        layout_Execute.addWidget(self.pushButton_Cancel)
        layout_Execute.addWidget(self.pushButton_Save)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)
        layout.addLayout(layout_Execute)

        self.setLayout(layout)
        #self.setFixedWidth(260)
        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed))

    @staticmethod
    def make_tab(metadata_dict):
        tab_layout = QtWidgets.QVBoxLayout()
        for key,value in metadata_dict.items():
            current_row = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(key)
            try:
                text = value.decode('utf-8')
            except AttributeError:
                text = str(value)
            lineedit = QtWidgets.QLineEdit(text)
            lineedit.setFixedWidth(180)
            current_row.addWidget(label,0,QtCore.Qt.AlignRight)
            current_row.addWidget(lineedit,0,QtCore.Qt.AlignRight)
            tab_layout.addLayout(current_row)
        tab = QtWidgets.QWidget()
        tab.setLayout(tab_layout)
        return tab

# used in panel.py
class SectionLabel(QtWidgets.QWidget):
    def __init__(self,section_title):
        QtWidgets.QWidget.__init__(self)

        line_left = QtWidgets.QFrame()
        line_left.setFrameShape(QtWidgets.QFrame.HLine)
        line_left.setFrameShadow(QtWidgets.QFrame.Sunken)
        line_left.setLineWidth(1)
        line_right = QtWidgets.QFrame()
        line_right.setFrameShape(QtWidgets.QFrame.HLine)
        line_right.setFrameShadow(QtWidgets.QFrame.Sunken)
        line_right.setLineWidth(1)

        label = QtWidgets.QLabel(section_title)
        label.setFont(sectionFont)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(line_left)
        layout.addWidget(label,0,QtCore.Qt.AlignCenter)
        layout.addWidget(line_right)

        self.setLayout(layout)


class TitleBar(QtWidgets.QWidget):

    def __init__(self, mainWindow:QMainWindow, parent):
        self.parent = parent
        super().__init__()

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.mainWindow = mainWindow
        self.menu = self.createMenu(mainWindow)
        self.window_control = self.WindowControlBar(mainWindow)
        self.label_filename = QtWidgets.QLabel("filename")

        self.layout.addWidget(self.menu,alignment=Qt.AlignLeft)
        self.layout.addWidget(self.label_filename, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.window_control,alignment=Qt.AlignRight)

        self.setMaximumHeight(50)
        self.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def createMenu(self, mainWindow:QMainWindow):
        menubar = mainWindow.menuBar()
        filemenu = menubar.addMenu('    &File    ')
        openmenu = filemenu.addMenu('   &open  ')
        self._openRecentMenu = filemenu.addMenu('   &open Recent File  ')
        save_menu = filemenu.addMenu('   &save  ')
        save_current_image_menu = filemenu.addMenu('   &save_current_image  ')

        # OPENMENU
        self.openAuto = QtWidgets.QAction("&auto", self)
        self.openDM = QtWidgets.QAction("&DM Memory Map", self)
        self.openGatan = QtWidgets.QAction("&Gatan K2 Binary", self)
        self.openEMPAD = QtWidgets.QAction("&EMPAD", self)
        # openAuto.triggered.connect(openFile)
        openmenu.addAction(self.openAuto)
        openmenu.addAction(self.openDM)
        openmenu.addAction(self.openGatan)
        openmenu.addAction(self.openEMPAD)

        self.addRecentFileMenu()

        # Save Menu
        self.save_as_file = QtWidgets.QAction("&save as file", self)
        self.save_as_directory = QtWidgets.QAction("&save as directory", self)
        save_menu.addAction(self.save_as_file)
        save_menu.addAction(self.save_as_directory)


        self.save_diffraction_space = QtWidgets.QAction("&diffraction space", self)
        self.save_real_space = QtWidgets.QAction("&real space", self)
        save_current_image_menu.addAction(self.save_diffraction_space)
        save_current_image_menu.addAction(self.save_real_space)

        menubar.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        return menubar

    def addRecentFile(self, filePath):
        # insert recent file to database
        db = database.DBFileList()
        db.insertOpenFileList(filePath, "type:not implemented yet")
        self.addRecentFileMenu()

    def addRecentFileMenu(self):
        # Open Recent Menu
        self._openRecentMenu.clear()
        self.openRecentFileActionList = []
        fileList = database.DBFileList().getOpenFileList()
        fileList.reverse()
        for file in fileList:
            filePath = file[1]
            qAction = QtWidgets.QAction("&" + filePath, self)
            # self.openRecentFileActionList.append(qAction)
            qAction.triggered.connect(self.test(qAction))
            qAction.triggered.connect(self.update_value(qAction))
            self._openRecentMenu.addAction(qAction)

    def test(self, qAction):
        return lambda: self.mainWindow.load_file(0, filePath=qAction.text()[1:])
    def update_value(self, qAction):
        return lambda: self.mainWindow.settings.data_filename.update_value(qAction.text()[1:])


    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.window_control.mainWindow.isMaximized():
            return

        if self.window_control.isMaximized():
            return

        if not hasattr(self, 'pressing'):
            return


        if self.pressing:
            self.end = self.mapToGlobal(a0.pos())
            self.movement = self.end - self.start
            self.parent.setGeometry(self.mapToGlobal(self.movement).x(),
                                    self.mapToGlobal(self.movement).y(),
                                    self.parent.width(),
                                    self.parent.height())
            self.start = self.end

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.start = self.mapToGlobal(a0.pos())
        self.pressing = True

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self.pressing = False

    def mouseDoubleClickEvent(self, a0: QtGui.QMouseEvent) -> None:
        if self.window_control.mainWindow.isMaximized():
            self.window_control.showNormal()
        else :
            self.window_control.showMaximized()

    class WindowControlBar(QtWidgets.QWidget):
        def __init__(self, mainWindow: QMainWindow):
            super().__init__()
            BUTTON_WIDTH = 5
            BUTTON_HEIGHT = 20
            self.layout = QtWidgets.QHBoxLayout()
            self.setLayout(self.layout)
            self.setContentsMargins(0, 0, 0, 0)
            self.layout.setContentsMargins(0, 0, 0, 0)
            self.layout.setSpacing(0)
            self.ButtonMin = QtWidgets.QPushButton("─")
            self.ButtonMin.setFixedSize(QtCore.QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
            self.ButtonMin.setObjectName("ButtonMin")
            # self.ButtonMin.setIcon(QtGui.QIcon("./icons/minimize.png"))
            self.ButtonMax = QtWidgets.QPushButton("□")
            self.ButtonMax.setFixedSize(QtCore.QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
            self.ButtonMax.setObjectName("ButtonMax")
            self.ButtonRestore = QtWidgets.QPushButton("□")
            self.ButtonRestore.setFixedSize(QtCore.QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
            self.ButtonRestore.setObjectName("ButtonRestore")
            self.ButtonRestore.setVisible(False)
            self.ButtonClose = QtWidgets.QPushButton("×")
            self.ButtonClose.setFixedSize(QtCore.QSize(BUTTON_WIDTH, BUTTON_HEIGHT))
            self.ButtonClose.setObjectName("ButtonClose")
            self.layout.addWidget(self.ButtonMin)
            self.layout.addWidget(self.ButtonMax)
            self.layout.addWidget(self.ButtonRestore)
            self.layout.addWidget(self.ButtonClose)
            self.mainWindow = mainWindow.main_window
            self.ButtonMin.clicked.connect(self.showMinimized)
            self.ButtonMax.clicked.connect(self.showMaximized)
            self.ButtonRestore.clicked.connect(self.showNormal)
            self.ButtonClose.clicked.connect(self.close)

        def showMinimized(self):
            self.mainWindow.showMinimized()

        def showMaximized(self):
            self.mainWindow.showMaximized()
            self.ButtonMax.setVisible(False)
            self.ButtonRestore.setVisible(True)

        def showNormal(self):
            self.mainWindow.showNormal()
            self.ButtonMax.setVisible(True)
            self.ButtonRestore.setVisible(False)

        def close(self):
            self.mainWindow.close()




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    controlPanel = ControlPanel()
    controlPanel.show()

    app.exec_()


#app = QtWidgets.QApplication(sys.argv)
#controlPanel = ControlPanel()
#controlPanel.show()
#sys.exit(app.exec_())
