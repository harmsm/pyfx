__description__ = \
"""
Utility functions for converting between data types, doing sanity checking
along the way.

Enforces these rules:
    1. Images can only be 1, 3, or 4 channel
    2. Float arrays must have values between 0 and 1
    3. Integer arrays must have values between 0 and 255

If an alpha channel is generated, it will be filled with a value of 1.0 (float)
or 255 (integer).
"""

import numpy as np
from PIL import Image
from skimage import color

INT_TYPES = (np.int,np.intc,np.intp,np.int8,np.int16,np.int32,np.int64,
             np.uint8,np.uint16,np.uint32,np.uint64)

FLOAT_TYPES = (np.float,np.float16,np.float32,np.float64)

def array_to_image(a):
    """
    Convert an array to an RGBA PIL.Image.
    """

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

def image_to_array(img,dtype=np.uint8,num_channels=4):
    """
    Convert a PIL.Image instance to an array (in a defined way).
    """

    # sanity check
    if num_channels not in (1,3,4):
        err = "number of channels must be 1, 3, or 4\n"
        raise ValueError(err)

    # convert to an array
    a = np.array(img,dtype=dtype)

    # If non integer type, place on 0-1 scale
    max_possible_value = 255
    if a.dtype not in INT_TYPES:
        if a.dtype != np.bool:
            max_possible_value = 1.0
            a = a/255

    out = np.zeros((a.shape[0],a.shape[1],num_channels),dtype=dtype)

    # 1 input channel
    if len(a.shape) == 2:

        # ... to 1 output channel
        if num_channels == 1:
            out = a

        # ... to 3 or 4 output channels
        else:
            out[:,:,:3] = a[:,:3]
            if num_channels == 4:
                out[:,:,3] = max_possible_value

    # 3 or 4 input channels (or 1 channel loaded into a 3rd array dimension)
    elif len(a.shape) == 3:

        # ... to 1 output channel
        if num_channels == 1:
            bw = color.rgb2gray(a)
            if dtype in INT_TYPES:
                out = np.array(np.round(bw*255,0),dtype=dtype)
            else:
                out = np.array(bw,dtype=dtype)

        # ... to 3 output channels
        elif num_channels == 3:

            # 1 to 3
            if a.shape[2] == 1:
                out[:,:,0] = a[:,:,0]
                out[:,:,1] = a[:,:,0]
                out[:,:,2] = a[:,:,0]

            # 3 to 3
            elif a.shape[2] == 3:
                out = a

            # 4 to 3
            elif a.shape[2] == 4:
                out[:,:,:3] = a[:,:,:3]
            else:
                err = "matrix must have 1,3 or 4 many channels\n"
                raise ValueError(err)

        # ... to 4 output channels
        elif num_channels == 4:

            # 1 to 4
            if a.shape[2] == 1:
                out[:,:,0] = a[:,:,0]
                out[:,:,1] = a[:,:,0]
                out[:,:,2] = a[:,:,0]
                out[:,:,3] = max_possible_value

            # 3 to 4
            if a.shape[2] == 3:
                out[:,:,:3] = a[:,:,:3]
                out[:,:,3] = max_possible_value

            # 4 to 4
            elif a.shape[2] == 4:
                out = a
            else:
                err = "matrix must have 1,3 or 4 many channels\n"
                raise ValueError(err)

    return out

def float_to_int(a,out_dtype=np.uint8):
    """
    Convert a float array to an integer array.
    """

    if np.min(a) < 0 or np.max(a) > 1:
        err = "float array must have values between 0 and 1\n"
        raise ValueError(err)

    if out_dtype not in INT_TYPES:
        err = "out_dtype {} is not an integer type\n".format(out_dtype)
        raise ValueError(err)

    out = np.array(np.round(a*255,0),dtype=out_dtype)

    return out


def int_to_float(a,dtype=np.float):
    """
    Convert an integer array to a float array.
    """

    if np.min(a) < 0 or np.max(a) > 255:
        err = "int array must have values between 0 and 255\n"
        raise ValueError(err)

    if out_dtype not in FLOAT_TYPES:
        err = "out_dtype {} is not an float type\n".format(out_dtype)
        raise ValueError(err)

    out = np.array(a/255,dtype=out_dtype)

    return out


def load_image_file(image_file,dtype=np.uint8,num_channels=4,return_array=True):
    """
    Load an image file.

    image_file: some sort of image file.
    dtype: output data type
    num_channels: number of output channels
    return_array: return an array (True) or PIL Image class (False)
    """


    img = Image.open(image_file)

    if return_array:
        return image_to_array(img,dtype=dtype,num_channels=num_channels)

    return img


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
        bottom_img = array_to_image(bottom)
        return_as_image = return_matrix_as_pil

    # Convert "b" to a PIL Image (if necessary)
    if type(top) == Image.Image:
        top_img = top
    else:
        top_img = array_to_image(top)

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
