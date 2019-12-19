
import pyfx

import os, glob

def test_videoclip(test_tmp_prefix,tmp_path,video_as_dir,background):

    clip_name = os.path.join(tmp_path,"{}.clip".format(test_tmp_prefix))

    vc = pyfx.VideoClip(name=clip_name,
                        src=video_as_dir,
                        bg_frame=background)
    assert os.path.isdir(clip_name)
    assert os.path.isfile(os.path.join(clip_name,"master_bg_image.png"))
    assert os.path.isfile(os.path.join(clip_name,"pyfx.json"))

    render_out = os.path.join(tmp_path,"{}-render".format(test_tmp_prefix))

    vc.render(render_out)
    assert os.path.isdir(render_out)
    assert len(glob.glob(os.path.join(render_out,"*.png"))) == len(glob.glob(os.path.join(video_as_dir,"*.png")))
