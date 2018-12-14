import numpy as np

def smooth(x,window_len=30):
    """
    Smooth a signal using a moving average.

    x: signal
    window_len: size of the smoothing window (defaults to 30 -- one second)
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
