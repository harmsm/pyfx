
from . import physics
from . import sprites

class ParticleCollection:
    """
    """

    def __init__(self,
                 hue=0.5,
                 dimensions=(1080,1920),
                 radius_pareto=1.0,
                 radius_max=100,
                 intensity_pareto=1.0,
                 intensity_max=100):

        self._hue = hue
        self._dimensions = np.array(dimensions,dtype=np.int)
        self._radius_pareto = radius_pareto
        self._radius_max = radius_max
        self._intensity_pareto = intensity_pareto
        self._intensity_max = intensity_max

        self._num_particles = 0
        self._particles = []
        self.potentials = []

    def construct_particles(self,num_particles=50,use_potential=0,
                            num_equilibrate_steps=0):
        """
        Populate list of particles.

        num_particles: how many particles to create
        use_potential: which potential to sample from to generate x,y
                       coordinates of the particles. If less than one,
                       do not use a potential -- choose randomly.  If there
                       is no potential loaded, also sample randomly.
        """

        self._num_particles = num_particles

        for i in range(self._num_particles):

            # Generate random radius (sampling from Pareto scale-free
            # distribution)
            radius = np.random.pareto(self._radius_pareto) + 1.0
            if radius > self._radius_max:
                radius = self._radius_max

            # Generate random intensity (sampling from Pareto scale-free
            # distribution)
            intensity = np.random.pareto(self._intensity_pareto) + 1.0
            if intensity > self._intensity_max:
                intensity = self._intensity_max
            intensity = intensity/self._intensity_max

            # Generate x,y coordinates for the particle
            if len(self.potentials) > 0 and use_potential >= 0:
                x, y = self.potentials[use_potential].sample_coord()
            else:
                x = np.random.choice(range(self._dimensions[0]))
                y = np.random.choice(range(self._dimensions[1]))

            # Generate a physical particle and sprite
            p = physics.Particle(x,y,radius=radius)
            sprite = sprites.GlowingParticle(radius,intensity,self._hue)

            self._particles.append((p,sprite))

        # equilibrate
        for i in range(num_equilibrate_steps):
            self.advance_time()

    def advance_time(self,dt=1.0):

        for p in self._particles:

            forces = np.array([0.0,0.0],dtype=np.float)
            for pot in self.potentials:
                forces += pot.get_forces(p[0].coord)
            p[0].advance_time(forces,dt)

    def write_out(self):
        """
        Write out sprites to an image array.
        """

        out_array = np.zeros((self._dimensions[0],self._dimensions[1],4),
                              dtype=np.uint8)
        for p in self._particles:
            out_array = p[1].write_to_image(out_array)

        return out_array
