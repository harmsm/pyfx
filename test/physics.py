
import numpy as np
np.random.seed(0)

import photonzombie as pz

print("Uniform potential")

p = pz.physics.Particle()
p.coord = [500,500]
u = pz.physics.UniformPotential(force_vector=np.array((5,0),dtype=np.float))
for i in range(10):
    forces = u.get_forces(p.coord)
    p.advance_time(forces)
    print(p.velocity,p.coord)

print("Radial potential")

p = pz.physics.Particle((320,320))
p.velocity = np.array((0.,0.))
r = pz.physics.RadialPotential(center_coord=np.array((300,300)),pot_mag=-1000)
for i in range(10):
    forces = r.get_forces(p.coord)
    p.advance_time(forces)
    print(p.velocity,p.coord)

print("Random potential")

p = pz.physics.Particle((500,500))
p.velocity = np.array((0.,0.))
r = pz.physics.RandomPotential()
for i in range(10):
    forces = r.get_forces(p.coord)
    p.advance_time(forces)
    print(p.velocity,p.coord)
