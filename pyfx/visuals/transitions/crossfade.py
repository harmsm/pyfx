
import numpy as np

from .base import Transition

class CrossFade(Transition):

    def _create_masks(self,trans_mask,**kwargs):

        step_size = 1/(trans_mask.shape[2] - 1)
        for i in range(trans_mask.shape[2]):
            value = int(round(i*step_size*255,0))
            trans_mask[:,:,i] = value

        return trans_mask
