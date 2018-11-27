import dlib
import numpy as np
from skimage import draw, util, color
from scipy import spatial, interpolate

from PIL import Image

import copy, string, random, os, warnings

class FaceFinder:
    """
    Use dlib to find facial landmarks given a set of trained data and an
    input image.
    """

    def __init__(self,training_data):

        self._training_data = training_data

        self._detector = dlib.get_frontal_face_detector()
        self._predictor = dlib.shape_predictor(self._training_data)

    def detect(self,bw_array):
        """
        Detect facial landmarks given a black and white image.
        """

        # Make sure this is in a 0-255 single channel format
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bw_array = util.img_as_ubyte(bw_array)

        # Search for faces
        faces = self._detector(bw_array, 1)

        # loop over the detected faces
        face_coord = []
        for face in faces:

            # determine the facial landmarks for the face region, then
            # convert the landmark (x, y)-coordinates to a NumPy array
            shape = self._predictor(bw_array, face)
            coord = np.zeros((shape.num_parts, 2), dtype=np.int)

            # loop over all facial landmarks and convert them
            # to a 2-tuple of (x, y)-coordinates
            for i in range(0, shape.num_parts):
                coord[i] = (shape.part(i).x, shape.part(i).y)

            # record the coordinates
            face_coord.append(coord)

        return face_coord

class FaceStack:
    """
    Hold a stack of facial landmarks extracted from images as a function of
    time.
    """

    def __init__(self,face_coords,current_time=0,max_time_gap=5):

        self._face_coord = []
        self._face_time = []
        self._max_time_gap = max_time_gap

        self._face_coord.append(face_coords)
        self._face_time.append(current_time)

        self._landmark_indexes = {"jaw":(0, 17),
                                  "right_eyebrow":(17, 22),
                                  "left_eyebrow":(22, 27),
                                  "nose":(27, 36),
                                  "right_eye":(36, 42),
                                  "left_eye":(42, 48),
                                  "mouth":(48, 68)}

    def get_dist(self,other_face_coords):
        """
        Return the Euclidian distance between an observed set of face
        coordinates and the last coordinates in this FaceStack.
        """

        return np.sqrt(np.sum((other_face_coords - self._face_coord[-1])**2))

    def append(self,other_face_coords,time):
        """
        Append a new observation of this face to the object.
        """

        self._face_coord.append(other_face_coords)
        self._face_time.append(time)

    def check_freshness(self,t):
        """
        Return True if this face has been observed in less than time_gap
        time steps.
        """

        if (t - self._face_time[-1]) <= self._max_time_gap:
            return True

        return False

    def get_centroid(self,landmark,fill_gaps=True):
        """
        Return the centroid of a landmark as a function of time.  Returns
        two arrays: time (1D), xy_coord of centroid (2D).
        """

        # Make sure the landmark is valid
        try:
            i, j = self._landmark_indexes[landmark]
        except KeyError:
            err = "landmark {} not recognized. Landmark should be one of:\n\n".format(landmark)
            err += ",".join(self.available_landmarks)
            raise ValueError(err)

        # Get centroid over time
        t = []
        mean_x = []
        mean_y = []
        for k, coord in enumerate(self._face_coord):

            t.append(self._face_time[k])

            landmark_coord = coord[i:j]
            mean_x.append(np.mean(landmark_coord[:,0]))
            mean_y.append(np.mean(landmark_coord[:,1]))

        # Interpolate
        if fill_gaps:

            fx = interpolate.interp1d(np.array(t),np.array(mean_x),kind='cubic')
            fy = interpolate.interp1d(np.array(t),np.array(mean_y),kind='cubic')

            out_t = np.array(range(min(self._face_time),max(self._face_time)+1),dtype=np.uint8)
            out_x = fx(out_t)
            out_y = fy(out_t)

        else:
            out_t = np.array(t)
            out_x = np.array(mean_x)
            out_y = np.array(mean_y)

        # Construct output
        out_coord = np.dstack((out_x,out_y))

        return out_t, out_coord

    def get_hull(self,landmark):
        """
        Return the polygon defined by the convex hull of the feature as a
        function of time.  Returns a 1D numpy array for time and a python
        list of tuples, each containing numpy arrays.

        For a FaceStack trained on a list of images with shape = dimensions:

        mask = np.zeros(dimensions,dtype=np.bool)
        t, coord_out = self.get_hull("left_eye")
        mask[coord_out[0][0],coord_out[0][1]] = True

        The mask would now have the polygon of the first time point.
        """

        # Make sure the landmark is valid
        try:
            i, j = self._landmark_indexes[landmark]
        except KeyError:
            err = "landmark {} not recognized. Landmark should be one of:\n\n".format(landmark)
            err += ",".join(self.available_landmarks)
            raise ValueError(err)

        # Get hull over time
        t = []
        hull_out = []
        for k, coord in enumerate(self._face_coord):

            t.append(self._face_time[k])

            # grab the (x, y)-coordinates associated with the
            # face landmark
            landmark_coord = coord[i:j]

            # compute the convex hull of the facial landmark coordinates
            hull = spatial.ConvexHull(landmark_coord)
            r = landmark_coord[hull.vertices,0]
            c = landmark_coord[hull.vertices,1]

            # Fill in the convex hull
            hull_out.append(draw.polygon(r,c))

        return np.array(t), hull_out

    @property
    def available_landmarks(self):

        return list(self._landmark_indexes.keys())

    @property
    def time_visible(self):

        return self._face_time[-1] - self._face_time[0]

