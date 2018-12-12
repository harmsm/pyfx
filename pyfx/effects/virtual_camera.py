import pyfx
from .base import Effect

import numpy as np
from scipy import interpolate, optimize
import skimage

import os, copy

def _objective(expand_factor,obj,width,height):
    """
    Objective function that, when minimized, yields the expansion factor that
    should be applied with the width and height so that camera moves remain
    within the frame the whole time.
    """

    new_width = width*expand_factor[0]
    new_height = height*expand_factor[0]

    total_crop = obj._calc_total_crop(new_width,new_height)

    final_width = total_crop[6]
    final_height = total_crop[7]

    return ((final_width - width) + (final_height - height))**2


class VirtualCamera(Effect):
    """
    Apply virtual pans, shakes, rotation, and zooming to frames.

    Waypoint properties:

    x: x position at time t
    y: y position at time t
    theta: rotation at time t (degrees counterclockwise)
    zoom: float >= 1.0, where 1.0 is no zoom and >1 is zoomed in
    shaking_magnitude: shaking_magnitude
    shaking_stiffness: shaking_stiffness
    """

    def __init__(self,workspace):

        self._default_waypoint = {"x":0.0,
                                  "y":0.0,
                                  "theta":0.0,
                                  "zoom":1.0,
                                  "shaking_magnitude":0.0,
                                  "shaking_stiffness":1.0}
        self._waypoints = {}
        self._waypoints[0] = copy.copy(self._default_waypoint)

        super().__init__(workspace)

    def _build_shaking(self):
        """
        Build a shaking trajectory.  This makes the camera wander randomly
        over a harmonic potential centered at 0, simulating a wobbly camera
        holder.
        """

        # Model the camera as a langevin particle being buffetted by kT
        p = pyfx.physics.Particle()
        harmonic = pyfx.physics.potential.Spring1D(spring_constant=self._shaking_stiffness[0])
        langevin = pyfx.physics.potential.Random(force_sd=self._shaking_magnitude[0])

        # Let it wander around the potential surface
        x = []
        y = []
        for t in self._workspace.times:

            # Update harmonic and langevin with new shaking parameters
            harmonic.update(spring_constant=self._shaking_stiffness[t])
            langevin.update(force_sd=self._shaking_magnitude[t])

            # Farthest we can go in any direction is three standard deviations
            # in kT away from center
            max_shake = int(round(3*self._shaking_magnitude[t]))

            h = harmonic.get_forces(p.coord)
            l = langevin.get_forces(p.coord)
            p.advance_time(h + l)

            p.coord[p.coord < -max_shake] = -max_shake
            p.coord[p.coord >  max_shake] =  max_shake

            x.append(p.coord[0])
            y.append(p.coord[1])

        return np.array(x), np.array(y)

    def _calc_total_crop(self,width,height):
        """
        Calculate the cropping that would result to make the x, y, theta, and
        zoom moves specified given the height and width.
        """

        # Deal with pan
        pan_crop_x, pan_crop_y, rotate_width, rotate_height = pyfx.util.crop.find_pan_crop(self._x,self._y,width,height)

        # Deal with rotation
        rotate_crop_x, rotate_crop_y, zoom_width, zoom_height = pyfx.util.crop.find_rotate_crop(self._theta,rotate_width,rotate_height)

        # Deal with zoom
        zoom_crop_x, zoom_crop_y, final_width, final_height = pyfx.util.crop.find_zoom_crop(self._zoom,zoom_width,zoom_height)

        return pan_crop_x, pan_crop_y, rotate_crop_x, rotate_crop_y, zoom_crop_x, zoom_crop_y, final_width, final_height


    def bake(self,max_expand=1.5):
        """
        Pre-calculate all of the camera moves in the waypoints.

        max_expand: float between 1 and 2.  How much to expand allow the frame
                    to expand by mirroring edges so virtual camera moves don't
                    end up zoomed up on a tiny portion of the frame.
        """

        if max_expand < 1 and max_expand > 2:
            err = "max_expand should be a float between 1 and 2\n"
            raise ValueError(err)

        # Load image as array
        img = self._workspace.get_frame(0)

        # Find dimensions of image
        self._width = img.shape[0]
        self._height = img.shape[1]

        # Final output size
        self._final_out_size = img.shape

        # Construct list of waypoint times.  If there is no waypoint at the
        # very end, create one.
        waypoint_times = list(self._waypoints.keys())
        waypoint_times.sort()
        if waypoint_times[-1] != self._workspace.max_time:
            t = waypoint_times[-1]
            self._waypoints[self._workspace.max_time] = self._waypoints[t]
            waypoint_times.append(self._workspace.max_time)

        # Grab waypoint values
        x = np.array([self.waypoints[t]["x"] for t in waypoint_times])
        y = np.array([self.waypoints[t]["y"] for t in waypoint_times])
        theta = np.array([self.waypoints[t]["theta"] for t in waypoint_times])
        zoom = np.array([self.waypoints[t]["zoom"] for t in waypoint_times])
        shaking_magnitude = np.array([self.waypoints[t]["shaking_magnitude"]
                                      for t in waypoint_times])
        shaking_stiffness = np.array([self.waypoints[t]["shaking_stiffness"]
                                      for t in waypoint_times])

        # Interpolate way point values.
        t = np.array(waypoint_times,dtype=np.float)
        out_t = np.array(range(len(self._workspace.times)),dtype=np.float)

        # choose order of interpolation
        if len(t) <= 3:
            kind="linear"
        else:
            kind="cubic"

        # Interpolate x
        x_interp = interpolate.interp1d(t,x,kind=kind)
        self._x = x_interp(out_t)

        # Interpolate y
        y_interp = interpolate.interp1d(t,y,kind=kind)
        self._y = y_interp(out_t)

        # Interpolate theta, convert to radians
        theta_interp = interpolate.interp1d(t,theta,kind=kind)
        self._theta = theta_interp(out_t)*np.pi/180

        # Interpolate zooming
        zoom_interp = interpolate.interp1d(t,zoom,kind=kind)
        self._zoom = zoom_interp(out_t)

        # Interpolate shaking_magnitude
        sm_interp = interpolate.interp1d(t,shaking_magnitude,kind=kind)
        self._shaking_magnitude = sm_interp(out_t)

        # Interpolate shaking_stiffness
        ss_interp = interpolate.interp1d(t,shaking_stiffness,kind=kind)
        self._shaking_stiffness = ss_interp(out_t)

        # Append shaking to x and y
        shake_x, shake_y = self._build_shaking()
        self._x = self._x + shake_x
        self._y = self._y + shake_y

        # --------------------------------------------------------------------
        # Figure out the cropping to use
        # --------------------------------------------------------------------

        # Find the expansion factor that yields a crop that is the same size
        # as the initial image
        fit = optimize.minimize(_objective,[1.0],
                                args=(self,self._width,self._height),
                                bounds=[(1.0,max_expand)])
        expand_fx = fit.x[0]
        if expand_fx > max_expand:
            expand_fx = max_expand

        # Split amount that we need to add between left/right
        x_to_add = int(round(self._width*(expand_fx - 1)))
        self._x_expand = [x_to_add//2, x_to_add//2 + x_to_add % 2]

        # Split amount that we need to add between top/bottom
        y_to_add = int(round(self._height*(expand_fx - 1)))
        self._y_expand = [y_to_add//2, y_to_add//2 + y_to_add % 2]

        # Calculate new crops
        self._new_width = self._width + x_to_add
        self._new_height = self._height + y_to_add
        total_crop = self._calc_total_crop(self._new_width,self._new_height)

        self._pan_crop_x = total_crop[0]
        self._pan_crop_y = total_crop[1]
        self._rotate_crop_x = total_crop[2]
        self._rotate_crop_y = total_crop[3]
        self._zoom_crop_x = total_crop[4]
        self._zoom_crop_y = total_crop[5]
        self._final_width = total_crop[6]
        self._final_height = total_crop[7]

        print("final crop size:",self._final_width,self._final_height)

        self._baked = True

    def render(self,img):

        t = self._workspace.current_time

        # expand image if requested
        img = pyfx.util.crop.expand(img,self._x_expand,self._y_expand)

        # Find crop incorporating pan in x.  Make sure the crop is always
        # of the correct size
        x1 = int(round(self._pan_crop_x[0] + self._x[t]))
        x2 = int(round(self._pan_crop_x[1] + self._x[t]))
        diff = (self._pan_crop_x[0] + self._pan_crop_x[1]) - (x1 + x2)
        x2 = x2 + diff

        # Find crop incorporating pan in y.  Make sure the crop is always
        # of the co rrect size
        y1 = int(round(self._pan_crop_y[0] + self._y[t]))
        y2 = int(round(self._pan_crop_y[1] + self._y[t]))
        diff = (self._pan_crop_y[0] + self._pan_crop_y[1]) - (y1 + y2)
        y2 = y2 + diff

        # Crop to simulate panning
        cropped_for_pan = pyfx.util.crop.crop(img,(x1,x2),(y1,y2))

        # Rotate by theta
        rot = skimage.transform.rotate(cropped_for_pan,self._theta[t]*180/np.pi)

        # Crop rotated image
        pan_rot = pyfx.util.crop.crop(rot,self._rotate_crop_x,
                                          self._rotate_crop_y)

        # Crop for zoom
        pan_rot_zoom = pyfx.util.crop.crop(pan_rot,self._zoom_crop_x,
                                                   self._zoom_crop_y)

        # Make sure the image is the correct size after our maniuplations
        final = skimage.transform.resize(pan_rot_zoom,self._final_out_size)

        return final
