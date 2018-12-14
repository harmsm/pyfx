
from .face_finder import find_face_stacks
from ..base import Processor

import pickle

class HumanFaces(Processor):
    """
    Find human faces using dlib.  Interpolate coordinates over short intervals
    in case the model misses a face in a frame or two.
    """

    def __init__(self):
        super().__init__()

    def process(self,
                workspace,
                training_data=None,
                max_time_gap=5,
                p_cutoff=0.9,
                real_cutoff=100,
                min_time_visible=5):

        if training_data is None:
            training_data = os.path.join(pyfx.root_dir,'data',
                                         'shape_predictor_68_face_landmarks.dat')

        img_list = []
        for t in workspace.times:
            img_list.append(workspace.get_frame(t,as_file=True))

        face_stacks = find_face_stacks(img_list=img_list,
                                       training_data=training_data,
                                       max_time_gap=max_time_gap,
                                       p_cutoff=p_cutoff,
                                       real_cutoff=real_cutoff,
                                       min_time_visible=min_time_visible)

        out_file = os.path.join(workspace.name,"face_stacks.pickle")
        pickle.dump(face_stacks,open(out_file,"wb"))
