
import colorsys
import numpy as np

def ghostify(bw_array,diff_array,hue=0.5,total_alpha=0.8):
    """
    Return a an rgba (0-1 format) array of a ghost.
    """

    rgb = colorsys.hsv_to_rgb(hue,1.0,1.0)

    ghost = np.zeros((bw_array.shape[0],bw_array.shape[1],4),dtype=np.float)
    ghost[:,:,0] = ghost_pixels*rgb[0]
    ghost[:,:,1] = ghost_pixels*rgb[1]
    ghost[:,:,2] = ghost_pixels*rgb[2]
    ghost[:,:,3] = (1 - diff_array)*total_alpha

    return ghost
