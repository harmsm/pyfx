
import pyfx

import os, shutil, glob

START_DIR = os.getcwd()
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_INPUT_DEMO = "../../demos/video_as_dir"
BG_FILE = "../../demos/background.png"
CLIP_NAME = "test.clip"


def test_virtual_camera():

    os.chdir(THIS_DIR)

    vc = pyfx.VideoClip(CLIP_NAME,DIR_INPUT_DEMO)

    cam = pyfx.effects.VirtualCamera(vc)
    cam.add_waypoint(5,x=100,theta=-3,shaking_magnitude=10)
    cam.bake()

    vc.render("test_render",effects=(cam,))

    #shutil.rmtree("test_render")
    #shutil.rmtree(CLIP_NAME)

    os.chdir(START_DIR)
