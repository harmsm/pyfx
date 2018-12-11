
import numpy as np
from scipy import interpolate

class VirtualCamera:

    def __init__(self,width=1920,height=1080):

        self._width = width
        self._height = height

        self._waypoints = []

    def _find_pan_crop(self,x,y,width,height):
        """
        If the camera pans along values in x and y, for a starting frame of the
        size width vs. height, return crop values for the image that mean the
        pan will never pass outside of the starting frame while moves are made.
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
        proportional_shift_in_y = max_shake_in_y/height

        # Figure out whether to scale to x or y, depending on which has the
        # larger proportional shift in magnitude
        if proportional_shift_in_x >= proportional_shift_in_y:
            fx = proportional_shift_in_x
        else:
            fx = proportional_shift_in_y

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

        wh = (width - x_crop_pix, height - y_crop_pix)
        crop_x = (x_left_pix, x_right_pix)
        crop_y = (y_bottom_pix, y_top_pix)

        return wh, crop_x, crop_y

    def _find_rotate_crop(self,theta,width,height):
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

        wh = (width - del_x, height - del_y)

        return wh, crop_x, crop_y

    def _find_zoom_crop(self,magnitude,width,height):
        """
        Find crops that allow a zoom of some magnitude onto a frame of width
        and height.
        """

        if magnitude < 1.0:
            err = "this function can only be used for zooming in, not out.\n"
            raise ValueError(err)

        del_x = int(round(width*(1 - 1/magnitude),0))
        if del_x % 2 != 0:
            del_x += 1
        crop_x = (del_x/2,del_x/2)

        del_y = int(round(height*(1 - 1/magnitude),0))
        if del_y % 2 != 0:
            del_y += 1
        crop_y = (del_y/2,del_y/2)

        wh = (width - del_x, height - del_y)

        return wh, crop_x, crop_y


    def _find_shake_crop(self,max_shake,width,height):
        """
        Find crop that will select only known pixels in an array of width and
        height even after displaced randomly by max_shake.
        """

        shake_interval = [-max_shake,max_shake]

        return self._find_pan_crop(x=shake_interval,y=shake_interval,
                                   width=width,height=height)


    def add_waypoint(self,t,x,y,theta):

        self._waypoints.append((t,x,y,theta))


    def render_moves(self,img_list,shaking_magnitude=0):

        waypoints = self._waypoints[:]

        # sort according to time
        waypoints.sort()

        # Add a start-time at 0,0,0 if not given
        if waypoints[0][0] != 0:
            waypoints.insert(0,(0,0,0,0))

        # Add end-time at 0,0,0 if not given
        t_end = len(img_list) - 1
        if waypoints[0][-1] != t_end:
            waypoints.insert((t_end,0,0,0))

        # Extract t, x, y, and theta
        t, x, y, theta = zip(*waypoints)

        # Interpolate entire stack of t, x, y, and theta
        t = np.array(t)
        out_t = np.array(range(len(img_list)),dtype=np.float)

        x = np.array(x)
        x_interp = interpolate.interp1d(t,x,kind='cubic')
        x = x_interp(out_t)

        y = np.array(y)
        y_interp = interpolate.interp1d(t,y,kind='cubic')
        y = y_interp(out_t)

        theta = np.array(theta)
        theta_interp = interpolate.interp1d(t,theta,kind='cubic')
        theta = theta_interp(out_t)



        height = img_list[0].shape[0]
        width = img_list[0].shape[1]

        wh = (width, height)

        wh_list = []
        crop_x_list = []
        crop_y_list = []

        # First deal with shaking
        new_wh, crop_x, crop_y = self._find_shake_crop(max_shape,wh[0],wh[1])
        wh_list.append(new_wh)
        crop_x_list.append(crop_x)
        crop_y_list.append(crop_y)

        # Next deal with panning
        new_wh, crop_x, crop_y = self._find_pan_crop(x,y,new_wh[0],new_wh[1])
        wh_list.append(new_wh)
        crop_x_list.append(crop_x)
        crop_y_list.append(crop_y)

        # Finally, deal with rotation
        new_wh, crop_x, crop_y = self._find_rotate_crop(theta,new_wh[0],new_wh[1])
        wh_list.append(new_wh)
        crop_x_list.append(crop_x)
        crop_y_list.append(crop_y)

        for img in img_list:
            # crop with random offset for camera shaking
            # now crop the output of random shaking for panning
            # rotate output by theta
            # crop that according to final crop to account for rotation

            rotated = skimage.transform.rotate(img,current_theta)
            cropped = skimage.util.crop(rotated,crop,copy=True)

            out_stack.append(cropped)

        return out_stack




    def shake(self,magnitude,total_time):

        pass

    def zoom(self,magnitude,total_time):

        pass
