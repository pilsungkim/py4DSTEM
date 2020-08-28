import numpy as np
import matplotlib.pyplot as plt
import copy
import py4DSTEM.process.utils.constants as ct

class RoiMask():

    def __init__(self, slices: tuple, roiShape=None, innerR=0, data=None):

        self.slice_x, self.slice_y = slices
        self.size_x = self.slice_x.stop - self.slice_x.start
        self.size_y = self.slice_y.stop - self.slice_y.start
        self.innerR = innerR
        self.isRectShape = False
        self.isMerged = False

        # get mask data
        if roiShape == ct.DetectorShape.rectangular:
            self.data = np.ones((self.size_x, self.size_y), dtype=bool)
        elif roiShape == ct.DetectorShape.point:
            self.data = np.ones((1, 1), dtype=bool)
        elif roiShape == ct.DetectorShape.circular:
            self.data = get_circ_mask(self.size_x, self.size_y)
        elif roiShape == ct.DetectorShape.annular:
            self.data = get_annular_mask(self.size_x, self.size_y, self.innerR)
        elif roiShape == ct.DetectorShape.zero:
            self.data = np.zeros((self.size_x, self.size_y),dtype=bool)
        elif roiShape is None:
            self.data = data

        # isRectShape
        if roiShape in (ct.DetectorShape.rectangular, ct.DetectorShape.point):
            self.isRectShape = True

        # is it merged mask?
        if roiShape is None:
            self.isMerged = True

    def getCenter(self):
        grid_y, grid_x = np.meshgrid(
            np.arange(self.slice_y.start,self.slice_y.stop),
            np.arange(self.slice_x.start,self.slice_x.stop)
        )
        center_x = int(np.sum(grid_x * self.data) / np.sum(self.data))
        center_y = int(np.sum(grid_y * self.data) / np.sum(self.data))
        return center_x, center_y

    def crop_to_fit_image_size(self):
        """
        crop mask when get out of image boundary
        """
        # todo


class RoiMaskList(list):

    # # Deprecated
    # def merge2(self):
    #     rs_mask = self[0]
    #     for roiMask in self[1:]:
    #         min_x, _ = np.sort((roiMask.slice_x.start, rs_mask.slice_x.start))
    #         _, max_x = np.sort((roiMask.slice_x.stop, rs_mask.slice_x.stop))
    #         min_y, _ = np.sort((roiMask.slice_y.start, rs_mask.slice_y.start))
    #         _, max_y = np.sort((roiMask.slice_y.stop, rs_mask.slice_y.stop))
    #
    #         zero_maskdata = np.zeros((max_x - min_x, max_y - min_y))
    #         roiMask_or_zeroMask_data = zero_maskdata.copy()
    #         rsMask_or_zeroMask_data = zero_maskdata.copy()
    #         roiMask_or_zeroMask_data[roiMask.slice_x.start-min_x:roiMask.slice_x.stop-min_x,
    #                 roiMask.slice_y.start-min_y:roiMask.slice_y.stop-min_y] = roiMask.data
    #         rsMask_or_zeroMask_data[rs_mask.slice_x.start - min_x:rs_mask.slice_x.stop - min_x,
    #                 rs_mask.slice_y.start - min_y:rs_mask.slice_y.stop - min_y] = rs_mask.data
    #         rs_mask = np.logical_or(roiMask_or_zeroMask_data, rsMask_or_zeroMask_data)
    #         rs_mask = RoiMask((slice(min_x,max_x),slice(min_y,max_y)),data=rs_mask)
    #         # plt.imshow(rs_mask.data)
    #         # plt.show()
    #     return rs_mask

    def merge(self):

        # create zero mask
        zero_mask = self.create_zero_mask(self)

        # create new masks with zero mask shape
        new_masks = [copy.deepcopy(zero_mask)] * len(self)

        # put data in new_masks
        for roiMask, new_mask in zip(self, new_masks):
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

    def create_zero_mask(self, masks):
        min_x = np.min([roiMask.slice_x.start for roiMask in masks])
        min_y = np.min([roiMask.slice_y.start for roiMask in masks])
        max_x = np.max([roiMask.slice_x.stop for roiMask in masks])
        max_y = np.max([roiMask.slice_y.stop for roiMask in masks])
        zero_maskdata = np.zeros((max_x - min_x, max_y - min_y))
        return RoiMask((slice(min_x,max_x),slice(min_y,max_y)),data=zero_maskdata)

    def isOverlapped(self):
        # create zero mask
        zero_mask = self.create_zero_mask()

        # create new masks with zero mask shape
        new_masks = [copy.deepcopy(zero_mask)] * len(self)

        # put data in new_masks
        for roiMask, new_mask in zip(self, new_masks):
            new_mask.data[
                roiMask.slice_x.start - zero_mask.slice_x.start:
                roiMask.slice_x.stop - zero_mask.slice_x.start,
                roiMask.slice_y.start - zero_mask.slice_y.start:
                roiMask.slice_y.stop - zero_mask.slice_y.start
                ] = roiMask.data

        # merge it
        rs_mask = copy.deepcopy(zero_mask)
        for new_mask in new_masks:
            rs_mask.data = np.logical_and(new_mask.data, rs_mask.data)

        if np.sum(rs_mask.data) > 0:
            return True
        else:
            return False

###############

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
    return RoiMask((slice(min_x,max_x),slice(min_y,max_y)),data=zero_maskdata)


def isOverlapped(mask_list: list):
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
        rs_mask.data = np.logical_and(new_mask.data, rs_mask.data)

    if np.sum(rs_mask.data) > 0:
        return True
    else:
        return False

def get_compound_mask_list(mask_list: list):

    compound_mask = []

    while len(mask_list) > 0:
        overlappedMask = [mask_list.pop(0)]
        for mask in mask_list:
            if isOverlapped(overlappedMask+[mask]):
                _mask = mask_list.pop(mask_list.index(mask))
                overlappedMask.append(_mask)
        compound_mask.append(merge(overlappedMask))

    return compound_mask

###############




def get_circ_mask(size_x, size_y, R=1):
    rs = np.fromfunction(
        lambda x, y: (((x + 0.5) / (size_x / 2.) - 1) ** 2 + ((y + 0.5) / (size_y / 2.) - 1) ** 2) < R ** 2,
        (size_x, size_y))
    return rs


def get_annular_mask(size_x, size_y, innerR):
    return np.logical_xor(get_circ_mask(size_x, size_y), get_circ_mask(size_x, size_y, innerR))


