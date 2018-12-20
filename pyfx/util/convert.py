__description__ = \
"""
Utility functions for converting between data types, doing sanity checking
along the way.

Enforces these rules:
    1. Images can only be 1, 3, or 4 channel
    2. Float arrays must have values between 0 and 1
    3. Integer arrays must have values between 0 and 255

When lowering the number of channels, the RGB channels are mixed to yield a
single channel.  When increasing the number of channels, the single channel
is copied to all three channels.

If an alpha channel is lost (say in a 4->3 channel conversion), it is discarded.
If an alpha channel is generated (say in a 3->4 channel conversion), it will be
filled with a value of 1.0 (float) or 255 (integer).

When possible, objects are not modified, but returned.  (For example, trying to
convert a 3 channel int array to another 3 channel int array will simply return
the input ndarray object.  This means the user can call to_array() willy-nilly
to make sure they have the right data type for an operation, without having
a ton of numpy operations added to their call.
"""

import numpy as np
from PIL import Image
from skimage import color

import re

PIL_PATTERN = re.compile("PIL\.")

INT_TYPES = (np.int,np.intc,np.intp,np.int8,np.int16,np.int32,np.int64,
             np.uint8,np.uint16,np.uint32,np.uint64)

FLOAT_TYPES = (np.float,np.float16,np.float32,np.float64)


def to_array(img,dtype=np.uint8,num_channels=4,copy=False):
    """
    Convert a file, array, or PIL image to an array with the specificed
    number of channels and data type.

    img: string with file, numpy.ndarray, or PIL.Image instance.
    dtype: must be some form of numpy int or float.
    num_channels: number of output channels (1,3, or 4).
    copy: whether or not to require the array to be copied. (If False and the
          array is already in the right format, just send the object back
          without doing anything to it)
    """

    # Make sure output specs are sane
    if dtype not in FLOAT_TYPES and dtype not in INT_TYPES:
        err = "dtype must be some form of numpy integer or float.\n"
        raise ValueError(err)

    if num_channels not in [1,3,4]:
        err = "num_channels must be 1,3, or 4.\n"
        raise ValueError(err)

    # Read from a file
    if type(img) is str:
        out = _from_file(img,dtype=dtype,num_channels=num_channels)

    # Convert between array types
    elif type(img) is np.ndarray:

        # Don't do a conversion if this is already an ndarray with the correct
        # dimensions and data type
        if img.dtype == dtype:
            if num_channels == 1:
                if len(img.shape) == 2:
                    if copy: img = np.copy(img)
                    return img
            else:
                if len(img.shape) == 3 and img.shape[2] == num_channels:
                    if copy: img = np.copy(img)
                    return img

        # If we get here, we're going to need to convert the array to a
        # different type.
        if img.dtype in INT_TYPES:
            if dtype in FLOAT_TYPES:
                out = _int_to_float(img,dtype=dtype)
            else:
                out = np.array(img,dtype=dtype)
        else:
            out = _float_to_int(img,dtype=dtype)

        out = _convert_channels(out,dtype,num_channels)

    # Try to treat as a PIL Image
    elif PIL_PATTERN.search(str(type(img))):
        out = _image_to_array(img,dtype=dtype,num_channels=num_channels)

    else:
        err = "image type not recognized.\n"
        raise ValueError(err)

    return out

def to_image(img):
    """
    Convert to a PIL.Image.

    img: string with file, numpy.ndarray, or PIL.Image instance.
    """

    # Read from file
    if type(img) is str:
        return _from_file(img,return_array=False)

    # See if it's an array
    elif type(img) is np.ndarray:
        return _array_to_image(img)

    # If it's aready a PIL image, return that.
    elif PIL_PATTERN.search(str(type(img))):
        return img

    else:
        err = "image type not recognized.\n"
        raise ValueError(err)

def to_file(image,image_file):
    """
    Write an image to a file.

    image: numpy.ndarray, or PIL.Image instance.
    image_file: output file
    """

    if type(image) is np.ndarray:
        image = _array_to_image(image)

    elif PIL_PATTERN.search(str(type(image))):
        image = image

    else:
        err = "image type not recognized.\n"
        raise ValueError(err)

    image.save(image_file)


def alpha_composite(bottom,top,return_as_pil=False):
    """
    Place image "top" over image "bottom" using alpha compositing.  If
    return_as_pil, return as a PIL.Image instance.  Otherwise, return a
    0-255, 4-channel array.
    """

    bottom_img = to_image(bottom)
    top_img = to_image(top)

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
    if return_as_pil:
        return composite

    # Return as array
    return to_array(composite,dtype=np.uint8,num_channels=4)


def _array_to_image(a):
    """
    Convert an array to an RGBA PIL.Image.
    """

    if type(a) is not np.ndarray:
        err = "input is not an array\n"
        raise ValueError(err)

    an_array = to_array(a,num_channels=4,dtype=np.uint8)
    return Image.fromarray(an_array)


def _image_to_array(img,dtype=np.uint8,num_channels=4):
    """
    Convert a PIL.Image instance to an array (in a defined way).
    """

    # convert to an array
    a = np.array(img,dtype=dtype)

    # If non integer type, place on 0-1 scale
    max_possible_value = 255
    if a.dtype not in INT_TYPES:
        if a.dtype != np.bool:
            max_possible_value = 1.0
            a = a/255

    out = _convert_channels(a,dtype,num_channels)

    return out

