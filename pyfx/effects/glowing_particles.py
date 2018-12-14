__description__ = \
"""
Collection of glowing particles that respond to underlying potentials.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-11-29"

import pyfx
from .base import Effect

import numpy as np

class GlowingParticles(Effect):
    """
    Glowing particle effect creates a collection of glowing particles that
    can respond to underlying potential(s) defined in the physics submodule.
    """

    def __init__(self,workspace):
        """
        workspace: the workspace associated with this effect

        num_particles: number of particles to add
        potentials: list of physics.Potential instances
        """

        self._default_waypoint = {"num_particles":200,
                                  "potentials":[]}

        super().__init__(workspace)

    def bake(self,
             hue=0.5,
             velocity_sd=1.0,
             particle_density=0.01,
             radius_pareto=1.0,
             radius_max=5,
             intensity_pareto=1.0,
             intensity_max=10,
             sample_which_potential=0,
             purge=True,
             smooth_window_len=30):
        """
        hue: particle hue (0 to 1 scale)
        velocity_sd: standard deviation of the velocity distribution for initial
                     particle placement
        particle_density: density of each particle (for relating radius to
                          mass)
        radius_pareto: pareto shape parameter for the distribution used to
                       sample particle radii
        radius_max: maximum radius
        intensity_pareto: pareto shape parameter for particle glow intensity
        intensity_max: maximum particle glow intensity
        sample_which_potential: which potential to use when generating a new
                                particle. If less than one, do not use a
                                potential -- choose randomly.  If there
                                is no potential loaded, also sample randomly.
        purge: whether or not to purge invisible particles and replace them to
               keep the number of particles constant.
        smooth_window_len: length of window for interpolation
        """

        self._hue = hue
        self._dimensions = self._workspace.shape
        self._velocity_sd = velocity_sd
        self._particle_density = particle_density
        self._radius_pareto = radius_pareto
        self._radius_max = radius_max
        self._intensity_pareto = intensity_pareto
        self._intensity_max = intensity_max
        self._sample_which_potential = sample_which_potential
        self._purge = purge

        self._current_time = 0

        self._interpolate_waypoints(smooth_window_len)

        self._particles = []

        self._baked = True

    def render(self,img):

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        # Figure out how many time steps we need to take
        num_steps = (t - self._current_time)
        if num_steps < 0:
            err = "time cannot run backwards for this effect\n"
            raise ValueError(err)
        self._current_time = t

        # Advance time for the particles
        self._advance_time(num_steps=num_steps)

        # Remove particles that are off screen
        if self._purge:
            self._purge_invisible()

        # Add or subtract particles so we have the desired number
        target_num_particles = self.num_particles[t]
        if target_num_particles < 0:
            target_num_particles = 0
        self._equalize_particles(target_num_particles)

        # Construct the particle sprites
        out_array = np.zeros((self._dimensions[0],self._dimensions[1],4),
                              dtype=np.uint8)
        for p in self._particles:
            out_array = p[1].write_to_image(p[0]._coord,out_array)

        # Write out
        out_array[:,:,3] = out_array[:,:,3]*self.alpha[t]
        return pyfx.util.alpha_composite(img,out_array)

    def _generate_random_particle(self):
        """
        Generate a new particle.
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
        if len(self.potentials[self._current_time]) > 0 and self._sample_which_potential >= 0:
            coord = self.potentials[self._current_time][self._sample_which_potential].sample_coord()
        else:
            x = np.random.choice(range(self._dimensions[0]))
            y = np.random.choice(range(self._dimensions[1]))
            coord = np.array((x,y))

        # Generate random velocity (sampling from a normal distribution)
        velocity = np.random.normal(0,self._velocity_sd,2)

        # Generate a physical particle
        p = pyfx.physics.Particle(coord,velocity=velocity,radius=radius,
                                  density=self._particle_density)

        # Generate the sprite
        sprite = pyfx.visuals.sprites.GlowingParticle(radius,intensity,self._hue)

        return p, sprite

    def _construct_particles(self,num_particles):
        """
        Populate list of particles.
        """
        for i in range(num_particles):
            self._particles.append(self._generate_random_particle())

    def _purge_invisible(self):
        """
        Remove particles that have moved off screen.
        """

        for i in range(len(self._particles)-1,-1,-1):
            if self._particles[i][1].out_of_frame:
                self._particles.pop(i)

    def _equalize_particles(self,target_num_particles):
        """
        Make sure the number of particles matches what is wanted.
        """

        difference = int(round(target_num_particles - len(self._particles)))
        if difference < 0:

            # We don't want any particles; nuke em all
            if target_num_particles == 0:
                self._particles = []
                return

            # Choose some random particles to remove
            indexes_to_remove = np.random.choice(range(len(self._particles)),
                                                 np.abs(difference),
                                                 replace=False)
            indexes_to_remove.sort()
            for i in indexes_to_remove.reverse():
                self._particles.pop(i)

        # Add particles
        elif difference > 0:
            for i in range(difference):
                self._particles.append(self._generate_random_particle())

        # Don't do anything if there is no difference.
        else:
            pass

    def _advance_time(self,dt=1.0,num_steps=1):
        """
        Take time step(s).

        dt: time step size.
        num_steps: number of steps to take
        """

        for p in self._particles:
            self._apply_forces(p[0],dt,num_steps)

    def _apply_forces(self,particle,dt=1.0,num_steps=1):
        """
        Apply forces to a particle.

        particle: physics.Particle instance
        dt: time step
        num_steps: number of steps
        """

        for i in range(num_steps):
            forces = np.array([0.0,0.0],dtype=np.float)
            for pot in self.potentials[self._current_time]:
                forces += pot.get_forces(particle.coord)
            particle.advance_time(forces,dt)
