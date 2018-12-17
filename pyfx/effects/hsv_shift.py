import pyfx
from .base import Effect

from skimage import color

import numpy as np

class HSVShift(Effect):
    """
    Apply fluctuating changes in hue, saturation, and value across a collection
    of video frames.

    Waypoint properties:

    hue: float from 0 to 1. Rotate hue of each pixel by this amount.
    saturation: float from 0 to 1.  Multiply saturation value of each pixel by
                this amount.
    value: float from 0 to 1.  Multiply value of each pixel by this amount.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"hue":1.0,
                                  "saturation":1.0,
                                  "value":1.0}

        super().__init__(workspace)

    def render(self,img):
        """
        Render the image at time t.
        """

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        # Convert to hsv
        alpha = None
        if len(img.shape) == 2:
            hsv = color.rgb2hsv(color.gray2rgb(img))
        elif len(img.shape) == 3:
            if img.shape[2] == 3:
                hsv = color.rgb2hsv(img)
            elif img.shape[2] == 4:
                # Save the alpha channel if it exists
                alpha = img[:,:,3]
                hsv = color.rgb2hsv(img[:,:,:3])
            else:
                err = "input image should be grayscale, RGB, or RGBA\n"
                raise ValueError(err)
        else:
            err = "input image should be grayscale, RGB, or RGBA\n"
            raise ValueError(err)

        # Apply hue, saturation, value transformations to hsv
        hsv[:,:,0] = hsv[:,:,0]*self.hue[t]
        hsv[:,:,1] = hsv[:,:,1]*self.saturation[t]
        hsv[:,:,2] = hsv[:,:,2]*self.value[t]

        # Convert back to rgb
        rgb = pyfx.util.to_array(color.hsv2rgb(hsv),
                                 dtype=np.uint8,
                                 num_channels=3)

        # Protect masked portions of the input image
        rgb = self._protect(img,rgb)

        # Convert to original input format
        if len(img.shape) == 2:
            out = pyfx.util.to_array(rgb,dtype=img.dtype,num_channels=1)
        else:
            if img.shape[2] == 3:
                out = rgb
            else:
                out = np.zeros(img.shape,dtype=img.dtype)
                out[:,:,:3] = rgb[:,:,:3]
                out[:,:,3] = alpha

        return out
