
import pyfx
import numpy as np
import copy

class MultiClip:
    """
    Class for managing a collection of clips. Each clip has a variety of
    properties:
        layer (from bottom to top, indexed from 0 to 1)
        alpha (opacity, from 0 (transparent) to 1 (opaque))
        start (when, in time, to start the clip)

    Clips can be acccessed by the VideoClip.name or by the layer number.
    """

    def __init__(self):

        self._clips = []         # list of clip instances (stable, order they
                                 # are added)
        self._clip_to_layer = [] # clip layers (indexed by order added)
        self._clip_start = []    # clip start times (indexed by order added)
        self._clip_alpha = []    # alpha for clip level (indexed by order added)

        self._name_to_clip = {}  # dictionary keying videoclip name to position
                                 # in "_clips" list

        self._layer_to_clip = []  # list that maps layer to position in
                                  # _clips list

        self._shape = None        # dimensions of the video clips included

    def _parse_clip_id(self,clip_id):
        """
        User can specify clip_id as either the layer number or the name of the
        clip. Private function parses this input and returns the internal clip
        index.
        """

        # Parse a string
        if type(clip_id) is str:
            try:
                index = self._name_to_clip[clip_id]
            except KeyError:
                err = "\n\nclip '{}' not recognized.  Clips are: \n".format(clip_id)
                for c in self._name_to_clip.keys():
                    err += "    {}\n".format(c)
                err += "\n\n"
                raise ValueError(err)

        # Parse a non-string.
        else:
            try:
                layer = int(clip_id)
            except TypeError:
                err = "\n\nclip '{}' not recognized.  Should be integer or string name\n".format(clip_id)
                raise ValueError(err)

            # Convert to an index
            try:
                index = self._layer_to_clip[layer]
            except IndexError:
                err = "layer {} not found\n".format(layer)
                raise IndexError(layer)

        return index

    def _update_clip_to_layer(self):
        """
        Synchronize clip_to_layer to match whatever is in clip_to_layer.
        """

        self._clip_to_layer = [None for _ in range(len(self._layer_to_clip))]
        for layer in range(len(self._layer_to_clip)):
            clip = self._layer_to_clip[layer]
            self._clip_to_layer[clip] = layer

    def get_frame(self,t):
        """
        Get the composite frame at time t.  Return as an array.
        """

        # Determine what clips overlap this time point
        include = []
        for i, c in enumerate(self._clips):

            start = self._clip_start[i]
            length = c.max_time

            if t >= start and t < (start + length):
                include.append(self._clip_to_layer[i])

        # Reverse sort by layers.
        include.sort(reverse=True)

        # Return black if no layers have frames at this time point
        if len(include) == 0:
            frame = np.zeros((size[0],size[1],4),dtype=np.uint8)
            frame = frame[:,:,3] = 255

        # If a single layer
        else:

            combined_frame = None
            for i in range(len(include)):

                # Figure out internal index corresponding to this layer
                index = self._layer_to_clip[include[i]]

                # The frame coming out of a video clip will be a four-channel,
                # np.uint8 array.
                frame = self._clips[index].get_frame(t + self._clip_start[index])

                # If alpha for this frame is not 1, apply the requested alpha
                # channel
                if self._clip_alpha[index] != 1:

                    if self._clip_alpha[index] == 0:
                        frame[:,:,3] = 0
                    else:
                        frame[:,:,3] = np.array(np.round(frame[:,:,3]*self._clip_alpha[index]),
                                                dtype=np.uint8)

                if combined_frame is None:
                    combined_frame = frame
                else:
                    combined_frame = pyfx.util.alpha_composite(combined_frame,frame)

        return combined_frame

    def add_clip(self,videoclip,layer=None,start=0,alpha=1.0):
        """
        Add a new clip to the multiclip.

        videoclip: VideoClip instance
        layer: layer in which to add it.  If None, put on top (last layer).
        start: frame to start the video
        alpha: opacity for the layer
        """

        # Make sure the videoclip is a VideoClip object
        if type(videoclip) is not pyfx.VideoClip:
            err = "videoclip does not appear to be a videoclip object\n"
            raise ValueError(err)

        # Make sure new videoclip has the same dimensions as the old video
        # clip.
        if self.shape is not None:
            if self.shape != videoclip.shape:
                err = "The new VideoClip has dimension {}, but the MultiClip has dimension {}.\n".format(videoclip.shape,
                                                                                                         self.shape)
                raise ValueError(err)

        # See if the clip has already been added
        try:
            self._name_to_clip[videoclip.name]
            err = "a video clip with the name '{}' has already been added\n".format(videoclip.name)
            raise ValueError(err)
        except KeyError:
            pass

        # Make sure layer argument is sane and interpretable before adding anythings
        if layer is not None:
            try:
                tmp = self._clip_to_layer[:]
                start_len = len(tmp)
                tmp.insert(layer,0)
                if len(tmp) != start_len + 1:
                    raise TypeError
            except TypeError:
                err = "layer {} not recognized\n".format(layer)
                raise ValueError(err)

        # Add clip and its properties
        self._clips.append(videoclip)
        self._clip_start.append(start)
        self._clip_alpha.append(alpha)
        if self._shape is None:
            self._shape = copy.deepcopy(videoclip.shape)

        # Update dictionary mapping clip name to its underlying index
        index = len(self._clips) - 1
        self._name_to_clip[videoclip.name] = index

        # If no layer is specified, append to the end
        if layer is None:
            self._layer_to_clip.append(index)
            self._clip_to_layer.append(len(self._layer_to_clip) - 1)

        # Insert layer
        else:
            self._layer_to_clip.insert(layer,index)
            self._update_clip_to_layer()

    def raise_clip(self,clip_id,to_top=False):
        """
        Raise a clip to the next layer above. If to_top is True, move the
        layer to the top.
        """

        index = self._parse_clip_id(clip_id)
        current_layer = self._clip_to_layer[index]

        # If already at top, done
        if current_layer == len(self._layer_to_clip) - 1:
            return

        # If sending to the top...
        if to_top:
            this_index = self._layer_to_clip.pop(current_layer)
            self._layer_to_clip.append(this_index)

        # Swap with layer above
        else:
            c1 = self._layer_to_clip.pop(index)
            c2 = self._layer_to_clip.pop(index)

            self._layer_to_clip.insert(index,c1)
            self._layer_to_clip.insert(index,c2)

        self._update_clip_to_layer()


    def lower_clip(self,clip_id,to_bottom=False):
        """
        Lower a clip to the next layer below. If to_bottom is True, move the
        layer to the bottom.
        """

        index = self._parse_clip_id(clip_id)
        current_layer = self._clip_to_layer[index]

        # If already at bottom, done
        if current_layer == 0:
            return

        # If going to the bottom
        if to_bottom:
            this_index = self._layer_to_clip.pop(current_layer)
            self._layer_to_clip.insert(0,this_index)

        # Swap with laber below
        else:
            c1 = self._layer_to_clip.pop(current_layer-1)
            c2 = self._layer_to_clip.pop(current_layer-1)

            self._layer_to_clip.insert(current_layer-1,c1)
            self._layer_to_clip.insert(current_layer-1,c2)

        self._update_clip_to_layer()

    def set_clip_layer(self,clip_id,layer):
        """
        Move the clip to a layer.
        """

        index = self._parse_clip_id(clip_id)

        try:
            layer = int(layer)
            self._layer_to_clip[layer]
        except ValueError:
            err = "layer must be interpretable as an int\n"
            raise ValueError(err)
        except IndexErrror:
            err = "layer {} is not found\n".format(layer)
            raise ValueError(err)

        # If the layer is already the specified layer, don't do anything
        if self._clip_to_layer == layer:
            return

        # Remove the clip from its original location and insert it at layer
        self._layer_to_clip.pop(self._clip_to_layer[index])
        self._layer_to_clip.insert(layer,index)
        self._update_clip_to_layer()


    def shift_clip_start(self,clip_id,shift_by=0):
        """
        Shift the start position of the clip by shift_by.
        """

        index = self._parse_clip_id(clip_id)

        current_pos = self._clip_start[index]
        try:
            new_pos = int(shift_by) + current_pos
        except ValueError:
            err = "shift_by must be interpretable as an integer\n"
            raise ValueError(err)

        self._clip_start[index] = new_pos

    def set_clip_start(self,clip_id,start_position=0):
        """
        Set the clip start position to start_position.
        """

        index = self._parse_clip_id(clip_id)

        try:
            new_pos = int(start_position)
        except ValueError:
            err = "start_position must be interpretable as an integer\n"
            raise ValueError(err)

        self._clip_start[index] = new_pos

    def get_clip_start(self,clip_id):
        """
        Get the clip start value.
        """

        index = self._parse_clip_id(clip_id)
        return self._clip_start[index]

    def set_clip_alpha(self,clip_id,alpha_value=1.0):
        """
        Set the clip alpha value to alpha_value.
        """

        index = self._parse_clip_id(clip_id)

        if alpha_value <= 0 or alpha_value >= 1.0:
            err = "alpha_value must be between 0 and 1\n"
            raise ValueError(err)

        self._clip_alpha[index] = alpha_value

    def get_clip_alpha(self,clip_id):
        """
        Get the clip alpha value.
        """

        index = self._parse_clip_id(clip_id)
        return self._clip_alpha[index]

    @property
    def clips(self):
        """
        Return VideoClip objects, ordered from bottom to top layer.
        """
        return [self._clips[x] for x in self._layer_to_clip]

    @property
    def starts(self):
        """
        Return starting from for clips, ordered from bottom to top layer.
        """
        return [self._clip_start[x] for x in self._layer_to_clip]

    @property
    def alphas(self):
        """
        Return alphas for each clip, ordered from bottom to top layer.
        """
        return [self._clip_alpha[x] for x in self._layer_to_clip]

    @property
    def shape(self):
        """
        Return video clip dimensions.
        """
        return self._shape
