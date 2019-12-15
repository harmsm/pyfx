
import pyfx

import os, shutil, glob

START_DIR = os.getcwd()
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_INPUT_DEMO = "../../demos/video_as_dir"
BG_FILE = "../../demos/background.png"
CLIP_NAME = "test.clip"

def test_videoclip():

    os.chdir(THIS_DIR)

    vc = pyfx.VideoClip(name=CLIP_NAME,
                        src=DIR_INPUT_DEMO,
                        bg_frame=BG_FILE)
    assert os.path.isdir(CLIP_NAME)
    assert os.path.isfile(os.path.join(CLIP_NAME,"master_bg_image.png"))
    assert os.path.isfile(os.path.join(CLIP_NAME,"pyfx.json"))

    vc.render("test_stream_output")
    assert os.path.isdir("test_stream_output")
    assert len(glob.glob("test_stream_output/*.png")) == len(glob.glob(os.path.join(DIR_INPUT_DEMO,"*.png")))

    shutil.rmtree(CLIP_NAME)
    shutil.rmtree("test_stream_output")

    os.chdir(START_DIR)
