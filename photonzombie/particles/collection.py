
import numpy as np
from . import Background, Particle
from . import util

from scipy import interpolate

class ParticleCollection:
    """
    Keeps track of particles, integrates with time.
    """

    def __init__(self,dimensions=(1080,1920),force_scale=1,kT=1,dt=1):

        self._dimensions = np.array(dimensions,dtype=np.int)
        if len(self._dimensions) != 2 or np.sum(dimensions > 0) != 2
            err = "dimensions must be list-like with 2 positive entries\n"
            raise ValueError(err)

        self._force_scale = force_scale
        self._kT = kT
        self._dt = dt

        self._x_grid = np.array(range(self._dimensions[0]),dtype=np.int)
        self._y_grid = np.array(range(self._dimensions[1]),dtype=np.int)

    def _add_particle(self):
        """
        Add a particle, choosing its location based on the Boltzmann weight
        of the potential surface.
        """

        position = np.random.choice(self._p_indexes,p=self._p)
        y_coord = np.mod(position,self._w.shape[1])
        x_coord = np.int((position - y_coord)/self._w.shape[1])

        self._particles.append(Particle())
        self._particles[-1].create_particle(x_coord,y_coord)

    def _update_potential(self,obs_potential):
        """
        Load in a new potential.

        self._w: boltzmann weights
        self._p: boltzmann weighted probabilities
        self._field: coarse-grained field of boltzmann weighted probability
        self._field_coord: x-y coordinates of center of each cell
        """

        self._obs_potential = obs_potential
        self._potential = interpolate.RectBivariateSpline(x,y,pot)

        self._w = np.exp(-self._potential/self._kT)
        self._p = np.ravel(self._w)/np.sum(self._w)

        #self._coarseness = np.int(np.ceil(self._coarse_grain*np.max(self._dimensions)))
        #x, z = util.coarse_grain(self._w,self._coarseness)
        #self._field_coord = np.copy(x)
        #self._field = z.ravel()

    def create_particles(self,
                         potential=None,
                         beta=10,
                         num_particles=None,
                         particle_density=1e-5,
                         coarse_grain=0.05):
        """
        Create an initial collection of particles.

        potential: a potential surface (2D array of floats) or None.  If None,
                   a uniform potential of 0 is used.
        beta: inverse temperature (1/kT)
        num_particles: number of particles to add (integer) or None.  If None,
                       particles are added using the particle_density.  If
                       num_particles is specified, particle_density is ignored.
        particle_density: number of particles to add per potential per area.
                          Ignored if num_particles is set.
        coarse_grain: degree to coarse-grain potential.  Float between 0 and 1.
                      A value of 0.05 means potential will be broken into blocks
                      5% of the size of the longest dimension, and then the
                      average potential for that block assigned.
        """

        self._potential = potential
        if potential is None:
            self._potential = np.zeros(self._dimensions,dtype=np.float)

        self._particle_density = particle_density
        self._beta = beta
        self._num_particles = num_particles
        self._coarse_grain = coarse_grain

        # Create arrays for selecting Boltzmann-weighted coordinates
        self._update_potential(start_frame_file)
        self._p_indexes = np.array(range(len(self._p)))

        # How many particles to create (based on how different this image
        # is from background)
        if self._num_particles is None:
            self._num_particles = np.int(np.round(self._particle_density*np.sum(self._w)))

        self._particles = []
        for i in range(self._num_particles):
            self._add_particle()


    def advance_time(self,new_potential=None):
        """
        Take a time step.  If new_potential is not None, calculate the forces
        on the particles using this new potential.
        """

        # Update images
        if new_potential is not None:
            self._update_potential(new_potential)

        #self._particle_coords = np.zeros((len(self._particles),2),
        #                                 dtype=np.float)

        for i, p in enumerate(self._particles):

            Fx = -self._potential(p.coord[0],p.coord[1],dx=1)
            Fy = -self._potential(p.coord[0],p.coord[1],dy=1)

            ## ADD POINT SOURCE INTERACTION HERE
            ## ADD LANGEVIN DYNAMICS HERE

            p.advance_time(np.array((Fx,Fy)))

            #self._particle_coords[i,:] = p.coord


            # Difference in coordinates
            #d_coord = self._field_coord - p.coord
            #d_coord_sq = d_coord**2
            #r_sq = np.sum(d_coord_sq,1)

            #x_sq = r_sq - d_coord_sq[:,1]
            #y_sq = r_sq - d_coord_sq[:,0]

            #x_sign = 2.0*((d_coord[:,0] > 0) - 0.5)
            #y_sign = 2.0*((d_coord[:,1] > 0) - 0.5)

            #force = self._force_scale*self._beta*np.log(self._field)/r_sq

            #force_x = np.sum(x_sign*force*np.sqrt(x_sq/r_sq))
            #force_y = np.sum(y_sign*force*np.sqrt(y_sq/r_sq))


        #self._update_forces()


    def write_out(self):
        """
        Write out sprites to an image array.
        """

        out_array = np.zeros((self._dimensions[0],self._dimensions[1],4),
                              dtype=np.uint8)
        for p in self._particles:
            out_array = p.write_to_image(out_array)

        return out_array
