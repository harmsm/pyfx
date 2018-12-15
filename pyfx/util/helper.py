__description__ = \
"""
Sundry functions that are helpful for generating masks etc.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-14"

import pyfx
import numpy as np

import sys, shutil, random, string

def foreground_mask(input_directory,bg_frame,time_interval=(0,-1)):
    """
    Create an image array where pixel intensity is the frequency that
    the pixel in question differs from the background.
    """

    # Create a temporary workspace
    name = "".join([random.choice(string.ascii_letters) for i in range(10)])
    ws = pyfx.Workspace(name=name,
                        src=input_directory,
                        bg_frame=bg_frame)

    num_to_check = len(ws.times[time_interval[0]:time_interval[-1]])

    # Calculate the difference between each image and the background
    out_array = np.zeros((ws.shape[0],ws.shape[1]),dtype=np.float)

    for i, t in enumerate(ws.times[time_interval[0]:time_interval[-1]]):
        print(i,'/',num_to_check); sys.stdout.flush()
        frame = ws.get_frame(t)
        frame_diff = ws.background.frame_diff(frame)

        out_array[:,:] = out_array[:,:] + frame_diff

    out_array = out_array/np.max(out_array)

    shutil.rmtree(name)

    return pyfx.util.to_array(out_array,num_channels=1,dtype=np.uint8)


def number_frames(input_directory,bg_frame):
    """
    Number every frame.
    """

    pass


    # create font object with the font file and specify
    # desired size

    font = ImageFont.truetype('Roboto-Bold.ttf', size=45)

    # starting position of the message

    (x, y) = (50, 50)
    message = "Happy Birthday!"
    color = 'rgb(0, 0, 0)' # black color

    # draw the message on the background

    draw.text((x, y), message, fill=color, font=font)
    (x, y) = (150, 150)
    name = 'Vinay'
    color = 'rgb(255, 255, 255)' # white color
    draw.text((x, y), name, fill=color, font=font)

    # save the edited image

    image.save('greeting_card.png')
