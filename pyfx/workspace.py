__description__ = \
"""
Main class for managing a pyfx session.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-07"

import pyfx

import numpy as np
import copy, os, string, warnings, json, glob, shutil, sys

class Workspace:
    """
    Main class for managing a pyfx session.
    """

    def __init__(self,name,src=None,bg_frame=None):
        """
        name:   string, name of workspace.
        src:    If string, treat as video file.
                If dir, treat as directory of png files.
                If list, treat as list of image files corresponding to frames.
                If None, load from existing source.
                If loading from an existing source, this argument is ignored.
        bg_frame: Frame to use for background subtraction (string pointing to
                  image file, PIL.Image instance, or array).  x,y dimensions
                  must match those from src.  If None, a background of uniform
                  127,127,127 is used for all calculations.
                  If loading from an existing source, this argument is ignored.
        """

        self._name = name
        self._src = copy.copy(src)
        self._bg_frame = bg_frame

        # If the workspace exists, load it.  If not, create it.
        if os.path.exists(self._name):
            if os.path.isdir(self._name):
                self._load()
            else:
                err = "{} exists but is not a directory\n".format(self._name)
                raise ValueError(err)
        else:
            self._initialize_workspace()

    def render(self,out_dir,effects=(),time_interval=None,overwrite=False):
        """
        out_dir: directory to write out frames
        effects: tuple containing what effects to apply, in what order.
        time_interval: tuple or list of length = 2 that indicates starting and
                       ending frame to render.
        overwrite: bool indicating whether or not to overwrite existing output
        """

        # Make the output directory
        if os.path.isdir(out_dir):
            if overwrite:
                shutil.rmtree(out_dir)
                os.mkdir(out_dir)
            else:
                err = "output directory {} exists\n".format(out_dir)
                raise FileExistsError(err)
        else:
            os.mkdir(out_dir)

        if time_interval is None:
            time_interval = (0,self._max_time + 1)

        # Do some quick sanity checking -- were the effects all created
        # using this workspace?
        for e in effects:
            if e.workspace != self:
                err = "effect {} was not generated with this workspace".format(e)
                raise ValueError(err)

        # Go over the frames in the specified time interval
        for t in range(time_interval[0],time_interval[1]):

            self._current_time = t
            print("processing frame ",t)
            sys.stdout.flush()

            # Go over each effect, in order
            img = self.get_frame(t)
            for e in effects:

                # Make sure the effect is baked before running
                if not e.baked:
                    e.bake()
                img = e.render(img)

            # Write out image
            out_file = "frame{:08d}.png".format(t)
            out_file = os.path.join(out_dir,out_file)
            pyfx.util.to_file(img,out_file)

        self._save()

    def set_background(self,bg_frame=None,blur_sigma=10):
        """
        Set the background frame.

        bg_frame: array, PIL.Image, or string pointing to image file to use
                  as a background frame.  If None, generate a field of
                  127,127,127 and use as a background image.
        blur_sigma: how much to blur background and foreground images when
                    comparing them.
        """

        self._bg_frame = bg_frame

        # If the background frame is not specified, create a fake, flat one.
        if self._bg_frame is None:
            self._bg_frame = 127*np.ones((self.shape[0],self.shape[1],4),
                                         dtype=np.uint8)
            self._bg_frame = bg[:,:,3] = 255

        # Convert to an array
        self._bg_frame = pyfx.util.to_array(bg_frame,
                                            num_channels=4,
                                            dtype=np.uint8)

        # Send to the Background instance
        self._bg = pyfx.util.Background(self._bg_frame,blur_sigma)

        self._save()

    def get_frame(self,t,as_file=False):
        """
        Get the frame at time t.  Return as an array unless as_file is True,
        in which case return a string pointing to the filename.
        """

        if as_file:
            return self._img_list[t]

        return pyfx.util.to_array(self._img_list[t],dtype=np.uint8,
                                  num_channels=4)

    def _initialize_workspace(self):
        """
        Initialize a workspace.
        """

        if not os.path.exists(self._name):
            os.mkdir(self._name)

        self._initialize_src()
        self.set_background(self._bg_frame)
        self._save()

    def _load(self):
        """
        Load a workspace state from disk.
        """

        if not os.path.isdir(self._name):
            err = "workspace {} does not exist.\n".format(self._name)
            raise FileNotFoundError(err)

        f = open(os.path.join(self._name,"pyfx.json"))
        input_dict = json.load(f)
        f.close()

        if input_dict["version"] != pyfx.__version__:
            w = "version mismatch between pyfx ({}) and workspace ({})\n"
            warnings.warn(w.format(pyfx.__version__,input_dict["version"]))

        if input_dict["name"] != self._name:
            err = "workspace name mismatch ({} vs. {})".format(input_dict["name"],
                                                               self._name)
            raise ValueError(err)

        self._name = input_dict["name"]
        self._src = input_dict["src"]
        self._bg_frame = input_dict["bg_frame"]

        self._initialize_workspace()

    def _save(self):
        """
        Write out workspace state to disk.
        """

        out_dict = {}
        out_dict["version"] = pyfx.__version__
        out_dict["name"] = self._name
        out_dict["src"] = self._src

        # Write out the background file as an image
        bg_file = os.path.join(self._name,"master_bg_image.png")
        pyfx.util.to_file(self._bg_frame,bg_file)
        out_dict["bg_frame"] = bg_file

        f = open(os.path.join(self._name,"pyfx.json"),"w")
        json.dump(out_dict,f)
        f.close()

    def _intialize_src(self):
        """
        Load the video source.
        """

        self._img_list = []
        if type(self._src) is str:

            # Parse a directory of png files
            if os.path.isdir(self._src):
                self._img_list = glob.glob(os.path.join(self._src,"*.png"))
                self._img_list.sort()

            # Parse a video file
            elif os.path.isfile(self._src):
                err = "input appears to be a video file -- not implemented yet\n"
                raise NotImplementedError(err)

            # Error
            else:
                err = "source type is not recognized.\n"
                raise ValueError(err)

        # Parse a list of image files
        elif type(self._src) is list or type(self._src) is tuple:

            for x in self._src:
                if not os.path.isfile(x):
                    err = "input file {} not found\n".format(x)
                    raise FileNotFoundError(err)

            self._img_list = copy.copy(self._src)

        else:
            err = "could not parse src of type {}\n".format(type(self._src))
            raise ValueError(err)

        self._current_time = 0
        self._max_time = len(self._img_list) - 1
        self._shape = pyfx.util.to_array(self._img_list[0],num_channels=1).shape

        self._save()

    @property
    def name(self):
        """
        Name of workspace.
        """
        return self._name

    @property
    def bg_frame(self):
        """
        Background frame used for workspace. (return as array)
        """

        return self._bg_frame

    @property
    def src(self):
        """
        Source used for video.
        """

        return copy.copy(self._src)

    @property
    def current_time(self):
        """
        Current time of the workspace.
        """
        return self._current_time

    @property
    def max_time(self):
        """
        Maximum time in the workspace.
        """
        return self._max_time

    @property
    def times(self):
        """
        All times in the workspace.
        """
        return list(range(self._max_time + 1))

    @property
    def shape(self):
        """
        Width and height of the workspace.
        """

        return self._shape

    @property
    def background(self):
        """
        Background instance.
        """

        return self._bg
