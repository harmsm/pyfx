
class GlowingEyes:

    def __init__(self,face_stacks_pickle):

        face_stacks = pickle.load(open(face_stacks_pickle,'rb'))

        self._eye_sprite = pyfx.sprites.GlowingParticle(radius=4)

        self._left_eye_coord = {}
        self._right_eye_coord = {}
        for f in face_stacks:

            r = f.get_centroid("right_eye")

            rt = r[0]
            rc = r[1][0]

            for i in range(len(rt)):
                to_write = (rc[i,1],rc[i,0],rc[i,2])
                try:
                    self._right_eye_coord[rt[i]].append(to_write)
                except KeyError:
                    self._right_eye_coord[rt[i]] = [to_write]

            l = f.get_centroid("left_eye")

            lt = l[0]
            lc = l[1][0]

            for i in range(len(lt)):
                to_write = (lc[i,1],lc[i,0],lc[i,2])
                try:
                    self._left_eye_coord[lt[i]].append(to_write)
                except KeyError:
                    self._left_eye_coord[lt[i]] = [to_write]

    def write_eyes(self,frame_number,img_to_write):
        """
        Write glowing eyes for this frame number (if there are any) to
        img_to_write.
        """

        try:
            left_eye = self._left_eye_coord[frame_number]
            radius = left_eye[2]


            self._eye_sprite.radius = left_eye[2]

        except KeyError:
            pass

        try:
            right_eye = self._right_eye_coord[frame_number]
        except KeyError:
            pass
