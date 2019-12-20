
from .base import Sprite

import matplotlib
import numpy as np
from skimage import draw, filters

class GlowingParticle(Sprite):

    def __init__(self,
                 radius=1,
                 intensity=1,
                 hue=0.5,
                 num_rings=8,
                 expansion_factor=1.3,
                 alpha=1,
                 alpha_decay=1):
        """
        radius: particle radius
        intensity: how brightly the particle glows (0 to 1 scale)
        hue: hue (0 to 1 scale)
        num_rings: how many rings to expand out from the point source
        expansion_factor: how much bigger each ring is than the previous ring
        alpha: maximum alpha for center of particle (0 to 1 scale)
        alpha_decay: multiply alpha by this value for each new ring
        """

        if radius < 0:
            err = "radius must be positive\n"
            raise ValueError(err)
        self._radius = radius

        if intensity < 0 or intensity > 1:
            err = "intensity must be between 0 and 1\n"
            raise ValueError(err)
        self._intensity = intensity

        if hue < 0 or hue > 1:
            err = "hue must be between 0 and 1\n"
            raise ValueError(err)
        self._hue = hue

        if num_rings < 1:
            err = "num_rings must be 1 or more.\n"
            raise ValueError(err)
        self._num_rings = num_rings

        if expansion_factor <= 1:
            err = "expansion factor must be > 1.\n"
            raise ValueError(err)
        self._expansion_factor = expansion_factor

        if alpha < 0 or alpha > 1:
            err = "alpha must be between 0 and 1\n"
            raise ValueError(err)
        self._alpha = alpha

        if alpha_decay <= 0:
            err = "alpha decay must be larger than 0\n"
            raise ValueError(err)
        self._alpha_decay = alpha_decay

        super().__init__()

    def _build_sprite(self):
        """
        Construct a bitmap representation of this particle.
        """

        # Create mini array to draw object
        size = self._radius*(self._expansion_factor**(self._num_rings - 1)) + 3
        self._size = int(np.ceil(size))
        img = np.zeros((2*self._size + 3,2*self._size + 3),dtype=np.float)

        # Find center of mini array for drawing
        center = self._size
        # Draw num_rings circles, expanding radius by expansion_factor each time
        # and dropping the alpha value by alpha_decay
        alpha = self._alpha
        radius = self._radius
        for i in range(self._num_rings):
            rr, cc = draw.circle(center,center,
                                 radius=radius)
            img[rr,cc] += alpha

            alpha = alpha*self._alpha_decay
            radius = int(round(radius*self._expansion_factor))

        # Blur
        img = filters.gaussian(img,sigma=self._radius)

        # Normalize the array so it ranges from 0 to 1
        img = img/np.max(img)*self._intensity

        # Hue is set by user, value fixed at one, saturation is determined by
        # intensity
        hue =   np.ones(img.shape,dtype=np.float)*self._hue
        value = np.ones(img.shape,dtype=np.float)
        saturation = 1 - img

        col = np.stack((hue,saturation,value),2)
        rgb = np.array(255*matplotlib.colors.hsv_to_rgb(col),dtype=np.uint8)

        # Create output image, RGBA
        self._sprite = np.zeros((img.shape[0],img.shape[1],4),dtype=np.uint8)
        self._sprite[:,:,:3] = 255*matplotlib.colors.hsv_to_rgb(col)
        self._sprite[:,:,3] = self._alpha*255*img

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self,radius):

        if radius < 0:
            err = "radius must be positive\n"
            raise ValueError(err)

        if self._radius != radius:
            self._radius = radius
            self._build_sprite()

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self,intensity):

        if intensity < 0 or intensity > 1:
            err = "intensity must be between 0 and 1\n"
            raise ValueError(err)

        self._intensity = intensity
        self._build_sprite()

    @property
    def hue(self):
        return self._hue

    @hue.setter
    def hue(self,hue):

        if hue < 0 or hue > 1:
            err = "hue must be between 0 and 1\n"
            raise ValueError(err)

        self._hue = hue
        self._build_sprite()

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self,alpha):

        if alpha < 0 or alpha > 1:
            err = "alpha must be between 0 and 1\n"
            raise ValueError(err)

        self._alpha = alpha
        self._build_sprite()

class GlowingParticleGenerator:

    def __init__(self,
                 hue=0.5,
                 radius_pareto=1.0,
                 radius_max=5,
                 intensity_pareto=1.0,
                 intensity_max=10):

        self._hue = hue
        self._radius_pareto = radius_pareto
        self._radius_max = radius_max
        self._intensity_pareto = intensity_pareto
        self._intensity_max = intensity_max

    def create(self,**kwargs):
        """
        This is built around **kwargs so a ParticleCollection instance can
        throw particle properties at it.
        """

        try:
            radius = kwargs["radius"]
        except KeyError:
            radius = np.random.pareto(self._radius_pareto) + 1.0
            if radius > self._radius_max:
                radius = self._radius_max

        # Generate random intensity (sampling from Pareto scale-free
        # distribution)
        intensity = np.random.pareto(self._intensity_pareto) + 1.0
        if intensity > self._intensity_max:
            intensity = self._intensity_max
        intensity = intensity/self._intensity_max

        return GlowingParticle(radius=radius,intensity=intensity,hue=self._hue)

    @property
    def hue(self):
        return self._hue
    @hue.setter
    def hue(self,hue):
        self._hue = hue

    @property
    def radius_pareto(self):
        return self._radius_pareto
    @radius_pareto.setter
    def radius_pareto(self,radius_pareto):
        self._radius_pareto = radius_pareto

    @property
    def radius_max(self):
        return self._radius_max
    @radius_max.setter
    def radius_max(self,radius_max):
        self._radius_max = radius_max

    @property
    def intensity_pareto(self):
        return self._intensity_pareto
    @intensity_pareto.setter
    def intensity_pareto(self,intensity_pareto):
        self._intensity_pareto = intensity_pareto

    @property
    def intensity_max(self):
        return self._intensity_max
    @intensity_max.setter
    def intensity_max(self,intensity_max):
        self._intensity_max = intensity_max
