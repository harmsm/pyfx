__description__ = \
"""
Sundry functions that are helpful for generating masks etc.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-14"

import pyfx
from PIL import ImageDraw, ImageFont
import numpy as np

import sys, shutil, random, string, os, warnings

def foreground_mask(workspace,time_interval=(0,-1),threshold=0.1):
    """
    Create an image array where pixel intensity is the frequency that
    the pixel in question differs from the background.  Useful for helping
    create foreground masks.
    """

    ws = workspace

    num_to_check = len(ws.times[time_interval[0]:time_interval[-1]])

    # Calculate the difference between each image and the background
    out_array = np.zeros((ws.shape[0],ws.shape[1]),dtype=np.float)
    for i, t in enumerate(ws.times[time_interval[0]:time_interval[-1]]):
        print(i,'/',num_to_check); sys.stdout.flush()
        frame = ws.get_frame(t)
        frame_diff = ws.background.frame_diff(frame)

        out_array = out_array + frame_diff

    out_array = out_array/np.max(out_array)

    shutil.rmtree(name)

    return pyfx.util.to_array(out_array,num_channels=1,dtype=np.uint8)

def text_on_image(img,text,location=(0,0),size=100,color=(0,0,0)):
    """
    Draw text on an image.

    img: image (array,file,PIL.Image)
    text: string of text to write
    location: starting location in pixels
    size: font size
    color: color (rgb, 0-1 format)
    """

    if size < 0:
        err = "size must be positive\n"
        raise ValueError(err)

    if len(color) != 3 or max(color) > 1 or min(color) < 0:
        err = "rgb should be three values between 0 and 1\n"
        raise ValueError(err)

    # Make sure location is integers
    location = tuple([int(round(x,0)) for x in location])

    # Put color on 0-255 scale
    color = tuple([int(round(c*255)) for c in color])

    # create a PIL.Image object with the input image
    edited_image = pyfx.util.to_image(img)

    # initialise the drawing context
    draw = ImageDraw.Draw(edited_image)

    # create font object with the font file and specify size
    font_location = os.path.join(pyfx.root_dir,"data","fonts","Lato-Light.ttf")
    font = ImageFont.truetype(font_location, size=size)

    # draw the text
    draw.text(location, text, fill=color, font=font)

    # Figre out the number of output channels (match input)
    if type(img) is str:
        num_channels = 4
        dtype = np.uint8
    else:
        dtype = img.dtype
        if len(img.shape) == 2:
            num_channels = 1
        else:
            num_channels = img.shape[2]

    return pyfx.util.to_array(edited_image,
                              num_channels=num_channels,
                              dtype=dtype)

def number_frames(workspace,out_dir,overwrite=False):
    """
    Number every frame.
    """
    ws = workspace

    if os.path.isdir(out_dir):
        if overwrite:
            shutil.rmtree(out_dir)
            os.mkdir(out_dir)
        else:
            err = "{} already exists\n".format(out_dir)
            raise FileExistsError(err)
    else:
        os.mkdir(out_dir)

    fmt_string = "{:0" + str(len(str(ws.max_time)) + 1) + "d}"
    for t in ws.times:
        print(t,"/",len(ws.times))

        frame = ws.get_frame(t)
        to_write = fmt_string.format(t)
        img = pyfx.util.helper.text_on_image(frame,to_write,
                                             location=(50,50),
                                             size=150,color=(1,0,0))

        out_file = os.path.join(out_dir,fmt_string.format(t) + ".png")
        pyfx.util.to_file(img,out_file)

def kelvin_to_rgb(T):
    """
    Hacked, empirical way to go from a color temperature in Kelvin to
    the RGB value for the white point. Approximately valid between
    1000-40000 K.  Returns a numpy array of R,G,B in 0-255 format.

    Lifted from:
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """

    if T < 1000 or T > 40000:
        warnings.warn("T value outside of valid range (1000 to 40000 K)\n"

    T = T/100.0

    if T <= 66:
        r = 255
        g = 99.4708025861*np.log(T) - 161.1195681661
        if T <= 19:
            b = 0
        else:
            b = 138.5177312231*np.log(T - 10) - 305.0447927307
    else:
        r = 329.698727446*((T - 60)**(-0.1332047592))
        g = 288.122169528*((T - 60)**(-0.0755148492))
        b = 255

    r = int(round(r))
    g = int(round(g))
    b = int(round(b))

    # Fix bounds
    if r < 0: r = 0
    if r > 255: r = 255
    if g < 0: b = 0
    if g > 255: b = 255
    if b < 0: b = 0
    if b > 255: b = 255

    return np.array([r,g,b],dtype=np.uint8)


def color_temperature(img,T):





– Calculate temperature RGB
– Loop through the image one pixel at a time. For each pixel:
— Get RGB values
— Calculate luminance of those RGB values (Luminance = (Max(R,G,B) + Min(R,G,B)) / 2)
— Alpha-blend the RGB values with the temperature RGB values at the requested strength (max strength = 50/50 blend)
— Calculate HSL equivalents for the newly blended RGB values
— Convert those HSL equivalents back to RGB, but substitute the ORIGINAL luminance value (this maintains the luminance of the pixel)
