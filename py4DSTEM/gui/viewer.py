################################ Viewer for 4D STEM data ####################################
#                                                                                           #
# Defines a class -- DataViewer -- creating a GUI for interacting with 4D STEM datasets.    #
#                                                                                           #
#                                                                                           #
# Relevant documentation for lower level code:                                              #
#                                                                                           #
# Qt is being run through PyQt5.  See http://pyqt.sourceforge.net/Docs/PyQt5/.              #
#                                                                                           #
# pyqtgraph facilitates fast-running scientific visualization.  See http://pyqtgraph.org/.  #
# pyqtgraph is being used for the final data displays.                                      #
#                                                                                           #
# ScopeFoundry is an open source package for control of laboratory experiments as well as   #
# some scientific data visualization.  See http://www.scopefoundry.org/.  This code uses    #
# a simplified version of ScopeFoundry's LoggedQuantity and LQCollection objects to serve   #
# as an interface connecting GUI entries, stored quantities, and updates to visualiation    #
# and analysis; see gui/utils.py.                                                           #
#                                                                                           #
#############################################################################################

from __future__ import division, print_function
from PyQt5.QtCore import Qt
import time
from ..process.imaging import compute
from ..process.utils import constants as cs
from skimage import io
from . import detector

from .dialogs import ControlPanel, SaveWidget, EditMetadataWidget, DetectorShapeWidget, TitleBar
from .gui_utils import datacube_selector
from ..file.datastructure.datacube import DataCube
from .strain import *

import IPython
if IPython.version_info[0] < 4:
    from IPython.qt.console.rich_ipython_widget import RichIPythonWidget as RichJupyterWidget
    from IPython.qt.inprocess import QtInProcessKernelManager
else:
    from qtconsole.rich_jupyter_widget import RichJupyterWidget
    from qtconsole.inprocess import QtInProcessKernelManager


