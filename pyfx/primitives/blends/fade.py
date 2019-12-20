
import numpy as np

def fade(shape,num_steps):
    """
    Create a smooth collection of transition masks fading from 0 to 255.
    """

    out_masks = np.zeros((num_steps+1,shape[0],shape[1]),dtype=np.uint8)

    step_size = 1/num_steps
    for i in range(num_steps + 1):
        value = int(round(i*step_size*255,0))
        out_masks[i,:,:] = value

    return out_masks
