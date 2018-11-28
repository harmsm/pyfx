
import numpy as np
from PIL import Image

INT_TYPES = (np.int8,np.int16,np.int32,np.int64,np.uint8,np.uint16,np.uint32,np.uint64)

def matrix_to_image(a):

    if len(a.shape) == 2:
        duplicate_channels = True
        fake_alpha = True

    elif len(a.shape) == 3:
        if a.shape[2] in (0,1):
            duplicate_channels = True
            fake_alpha = True
        elif a.shape[2] == 3:
            duplicate_channels = False
            fake_alpha = True
        elif a.shape[2] == 4:
            duplicate_channels = False
            fake_alpha = False
        else:
            err = "the 3rd array dimension must be 4 or less\n"
            raise ValueError(err)

    else:
        err = "array must be 2D or 3D\n"
        raise ValueError(err)

    if a.dtype in INT_TYPES:
        if np.min(a) < 0 or np.max(a) > 255:
            err = "integer arrays must have values between 0 and 255\n"
            raise ValueError(err)
        else:
            a_tmp = a
    else:
        if np.min(a) < 0 or np.max(a) > 1:
            err = "non-integer arrays must have values between 0 and 1\n"
            raise ValueError(err)
        else:
            a_tmp = 255*a

    # convert array to three-channel color plus alpha
    a_array = np.zeros((a.shape[0],a.shape[1],4),np.uint8)
    if duplicate_channels:
        a_array[:,:,0] = a_tmp
        a_array[:,:,1] = a_tmp
        a_array[:,:,2] = a_tmp
    else:
        a_array[:,:,:3] = a_tmp[:,:,:3]

    if fake_alpha:
        a_array[:,:,3] = 255
    else:
        a_array[:,:,3] = a_tmp[:,:,3]

    a_img = Image.fromarray(a_array)

    return a_img


def alpha_composite(bottom,top,return_matrix_as_pil=False):
    """
    Place image "top" over image "bottom" using alpha compositing.
    """

    # Convert "a" to a PIL Image (if necessary)
    if type(a) == Image.Image:
        bottom_img = bottom
        return_as_image = True
    else:
        bottom_img = matrix_to_image(bottom)
        return_as_image = return_matrix_as_pil

    # Convert "b" to a PIL Image (if necessary)
    if type(top) == Image.Image:
        top_img = top
    else:
        top_img = matrix_to_image(top)

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
    if bottom.dtype in INT_TYPES:
        return np.array(composite,dtype=bottom.dtype)

    # Return as a 0-1 array
    return np.array(np.array(composite)/255,dtype=bottom.dtype)
