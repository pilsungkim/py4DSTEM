import numpy as np
from pyqtgraph.graphicsItems import ROI


# Utility functions

def get_ROI_dataslice_rect(datacube, slice_x, slice_y):
    """
    Returns a subset of datacube corresponding to a rectangular ROI in the diffraction plane
    specified by slice_x, slice_y
    """
    return datacube.data[:, :, slice_x, slice_y]


def get_circ_mask(size_x, size_y, R=1):
    """
    Returns a mask of shape (size_x,size_y) which is True inside an ellipse with major/minor
    diameters of R*size_x, R*size_y.  Thus if R=1 and size_x=size_y, returns a ciruclar mask which
    is inscribed inside a square array.
    Note that an ellipse, rather than a circle, is used to prevent failure when the slice objects
    returned when calling getArraySlice on a pyqtgraph circular ROI are off-by-one in length.
    """
    return np.fromfunction(
        lambda x, y: (((x + 0.5) / (size_x / 2.) - 1) ** 2 + ((y + 0.5) / (size_y / 2.) - 1) ** 2) < R ** 2,
        (size_x, size_y))


def get_annular_mask(size_x, size_y, R):
    """
    Returns an annular mask, where the outer annulus is inscribed in a rectangle of shape
    (size_x,size_y) - and can thus be elliptical - and the inner radius to outer radius ratio is R.
    """
    return np.logical_xor(get_circ_mask(size_x, size_y), get_circ_mask(size_x, size_y, R))


def get_mask_from_roi(slice_x: slice, slice_y: slice, detector_shape: int, R=1):
    """

    """
    size_x = slice_x.stop - slice_x.start
    size_y = slice_y.stop - slice_y.start
    # Rectangular detector
    if detector_shape == 0:
        mask = None
    # Circular detector
    elif detector_shape == 1:
        mask = get_circ_mask(size_x, size_y)
    # Annular detector
    elif detector_shape == 2:
        mask = get_annular_mask(size_x, size_y, R)
    # Point
    elif detector_shape == 3:
        mask = None
    return mask


def get_virtual_image_integrate(datacube, slice_x, slice_y, detector_shape: int, R=1):
    mask = get_mask_from_roi(slice_x, slice_y, detector_shape, R)
    try:
        if mask is None:
            img = datacube.data[:, :, slice_x, slice_y].sum(axis=(2, 3))
        else:
            img = (datacube.data[:, :, slice_x, slice_y] * mask).sum(axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0


# Detector Mode
def get_virtual_image_diffX(datacube, slice_x, slice_y, detector_shape: int, R=1):
    """
    Returns a virtual image as an ndarray, generated from a circular detector in difference
    mode. Also returns a bool indicating success or failure.
    """
    mask = get_mask_from_roi(slice_x, slice_y, detector_shape, R)
    try:
        midpoint = slice_x.start + (slice_x.stop - slice_x.start) / 2
        slice_left = slice(slice_x.start, int(np.floor(midpoint)))
        slice_right = slice(int(np.ceil(midpoint)), slice_x.stop)
        if mask is None:
            img = datacube.data[:, :, slice_left, slice_y].sum(axis=(2, 3)).astype('int64') - datacube.data[:, :,
                                                                                              slice_right, slice_y].sum(
                axis=(2, 3)).astype('int64')
        else:
            img = np.ndarray.astype(
                np.sum(datacube.data[:, :, slice_left, slice_y] * mask[:slice_left.stop - slice_left.start, :],
                       axis=(2, 3)) - np.sum(
                    datacube.data[:, :, slice_right, slice_y] * mask[slice_right.start - slice_right.stop:, :],
                    axis=(2, 3)), 'int64')
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_diffY(datacube, slice_x, slice_y, detector_shape: int, R=1):
    """

    """
    mask = get_mask_from_roi(slice_x, slice_y, detector_shape, R)
    try:
        midpoint = slice_y.start + (slice_y.stop - slice_y.start) / 2
        slice_bottom = slice(slice_y.start, int(np.floor(midpoint)))
        slice_top = slice(int(np.ceil(midpoint)), slice_y.stop)
        if mask is None:
            img = datacube.data[:, :, slice_x, slice_bottom].sum(axis=(2, 3)).astype('int64') - datacube.data[:, :,
                                                                                                slice_x, slice_top].sum(
                axis=(2, 3)).astype('int64')
        else:
            img = np.ndarray.astype(
                np.sum(datacube.data[:, :, slice_x, slice_bottom] * mask[:, :slice_bottom.stop - slice_bottom.start],
                       axis=(2, 3)) - np.sum(
                    datacube.data[:, :, slice_x, slice_top] * mask[:, slice_top.start - slice_top.stop:], axis=(2, 3)),
                'int64')
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_CoMX(datacube, slice_x, slice_y, detector_shape: int, R=1, start_x=0, start_y=0):
    """

    """
    mask = get_mask_from_roi(slice_x, slice_y, detector_shape, R)
    ry, rx = np.meshgrid(np.arange(slice_y.stop - slice_y.start), np.arange(slice_x.stop - slice_x.start))
    ry += start_y
    rx += start_x
    try:
        if mask is None:
            img = np.sum(datacube.data[:, :, slice_x, slice_y] * rx, axis=(2, 3)) / datacube.data[:, :, slice_x,
                                                                                    slice_y].sum(axis=(2, 3))
        else:
            img = np.sum(datacube.data[:, :, slice_x, slice_y] * rx * mask, axis=(2, 3)) / np.sum(
                datacube.data[:, :, slice_x, slice_y] * mask, axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image_CoMY(datacube, slice_x, slice_y, detector_shape: int, R=1, start_x=0, start_y=0):
    """
    Returns a virtual image as an ndarray, generated from a rectangular detector, in CoM
    mode. Also returns a bool indicating success or failure.
    """
    mask = get_mask_from_roi(slice_x, slice_y, detector_shape, R)
    ry, rx = np.meshgrid(np.arange(slice_y.stop - slice_y.start), np.arange(slice_x.stop - slice_x.start))
    ry += start_y
    rx += start_x
    try:
        if mask is None:
            img = np.sum(datacube.data[:, :, slice_x, slice_y] * ry, axis=(2, 3)) / datacube.data[:, :, slice_x,
                                                                                    slice_y].sum(axis=(2, 3))
        else:
            img = np.sum(datacube.data[:, :, slice_x, slice_y] * ry * mask, axis=(2, 3)) / np.sum(
                datacube.data[:, :, slice_x, slice_y] * mask, axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0


def get_virtual_image(datacube, slice_x, slice_y, _detector_shape: int, _detector_mode_type: int, R=1):
    if _detector_mode_type == DetectorModeType.integrate:
        get_virtual_image_integrate(datacube, slice_x, slice_y, _detector_shape, R)
    if _detector_mode_type == DetectorModeType.diffX:
        get_virtual_image_diffX(datacube, slice_x, slice_y, _detector_shape, R)
    if _detector_mode_type == DetectorModeType.diffY:
        get_virtual_image_diffY(datacube, slice_x, slice_y, _detector_shape, R)
    if _detector_mode_type == DetectorModeType.CoMX:
        get_virtual_image_CoMX(datacube, slice_x, slice_y, _detector_shape, R)
    if _detector_mode_type == DetectorModeType.CoMY:
        get_virtual_image_CoMY(datacube, slice_x, slice_y, _detector_shape, R)


class DetectorModeType:
    integrate = 0
    diffX = 1
    diffY = 2
    CoMX = 3
    CoMY = 4


class DetectorShape:
    rectangular = 0
    circular = 1
    annular = 2
