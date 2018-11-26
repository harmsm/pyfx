
def coarse_grain(some_array,coarseness=5):

    # Figure out dimensions of final array (multiple of coarseness)
    shape = np.array(some_array.shape, dtype=float)
    new_shape = coarseness * np.ceil(shape / coarseness).astype(int)

    # Create the zero-padded array and assign it with the old density
    density = np.zeros(new_shape)
    density[:some_array.shape[0], :some_array.shape[1]] = some_array

    # Average each block
    temp = density.reshape((new_shape[0] // coarseness, coarseness,
                            new_shape[1] // coarseness, coarseness))

    x = np.arange(0,new_shape[0],coarseness) + coarseness/2
    y = np.arange(0,new_shape[1],coarseness) + coarseness/2
    x, y = np.meshgrid(x,y,indexing="ij")

    coord = np.stack((x.ravel(),y.ravel())).T

    return coord, np.sum(temp, axis=(1,3))


def random_pareto(a,minimum=1,maximum=6):
    """
    Sample from a pareto distribution, forcing output to be between minimum
    and maximum.
    """

    b = np.random.pareto(a) + minimum
    if b > maximum:
        b = maximum

    return b
