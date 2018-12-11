import numpy as np
from scipy import interpolate
import skimage
import pyfx

import os

def _objective(expand_factor,width,height,x,y,theta):

    new_width = width*expand_factor
    new_height = height*expand_factor

    total_crop = self._calc_total_crop(new_width,new_height,x,y,theta)

    new_width = total_crop[4][0]
    new_height = total_crop[4][1]

    return (new_width - width) + (new_height - height)

def find_pan_crop(self,x,y,width,height):
    """
    Find crop that, when applied to a frame shifted by the maximum pans in
    x and y, is still in the original bounds given by width and height.
    """

    # Find maximum displacement in x
    min_x = np.min(x)
    if min_x > 0: min_x = 0
    max_x = np.max(x)
    if max_x < 0: max_x = 0

    max_shift_in_x = np.abs(min_x) + max_x
    proportional_shift_in_x = max_shift_in_x/width

    # Find maximum displacement in y
    min_y = np.min(y)
    if min_y > 0: min_y = 0
    max_y = np.max(y)
    if max_y < 0: max_y = 0

    max_shift_in_y = np.abs(min_y) + max_y
    proportional_shift_in_y = max_shift_in_y/height

    # Figure out whether to scale to x or y, depending on which has the
    # larger proportional shift in magnitude
    if proportional_shift_in_x >= proportional_shift_in_y:
        fx = proportional_shift_in_x
    else:
        fx = proportional_shift_in_y

    # Figure out x-cropping

    # Total number of pixels in x-crop
    x_crop_pix = int(round(fx*width))

    # Find fraction of pixels to place to the right of the crop.  If there
    # is no crop in this axis, place half of pixels to left and half to
    # the right.
    if max_shift_in_x == 0:
        x_fx_right = 0.5
    else:
        x_fx_right = max_x/max_shift_in_x

    # Define crops.  Add an offset so the two sides add to the right number
    # even in case of rounding error.
    x_right_pix = int(round(x_crop_pix*x_fx_right))
    x_left_pix = int(round(x_crop_pix*(1 - x_fx_right)))
    x_offset = x_crop_pix - (x_right_pix + x_left_pix)
    x_left_pix += x_offset

    crop_x = (x_left_pix, x_right_pix)

    # Figure out y-cropping

    # Total number of pixels in y-crop
    y_crop_pix = int(round(fx*height))

    # Find fraction of pixels to place to the top of the crop.  If there
    # is no crop in this axis, place half of pixels to top and half to
    # the bottom.
    if max_shift_in_y == 0:
        y_fx_top = 0.5
    else:
        y_fx_top = max_y/max_shift_in_y

    # Define crops.  Add an offset so the two sides add to the bottom number
    # even in case of rounding error.
    y_top_pix = int(round(y_crop_pix*y_fx_top))
    y_bottom_pix = int(round(y_crop_pix*(1 - y_fx_top)))
    y_offset = y_crop_pix - (y_top_pix + y_bottom_pix)
    y_bottom_pix += y_offset

    crop_y = (y_bottom_pix, y_top_pix)

    new_width = width - x_crop_pix
    new_height = height - y_crop_pix

    return crop_x, crop_y, new_width, new_height

def find_rotate_crop(self,theta,width,height):
    """
    Find crop that, when applied to a rotated frame with a maximum rotation
    of theta, is still in the original bounds given by width and height.
    """

    # Find largest rotation that we are going to have to do
    theta_max = np.max(np.abs(theta))

    # Find height and width of box rotated in and bounded by the current
    # height and width
    h_prime = width*height/(height*np.sin(theta_max) + width)
    w_prime = width*h_prime/height

    # Figure out cropping
    del_x = int(round(width - w_prime,0))
    del_y = int(round(height - h_prime,0))

    if del_x % 2 != 0:
        del_x += 1
    crop_x = (del_x/2,del_x/2)

    if del_y % 2 != 0:
        del_y += 1
    crop_y = (del_y/2,del_y/2)

    return crop_x, crop_y, width - del_x, height - del_y

