
import pyfx

from .base import Effect

import numpy as np

class MixForeAndBack(Effect):
    """
    Mix a foreground and background.  The mix is determined by the mask waypoint
    paramter.  The mask should be a 2D np.uint8 array. Values of 0 will be all
    background, values of 255 will be all foreground. The function will coerce
    any array/PIL.Image/file into a single-channel array.  This means a black
    and white images will work fine.  A color image will be flattend to gray
    scale and then applied.

    This is typically applied as the first effect.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"mask":None}

        super().__init__(workspace)

    def render(self,img):

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        if self.mask[t] is not None:

            # Make sure mask is a single channel array
            mask = pyfx.util.to_array(self.mask[t],num_channels=1,dtype=np.uint8)

            bg = np.copy(self._workspace.background.image)
            fg = pyfx.util.to_array(img,num_channels=4,dtype=np.uint8)
            fg[:,:,3] = self.mask[t]*self.alpha[t]

            return pyfx.util.alpha_composite(bg,fg)

        return img
