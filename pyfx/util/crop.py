__description__ = \
"""
Utility functions for cropping frames.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-10"

import pyfx

import skimage
import numpy as np

def crop(img,x_crop=(0,0),y_crop=(0,0)):
    """
    Crop an image using the values in x_crop and y_crop.  x_crop specify
    the number of pixels to be taken off the left/right and top/bottom
    respectively. x_crop=(100,50) would take 100 pixels off the left and
    50 pixels off the right of the img.

    img: image matrix
    x_crop: tuple of two positive ints; pixels to take off left and right
    y_crop: tuple of two positive ints; pixels to take off top and bottom
    """

    if len(x_crop) != 2:
        err = "x_crop must be a two-value tuple\n"
        raise ValueError(err)

    if len(y_crop) != 2:
        err = "y_crop must be a two-value tuple\n"
        raise ValueError(err)

    if x_crop[0] < 0 or x_crop[1] < 0 or y_crop[0] < 0 or y_crop[1] < 0:
        err = "crop values must be positive integers\n"
        raise ValueError(err)

    x_crop = tuple([int(round(c)) for c in x_crop])
    y_crop = tuple([int(round(c)) for c in y_crop])

    if len(img.shape) == 2:
        crops = (x_crop,y_crop)
    elif len(img.shape) == 3:
        crops = (x_crop,y_crop,(0,0))
    else:
        err = "image matrix must be either 2 or 3 dimensional\n"
        raise ValueError(err)

    return skimage.util.crop(img,crops,copy=True)

def expand(img,x_expand=None,y_expand=None):
    """
    Expand an image by dimensions in x_expand and y_expand. This is
    done by mirroring the appropriate amount of the existing image,
    thus making a seamless transition.  The syntax is basically an inverse
    crop.

    img: img as array
    x_expand: tuple (left, right), where left and right are amount to
              to add to left and right, in pixels
    y_expand: tuple (top, bottom), where top and bottom are the amount
              to add to the top and bottom in pixels"""


    do_x_expansion = True
    if x_expand is None or x_expand == (0,0):
        x_expand = (0,-img.shape[0])
        do_x_expansion = False

    do_y_expansion = True
    if y_expand is None or y_expand == (0,0):
        y_expand = (0,-img.shape[1])
        do_y_expansion = False

    # Don't do anything to image if no expansion actually requested
    if not do_x_expansion and not do_y_expansion:
        return img

    if img.shape[0] < x_expand[0] or img.shape[0] < x_expand[1]:
        err = "cannot expand more than 2x in the x direction\n"
        raise ValueError(err)

    if img.shape[1] < y_expand[0] or img.shape[1] < y_expand[1]:
        err = "cannot expand more than 2x in the y direction\n"
        raise ValueError(err)

    new_dim = [img.shape[0],img.shape[1]]

    if do_x_expansion:
        new_dim[0] = new_dim[0] + x_expand[0] + x_expand[1]

    if do_y_expansion:
        new_dim[1] = new_dim[1] + y_expand[0] + y_expand[1]

    if len(img.shape) > 2:
        out_array = np.zeros((new_dim[0],new_dim[1],img.shape[2]),dtype=img.dtype)
    else:
        out_array = np.zeros((new_dim[0],new_dim[1]),dtype=img.dtype)

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
        top_left = pyfx.util.convert.alpha_composite(top_left_a,top_left_b)
        out_array[:x_expand[0],  :y_expand[0],:] = top_left

        top_right_a = right_slice[:,:y_expand[0]]
        top_right_a = np.flip(top_right_a,1)
        top_right_b =  top_slice[-x_expand[1]:,:]
        top_right_b = np.flip(top_right_b,0)
        top_right = pyfx.util.convert.alpha_composite(top_right_a,top_right_b)
        out_array[-x_expand[1]:, :y_expand[0],:] = top_right

        bottom_left_a = left_slice[:,-y_expand[1]:]
        bottom_left_a = np.flip(bottom_left_a,1)
        bottom_left_b =  bottom_slice[:x_expand[0],:]
        bottom_left_b = np.flip(bottom_left_b,0)
        bottom_left = pyfx.util.convert.alpha_composite(bottom_left_a,bottom_left_b)
        out_array[:x_expand[0], -y_expand[1]:,:] = bottom_left

        bottom_right_a = right_slice[:,-y_expand[1]:]
        bottom_right_a = np.flip(bottom_right_a,1)
        bottom_right_b =  bottom_slice[-x_expand[1]:,:]
        bottom_right_b = np.flip(bottom_right_b,0)
        bottom_right = pyfx.util.convert.alpha_composite(bottom_right_a,bottom_right_b)
        out_array[-x_expand[1]:,-y_expand[1]:,:] = bottom_right

    return out_array

def find_pan_crop(x,y,width,height):
    """
    Find crop that, when applied to a frame shifted by the maximum pans in
    x and y, is still in the original bounds given by width and height.

    returns: crop tuple for x, crop tuple for y, new width, new height
    """

    # Find maximum displacement in x
    min_x = np.min(x)
    if min_x > 0: min_x = 0
    max_x = np.max(x)
    if max_x < 0: max_x = 0

    max_shift_in_x = np.abs(min_x) + max_x
    proportional_shift_in_x = max_shift_in_x/width

    # Find maximum displacement in y
    min_y = np.min(y)
    if min_y > 0: min_y = 0
    max_y = np.max(y)
    if max_y < 0: max_y = 0

    max_shift_in_y = np.abs(min_y) + max_y
    proportional_shift_in_y = max_shift_in_y/height

    # Figure out whether to scale to x or y, depending on which has the
    # larger proportional shift in magnitude
    if proportional_shift_in_x >= proportional_shift_in_y:
        fx = proportional_shift_in_x
    else:
        fx = proportional_shift_in_y

    # Figure out x-cropping

    # Total number of pixels in x-crop
    x_crop_pix = int(round(fx*width))

    # Find fraction of pixels to place to the right of the crop.  If there
    # is no crop in this axis, place half of pixels to left and half to
    # the right.
    if max_shift_in_x == 0:
        x_fx_right = 0.5
    else:
        x_fx_right = max_x/max_shift_in_x

    # Define crops.  Add an offset so the two sides add to the right number
    # even in case of rounding error.
    x_right_pix = int(round(x_crop_pix*x_fx_right))
    x_left_pix = int(round(x_crop_pix*(1 - x_fx_right)))
    x_offset = x_crop_pix - (x_right_pix + x_left_pix)
    x_left_pix += x_offset

    crop_x = (x_left_pix, x_right_pix)

    # Figure out y-cropping

    # Total number of pixels in y-crop
    y_crop_pix = int(round(fx*height))

    # Find fraction of pixels to place to the top of the crop.  If there
    # is no crop in this axis, place half of pixels to top and half to
    # the bottom.
    if max_shift_in_y == 0:
        y_fx_top = 0.5
    else:
        y_fx_top = max_y/max_shift_in_y

    # Define crops.  Add an offset so the two sides add to the bottom number
    # even in case of rounding error.
    y_top_pix = int(round(y_crop_pix*y_fx_top))
    y_bottom_pix = int(round(y_crop_pix*(1 - y_fx_top)))
    y_offset = y_crop_pix - (y_top_pix + y_bottom_pix)
    y_bottom_pix += y_offset

    crop_y = (y_bottom_pix, y_top_pix)

    new_width = width - x_crop_pix
    new_height = height - y_crop_pix

    return crop_x, crop_y, new_width, new_height

def find_rotate_crop(theta,width,height):
    """
    Find crop that, when applied to a rotated frame with a maximum rotation
    of theta, is still in the original bounds given by width and height.

    returns: crop tuple for x, crop tuple for y, new width, new height
    """

    # Find largest rotation that we are going to have to do
    theta_max = np.max(np.abs(theta))

    # Find height and width of box rotated in and bounded by the current
    # height and width
    h_prime = width*height/(height*np.sin(theta_max) + width)
    w_prime = width*h_prime/height

    # Figure out cropping
    del_x = int(round(width - w_prime,0))
    del_y = int(round(height - h_prime,0))

    if del_x % 2 != 0:
        del_x += 1
    crop_x = (del_x/2,del_x/2)

    if del_y % 2 != 0:
        del_y += 1
    crop_y = (del_y/2,del_y/2)

    return crop_x, crop_y, width - del_x, height - del_y

def find_zoom_crop(magnitude,width,height):
    """
    Find crop that, when applied to a rotated frame with a minimal zooming in,
    is still in the original bounds given by width and height.

    returns: crop tuple for x, crop tuple for y, new width, new height
    """

    mag = np.min(magnitude)

    if mag < 1.0:
        err = "this function can only be used for zooming in, not out.\n"
        raise ValueError(err)

    del_x = int(round(width*(1 - 1/mag),0))
    if del_x % 2 != 0:
        del_x += 1
    crop_x = (del_x/2,del_x/2)

    del_y = int(round(height*(1 - 1/mag),0))
    if del_y % 2 != 0:
        del_y += 1
    crop_y = (del_y/2,del_y/2)

    return crop_x, crop_y, width - del_x, height - del_y
