import numpy as np
from skimage import morphology

import colorsys

def create_halo(bw_array,
                halo_size=10,
                num_apply=5,
                decay_scalar=0.65):
    """
    Return mask representing the alpha values for a halo.

    The halo is calculated by taking dark areas in the image and eroding them
    to make them larger.  This is done num_apply times.  Each time this is
    done, the expanded region is multiplied by a scalar and added to the
    output.  The scalar is multipled by decay_scalar after each replicate,
    meaning that pixels added to the region by later erosion steps have
    lower weights than those added later.  This causes the halo to fall off
    in intensity.

    The morphological element controlling the erosion is a disk of
    halo_size.

    The function returns an array with values between 0 and 1, where one is
    the center of the halo (e.g. high alpha) and 0 is past the edge of the halo
    (e.g. low alpha).
    """

    out = np.zeros(bw_array.shape,dtype=np.float)
    array_eroded = np.copy(bw_array)

    # Erode to form halo
    scalar = 1.0
    for i in range(num_apply):
        array_eroded = morphology.erosion(array_eroded,
                                          selem=morphology.disk(halo_size))

        out = out + array_eroded*scalar
        scalar = scalar*decay_scalar

    # Normalize array
    out = 1 - out/np.max(out)

    return out


def ghostify(bw_array,diff_array,hue=0.5,total_alpha=0.8):
    """
    Return a an RGBA array (0-1 format) of a ghost given an single channel input
    and a difference array..
    """

    rgb = colorsys.hsv_to_rgb(hue,1.0,1.0)

    ghost = np.zeros((bw_array.shape[0],bw_array.shape[1],4),dtype=np.float)
    ghost[:,:,0] = ghost_pixels*rgb[0]
    ghost[:,:,1] = ghost_pixels*rgb[1]
    ghost[:,:,2] = ghost_pixels*rgb[2]
    ghost[:,:,3] = diff_array*total_alpha

    return ghost
