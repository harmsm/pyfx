
import pyfx

from .base import Effect

class MixForeAndBack(Effect):
    """
    Mix a foreground and background.  The mix is determined by the mask waypoint
    paramter.  The mask should be a 2D np.uint8 array. Values of 0 will be all
    background, values of 255 will be all foreground. This is typically applied
    as the first effect.
    """

    def __init__(self,workspace):

        self._default_waypoint = {"mask":None}

        super().__init__(workspace)

    def render(self,img,t):

        if self.mask[t] is not None:

            if self.mask[t].shape != (img.shape[0],image.shape[1]) \
               or self.mask.dtype != np.uint8:
                err = "mask must be one channel, with same x/y dimensions as\n"
                err += "image, and be a 0-255 uint array."
                raise ValueError(err)

            bg = np.copy(self._workspace.background.image)
            fg = pyfx.util.to_array(img,num_channels=4,dtype=np.uint8)
            fg[:,:,3] = self.mask[t]*self.alpha[t]

            return pyfx.util.alpha_composite(bg,fg)

        else:

            return img



            pyfx.util.alpha_composite(frame,m)
