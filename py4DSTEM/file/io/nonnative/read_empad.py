# Reads an EMPAD 4D-STEM dataset

from pathlib import Path
from ...datastructure import DataCube
import os
from os.path import splitext
from pathlib import Path
from xml.dom import minidom
import numpy as np
from PyQt5.QtWidgets import QWidget

detector_size_x = 128
detector_size_y = 128
detector_pixel_data_size = 4
image_gap_size = 1024
frame_size = detector_size_x * detector_size_y * detector_pixel_data_size \
             + image_gap_size


def read_empad(fp, mem="RAM", binfactor=1, **kwargs):
    """
    Read an EMPAD 4D-STEM file.

    Accepts:
        fp          str or Path Path to the file
        mem         str         (opt) Specifies how the data should be stored; must be "RAM" or "MEMMAP". See
                                docstring for py4DSTEM.file.io.read. Default is "RAM".
        binfactor   int         (opt) Bin the data, in diffraction space, as it's loaded. See docstring for
                                py4DSTEM.file.io.read.  Default is 1.
        **kwargs

    Returns:
        dc          DataCube    The 4D-STEM data.
        md          MetaData    The metadata.
    """
    assert(isinstance(fp,(str,Path))), "Error: filepath fp must be a string or pathlib.Path"
    assert(mem in ['RAM','MEMMAP']), 'Error: argument mem must be either "RAM" or "MEMMAP"'
    assert(isinstance(binfactor,int)), "Error: argument binfactor must be an integer"
    assert(binfactor>=1), "Error: binfactor must be >= 1"

    if (mem,binfactor)==("RAM",1):
        # TODO
        pass
    elif (mem,binfactor)==("MEMMAP",1):
        # TODO
        pass
    elif (mem)==("RAM"):
        # TODO
        pass
    else:
        # TODO
        pass

    rawPath, scanSize = get_rawpath_and_scansize(fp)
    data = get_data_from_raw_file(rawPath, scanSize)
    dc = DataCube(data)
    md = None

    # TK TODO load the metadata

    return dc, md


def get_rawpath_and_scansize(fp: str):
    _, fext = splitext(fp)
    if fext in [".xml"]:
        # attribution,copyright : Alexander Clausen
        # https://github.com/LiberTEM/LiberTEM/blob/master/src/libertem/io/dataset/empad.py
        # license : GPLv3
        try:
            dom = minidom.parse(fp)
            root = dom.getElementsByTagName("root")[0]
            raw_filename = root.getElementsByTagName("raw_file")[0].getAttribute('filename')
            # because these XML files contain the full path, they are not relocatable.
            # we strip off the path and only use the basename, hoping the .raw file will
            # be in the same directory as the XML file:
            filename = os.path.basename(raw_filename)
            path_raw = os.path.join(
                os.path.dirname(fp),
                filename
            )
            scan_y = int(root.getElementsByTagName("pix_y")[0].childNodes[0].data.strip("'"))
            scan_x = int(root.getElementsByTagName("pix_x")[0].childNodes[0].data.strip("'"))
            scan_size = (scan_y, scan_x)
            return path_raw, scan_size
        except Exception as e:
            raise Exception(
                "could not initialize EMPAD xml file; error: %s" % (
                    str(e))
            )
    if fext in [".raw"]:
        try:
            fileSize = os.path.getsize(fp)
            assert (fileSize % frame_size == 0), "Error: Are you sure using EMPAD raw files?"
            squareRootedSize = int(np.sqrt(fileSize // frame_size))
            assert (squareRootedSize * squareRootedSize == fileSize // frame_size), "Error: Cannot specify EMPAD scan size. Currently, only squared sample works."
            return fp, (squareRootedSize, squareRootedSize)
        except Exception as e:
            raise Exception(
                "could not initialize EMPAD raw file; error: %s" % (
                    str(e))
            )


def get_data_from_raw_file(rawFilePath: str, size: (int, int)):
    scan_size_x, scan_size_y = size
    image_gap_y = image_gap_size // detector_pixel_data_size // detector_size_y
    data = np.fromfile(rawFilePath, dtype=np.float32, count=-1, offset=0)
    data = data.reshape(scan_size_y,
                        scan_size_x,
                        detector_size_y + image_gap_y,
                        detector_size_x)
    data = np.delete(data, np.s_[detector_size_y::], 2)
    data = data.transpose(1,0,2,3)
    return data

# class sampleSizeDialog(QWidget):
#     def __init__(self):
#         QWidget.__init__(self)
