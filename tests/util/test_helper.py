

import pyfx
import numpy as np
import pytest

def test_alpha_composite():
    pass

def test_foreground_mask():
    pass

def test_text_on_image():
    pass

def test_number_frames():
    pass

def test_kelvin_to_rgb():
    pass

def test_channel_stretch():
    pass

def test_adjust_white_balance():
    pass

def test_smooth():
    pass

def test_position_by_string():

    test_array_size = 11

    # Test array check
    test_array = np.zeros((test_array_size))
    with pytest.raises(ValueError):
        pyfx.util.helper.position_by_string(test_array.shape)

    # Test default (middle center)
    test_array = np.zeros((test_array_size,test_array_size))
    r, c = pyfx.util.helper.position_by_string(test_array.shape)
    assert r == test_array_size//2
    assert c == test_array_size//2

    # Test bad entry (middle middle)
    test_array = np.zeros((test_array_size,test_array_size))
    with pytest.raises(ValueError):
        pyfx.util.helper.position_by_string(test_array.shape,"middlemiddle")


    r = ["","top","middle","bottom"]
    r_value = [test_array_size//2,0,test_array_size//2,test_array_size-1]
    y_value = [test_array_size//2,test_array_size-1,test_array_size//2,0]

    c = ["","left","center","right"]
    c_value = [test_array_size//2,0,test_array_size//2,test_array_size-1]
    x_value = [test_array_size//2,0,test_array_size//2,test_array_size-1]

    for i in range(len(r)):
        for j in range(len(c)):
            pos_str = "{}{}".format(r[i],c[j])
            r_out, c_out = pyfx.util.helper.position_by_string(test_array.shape,
                                                               pos_str)
            assert r_out == r_value[i]
            assert c_out == c_value[j]

            x_out, y_out = pyfx.util.helper.position_by_string(test_array.shape,
                                                               pos_str,
                                                               return_xy=True)
            assert x_out == x_value[j]
            assert y_out == y_value[i]

def test_harmonic_langenvin():
    pass
