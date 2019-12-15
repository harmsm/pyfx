
import pyfx

from .face_finder import find_face_stacks
from ..base import Processor

import pickle, os

class HumanFaces(Processor):
    """
    Find human faces using dlib.  Interpolate coordinates over short intervals
    in case the model misses a face in a frame or two.
    """

    def __init__(self,
                 videoclip,
                 training_data=None,
                 max_time_gap=5,
                 p_cutoff=0.9,
                 real_cutoff=100,
                 min_time_visible=5):

        self._videoclip = videoclip

        if training_data is None:
            self._training_data = os.path.join(pyfx.root_dir,'data',
                                               'shape_predictor_68_face_landmarks.dat')
        else:
            self._training_data = training_data

        self._max_time_gap = max_time_gap
        self._p_cutoff = p_cutoff
        self._real_cutoff = real_cutoff
        self._min_time_visible = min_time_visible

        self._baked = False

    def bake(self):
        """
        Find human faces across a collection of frames.
        """

        out_file = os.path.join(self._videoclip.name,"HumanFaces.pickle")

        self._img_list = []
        for t in self._videoclip.times:
            self._img_list.append(self._videoclip.get_frame(t))

        if os.path.isfile(out_file):
            f = open(out_file,'rb')
            self._face_stacks = pickle.load(f)
            f.close()

        else:
            print("Searching for human faces (slow, but only happens once).")
            self._face_stacks = find_face_stacks(img_list=self._img_list,
                                                 training_data=self._training_data,
                                                 max_time_gap=self._max_time_gap,
                                                 p_cutoff=self._p_cutoff,
                                                 real_cutoff=self._real_cutoff,
                                                 min_time_visible=self._min_time_visible)

            f = open(out_file,"wb")
            pickle.dump(self._face_stacks,f)
            f.close()

        self._baked = True

    @property
    def face_stacks(self):

        if not self._baked:
            self.bake()

        return self._face_stacks
