
import numpy as np

class Potential:

    def __init__(self,kT):

        if kT < 0:
            err = "kT must be positive\n"
            raise ValueError(err)
        self._kT = kT

    def update(self,*args,**kwargs):

        pass

    def sample_coord(self):

        return np.random.normal(0,1,2)

    def get_forces(self):

        return np.array([0,0],dtype=np.float)

    @property
    def kT(self):
        return self._kT

    @kT.setter
    def kT(self,kT):
        self._kT = kT
        self.update()
