# pyfx

Python library for adding visual effects to video streams.  This is a personal
project to learn how to think about such effects, rather than an attempt to
build a real production tool.  It's built on libraries such as
[skimage](https://scikit-image.org/), [pillow](https://pillow.readthedocs.io/),
[dlib](http://dlib.net/) and (of course)
[numpy](http://www.numpy.org/)/[scipy](https://www.scipy.org/).

It currently has a few features:

+ Simple physics calculated for particles.  These can be placed on a variety
  of potential surfaces, allowing them to evolve over time.
+ A class that uses dlib to find facial features and track them over frames.  
  This lets you add fun effects like glowing eyes.
+ A Sprite class that lets you decorate things like particles and write them
  to images in a coherent way.
+ A class that identifies foreground pixels.
+ Some styling to create ghost and halo effects.  

Design choices:
+ Arrays are enforced to be of only a few types:
    +

The API is pretty rough at this point.  Expect changes.
