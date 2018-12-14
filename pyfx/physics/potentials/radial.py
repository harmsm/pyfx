
from .base import Potential
import numpy as np

class Radial(Potential):

    def __init__(self,center_coord,dimensions=(1080,1920),
                 pot_mag=1.0,min_r=2,kT=1):
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
        self._min_r = min_r

        super().__init__(kT)

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

    def sample_coord(self,particle_charge=1.0,max_tries=500):

        # Sample a radius from the Boltzmann-weighted possibilities
        r = self._possible_r[np.random.choice(self._p_indexes,p=self._p)]

        # Really a hack, but make sure that we end up with a particle that
        # is within the desired dimensions
        not_found = True
        counter = 0
        while not_found and counter < max_tries:

            # Grab a random theta
            theta = 2*np.pi*np.random.random()

            # calculate x and y
            x = self._center_coord[0] + np.cos(theta)*r
            y = self._center_coord[1] + np.sin(theta)*r

            if x > 0 and x < self._dimensions[0] and y > 0 and y < self._dimensions[1]:
                not_found = False

            counter += 1

        if not_found:
            return np.array((np.nan,np.nan))

        return np.array((x,y))

    def get_energy(self,coord,particle_charge=1.0):

        r = np.sqrt(np.sum((coord - self._center_coord)**2))

        if r == 0:
            E = np.nan
        else:
            E = self._pot_mag*particle_charge/r

        return E

    def get_forces(self,coord,particle_charge=1.0):

        r = np.sqrt(np.sum((coord - self._center_coord)**2))

        # To avoid an explosion in potential, the shortest possible distnace
        # is set to min_r
        force_r = r
        if force_r < self._min_r:
            force_r = self._min_r
        force_in_r = self._pot_mag*particle_charge*(1/force_r**2)

        # Fx = Fr*x/r (similar triangle), Fy = Fr*y/r.  Signs shake out
        # by coord - center_coord.
        F = force_in_r*(coord - self._center_coord)/r

        return F
