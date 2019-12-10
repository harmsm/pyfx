
import pytest

import numpy as np
np.random.seed(0)

import pyfx

def test_radial():

    print("Radial potential")

    p = pyfx.physics.Particle((320,320))
    p.velocity = np.array((0.,0.))
    r = pyfx.physics.potentials.Radial(center_coord=np.array((300,300)),pot_mag=-1000)
    for i in range(10):
        forces = r.get_forces(p.coord)
        p.advance_time(forces)
        print(p.velocity,p.coord)
