import pyfx
from .base import Effect

from skimage import color

import numpy as np

class ColorShift(Effect):
    """
    Apply fluctuating changes in hue, saturation, value and/or color temperature
    across a collection of video frames.  HSV is altered first, followed by
    color temperature.

    Waypoint properties:

    hue: float from 0 to 1. If negative, do not change hue.
    saturation: float from 0 to 1.  If negative, do not change saturation.
    value: float from 0 to 1.  If negative, do not change value.
    temperature: color temperature, in Kelvin, to mix in.  If negative, do
                 nothing.
    temperature_mix_value: float from 0 to 1.  How much to of the new color
                           temperature to mix into the original image.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"hue":-1.0,
                                  "saturation":-1.0,
                                  "value":-1.0,
                                  "temperature":-1.0,
                                  "temperature_mix_value":0.5}

        super().__init__(workspace)

    def bake(self,smooth_window_len=0,over_under_tolerance=0.01):
        """
        Interpolate waypoints and clean up HSV.

        smooth_window_len: length of smoothing window between interpolated
                           points
        over_under_tolerance: set each HSV of -over_under_tolerance to 0 and
                              1 + over_under_tolerance to 1.0.  This prevents
                              numerical errors after interpolation from
                              propagating to strange HSV values.
        """

        self._interpolate_waypoints(smooth_window_len)

        # Trim interpolated hsv that incidentally dropped below 0
        self.hue[np.logical_and(self.hue < 0,
                                self.hue > -over_under_tolerance)] = 0.0
        self.saturation[np.logical_and(self.saturation < 0,
                                       self.saturation > -over_under_tolerance)] = 0.0
        self.value[np.logical_and(self.value < 0,
                                self.value > -over_under_tolerance)] = 0.0

        # Trim interpolated hsv that incidentally went above 1
        self.hue[np.logical_and(self.hue > 1,
                                self.hue < 1 + over_under_tolerance)] = 1.0
        self.saturation[np.logical_and(self.saturation > 1,
                                       self.saturation < 1 + over_under_tolerance)] = 1.0
        self.value[np.logical_and(self.value > 1,
                                  self.value < 1 + over_under_tolerance)] = 1.0

        self._baked = True

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
        if self.hue[t] >= 0:
            hsv[:,:,0] = self.hue[t]

        if self.saturation[t] >= 0:
            hsv[:,:,1] = self.saturation[t]

        if self.value[t] >= 0:
            hsv[:,:,2] = self.value[t]

        # Convert back to rgb
        rgb = pyfx.util.to_array(color.hsv2rgb(hsv),
                                 dtype=np.uint8,
                                 num_channels=3)


        # Apply tempreature
        if self.temperature[t] > 0:

            mix_value = np.int(np.round(255*self.temperature_mix_value[t]))

            T = np.zeros((rgb.shape[0],rgb.shape[1],4),dtype=np.uint8)
            T[:,:,:3] = pyfx.util.helper.kelvin_to_rgb(self.temperature[t])
            T[:,:,3] = mix_value

            rgba = pyfx.util.to_array(rgb,num_channels=4)
            rgb[:,:,3] = 255 - mix_value

            # Form alpha composite with new color temperature
            mixed = pyfx.util.alpha_composite(rgba,T)

            rgb = mixed[:,:,:3]

        # Protect masked portions of the input image
        rgb = self._protect(img,rgb)

        if self.alpha[t] != 0:
            rgba = np.zeros((rgb.shape[0],rgb.shape[1],4),dtype=np.uint8)
            rgba[:,:,:3] = rgb[:,:,:3]
            rgba[:,:,3] = alpha

            combined = pyfx.util.alpha_composite(img,rgba)
            rgb = combined[:,:,:3]


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
