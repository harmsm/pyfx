
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


"""
process1 = (
    ffmpeg
    .input(in_filename)
    .output('pipe:', format='rawvideo', pix_fmt='rgb24')
    .run_async(pipe_stdout=True)
)

process2 = (
    ffmpeg
    .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(width, height))
    .output(out_filename, pix_fmt='yuv420p')
    .overwrite_output()
    .run_async(pipe_stdin=True)
)

while True:
    in_bytes = process1.stdout.read(width * height * 3)
    if not in_bytes:
        break
    in_frame = (
        np
        .frombuffer(in_bytes, np.uint8)
        .reshape([height, width, 3])
    )
    out_frame = in_frame * 0.3
    process2.stdin.write(
        frame
        .astype(np.uint8)
        .tobytes()
    )

process2.stdin.close()
process1.wait()
process2.wait() 
"""
