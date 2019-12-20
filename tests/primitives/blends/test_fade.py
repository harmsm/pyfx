
import pytest
import pyfx
import numpy as np

def test_fade():

    mask = pyfx.primitives.blends.fade((5,5),5)
    assert mask.shape == (6,5,5)

    assert np.array_equal(mask[0,:],np.zeros((5,5),dtype=np.uint8))
    assert np.array_equal(mask[5,:],255*np.ones((5,5),dtype=np.uint8))
    assert np.array_equal(mask[1,:],51*np.ones((5,5),dtype=np.uint8))
