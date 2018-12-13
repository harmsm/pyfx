import pyfx
from .base import Effect

from skimage import color

class HSVShift(Effect):
    """
    Apply fluctuating changes in exposure across a collection of video
    frames.

    Waypoint properties:

    hue: float from 0 to 1. Rotate hue of each pixel by this amount.
    saturation: float from 0 to 1.  Multiply saturation value of each pixel by
                this amount.
    value: float from 0 to 1.  Multiply value of each pixel by this amount.
    protect_mask: 2D array applied as an alpha mask to protect certain
                  chunks of the image from exposure changes.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"hue":None,
                                  "saturation":None,
                                  "value":None,
                                  "protect_mask":None}

        super().__init__(workspace)

    def render(self,img,t):

        # Convert to hsv
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
        rgb = color.hsv2rgb(hsv)

        # Convert to original input format
        if len(img.shape) == 2:
            img = color.rgb2gray(rgb)
        else:
            if img.shape[2] == 3:
                img = rgb
            else:
                img = np.zeros(img.shape,dtype=img.dtype)
                img[:,:,:3] = rgb
                img[:,:,3] = alpha

        return img
