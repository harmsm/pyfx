
import pyfx
from skimage import draw
import numpy as np

def transition_mask(shape,num_steps,start=None,end=None,feather=0):
    """
    Create a num_steps long collection of 0-255 int masks to wipe
    between "start" and "end" coordinates along the image.

    shape: 2-tuple, shape of image to create wipe mask for
    start: 2-tuple, position from which to start the wipe (must be on an edge)
           If None, left middle
    end: 2-tuple, position at which to end the wipe (does not have to be on
         an edge)  If none, right middle
    num_steps: int, number of steps over which to wipe
    feather: bool, create a smooth edge that is feather steps in width
             along wipe line
    """

    # (middle,left)
    if start is None:
        start = (int(shape[0]/2),0)

    # (middle,right)
    if end is None:
        end = (int(shape[0]/2),shape[1])

    # If feather is specified
    if feather > 0:

        # Feathering works better for odd numbers of steps
        if num_steps % 2 == 0:
            num_steps += 1

        # Add steps so running average does not reduce
        # number of steps
        num_steps = num_steps + feather - 1

    # Grab edges of the array in rc coordinates
    min_r = 0
    max_r = shape[0] - 1
    min_c = 0
    max_c = shape[1] - 1

    # no change in r; move to middle to avoid numerical problems that
    # can arise from corners
    if start[0] == end[0]:
        middle = np.int(np.floor((max_r - min_r)/2))
        start[0] = middle
        end[0] = middle

    # no change in c; move to middle to avoid numerical problems htat
    # can arise from corners
    if start[1] == end[1]:
        middle = np.int(np.floor((max_c - min_c)/2))
        start[1] = middle
        end[1] = middle

    # Create output masks
    out_masks = np.zeros((num_steps+1,shape[0],shape[1]),dtype=np.float)

    # Because I'm not smart enough to do trigonometry in rc coordinates,
    # convert to left-handed xy coordinates.
    initial_tl = pyfx.util.rc_to_xy([min_r,min_c],shape) # top left
    initial_tr = pyfx.util.rc_to_xy([min_r,max_c],shape) # top right
    initial_bl = pyfx.util.rc_to_xy([max_r,min_c],shape) # bottom left
    initial_br = pyfx.util.rc_to_xy([max_r,max_c],shape) # bottom right
    initial_start = pyfx.util.rc_to_xy(start,shape)
    initial_end = pyfx.util.rc_to_xy(end,shape)

    # Start is on bottom edge
    if initial_start[1] == initial_bl[1]:

        theta = 0.0
        tl = initial_tl
        tr = initial_tr
        bl = initial_bl
        br = initial_br

    # Start is on top edge
    elif initial_start[1] == initial_tl[1]:

        theta = 180.0*np.pi/180.0
        tl = initial_br
        tr = initial_bl
        bl = initial_tr
        br = initial_tl

    # Start is on neither top nor bottom edge
    else:

        # Start is on left edge
        if initial_start[0] == initial_tl[0]:

            theta = 90.0*np.pi/180.0
            tl = initial_tr
            tr = initial_br
            bl = initial_tl
            br = initial_bl

        # Start is on right edge
        elif initial_start[0] == initial_tr[0]:

            theta = -90.0*np.pi/180.0
            tl = initial_bl
            tr = initial_tl
            bl = initial_br
            br = initial_tr

        # Start is on neither left nor right
        else:

            err = "Start position must be on an outside edge of the array\n"
            raise ValueError(err)

    # Create rotation matrix
    T = np.array([[np.cos(theta),-np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])

    # Matrix for reverting back to original coordinates
    T_rev = np.array([[np.cos(-theta),-np.sin(-theta)],
                      [np.sin(-theta), np.cos(-theta)]])

    # Rotate start so wipe is coming off bottom edge
    s = np.dot(T,np.array(initial_start))

    # Rotate corners and then translate so "s" is the origin
    top_left     = np.dot(T,tl) - s
    top_right    = np.dot(T,tr) - s
    bottom_left  = np.dot(T,bl) - s
    bottom_right = np.dot(T,br) - s

    # Edge values for x and y in the new coordinate system
    x_min = top_left[0]
    x_max = top_right[0]
    y_min = bottom_left[1]
    y_max = top_left[1]

    # Vector describing center of wipe moving across array
    u = np.dot(T,initial_end) - s

    # Total change in x and y along vector following center of wipe
    dx = u[0]
    dy = u[1]

    # For each step in the wipe
    for i in range(1,num_steps + 1):

        # How far along the wipe?
        phi = i/num_steps

        # Wipe straight up from bottom
        if np.isclose(dx,0):

            current_y = dy*phi

            points = [bottom_left]
            points.append([x_min,current_y])
            points.append([x_max,current_y])
            points.append(bottom_right)

        # Wipe left to right
        elif np.isclose(dy,0):

            current_x = dx*phi

            points = [bottom_left]
            points.append(top_left)
            points.append(np.array([current_x,y_max]))
            points.append(np.array([current_x,y_min]))
            points.append(bottom_left)

        # Wipe along angle
        else:

            # Equation for advancing wipe line
            slope = -dy/dx
            intercept = 2*dy*phi

            # x value for line at extreme bottom and top of array
            x_bottom = (y_min - intercept)/slope
            x_top    = (y_max - intercept)/slope

            # y value for line at extreme left and right of array
            y_left =  x_min*slope + intercept
            y_right = x_max*slope + intercept

            # Start polygon at 0,0 (start)
            points = [np.array([0.0,0.0])]

            # POSITIVE SLOPE: Walk arond polygon clockwise
            if slope > 0:

                # Hits bottom edge, to left of origin.
                if x_bottom >= x_min and x_bottom <= 0:
                    points.append(np.array([x_bottom,y_min]))
                else:

                    # Hits left edge
                    if y_left >= y_min and y_left <= y_max:
                        points.append(bottom_left)
                        points.append(np.array([x_min,y_left]))

                # Hits top edge
                if x_top >= x_min and x_top <= x_max:
                    points.append(np.array([x_top,y_max]))
                    points.append(top_right)
                    points.append(bottom_right)
                else:

                    # Hits right edge
                    if y_right >= y_min and y_right <= y_max:
                        points.append(np.array([x_max,y_right]))
                        points.append(bottom_right)

            # NEGATIVE SLOPE: Walk around polygon counter-clockwise
            else:

                # Hits bottom edge, to right of origin
                if x_bottom <= x_max and x_bottom >= 0:
                    points.append(np.array([x_bottom,y_min]))
                else:

                    # Hits right edge
                    if y_right >= y_min and y_right <= y_max:
                        points.append(bottom_right)
                        points.append(np.array([x_max,y_right]))

                # Hits top edge
                if x_top >= x_min and x_top <= x_max:
                    points.append(np.array([x_top,y_max]))
                    points.append(top_left)
                    points.append(bottom_left)
                else:

                    # Hits left edge
                    if y_left >= y_min and y_left <= y_max:
                        points.append(np.array([x_min,y_left]))
                        points.append(bottom_left)


        # Convert points back to rc to draw polygon
        r = []
        c = []
        for p in points:

            p_trans = np.array(np.round(np.dot(T_rev,p + s)),dtype=np.int)
            new_p = pyfx.util.xy_to_rc(p_trans,shape)

            if new_p[0] == shape[0]-1:
                new_p[0] += 1
            if new_p[1] == shape[1]-1:
                new_p[1] += 1

            r.append(new_p[0])
            c.append(new_p[1])

        # Draw polygon
        rr, cc = draw.polygon(r, c, shape=shape)
        out_masks[i,rr,cc] = 1.0

    # feather
    if feather > 0:
        cs = np.cumsum(out_masks,axis=0)
        cs[feather:] = cs[feather:] - cs[:-feather]
        out_masks = cs[feather-1:]/feather

    # Return 0-255 mask array

    return pyfx.util.to_array(out_masks,dtype=np.uint8,num_channels=1)
