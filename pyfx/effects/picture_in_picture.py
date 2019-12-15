__description__ = \
"""
Cut out a chunk of the video frame and replace it with another video or
still image.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-14"

import pyfx
from .base import Effect

import skimage

import numpy as np

import os, glob, warnings

class PictureInPicture(Effect):
    """
    If the picture-in-picture video runs out of frames (in either direction),
    show the first or last frame in the picture-in-picture video and throw
    a warning.

    The portion of the screen that is overlaid is given by picture_mask.
    The relative position and size of the picture-in-picture is given by
    pip_offset (tuple of x,y) and pip_size (scalar).

    To turn off at a given waypoint x, set set_waypoint(x,picture_mask=None).
    """

    def __init__(self,videoclip,pip_video,pip_start_frame=0):
        """
        videoclip: videoclip for this effect
        pip_video: If string, treat as video file. (not implemented)
                   If dir, treat as directory of png files.
                   If list, treat as list of image files corresponding to frames.
        pip_start_frame: pip video frame corresponding to 0 in the videoclip.
                         integer, which can be negative
        """

        self._pip_start_frame = pip_start_frame

        if type(pip_video) is str:
            if os.path.exists(pip_video):
                if os.path.isdir(pip_video):
                    self._img_list = glob.glob(os.path.join(pip_video,"*.png"))
                    self._img_list.sort()
                elif os.path.isfile(pip_video):
                    err = "{} appears to a video.  Not readable yet.\n".format(pip_video)
                    raise NotImplementedError(err)
                else:
                    err = "{} format not recognized\n".format(pip_video)
                    raise ValueError(err)
            else:
                err = "{} not found\n".format(pip_video)
                raise FileNotFoundError(err)
        else:
            if type(pip_video) in [list,tuple]:
                self._img_list = copy.copy(pip_video)
            else:
                err = "{} format not recognized\n".format(pip_video)
                raise ValueError(err)

        self._default_waypoint = {"picture_mask":None,
                                  "pip_offset":(0,0),
                                  "pip_scale":1.0}

        super().__init__(videoclip)

    def _get_frame(self,t):

        frame_index = t + self._pip_start_frame

        if frame_index < 0:
            warning = "time {} is before start of picture-in-picture video\n".format(t)
            warnings.warn(warning)
            frame_index = 0

        if frame_index >= len(self._img_list):
            warning = "time {} is after end of picture-in-picture video\n".format(t)
            warnings.warn(warning)
            frame_index = -1

        return pyfx.util.to_array(self._img_list[frame_index],
                                  num_channels=4,dtype=np.uint8)

    def render(self,img):

        t = self._videoclip.current_time
        if not self._baked:
            self.bake()

        if self.picture_mask[t] is not None:

            pip = self._get_frame(t)

            tmp = 127*np.ones(img.shape,dtype=np.uint8)

            # x translation
            cut_x = [0,img.shape[1]-1]
            if self.pip_offset[t][0] != 0:
                if self.pip_offset[t][0] < 0:
                    cut_x[0] = -self.pip_offset[t][0]
                    tmp[:,:(cut_x[1]-cut_x[0] + 1),:] = pip[:,cut_x[0]:,:]
                    tmp[:,(cut_x[1]-cut_x[0]):    ,:] = 127
                else:
                    cut_x[1] = img.shape[1] - self.pip_offset[t][0]
                    tmp[:,self.pip_offset[t][0]:,:] = pip[:,:cut_x[1],:]

                pip = np.copy(tmp)

            # y translation
            cut_y = [0,img.shape[0]-1]
            if self.pip_offset[t][1] != 0:
                if self.pip_offset[t][1] < 0:
                    cut_y[0] = -self.pip_offset[t][1]
                    tmp[:(cut_y[1]-cut_y[0] + 1),:,:] = pip[cut_y[0]:,:,:]
                    tmp[(cut_y[1]-cut_y[0]):,:,:] = 127
                else:
                    print("x")
                    cut_y[1] = img.shape[0] - self.pip_offset[t][1]
                    tmp[self.pip_offset[t][1]:,:,:] = pip[:cut_y[1],:,:]
                    tmp[:self.pip_offset[t][1],:,:] = 127

                pip = np.copy(tmp)

            if self.pip_scale[t] != 1.0:

                rescaled = skimage.transform.rescale(pip,self.pip_scale[t],
                                                     multichannel=True)

                diff_x = abs(rescaled.shape[0] - img.shape[0])
                crop_x = (diff_x//2,diff_x//2 + diff_x % 2)

                diff_y = abs(rescaled.shape[1] - img.shape[1])
                crop_y = (diff_y//2,diff_y//2 + diff_y % 2)

                if self.pip_scale[t] < 1.0:
                    pip = pyfx.util.crop(rescaled,crop_x,crop_y)
                else:
                    pip = pyfx.util.expand(rescaled,crop_x,crop_y)

            final_alpha = np.round(self.alpha[t]*(255 - self.picture_mask[t]),0)
            masked_img = pyfx.util.to_array(img,num_channels=4,dtype=np.uint8)
            masked_img[:,:,3] = final_alpha

            pip[:,:,3] = 255

            img = pyfx.util.alpha_composite(pip,masked_img)

        return img
