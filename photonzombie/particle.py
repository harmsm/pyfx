__description__ = \
"""
"""

import numpy as np
from skimage import draw
import copy
import matplotlib

def _random_pareto(a,minimum=1,maximum=6):
    """
    Sample from a pareto distribution, forcing output to be between minimum
    and maximum.
    """

    b = np.random.pareto(a) + minimum
    if b > maximum:
        b = maximum

    return b

class Particle:
    """
    """

    def __init__(self,hue=0.5,
                 num_rings=8,expansion_factor=1.3,
                 alpha=1,alpha_decay=1):
        """
        hue: hue (0 to 1 scale)
        num_rings: how many rings to expand out from the point source
        expansion_factor: how much bigger each ring is than the previous ring
        alpha: maximum alpha for center of particle (0 to 1 scale)
        alpha_decay: multiply alpha by this value for each new ring
        """

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

        self._out_of_frame = False


    def create_particle(self,x,y,nearest=None,radius=None,intensity=None):
        """
        Create a particle at position x,y.
        """

        a = 1
        b = 1
        some_scale = 1

        self._coord = np.array((x,y),dtype=np.float)

        if nearest is None:
            self._nearest = np.random.normal(some_scale)
        else:
            self._nearest = nearest_neighor
        self._nearest = nearest

        if radius is None:
            self._radius = _random_pareto(a)
        else:
            self._radius = radius

        if intensity is None:
            self._intensity = _random_pareto(b,maximum=5)/5.0
        else:
            self._intensity = intensity

        self._velocity = np.random.normal(0,some_scale,2)

        self._build_sprite()

    def _build_sprite(self):
        """
        Construct a bitmap representation of this particle.
        """

        # Create mini array to draw object
        size = self._radius*(self._expansion_factor**(self._num_rings - 1)) + 3
        self._size = int(np.ceil(size))
        img = np.zeros((2*self._size + 1,2*self._size + 1),dtype=np.float)

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

    def _advance_time(self):

        self._coord = self._coord + self._velocity

    def write_to_image(self,img_matrix,advance=True):
        """
        Write the sprite to an image.  By default, each write_to_image call
        advances the time step by one.
        """

        # Update the particle position
        if advance:
            self._advance_time()

        # Now figure out where this should go in the output matrix
        x_min = int(np.round(self._coord[0] - self._size - 1))
        x_max = x_min + self.sprite.shape[0]
        y_min = int(np.round(self._coord[1] - self._size - 1))
        y_max = y_min + self.sprite.shape[1]

        i_min = 0
        i_max = self.sprite.shape[0]
        j_min = 0
        j_max = self.sprite.shape[1]

        # Deal with x/i-bounds
        if x_min < 0:

            i_min = abs(x_min)
            if i_min >= self.sprite.shape[0]:
                self._out_of_frame = True
                return img_matrix
            x_min = 0

        if x_max >= img_matrix.shape[0]:

            i_max = i_max - (x_max - img_matrix.shape[0])
            if i_max <= 0:
                self._out_of_frame = True
                return img_matrix
            x_max = img_matrix.shape[0]

        # Deal with y/j-bounds
        if y_min < 0:

            j_min = abs(y_min)
            if j_min >= self.sprite.shape[1]:
                self._out_of_frame = True
                return img_matrix
            y_min = 0

        if y_max >= img_matrix.shape[1]:

            j_max = j_max - (y_max - img_matrix.shape[1])
            if j_max <= 0:
                self._out_of_frame = True
                return img_matrix
            y_max = img_matrix.shape[1]

        # Update output matrix with the new output
        new_alpha = np.zeros((x_max-x_min,y_max-y_min),dtype=np.uint16)
        new_alpha[:,:] += img_matrix[x_min:x_max,y_min:y_max,3]
        new_alpha[:,:] += self.sprite[i_min:i_max,j_min:j_max,3]
        new_alpha[new_alpha>255] = 255

        img_matrix[x_min:x_max,y_min:y_max,:3] += self.sprite[i_min:i_max,j_min:j_max,:3]
        img_matrix[x_min:x_max,y_min:y_max,3] = new_alpha

        return img_matrix

    @property
    def sprite(self):
        return self._sprite

    @property
    def out_of_frame(self):
        return self._out_of_frame
