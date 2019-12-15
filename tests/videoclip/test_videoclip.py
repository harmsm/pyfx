
import pyfx

def test_videoclip():

    vc = pyfx.VideoClip("test.clip","../../demos/video_as_dir")
    vc.render("test_stream_output")

    
