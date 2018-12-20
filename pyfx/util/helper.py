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
        warnings.warn("T value outside of valid range (1000 to 40000 K)\n")

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

def channel_stretch(img,cutoff=0.005):
    """
    Independently stretch the RGB values so they range from 0 to 255.  Tosses
    the highest and lowest 0.005 of pixel values to avoid bias from outlier
    points.  This follows description of the algorithm used by the GIMP for
    white balance. (https://docs.gimp.org/2.10/en/gimp-layer-white-balance.html)
    """

    rgb = pyfx.util.to_array(img,num_channels=3,dtype=np.uint8)

    for i in range(3):

        # Grab the values of the top and bottom cutoff-th percentiles
        # for the channel
        h = np.histogram(rgb[:,:,i],bins=range(257))
        cumsum = np.cumsum(h[0]/np.sum(h[0]))
        bottom = np.min(h[1][:-1][cumsum > cutoff])
        top = np.max(h[1][:-1][cumsum < (1 - cutoff)])

        # Normalize the channel value to these top and bottom values
        normalized = (rgb[:,:,i] - bottom)/(top - bottom)

        # Whack any values that are outside of 0 to 1 after normalization
        normalized[normalized > 1] = 1.0
        normalized[normalized < 0] = 0.0

        # Load back into the rgb image
        rgb[:,:,i] = np.round(255*normalized,0)

    return rgb

def adjust_white_balance(img,white_point=(255,255,255)):
    """
    Given an RGB value that is defined as actual white (on 0-255 scale),
    transform pixels in image to adjust white balance.
    """

    img = pyfx.util.to_array(img,num_channels=3)

    try:
        if len(white_point) != 3:
            raise TypeError
    except TypeError:
        err = "white point should be a list/tuple/array with 3 values\n"
        raise ValueError(err)

    white_point = np.array(white_point,dtype=np.float)
    transform_matrix = (255/white_point)*np.eye((3))

    new_img = np.dot(img,transform_matrix)
    new_img[np.isnan(new_img)] = 0
    new_img[new_img > 255] = 255
    new_img[new_img < 0] = 0

    return np.array(np.round(new_img),dtype=np.uint8)

def smooth(x,window_len=0):
    """
    Smooth a signal using a moving average.

    x: signal
    window_len: size of the smoothing window
                if 0, no smoothing is done.
    """

    if window_len == 0:
        return x

    if window_len < 0:
        err = "window length must be a positive integer\n"
        raise ValueError(err)

    window_len = int(round(window_len))
    if window_len % 2 == 0:
        window_len += 1

    window = np.ones(window_len,'d')
    signal = np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    smoothed = np.convolve(window/window.sum(),signal,mode='valid')

    trim = int((window_len - 1)/2)

    return smoothed[trim:-trim]


def harmonic_langenvin(num_steps,
                       spring_constant=1.0,
                       force_sd=1.0,
                       max_value=None):
    """
    Build a shaking trajectory.  This makes the a particle wander randomly
    over a harmonic potential centered at 0.  This can be used to simulate
    wobbling cameras, flickering lights... anything that can be described as
    random fluctuations along a trajectory that stays around some value.  The
    output trajectory is in 2D, but each dimension is independent, so you can
    take a single dimension from the output if wanted.

    num_steps: how many steps to take.

    The following three parameters can either be individual values OR a list-
    like object that is num_steps long.  If list-like, those constants will be
    updated throughout the trajectory.

    spring_constant: how stiff is the harmonic potential
    force_sd: how hard does the particle get jostled each step (sqrt(temperature))
    max_value: how far to let the particle get away from zero.  if None, bound
               at 3 x force_sd.
    """

    try:
        if len(spring_constant) != num_steps:
            err = "spring constant array is not the same length as num_steps\n"
            raise ValueError(err)
    except TypeError:
        try:
            spring_constant = np.array([float(spring_constant)
                                        for i in range(num_steps)])
        except ValueError:
            err = "spring constant could not be coerced into a float\n"
            raise ValueError(err)

    try:
        if len(force_sd) != num_steps:
            err = "force_sd array is not the same length as num_steps\n"
            raise ValueError(err)
    except TypeError:
        try:
            force_sd = np.array([float(force_sd)
                                        for i in range(num_steps)])
        except ValueError:
            err = "force_sd could not be coerced into a float\n"
            raise ValueError(err)

    try:
        if len(max_value) != num_steps:
            err = "max_value array is not the same length as num_steps\n"
            raise ValueError(err)
    except TypeError:

        try:
            if max_value is None:
                max_value = [None for i in range(num_steps)]
            else:
                max_value = np.array([float(max_value)
                                            for i in range(num_steps)])
        except ValueError:
            err = "max_value could not be coerced into a float\n"
            raise ValueError(err)


    # Model a langevin particle being buffetted by kT
    p = pyfx.physics.Particle()
    harmonic = pyfx.physics.potentials.Spring1D(spring_constant=spring_constant[0])
    langevin = pyfx.physics.potentials.Random(force_sd=force_sd[0])

    # Let it wander around the potential surface
    x = []
    y = []
    for i in range(num_steps):

        # Update harmonic and langevin with new shaking parameters
        harmonic.update(spring_constant=spring_constant[i])
        langevin.update(force_sd=force_sd[i])

        # If no bound is specified, the farthest we can go in any direction is
        # three standard deviations in sqrt(kT) away from center
        if max_value[i] is None:
            bound = int(round(3*force_sd[i]))
        else:
            bound = max_shake[i]

        h = harmonic.get_forces(p.coord)
        l = langevin.get_forces(p.coord)
        p.advance_time(h + l)

        p.coord[p.coord < -bound] = -bound
        p.coord[p.coord >  bound] =  bound

        x.append(p.coord[0])
        y.append(p.coord[1])

    return np.array(x), np.array(y)
