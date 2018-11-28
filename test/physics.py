
import numpy as np
np.random.seed(0)

import pyfx

print("Uniform potential")

p = pyfx.physics.Particle()
p.coord = [500,500]
u = pyfx.physics.UniformPotential(force_vector=np.array((5,0),dtype=np.float))
for i in range(10):
    forces = u.get_forces(p.coord)
    p.advance_time(forces)
    print(p.velocity,p.coord)

print("Radial potential")

p = pyfx.physics.Particle((320,320))
p.velocity = np.array((0.,0.))
r = pyfx.physics.RadialPotential(center_coord=np.array((300,300)),pot_mag=-1000)
for i in range(10):
    forces = r.get_forces(p.coord)
    p.advance_time(forces)
    print(p.velocity,p.coord)

print("Random potential")

p = pyfx.physics.Particle((500,500))
p.velocity = np.array((0.,0.))
r = pyfx.physics.RandomPotential()
for i in range(10):
    forces = r.get_forces(p.coord)
    p.advance_time(forces)
    print(p.velocity,p.coord)
