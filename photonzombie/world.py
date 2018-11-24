
import numpy as np


def coarse_grain(some_array,coarseness=5):

    # Figure out dimensions of final array (multiple of coarseness)
    shape = np.array(some_array.shape, dtype=float)
    new_shape = coarseness * np.ceil(shape / coarseness).astype(int)

    # Create the zero-padded array and assign it with the old density
    density = np.zeros(new_shape)
    density[:some_array.shape[0], :some_array.shape[1]] = some_array

    # Now use the same method as before
    temp = density.reshape((new_shape[0] // coarseness, coarseness,
                            new_shape[1] // coarseness, coarseness))

    coord = np.zeros((new_shape[0],new_shape[1],2),dtype=np.float)
    x = np.arange(0,new_shape[0],coarseness) + coarseness/2
    y = np.arange(0,new_shape[1],coarseness) + coarseness/2

    return x, y, np.sum(temp, axis=(1,3))

def X(diff_array,coarseness=100):

    coarse_x, coarse_y, coarse_diff = coarse_grain(diff_array,coarseness)

    for p in particles:

        force = np.zeros(2,dtype=np.float)
        for b in blobs:

            signs = (b.coord - p.coord)

            r = np.sqrt(np.sum(signs**2))
            mag = gamma*(1/r)**6 - beta**(1/r)**12

    a = np.sum((gamma/r)**12 - (beta/r)**6)

    coord = (a/2)*(dt*dt) + (vel*dt) + coord
    vel = a*dt + vel



def create_particles(diff_array,particle_density=1e-5,beta=10,num_particles=None):

    # Boltzmann-weight density
    w = np.exp(beta*diff_array)

    # Create arrays for selecting Boltzmann-weighted coordinates
    p = w.ravel()/np.sum(w)
    indexes = np.array(range(len(p)))

    # How many particles to create (based on how different this image
    # is from background)
    if num_particles is None:
        num_particles = np.int(np.round(particle_density*np.sum(w)))
    else:
        num_particles = num_particles

    particles = []
    for i in range(num_particles):

        position = np.random.choice(indexes,p=p)
        y_coord = np.mod(position,w.shape[1])
        x_coord = np.int((position - y_coord)/w.shape[1])

        particles.append(particle.Particle())
        particles[-1].create_particle(x_coord,y_coord)

    # equilibrate particles
    for p in particles:
        for j in range(50):
            p._advance_time()

    return particles
