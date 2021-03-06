import pyfx

import numpy as np
from PIL import Image

class Sprite:
    """
    Base class for all sprites.  (It is a 5x5 white square).  To define
    a new sprite, re-define __init__ (making sure to call super(self).__init__())
    and _build_sprite.
    """

    def __init__(self):
        """
        Initialize class.
        """

        self._out_of_frame = False
        self._build_sprite()

    def _build_sprite(self):
        """
        Construct a bitmap representation of this sprite.
        """

        # Create output image, RGBA
        self._sprite = np.zeros((5,5,4),dtype=np.uint8)
        self._sprite[:,:,:3] = 255
        self._sprite[:,:,3] = 255

    def write_to_image(self,coord,img_matrix):
        """
        Write the sprite to an image.
        """

        # Now figure out where this should go in the output matrix
        x_min = int(np.round(coord[1] - self._size - 1))
        x_max = x_min + self.sprite.shape[1]

        i_min = 0
        i_max = self.sprite.shape[1]

        y_min = int(np.round(coord[0] - self._size - 1))
        y_max = y_min + self.sprite.shape[0]

        j_min = 0
        j_max = self.sprite.shape[0]
        
        # Deal with x/i-bounds
        self._out_of_frame = False
        if x_min < 0:

            i_min = abs(x_min)
            if i_min >= self.sprite.shape[1]:
                self._out_of_frame = True
                return img_matrix
            x_min = 0

        if x_max >= img_matrix.shape[1]:

            i_max = i_max - (x_max - img_matrix.shape[1])
            if i_max <= 0:
                self._out_of_frame = True
                return img_matrix
            x_max = img_matrix.shape[1]

        # Deal with y/j-bounds
        if y_min < 0:

            j_min = abs(y_min)
            if j_min >= self.sprite.shape[0]:
                self._out_of_frame = True
                return img_matrix
            y_min = 0

        if y_max >= img_matrix.shape[0]:

            j_max = j_max - (y_max - img_matrix.shape[0])
            if j_max <= 0:
                self._out_of_frame = True
                return img_matrix
            y_max = img_matrix.shape[0]

        a = pyfx.util.alpha_composite(img_matrix[y_min:y_max,x_min:x_max,:],
                                      self.sprite[j_min:j_max,i_min:i_max,:])

        img_matrix[y_min:y_max,x_min:x_max] = a[:,:]

        return img_matrix


    @property
    def sprite(self):
        return self._sprite

    @property
    def out_of_frame(self):
        return self._out_of_frame
