__description__ = \
"""
Collection of glowing particles that respond to underlying potentials.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-11-29"

from . import physics
from . import sprites

import numpy as np

class GlowingParticles:
    """
    Glowing particle effect creates a collection of glowing particles that
    can respond to underlying potential(s) defined in the physics submodule.
    """

    def __init__(self,
                 hue=0.5,
                 dimensions=(1080,1920),
                 velocity_sd=1.0,
                 particle_density=0.01,
                 radius_pareto=1.0,
                 radius_max=5,
                 intensity_pareto=1.0,
                 intensity_max=10):
        """
        hue: particle hue (0 to 1 scale)
        dimensions: size of frame where particles may be placed
        velocity_sd: standard deviation of the velocity distribution for initial
                     particle placement
        particle_density: density of each particle (for relating radius to
                          mass)
        radius_pareto: pareto shape parameter for the distribution used to
                       sample particle radii
        radius_max: maximum radius
        intensity_pareto: pareto shape parameter for particle glow intensity
        intensity_max: maximum particle glow intensity
        """

        self._hue = hue
        self._dimensions = np.array(dimensions,dtype=np.int)
        self._velocity_sd = velocity_sd
        self._particle_density = particle_density
        self._radius_pareto = radius_pareto
        self._radius_max = radius_max
        self._intensity_pareto = intensity_pareto
        self._intensity_max = intensity_max

        self._num_particles = 0
        self._particles = []
        self.potentials = []

    def purge_invisible(self,replace=False,use_potential=0,num_equilibrate_steps=0):
        """
        Remove particles that have moved off screen.

        replace: replace the particle with a randomly generated new one (bool)
        use_potential: if replacing, sample from the specified potential
        num_equilibrate_steps: if replacing, equilibrate the new particle for
                               num_equilibrate steps
        """

        for i in range(self._num_particles-1,-1,-1):
            if self._particles[i][1].out_of_frame:

                if replace:
                    self._particles[i] = self._generate_random_particle(use_potential,
                                                                        num_equilibrate_steps)
                else:
                    self._particles.pop(i)

        self._num_particles = len(self._particles)

    def construct_particles(self,num_particles=50,use_potential=0,
                            num_equilibrate_steps=0):
        """
        Populate list of particles.

        num_particles: how many particles to create
        use_potential: which potential to sample from to generate x,y
                       coordinates of the particles. If less than one,
                       do not use a potential -- choose randomly.  If there
                       is no potential loaded, also sample randomly.
        num_equilibrate_steps: number of steps of equilibration after particle
                               placement
        """

        self._num_particles = num_particles

        for i in range(self._num_particles):

            self._particles.append(self._generate_random_particle(use_potential,
                                                                  num_equilibrate_steps))

    def advance_time(self,dt=1.0,num_steps=1):
        """
        Take time step(s).

        dt: time step size.
        num_steps: number of steps to take
        """

        for p in self._particles:
            self._apply_foces(p[0],dt,num_steps)

    def write_out(self):
        """
        Write out sprites to an image array (0-255).
        """

        out_array = np.zeros((self._dimensions[0],self._dimensions[1],4),
                              dtype=np.uint8)
        for p in self._particles:
            out_array = p[1].write_to_image(p[0]._coord,out_array)

        return out_array

    def _generate_random_particle(self,use_potential=0,num_equilibrate_steps=0):
        """
        Generate a new particle.

        use_potential: which potential to use to sample from
        num_equilibrate_steps: number of time steps to equilibrate the particle
        """

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

        # Generate x,y coordinates for the particle (sampling from potential
        # or random)
        if len(self.potentials) > 0 and use_potential >= 0:
            coord = self.potentials[use_potential].sample_coord()
        else:
            x = np.random.choice(range(self._dimensions[0]))
            y = np.random.choice(range(self._dimensions[1]))
            coord = np.array((x,y))

        # Generate random velocity (sampling from a normal distribution)
        velocity = np.random.normal(0,self._velocity_sd,2)

        # Generate a physical particle
        p = physics.Particle(coord,velocity=velocity,radius=radius,
                             density=self._particle_density)

        # Equilibrate the physical particle
        if num_equilibrate_steps > 0:
            self._apply_foces(p,num_steps,num_equilibrate_steps)

        # Generate the sprite
        sprite = sprites.GlowingParticle(radius,intensity,self._hue)

        return p, sprite

    def _apply_foces(self,particle,dt=1.0,num_steps=1):
        """
        Apply forces to a particle.

        particle: physics.Particle instance
        dt: time step
        num_steps: number of steps
        """

        for i in range(num_steps):
            forces = np.array([0.0,0.0],dtype=np.float)
            for pot in self.potentials:
                forces += pot.get_forces(particle.coord)
            particle.advance_time(forces,dt)
