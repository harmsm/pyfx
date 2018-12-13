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
    protect_mask: 2D array applied as an alpha mask to protect certain
                  chunks of the image from exposure changes.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"hue":1.0,
                                  "saturation":1.0,
                                  "value":1.0,
                                  "protect_mask":None}

        super().__init__(workspace)

    def render(self,img,t):
        """
        Render the image at time t.
        """

        # Convert to hsv
        alpha = None
        if len(img.shape) == 2:
            hsv = color.rgb2hsv(color.gray2rgb(img))
        elif len(img.shape) == 3:
            if img.shape[2] == 3:
                hsv = color.rgb2hsv(img)
            elif img.shape[2] == 4:
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
        rgb = pyfx.util.convert.float_to_int(color.hsv2rgb(hsv))

        if self.protect_mask[t] is not None:

            # Drop protection mask onto original image
            protect = np.zeros((img.shape[0],img.shape[1],4),dtype=np.uint8)
            if len(img.shape) == 2:
                protect[:,:,:3] = color.gray2rgb(img)
            else:
                protect[:,:,:3] = img[:,:,:3]

            protect[:,:,3] = self.protect_mask[t]

            # Add an alpha channel to the new rgb value
            rgba = 255*np.ones((img.shape[0],img.shape[1],4),dtype=np.uint8)
            rgba[:,:,:3] = rgb

            # Do alpha compositing
            out = pyfx.util.convert.alpha_composite(rgba,protect)

            # Drop alpha channel
            rgb = out[:,:,:3]

        # Convert to original input format
        if len(img.shape) == 2:
            out = pyfx.util.convert.float_to_int(color.rgb2gray(rgb))
        else:
            if img.shape[2] == 3:
                out = rgb
            else:
                out = np.zeros(img.shape,dtype=img.dtype)
                out[:,:,:3] = rgb
                out[:,:,3] = alpha

        return out
