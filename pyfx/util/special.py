__description__ = \
"""
"""

from . import util

import numpy as np
from PIL import Image

def alpha_composite(bottom,top,return_matrix_as_pil=False):
    """
    Place image "top" over image "bottom" using alpha compositing.  If
    return_matrix_as_pil is True, return as a PIL.Image instance.
    """

    # Convert "a" to a PIL Image (if necessary)
    if type(bottom) == Image.Image:
        bottom_img = bottom
        return_as_image = True
    else:
        bottom_img = util.array_to_image(bottom)
        return_as_image = return_matrix_as_pil

    # Convert "b" to a PIL Image (if necessary)
    if type(top) == Image.Image:
        top_img = top
    else:
        top_img = util.array_to_image(top)

    # Sanity checks
    if top_img.mode != 'RGBA' or bottom_img.mode != 'RGBA':
        err = "top and bottom must have alpha channels for compositing\n"
        raise ValueError(err)

    if top_img.size != bottom_img.size:
        err = "top and bottom must have the same shape\n"
        raise ValueError(err)

    # Do compositing
    composite = Image.alpha_composite(bottom_img,top_img)

    # Return as an Image instance
    if return_as_image:
        return composite

    # Return as a 0-255 array
    if bottom.dtype in util.INT_TYPES:
        return np.array(composite,dtype=bottom.dtype)

    # Return as a 0-1 array
    return np.array(np.array(composite)/255,dtype=bottom.dtype)
