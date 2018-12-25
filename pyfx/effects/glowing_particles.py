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
        hue: particle hue (0 to 1 scale)
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
        intensity_pareto: pareto shape parameter for particle glow intensity
        intensity_max: maximum particle glow intensity
        sample_which_potential: which potential to use when generating a new
                                particle. If less than one, do not use a
                                potential -- choose randomly.  If there
                                is no potential loaded, also sample randomly.
        purge: whether or not to purge invisible particles and replace them to
               keep the number of particles constant.
        """

        self._default_waypoint = {"num_particles":200,
                                  "potentials":[],
                                  "hue":0.5,
                                  "velocity_dist":1.0,
                                  "particle_density":0.01,
                                  "radius_pareto":1.0,
                                  "radius_max":5,
                                  "intensity_pareto":1.0,
                                  "intensity_max":10,
                                  "sample_which_potential":0,
                                  "num_equilibrate_steps":0,
                                  "purge":True}

        super().__init__(workspace)

    def bake(self,smooth_window_len=0):
        """
        smooth_window_len: length of window for interpolation
        """

        self._current_time = 0
        self._dimensions = self._workspace.shape

        self._interpolate_waypoints(smooth_window_len)

        self._sprite_generator = pyfx.visuals.sprites.GlowingParticleGenerator(hue=self.hue,
                                                          radius_pareto=self.radius_pareto[0],
                                                          radius_max=self.radius_max[0],
                                                          intensity_pareto=self.intensity_pareto[0],
                                                          intensity_max=self.intensity_max[0])

        self._particle_collection = pyfx.physics.ParticleCollection(num_particles=self.num_particles[0],
                                                       potentials=self.potentials[0],
                                                       velocity_dist=self.velocity_dist[0],
                                                       particle_density=self.particle_density[0],
                                                       radius_pareto=self.radius_pareto[0],
                                                       radius_max=self.radius_max[0],
                                                       sample_which_potential=self.sample_which_potential[0],
                                                       purge=self.purge[0],
                                                       num_equilibrate_steps=self.num_equilibrate_steps[0],
                                                       sprite_generator=self._sprite_generator)
        self._baked = True

    def render(self,img):

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        # Update the sprite generator
        self._sprite_generator.hue = self.hue[t]
        self._sprite_generator.intensity_pareto = self.intensity_pareto[t]
        self._sprite_generator.intensity_max = self.intensity_max[t]
        self._sprite_generator.radius_pareto = self.radius_pareto[t]
        self._sprite_generator.radius_max = self.radius_max[t]

        # Update the particle collection
        self._particle_collection.potentials = self.potentials[t]
        self._particle_collection.velocity_dist = self.velocity_dist[t]
        self._particle_collection.particle_density = self.particle_density[t]
        self._particle_collection.radius_pareto = self.radius_pareto[t]
        self._particle_collection.radius_max = self.radius_max[t]
        self._particle_collection.sample_which_potential = np.int(self.sample_which_potential[t])
        self._particle_collection.purge = self.purge[t]
        self._particle_collection.num_equilibrate_steps = self.num_equilibrate_steps[t]

        # Figure out how many time steps we need to take
        num_steps = (t - self._current_time)
        if num_steps < 0:
            err = "time cannot run backwards for this effect\n"
            err += "(try baking again before running.)\n"
            raise ValueError(err)
        self._current_time = t

        # Advance time for the particles
        self._particle_collection.advance_time(num_steps=num_steps)

        # Remove particles that are off screen
        if self.purge[t]:
            self._particle_collection.purge_invisible()

        # Add or subtract particles so we have the desired number
        target_num_particles = np.int(self.num_particles[t])
        if target_num_particles < 0:
            target_num_particles = 0
        self._particle_collection.equalize_particles(target_num_particles)

        # Construct the particle sprites
        out_array = np.zeros((self._dimensions[0],self._dimensions[1],4),
                              dtype=np.uint8)
        for p in self._particle_collection.particles:
            out_array = p[1].write_to_image(p[0]._coord,out_array)

        # Write out
        out_array[:,:,3] = out_array[:,:,3]*self.alpha[t]

        final = pyfx.util.alpha_composite(img,out_array)

        # Protect image, if requested
        final = self._protect(img,final)

        return final
