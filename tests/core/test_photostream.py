
import pyfx
import pytest
import os, glob

def test_photostream(test_tmp_prefix,tmp_path,slideshow_dir):

    slideshow_file = os.path.join(slideshow_dir,"slideshow.csv")
    clip_name = os.path.join(tmp_path,"{}.clip".format(test_tmp_prefix))

    # Test basic ability to load
    ps = pyfx.PhotoStream(name=clip_name,src=slideshow_file)
    assert os.path.isdir(clip_name)
    assert os.path.isfile(os.path.join(clip_name,"master_bg_image.png"))
    assert os.path.isfile(os.path.join(clip_name,"pyfx.json"))

    # Test ability to render
    render_out = os.path.join(tmp_path,"{}-render".format(test_tmp_prefix))
    ps.render(render_out)
    assert os.path.isdir(render_out)
    assert len(glob.glob(os.path.join(render_out,"*.png"))) == 46
