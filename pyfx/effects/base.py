
import copy

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

    def render(self,img):
        return img

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