def find_zoom_crop(self,magnitude,width,height):
    """
    Find crop that, when applied to a rotated frame with a minimal zooming in,
    is still in the original bounds given by width and height.
    """

    width = wh[0]
    height = wh[1]

    mag = np.min(magnitude)

    if mag < 1.0:
        err = "this function can only be used for zooming in, not out.\n"
        raise ValueError(err)

    del_x = int(round(width*(1 - 1/mag),0))
    if del_x % 2 != 0:
        del_x += 1
    crop_x = (del_x/2,del_x/2)

    del_y = int(round(height*(1 - 1/mag),0))
    if del_y % 2 != 0:
        del_y += 1
    crop_y = (del_y/2,del_y/2)

    wh = (width - del_x, height - del_y)

    return wh, crop_x, crop_y


def build_shaking(self,shaking_magnitude,num_steps):
    """
    Build a shaking trajectory.  This makes the camera wander randomly
    over a harmonic potential centered at 0, simulating a wobbly camera
    holder.
    """

    if shaking_magnitude < 0:
        err = "shaking magntiude must be >= 0.\n"
        raise ValueError(err)

    # Farthest we can go in any direction is three standard deviations away
    # from center
    max_shake = int(round(3*shaking_magnitude))

    # Model this as a langevin particle being buffetted by kT
    p = pyfx.physics.Particle()
    harmonic = pyfx.physics.potential.Spring1D()
    langevin = pyfx.physics.potential.Random(force_sd=shaking_magnitude)

    # Let it wander around the potential surface
    x = []
    y = []
    for i in range(num_steps):

        h = harmonic.get_forces(p.coord)
        l = langevin.get_forces(p.coord)
        p.advance_time(h + l)

        p.coord[p.coord < -max_shake] = -max_shake
        p.coord[p.coord >  max_shake] =  max_shake

        x.append(p.coord[0])
        y.append(p.coord[1])

    return np.array(x), np.array(y)

def calc_total_crop(self,width,height,x,y,theta):
    """
    Calculate the cropping that would result to make the x, y, and theta
    moves specified given the height and width.
    """

    # Deal with panning
    pan_wh = (width, height)
    rotate_wh, pan_crop_x, pan_crop_y = find_pan_crop(x,y,pan_wh)

    # Deal with rotation
    final_wh, rotate_crop_x, rotate_crop_y = find_rotate_crop(theta,rotate_wh)

    return pan_crop_x, pan_crop_y, rotate_crop_x, rotate_crop_y, final_wh

