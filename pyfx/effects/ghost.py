__description__ = \
"""
Convert any non-background image into a ghost (with an optional glowing halo).
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-19"

import pyfx
from .base import Effect
import numpy as np
from skimage import color

class Ghost(Effect):
    """
    Create a effect by taking the difference between the current frame and the
    background, adding a glowing halo, and making transparent.

    Waypoint properties:
    halo_size: positive int.  the size of the visual element used to carve out
               the halo.
    num_apply: positive integer. how many times to run the erosition to
               generate a halo.
    decay_scalar: positive float. how much to scale the alpha value for each
                  successive halo erosion.
    hue: float between 0 and 1.
    total_alpha: float between 0 and 1.  how transparent to make the ghost.
    use_base_frame: boolean.  Calculate the ghost using the unprocessed image
                    returned by the workspace.get_frame(t) call, and then paste
                    it onto the input image. If False, calculate the ghost on
                    the input image, and then paste the ghost onto that image.
    """


    def __init__(self,workspace):

        self._default_waypoint = {"halo_size":10,
                                  "num_apply":5,
                                  "decay_scalar":0.65,
                                  "hue":0.5,
                                  "total_alpha":0.9,
                                  "use_base_frame":True}

        super().__init__(workspace)

        self._baked = False

    def render(self,img):

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        # decide whether to use the image piped into render or the unprocessed
        # image from the current workspace time to get the ghost.
        to_proc = img
        if self.use_base_frame[t]:
            to_proc = self._workspace.get_frame(t)

        # Make a black and white version of image
        ghost = pyfx.util.to_array(to_proc,num_channels=1,
                                   dtype=np.uint8)

        # Convert to HSV
        ghost = pyfx.util.to_array(ghost,num_channels=3,dtype=np.float)
        ghost = color.rgb2hsv(ghost)

        # Change hue to current waypoint color
        ghost[:,:,0] = self.hue[t]
        ghost[:,:,1] = 1.0

        # Convert back to an RGBA int array
        ghost = color.hsv2rgb(ghost)
        ghost = pyfx.util.to_array(ghost,num_channels=4,dtype=np.uint8)

        # Put diff on alpha channel, scaling by total_alpha
        diff = self._workspace.background.frame_diff(to_proc)
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
