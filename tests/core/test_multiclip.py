
import pyfx
import pytest
import os

def test_multiclip(test_tmp_prefix,tmp_path,video_as_dir,):

    mc = pyfx.MultiClip()

    c1_name = os.path.join(tmp_path,"{}-1.clip".format(test_tmp_prefix))
    c2_name = os.path.join(tmp_path,"{}-2.clip".format(test_tmp_prefix))
    c3_name = os.path.join(tmp_path,"{}-3.clip".format(test_tmp_prefix))

    c1 = pyfx.VideoClip(name=c1_name,src=video_as_dir)
    c2 = pyfx.VideoClip(name=c2_name,src=video_as_dir)
    c3 = pyfx.VideoClip(name=c3_name,src=video_as_dir)

    # -------------------------------------------------------------------------
    # Make sure we can add clips
    # -------------------------------------------------------------------------

    mc.add_clip(c1)
    assert len(mc.clips) == 1
    assert mc.clips[0].name == c1_name

    mc.add_clip(c2,start=10)
    assert len(mc.clips) == 2
    assert mc.clips[1].name == c2_name

    mc.add_clip(c3,alpha=0.1)
    assert len(mc.clips) == 3
    assert mc.clips[2].name == c3_name

    # -------------------------------------------------------------------------
    # Check clip shape
    # -------------------------------------------------------------------------
    assert mc.shape == c1.shape

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
    mc.raise_clip(c3_name)
    assert mc.clips[0].name == c1_name
    assert mc.clips[1].name == c2_name
    assert mc.clips[2].name == c3_name

    # Raise the middle layer, indexed by layer number
    mc.raise_clip(1)
    assert mc.clips[0].name == c1_name
    assert mc.clips[1].name == c3_name
    assert mc.clips[2].name == c2_name

    # Raise the bottom layer to the top
    mc.raise_clip(c1_name,to_top=True)
    assert mc.clips[0].name == c3_name
    assert mc.clips[1].name == c2_name
    assert mc.clips[2].name == c1_name

    # -------------------------------------------------------------------------
    # Test lowering clips through layers
    # -------------------------------------------------------------------------

    # Lower the bottom layer to the bottom, indexed by layer number
    mc.lower_clip(0)
    assert mc.clips[0].name == c3_name
    assert mc.clips[1].name == c2_name
    assert mc.clips[2].name == c1_name

    # Lower the middle layer to the bottom
    mc.lower_clip(c2_name)
    assert mc.clips[0].name == c2_name
    assert mc.clips[1].name == c3_name
    assert mc.clips[2].name == c1_name

    # Lower the top layer to the bottom, index by the layer number
    mc.lower_clip(2,to_bottom=True)
    assert mc.clips[0].name == c1_name
    assert mc.clips[1].name == c2_name
    assert mc.clips[2].name == c3_name

    # -------------------------------------------------------------------------
    # Test directly setting clip layer
    # -------------------------------------------------------------------------

    mc.set_clip_layer(2,0)
    assert mc.clips[0].name == c3_name
    assert mc.clips[1].name == c1_name
    assert mc.clips[2].name == c2_name

    mc.set_clip_layer(c2_name,1)
    assert mc.clips[0].name == c3_name
    assert mc.clips[1].name == c2_name
    assert mc.clips[2].name == c1_name

    # -------------------------------------------------------------------------
    # Test alpha setter and getter
    # -------------------------------------------------------------------------

    # Get list of alaphas
    alpha = mc.alphas[:]
    assert alpha[0] == 0.1
    assert alpha[1] == 1.0
    assert alpha[2] == 1.0

    # Set alpha for clip, indexed by name
    mc.set_clip_alpha(c1_name,0.5)
    assert mc.alphas[0] == 0.1
    assert mc.alphas[1] == 1.0
    assert mc.alphas[2] == 0.5

    # Get alpha for clip, indexed by layer
    assert mc.get_clip_alpha(2) == 0.5

    # Set bad alpha value
    with pytest.raises(ValueError):
        mc.set_clip_alpha(c2_name,20.0)

    # -------------------------------------------------------------------------
    # Test start setter and getter
    # -------------------------------------------------------------------------

    # Get list of starts
    start = mc.starts[:]
    assert start[0] == 0
    assert start[1] == 10
    assert start[2] == 0

    # Set start for clip, indexed by name
    mc.set_clip_start(c3_name,2000)
    assert mc.starts[0] == 2000
    assert mc.starts[1] == 10
    assert mc.starts[2] == 0

    # Get start for clip, indexed by layer
    assert mc.get_clip_start(2) == 0

    # Test shift clip start
    mc.shift_clip_start(0,-100)
    assert mc.starts[0] == 1900

    # Set bad start value
    with pytest.raises(ValueError):
        mc.set_clip_start(c2_name,"stupid")

    # -------------------------------------------------------------------------
    # Get a frame
    # -------------------------------------------------------------------------

    # Test whether this fails.  Going to need to figure out a better, higher
    # level test suite for video renders.  
    frame = mc.get_frame(0)