def _convert_channels(a,dtype=np.uint8,num_channels=4):
    """
    Convert an array "a" to whatever num_channels is requested. An RGB array
    going to a single channel is mixed using skimage.color.rgb2gray.  For a
    single channel, the alpha channel is discarded.  Going from a single
    channel to a 3 or 4 channel, the single channel is duplicated across
    the RGB channels.  The maximum value for the array type is assigned to the
    new alpha channel.  Integers are forced to be 0-255.
    """

    # Figure out what the maximum possible value of an entry is if we have to
    # construct a new channel
    max_possible_value = 255
    if dtype not in INT_TYPES:
        max_possible_value = 1.0

    # sanity check
    if type(a) is not np.ndarray:
        err = "input is not a numpy array\n"
        raise ValueError(err)

    if num_channels not in (1,3,4):
        err = "number of channels must be 1, 3, or 4\n"
        raise ValueError(err)

    if num_channels == 1:
        out = np.zeros((a.shape[0],a.shape[1]),dtype=a.dtype)
    else:
        out = np.zeros((a.shape[0],a.shape[1],num_channels),dtype=a.dtype)

    # 1 input channel
    if len(a.shape) == 2:

        # ... to 1 output channel (no change --> return same object)
        if num_channels == 1:
            out = a

        # ... to 3 or 4 output channels
        else:
            out[:,:,0] = a[:,:]
            out[:,:,1] = a[:,:]
            out[:,:,2] = a[:,:]
            if num_channels == 4:
                out[:,:,3] = max_possible_value

    # 1, 2, 3 or 4 input channels (or 1 channel loaded into a 3rd array dimension)
    elif len(a.shape) == 3:

        # ... to 1 output channel
        if num_channels == 1:

            # 1 or 2 channels
            if a.shape[2] == 1 or a.shape[2] == 2:
                out[:,:] = a[:,:,0]

            # 3 or 4 channels
            elif a.shape[2] == 3 or a.shape[2] == 4:

                bw = color.rgb2gray(a)
                if dtype in INT_TYPES:
                    out = np.round(bw*255,0)
                    out[out > 255] = 255
                    out[out < 0] = 0
                    out = np.array(out,dtype=dtype)
                else:
                    out = np.array(bw,dtype=dtype)

            else:
                err = "input array must have 1,2,3, or 4 channels.\n"
                raise ValueError(err)

        # ... to 3 output channels
        elif num_channels == 3:

            # 1 to 3 or 2 to 3 (drop input alpha channel for 2 to 3)
            if a.shape[2] == 1 or a.shape[2] == 2:
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
                err = "matrix must have 1,2,3 or 4 channels\n"
                raise ValueError(err)

        # ... to 4 output channels
        elif num_channels == 4:

            # 1 to 4
            if a.shape[2] == 1:
                out[:,:,0] = a[:,:,0]
                out[:,:,1] = a[:,:,0]
                out[:,:,2] = a[:,:,0]
                out[:,:,3] = max_possible_value

            # 2 to 4  (treat second channel as alpha)
            elif a.shape[2] == 2:
                out[:,:,0] = a[:,:,0]
                out[:,:,1] = a[:,:,0]
                out[:,:,2] = a[:,:,0]
                out[:,:,3] = a[:,:,1]

            # 3 to 4
            elif a.shape[2] == 3:
                out[:,:,:3] = a[:,:,:3]
                out[:,:,3] = max_possible_value

            # 4 to 4
            elif a.shape[2] == 4:
                out = a
            else:
                err = "matrix must have 1,2,3 or 4 channels\n"
                raise ValueError(err)

    return out

def _float_to_int(a,dtype=np.uint8,zero_tolerance=1e-6):
    """
    Convert a float array to an integer array.
    """

    if dtype not in INT_TYPES:
        err = "dtype {} is not an integer type\n".format(dtype)
        raise ValueError(err)

    # Start with pointer to "a"
    b = a

    # Check min/max bounds
    if np.min(b) < 0 or np.max(b) > 1:

        # We're about to modify array; make a copy
        b = np.copy(a)

        # Filter out values that are just below zero or just above 1.
        low_cut = np.logical_and(a < 0,np.abs(a) < zero_tolerance)
        high_cut = np.logical_and(a > 1,(a - 1) < zero_tolerance)

        b[low_cut] = 0.0
        b[high_cut] = 1.0

        # If we're still outside bounds, throw error
        if np.min(b) < 0 or np.max(b) > 1:
            err = "float array must have values between 0 and 1\n"
            err += "array min: {}, array max: {}\n".format(np.min(b),np.max(b))
            raise ValueError(err)

    out = np.array(np.round(b*255,0),dtype=dtype)
    out[out > 255] = 255
    out[out < 0]   = 0

    return out


def _int_to_float(a,dtype=np.float):
    """
    Convert an integer array to a float array.
    """

    if dtype not in FLOAT_TYPES:
        err = "dtype {} is not an float type\n".format(dtype)
        raise ValueError(err)

    # Start with pointer to "a"
    b = a

    # Check min/max bounds
    if np.min(b) < 0 or np.max(b) > 255:

        # Truncate values of -1 and 256 --> maybe reached by a rounding
        # error elsewhere.
        b = np.copy(a)
        b[a == -1] = 0
        b[a == 256] = 255

        # If that still didn't fix it, throw an error
        if np.min(b) < 0 or np.max(b) > 255:
            err = "int array must have values between 0 and 255\n"
            err += "array min: {}, array max: {}\n".format(np.min(b),np.max(b))
            raise ValueError(err)

    out = np.array(b/255,dtype=dtype)
    out[out < 0] = 0.0
    out[out > 1] = 1.0

    return out


def _from_file(image_file,dtype=np.uint8,num_channels=4,return_array=True):
    """
    Load an image file.

    image_file: some sort of image file.
    dtype: output data type
    num_channels: number of output channels
    return_array: return an array (True) or PIL Image class (False)
    """

    img = Image.open(image_file)

    if return_array:
        return _image_to_array(img,dtype=dtype,num_channels=num_channels)

    return img
