
from .base import Processor

import os, shutil, pickle, inspect, json

class DiffPotential(Processor):

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

        self._initialize()

        self._baked = False

    def _initialize(self):
        """
        Initialize class.
        """

        self._json_file = os.path.join(self._processor_dir,"param.json")
        if not os.path.isdir(self._processor_dir):
            os.mkdir(self._processor_dir)

            f = open(self._json_file,"r")
            self._params = json.load(f)
            f.close()

        else:
            print(self.__class__.__name__,"processor will use existing directory")

            f = open(self._json_file,"w")
            json.dump(self._params,f)
            f.close()

    def bake(self):

        self._pot_files = []
        max_digits = str(len(str(workspace.max_time)))
        fmt_string = "{:0" + max_digits + "d}.pickle"

        self._potential_files = {}
        self._img_files = {}

        current_file = None
        for t in workspace.times:

            if t % self._params["update_interval"] == 0 or current_file = None:
                current_file = os.path.join(self._processor_dir,
                                            fmt_string.format(t))
                current_image = self._workspace.get_frame(t,as_file=True)

            self._potential_files[t] = current_file
            self._img_files[t] = current_image

        self._baked = True

    def get_frame(self,t):

        pot_file = self._potential_files[t]

        # If already calculated, return
        if os.path.isfile(pot_file):
            return pickle.load(open(pot_file,"rb"))

        print("calculating potential surface for frame {}",t)
        diff_smooth = workspace.background.smooth_diff(self._img_files[t],
                                                       threshold=self._params["threshold"],
                                                       num_iterate=self._params["num_iterate"],
                                                       dilation_interval=self._params["dilation_interval"],
                                                       disk_size=self._params["disk_size"],
                                                       blur=self._params["blur"])
        pot = pyfx.physics.potentials.Empirical(diff_smooth,kT=self._params["kT"])

        # Write out, so we do not have to calculate again
        pickle.dump(pot,open(pot_file,"wb"))

        return pot
