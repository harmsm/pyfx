__description__ = \
"""
Main class for managing a pyfx session.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-07"

import pyfx

import copy, os, string, warnings, json, glob, shutil, sys

class Workspace:
    """
    """

    def __init__(self,name=None,src=None,bg_img=None):
        """
        name:   string, name of workspace.  If None, a random name will be made
        src:    If string, treat as video file.  If dir, treat as directory of
                png files.  If list, treat as list of image files corresponding
                to frames.  If None, load source from an existing workspace.
        bg_img: frame to use for background subtraction.  If None, no
                background subtraction functionality will be available.
        """

        self._name = name
        self._src = src
        self._bg_img = bg_img

        # Create a random workspace name if none is specified
        if self._name is None:
            r = "".join([random.choice(string.ascii_letters) for i in range(10)])
            self._name = "pyfx_{}".format(r)

        # If the workspace exists, load it.  If not, create it.
        if os.path.isdir(self._name):
            self._load_workspace()
        else:
            self._create_workspace()

    def _create_workspace(self):
        """
        Create a workspace.
        """

        if os.path.isdir(self._name):
            err = "directory with name {} already exists.\n".format(self._name)
            raise FileExistsError(err)

        if self._bg_img is None or self._src is None:
            err = "bg_img and src must be specified.\n"
            raise ValueError(err)

        os.mkdir(self._name)

        self._parse_src()
        self.set_background(self._bg_img)

        #self._write_json()

    def _load_workspace(self):

        err = "not yet implemented\n"
        raise NotImplementedError(err)

        if not os.path.isdir(self._name):
            err = "workspace {} does not exist.\n".format(self._name)
            raise FileNotFoundError(err)

        self._read_json()

    def _read_json(self):
        """
        Read a json file with current workspace state.
        """

        input_dict = json.load(open(os.path.join(self._name,"pyfx.json")))

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
        self._img_list = input_dict["_img_list"]

    def _write_json(self):
        """
        Write a json file with current workspace state.
        """

        out_dict = {}
        out_dict["version"] = pyfx.__version__
        out_dict["src"] = self._src
        out_dict["name"] = self._name
        out_dict["bg_img"] = self._bg_img
        out_dict["bg"] = "background.pickle"
        out_dict["img_list"] = "img_list.pickle"

        json.dump(out_dict,open(os.path.join(self._name,"pyfx.json"),"w"))

    def _parse_src(self):
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

        self._max_time = len(self._img_list)

    def render(self,out_dir,effects,time_interval=None,overwrite=False):

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

        # Do some quick sanity checking -- were these effects created
        # using this workspace?
        for e in effects:
            if e.workspace != self:
                err = "effect {} was not generated with this workspace".format(e)
                raise ValueError(err)

        for t in range(time_interval[0],time_interval[1]):

            self._current_time = t
            print("processing frame ",t)
            sys.stdout.flush()

            img = self.get_frame(t)
            for e in effects:

                # Make sure the effect is baked before running
                if not e.baked:
                    e.bake()
                img = e.render(img,t)

            # Write out image
            out_file = "frame{:06d}.png".format(t)
            out_file = os.path.join(out_dir,out_file)
            pyfx.util.convert.to_file(img,out_file)

    def get_frame(self,t):

        return pyfx.util.convert.from_file(self._img_list[t])

    def set_background(self,bg_frame,blur_sigma=10):

        self._bg_frame = bg_frame
        self._bg = pyfx.util.Background(bg_frame,blur_sigma)

    @property
    def name(self):
        return self._name

    @property
    def current_time(self):
        return self._current_time

    @property
    def max_time(self):
        return self._max_time

    @property
    def times(self):
        return list(range(self._max_time))

    @property
    def bg_img(self):
        return self._bg.image
