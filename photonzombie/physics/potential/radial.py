
from .base import Potential
import numpy as np

class Radial(Potential):

    def __init__(self,center_coord,dimensions=(1080,1920),
                 pot_mag=1.0,r_min=2,kT=1):
        """
        For a positively charged particle:
            pot_mag > 0 -> repulsive; pot_mag < 0 -> attractive
        """

        try:
            if len(center_coord) != 2:
                raise TypeError
        except TypeError:
            err = "center_coord must be list-like and have a length of 2\n"
            raise ValueError(err)
        self._center_coord = np.array(center_coord,dtype=np.float)

        try:
            if len(dimensions) != 2:
                raise TypeError
        except TypeError:
            err = "dimensions must be list-like and have a length of 2\n"
            raise ValueError(err)
        self._dimensions = np.array(dimensions,dtype=np.int)

        self._pot_mag = pot_mag
        self._r_min = r_min

        super(self).__init__(kT)

        self.update()

    def update(self,center_coord=None,pot_mag=None):

        if center_coord is not None:
            self._center_coord = np.array(center_coord)

        if pot_mag is not None:
            self._pot_mag = pot_mag

        self._max_r = np.max(np.abs(self._dimensions - self._center_coord))
        self._possible_r = np.linspace(self._min_r,self._max_r,500)

        U = self._pot_mag/self._possible_r

        self._w = np.exp(-U/self._kT)
        self._p = self._w/np.sum(self._w)
        self._p_indexes = np.array(range(len(self._p)),dtype=np.int)

    def sample_coord(self,particle_charge=1.0):

        # Sample a radius from the Boltzmann-weighted possibilities
        r = self._possible_r[np.random.choice(self._p_indexes,p=self._p)]

        # Grab a random theta
        theta = 2*np.pi*np.random.random()

        # calculate x and y
        x = np.cos(theta)*r
        y = np.sin(theta)*r

        return np.array(x,y)

    def get_forces(self,coord,particle_charge=1.0):

        r = np.sqrt(np.sum((coord - self._center_coord)**2))

        # To avoid an explosion in potential, the shortest possible distnace
        # is set to min_r
        force_r = r
        if force_r < self._r_min:
            force_r = self._r_min
        force_in_r = -self._pot_mag*particle_charge*(1/force_r**2)

        # Fx = Fr*x/r (similar triangle), Fy = Fr*y/r.  Signs shake out
        # by coord - center_coord.
        F = force_in_r*(coord - self._center_coord)/r

        return F
