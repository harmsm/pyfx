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


def expand(img,x_expand=None,y_expand=None):
    """
    Expand an image by dimensions in x_expand and y_expand. This is
    done by mirroring the appropriate amount of the existing image,
    thus making a seamless transition.

    img: img as array
    x_expand: tuple (left, right), where left and right are amount to
              to add to left and right, in pixels
    y_expand: tuple (top, bottom), where top and bottom are the amount
              to add to the top and bottom in pixels"""

    # Convert image to a float image
    if img.dtype in util.INT_TYPES:
        img = util.int_to_float(img)

    do_x_expansion = True
    if x_expand is None:
        x_expand = (0,1)
        do_x_expansion = False

    do_y_expansion = True
    if y_expand is None:
        y_expand = (0,1)
        do_y_expansion = False

    if img.shape[0] < x_expand[0] or img.shape[0] < x_expand[1]:
        err = "cannot expand more than 2x in the x direction\n"
        raise ValueError(err)

    if img.shape[1] < y_expand[0] or img.shape[1] < y_expand[1]:
        err = "cannot expand more than 2x in the y direction\n"
        raise ValueError(err)

    new_dim = [img.shape[0],img.shape[1]]
    new_dim[0] = new_dim[0] + x_expand[0] + x_expand[1]
    new_dim[1] = new_dim[1] + y_expand[0] + y_expand[1]

    if len(img.shape) > 2:
        out_array = np.zeros((new_dim[0],new_dim[1],img.shape[2]),dtype=np.float)
    else:
        out_array = np.zeros((new_dim[0],new_dim[1]),dtype=np.float)

    out_array[x_expand[0]:-x_expand[1],y_expand[0]:-y_expand[1]] = img[:,:]

    # Build strips on left and right
    if do_x_expansion:
        left_slice = img[:x_expand[0],:]
        left_slice = np.flip(left_slice,0)
        out_array[:x_expand[0] ,y_expand[0]:-y_expand[1]] = left_slice

        right_slice = img[-x_expand[1]:,:]
        right_slice = np.flip(right_slice,0)
        out_array[-x_expand[1]:,y_expand[0]:-y_expand[1]] = right_slice

    # Build strips on top and bottom
    if do_y_expansion:
        top_slice = img[:,:y_expand[0]]
        top_slice = np.flip(top_slice,1)
        out_array[x_expand[0]:-x_expand[1],:y_expand[0]] = top_slice

        bottom_slice = img[:,-y_expand[1]:]
        bottom_slice = np.flip(bottom_slice,1)
        out_array[x_expand[0]:-x_expand[1],-y_expand[1]:] = bottom_slice

    # If we built strips on top and bottom and left and right, fill in corners
    if do_x_expansion and do_y_expansion:

        top_left_a = left_slice[:,:y_expand[0]]
        top_left_a = np.flip(top_left_a,1)
        top_left_b =  top_slice[:x_expand[0],:]
        top_left_b = np.flip(top_left_b,0)
        top_left = alpha_composite(top_left_a,top_left_b)
        out_array[:x_expand[0],  :y_expand[0],:] = top_left

        top_right_a = right_slice[:,:y_expand[0]]
        top_right_a = np.flip(top_right_a,1)
        top_right_b =  top_slice[-x_expand[1]:,:]
        top_right_b = np.flip(top_right_b,0)
        top_right = alpha_composite(top_right_a,top_right_b)
        out_array[-x_expand[1]:, :y_expand[0],:] = top_right

        bottom_left_a = left_slice[:,-y_expand[1]:]
        bottom_left_a = np.flip(bottom_left_a,1)
        bottom_left_b =  bottom_slice[:x_expand[0],:]
        bottom_left_b = np.flip(bottom_left_b,0)
        bottom_left = alpha_composite(bottom_left_a,bottom_left_b)
        out_array[:x_expand[0], -y_expand[1]:,:] = bottom_left

        bottom_right_a = right_slice[:,-y_expand[1]:]
        bottom_right_a = np.flip(bottom_right_a,1)
        bottom_right_b =  bottom_slice[-x_expand[1]:,:]
        bottom_right_b = np.flip(bottom_right_b,0)
        bottom_right = alpha_composite(bottom_right_a,bottom_right_b)
        out_array[-x_expand[1]:,-y_expand[1]:,:] = bottom_right

    return util.float_to_int(out_array)
