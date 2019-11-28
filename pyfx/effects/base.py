__description__ = \
"""
A new effect should be a subclass of Effect with the following four
characteristics.

0. __init__ must take a workspace instance and use it to initialize the base
   class via `super().__init__(workspace)`.

1. In __init__, define the self._default_waypoint attribute (minimally an
   empty dictionary).  This defines the waypoint parameters that will be
   settable by add_waypoint(), as well as setting what the default values for
   those waypoint parameters should be.  Any key defined in this dictionary
   (for example, "key_name") will automatically be made available within the
   class instance (for example, as self.key_name).

2. Define a bake() method.  This should precalculate information necessary
   for the final compositing at any time t.  If no precalculation is necessary,
   bake need not be defined.

   Any re-defined bake method must:

     A. Run self._interpolate_waypoints and
     B. Set self._bake = True
     C. Have default values for all arguments, so it can be run as self.bake().

3. Define a render() method.  This method must have an img as its one and
   only argument.  This should take an image in array format. Render should
   apply whatever transformation is necessary at time and must return an image
   of identical dimensions to the input image.

Some useful private methods/features of the Effect class:

1.
"""
import pyfx

from scipy import interpolate
import numpy as np

import copy

class Effect:
    """
    Base class for defining effects that should be applied across an entire
    video workspace.  Should not be used on its own; must be subclassed.

    The following paramters are defined here.
    t: time
    protect_mask: 2D array applied as an alpha mask to protect certain
                  chunks of the image from effect.  A value of 0 means have
                  effect; a value of 255 means keep original frame.
    """

    def __init__(self,workspace):
        """
        This __init__ function should be called in subclasses using
        super().__init__(workspace)
        """

        reserved_keys = ["t","protect_mask","alpha"]

        self._workspace = workspace

        try:
            self._default_waypoint
        except AttributeError:
            err = "Subclasses of Effect must define the self._default_waypoint\n"
            err += "attribute, which specifies tke kwargs that can be passed\n"
            err += "to self.add_waypoint.\n"
            raise NotImplementedError(err)

        # Make sure the self._default_waypoint keys are valid
        for k in self._default_waypoint.keys():

            if k in reserved_keys:
                err = "the waypoint parameter name '{}' is reserved and cannot\n"
                err += "be used.\n"
                raise ValueError(err)
        self._default_waypoint["protect_mask"] = None
        self._default_waypoint["alpha"] = 1.0

        # Expose waypoint attributes as attributes to the class.  These are
        # none until the effect is baked.
        for k in self._default_waypoint.keys():
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

    def bake(self,smooth_window_len=0):
        """
        Can be redefined in subclass.  Note: be careful calling this with
        super().bake(), as this will set the internal status of self._bake
        to True.

        Interpolate waypoints and do whatever precalculations are necessary
        for rendering.
        """

        self._interpolate_waypoints(smooth_window_len)
        self._baked = True

    def render(self,img):
        """
        Should be redefined in subclass.
        """

        return img

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

    def add_waypoints(self,waypoints):
        """
        Add a block of waypoints all at once.  waypoints should be a pandas
        dataframe or file that can be read by pandas (csv/excel).  The
        dataframe must have a 't' column that indicates the waypoint time (in
        workspace time).  Other columns are interpreted as keywords.  For
        example, the data frame:

        t,color
        10,red
        17,blue

        would create two waypoints:
            self.add_waypoint(t=10,color="red")
            self.add_waypoint(t=17,color="blue")
        """

        # Try to read waypoints from a file
        if type(waypoints) is str:

            print("{} is a string.  Trying to read as file.".format(waypoints))

            if not os.path.isfile(waypoints):
                err = "\n\n{} does not exist.\n\n".format(waypoints)
                raise FileNotFoundError(err)

            if waypoints[:-5] == ".xlsx" or waypoints[:-4] == ".xls":
                self._waypoint_df = pd.read_excel(waypoints)
            elif waypoints[:-4] == ".csv":
                self._waypoint_df = pd.read_csv(waypoints)
            else:
                err = "\n\nFile type of {} not recognized.  Should be excel or csv.\n\n".format(waypoints)
                raise ValueError(err)

        # Grab the waypoints as as pandas dataframe
        elif type(waypoints) is pd.DataFrame:
            self._waypoint_df = waypoints.copy()

        else:
            err = "\n\nwaypoints type not recognized.  Should be file readable "
            err += "by pandas or a pandas DataFrame.\n\n".format(waypoints)
            raise ValueError(err)

        # Create list of all columns in dataframe except 't'
        columns = list(self._waypoint_df.columns)
        try:
            columns.remove('t')
        except ValueError:
            err = "waypoints dataframe must have a 't' column indicating time (in workspace frame)\n"
            raise ValueError(err)

        # Create list of all 't', making sure that the times are unique
        times = np.copy(self._waypoint_df.t)
        times = list(np.array(np.round(times,0),dtype=np.int))
        if len(times) != len(set(times)):
            err = "Duplicate waypoints in file. (Float times are rounded to nearest integer time.)\n"
            raise ValueError(err)

        # Create a waypoint for each time point
        for i in range(len(times)):

            kwargs = {}
            for c in columns:
                kwargs[c] = self._waypoint_df[c].iloc[i]

            self.add_waypoint(times[i],**kwargs)


    def _protect(self,original_img,processed_img):
        """
        Protect some portion of the processed image with an original image.
        """

        t = self._workspace.current_time

        if self.protect_mask[t] is not None:

            # Drop protection mask onto original image
            protect = pyfx.util.to_array(original_img,
                                         num_channels=4,
                                         dtype=np.uint8)

            protect[:,:,3] = pyfx.util.to_array(self.protect_mask[t],
                                                num_channels=1,
                                                dtype=np.uint8)

            # Add an alpha channel to the new rgb value
            rgba = 255*np.ones((original_img.shape[0],original_img.shape[1],4),
                               dtype=np.uint8)
            rgba[:,:,:3] = processed_img[:,:,:3]

            # Do alpha compositing
            out = pyfx.util.alpha_composite(rgba,protect)

            return out

        else:
            return processed_img

    def _interpolate_waypoints(self,window_len=0):
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

            try:
                float(values[0])

                # booleans should not be interpolated ...
                if type(values[0]) in [np.bool_,bool]:
                    raise ValueError

                values = np.array(values)
                interpolator = interpolate.interp1d(times,values,kind="linear")
                interpolated = interpolator(self.t)
                smoothed = pyfx.util.helper.smooth(interpolated,window_len=window_len)

                self.__dict__[k] = smoothed

            # If the value cannot be readily converted into a float, do not
            # interpolate, just repeat the value of the parameter over and
            # over.
            except (TypeError,ValueError):

                out = []
                tmp_waypoint_times = waypoint_times[:]
                this_t = tmp_waypoint_times.pop(0)
                for i in range(self._workspace.max_time + 1):
                    if i == tmp_waypoint_times[0]:
                        this_t = tmp_waypoint_times.pop(0)
                    out.append(self._waypoints[this_t][k])

                self.__dict__[k] = out
                continue


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
