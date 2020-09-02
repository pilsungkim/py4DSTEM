import py4DSTEM.process.utils.constants as cs
import pyqtgraph as pg
from py4DSTEM.gui.dialogs import DetectorShapeWidget
from .gui_utils import pg_point_roi
from PyQt5.QtCore import Qt


# is name Detector appropriate?
class DetectorGroup(list):
    def __init__(self, viewer, imageView:pg.ImageView, layout_to_put_widget, widget=DetectorShapeWidget):
        self.viewer = viewer
        self.imageView = imageView
        self.layout_to_put_widget = layout_to_put_widget
        self.numCount = 1
        self.widget = widget
        # self.roiSignalBinding = roiSignalBinding
        # self.widgetSignalBiding = widgetSignalBiding

    def addDetector(self, shape_type):
        rois = self.get_rois(shape_type)
        for roi in rois:
            self.imageView.addItem(roi)

        init_name = self.get_init_name(shape_type)

        detector_shape_control_widget = self.widget(shape_type, init_name)
        self.layout_to_put_widget.insertWidget(self.layout_to_put_widget.count()-1,
                                               detector_shape_control_widget,
                                               alignment=Qt.AlignTop)

        detector = Detector(init_name, detector_shape_control_widget, rois, shape_type)
        detector.roi_to_dialog_update()
        # self.roiSignalBinding(detector)
        # self.widgetSignalBinding(detector)
        self.append(detector)
        return detector


    def deleteDetector(self, Detector):
        for roi in Detector.rois:
            self.imageView.scene.removeItem(roi)
        Detector.controlWidget.close()

    def deleteAll(self):
        while len(self) > 0:
            self.deleteDetector(self.pop(0))

    def get_init_name(self, shape_type):
        name = ""
        if shape_type == cs.DetectorShape.rectangular:
            name = "Rectangular Detector "
        elif shape_type == cs.DetectorShape.circular:
            name = "Circular Detector "
        elif shape_type == cs.DetectorShape.annular:
            name = "Annular Detector "
        elif shape_type == cs.DetectorShape.point:
            name = "Point Detector "
        name = name + str(self.numCount)
        self.numCount += 1
        return name

    def get_rois(self, shape_type):
        rois = []

        x, y = self.imageView.image.shape
        x0, y0 = x / 2, y / 2
        xr, yr = x / 10, y / 10

        if shape_type == cs.DetectorShape.rectangular:  # rect
            roi = pg.RectROI([int(x0 - xr / 2), int(y0 - yr / 2)], [int(xr), int(yr)], pen=(3, 9))
            rois.append(roi)
        elif shape_type == cs.DetectorShape.circular:  # circle
            roi = pg.CircleROI([int(x0 - xr / 2), int(y0 - yr / 2)], [int(xr), int(yr)], pen=(3, 9))
            rois.append(roi)
        elif shape_type == cs.DetectorShape.annular:  # annular
            roi_outer = pg.CircleROI([int(x0 - xr), int(y0 - yr)], [int(2 * xr), int(2 * yr)], pen=(3, 9))
            roi_inner = pg.CircleROI([int(x0 - xr / 2), int(y0 - yr / 2)], [int(xr), int(yr)], pen=(4, 9), movable=False)
            rois.append(roi_outer)
            rois.append(roi_inner)
            # Connect size/position of inner and outer detectors

        elif shape_type == cs.DetectorShape.point:  # point
            roi = pg_point_roi(self.imageView, x0, y0)
            rois.append(roi)

        return rois

    # def roiSignalBinding(self, dtt):
    #     if len(dtt.rois) == 1:  # Rect, Circular, Point
    #         dtt.rois[0].sigRegionChangeFinished.connect(self.viewer.update_real_space_view)
    #     else:  # Annular
    #         roi_outer = dtt.rois[0]
    #         roi_inner = dtt.rois[1]
    #         roi_outer.sigRegionChangeFinished.connect(
    #             lambda: update_annulus_pos(roi_inner, roi_outer))
    #         roi_outer.sigRegionChangeFinished.connect(
    #             lambda: update_annulus_radii(roi_inner, roi_outer))
    #         roi_inner.sigRegionChangeFinished.connect(
    #             lambda: update_annulus_radii(roi_inner, roi_outer))
    #
    # def widgetSignalBinding(self, dtt):
    #     dtt.controlWidget.delButton.clicked.connect(lambda: self.deleteShape(dtt))
    #     # virtual_detector_shape_control_widget.firstLineText1.valueChanged.connect(self.update_roi)
    #     # virtual_detector_shape_control_widget.firstLineText2.valueChanged.connect(self.update_roi)
    #     # virtual_detector_shape_control_widget.secondLineText1.valueChanged.connect(self.update_roi)
    #     # virtual_detector_shape_control_widget.secondLineText2.valueChanged.connect(self.update_roi)
    #     dtt.controlWidget.addKeyEvent(self.viewer.update_roi)

    def get_by_name(self):
        pass

    def get_by_id(self):
        pass

    def get_by_widget(self):
        pass

    def get_by_roi(self):
        pass


