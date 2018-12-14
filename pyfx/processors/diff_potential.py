
import pyfx

from .base import Processor

import os, shutil, pickle, inspect, json

class DiffPotential(Processor):
    """
    Workspace-aware class that updates a smooth potential depending on the
    workspace time.  It reproduces the physics.Potential methods, so Effects
    can access this time-dependent potential as though it is just some other
    potential.
    """

    def __init__(self,
                 workspace,
                 kT=1.0,
                 update_interval=5,
                 threshold=0.2,
                 num_iterate=20,
                 dilation_interval=2,
                 disk_size=35,
                 blur=50):

        super().__init__()

        self._workspace = workspace
        self._processor_dir = os.path.join(workspace.name,
                                           self.__class__.__name__)

        # Parse a generic set of kwargs and record as params
        kwarg_keys = inspect.getfullargspec(self.__init__)[0]
        kwarg_keys.remove("self")
        kwarg_keys.remove("workspace")

        local_variables = locals()
        self._params = dict([(k,local_variables[k]) for k in kwarg_keys])

        self._json_file = os.path.join(self._processor_dir,"param.json")
        if not os.path.isdir(self._processor_dir):
            os.mkdir(self._processor_dir)

            f = open(self._json_file,"w")
            json.dump(self._params,f)
            f.close()

        else:
            print(self.__class__.__name__,"processor will use existing directory")

            f = open(self._json_file,"r")
            self._params = json.load(f)
            f.close()

        self._last_retrieved_t = -1
        self._last_retrieved_pot = None

        self._baked = False


    def bake(self):

        self._pot_files = []
        max_digits = str(len(str(self._workspace.max_time)) + 2)
        fmt_string = "{:0" + max_digits + "d}.pickle"

        self._potential_files = {}
        self._img_files = {}

        current_file = None
        for t in self._workspace.times:

            if t % self._params["update_interval"] == 0 or current_file is None:
                current_file = os.path.join(self._processor_dir,
                                            fmt_string.format(t))
                current_image = self._workspace.get_frame(t,as_file=True)

            self._potential_files[t] = current_file
            self._img_files[t] = current_image

        self._baked = True

    def _update(self):
        """
        Update the potential given the current time in the workspace.
        """

        # If the last potential retrieved was this one, don't reload
        if self._workspace.current_time == self._last_retrieved_t:
            return

        if not self._baked:
            self.bake()

        t = self._workspace.current_time

        pot_file = self._potential_files[t]

        # If already calculated, return
        if os.path.isfile(pot_file):
            return pickle.load(open(pot_file,"rb"))

        print("calculating potential surface for frame {}".format(t))
        diff_smooth = self._workspace.background.smooth_diff(self._img_files[t],
                                                       threshold=self._params["threshold"],
                                                       num_iterate=self._params["num_iterate"],
                                                       dilation_interval=self._params["dilation_interval"],
                                                       disk_size=self._params["disk_size"],
                                                       blur=self._params["blur"])
        pot = pyfx.physics.potentials.Empirical(diff_smooth,kT=self._params["kT"])

        # Write out, so we do not have to calculate again
        pickle.dump(pot,open(pot_file,"wb"))

        # Keep the last pot that was retrieved/calculated in memory
        self._last_retrieved_t = t
        self._last_retrieved_pot = pot

    def sample_coord(self):

        self._update()
        return self._last_retrieved_pot.sample_coord()

    def get_energy(self,coord):

        self._update()
        return self._last_retrieved_pot.get_energy(coord)

    def get_forces(self,coord):

        self._update()
        return self._last_retrieved_pot.get_forces(coord)

    @property
    def kT(self):
        self._update()
        return self._last_retrieved_pot.kT

    @kT.setter
    def kT(self,kT):
        self._update()
        self._last_retrieved_pot.kT = kT
