__version__ = "0.2"

from . import effects
from . import physics
from . import processors
from . import util
from . import visuals

from .core import VideoClip
from .core import MultiClip
from .core import PhotoStream

import os
root_dir = os.path.dirname(os.path.abspath(__file__))