class VirtualCamera:
    """
    Apply virtual pans, shakes, rotation, and zooming to frames.
    """

    def __init__(self):

        self._waypoints = []

    def add_waypoint(self,t,x,y,theta):
        """
        Add a waypoint to the camera instructions.

        t: time of waypoint
        x: x position at time t
        y: y position at time t
        theta: rotation at time t (degrees counterclockwise)
        """

        self._waypoints.append((t,x,y,theta))


    def render_moves(self,img_list,out_dir,shaking_magnitude=0,expand=True):
        """
        Render all of the camera moves in the waypoints for the images in
        img_list.

        img_list: list of image files
        out_dir: output directory
        shaking_magnitude: whether to apply shaking. magnitude is standard
                           deviation on random noise applied to x/y
        expand: bool.  whether to expand frame by mirroring content in the
                frame prior to cropping, thus keeping same composition.
        """

        # Create directory if it does not exist
        if not os.path.isdir(out_dir):
            if os.path.exists(out_dir):
                err = "{} is not a directory.\n".format(out_dir)
                raise ValueError(err)
            os.mkdir(out_dir)

        # Load image as array
        img = pyfx.util.from_file(img_list[0])

        # Find dimensions of image
        height = img.shape[1]
        width = img.shape[0]
        if len(img.shape) > 2:
            multichannel = True
        else:
            multichannel = False

        final_out_size = img.shape

        # Grab waypoints and sort according to time
        waypoints = self._waypoints[:]
        waypoints.sort()

        # Add a start-time at 0,0,0 if no start point is given
        if waypoints[0][0] != 0:
            waypoints.insert(0,(0,0,0,0))

        # Add end-time at 0,0,0 if no end point is given
        t_end = len(img_list) - 1
        if waypoints[-1][0] != t_end:
            waypoints.append((t_end,0,0,0))

        # Extract t, x, y, and theta from waypoints
        t, x, y, theta = zip(*waypoints)

        # Interpolate entire stack of t, x, y, and theta
        t = np.array(t)
        out_t = np.array(range(len(img_list)),dtype=np.float)

        # choose order of interpolation
        if len(x) <= 3:
            kind="linear"
        else:
            kind="cubic"

        # Interpolate
        x = np.array(x)
        x_interp = interpolate.interp1d(t,x,kind=kind)
        x = x_interp(out_t)

        y = np.array(y)
        y_interp = interpolate.interp1d(t,y,kind=kind)
        y = y_interp(out_t)

        # If we want the camera to shake, this is basically just another
        # set of (randomly directed) pans.
        if shaking_magnitude > 0:
            shake_x, shake_y = build_shaking(shaking_magnitude,len(x))
            x = x + shake_x
            y = y + shake_y

        # Convert to theta radians
        theta = np.array(theta)*np.pi/180
        theta_interp = interpolate.interp1d(t,theta,kind=kind)
        theta = theta_interp(out_t)

        # Calculate the pans we are going to use
        total_crop = calc_total_crop(width,height,x,y,theta)

        # If we are expanding (rather than simply cropping)...
        if expand:

            pan_crop_x, pan_crop_y, rotate_crop_x, rotate_crop_y, final_wh = self._calc_total_crop(new_width,new_height,x,y,theta)

            # Find largest expansion in x and y and start there
            expand_in_x = width/final_wh[0]
            expand_in_y = height/final_wh[1]

            if expand_in_x > expand_in_y:
                expand_fx = expand_in_x
            else:
                expand_fx = expand_in_y

            expand_fx = expand_fx

            # Split amount that we need to add over between left/right
            x_to_add = int(round(width*(expand_fx - 1)))
            x_expand = [x_to_add//2, x_to_add//2 + x_to_add % 2]

            # Split amount that we need to add over between top/bottom
            y_to_add = int(round(height*(expand_fx - 1)))
            y_expand = [y_to_add//2, y_to_add//2 + y_to_add % 2]

            # Calculate new crops
            new_width = width + x_to_add
            new_height = height + y_to_add
            pan_crop_x, pan_crop_y, rotate_crop_x, rotate_crop_y, final_wh = self._calc_total_crop(new_width,new_height,x,y,theta)

        pan_crop_x, pan_crop_y, rotate_crop_x, rotate_crop_y, final_wh = total_crop
        print("final crop size:",final_wh)

        # For each image file
        for i, img_file in enumerate(img_list):

            # Get image, possibly expanding according to expansion determined
            # above
            img = pyfx.util.from_file(img_file)
            if expand:
                img = pyfx.util.expand(img,x_expand,y_expand)

            # Find crop incorporating pan in x.  Make sure the crop is always
            # of the correct size
            x1 = int(round(pan_crop_x[0] + x[i]))
            x2 = int(round(pan_crop_x[1] + x[i]))
            diff = (pan_crop_x[0] + pan_crop_x[1]) - (x1 + x2)
            x2 = x2 + diff

            # Find crop incorporating pan in y.  Make sure the crop is always
            # of the correct size
            y1 = int(round(pan_crop_y[0] + y[i]))
            y2 = int(round(pan_crop_y[1] + y[i]))
            diff = (pan_crop_y[0] + pan_crop_y[1]) - (y1 + y2)
            y2 = y2 + diff

            # Construct cropping syntax
            if multichannel:
                crops = ((x1,x2),(y1,y2),(0,0))
            else:
                crops = ((x1,x2),(y1,y2))

            # Crop to simulate panning
            cropped_for_pan = skimage.util.crop(img,crops,copy=True)

            # Rotate by theta
            rotated = skimage.transform.rotate(cropped_for_pan,theta[i])

            if multichannel:
                crops = (rotate_crop_x,rotate_crop_y,(0,0))
            else:
                crops = (rotate_crop_x,rotate_crop_y)

            # Crop rotated image
            panned_and_rotated = skimage.util.crop(rotated,crops,copy=True)

            final = skimage.transform.resize(panned_and_rotated,final_out_size)

            img_root = os.path.split(img_file)[-1]
            out_file = os.path.join(out_dir,img_root)

            pyfx.util.to_file(final,out_file)
