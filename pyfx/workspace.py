__description__ = \
"""
Main class for managing a pyfx session.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-07"

import copy, os, string, warnings

class Workspace:

    def __init__(self,name=None,src=None,bg_frame=None):
        """
        name: string, name of workspace.  If None, a random name will be made
        src: If string, treat as video file.  If list, treat as list of
             images corresponding to frames.  If None, load source from an
             existing workspace.
        bg_frame: int, frame to use for background subtraction.  If None, no
                  background subtraction functionality will be available.
        """

        self._name = name
        self._src = src
        self._bg_frame = bg_frame

        # Create a random workspace name if none is specified
        if self._name is None:
            r = "".join([random.choice(string.ascii_letters) for i in range(10)])
            self._name = "pyfx_{}".format(r)

        if os.path.isdir(self._name):
            self._load_workspace(self._name)
        else:
            self._create_workspace()

    def _create_workspace(self):

        if os.path.isdir(self._name):
            err = "directory with name {} already exists.\n".format(self._name)
            raise FileExistsError(err)

        # Figure out what sort of input this is
        if type(self._src) is str:
            self._input_type = "video"
        elif type(self._src) in [list,tuple]:
            self._input_type = "images"
        else:
            err = "source type not recognized\n"
            raise ValueError(err)

        os.mkdir(self._name)

        self._write_json()

    def _load_workspace(self,):

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
        self._input_type = input_dict["input_type"]

    def _write_json(self):
        """
        Write a json file with current workspace state.
        """

        out_dict = {}
        out_dict["version"] = pyfx.__version__
        out_dict["src"] = self._src
        out_dict["name"] = self._name
        out_dict["bg_frame"] = self._bg_frame

        out_dict["input_type"] = self._input_type

        json.dump(out_dict,open(os.path.join(self._name,"pyfx.json"),"w"))

    @property
    def name(self):
        return self._name
