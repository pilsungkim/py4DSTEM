from py4DSTEM.file.datastructure import datacube
from . import mask as mk
import numpy as np

def _get_diffraction_image_average(datacube: datacube, mask: mk):
    try:
        if mask.isRectShape:
            img = np.sum(datacube.data[mask.slice_x, mask.slice_y, :, :], axis=(0, 1))
        else:
            slice_data = datacube.data[mask.slice_x, mask.slice_y, :, :]
            slice_data = slice_data.transpose((2,3,0,1))
            masked_data = slice_data * mask.data
            img = np.sum(masked_data, axis=(2, 3))
        return img, 1
    except ValueError:
        return 0, 0

def get_diffraction_image(datacube: datacube, mask: mk):
    return _get_diffraction_image_average(datacube, mask)