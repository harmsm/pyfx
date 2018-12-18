
from .base import Potential
import numpy as np
from scipy import interpolate

class Empirical(Potential):
    """
    """

    def __init__(self,obs_potential,kT=1):

        self._dimensions = np.copy(obs_potential.shape)
        if len(self._dimensions) != 2:
            err = "only two-dimensional arrays supported\n"
            raise ValueError(err)


        super().__init__(kT)

        self._x_grid = np.array(range(self._dimensions[0]),dtype=np.int)
        self._y_grid = np.array(range(self._dimensions[1]),dtype=np.int)

        self.update(obs_potential)

    def update(self,obs_potential=None):
        """
        Load in a new potential.

        obs_potential should be a 2D array of a potential.

        self._potential is a spline approximation of the observed potential
        self._w: boltzmann weights
        self._p: boltzmann weighted probabilities (as a 1D array)
        """

        if obs_potential is not None:
            self._obs_potential = obs_potential
            self._potential = interpolate.RectBivariateSpline(self._x_grid,
                                                              self._y_grid,
                                                              self._obs_potential)

        self._w = None
        self._p = None
        self._p_indexes = None

    def sample_coord(self):
        """
        Return a set of coordinates sampled from the Boltzmann-weighted
        potential surface.
        """

        # The weights have not been calculated for this potential -- calculate
        # them.
        if self._w is None:
            self._w = np.exp(-self._obs_potential/self._kT)
            self._p = np.ravel(self._w)/np.sum(self._w)
            self._p_indexes = np.array(range(len(self._p)),dtype=np.int)

        position = np.random.choice(self._p_indexes,p=self._p)
        y_coord = np.mod(position,self._w.shape[1])
        x_coord = np.int((position - y_coord)/self._w.shape[1])

        return np.array((x_coord, y_coord))

    def get_energy(self,coord):

        return self._potential(coord[0],coord[1])

    def get_forces(self,coord):
        """
        Return force applied in x and y at position x,y.
        """

        Fx = -self._potential(coord[0],coord[1],dx=1)
        Fy = -self._potential(coord[0],coord[1],dy=1)

        return np.array(np.array((Fx[0,0],Fy[0,0])))
