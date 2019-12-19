
import pyfx
import pytest
import os

def test_photostream(test_tmp_prefix,tmp_path,slideshow_dir):

    slideshow_file = os.path.join(slideshow_dir,"slideshow.csv")
    clip_name = os.path.join(tmp_path,"{}.clip".format(test_tmp_prefix))

    pyfx.PhotoStream(name=clip_name,src=slideshow_file)
