import numpy as np
import copy
from ..utils import constants as cs
import pyqtgraph as pg


class RoiMask():

    def __init__(self, slices: tuple, roiShape=None, innerR=0, data=None, maxSize:tuple=None):

        self.slice_x, self.slice_y = slices[0:2]
        self.size_x = self.slice_x.stop - self.slice_x.start
        self.size_y = self.slice_y.stop - self.slice_y.start
        self.innerR = innerR
        self.isRectShape = False
        self.isMerged = False
        self.maxSize = maxSize

        # get mask data
        if roiShape == cs.DetectorShape.rectangular:
            self.data = np.ones((self.size_x, self.size_y), dtype=bool)
        elif roiShape == cs.DetectorShape.point:
            self.data = np.ones((1, 1), dtype=bool)
        elif roiShape == cs.DetectorShape.circular:
            self.data = get_circ_mask(self.size_x, self.size_y)
        elif roiShape == cs.DetectorShape.annular:
            self.data = get_annular_mask(self.size_x, self.size_y, self.innerR)
        elif roiShape == cs.DetectorShape.zero:
            self.data = np.zeros((self.size_x, self.size_y), dtype=bool)
        elif roiShape is None:
            self.data = data

        # trim the data to datacube size


        # isRectShape
        if roiShape in (cs.DetectorShape.rectangular, cs.DetectorShape.point):
            self.isRectShape = True

        # is it merged mask?
        if roiShape is None:
            self.isMerged = True

    def trim_data_to_image(self):
        """
        crop mask when get out of image boundary
        """
        if self.maxSize is not None:
            max_x, max_y = self.maxSize
            x_start = self.slice_x.start
            y_start = self.slice_y.start
            x_stop = self.slice_x.stop
            y_stop = self.slice_y.stop
            if self.slice_x.start < 0 :
                x_start = 0
            if self.slice_x.stop < 0 :
                x_stop = 0
            if self.slice_y.start < 0 :
                y_start = 0
            if self.slice_y.stop < 0 :
                y_stop = 0
            if self.slice_x.stop > max_x :
                x_stop = max_x
            if self.slice_x.start > max_x :
                x_start = max_x
            if self.slice_y.stop > max_y :
                y_stop = max_y
            if self.slice_y.start > max_y :
                y_start = max_y
            self.slice_x = slice(x_start, x_stop)
            self.slice_y = slice(y_start, y_stop)
            self.size_x = self.slice_x.stop - self.slice_x.start
            self.size_y = self.slice_y.stop - self.slice_y.start
            self.data = self.data[:self.size_x, :self.size_y]
        return self

    def getCenter(self):
        grid_y, grid_x = np.meshgrid(
            np.arange(self.slice_y.start, self.slice_y.stop),
            np.arange(self.slice_x.start, self.slice_x.stop)
        )
        center_x = int(np.sum(grid_x * self.data) / np.sum(self.data))
        center_y = int(np.sum(grid_y * self.data) / np.sum(self.data))
        return center_x, center_y

    def count_mask_pixel(self):
        return np.sum(self.data)


def merge(mask_list: list):
    if len(mask_list) == 1:
        return mask_list[0]

    # create zero mask
    zero_mask = create_zero_mask(mask_list)

    # create new masks with zero mask shape
    new_masks = [copy.deepcopy(zero_mask)] * len(mask_list)

    # put data in new_masks
    for roiMask, new_mask in zip(mask_list, new_masks):
        new_mask.data[
        roiMask.slice_x.start - zero_mask.slice_x.start:
        roiMask.slice_x.stop - zero_mask.slice_x.start,
        roiMask.slice_y.start - zero_mask.slice_y.start:
        roiMask.slice_y.stop - zero_mask.slice_y.start
        ] = roiMask.data

    # merge it
    rs_mask = copy.deepcopy(zero_mask)
    for new_mask in new_masks:
        rs_mask.data = np.logical_or(new_mask.data, rs_mask.data)

    return rs_mask


