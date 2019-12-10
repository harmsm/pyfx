
import pytest

import numpy as np
np.random.seed(0)

import pyfx

def test_uniform():

    print("Uniform potential")

    p = pyfx.physics.Particle()
    p.coord = [500,500]
    u = pyfx.physics.potentials.Uniform(force_vector=np.array((5,0),dtype=np.float))
    for i in range(10):
        forces = u.get_forces(p.coord)
        p.advance_time(forces)
        print(p.velocity,p.coord)
