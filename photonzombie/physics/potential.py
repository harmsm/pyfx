
import numpy as np
from scipy import interpolate

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

class RadialRadial(Potential):

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



class EmpiricalPotential(Potential):
    """
    """

    def __init__(self,obs_potential,kT=1):

        self._dimensions = np.copy(obs_potential.shape)

        super(self).__init__(kT)

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
            self._potential = interpolate.RectBivariateSpline(x,y,pot)

        self._w = np.exp(-self._potential/self._kT)
        self._p = np.ravel(self._w)/np.sum(self._w)
        self._p_indexes = np.array(range(len(self._p)),dtype=np.int)

    def sample_coord(self):
        """
        Return a set of coordinates sampled from the Boltzmann-weighted
        potential surface.
        """

        position = np.random.choice(self._p_indexes,p=self._p)
        y_coord = np.mod(position,self._w.shape[1])
        x_coord = np.int((position - y_coord)/self._w.shape[1])

        return x_coord, y_coord

    def get_forces(self,coord):
        """
        Return force applied in x and y at position x,y.
        """

        Fx = -self._potential(coord[0],coord[1],dx=1)
        Fy = -self._potential(coord[0],coord[1],dy=1)

        return np.array((Fx,Fy))
