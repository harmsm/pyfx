
import pyfx
import os

def test_virtual_camera(test_tmp_prefix,tmp_path,video_as_dir):

    vc = pyfx.VideoClip(name="clip",src=video_as_dir)

    cam = pyfx.effects.VirtualCamera(vc)
    cam.add_waypoint(5,x=100,theta=-3,shaking_magnitude=10)
    cam.bake()

    vc.render(os.path.join(tmp_path,test_tmp_prefix),effects=(cam,))

