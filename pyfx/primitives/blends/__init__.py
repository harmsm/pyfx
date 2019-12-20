__description__ = \
"""
Primitive masks for blending over time.  Functions take a shape, the number
of steps, and possibly other arguments.  They then return a mask that is has
dimensions num_steps + 1, shape[0], shape[1] that transitions from 0 to 255
for whatever blend is being done.
"""
__author__ = "Michael J. Harms"
__date__ = "2019-12-19"

from .fade import fade
from .wipe import wipe