class Detector:
    def __init__(self, name:str, controlWidget:DetectorShapeWidget, rois:pg.ROI, shape_type:str):
        self.name = name
        self.controlWidget = controlWidget
        self.rois = rois
        self.shape_type = shape_type

    def dialog_to_roi_update(self):
        self.updating_roi = True
        types = self.shape_type
        controlwidget = self.controlWidget
        # InitialLizing ROIs #
        roi: pg.ROI = self.rois[0]

        prev_state = roi.getState()
        state = roi.getState()

        if types == cs.DetectorShape.annular:  # for Annular
            roi2: pg.ROI = self.rois[1]
            state2 = roi.getState()

        # Set Size #
        if types == cs.DetectorShape.rectangular:
            size_x = controlwidget.secondLineText1.value()
            size_y = controlwidget.secondLineText2.value()
            state['size'] = (size_x, size_y)
        elif types == cs.DetectorShape.circular:
            _R = controlwidget.secondLineText1.value()
            size_x = _R * 2
            size_y = size_x
            state['size'] = (size_x, size_y)
        elif types == cs.DetectorShape.annular:
            _outerR = controlwidget.secondLineText1.value()
            _innerR = controlwidget.secondLineText2.value()
            state['size'] = (_outerR * 2, _outerR * 2)
            state2['size'] = (_innerR * 2, _innerR * 2)

        # Set Pos #
        x0 = controlwidget.firstLineText1.value()
        y0 = controlwidget.firstLineText2.value()
        if types == cs.DetectorShape.circular:
            state['pos'] = (x0 - _R, y0 - _R)
        elif types == cs.DetectorShape.annular:
            state2['pos'] = (x0 - _innerR, y0 - _innerR)
            state['pos'] = (x0 - _outerR, y0 - _outerR)
            roi2.setState(state2)
        else:
            state['pos'] = (x0, y0)

        flag = True
        if state['pos'][0] == prev_state['pos'][0] and \
                state['pos'][1] == prev_state['pos'][1] and \
                state['size'][0] == prev_state['size'][0] and \
                state['size'][1] == prev_state['size'][1]:
            flag = False
        if flag:
            roi.setState(state)
        self.updating_roi = False

    def roi_to_dialog_update(self):

        roi: pg.ROI = self.rois[0]
        shape_type = self.shape_type
        controlwidget = self.controlWidget

        roi_state = roi.getState()
        x0, y0 = roi_state['pos']
        size_x, size_y = roi_state['size']
        _R = size_x / 2
        center_x = (x0 + _R)
        center_y = (y0 + _R)
        # slice_x, slice_y = self.getSlices(roi)
        # center_x = (slice_x.stop + slice_x.start) / 2
        # center_y = (slice_y.stop + slice_y.start) / 2
        # size_x = slice_x.stop - slice_x.start
        # size_y = slice_y.stop - slice_y.start
        # x0 = slice_x.start
        # y0 = slice_y.start
        # _R = size_x / 2
        if shape_type == cs.DetectorShape.annular:
            roi2: pg.ROI = self.rois[1]
            roi2_state = roi2.getState()
            size_x, size_y = roi2_state['size']
            _innerR = size_x / 2
        if shape_type == cs.DetectorShape.rectangular:
            controlwidget.firstLineText1.setValue(x0)
            controlwidget.firstLineText2.setValue(y0)
            controlwidget.secondLineText1.setValue(size_x)
            controlwidget.secondLineText2.setValue(size_y)
        elif shape_type == cs.DetectorShape.circular:
            controlwidget.firstLineText1.setValue(center_x)
            controlwidget.firstLineText2.setValue(center_y)
            controlwidget.secondLineText1.setValue(_R)
        elif shape_type == cs.DetectorShape.annular:
            controlwidget.firstLineText1.setValue(center_x)
            controlwidget.firstLineText2.setValue(center_y)
            controlwidget.secondLineText1.setValue(_R)
            controlwidget.secondLineText2.setValue(_innerR)
        elif shape_type == cs.DetectorShape.point:
            controlwidget.firstLineText1.setValue(x0)
            controlwidget.firstLineText2.setValue(y0)

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