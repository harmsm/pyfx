__description__ = \
"""
Convert any non-background image into a ghost (with an optional glowing halo).
"""
import pyfx
from .base import Effect

import numpy as np

from skimage import color

class Ghost(Effect):

    def __init__(self,workspace):

        self._default_waypoint = {"halo_size":10,
                                  "num_apply":5,
                                  "decay_scalar":0.65,
                                  "hue":0.5,
                                  "total_alpha":0.8}

        super().__init__(workspace)

        self._baked = False

    def render(self,img):

        t = self._workspace.current_time

        # Make a black and white version of image, then flip back to RGB
        # with same color on all three channels
        frame_without_proc = self._workspace.get_frame(t)
        ghost = pyfx.util.to_array(frame_without_proc,num_channels=1,
                                   dtype=np.uint8)
        ghost = pyfx.util.to_array(ghost,num_channels=3,dtype=np.float)

        # Change hue to current waypoint color
        ghost = color.rgb2hsv(ghost)
        ghost[:,:,0] = self.hue[t]
        ghost = color.hsv2rgb(ghost)

        # Convert back to an RGBA int array
        ghost = pyfx.util.to_array(ghost,num_channels=4,dtype=np.uint8)

        # Put diff on alpha channel, scaling by total_alpha
        diff = self._workspace.background.frame_diff(img)
        ghost[:,:,3] = pyfx.util.to_array(diff*self.total_alpha[t],
                                          num_channels=1,dtype=np.uint8)

        # Create HSV glow with hue at time t
        glow = np.ones((self._workspace.shape[0],
                        self._workspace.shape[1],3),dtype=np.float)
        glow[:,:,0] = self.hue[t]

        # Convert back to an RGBA array
        glow = color.hsv2rgb(glow)
        glow = pyfx.util.to_array(glow,num_channels=4,dtype=np.uint8)

        # Create a halo alpha channel for the glow
        halo = pyfx.visuals.filters.create_halo(1-diff,
                                                decay_scalar=self.decay_scalar[t],
                                                halo_size=self.halo_size[t])
        halo_alpha = pyfx.util.to_array(halo*self.total_alpha[t],
                                        num_channels=1,dtype=np.uint8)
        glow[:,:,3] = halo_alpha

        # Composite components
        glowing_ghost = pyfx.util.alpha_composite(glow,ghost)

        final = pyfx.util.alpha_composite(img,glowing_ghost)

        # Protect image, if requested
        final = self._protect(img,final)

        return final
