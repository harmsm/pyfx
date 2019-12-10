
import pytest

import numpy as np
np.random.seed(0)

import pyfx

def test_random():

    known_velocity = np.array([[0.42113648,0.0955305 ],
                               [0.65479296,0.63050434],
                               [1.10063959,0.39719643]])

    known_position = np.array([[500.42113648,500.0955305 ],
                               [501.07592943,500.72603484],
                               [502.17656902,501.12323127]])

    p = pyfx.physics.Particle((500,500))
    p.velocity = np.array((0.,0.))
    r = pyfx.physics.potentials.Random()

    out_velocity = np.zeros((3,2),dtype=np.float)
    out_position = np.zeros((3,2),dtype=np.float)
    for i in range(3):
        forces = r.get_forces(p.coord)
        p.advance_time(forces)

        out_velocity[i,:] = p.velocity
        out_position[i,:] = p.coord

    v_test = int(np.sum(np.isclose(out_velocity,known_velocity)))
    p_test = int(np.sum(np.isclose(out_position,known_position)))

    assert v_test == 6
    assert p_test == 6


#test_random_potential()
