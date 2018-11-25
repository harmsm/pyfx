
import numpy as np
from . import Background, Particle

def _coarse_grain(some_array,coarseness=5):

    # Figure out dimensions of final array (multiple of coarseness)
    shape = np.array(some_array.shape, dtype=float)
    new_shape = coarseness * np.ceil(shape / coarseness).astype(int)

    # Create the zero-padded array and assign it with the old density
    density = np.zeros(new_shape)
    density[:some_array.shape[0], :some_array.shape[1]] = some_array

    # Average each block
    temp = density.reshape((new_shape[0] // coarseness, coarseness,
                            new_shape[1] // coarseness, coarseness))

    x = np.arange(0,new_shape[0],coarseness) + coarseness/2
    y = np.arange(0,new_shape[1],coarseness) + coarseness/2
    x, y = np.meshgrid(x,y,indexing="ij")

    coord = np.stack((x.ravel(),y.ravel())).T

    return coord, np.sum(temp, axis=(1,3))


class World:
    """
    Keeps track of particles, integrates with time.
    """

    def __init__(self,bg_file,force_scale=1):

        self._bg_file = bg_file
        self._bg = Background(self._bg_file)
        self._force_scale = force_scale

    def _add_particle(self):
        """
        Add a particle, choosing its location based on the Boltzmann weight.
        """

        position = np.random.choice(self._p_indexes,p=self._p)
        y_coord = np.mod(position,self._w.shape[1])
        x_coord = np.int((position - y_coord)/self._w.shape[1])

        self._particles.append(Particle())
        self._particles[-1].create_particle(x_coord,y_coord)

    def _update_potential(self,new_img):
        """
        Load in a new diff_array and populate the boltzmann weights.

        self._w: boltzmann weights
        self._p: boltzmann weighted probabilities
        self._field: coarse-grained field of boltzmann weighted probability
        self._field_coord: x-y coordinates of center of each cell
        """

        self._diff_array = self._bg.get_frame_diff(new_img)

        self._w = np.exp(self._beta*self._diff_array)
        self._p = np.ravel(self._w)/np.sum(self._w)

        self._coarseness = np.int(np.ceil(self._coarse_grain*np.max(self._bg.bw.shape)))

        x, z = _coarse_grain(self._w,self._coarseness)

        self._field_coord = np.copy(x)
        self._field = z.ravel()

    def _update_forces(self):
        """
        """

        for i, p in enumerate(self._particles):

            # Difference in coordinates
            d_coord = self._field_coord - p.coord
            d_coord_sq = d_coord**2
            r_sq = np.sum(d_coord_sq,1)

            x_sq = r_sq - d_coord_sq[:,1]
            y_sq = r_sq - d_coord_sq[:,0]

            x_sign = 2.0*((d_coord[:,0] > 0) - 0.5)
            y_sign = 2.0*((d_coord[:,1] > 0) - 0.5)

            force = self._force_scale*self._beta*np.log(self._field)/r_sq

            force_x = np.sum(x_sign*force*np.sqrt(x_sq/r_sq))
            force_y = np.sum(y_sign*force*np.sqrt(y_sq/r_sq))

            # Update force
            p.add_force(np.array((force_x,force_y)))

    def create_particles(self,
                         start_frame_file,
                         particle_density=1e-5,
                         beta=10,
                         num_particles=None,
                         coarse_grain=0.05):

        self._start_frame_file = start_frame_file
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


    def advance_time(self,new_img=None):

        # Update images
        if new_img is not None:
            self._update_potential(new_img)

        self._update_forces()
        self._particle_coords = np.zeros((len(self._particles),2),
                                         dtype=np.float)
        for i, p in enumerate(self._particles):
            p.advance_time()
            self._particle_coords[i,:] = p.coord


    def write_out(self):

        out_array = np.zeros((self._bg.bw.shape[0],
                              self._bg.bw.shape[1],4),dtype=np.uint8)
        for p in self._particles:
            out_array = p.write_to_image(out_array)

        return out_array
