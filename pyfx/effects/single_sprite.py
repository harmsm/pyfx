
import pyfx
from .base import Effect

class SingleSprite(Effect):
    """
    Draw a single sprite as a function of time.
    """

    def __init__(self,videoclip):

        self._default_waypoint = {"hue":0.5,
                                  "saturation":1.0,
                                  "value":1.0,
                                  "position":(500,500),
                                  "radius":5,
                                  "visible":True}

        super().__init__(videoclip)

        self._baked = False

    def bake(self,smooth_window_len=0,sprite=None):

        self._interpolate_waypoints(smooth_window_len)

        if sprite is not None:
            self._sprite = sprite
        else:
            self._sprite = pyfx.primitives.sprites.GlowingParticle(radius=self.radius[0],
                                                                      hue=self.hue[0])

        self._baked = True

    def render(self,img):

        t = self._videoclip.current_time
        if not self.visible[t]:
            return img

        self._sprite.radius = self.radius[t]
        self._sprite.hue = self.hue[t]

        return self._sprite.write_to_image(self.position[t],img)
