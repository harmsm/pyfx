
import numpy as np
from . import Background, Particle
from . import util

from scipy import interpolate

class Potential:
    """
    Keeps track of particles, integrates with time.
    """

    def __init__(self,obs_potential,force_scale=1,kT=1,dt=1):

        self._dimensions = np.copy(obs_potential.shape)
        self._force_scale = force_scale
        self._kT = kT
        self._dt = dt

        self._x_grid = np.array(range(self._dimensions[0]),dtype=np.int)
        self._y_grid = np.array(range(self._dimensions[1]),dtype=np.int)

        self.update_potential(obs_potential)

    def update_potential(self,obs_potential):
        """
        Load in a new potential.

        obs_potential should be a 2D array of a potential.

        self._potential is a spline approximation of the observed potential
        self._w: boltzmann weights
        self._p: boltzmann weighted probabilities (as a 1D array)
        """

        self._obs_potential = obs_potential
        self._potential = interpolate.RectBivariateSpline(x,y,pot)

        self._w = np.exp(-self._potential/self._kT)
        self._p = np.ravel(self._w)/np.sum(self._w)
        self._p_indexes = np.array(range(len(self._p)))

    def sample_coord(self):
        """
        Return a set of coordinates sampled from the Boltzmann-weighted
        potential surface.
        """

        position = np.random.choice(self._p_indexes,p=self._p)
        y_coord = np.mod(position,self._w.shape[1])
        x_coord = np.int((position - y_coord)/self._w.shape[1])

        return np.array((x_coord,y_coord))

    def get_forces(self,x,y):
        """
        Return force applied in x and y at position x,y.
        """

        Fx = -self._potential(x,y,dx=1)
        Fy = -self._potential(x,y,dy=1)

        return np.array((Fx,Fy))
