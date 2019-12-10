

import pyfx
import numpy as np
import pytest

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
