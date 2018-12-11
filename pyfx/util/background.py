
from . import convert

import numpy as np
from skimage import color, filters, measure

class Background:
    """
    Class to measure difference between each frame and a background frame.
    """

    def __init__(self,bg_file,blur_sigma=10):

        self._bg_file = bg_file
        self._blur_sigma = blur_sigma

        self._bg_img = convert.load_image_file(bg_file,return_array=False)

        self._bg_array_color = convert.image_to_array(self._bg_img,num_channels=3,dtype=np.float)
        self._bg_array_bw = convert.image_to_array(self._bg_img,num_channels=1,dtype=np.float)
        self._bg_array_blur = filters.gaussian(self._bg_array_bw,self._blur_sigma)
        self._bg_out = convert.image_to_array(self._bg_img,num_channels=4,dtype=np.uint8)

    def get_frame_diff(self,img_file):
        """
        """

        img_array_bw = convert.load_image_file(img_file,dtype=np.float,num_channels=1)
        img_array_blur = filters.gaussian(img_array_bw,sigma=self._blur_sigma)

        total_diff, diff_array = measure.compare_ssim(img_array_blur,
                                                      self._bg_array_blur,
                                                      full=True)

        return 1 - diff_array

    @property
    def color(self):
        return self._bg_array_color

    @property
    def bw(self):
        return self._bg_array_bw

    @property
    def image(self):
        return self._bg_out