def create_zero_mask(masks):
    min_x = np.min([roiMask.slice_x.start for roiMask in masks])
    min_y = np.min([roiMask.slice_y.start for roiMask in masks])
    max_x = np.max([roiMask.slice_x.stop for roiMask in masks])
    max_y = np.max([roiMask.slice_y.stop for roiMask in masks])
    zero_maskdata = np.zeros((max_x - min_x, max_y - min_y))
    return RoiMask((slice(min_x, max_x), slice(min_y, max_y)), data=zero_maskdata)


def isOverlapped(mask_list: list):
    if len(mask_list) == 1:
        return False

    # create zero mask
    zero_mask = create_zero_mask(mask_list)

    # create new masks with zero mask shape
    new_masks = [copy.deepcopy(zero_mask) for _ in mask_list]

    # put data in new_masks
    for roiMask, new_mask in zip(mask_list, new_masks):
        new_mask.data[
        roiMask.slice_x.start - zero_mask.slice_x.start:
        roiMask.slice_x.stop - zero_mask.slice_x.start,
        roiMask.slice_y.start - zero_mask.slice_y.start:
        roiMask.slice_y.stop - zero_mask.slice_y.start
        ] = roiMask.data

    # merge it
    rs_mask = new_masks[0]
    for new_mask in new_masks[1:]:
        rs_mask.data = np.logical_and(new_mask.data, rs_mask.data)
        if np.sum(rs_mask.data) > 0:
            return True

    return False


def get_compound_mask_list(mask_list: list):
    compound_mask = []

    while len(mask_list) > 0:
        overlappedMask = [mask_list.pop(0)]
        for mask in mask_list:
            if isOverlapped(overlappedMask + [mask]):
                _mask = mask_list.pop(mask_list.index(mask))
                overlappedMask.append(_mask)
        compound_mask.append(merge(overlappedMask))

    return compound_mask


def get_mask_grp_from_rois(detector_grp: list, imageView: pg.ImageView):

    roi_mask_grp = []
    for dtt in [detector for detector in detector_grp if not detector.hide]:
        shape_type = dtt.shape_type
        rois = dtt.rois

        slices, transforms = dtt.rois[0].getArraySlice(imageView.image,
                                                       imageView)
        slices = slices[0:2]

        if shape_type in (cs.DetectorShape.rectangular, cs.DetectorShape.circular):
            mask = RoiMask(roiShape=shape_type, slices=slices, maxSize=imageView.image.shape[0:2])
        elif shape_type is cs.DetectorShape.point:
            x = np.int(np.ceil(rois[0].x()))
            y = np.int(np.ceil(rois[0].y()))
            slices = (slice(x, x + 1), slice(y, y + 1))
            mask = RoiMask(roiShape=shape_type, slices=slices, maxSize=imageView.image.shape[0:2])
        elif shape_type is cs.DetectorShape.annular:
            slice_x, slice_y = slices
            slices_inner, transforms = rois[1].getArraySlice(imageView.image,
                                                             imageView)
            slices_inner = slices_inner[0:2]
            slice_inner_x, slice_inner_y = slices_inner
            R = 0.5 * ((slice_inner_x.stop - slice_inner_x.start) / (slice_x.stop - slice_x.start) + (
                    slice_inner_y.stop - slice_inner_y.start) / (slice_y.stop - slice_y.start))
            mask = RoiMask(roiShape=shape_type, slices=slices, innerR=R, maxSize=imageView.image.shape[0:2])
        roi_mask_grp.append(mask)
    return roi_mask_grp


def get_circ_mask(size_x, size_y, R=1):
    rs = np.fromfunction(
        lambda x, y: (((x + 0.5) / (size_x / 2.) - 1) ** 2 + ((y + 0.5) / (size_y / 2.) - 1) ** 2) < R ** 2,
        (size_x, size_y))
    return rs


def get_annular_mask(size_x, size_y, innerR):
    return np.logical_xor(get_circ_mask(size_x, size_y), get_circ_mask(size_x, size_y, innerR))
