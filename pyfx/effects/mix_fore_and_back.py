__description__ = \
"""
Mix the foreground of the current frame with the background for the whole
clip.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-19"

import pyfx
from .base import Effect
import numpy as np

class MixForeAndBack(Effect):
    """
    Combine the current image (foreground) and the clip background, using a
    mask to determine how they should be alpha composited.  The mask is a 2D
    array where low values mean background and high values mean foreground. For
    an int array, low = 0 and high = 255; for a float array, low = 0, high =
    255.  If the array has more than one channel, it is mixed down to a single
    channel before being applied. The alpha channel of the mask is ignored.

    Waypoint properties:

    mask: numpy array of appropriate size, 1 channel.  Determines how mixing is
          done.  If None, do not mix and return foreground image.
    bg_override: image to use instead of the workspace background channel
                 for the background.  If None, use the background image for the
                 workspace.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"mask":None,
                                  "bg_override":None}

        super().__init__(workspace)

    def render(self,img):

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        new_img = img
        if self.mask[t] is not None:

            # Put mask into single channel 0-255 array
            if self.alpha[t] != 1.0:
                mask = pyfx.util.to_array(self.mask[t],
                                          num_channels=1,
                                          dtype=np.float)
                mask = pyfx.util.to_array(mask*self.alpha[t],
                                          num_channels=1,
                                          dtype=np.uint8)
            else:
                mask = pyfx.util.to_array(self.mask[t],
                                          num_channels=1,
                                          dtype=np.uint8)

            # Load background
            local_bg = self._workspace.background.image
            if self.bg_override[t] is not None:
                local_bg = self.bg_override[t]
            bg = pyfx.util.to_array(local_bg,
                                    num_channels=4,dtype=np.uint8)

            # Load foreground and stick mask into alpha channel
            fg = pyfx.util.to_array(img,num_channels=4,dtype=np.uint8)
            fg[:,:,3] = mask

            # Alpha composite
            new_img = pyfx.util.alpha_composite(bg,fg)

            # Protect the image, if requested
            new_img = self._protect(img,new_img)

        return new_img