class DataViewer(QtWidgets.QMainWindow):
    """
    The class is used by instantiating and then entering the main Qt loop with, e.g.:
        app = DataViewer(sys.argv)
        app.exec_()
    """
    def __init__(self, argv):
        """
        Initialize class, setting up windows and widgets.
        """
        # flag
        self.updating_roi = False

        QtWidgets.QApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        # Define this as the QApplication object
        self.qtapp = QtWidgets.QApplication.instance()
        if not self.qtapp:
            self.qtapp = QtWidgets.QApplication(argv)
        QtWidgets.QMainWindow.__init__(self)
        self.this_dir, self.this_filename = os.path.split(__file__)

        # Make settings collection
        self.settings = LQCollection()

        self.strain_window = None

        self.main_window = QtWidget_Key(self)
        self.main_window.setWindowFlags(Qt.FramelessWindowHint)

        # TitleBar
        self.titleBar = TitleBar(self, self.main_window)

        # Set up sub-windows and arrange into primary py4DSTEM window
        self.setup_diffraction_space_widget()
        self.setup_real_space_widget()
        self.setup_control_widget()
        # self.setup_console_widget()
        self.setup_main_window()

        # create detector Group
        self.detectorGroup_diffractionSpace = detector.DetectorGroup(viewer=self,
                                                                     imageView=self.diffraction_space_widget,
                                                                     layout_to_put_widget=self.control_widget.detectorShapeTabs.diffractionSpaceTab.detector_shape_group_widget_layout,
                                                                     widget=DetectorShapeWidget)
        self.detectorGroup_realSpace = detector.DetectorGroup(viewer=self,
                                                              imageView=self.real_space_widget,
                                                              layout_to_put_widget=self.control_widget.detectorShapeTabs.realSpaceTab.detector_shape_group_widget_layout,
                                                              widget=DetectorShapeWidget)

        import qdarkstyle
        self.main_window.setStyleSheet(qdarkstyle.load_stylesheet())

        # Set up temporary datacube
        self.datacube = DataCube(data=np.zeros((10,10,10,10)))

        # Set up initial views in real and diffraction space
        self.update_diffraction_space_view()
        # self.update_virtual_detector_mode()
        self.diffraction_space_widget.ui.normDivideRadio.setChecked(True)
        self.diffraction_space_widget.normRadioChanged()


    def addShape_diffractionSpace(self, shape_type):
        detector = self.detectorGroup_diffractionSpace.addDetector(shape_type)
        self.roiSignalBinding(detector,True)
        self.widgetSignalBinding(detector,True)
        self.update_real_space_view()
        return detector

    def addShape_realSpace(self, shape_type):
        detector = self.detectorGroup_realSpace.addDetector(shape_type)
        self.roiSignalBinding(detector, False)
        self.widgetSignalBinding(detector, False)
        self.update_diffraction_space_view()
        return detector

    def roiSignalBinding(self, detector: detector.Detector, diffractionSpace:bool):
        detector.rois[0].sigRegionChangeFinished.connect(detector.roi_to_dialog_update)



        if diffractionSpace:
            detector.rois[0].sigRegionChangeFinished.connect(lambda: self.update_real_space_view(False))
        else:
            detector.rois[0].sigRegionChangeFinished.connect(lambda: self.update_diffraction_space_view(False))

        # Treat Annular Circle
        if detector.shape_type == cs.DetectorShape.annular:
            detector.rois[0].sigRegionChangeFinished.connect(lambda: print("rois0"))
            detector.rois[1].sigRegionChangeFinished.connect(lambda: print("rois1"))

            detector.rois[1].sigRegionChangeFinished.connect(detector.roi_to_dialog_update)
            if diffractionSpace:
                detector.rois[1].sigRegionChangeFinished.connect(self.update_real_space_view)
            else:
                detector.rois[1].sigRegionChangeFinished.connect(self.update_diffraction_space_view)



        detector.rois[0].setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        detector.rois[0].sigClicked.connect(lambda: self.select(detector))

    def select(self, detector: detector.Detector):
        if detector.selected:
            detector.unselectEvent()
            delattr(self, 'selected_detector')
        else:
            if hasattr(self, 'selected_detector'):
                self.selected_detector.unselectEvent()
            self.selected_detector = detector
            detector.selectEvent()


    dtt:detector.Detector
    def widgetSignalBinding(self, detector: detector.Detector, diffractionSpace:bool):

        # Mouse Hovering Event #
        detector.controlWidget.addKeyEvent(detector.dialog_to_roi_update)

        detector.controlWidget.addEnterEvent(
            lambda: detector.rois[0].setPen(color='y') if not detector.selected else 0)
        detector.controlWidget.addEnterEvent(
            lambda: detector.controlWidget.frame.setStyleSheet("QFrame#frame{border: 3px solid #ffff00;}") if not detector.selected else 0)

        detector.controlWidget.addLeaveEvent(
            lambda: detector.rois[0].setPen(color=detector.color) if not detector.selected else 0)
        detector.controlWidget.addLeaveEvent(
            lambda: detector.controlWidget.frame.setStyleSheet("QFrame#frame{border: 3px solid #444a4f;}") if not detector.selected else 0)

        detector.controlWidget.addMouseReleaseEvent(
            lambda: detector.controlWidget.setStyleSheet("QFrame#frame{border: 3px solid #ff0000;}") if not detector.selected else 0)
        detector.controlWidget.addMouseReleaseEvent(
            lambda: self.select(detector))

        # Delete Button #
        if diffractionSpace:
            detector.controlWidget.delButton.clicked.connect(
                lambda: self.detectorGroup_diffractionSpace.deleteDetector(detector))
            detector.controlWidget.delButton.clicked.connect(
                self.update_real_space_view)
        else:
            detector.controlWidget.delButton.clicked.connect(
                lambda: self.detectorGroup_realSpace.deleteDetector(detector))
            detector.controlWidget.delButton.clicked.connect(
                self.update_diffraction_space_view)

    ###############################################
    ############ Widget setup methods #############
    ###############################################


    def setup_control_widget(self):
        """
        Set up the control window for diffraction space.
        """
        #self.control_widget = load_qt_ui_file(sibling_path(__file__, "control_widget.ui"))
        self.control_widget = ControlPanel()
        self.control_widget.setWindowTitle("Control Panel")

        ############################ Controls ###############################
        # For each control:                                                 # 
        #   -creates items in self.settings                                 #
        #   -connects UI changes to updates in self.settings                # 
        #   -connects updates in self.settings items to function calls      #
        #   -connects button clicks to function calls                       #
        #####################################################################

        ## Load ##
        self.settings.New('data_filename',dtype='file')
        self.settings.data_filename.connect_to_browse_widgets(self.titleBar.label_filename, self.titleBar.openAuto)
        self.settings.data_filename.connect_to_browse_widgets(self.titleBar.label_filename, self.titleBar.openDM)
        self.settings.data_filename.connect_to_browse_widgets(self.titleBar.label_filename, self.titleBar.openGatan)
        self.settings.data_filename.connect_to_browse_widgets(self.titleBar.label_filename, self.titleBar.openEMPAD)
        self.titleBar.openAuto.triggered.connect(lambda: self.load_file(0))
        self.titleBar.openDM.triggered.connect(lambda: self.load_file(1))
        self.titleBar.openGatan.triggered.connect(lambda: self.load_file(2))
        self.titleBar.openEMPAD.triggered.connect(lambda: self.load_file(3))
        # self.settings.data_filename.updated_value.connect(lambda x: self.load_file(mode=0))

        ## Preprocess ##
        self.settings.New('R_Nx', dtype=int, initial=1)
        self.settings.New('R_Ny', dtype=int, initial=1)
        self.settings.New('bin_r', dtype=int, initial=1)
        self.settings.New('bin_q', dtype=int, initial=1)
        self.settings.New('crop_r_showROI', dtype=bool, initial=False)
        self.settings.New('crop_q_showROI', dtype=bool, initial=False)
        self.settings.New('isCropped_r', dtype=bool, initial=False)
        self.settings.New('isCropped_q', dtype=bool, initial=False)
        self.settings.New('crop_rx_min', dtype=int, initial=0)
        self.settings.New('crop_rx_max', dtype=int, initial=0)
        self.settings.New('crop_ry_min', dtype=int, initial=0)
        self.settings.New('crop_ry_max', dtype=int, initial=0)
        self.settings.New('crop_qx_min', dtype=int, initial=0)
        self.settings.New('crop_qx_max', dtype=int, initial=0)
        self.settings.New('crop_qy_min', dtype=int, initial=0)
        self.settings.New('crop_qy_max', dtype=int, initial=0)

        self.settings.R_Nx.connect_bidir_to_widget(self.control_widget.spinBox_Nx)
        self.settings.R_Ny.connect_bidir_to_widget(self.control_widget.spinBox_Ny)
        self.settings.bin_r.connect_bidir_to_widget(self.control_widget.spinBox_Bin_Real)
        self.settings.bin_q.connect_bidir_to_widget(self.control_widget.spinBox_Bin_Diffraction)
        self.settings.crop_r_showROI.connect_bidir_to_widget(self.control_widget.checkBox_Crop_Real)
        self.settings.crop_q_showROI.connect_bidir_to_widget(self.control_widget.checkBox_Crop_Diffraction)

        self.settings.R_Nx.updated_value.connect(self.update_scan_shape_Nx)
        self.settings.R_Ny.updated_value.connect(self.update_scan_shape_Ny)
        self.settings.crop_r_showROI.updated_value.connect(self.toggleCropROI_real)
        self.settings.crop_q_showROI.updated_value.connect(self.toggleCropROI_diffraction)

        self.control_widget.pushButton_CropData.clicked.connect(self.crop_data)
        self.control_widget.pushButton_BinData.clicked.connect(self.bin_data)
        self.control_widget.pushButton_EditFileMetadata.clicked.connect(self.edit_file_metadata)
        self.control_widget.pushButton_EditDirectoryMetadata.clicked.connect(self.edit_directory_metadata)
        self.titleBar.save_as_file.triggered.connect(self.save_file)
        self.titleBar.save_as_directory.triggered.connect(self.save_directory)
        self.control_widget.pushButton_LaunchStrain.clicked.connect(self.launch_strain)

        ## Virtual detectors mode ##
        self.settings.New('virtual_detector_mode', dtype=int, initial=0)
        self.settings.virtual_detector_mode.connect_bidir_to_widget(self.control_widget.buttonGroup_DetectorMode)
        self.settings.virtual_detector_mode.updated_value.connect(self.update_virtual_detector_mode)

        ## DP Scaling mode ##
        self.settings.New('diffraction_scaling_mode',dtype=int,initial=0)
        self.settings.diffraction_scaling_mode.connect_bidir_to_widget(self.control_widget.buttonGroup_DiffractionMode)
        self.settings.diffraction_scaling_mode.updated_value.connect(self.diffraction_scaling_changed)

        self.settings.New('real_scaling_mode', dtype=int, initial=0)
        self.settings.real_scaling_mode.connect_bidir_to_widget(self.control_widget.buttonGroup_realMode)
        self.settings.real_scaling_mode.updated_value.connect(self.real_sacling_changed)

        ## Setting ##
        self.settings.New('color_mode', dtype=bool, initial=False)
        self.settings.color_mode.connect_bidir_to_widget(self.control_widget.checkBox_color)
        self.settings.color_mode.updated_value.connect(self.update_color_checked)
        self.settings.New('real_time_update_mode', dtype=bool, initial=False)
        self.settings.real_time_update_mode.connect_bidir_to_widget(self.control_widget.checkBox_update)

        ## Virtual Detector Shape ##
        self.control_widget.pushBtn_rect_diffractionSpace.clicked.connect(
            lambda: self.addShape_diffractionSpace(cs.DetectorShape.rectangular))
        self.control_widget.pushBtn_circ_diffractionSpace.clicked.connect(
            lambda: self.addShape_diffractionSpace(cs.DetectorShape.circular))
        self.control_widget.pushBtn_annular_diffractionSpace.clicked.connect(
            lambda: self.addShape_diffractionSpace(cs.DetectorShape.annular))
        self.control_widget.pushBtn_point_diffractionSpace.clicked.connect(
            lambda: self.addShape_diffractionSpace(cs.DetectorShape.point))

        ## RealSpace Detector Shape ##
        self.control_widget.pushBtn_rect_realSpace.clicked.connect(
            lambda: self.addShape_realSpace(cs.DetectorShape.rectangular))
        self.control_widget.pushBtn_circ_realSpace.clicked.connect(
            lambda: self.addShape_realSpace(cs.DetectorShape.circular))
        self.control_widget.pushBtn_annular_realSpace.clicked.connect(
            lambda: self.addShape_realSpace(cs.DetectorShape.annular))
        self.control_widget.pushBtn_point_realSpace.clicked.connect(
            lambda: self.addShape_realSpace(cs.DetectorShape.point))

        self.titleBar.save_diffraction_space.triggered.connect(lambda:self.save_current_space(True))
        self.titleBar.save_real_space.triggered.connect(lambda:self.save_current_space(False))

        return self.control_widget

    def save_current_space(self, diffractionSpace = True):
        fileFilter = "tiff(*.tiff);; jpg(*.jpg)"
        fileName,_ = QtWidgets.QFileDialog.getSaveFileName(None, "name", None, fileFilter)

        if fileName == "":
            return

        if diffractionSpace :
            img = self.diffraction_space_widget.image
        else :
            img = self.real_space_widget.image
        print("Save image to "+fileName)
        io.imsave(fileName, img)

    def setup_diffraction_space_widget(self):
        # Create pyqtgraph ImageView object
        self.diffraction_space_widget = pg.ImageView()
        self.diffraction_space_widget.noRepeatKeys = []
        self.diffraction_space_widget.setImage(np.zeros((512,512)))
        self.diffraction_space_view_text = pg.TextItem('Diffraction Space',(200,200,200),None,(0,1))
        self.diffraction_space_widget.addItem(self.diffraction_space_view_text)
        self.diffraction_space_widget.setWindowTitle('Diffraction Space')
        return self.diffraction_space_widget

    def setup_real_space_widget(self):
        # Create pyqtgraph ImageView object
        self.real_space_widget = pg.ImageView()
        self.real_space_widget.noRepeatKeys = []
        self.real_space_widget.setImage(np.zeros((512,512)))
        self.real_space_view_text = pg.TextItem('Real Space',(200,200,200),None,(0,1))
        self.real_space_widget.addItem(self.real_space_view_text)

        # Add point selector connected to displayed diffraction pattern
        # self.real_space_point_selector = pg_point_roi(self.real_space_widget.getView())
        # self.real_space_point_selector.sigRegionChanged.connect(self.update_diffraction_space_view)

        # Name and return
        self.real_space_widget.setWindowTitle('Real Space')
        return self.real_space_widget

    def setup_console_widget(self):
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        self.kernel.gui = 'qt4'
        self.kernel.shell.push({'np': np, 'app': self})
        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

        #Avoid setting up multiple consoles
        alreadysetup = False
        if hasattr(self,'console_widget'):
            if (isinstance(self.console_widget,RichJupyterWidget)):
                alreadysetup = True

        if not alreadysetup: self.console_widget = RichJupyterWidget()
        self.console_widget.setWindowTitle("py4DSTEM IPython Console")
        self.console_widget.kernel_manager = self.kernel_manager
        self.console_widget.kernel_client = self.kernel_client

        return self.console_widget


    def setup_main_window(self):
        """
        Setup main window, arranging sub-windows inside
        """
        layout_data = QtWidgets.QHBoxLayout()
        layout_data.addWidget(self.diffraction_space_widget,1)
        layout_data.addWidget(self.real_space_widget,1)

        layout_data_and_control = QtWidgets.QVBoxLayout()
        layout_data_and_control.addWidget(self.titleBar,0,alignment=Qt.AlignTop)
        layout_data_and_control.addWidget(self.control_widget,1)
        layout_data_and_control.addLayout(layout_data,3)
        layout_data_and_control.setSpacing(0)
        layout_data_and_control.setContentsMargins(0,0,0,0)

        self.main_window.setLayout(layout_data_and_control)
        self.main_window.resize(1200,800)
        # self.main_window.setGeometry(0,0,1200,800)
        #self.console_widget.setGeometry(0,1800,1600,250)
        self.main_window.show()
        self.main_window.raise_()
        #self.console_widget.show()
        #self.console_widget.raise_()
        return self.main_window

    ##################################################################
    ############## Methods connecting to user inputs #################
    ##################################################################

    ##################################################################
    # In general, these methods collect any relevant user inputs,    #
    # then pass them to functions defined elsewhere, often in e.g.   #
    # the process directory.                                         #
    # Additional functionality here should be avoided, to ensure     #
    # consistent output between processing run through the GUI       #
    # or from the command line.                                      # 
    ##################################################################

    def launch_strain(self):
        self.strain_window = StrainMappingWindow(main_window=self)
        self.strain_window.setup_tabs()


    ################ Load ################

    def Unidentified_file(self,fname):
        msg = QtWidgets.QMessageBox()
        msg.setText("Couldn't open {0} as it doesn't conform to currently implemented py4DSTEM standards".format(fname))
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def load_file(self,mode,filePath=None):
        """
        Loads a file by creating and storing a DataCube object.
        """
        if filePath is None:
            fname = self.settings.data_filename.val
            if not fname:
                if hasattr(self, "prev_fname"):
                    self.settings.data_filename.update_value(self.prev_fname)
                return
        else:
            fname = filePath

        print("Loading file",fname)


        # Instantiate DataCube object
        self.datacube = None
        gc.collect()

        # load based on chosen mode:
        if mode == 0:
            #auto mode
            if is_py4DSTEM_file(fname):
                self.datacube = datacube_selector(fname)
            else:
                self.datacube,_ = read(fname)
            if type(self.datacube) == str :
                self.Unidentified_file(fname)
                #Reset view
                self.__init__(sys.argv)
                return
        elif mode == 1:
            if is_py4DSTEM_file(fname):
                self.datacube = datacube_selector(fname)
            else:
                self.datacube,_ = read(fname, mem="MEMMAP")
        elif mode == 2:
            self.datacube,_ = read(fname, ft='gatan_bin')
        elif mode == 3:
            self.datacube,_ = read(fname, ft='empad')

        # remove detector shape
        self.detectorGroup_diffractionSpace.deleteAll()
        self.detectorGroup_realSpace.deleteAll()

        # Update scan shape information
        self.settings.R_Nx.update_value(self.datacube.R_Nx)
        self.settings.R_Ny.update_value(self.datacube.R_Ny)

        # Update data views
        self.diffraction_space_view,_ = compute.get_diffraction_image(
            self.datacube,
            [mk.RoiMask((slice(0, 1), slice(0, 1)), roiShape=cs.DetectorShape.point)]
        )
        self.diffraction_space_widget.setImage(self.diffraction_space_view, autoLevels=True, autoRange=True)

        # self.update_virtual_detector_mode()
        self.addShape_diffractionSpace(cs.DetectorShape.rectangular)
        self.real_space_widget.autoLevels()
        self.real_space_point_selector = self.addShape_realSpace(cs.DetectorShape.point)

        # Normalize diffraction space view
        self.diffraction_space_widget.ui.normDivideRadio.setChecked(True)
        self.diffraction_space_widget.normRadioChanged()

        # Set scan size maxima
        self.control_widget.spinBox_Nx.setMaximum(self.datacube.R_N)
        self.control_widget.spinBox_Ny.setMaximum(self.datacube.R_N)

        self.real_space_widget.levelMin = 0

        # titleBar
        self.titleBar.addRecentFile(fname)
        self.prev_fname = fname

        # update text
        self.update_view_text()

        return

    def update_view_text(self):
        self.diffraction_space_view_text.setText("Diffraction Space " + str(self.datacube.data.shape[2:4]))
        self.real_space_view_text.setText("Real Space " + str(self.datacube.data.shape[0:2]))
    ############## Preprocess ##############

    ### Scan Shape ###

    def update_scan_shape_Nx(self):
        R_Nx = self.settings.R_Nx.val
        self.settings.R_Ny.update_value(int(self.datacube.R_N/R_Nx))
        R_Ny = self.settings.R_Ny.val

        self.datacube.set_scan_shape(R_Nx, R_Ny)
        self.update_real_space_view()

    def update_scan_shape_Ny(self):
        R_Ny = self.settings.R_Ny.val
        self.settings.R_Nx.update_value(int(self.datacube.R_N/R_Ny))
        R_Nx = self.settings.R_Nx.val

        self.datacube.set_scan_shape(R_Nx, R_Ny)
        self.update_real_space_view()

    ### Crop ###

    def toggleCropROI_real(self, show=True):
        """
        If show=True, makes an RIO.  If False, removes the ROI.
        """
        if show:
            self.crop_roi_real = pg.RectROI([0,0], [self.datacube.R_Nx, self.datacube.R_Ny], pen=(3,9), removable=True, translateSnap=True, scaleSnap=True)
            self.crop_roi_real.setPen(color='r')
            self.real_space_widget.getView().addItem(self.crop_roi_real)
        else:
            if hasattr(self,'crop_roi_real'):
                self.real_space_widget.getView().removeItem(self.crop_roi_real)
                self.crop_roi_real = None
            else:
                pass

    def toggleCropROI_diffraction(self, show=True):
        """
        If show=True, makes an RIO.  If False, removes the ROI.
        """
        if show:
            self.crop_roi_diffraction = pg.RectROI([0,0], [self.datacube.Q_Nx,self.datacube.Q_Ny], pen=(3,9), removable=True, translateSnap=True, scaleSnap=True)
            self.crop_roi_diffraction.setPen(color='r')
            self.diffraction_space_widget.getView().addItem(self.crop_roi_diffraction)
        else:
            if hasattr(self,'crop_roi_diffraction'):
                self.diffraction_space_widget.getView().removeItem(self.crop_roi_diffraction)
                self.crop_roi_diffraction = None
            else:
                pass

    def crop_data(self):

        # Diffraction space
        if self.control_widget.checkBox_Crop_Diffraction.isChecked():
            # Get crop limits from ROI
            slices_q, transforms_q = self.crop_roi_diffraction.getArraySlice(self.datacube.data[0,0,:,:], self.diffraction_space_widget.getImageItem())
            slice_qx,slice_qy = slices_q
            crop_Qx_min, crop_Qx_max = slice_qx.start, slice_qx.stop-1
            crop_Qy_min, crop_Qy_max = slice_qy.start, slice_qy.stop-1
            crop_Qx_min, crop_Qx_max = max(0,crop_Qx_min), min(self.datacube.Q_Nx,crop_Qx_max)
            crop_Qy_min, crop_Qy_max = max(0,crop_Qy_min), min(self.datacube.Q_Ny,crop_Qy_max)
            # Move ROI selector
            # x0,y0 = self.virtual_detector_roi.x(), self.virtual_detector_roi.y()
            # x0_len,y0_len = self.virtual_detector_roi.size()
            # xf = int(x0*(crop_Qx_max-crop_Qx_min)/self.datacube.Q_Nx)
            # yf = int(y0*(crop_Qy_max-crop_Qy_min)/self.datacube.Q_Ny)
            # xf_len = int(x0_len*(crop_Qx_max-crop_Qx_min)/self.datacube.Q_Nx)
            # yf_len = int(y0_len*(crop_Qy_max-crop_Qy_min)/self.datacube.Q_Ny)
            # self.virtual_detector_roi.setPos((xf,yf))
            # self.virtual_detector_roi.setSize((xf_len,yf_len))
            # Crop data
            self.datacube.crop_data_diffraction(crop_Qx_min,crop_Qx_max,crop_Qy_min,crop_Qy_max)
            # Update settings
            self.settings.crop_qx_min.update_value(crop_Qx_min)
            self.settings.crop_qx_max.update_value(crop_Qx_max)
            self.settings.crop_qy_min.update_value(crop_Qy_min)
            self.settings.crop_qy_max.update_value(crop_Qy_max)
            self.settings.isCropped_q.update_value(True)
            # Uncheck crop checkbox and remove ROI
            self.control_widget.checkBox_Crop_Diffraction.setChecked(False)
            # Update display
            self.update_diffraction_space_view()
        else:
            self.settings.isCropped_q.update_value(False)

        # Real space
        if self.control_widget.checkBox_Crop_Real.isChecked():
            # Get crop limits from ROI
            slices_r, transforms_r = self.crop_roi_real.getArraySlice(self.datacube.data[:,:,0,0], self.real_space_widget.getImageItem())
            slice_rx,slice_ry = slices_r
            crop_Rx_min, crop_Rx_max = slice_rx.start, slice_rx.stop-1
            crop_Ry_min, crop_Ry_max = slice_ry.start, slice_ry.stop-1
            crop_Rx_min, crop_Rx_max = max(0,crop_Rx_min), min(self.datacube.R_Nx,crop_Rx_max)
            crop_Ry_min, crop_Ry_max = max(0,crop_Ry_min), min(self.datacube.R_Ny,crop_Ry_max)
            # Move point selector
            # x0,y0 = self.real_space_point_selector.x(),self.real_space_point_selector.y()
            # xf = int(x0*(crop_Rx_max-crop_Rx_min)/self.datacube.R_Nx)
            # yf = int(y0*(crop_Ry_max-crop_Ry_min)/self.datacube.R_Ny)
            # self.real_space_point_selector.setPos((xf,yf))
            # Crop data
            self.datacube.crop_data_real(crop_Rx_min,crop_Rx_max,crop_Ry_min,crop_Ry_max)
            # Update settings
            self.settings.crop_rx_min.update_value(crop_Rx_min)
            self.settings.crop_rx_max.update_value(crop_Rx_max)
            self.settings.crop_ry_min.update_value(crop_Ry_min)
            self.settings.crop_ry_max.update_value(crop_Ry_max)
            self.settings.isCropped_r.update_value(True)
            self.settings.R_Nx.update_value(self.datacube.R_Nx,send_signal=False)
            self.settings.R_Ny.update_value(self.datacube.R_Ny,send_signal=False)
            # Uncheck crop checkbox and remove ROI
            self.control_widget.checkBox_Crop_Real.setChecked(False)
            # Update display
            self.update_real_space_view()
        else:
            self.settings.isCropped_r.update_value(False)

        self.update_view_text()

    ### Bin ###

    def bin_data(self):
        # Get bin factors from GUI
        bin_factor_Q = self.settings.bin_q.val
        bin_factor_R = self.settings.bin_r.val
        if bin_factor_Q>1:
            # Move ROI selector
            # x0,y0 = self.virtual_detector_roi.x(), self.virtual_detector_roi.y()
            # x0_len,y0_len = self.virtual_detector_roi.size()
            # xf = int(x0/bin_factor_Q)
            # yf = int(y0/bin_factor_Q)
            # xf_len = int(x0_len/bin_factor_Q)
            # yf_len = int(y0_len/bin_factor_Q)
            # self.virtual_detector_roi.setPos((xf,yf))
            # self.virtual_detector_roi.setSize((xf_len,yf_len))
            # Bin data
            if isinstance(self.datacube.data,np.ndarray):
                self.datacube.bin_data_diffraction(bin_factor_Q)
            else:
                self.datacube.bin_data_mmap(bin_factor_Q)
            # Update display
            self.update_diffraction_space_view()
        if bin_factor_R>1:
            # Move point selector
            # x0,y0 = self.real_space_point_selector.x(),self.real_space_point_selector.y()
            # xf = int(x0/bin_factor_R)
            # yf = int(y0/bin_factor_R)
            # self.real_space_point_selector.setPos((xf,yf))
            # Bin data
            self.datacube.bin_data_real(bin_factor_R)
            # Update settings
            self.settings.R_Nx.update_value(self.datacube.R_Nx,send_signal=False)
            self.settings.R_Ny.update_value(self.datacube.R_Ny,send_signal=False)
            # Update display
            self.update_real_space_view()
        # Set bin factors back to 1
        self.settings.bin_q.update_value(1)
        self.settings.bin_r.update_value(1)
        self.update_view_text()



    ### Metadata ###

    def edit_file_metadata(self):
        """
        Creates a popup dialog with tabs for different metadata groups, and fields in each
        group with current, editable metadata values.
        """
        # Make widget
        self.EditMetadataWidget = EditMetadataWidget(self.datacube)
        self.EditMetadataWidget.setWindowTitle("Metadata Editor")
        self.EditMetadataWidget.show()
        self.EditMetadataWidget.raise_()

        # Cancel or save
        self.EditMetadataWidget.pushButton_Cancel.clicked.connect(self.cancel_editMetadata)
        self.EditMetadataWidget.pushButton_Save.clicked.connect(self.save_editMetadata)

    def cancel_editMetadata(self):
        self.EditMetadataWidget.close()

    def save_editMetadata(self):
        print("Updating metadata...")
        for i in range(self.EditMetadataWidget.tabs.count()):
            tab = self.EditMetadataWidget.tabs.widget(i)
            # Get appropriate metadata dict
            tabname = self.EditMetadataWidget.tabs.tabText(i)
            metadata_dict_name = [name for name in self.datacube.metadata.__dict__.keys() if tabname[1:] in name][0]
            metadata_dict = getattr(self.datacube.metadata, metadata_dict_name)
            for row in tab.layout().children():
                key=row.itemAt(0).widget().text()
                try:
                    value=row.itemAt(1).widget().text()
                except AttributeError:
                    # Catches alternate widget (QPlainTextEdit) in comments tab
                    value=row.itemAt(1).widget().toPlainText()
                try:
                    value=float(value)
                except ValueError:
                    pass
                metadata_dict[key]=value
        self.EditMetadataWidget.close()
        print("Done.")

    def edit_directory_metadata(self):
        print('edit directory metadata pressed')
        pass

    ### Save ###

    def save_file(self):
        """
        Saving files to the .h5 format.
        This method:
            1) opens a separate dialog
            2) puts a name in the "Save as:" field according to the original filename and any
               preprocessing that's been done
            2) Exits with or without saving when 'Save' or 'Cancel' buttons are pressed.
        """
        # Make widget
        save_path = os.path.splitext(self.settings.data_filename.val)[0]+'.h5'
        self.save_widget = SaveWidget(save_path)
        self.save_widget.setWindowTitle("Save as...")
        self.save_widget.show()
        self.save_widget.raise_()

        # Cancel or save
        self.save_widget.pushButton_Cancel.clicked.connect(self.cancel_saveas)
        self.save_widget.pushButton_Execute.clicked.connect(self.execute_saveas)

    def cancel_saveas(self):
        self.save_widget.close()

    def execute_saveas(self):
        f = self.save_widget.lineEdit_SavePath.text()
        print("Saving file to {}".format(f))
        save(f,self.datacube)
        self.save_widget.close()

    def save_directory(self):
        print('save directory metadata pressed')
        pass

    ################# Virtual Detectors #################

    def update_annulus_pos(self,inner,outer):
        """
        Function to keep inner and outer rings of annulus aligned.
        """
        R_outer = outer.size().x()/2
        R_inner = inner.size().x()/2
        # Only outer annulus is draggable; when it moves, update position of inner annulus
        x0 = outer.pos().x() + R_outer
        y0 = outer.pos().y() + R_outer
        inner.setPos(x0-R_inner, y0-R_inner)

    def update_annulus_radii(self,inner,outer):
        R_outer = outer.size().x()/2
        R_inner = inner.size().x()/2
        if R_outer < R_inner:
            x0 = outer.pos().x() + R_outer
            y0 = outer.pos().y() + R_outer
            outer.setSize(2*R_inner+6)
            outer.setPos(x0-R_inner-3, y0-R_inner-3)

    def update_virtual_detector_mode(self):
        self.update_real_space_view()

    ################## Get virtual images ##################

    def diffraction_scaling_changed(self):
        self.update_diffraction_space_view(True)

    def real_sacling_changed(self):
        self.update_real_space_view(True)

    def update_color_checked(self):
        # if self.control_widget.checkBox_color.isChecked():
        #     for detector in self.detectorGroup_diffractionSpace:
        #         detector.controlWidget.colorButton.setVisible(True)
        #     for detector in self.detectorGroup_realSpace:
        #         detector.controlWidget.colorButton.setVisible(True)
        # else:
        #     for detector in self.detectorGroup_diffractionSpace:
        #         detector.controlWidget.colorButton.setVisible(False)
        #     for detector in self.detectorGroup_realSpace:
        #         detector.controlWidget.colorButton.setVisible(False)
        if self.control_widget.checkBox_color.isChecked():
            self.control_widget.radioButton_DiffX.setDisabled(True)
            self.control_widget.radioButton_DiffY.setDisabled(True)
            self.control_widget.radioButton_CoMX.setDisabled(True)
            self.control_widget.radioButton_CoMY.setDisabled(True)
            # self.diffraction_space_widget.getHistogramWidget().item.setLevelMode('rgba')
            # self.real_space_widget.getHistogramWidget().item.setLevelMode('rgba')

        else:
            self.control_widget.radioButton_DiffX.setDisabled(False)
            self.control_widget.radioButton_DiffY.setDisabled(False)
            self.control_widget.radioButton_CoMX.setDisabled(False)
            self.control_widget.radioButton_CoMY.setDisabled(False)
            # self.diffraction_space_widget.getHistogramWidget().item.setLevelMode('mono')
            # self.real_space_widget.getHistogramWidget().item.setLevelMode('mono')
        if not self.control_widget.radioButton_Integrate.isChecked():
            self.control_widget.radioButton_Integrate.setChecked(True)

        # self.diffraction_space_widget.getHistogramWidget().item.vb.setLimits(yMin=1)
        # self.real_space_widget.getHistogramWidget().item.vb.setLimits(yMin=1)

        self.update_real_space_view(autoLevels=True)
        self.update_diffraction_space_view(autoLevels=True)

        # todo
        # self.diffraction_space_widget.getHistogramWidget().item.vb.
        # print(self.diffraction_space_widget.getHistogramWidget().item.getLevels())

    def update_diffraction_space_view(self, autoLevels=False):
        if len(self.detectorGroup_realSpace) == 0:
            return

        if self.settings.color_mode.val == False:
            ## Create Mask ##
            roi_mask_grp = mk.get_mask_grp_from_rois(self.detectorGroup_realSpace,
                                                     self.real_space_widget.getImageItem(),
                                                     True)
            ## Get Virtual Image ##
            new_diffraction_space_view, success = compute.get_diffraction_image(self.datacube, masks=roi_mask_grp)

        else:
            new_diffraction_space_view, success = compute.get_diffraction_image_color(self.datacube,
                                                                           self.detectorGroup_realSpace)

        if success:
            # Scaling
            self.diffraction_space_view = compute.scaling(new_diffraction_space_view, self.settings.diffraction_scaling_mode.val, self.datacube)
            self.diffraction_space_widget.setImage(self.diffraction_space_view,
                                                   autoLevels=autoLevels)

        ## Scale Level For Color ##
        if autoLevels == True and self.settings.color_mode.val == True:
            self.diffraction_space_widget.setLevels(min=self.diffraction_space_view.min(), max=self.diffraction_space_view.max())

    def update_diffraction_space_view2(self):
        roi_state = self.real_space_point_selector.saveState()
        x0,y0 = roi_state['pos']
        xc,yc = int(x0+1),int(y0+1)

        # Set the diffraction space image
        new_diffraction_space_view, success = self.datacube.get_diffraction_space_view(xc,yc)
        if success:
            self.diffraction_space_view = new_diffraction_space_view
            self.real_space_view_text.setText(f"[{xc},{yc}]")

            # rescale DP as selected (0 means raw, does no scaling)
            if self.settings.diffraction_scaling_mode.val == 1:
                # sqrt mode
                self.diffraction_space_view = np.sqrt(self.diffraction_space_view)
            elif self.settings.diffraction_scaling_mode.val == 2:
                # log mode
                self.diffraction_space_view = np.log(
                    self.diffraction_space_view - np.min(self.diffraction_space_view) + 1)
            elif self.settings.diffraction_scaling_mode.val == 3:
                # EWPC mode
                h = np.hanning(self.datacube.Q_Nx)[:,np.newaxis] @ np.hanning(self.datacube.Q_Ny)[np.newaxis,:]
                self.diffraction_space_view = np.abs(np.fft.fftshift(np.fft.fft2(np.log(
                    (h*(self.diffraction_space_view - np.min(self.diffraction_space_view))) + 1))))**2

            self.diffraction_space_widget.setImage(self.diffraction_space_view,
                                                   autoLevels=False,autoRange=False)
        else:
            pass
        return

    # def update_dialog_diffractionSpace(self):
    #
    #     if self.updating_roi:
    #         return
    #
    #     if len(self.detectorGroup_diffractionSpace) == 0:
    #         return
    #
    #     dtt: detector.Detector
    #     for dtt in self.detectorGroup_diffractionSpace:
    #         # a = DetectorShapeWidget(0)
    #         # self.widget_roi_dic.get(controlwidget)
    #         roi: pg.ROI = dtt.rois[0]
    #         shape_type = dtt.shape_type
    #         controlwidget = dtt.controlWidget
    #
    #         roi_state = roi.getState()
    #         x0, y0 = roi_state['pos']
    #         size_x, size_y = roi_state['size']
    #         _R = size_x / 2
    #         center_x = (x0+_R)
    #         center_y = (y0+_R)
    #         # slice_x, slice_y = self.getSlices(roi)
    #         # center_x = (slice_x.stop + slice_x.start) / 2
    #         # center_y = (slice_y.stop + slice_y.start) / 2
    #         # size_x = slice_x.stop - slice_x.start
    #         # size_y = slice_y.stop - slice_y.start
    #         # x0 = slice_x.start
    #         # y0 = slice_y.start
    #         # _R = size_x / 2
    #
    #         if shape_type == cs.DetectorShape.annular:
    #             roi2: pg.ROI = dtt.rois[1]
    #             roi2_state = roi2.getState()
    #             size_x, size_y = roi2_state['size']
    #             _innerR = size_x/2
    #
    #         if shape_type == cs.DetectorShape.rectangular:
    #             controlwidget.firstLineText1.setValue(x0)
    #             controlwidget.firstLineText2.setValue(y0)
    #             controlwidget.secondLineText1.setValue(size_x)
    #             controlwidget.secondLineText2.setValue(size_y)
    #         elif shape_type == cs.DetectorShape.circular:
    #             controlwidget.firstLineText1.setValue(center_x)
    #             controlwidget.firstLineText2.setValue(center_y)
    #             controlwidget.secondLineText1.setValue(_R)
    #         elif shape_type == cs.DetectorShape.annular:
    #             controlwidget.firstLineText1.setValue(center_x)
    #             controlwidget.firstLineText2.setValue(center_y)
    #             controlwidget.secondLineText1.setValue(_R)
    #             controlwidget.secondLineText2.setValue(_innerR)
    #         elif shape_type == cs.DetectorShape.point:
    #             controlwidget.firstLineText1.setValue(x0)
    #             controlwidget.firstLineText2.setValue(y0)


    # def update_roi_diffractionSpace(self):
    #     if len(self.detectorGroup_diffractionSpace) == 0:
    #         return
    #     self.updating_roi = True
    #     controlwidget: DetectorShapeWidget
    #     dtt : detector.Detector
    #     for dtt in self.detectorGroup_diffractionSpace:
    #
    #         types = dtt.shape_type
    #         controlwidget = dtt.controlWidget
    #         # InitialLizing ROIs #
    #         roi: pg.ROI = dtt.rois[0]
    #
    #         prev_state = roi.getState()
    #         state = roi.getState()
    #
    #         if types == cs.DetectorShape.annular: #for Annular
    #             roi2: pg.ROI = dtt.rois[1]
    #             state2 = roi.getState()
    #
    #         # Set Size #
    #         if types == cs.DetectorShape.rectangular:
    #             size_x = controlwidget.secondLineText1.value()
    #             size_y = controlwidget.secondLineText2.value()
    #             state['size']=(size_x,size_y)
    #         elif types == cs.DetectorShape.circular:
    #             _R = controlwidget.secondLineText1.value()
    #             size_x = _R*2
    #             size_y = size_x
    #             state['size']=(size_x,size_y)
    #         elif types == cs.DetectorShape.annular:
    #             _outerR = controlwidget.secondLineText1.value()
    #             _innerR = controlwidget.secondLineText2.value()
    #             state['size']=(_outerR*2,_outerR*2)
    #             state2['size']=(_innerR*2,_innerR*2)
    #
    #         # Set Pos #
    #         x0 = controlwidget.firstLineText1.value()
    #         y0 = controlwidget.firstLineText2.value()
    #         if types == cs.DetectorShape.circular:
    #             state['pos']=(x0-_R, y0-_R)
    #         elif types == cs.DetectorShape.annular:
    #             state2['pos']=(x0-_innerR, y0-_innerR)
    #             state['pos']=(x0-_outerR, y0-_outerR)
    #             roi2.setState(state2)
    #         else:
    #             state['pos']=(x0, y0)
    #
    #         flag = True
    #         if state['pos'][0] == prev_state['pos'][0] and \
    #             state['pos'][1] == prev_state['pos'][1] and \
    #             state['size'][0] == prev_state['size'][0] and \
    #             state['size'][1] == prev_state['size'][1] :
    #             flag = False
    #         if flag:
    #             roi.setState(state)
    #
    #     self.updating_roi = False


    def update_real_space_view(self, autoLevels=False):
        tic = time.process_time()
        virtual_detector_mode = self.settings.virtual_detector_mode.val

        ## retun if roi none ##
        if len(self.detectorGroup_diffractionSpace) == 0:
            return

        if self.settings.color_mode.val == False:
            ## Create Mask ##
            roi_mask_grp = mk.get_mask_grp_from_rois(self.detectorGroup_diffractionSpace,
                                                     self.diffraction_space_widget.getImageItem(),
                                                     False)

            ## Get Virtual Image ##
            new_real_space_view, success = compute.get_virtual_image(self.datacube, masks=roi_mask_grp, integration_mode=virtual_detector_mode)
        else:
            new_real_space_view, success = compute.get_virtual_image_color(self.datacube, self.detectorGroup_diffractionSpace)

        if success:
            ## Scaling ##
            new_real_space_view = compute.scaling(new_real_space_view,
                                                  self.settings.real_scaling_mode.val, self.datacube)

            ## Set Image ##
            self.real_space_view = new_real_space_view
            self.real_space_widget.setImage(self.real_space_view, autoLevels=autoLevels)

            ## Scale Level For Color ##
            if autoLevels == True and self.settings.color_mode.val == True:
                self.real_space_widget.setLevels(min=self.real_space_view.min(), max=self.real_space_view.max())

            ## Update strain_window ##
            if self.strain_window is not None:
                self.strain_window.bragg_disk_tab.update_views()

            toc = time.process_time()
            print("analysis done in "+str(toc-tic)+"ms")


    def exec_(self):
        return self.qtapp.exec_()

class QtWidget_Key(QtWidgets.QWidget):
    def __init__(self, dataViewer:DataViewer):
        QtWidgets.QWidget.__init__(self)
        self.dataViewer=dataViewer

    def keyReleaseEvent(self, e: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(e)

        if e.key() not in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
            return

        if hasattr(self.dataViewer, 'selected_detector'):
            roi_state = self.dataViewer.selected_detector.rois[0].saveState()
            x0, y0 = roi_state['pos']
            if e.key() == QtCore.Qt.Key_Left:
                x0 = (x0-1)%(self.dataViewer.selected_detector.imageView.image.shape[0])
            elif e.key() == QtCore.Qt.Key_Right:
                x0 = (x0+1)%(self.dataViewer.selected_detector.imageView.image.shape[0])
            elif e.key() == QtCore.Qt.Key_Up:
                y0 = (y0-1)%(self.dataViewer.selected_detector.imageView.image.shape[1])
            elif e.key() == QtCore.Qt.Key_Down:
                y0 = (y0+1)%(self.dataViewer.selected_detector.imageView.image.shape[1])
            self.dataViewer.selected_detector.rois[0].setPos((x0,y0))


################################ End of class ##################################