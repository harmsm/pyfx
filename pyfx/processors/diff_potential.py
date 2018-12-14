
from .base import Processor

import os, shutil, pickle

class DiffPotential(Processor):

    def __init__(self):

        super().__init__()

    def process(self,
                workspace,
                overwrite=False,
                kT=1.0,
                update_interval=5,
                threshold=0.2,
                num_iterate=20,
                dilation_interval=2,
                disk_size=35,
                blur=50):

        diff_dir = os.path.join(workspace.name,"diff_pot")
        if not os.path.isdir(diff_dir):
            os.mkdir(diff_dir)
        else:
            if overwrite:
                shutil.rmtree(diff_dir)
                os.mkdir(diff_dir)
            else:
                err = "Could not make {}. Directory exists\n"
                raise FileExistsError(err)

        for t in workspace.times:

            if t % update_interval != 0:
                continue

            print("calculating potential surface for frame {}",t)

            img = self.get_frame(t)
            diff_smooth = self._bg.smooth_diff(img)
            pot = pyfx.physics.potential.Empirical(diff_smooth)

            frame_diff = background.frame_diff(img_list[i])
            pot = self._construct_potential(frame_diff)

            out_file = os.path.join(diff_dir,"{:10d}.pickle".format(t))

            pickle.dump(pot,out_file)
