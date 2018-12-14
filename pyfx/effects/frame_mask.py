
import pyfx

from .base import Effect

class FrameMask(Effect):
    """
    Apply a mask to a frame.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"masks":[]}

        super().__init__(workspace)

    def render(self,img,t):

        for m in self.masks[t]:
            pyfx.util.alpha_composite(frame,m)
