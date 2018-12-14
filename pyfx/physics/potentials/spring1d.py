
from .base import Potential
import numpy as np

class Spring1D(Potential):
    """
    1D harmonic potential.
    """

    def __init__(self,minimum=0,spring_constant=1.0,kT=1.0,max_r=2000):
        """
        minimum: equilibrium spring length
        spring_constant: stiffness of spring
        kT: energy scale
        max_r: maximum r to consider
        """

        self._minimum = minimum
        self._spring_constant = spring_constant
        self._max_r = max_r

        super().__init__(kT)

        self.update()

    def update(self,minimum=None,spring_constant=None,max_r=None):

        if minimum is not None:
            self._minimum = minimum

        if spring_constant is not None:
            self._spring_constant = spring_constant

        if max_r is not None:
            self._max_r = max_r

        self._possible_r = np.linspace(-self._max_r,self._max_r,500)

        U = 0.5*self._spring_constant*(self._possible_r)**2

        self._w = np.exp(-U/self._kT)
        self._p = self._w/np.sum(self._w)
        self._p_indexes = np.array(range(len(self._p)),dtype=np.int)

    def sample_coord(self,max_tries=500):

        # Sample a value from the Boltzmann-weighted possibilities
        r = self._possible_r[np.random.choice(self._p_indexes,p=self._p)]

        return r + self._minimum

    def get_energy(self,position):

        r = position - self._minimium

        return 0.5*self._spring_constant*(r**2)

    def get_forces(self,position):

        r = position - self._minimum

        return -self._spring_constant*r