def find_face_stacks(img_list,
                     max_time_gap=5,
                     p_cutoff=0.9,
                     real_cutoff=100,
                     min_time_visible=5):
    """
    Return a list of FaceStack instances extracted from

    """

    # Create detector for finding face features
    detector = FaceFinder(training_data)

    # Go through list of images
    faces_seen = []
    stale_faces = []
    for t, img in enumerate(img_list):

        # If image list is full of strings, load image from file
        if type(img) is str:
            f = np.array(Image.open(img))
            img = color.rgb2gray(f)

        # Look for faces in this image
        new_faces = detector.detect(img)

        # If no faces have been seen yet, append these and continue
        if len(faces_seen) = 0:
            for nf in new_faces:
                faces_seen.append(FaceStack(nf,t))
            continue

        # Calculate distance between the new faces and the faces already seen
        face_dist = []
        for nf in new_faces:
            face_dist.append([])
            for fs in faces_seen:
                face_dist[-1].append(fs.get_dist(nf))
        face_dist = np.array(face_dist)

        # These are RMSD distnaces; convert to likelihoods and then weights
        face_score = 2*np.exp(face_dist**2)
        face_score = face_score/np.sum(face_score,1)

        # Assign new faces to old faces
        for i in range(len(new_faces)):

            assigned = False

            # If the new face is much closer to one previous face than any other...
            if np.max(face_score[i,:]) > p_cutoff:

                # If the new face is close to the previous face in absolute
                # terms ...
                j = np.argmax(face_score,i)
                if face_dist[i,j] < real_cutoff:

                    # The new face is actually one of the previously assigned
                    # faces
                    faces_seen[j].append(new_faces[i],t)
                    assigned = True

            # If this face cannot be assigned, create a new face
            if not assigned:
                faces_seen.append(FaceStack(new_faces[i],t))

        # Look for faces that have not been seen for awhile and stop
        # considering them as possible matches
        for i in rage(len(faces_seen)-1,-1,-1):
            if not faces_seen[i].check_freshness(t):
                stale_faces.append(faces_seen.pop(i))

    # The final set of FaceStacks should include both the currently active and
    # stale faces.
    faces_seen.extend(stale_faces)

    # Only take faces seen for at least min_time_visible.
    out = []
    for fs in faces_seen:
        if fs.time_visible >= min_time_visible:
            out.append(fs)

    return out
