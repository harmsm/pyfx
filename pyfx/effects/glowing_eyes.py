__description__ = \
"""
Find the eyes of people in a frame and then give them glowing orbs instead
of normal eyes.
"""
__author__ = "Michael J. Harms"
__date__ = "2018-12-19"

import pyfx
from .base import Effect
import numpy as np

class GlowingEyes(Effect):
    """
    Give people in a collection of frames glowing eyes.  The eyes are found
    along the entirety of the video clip, and then interpolated for gaps where
    the eyes were missed.  As a result, this clas has a huge .bake() call with
    a lot of options.

    Waypoint properties

    eye_scalar: float, how big to make the eyes relative to the size of the
                eye found by dlib.
    """

    def __init__(self,videoclip):

        self._default_waypoint = {"eye_scalar":1.0}

        super().__init__(videoclip)

        self._baked = False

    def bake(self,
             training_data=None,
             max_time_gap=5,
             p_cutoff=0.9,
             real_cutoff=100,
             min_time_visible=5,
             smooth_window_len=0):
        """
        Prep for the glowing eyes effect by finding eyes over the course of the
        video clip.

        training_data: dlib face training data.  If None, use the default model
        max_time_gap: maximum time gap over which a facial feature is not seen
                      that can be interpolated.
        max_time_gap: maximum time over which two similar faces are considered
                      the same without observing the face at intermediate times
        p_cutoff: minimum probability at which two faces are considered the same
                  when comparing a newly found face to a collection of previously
                  identified faces.
        real_cutoff: maximum Euclidian distance between two faces for which they
                     are considered the same
        min_time_visible: do not return any face stacks in which the minimum time
                          seen is less than min_time_visible.
        smooth_window_len: how much to smooth the interpolated trajectories.
        """

        self._human_faces = pyfx.processors.HumanFaces(self._videoclip,
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

                # make sure radius does not end up negaitve due to numerical
                # error
                if rc[i,2] < 0: rc[i,2] = 0.0

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

                # make sure radius does not end up negaitve due to numerical
                # error
                if lc[i,2] < 0: lc[i,2] = 0.0

                # Left eye coordinates (x, y, r)
                to_write = (lc[i,1],lc[i,0],lc[i,2])
                try:
                    self._left_eye_coord[lt[i]].append(to_write)
                except KeyError:
                    self._left_eye_coord[lt[i]] = [to_write]

        self._interpolate_waypoints(smooth_window_len)

        # make sure interpolated eye scalar does not end up negative
        self.eye_scalar[self.eye_scalar < 0] = 0.0

        self._baked = True

    def render(self,img):

        t = self._videoclip.current_time
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
