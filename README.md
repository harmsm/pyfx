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







## Complicated demo

1. Create a workspace, assigning a background frame and associated images

   ```python
   import pyfx
   ws = pyfx.create_workspace(name,img_list,bg_image)
   ```

2. Precalculate stuff

   ```python
   pyfx.processors.find_faces(ws)
   pyfx.processors.diff_potentials(ws)
   ```

3. Add custom particle potentials

   ```python
   gradient = pyfx.potential_from_img(gradient_img_file)
   pyfx.add_potential(ws,gradient,start=10)
   ```

4. Add effects layers

   ```python
   pyfx.effects.photonzombie(ws,particles=200)
   ```

5. Render

   ```python
   ws.render(out_file)
   ```
