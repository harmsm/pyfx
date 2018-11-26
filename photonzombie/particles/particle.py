__description__ = \
"""
"""

import numpy as np
from skimage import draw
import copy
import matplotlib

from . import util

class Particle:
    """
    """

    def __init__(self,kT=1,radius_pareto=1):

        self._kT = kT
        self._radius_pareto = radius_pareto

    def create_particle(self,x,y,radius=None,intensity=None):
        """
        Create a particle at position x,y.
        """

        self._coord = np.array((x,y),dtype=np.float)

        if radius is None:
            self._radius = util.random_pareto(self._radius_pareto)
        else:
            self._radius = radius

        self._mass = 4/3*np.pi*self._radius**3
        self._velocity = np.random.normal(0,2*self._kT,2)
        self._forces = np.array((0,0),dtype=np.float)

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

    def advance_time(self,forces=None,dt=1.0):

        if forces is None:
            self._forces = np.array((0.0,0.0),dtype=np.float)

        # dt is defined as 1
        self._accel  = self._forces/self._mass
        new_vel = self._accel*dt + self._velocity
        self._coord = (dt*dt)*self._accel/2 + (dt)*(self._velocity + new_vel)/2 + self._coord
        self._velocity = np.copy(new_vel)

    def write_to_image(self,img_matrix):
        """
        Write the sprite to an image.  By default, each write_to_image call
        advances the time step by one.
        """

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

    @property
    def coord(self):
        return self._coord
