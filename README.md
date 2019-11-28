# pyfx

Python library for adding visual effects to video streams. It's built on libraries such as
[skimage](https://scikit-image.org/), [pillow](https://pillow.readthedocs.io/), [dlib](http://dlib.net/), [numpy](http://www.numpy.org/), and [scipy](https://www.scipy.org/).

This started as a simple project to explore how to do visual effects, rather than as an attempt to build a fully functional effects platform.  

### Workflow

```python
import pyfx
ws = pyfx.Workspace("workspace.pyfx",source)

# Add effects here...

ws.render(output)
```

#### Example

The following code loads a video stream and, over the first 5 frames, pans left-to-right 100 pixels, rotates 3-degrees clockwise, and adds camera shake.

```python
import pyfx

ws = pyfx.Workspace(name,source)

vc = pyfx.effects.VirtualCamera(ws)
vc.add_waypoint(5,x=100,theta=-3,shaking_magnitude=10)
vc.bake()

ws.render(output,effects=(vc,))
```

Effects can be applied in serial as a pipeline.  The following adds flickering exposure to the existing effect.

```python
import pyfx
import random

ws = pyfx.Workspace(name,source)

vc = pyfx.effects.VirtualCamera(ws)
vc.add_waypoint(5,x=100,theta=-3,shaking_magnitude=10)
vc.bake()

cs = pyfx.effects.ColorShift(ws)
for i in range(30):
    cs.add_waypoint(i,value=random.random())
cs.bake()

ws.render(output,effects=(vc,cs))
```

#### Main classes

+ `Effect` base class that can be extended to generate arbitrarily complicated time-aware visual effects.
+ `Sprite` class that can be used to define new visuals to attach to particles
+ `Background` class that allows ready identification of foreground and background pixels
+ `Potential` and `Particle` classes for doing physics-based 2D particle effects.
+ `Processor` classes are classes that update things like potentials or sprites as a function of time.

####  Design choices:

Image arrays are enforced to be of only a few types:
+ `float` (positive values between 0 and 1)
+ `int` (positive values between 0 and 255)
+ Grayscale (one channel), RGB (three channel), and RGBA (four channel)
+ Arrays are stored in `array[y,x,channel]` format, where `y` indexes height and  `x`  indexes width.   The origin is in the top, left.  So 0,0 corresponds to the top left.  540,960 corresponds to the center of the frame.

The simplest way to ensure compatibility across the library is to load images by  `pyfx.util.to_array`, which can take any image-like input and will spit out an array.  (`pyfx.util.to_file`  does the same basic functionality, but writes to an image file.)

#### Known issues

+ Inconsistent x/y height/width coordinate nomenclature and conventions.
+ Inconsistent masking conventions. (background/preserve should be 0; foreground/change should be 255)
