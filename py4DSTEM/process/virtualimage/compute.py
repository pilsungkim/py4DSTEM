from . import mask as mk
from . import virtualimage_process3 as vp
from py4DSTEM.file.datastructure.datacube import DataCube
from py4DSTEM.process.utils import constants as cs

class Context:

    def __init__(self, datacube: DataCube):
        """
        load datacube to compute
        """
        self.datacube = datacube

    def get_virtual_image(self, masks: list, integration_mode: cs.DetectorModeType):
        """

        """
        coumpound_mask = mk.get_compound_mask_list(masks)
        merged_mask = mk.merge(coumpound_mask)
        merged_mask_center = merged_mask.getCenter()
        rs=None
        for mask in coumpound_mask:
            img, success = vp.get_virtual_image(
                datacube=self.datacube,
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





