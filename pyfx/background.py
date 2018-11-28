
import numpy as np
from PIL import Image
from skimage import color, filters, measure

class Background:
    """
    Class to measure difference between each frame and a background frame.
    """

    def __init__(self,bg_file,blur_sigma=10):

        self._bg_file = bg_file
        self._blur_sigma = blur_sigma

        self._bg_img = Image.open(bg_file)
        self._bg_array_color = np.array(self._bg_img)
        self._bg_array_bw = color.rgb2gray(self._bg_array_color)
        self._bg_array_blur = filters.gaussian(self._bg_array_bw,self._blur_sigma)

        bg_alpha = np.array(255*np.ones(self._bg_array_bw.shape),dtype=np.uint8)
        self._bg_out = Image.fromarray(np.dstack((self._bg_array_color,bg_alpha)))

    def get_frame_diff(self,img_file):
        """
        """

        img = Image.open(img_file)
        img_array_color = np.array(img)
        img_array_bw = color.rgb2gray(img_array_color)
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
