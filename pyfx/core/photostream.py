__description__ = \
"""
Main class for managing a pyfx session.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-07"

import pyfx
from .videoclip import VideoClip

import numpy as np
import pandas as pd

import os, sys

class PhotoStream(VideoClip):
    """
    Class that creates a VideoClip-like instance that forms a slideshow from
    photos.
    """

    def __init__(self,name,src=None,bg_frame=None):
        """
        name:   string, name of videoclip.
        src:    spreadsheet with columns:
                image (image files, with path *relative to spreadsheet*)
                time (time to show that image)
        bg_frame: Frame to use for background subtraction (string pointing to
                  image file, PIL.Image instance, or array).  x,y dimensions
                  must match those from src.  If None, a background of uniform
                  127,127,127 is used for all calculations.
                  If loading from an existing source, this argument is ignored.
        """

        super().__init__(name,src,bg_frame)


    def get_frame(self,t):
        """
        Get the frame at time t.  Return as an array.
        """

        # If the user edited the df manually, reload it
        if not self._df.equals(self._previous_df):
            self._parse_df()

        # return None if t is past end of video
        if t > self._max_time:
            return None


        internal_t = self._internal_time[t]


        return pyfx.util.to_array(self._img_list[internal_t],dtype=np.uint8,
                                  num_channels=4)

    def _initialize_src(self):
        """
        Load the video source dataframe.
        """

        if type(self._src) is str:

            self._base_dir = os.path.abspath(os.path.dirname(self._src))

            if self._src[-4:] == ".csv":
                self._df = pd.read_csv(self._src)

            elif self._src[-4:] in [".xls","xlsx"]:
                self._df = pd.read_excel(self._src)
            else:
                err = "File type for {} not recognized. Should be .csv, .xlsx, or .xls\n".format(self._src)
                raise ValueError(err)

        else:
            err = "src must be a spreadsheet file\n"
            raise ValueError(err)

        # Sanity checking on data frame structure
        if "image" not in self._df.columns:
            err = "data frame must contain an 'image' column.\n"
            raise ValueError(err)

        if "time" not in self._df.columns:
            err = "data frame must contain an 'time' column.\n"
            raise ValueError(err)

        self._current_time = 0
        self._parse_df()

    def _parse_df(self):
        """
        Actually load the dataframe values.
        """

        self._img_list = []
        self._time_list = []
        self._internal_time = []

        self._shape = None
        self._max_time = 0
        for i in range(len(self._df.image)):

            # Append path of the dataframe file to the image filename
            f = os.path.join(self._base_dir,self._df.image[i])

            self._img_list.append(pyfx.util.to_array(f))
            if self._shape is None:
                self._shape = self._img_list[-1].shape[:2]

            if self._img_list[-1].shape[:2] != self.shape:
                err = "All images must have the same dimensions.\n"
                err += "{} has dimensions {}, but\n".format(f,self._img_list[-1].shape[:2])
                err += "the PhotoStream has dimensions {}".format(self.shape)
                raise ValueError(err)

            try:
                t = int(np.round(self._df.time[i],0))
                self._time_list.append(t)
            except TypeError:
                err = "'time' column must be interpretable as an integer"
                raise ValueError(err)

            for j in range(t):
                self._internal_time.append(i)

            # Record last, extra frame
            self._internal_time.append(i)
            self._max_time += t

        if self._current_time > self._max_time:
            print("Dataframe changed, so reloading.  Photostream clip current time set to 0.\n")
            self._current_time = 0

        self._previous_df = self._df.copy()

    @property
    def df(self):
        """
        Provide access to the dataframe itself.  This should let a user edit
        the dataframe.
        """
        return self._df
