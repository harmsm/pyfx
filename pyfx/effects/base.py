__description__ = \
"""
0. __init__ must take a workspace instance and use it to initialize the base
   class via `super().__init__(workspace)`.

1. In __init__, define the self._default_waypoint attribute.  This defines
   the waypoint parameters that will be settable by add_waypoint, as well as
   setting what the default values for those waypoint parameters should be.

2. Define a bake() method.  This should connect between the user-specified
   waypoints for all time points via self._interpolate_waypoints, and should
   precalculate information necesary for the final compositing at any time t.

3. Define a render() method.  This method must have two and only two arguments:
     img (an image in array format)
     t (an integer that indicates the time point to access)
   Render should apply whatever transformation is necessary at time and must
   return an image of identical dimensions to the input image.
"""
from scipy import interpolate

import numpy as np

import copy


### MAYBE MOVE THIS INTO ITS OWN FUNCTION IN UTIL
def smooth(x,window_len=30):
    """
    Smooth a signal using a moving average.

    x: signal
    window_len: size of the smoothing window (defaults to 30 -- one second)
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

class Effect:

    def __init__(self,workspace):

        self._workspace = workspace

        try:
            self._default_waypoint
        except AttributeError:
            err = "Subclasses of Effect must define the self._default_waypoint\n"
            err += "attribute, which specifies tke kwargs that can be passed\n"
            err += "to self.add_waypoint.\n"
            raise NotImplementedError(err)

        # Expose waypoint attributes as attributes to the class.  These are
        # none until the effect is baked.
        reserved_keys = ["t"]
        for k in self._default_waypoint.keys():

            if k in reserved_keys:
                err = "the waypoint parameter name '{}' is reserved and cannot\n"
                err += "be used.\n"
                raise ValueError(err)

            try:
                self.__dict__[k]
                err = "default waypoint overwrites an attribute in base class\n"
                err = "offending attribute: {}\n".format(k)
                raise AttributeError(err)
            except:
                self.__dict__[k] = None

        self._waypoints = {}
        self._waypoints[0] = copy.copy(self._default_waypoint)
        self._baked = False

    def add_waypoint(self,t,**kwargs):
        """
        Add a waypoint to the effect.
        """

        t = int(round(t))

        if t == -1:
            t = self._workspace.max_time

        if  t < 0 or t > self._workspace.max_time:
            err = "time {} is outside of the time spanned by the workspace\n".format(t)
            raise ValueError(err)

        # If the waypoint is already defined, keep its values
        try:
            current_waypoint = self._waypoints[t]

        # Otherwise, grab the waypoint just before time t.
        except KeyError:

            # Append t to the list of times, sort, and then look for whatever
            # index is before *t* in the list.
            times = list(self._waypoints.keys())
            times.append(t)
            times.sort()

            t_index = times.index(t)
            if t_index == 0:
                lookup_time = 0
            else:
                lookup_time = times[t_index - 1]

            current_waypoint = self._waypoints[lookup_time]

        self._waypoints[t] = copy.copy(current_waypoint)

        for k in kwargs.keys():
            if k in self._default_waypoint.keys():
                self._waypoints[t][k] = kwargs[k]
            else:
                err = "waypoint keyword {} not recognized\n".format(k)
                raise ValueError(err)

        self._baked = False

    def set_waypoint(self,t,**kwargs):
        """
        Modify the values in a waypoint.
        """

        # Just wrap add_waypoint, which will only modify values that differ
        # between kwargs and what is in the waypoint already
        self.add_waypoint(t,**kwargs)

    def remove_waypoint(self,t):
        """
        Remove a waypoint from the effect.
        """

        t = int(round(t))

        # Don't really *delete* 0, just make it default.
        if t == 0:
            self._waypoints[0] = copy.copy(self._default_waypoint)

        # Pop the waypoint.  If it is not present, throw an error.
        try:
            self._waypoints.pop(t)
        except KeyError:
            err = "waypoint {} not found\n".format(t)
            raise ValueError(err)

        self._baked = False

    def get_waypoint(self,t):
        """
        Get the waypoint at time t.
        """

        t = int(round(t))

        try:
            return copy.copy(self._waypoints[t])
        except KeyError:
            err = "waypoint {} not found\n".format(t)
            raise ValueError(err)

    def bake(self):
        pass

    def render(self,img,t):
        return img

    def _interpolate_waypoints(self,window_len=30):
        """
        Interpolate between the waypoint values specified by the user.  Load
        the interpolated values into arrays that are class attributes.  (e.g.,
        for a waypoint parameter "x", self.x will now have the interpolated
        values of "x" across the whole workspace time.

        window_len: width of smoothing window. if 0, do not smooth.
        """

        # Construct list of waypoint times.  If there is no waypoint at the
        # very end, create one.
        waypoint_times = list(self._waypoints.keys())
        waypoint_times.sort()
        if waypoint_times[-1] != self._workspace.max_time:
            t = waypoint_times[-1]
            self._waypoints[self._workspace.max_time] = self._waypoints[t]
            waypoint_times.append(self._workspace.max_time)

        # Deal with time
        times = np.array(waypoint_times,dtype=np.float)
        out_t = np.array(range(len(self._workspace.times)),dtype=np.int)
        self.__dict__["t"] = out_t

        # Interpolate each waypoint parameter, smooth, and load into class
        # attribute
        for k in self._waypoints[0].keys():
            values = []
            for t in waypoint_times:
                values.append(self._waypoints[t][k])

            values = np.array(values)
            interpolator = interpolate.interp1d(times,values,kind="linear")
            interpolated = interpolator(self.t)
            smoothed = smooth(interpolated,window_len=window_len)

            self.__dict__[k] = smoothed

    @property
    def default_waypoint(self):
        return copy.copy(self._default_waypoint)

    @property
    def waypoints(self):
        """
        Return a time-sorted list of waypoints.
        """

        out_dict = {}
        t_list = list(self._waypoints.keys())
        t_list.sort()

        for t in t_list:
            out_dict[t] = copy.copy(self._waypoints[t])

        return out_dict

    @property
    def baked(self):
        return self._baked

    @property
    def workspace(self):
        return self._workspace
