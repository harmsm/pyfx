import numpy as np

def smooth(x,window_len=0):
    """
    Smooth a signal using a moving average.

    x: signal
    window_len: size of the smoothing window
                if 0, no smoothing is done.
    """

    if window_len == 0:
        return x

    if window_len < 0:
        err = "window length must be a positive integer\n"
        raise ValueError(err)

    window_len = int(round(window_len))
    if window_len % 2 == 0:
        window_len += 1

    window = np.ones(window_len,'d')
    signal = np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    smoothed = np.convolve(window/window.sum(),signal,mode='valid')

    trim = int((window_len - 1)/2)

    return smoothed[trim:-trim]

def harmonic_langenvin(num_steps,
                       spring_constant=1.0,
                       force_sd=1.0,
                       max_value=None):
    """
    Build a shaking trajectory.  This makes the a particle wander randomly
    over a harmonic potential centered at 0.  This can be used to simulate
    wobblying cameras, flickering lights... anything that can be described as
    random fluctuations along a trajectory that stays around some value.  The
    output trajectory is in 2D, but each dimension is independent, so you can
    take a single dimension from the output if wanted.

    num_steps: how many steps to take.

    The following three parameters can either be individual values OR a list-
    like object that is num_steps long.  If list-like, those constants will be
    updated throughout the trajectory.

    spring_constant: how stiff is the harmonic potential
    force_sd: how hard does the particle get jostled each step (sqrt(temperature))
    max_value: how far to let the particle get away from zero.  if None, bound
               at 3 x force_sd.
    """

    try:
        if len(spring_constant) != num_steps:
            err = "spring constant array is not the same length as num_steps\n"
            raise ValueError(err)
    except TypeError:
        try:
            spring_constant = np.array([float(spring_constant)
                                        for i in range(num_steps)])
        except ValueError:
            err = "spring constant could not be coerced into a float\n"
            raise ValueError(err)

    try:
        if len(force_sd) != num_steps:
            err = "force_sd array is not the same length as num_steps\n"
            raise ValueError(err)
    except TypeError:
        try:
            force_sd = np.array([float(force_sd)
                                        for i in range(num_steps)])
        except ValueError:
            err = "force_sd could not be coerced into a float\n"
            raise ValueError(err)

    try:
        if len(max_value) != num_steps:
            err = "max_value array is not the same length as num_steps\n"
            raise ValueError(err)
    except TypeError:

        try:
            if max_value is None:
                max_value = [None for i in range(num_steps)]
            else:
                max_value = np.array([float(max_value)
                                            for i in range(num_steps)])
        except ValueError:
            err = "max_value could not be coerced into a float\n"
            raise ValueError(err)


    # Model a langevin particle being buffetted by kT
    p = pyfx.physics.Particle()
    harmonic = pyfx.physics.potentials.Spring1D(spring_constant=spring_constant[0])
    langevin = pyfx.physics.potentials.Random(force_sd=force_sd[0])

    # Let it wander around the potential surface
    x = []
    y = []
    for i in range(num_steps):

        # Update harmonic and langevin with new shaking parameters
        harmonic.update(spring_constant=spring_constant[i])
        langevin.update(force_sd=force_sd[i])

        # If no bound is specified, the farthest we can go in any direction is
        # three standard deviations in sqrt(kT) away from center
        if max_shake[i] is None:
            bound = int(round(3*force_sd[i]))
        else:
            bound = max_shake[i]

        h = harmonic.get_forces(p.coord)
        l = langevin.get_forces(p.coord)
        p.advance_time(h + l)

        p.coord[p.coord < -bound] = -bound
        p.coord[p.coord >  bound] =  bound

        x.append(p.coord[0])
        y.append(p.coord[1])

    return np.array(x), np.array(y)
