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

    # Model the camera as a langevin particle being buffetted by kT
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
