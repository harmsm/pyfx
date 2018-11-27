import numpy as np
import colorsys

class ColorShifter:
    """
    Class that returns an RGB value that shifts over time.
    """

    def __init__(self,initial_hue=None,color_step=0.01,min_hue=0.28,max_hue=0.56,
                 saturation=1.0,value=1.0):
        """
        Setting initial RGB color will overwrite saturation and value.
        """

        self._initial_hue = initial_hue
        self._color_step = color_step
        self._min_hue = min_hue
        self._max_hue = max_hue
        self._saturation = saturation
        self._value = value

        # figure out initial hue if not set
        if self._initial_hue is None:
            self._initial_hue = self._min_hue

        # Determine the sign and current hue
        if self._initial_hue < self._min_hue:
            self._current_hue = self._min_hue
            self._sign = 1
        elif self._initial_hue > self._max_hue:
            self._current_hue = self._max_hue
            self._sign = -1
        else:
            self._current_hue = self._initial_hue
            self._sign = 1


    def advance_time(self):

        hue = self._current_hue + self._sign*self._color_step
        if self._sign == 1:
            if hue <= self._max_hue:
                self._current_hue = hue
            else:
                self._sign = -1
                self._current_hue = self._current_hue - self._color_step
        else:
            if hue >= self._min_hue:
                self._current_hue = hue
            else:
                self._sign = 1
                self._current_hue = self._current_hue + self._color_step

    @property
    def rgb(self):

        rgb = colorsys.hsv_to_rgb(self._current_hue,self._saturation,self._value)

        return np.array(rgb)

    @property
    def hsv(self):

        return np.array((self._hue,self._saturation,self._value),dtype=np.float)
