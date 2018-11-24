import dlib
import numpy as np
from skimage import draw, util
from scipy import spatial

class FaceFinder:

    def __init__(self,training_data):

        self._training_data = training_data

        self._detector = dlib.get_frontal_face_detector()
        self._predictor = dlib.shape_predictor(self._training_data)

        self._landmark_indexes = {"mouth":(48, 68),
                                  "right_eyebrow":(17, 22),
                                  "left_eyebrow":(22, 27),
                                  "right_eye":(36, 42),
                                  "left_eye":(42, 48),
                                  "nose":(27, 36),
                                  "jaw":(0, 17)}

    def detect(self,bw_array,look_for=("left_eye","right_eye")):

        bw_array = util.img_as_ubyte(bw_array)

        mask = np.zeros(bw_array.shape,dtype=np.float)

        # Search for faces
        faces = self._detector(bw_array, 1)

        # loop over the face detections
        for face in faces:

            # determine the facial landmarks for the face region, then
            # convert the landmark (x, y)-coordinates to a NumPy array
            shape = self._predictor(bw_array, face)
            coord = np.zeros((shape.num_parts, 2), dtype=np.int)

            # loop over all facial landmarks and convert them
            # to a 2-tuple of (x, y)-coordinates
            for i in range(0, shape.num_parts):
                coord[i] = (shape.part(i).x, shape.part(i).y)

            # loop over the facial landmark regions individually
            for name in look_for:

                # grab the (x, y)-coordinates associated with the
                # face landmark
                i, j = self._landmark_indexes[name]
                pts = coord[i:j]

                # compute the convex hull of the facial landmark coordinates
                hull = spatial.ConvexHull(pts)
                r = pts[hull.vertices,0]
                c = pts[hull.vertices,1]

                # Fill in the convex hull
                rr, cc = draw.polygon(r,c)

                # Update mask with polygon for convex hull
                mask[cc,rr] = 1

        return mask

class Stack:

    def __init__(self,training_data,look_for=("left_eye","right_eye")):

        self._finder = FaceFinder(training_data)
        self._look_for = look_for

    def stack(self,img_list):







        for i, img in enumerate(img_list):

            bw = color.rgb2gray(np.array(Image.open(img)))
            eye_mask = self._finder.detect(bw,self._look_for)
