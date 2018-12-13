import pyfx
from .base import Effect



class ExposureShift(Effect):
    """
    Apply fluctuating changes in exposure across a collection of video
    frames.

    Waypoint properties:


    """

    def __init__(self,workspace):

        self._default_waypoint = {"hue":None,
                                  "saturation":None,
                                  "value":None}
        super().__init__(workspace)

    def bake(self):

        pass

    def render(self,img):

        return img
