
import pyfx

import numpy as np
from skimage import filters, measure, morphology

class Background:
    """
    Class to measure difference between each frame and a background frame.
    """

    def __init__(self,bg_frame,blur_sigma=10):

        self._bg_frame = bg_frame
        self._blur_sigma = blur_sigma

        self._bg_img = pyfx.util.to_image(bg_frame)

        self._bg_array_color = pyfx.util.to_array(self._bg_frame,num_channels=3,dtype=np.float)
        self._bg_array_bw = pyfx.util.to_array(self._bg_frame,num_channels=1,dtype=np.float)
        self._bg_array_blur = filters.gaussian(self._bg_array_bw,self._blur_sigma)
        self._bg_out = pyfx.util.to_array(self._bg_frame,num_channels=4,dtype=np.uint8)

    def frame_diff(self,img):
        """
        Return differnce between img and background.
        """

        img_array_bw = pyfx.util.to_array(img,dtype=np.float,num_channels=1)
        img_array_blur = filters.gaussian(img_array_bw,sigma=self._blur_sigma)

        total_diff, diff_array = measure.compare_ssim(img_array_blur,
                                                      self._bg_array_blur,
                                                      full=True)

        return 1 - diff_array

    def smooth_diff(self,
                    img,
                    threshold=0.2,
                    num_iterate=20,
                    dilation_interval=2,
                    disk_size=35,
                    blur=50):
        """
        Get a smoothed potential well for the difference between an image
        and the background.  Calculate using a series of expanding dilations.
        This is pretty darn slow, unfortunately.

        img: image in format recognized by pyfx
        threshold: difference between the frame and background that is called
                   as different
        num_iterate: how many times to iterate the dilation
        dilation_interval: how often to write out the dilation
        disk_size: size of morphological element for dilation
        blur: how much to blur final result (gaussian sigma)
        """

        frame_diff = self.frame_diff(img)
        disk = morphology.disk(disk_size)

        bool_cut = np.zeros(frame_diff.shape,dtype=np.bool)
        bool_cut[frame_diff > threshold] = True

        out = np.zeros(frame_diff.shape,dtype=np.float)

        tmp = np.copy(bool_cut)
        for i in range(0,num_iterate):
            tmp = morphology.binary_dilation(tmp,selem=disk)
            if i % dilation_interval == 0:
                out[tmp] += 1

        out = filters.gaussian(out,blur)
        out = 1-out/np.max(out)

        return np.array(np.round(255*out,0),dtype=np.uint8)


    @property
    def color(self):
        return self._bg_array_color

    @property
    def bw(self):
        return self._bg_array_bw

    @property
    def image(self):
        return self._bg_out
