
import pyfx

import pytest

class DummyVideoClip:
    """
    Fake VideoClip class that has a name attribute analogous to VideoClip.
    Used for testing MultiClip.
    """

    def __init__(self,name):

        self.name = name

def test_multiclip():

    mc = pyfx.MultiClip()

    c1 = DummyVideoClip("clip1")
    c2 = DummyVideoClip("clip2")
    c3 = DummyVideoClip("clip3")

    # -------------------------------------------------------------------------
    # Make sure we can add clips
    # -------------------------------------------------------------------------

    mc.add_clip(c1)
    assert len(mc.clips) == 1
    assert mc.clips[0].name == "clip1"

    mc.add_clip(c2,start=10)
    assert len(mc.clips) == 2
    assert mc.clips[1].name == "clip2"

    mc.add_clip(c3,alpha=0.1)
    assert len(mc.clips) == 3
    assert mc.clips[2].name == "clip3"

    # -------------------------------------------------------------------------
    # Make sure the sanity checks on adding clips work
    # -------------------------------------------------------------------------

    with pytest.raises(ValueError):
        mc.add_clip(2)

    # no duplicate
    with pytest.raises(ValueError):
        mc.add_clip(c1)

    # -------------------------------------------------------------------------
    # Make sure sanity checcks on clip names works
    # -------------------------------------------------------------------------

    # make sure that the sanity checker on clip index finder works
    with pytest.raises(ValueError):
        mc.raise_clip("stupid")

    with pytest.raises(IndexError):
        mc.raise_clip(3000)

    # -------------------------------------------------------------------------
    # Test raising clips through layers
    # -------------------------------------------------------------------------

    # Raise the topmost layer (do nothing)
    mc.raise_clip("clip3")
    assert mc.clips[0].name == "clip1"
    assert mc.clips[1].name == "clip2"
    assert mc.clips[2].name == "clip3"

    # Raise the middle layer, indexed by layer number
    mc.raise_clip(1)
    assert mc.clips[0].name == "clip1"
    assert mc.clips[1].name == "clip3"
    assert mc.clips[2].name == "clip2"

    # Raise the bottom layer to the top
    mc.raise_clip("clip1",to_top=True)
    assert mc.clips[0].name == "clip3"
    assert mc.clips[1].name == "clip2"
    assert mc.clips[2].name == "clip1"

    # -------------------------------------------------------------------------
    # Test lowering clips through layers
    # -------------------------------------------------------------------------

    # Lower the bottom layer to the bottom, indexed by layer number
    mc.lower_clip(0)
    assert mc.clips[0].name == "clip3"
    assert mc.clips[1].name == "clip2"
    assert mc.clips[2].name == "clip1"

    # Lower the middle layer to the bottom
    mc.lower_clip("clip2")
    assert mc.clips[0].name == "clip2"
    assert mc.clips[1].name == "clip3"
    assert mc.clips[2].name == "clip1"

    # Lower the top layer to the bottom, index by the layer number
    mc.lower_clip(2,to_bottom=True)
    assert mc.clips[0].name == "clip1"
    assert mc.clips[1].name == "clip2"
    assert mc.clips[2].name == "clip3"

    # -------------------------------------------------------------------------
    # Test directly setting clip layer
    # -------------------------------------------------------------------------

    mc.set_clip_layer(2,0)
    assert mc.clips[0].name == "clip3"
    assert mc.clips[1].name == "clip1"
    assert mc.clips[2].name == "clip2"

    mc.set_clip_layer("clip2",1)
    assert mc.clips[0].name == "clip3"
    assert mc.clips[1].name == "clip2"
    assert mc.clips[2].name == "clip1"

    # -------------------------------------------------------------------------
    # Test alpha setter and getter
    # -------------------------------------------------------------------------

    # Get list of alaphas
    alpha = mc.alphas[:]
    assert alpha[0] == 0.1
    assert alpha[1] == 1.0
    assert alpha[2] == 1.0

    # Set alpha for clip, indexed by name
    mc.set_clip_alpha("clip1",0.5)
    assert mc.alphas[0] == 0.1
    assert mc.alphas[1] == 1.0
    assert mc.alphas[2] == 0.5

    # Get alpha for clip, indexed by layer
    assert mc.get_clip_alpha(2) == 0.5

    # Set bad alpha value
    with pytest.raises(ValueError):
        mc.set_clip_alpha("clip2",20.0)

    # -------------------------------------------------------------------------
    # Test start setter and getter
    # -------------------------------------------------------------------------

    # Get list of starts
    start = mc.starts[:]
    assert start[0] == 0
    assert start[1] == 10
    assert start[2] == 0

    # Set start for clip, indexed by name
    mc.set_clip_start("clip3",2000)
    assert mc.starts[0] == 2000
    assert mc.starts[1] == 10
    assert mc.starts[2] == 0

    # Get start for clip, indexed by layer
    assert mc.get_clip_start(2) == 0

    # Set bad start value
    with pytest.raises(ValueError):
        mc.set_clip_start("clip2","stupid")
