from . import mask as mk, compute_real_image as vp
from ..utils import constants as cs
from . import compute_diffraction_image as di
from ...file.datastructure import datacube
import numpy as np


def get_virtual_image(datacube: datacube, masks: list, integration_mode: cs.DetectorModeType):
    if len(masks) == 0:
        return 0, 0
    masks = [a.trim_data_to_image() for a in masks]
    compound_mask = mk.get_compound_mask_list(masks)
    merged_mask = mk.merge(compound_mask)
    merged_mask_center = merged_mask.getCenter()
    rs = None
    for mask in compound_mask:
        img, success = vp.get_virtual_image(
            datacube=datacube,
            _detector_mode_type=integration_mode,
            mask=mask,
            center=merged_mask_center
        )
        if success:
            if rs is None:
                rs = img
            else:
                rs += img
    return rs, success


def get_virtual_image_color(datacube: datacube, detectors: list):
    if len(detectors) == 0:
        return 0, 0
    integrated_img = None
    for detector in detectors:
        if detector.hide:
            continue
        mask = detector.create_roi_mask()
        mask.trim_data_to_image()
        img, rs = vp.get_virtual_image(datacube, 0, mask, None)
        if rs == 1:
            img_r = img * detector.color_r / 255
            img_g = img * detector.color_g / 255
            img_b = img * detector.color_b / 255
            img = np.dstack((img_r, img_g, img_b))
            if integrated_img is None:
                integrated_img = img
            else :
                integrated_img += img
        else:
            return 0,0
    return integrated_img, 1


def get_diffraction_image(datacube: datacube, masks: list):
    # only average now #
    if len(masks) == 0:
        return 0, 0
    masks = [a.trim_data_to_image() for a in masks]
    compound_mask = mk.get_compound_mask_list(masks)
    # merged_mask = mk.merge(compound_mask)
    # merged_mask_center = merged_mask.getCenter()
    rs = None
    pixel_count = 0
    for mask in compound_mask:
        img, success = di.get_diffraction_image(
            datacube=datacube,
            mask=mask
        )
        pixel_count += np.sum(mask.data)
        if success:
            if rs is None:
                rs = img
            else:
                rs += img
        else:
            break
    if pixel_count != 0:
        rs = rs / pixel_count
    return rs, success


def get_diffraction_image_color(datacube: datacube, detectors: list):
    if len(detectors) == 0:
        return 0, 0
    integrated_img = None
    pixel_count = 0
    for detector in detectors:
        if detector.hide:
            continue
        mask = detector.create_roi_mask()
        mask.trim_data_to_image()
        img, rs = di.get_diffraction_image(datacube,mask)
        pixel_count += np.sum(mask.data)
        if rs == 1:
            img_r = img * detector.color_r / 255
            img_g = img * detector.color_g / 255
            img_b = img * detector.color_b / 255
            img = np.dstack((img_r, img_g, img_b))
            if integrated_img is None:
                integrated_img = img
            else:
                integrated_img += img
        else:
            return 0, 0
    if pixel_count != 0:
        img = img / pixel_count
    return integrated_img, 1


def scaling(img, mode, datacube: datacube):
    if mode == 1:
        # sqrt mode
        img = np.sqrt(img)
    elif mode == 2:
        # log mode
        img = np.log(
            img - np.min(img) + 1)
    elif mode == 3:
        # EWPC mode
        h = np.hanning(datacube.Q_Nx)[:, np.newaxis] @ np.hanning(datacube.Q_Ny)[np.newaxis, :]
        if len(img.shape) == 2:
            img = np.abs(np.fft.fftshift(np.fft.fft2(np.log(
                (h * (img - np.min(img))) + 1)))) ** 2
        elif len(img.shape) == 3:
            img = np.abs(np.fft.fftshift(np.fft.fft2(np.log(
                (np.dstack((h,h,h)) * (img - np.min(img))) + 1)))) ** 2
    return img
