__version__ = "0.1"

from . import effects
from . import physics
from . import processors
from . import util
from . import visuals

from ._workspace import Workspace

import os
root_dir = os.path.dirname(os.path.abspath(__file__))
