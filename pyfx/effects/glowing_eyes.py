
import pyfx

from .base import Effect

import numpy as np

class GlowingEyes(Effect):

    def __init__(self,workspace):

        self._default_waypoint = {"eye_scalar":1.0}

        super().__init__(workspace)

        self._baked = False

    def bake(self,
             training_data=None,
             max_time_gap=5,
             p_cutoff=0.9,
             real_cutoff=100,
             min_time_visible=5,
             smooth_window_len=0):

        self._human_faces = pyfx.processors.HumanFaces(self._workspace,
                                                       training_data,
                                                       max_time_gap,
                                                       p_cutoff,
                                                       real_cutoff,
                                                       min_time_visible)
        self._human_faces.bake()

        self._eye_sprite = pyfx.visuals.sprites.GlowingParticle(radius=4)

        self._left_eye_coord = {}
        self._right_eye_coord = {}

        for f in self._human_faces.face_stacks:

            r = f.get_centroid("right_eye")

            rt = r[0]
            rc = r[1][0]

            for i in range(len(rt)):

                # Right eye coordinates (x, y, r)
                to_write = (rc[i,1],rc[i,0],rc[i,2])
                try:
                    self._right_eye_coord[rt[i]].append(to_write)
                except KeyError:
                    self._right_eye_coord[rt[i]] = [to_write]

            l = f.get_centroid("left_eye")

            lt = l[0]
            lc = l[1][0]

            for i in range(len(lt)):

                # Left eye coordinates (x, y, r)
                to_write = (lc[i,1],lc[i,0],lc[i,2])
                try:
                    self._left_eye_coord[lt[i]].append(to_write)
                except KeyError:
                    self._left_eye_coord[lt[i]] = [to_write]

        self._interpolate_waypoints(smooth_window_len)

        self._baked = True

    def render(self,img):

        t = self._workspace.current_time
        if not self._baked:
            self.bake()

        tmp_img = np.zeros((img.shape),dtype=np.uint8)

        try:
            left_eyes = self._left_eye_coord[t]
            for eye in left_eyes:
                self._eye_sprite.radius = eye[2]*self.eye_scalar[t]
                self._eye_sprite.write_to_image(eye[:2],tmp_img)
        except KeyError:
            pass

        try:
            right_eyes = self._right_eye_coord[t]
            for eye in right_eyes:
                self._eye_sprite.radius = eye[2]*self.eye_scalar[t]
                self._eye_sprite.write_to_image(eye[:2],tmp_img)
        except KeyError:
            pass

        return pyfx.util.alpha_composite(img,tmp_img)
