import py4DSTEM.process.utils.constants as cs
import pyqtgraph as pg
from py4DSTEM.gui.dialogs import DetectorShapeWidget
from .gui_utils import pg_point_roi
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from py4DSTEM.process.imaging import mask as mk


class DetectorGroup(list):
    def __init__(self, viewer, imageView:pg.ImageView, layout_to_put_widget, widget=DetectorShapeWidget):
        self.viewer = viewer
        self.imageView = imageView
        self.layout_to_put_widget = layout_to_put_widget
        self.numCount = 1
        self.widget = widget

    def addDetector(self, shape_type):
        rois = self.get_rois(shape_type)
        for roi in rois:
            self.imageView.addItem(roi)

        init_name = self.get_init_name(shape_type)

        detector_shape_control_widget = self.widget(shape_type, init_name)
        self.layout_to_put_widget.insertWidget(self.layout_to_put_widget.count()-1,
                                               detector_shape_control_widget,
                                               alignment=Qt.AlignTop)

        detector = Detector(init_name, detector_shape_control_widget, rois, shape_type, self.imageView)
        detector.roi_to_dialog_update()
        self.append(detector)
        return detector

    def deleteDetector(self, Detector):
        for roi in Detector.rois:
            self.imageView.scene.removeItem(roi)
        Detector.controlWidget.close()
        if Detector in self:
            self.remove(Detector)

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

        x, y = self.imageView.image.shape[0:2]
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


class Detector:
    def __init__(self, name:str, controlWidget:DetectorShapeWidget, rois:pg.ROI, shape_type:str, imageView:pg.ImageView, color="", intensity_ratio=""):
        self.name = name
        self.controlWidget = controlWidget
        self.rois = rois
        self.shape_type = shape_type
        self.selected = False
        self.imageView = imageView.getImageItem()
        self.roiMask = None

        self.color = QColor(0, 255, 0)
        self.color_r = self.color.red()
        self.color_g = self.color.green()
        self.color_b = self.color.blue()
        self.color_name = self.color.name()
        self.intensityRatio = None

        self.hide = False
        self.intensity = 1



        if shape_type == cs.DetectorShape.annular:
            roi_outer = self.rois[0]
            roi_inner = self.rois[1]
            roi_outer.sigRegionChangeFinished.connect(
                lambda: self.update_annulus_pos(roi_inner, roi_outer))
            roi_outer.sigRegionChangeFinished.connect(
                lambda: self.update_annulus_radii(roi_inner, roi_outer))
            # roi_inner.sigRegionChangeFinished.connect(
            #     lambda: self.update_annulus_radii(roi_inner, roi_outer))

        self.updateColor()
        self.controlWidget.colorButton.clicked.connect(self.openColor)
        self.controlWidget.hide_checkBox.clicked.connect(self.hideButtonEvent)

    def openColor(self):
        self.color = self.controlWidget.colorDialog.getColor(initial=self.color)
        self.color_r = self.color.red()
        self.color_g = self.color.green()
        self.color_b = self.color.blue()
        self.color_name = self.color.name()
        self.updateColor()

    def updateColor(self):
        self.controlWidget.colorButton.setStyleSheet("QWidget#colorButton { background-color: %s }" % self.color_name)

        # Set ROI Color
        self.rois[0].setPen(color=self.color)
        if self.shape_type == cs.DetectorShape.annular:
            self.rois[1].setPen(color=self.color)

        # update view
        state = self.rois[0].saveState()
        self.rois[0].setState(state)


    def create_roi_mask(self):
        self.roiMask = mk.get_mask_grp_from_rois([self], self.imageView, self.rois)[0]
        return self.roiMask

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

        if state['pos'][0] == prev_state['pos'][0] and \
                state['pos'][1] == prev_state['pos'][1] and \
                state['size'][0] == prev_state['size'][0] and \
                state['size'][1] == prev_state['size'][1]:
            pass
        else:
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

    def selectEvent(self):
        self.controlWidget.frame.setStyleSheet("QFrame#frame{border: 3px solid #ff0000;}")
        pen = pg.mkPen(color=QColor(255, 0, 0), width=2, style=Qt.DashLine)
        self.rois[0].setPen(pen)
        self.rois[0].hoverPen = pen # your pyqtgraph should be latest version
        self.selected = True

    def unselectEvent(self):
        self.controlWidget.frame.setStyleSheet("QFrame#frame{border: 3px solid #444a4f;}")
        self.rois[0].setPen(color=self.color)
        self.rois[0].hoverPen = pg.mkPen(color='y')
        self.selected = False

    def update_annulus_pos(self):
        """
        Function to keep inner and outer rings of annulus aligned.
        """
        outer = self.rois[0]
        inner = self.rois[1]
        R_outer = outer.size().x() / 2
        R_inner = inner.size().x() / 2
        # Only outer annulus is draggable; when it moves, update position of inner annulus
        x0 = outer.pos().x() + R_outer
        y0 = outer.pos().y() + R_outer
        inner.setPos(x0 - R_inner, y0 - R_inner)

    def update_annulus_radii(self):
        outer = self.rois[0]
        inner = self.rois[1]
        R_outer = outer.size().x() / 2
        R_inner = inner.size().x() / 2
        if R_outer < R_inner:
            x0 = outer.pos().x() + R_outer
            y0 = outer.pos().y() + R_outer
            outer.setSize(2 * R_inner + 6)
            outer.setPos(x0 - R_inner - 3, y0 - R_inner - 3)

    def hideButtonEvent(self):
        if self.controlWidget.hide_checkBox.isChecked():
            pen = pg.mkPen(color=self.color, width=1, style=Qt.DotLine)
            self.rois[0].setPen(pen)
            self.hide = True
        else:
            self.rois[0].setPen(color=self.color)
            self.hide = False
        # update view
        state = self.rois[0].saveState()
        self.rois[0].setState(state)

