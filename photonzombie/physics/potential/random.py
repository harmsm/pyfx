
from .base import Potential
import numpy as np

class Random(Potential):
    """
    Apply a random force, drawn from a normal distribution. (Langevin style).
    """

    def __init__(self,dimensions=(1080,1920),force_sd=1.0,kT=1):
        """
        force_vector is the x and y terminii of a vector starting at 0,0
        """

        self._dimensions = np.array(dimensions)
        self._force_sd = force_sd

        super().__init__(kT)

    def update(self,force_sd):
        """
        Load in a new potential.
        """

        self._force_sd = force_sd

    def sample_coord(self):
        """
        Return a set of coordinates sampled from the Boltzmann-weighted
        potential surface.
        """

        x_coord = np.random.choice(range(self._dimensions[0]))
        y_coord = np.random.choice(range(self._dimensions[1]))

        return np.arary((x_coord, y_coord))

    def get_energy(self,coord):

        return 0.0

    def get_forces(self,coord):
        """
        Return random force.
        """

        return np.random.normal(0,force_sd,2)
