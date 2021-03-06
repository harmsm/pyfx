__description__ = \
"""
Class for managing a whole collection of particles.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-14"

import pyfx
import numpy as np

import copy

class ParticleCollection:
    """
    Manage a collection of particles interacting with potentials.
    """

    def __init__(self,
                 num_particles,
                 dimensions=(1920,1080),
                 potentials=[],
                 velocity_dist=1.0,
                 particle_density=0.01,
                 radius_pareto=1.0,
                 radius_max=5,
                 sample_which_potential=0,
                 purge=True,
                 num_equilibrate_steps=0,
                 sprite_generator=None):
        """
        num_particles: number of particles to add
        dimensions: dimensions of box
        potentials: list of physics.Potential instances
        velocity_dist: control velocity distribution for new particle creation.
                       Can take two different forms:
                       float: x and y same; mean of 0, sd of velocity_dist
                       list-like of 4 floats:
                            x_mean = velocity_dist[0]
                            x_sd = velocity_dist[1]
                            y_mean = velocity_dist[2]
                            y_sd = velocity_dist[3]
        particle_density: density of each particle (for relating radius to
                          mass)
        radius_pareto: pareto shape parameter for the distribution used to
                       sample particle radii
        radius_max: maximum radius
        sample_which_potential: which potential to use when generating a new
                                particle. If less than one, do not use a
                                potential -- choose randomly.  If there
                                is no potential loaded, also sample randomly.
        purge: whether or not to purge invisible particles and replace them to
               keep the number of particles constant.
        num_equilibrate_steps: number of steps to equilibrate each particle
                               after adding.
        sprite_generator: SpriteGenerator instance for creating new sprites.
                          If None, do not generate sprites
        """

        self.num_particles = num_particles
        self._dimensions = np.array(dimensions)
        self.potentials = copy.copy(potentials)
        self.velocity_dist = velocity_dist
        self.particle_density = particle_density
        self.radius_pareto = radius_pareto
        self.radius_max = radius_max
        self.sample_which_potential = sample_which_potential
        self.purge = purge
        self.num_equilibrate_steps = num_equilibrate_steps
        self.sprite_generator = sprite_generator

        self._particles = []

    def _generate_random_particle(self):
        """
        Generate a new particle.
        """

        # Generate random radius (sampling from Pareto scale-free
        # distribution)
        radius = np.random.pareto(self._radius_pareto) + 1.0
        if radius > self._radius_max:
            radius = self._radius_max

        # Generate x,y coordinates for the particle (sampling from potential
        # or random)
        if len(self.potentials) > 0 and self._sample_which_potential >= 0:
            coord = self.potentials[self._sample_which_potential].sample_coord()
        else:
            x = np.random.choice(range(self._dimensions[0]))
            y = np.random.choice(range(self._dimensions[1]))
            coord = np.array((x,y))

        # Generate random velocity (sampling from a normal distribution)
        vx = np.random.normal(self._velocity_dist[0],self._velocity_dist[1])
        vy = np.random.normal(self._velocity_dist[2],self._velocity_dist[3])
        velocity = np.array((vx,vy))

        # Generate a physical particle
        p = pyfx.physics.Particle(coord,velocity=velocity,radius=radius,
                                  density=self._particle_density)

        # Equilibrate particle, if requested
        if self._num_equilibrate_steps > 0:
            self.apply_forces(p,num_steps=self._num_equilibrate_steps)

        sprite = None
        if self._sprite_generator is not None:
            sprite = self._sprite_generator.create(radius=radius,
                                                   velocity=velocity)

        return p, sprite

    def construct_particles(self,num_particles=None):
        """
        Populate list of particles.
        """

        if num_particles is not None:
            self._num_particles = num_particles

        for i in range(self._num_particles):
            self._particles.append(self._generate_random_particle())

    def purge_invisible(self):
        """
        Remove particles that have moved off screen. If a sprite is defined,
        for the particle, use its out_of_frame property, as this accounts
        for the fact that the particle may have width.  If that is not
        defined, use the x,y coordinate of the particle.
        """

        for i in range(len(self._particles)-1,-1,-1):

            remove = False
            if self._particles[i][1] is not None:
                if self._particles[i][1].out_of_frame:
                    remove = True
            else:
                if np.min(self._particles[i][0].coord) < 0 or \
                   np.sum(self._particles[i][0].coord > self._dimensions) > 0:

                   remove = True

            if remove:
                self._particles.pop(i)

    def equalize_particles(self,target_num_particles):
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

    def advance_time(self,dt=1.0,num_steps=1):
        """
        Take time step(s).

        dt: time step size.
        num_steps: number of steps to take
        """

        for p in self._particles:
            self.apply_forces(p[0],dt,num_steps)

    def apply_forces(self,particle,dt=1.0,num_steps=1):
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

    @property
    def particles(self):
        return self._particles

    @property
    def num_particles(self):
        return self._num_particles

    @num_particles.setter
    def num_particles(self,num_particles):
        self._num_particles = int(round(num_particles))

    @property
    def velocity_dist(self):
        return self._velocity_dist

    @velocity_dist.setter
    def velocity_dist(self,velocity_dist):

        mangled = False
        new_velocity_dist = []
        try:
            if len(velocity_dist) == 4:
                # mean_x, sd_x, mean_y, sd_y; x and y different
                new_velocity_dist.append(velocity_dist[0])
                new_velocity_dist.append(velocity_dist[1])
                new_velocity_dist.append(velocity_dist[2])
                new_velocity_dist.append(velocity_dist[3])
            else:
                mangled = True
        except TypeError:

            # velocity_dist is a float --> give x and y mean velocities of zero
            # and standard deviations of velocity_dist
            try:
                velocity_dist = float(velocity_dist)
            except ValueError:
                mangled = True

            # mean_x = 0, sd_x, mean_y = 0, sd_y; x and y identical
            new_velocity_dist.append(0)
            new_velocity_dist.append(velocity_dist)
            new_velocity_dist.append(0)
            new_velocity_dist.append(velocity_dist)

        if new_velocity_dist[1] < 0 or new_velocity_dist[3] < 0:
            mangled = rue

        if mangled:
            err = "Uninterpretable velocity_dist.  This parameter should be a\n"
            err += "single float or list-like object of length 4.  standard \n"
            err += "deviations must be >= 0.\n"
            raise ValueError(err)

        # Store the values
        self._velocity_dist = np.array(new_velocity_dist,dtype=np.float)


    @property
    def particle_density(self):
        return self._particle_density

    @particle_density.setter
    def particle_density(self,particle_density):
        self._particle_density = float(particle_density)

    @property
    def radius_pareto(self):
        return self._radius_pareto

    @radius_pareto.setter
    def radius_pareto(self,radius_pareto):
        self._radius_pareto = float(radius_pareto)

    @property
    def radius_max(self):
        return self._radius_max

    @radius_max.setter
    def radius_max(self,radius_max):
        self._radius_max = float(radius_max)

    @property
    def sample_which_potential(self):
        return self._sample_which_potential

    @sample_which_potential.setter
    def sample_which_potential(self,sample_which_potential):
        self._sample_which_potential = int(sample_which_potential)

    @property
    def purge(self):
        return self._purge

    @purge.setter
    def purge(self,purge):
        self._purge = bool(purge)

    @property
    def num_equilibrate_steps(self):
        return self._num_equilibrate_steps

    @num_equilibrate_steps.setter
    def num_equilibrate_steps(self,num_equilibrate_steps):
        self._num_equilibrate_steps = int(num_equilibrate_steps)

    @property
    def sprite_generator(self):
        return self._sprite_generator

    @sprite_generator.setter
    def sprite_generator(self,sprite_generator):
        self._sprite_generator = sprite_generator
