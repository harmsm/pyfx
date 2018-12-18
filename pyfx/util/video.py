
import pyfx
import numpy as np

import ffmpeg

def video_dimensions(filename):

    probe = ffmpeg.probe(filename)

    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

    width = int(video_stream['width'])
    height = int(video_stream['height'])

    return width, height

def video_to_array(filename):

    width, height = video_dimensions(filename)

    video_stream, _ = (
        ffmpeg
        .input(filename)
        .output('pipe:', format='rawvideo', pix_fmt='rgb24')
        .run(capture_stdout=True)
    )

    video = (
        np
        .frombuffer(video_stream, np.uint8)
        .reshape([-1, height, width, 3])
    )

    return video
