

import pyfx
import numpy as np
import pytest

def test_to_array():

    # pass bad dtype
    # pass bad channels
    # test image to array

    in_dtypes = [np.int,np.float,str,"PIL"]
    out_dtype = [np.uint8,np.float]
    num_channels = [1,3,4]

    # OUTPUT VERSIONS
    # for dtype_in in in_dtypes:
        # for dtype_out in out_dtypes:
            # for channel_in in num_channels:
                # for channel_out in num_channels:
                    # conver



    pass

def test_to_image():
    pass

def test_to_file():
    pass

def test_rc_to_xy():

    shape = (10,10)
    out = pyfx.util.convert.rc_to_xy((0,0),shape)
    assert out[0] == 0
    assert out[1] == 9

    out = pyfx.util.convert.rc_to_xy((9,9),shape)
    assert out[0] == 9
    assert out[1] == 0

    out = pyfx.util.convert.rc_to_xy((5,2),shape)
    assert out[0] == 2
    assert out[1] == 4

def test_xy_to_rc():

    shape = (10,10)
    out = pyfx.util.convert.xy_to_rc((0,0),shape)
    assert out[0] == 9
    assert out[1] == 0

    out = pyfx.util.convert.xy_to_rc((9,9),shape)
    assert out[0] == 0
    assert out[1] == 9

    out = pyfx.util.convert.xy_to_rc((5,2),shape)
    assert out[0] == 7
    assert out[1] == 5
