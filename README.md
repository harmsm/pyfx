# pyfx

Python library for adding visual effects to video streams. It's built on libraries such as
[skimage](https://scikit-image.org/), [pillow](https://pillow.readthedocs.io/), [dlib](http://dlib.net/), [numpy](http://www.numpy.org/), and [scipy](https://www.scipy.org/).

### Workflow

```python
import pyfx
ws = pyfx.Workspace("workspace.pyfx",source)

# Add effects here...

ws.render(output)
```



The following working code loads a video stream and, over the first 5 frames, pans left-to-right 100 pixels, rotates 3-degrees clockwise, and adds camera shake. 

```python
import pyfx

ws = pyfx.Workspace(name,source)

vc = pyfx.effects.VirtualCamera(ws)
vc.add_waypoint(5,x=100,theta=-3,shaking_magnitude=10)
vc.bake()

ws.render(output,(vc,))
```

Effects can be applied in serial as a pipeline.  The following code adds flickering exposure to the existing shot. 

```python
import pyfx
import random

ws = pyfx.Workspace(name,source)

vc = pyfx.effects.VirtualCamera(ws)
vc.add_waypoint(5,x=100,theta=-3,shaking_magnitude=10)
vc.bake()

hsv = pyfx.effects.HSVShift(ws)
hsv.add_waypoint()
for i in range(30):
    hsv.add_waypoint(i,value=random.random())
hsv.bake()


ws.render(output,(vc,hsv))
```







It currently has a few features:

+ Good stuff under the hood:
  + `Effect` base class that can be extended to generate arbitrarily complicated time-aware visual effects.  
  +  `Sprite` class that can be used to define new visuals to attach to particles.
  + Simple physics, particles and ability to load in images as potential surfaces
  + A `Background` class that allows ready identification of foreground and background pixels

####  Design choices:

+ Image arrays are enforced to be of only a few types
    + `float` (positive values between 0 and 1)
    + `int` (positive values between 0 and 255)
    + Grayscale (one channel), RGB (three channel), and RGBA (four channel)
    + Arrays are stored in `array[y,x,channel]` format, where `y` indexes height and  `x`  indexes width.   The origin is in the top, left.  So 0,0 corresponds to the top left.  540,960 corresponds to the center of the frame.

## TO DO

1. Write integrated photonzombie effect. 
2. Implement `Sparks`  effect and sprite.
3. Integrate with ffmpeg???
4. Fix warnings thrown by FaceStack
5. Check `bake` calls for all effects and see if any of the parameters should be moved into `waypoint` parameters.  (Why not make them accessible as handles vs. time? )
6. Write unit tests, particularly for the `util`  functions. 

### Issues

+ Inconsistent x/y height/width coordinate nomenclature and conventions.
+ Inconsistent masking conventions. (background/preserve should be 0; foreground/change should be 255)



### Thinking

+ physics

  + potentials (expose sample_coord, get_energy, get_forces, update, properties)
    + empirical
    + radial
    + random
    + spring1D
    + uniform
  + objects (expose advance_time, properties)
    + particle

+ visuals

  + sprites (expose write_to_image, properties)
  + filters (one-off functions to tweak images)

+ `util`
  + `to_file` 
  + `to_array`
  + `to_image` 
  + `crop`
  + `expand`
  + `find_pan_crop`
  + `find_zoom_crop`
  + `find_rotate_crop`
  + `smooth`

+ processors (stuff applied to whole video stream that is painful enough to calculate that it gets stored in the workspace)

  + face_finder
  + diff_potential

+ effects (take a workspace object as input); should take mask indicating region that should not be touched; usually take a background; if they precalculate stuff like background images, this should be stored in the workspace

  + glowing_eyes
  + glowing_particles
  + ghost
  + virtual_camera
  + lighting_distortion
  + sparks (particles that are in uniform accelerationf field, shot out of a point source with some spread that then follow ballastic trajectory.  Tail points in opposite direction from velocity vector.  Length and brightness determined by speed.  maybe add friction?)



### Concepts

#### Workspace

#### Effects

#### Processors

#### Physics








```python
import pyfx

ws = pyfx.Workspace(name,some_collection_of_images,background)

effect_one = pyfx.effects.SomeEffect(ws)
effect_one.add_waypoint()
effect_one.add_waypoint()

effect_two = pyfx.effect.SomeOtherEffect(ws)
effect_two.add_waypoint()
effect_two.add_waypoint()

ws.render((effect_one,effect_two),out_dir)


```









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



## Special Effects

### VirtualCamera

The virtual camera can be used to add shaking, pans, rotation, or zooming an existing video file.

For a `1920x1080`  video: 

+ `shaking_magnitude=3`, `shaking_stiffness=1` .  A slightly drunk Uncle Steve, weaving with the camera.   
+ magnitude 5.Stiffness: 10,  Airline turbulence
+ 10 Stiffness: 10, having trouble keeping her together Captain!
+ 15,15: in the process of exploding

