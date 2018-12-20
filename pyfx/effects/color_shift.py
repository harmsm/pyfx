__description__ = \
"""
Class for altering the color of frames over time.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-19"

import pyfx
from .base import Effect
import numpy as np
from skimage import color

class ColorShift(Effect):
    """
    Alter hue, saturation, value, color temperature, or white balance
    across a collection of video frames.  HSV is altered first, followed by
    white balance, and then followed by color temperature.

    Waypoint properties:

    hue: float from 0 to 1. If negative, do not change hue.
    saturation: float from 0 to 1.  If negative, do not change saturation.
    value: float from 0 to 1.  If negative, do not change value.
    hue_shift: float from 0 to 1. Shift hue by this amount.  If negative, do
               not change value.
    saturation_shift: float from 0 to 1. Shift saturation by this amount.
                      If negative, do not change value.
    value_shift: float from 0 to 1. Shift value by this amount.  If negative, do
               not change value.
    temperature: color temperature, in Kelvin, to mix in.  If negative, do
                 nothing.
    white_point: RGB value of a "real" white object to calibrate the image.
                 length-three tuple or None.  If None, do nothing.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"hue":-1.0,
                                  "saturation":-1.0,
                                  "value":-1.0,
                                  "hue_shift":-1.0,
                                  "saturation_shift":-1.0,
                                  "value_shift":-1.0,
                                  "temperature":-1.0,
                                  "white_point":None}

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

        # Trim interpolated values that incidentally dropped below 0 or
        # rose above 1
        for v in [self.hue,
                  self.saturation,
                  self.value,
                  self.hue_shift,
                  self.saturation_shift,
                  self.value_shift]:

                  v[np.logical_and(v < 0, v > -over_under_tolerance)] = 0.0
                  v[np.logical_and(v > 1, v < 1 + over_under_tolerance)] = 1.0

        self._baked = True

    def render(self,img):
        """
        Render the image at time t.
        """

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        # Save the alpha channel if it exists
        saved_alpha = None
        if len(img.shape) == 3 and img.shape[2] == 4:
            saved_alpha = img[:,:,3]

        # Make sure we are in RGB
        rgb = pyfx.util.to_array(img,num_channels=3,dtype=np.uint8)

        # Manipulate HSV if requested
        if self.hue[t] >= 0 or \
           self.saturation[t] >= 0 or \
           self.value[t] >= 0 or \
           self.hue_shift[t] >= 0 or \
           self.saturation_shift[t] >= 0 or \
           self.value_shift[t] >= 0:

            hsv = color.rgb2hsv(rgb)

            # Set hue, saturation, and value
            if self.hue[t] >= 0:
                hsv[:,:,0] = self.hue[t]

            if self.saturation[t] >= 0:
                hsv[:,:,1] = self.saturation[t]

            if self.value[t] >= 0:
                hsv[:,:,2] = self.value[t]

            # shift hue, saturation and value
            if self.hue_shift[t] >= 0:
                hsv[:,:,0] += self.hue_shift[t]

            if self.saturation_shift[t] >= 0:
                hsv[:,:,1] += self.saturation_shift[t]

            if self.value_shift[t] >= 0:
                hsv[:,:,2] += self.value_shift[t]

            # Convert back to rgb
            rgb = pyfx.util.to_array(color.hsv2rgb(hsv),
                                     dtype=np.uint8,
                                     num_channels=3)

        # Set white balance to specified white point
        if self.white_point[t] is not None:
            rgb = pyfx.util.helper.adjust_white_balance(rgb,
                                                        self.white_point[t])

        # Apply color temperature
        if self.temperature[t] > 0:
            white_point = pyfx.util.helper.kelvin_to_rgb(self.temperature[t])
            rgb = pyfx.util.helper.adjust_white_balance(rgb,white_point)

        # If alpha is defined, perform an alpha composite with the original
        # image.
        if self.alpha[t] != 1.0:
            local_alpha = np.int(np.round(self.alpha[t]))
            if local_alpha < 0:
                local_alpha = 0
            elif local_alpha > 255:
                local_alpha = 255

            rgba = pyfx.util.to_array(rgb,num_channels=4,dtype=np.uint8)
            rgba[:,:,3] = local_alpha

            original_img = pyfx.util.to_array(img,num_channels=4,dtype=np.uint8)
            rgb = pyfx.util.alpha_composite(original_img,rgba)[:,:,:3]

        # Protect masked portions of the input image
        rgb = self._protect(img,rgb)

        # Convert to original input format
        if len(img.shape) == 2:
            out = pyfx.util.to_array(rgb,dtype=img.dtype,num_channels=1)
        else:
            out = pyfx.util.to_array(rgb,
                                     num_channels=img.shape[2],
                                     dtype=img.dtype)
            if saved_alpha is not None:
                out[:,:,3] = saved_alpha

        return out
