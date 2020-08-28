import numpy as np
from pyqtgraph.graphicsItems import ROI
import py4DSTEM.process.virtualimage.mask as mk
import py4DSTEM.process.utils.constants as ct


def get_virtual_image(datacube, _detector_mode_type: int, mask: mk.RoiMask, center: tuple):
    if _detector_mode_type == ct.DetectorModeType.integrate:
        img, success = get_virtual_image_integrate(datacube, mask)
    if _detector_mode_type == ct.DetectorModeType.diffX:
        img, success = get_virtual_image_diffX(datacube, mask, center)
    if _detector_mode_type == ct.DetectorModeType.diffY:
        img, success = get_virtual_image_diffY(datacube, mask, center)
    if _detector_mode_type == ct.DetectorModeType.CoMX:
        img, success = get_virtual_image_CoMX(datacube, mask, center)
    if _detector_mode_type == ct.DetectorModeType.CoMY:
        img, success = get_virtual_image_CoMY(datacube, mask, center)
    return img, success


def get_virtual_image_integrate(datacube, mask: mk.RoiMask):
    try:
        if mask.isRectShape:
            img = np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y], axis=(2, 3))
        else:
            img = np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * mask.data, axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_diffX(datacube, mask: mk.RoiMask, center: tuple):
    """
    Returns a virtual image as an ndarray, generated from a circular detector in difference
    mode. Also returns a bool indicating success or failure.
    """
    try:

        if center is not None:
            center_x, center_y = mask.getCenter()
        else:
            center_x, center_y = center

        slice_left = slice(mask.slice_x.start, center_x)
        slice_right = slice(center_x, mask.slice_x.stop)
        if mask.isRectShape:
            img = np.ndarray.astype(
                np.sum(datacube.data[:, :, slice_left, mask.slice_y], axis=(2, 3)) -
                np.sum(datacube.data[:, :, slice_right, mask.slice_y], axis=(2, 3)),
                'int64'
            )
        else:
            img = np.ndarray.astype(
                np.sum(
                    datacube.data[:, :, slice_left, mask.slice_y] * mask.data[:slice_left.stop - slice_left.start, :],
                    axis=(2, 3)) -
                np.sum(datacube.data[:, :, slice_right, mask.slice_y] * mask.data[slice_right.start - slice_right.stop:,
                                                                        :],
                       axis=(2, 3)),
                'int64')
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_diffY(datacube, mask: mk.RoiMask, center: tuple):
    """
    Returns a virtual image as an ndarray, generated from a circular detector in difference
    mode. Also returns a bool indicating success or failure.
    """
    try:

        if center is None:
            center_x, center_y = mask.getCenter()
        else:
            center_x, center_y = center

        slice_left = slice(mask.slice_y.start, center_y)
        slice_right = slice(center_y, mask.slice_y.stop)
        if mask.isRectShape:
            img = np.ndarray.astype(
                np.sum(datacube.data[:, :, mask.slice_x, slice_left], axis=(2, 3)) -
                np.sum(datacube.data[:, :, mask.slice_x, slice_right], axis=(2, 3)),
                'int64'
            )
        else:
            img = np.ndarray.astype(
                np.sum(datacube.data[:, :, mask.slice_x, slice_left] * mask.data[:, :slice_left.stop - slice_left.start],
                    axis=(2, 3)) -
                np.sum(datacube.data[:, :, mask.slice_x, slice_right] * mask.data[:,
                                                                        slice_right.start - slice_right.stop:],
                       axis=(2, 3)),
                'int64')
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_CoMX(datacube, mask: mk.RoiMask, center: tuple):
    """

    """
    ry, rx = np.meshgrid(np.arange(mask.slice_y.stop - mask.slice_y.start),
                         np.arange(mask.slice_x.stop - mask.slice_x.start))

    if center is None:
        center_x, center_y = mask.getCenter()
    else:
        center_x, center_y = center

    rx += mask.slice_x.start - center_x
    ry += mask.slice_y.start - center_y

    try:
        if mask.isRectShape:
            img = np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * rx, axis=(2, 3)) / \
                  np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y], axis=(2, 3))
        else:
            img = np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * rx * mask.data, axis=(2, 3)) / \
                  np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * mask.data, axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_CoMY(datacube, mask: mk.RoiMask, center: tuple):
    """
    Returns a virtual image as an ndarray, generated from a rectangular detector, in CoM
    mode. Also returns a bool indicating success or failure.
    """
    ry, rx = np.meshgrid(np.arange(mask.slice_y.stop - mask.slice_y.start),
                         np.arange(mask.slice_x.stop - mask.slice_x.start))

    if center is None:
        center_x, center_y = mask.getCenter()
    else:
        center_x, center_y = center

    rx += mask.slice_x.start - center_x
    ry += mask.slice_y.start - center_y

    try:
        if mask.isRectShape:
            img = np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * ry, axis=(2, 3)) / \
                  np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y], axis=(2, 3))
        else:
            img = np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * ry * mask.data, axis=(2, 3)) / \
                  np.sum(datacube.data[:, :, mask.slice_x, mask.slice_y] * mask.data, axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0
