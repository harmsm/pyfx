
import pytest
import pyfx

import numpy as np

def test_wipe():

    # Test sanity checking
    with pytest.raises(ValueError):
        out = pyfx.visuals.blends.wipe((5,5),start=[5,4],end=[0,4],num_steps=4)

    # Test a wipe from the top left to the bottom right
    out = pyfx.visuals.blends.wipe((5,5),start=[0,0],end=[4,4],num_steps=3,feather=0)

    # output shape is right
    assert out.shape == (4,5,5)

    # First frame is all 0
    assert np.sum(out[0,:,:] == np.zeros((5,5),dtype=np.uint8))== 25

    # Next frame has corner with 255
    test_array = np.zeros((5,5),dtype=np.uint8)
    for i in range(3):
        test_array[:(3-i),i] = 255
    assert np.sum(out[1,:,:] == test_array) == 25

    # Next frame has other corner with 0
    test_array = 255*np.ones((5,5),dtype=np.uint8)
    for i in range(3):
        test_array[(i+2):,(4-i):] = 0
    assert np.sum(out[2,:,:] == test_array) == 25

    # Final frame is all 255
    assert np.sum(out[3,:,:] == 255*np.ones((5,5),dtype=np.uint8)) == 25
