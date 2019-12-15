
import pyfx
from ..base import Effect

class Transition(Effect):

    def __init__(self,videoclip,pip_video,pip_start_frame=0):
        """
        videoclip: videoclip for this effect
        pip_video: If string, treat as video file. (not implemented)
                   If dir, treat as directory of png files.
                   If list, treat as list of image files corresponding to frames.
        pip_start_frame: pip video frame corresponding to 0 in the videoclip.
                         integer, which can be negative
        """

        self._pip_start_frame = pip_start_frame

        if type(pip_video) is str:
            if os.path.exists(pip_video):
                if os.path.isdir(pip_video):
                    self._img_list = glob.glob(os.path.join(pip_video,"*.png"))
                    self._img_list.sort()
                elif os.path.isfile(pip_video):
                    err = "{} appears to a video.  Not readable yet.\n".format(pip_video)
                    raise NotImplementedError(err)
                else:
                    err = "{} format not recognized\n".format(pip_video)
                    raise ValueError(err)
            else:
                err = "{} not found\n".format(pip_video)
                raise FileNotFoundError(err)
        else:
            if type(pip_video) in [list,tuple]:
                self._img_list = copy.copy(pip_video)
            else:
                err = "{} format not recognized\n".format(pip_video)
                raise ValueError(err)

        self._default_waypoint = {"picture_mask":None,
                                  "pip_offset":(0,0),
                                  "pip_scale":1.0}


    def bake(self):
        pass

    def render(self,img):

        t = self._videoclip.current_time
        if not self._baked:
            self.bake()

        new_img = img
        if self.mask[t] is not None:

            # Put mask into single channel 0-255 array
            if self.alpha[t] != 1.0:
                mask = pyfx.util.to_array(self.mask[t],
                                          num_channels=1,
                                          dtype=np.float)
                mask = pyfx.util.to_array(mask*self.alpha[t],
                                          num_channels=1,
                                          dtype=np.uint8)
            else:
                mask = pyfx.util.to_array(self.mask[t],
                                          num_channels=1,
                                          dtype=np.uint8)

            # Load background
            local_bg = self._videoclip.background.image
            if self.bg_override[t] is not None:
                local_bg = self.bg_override[t]
            bg = pyfx.util.to_array(local_bg,
                                    num_channels=4,dtype=np.uint8)

            # Load foreground and stick mask into alpha channel
            fg = pyfx.util.to_array(img,num_channels=4,dtype=np.uint8)
            fg[:,:,3] = mask

            # Alpha composite
            new_img = pyfx.util.alpha_composite(bg,fg)

            # Protect the image, if requested
            new_img = self._protect(img,new_img)

        return new_img

    def apply(self,stream_1,stream_2,**kwargs):

        if stream_1.shape[:2] != stream_2.shape[:2]:
            err = "streams do not have the same shape\n"
            raise ValueError(err)

        trans_mask = np.zeros(stream_1.shape,dtype=np.uint8)
        trans_mask = self._create_masks(trans_mask,**kwargs)

        output = np.zeros(stream_1.shape,dtype=stream_1.dtype)
        for i in range(len(stream_1.shape[2])):

            bg = pyfx.util.to_array(stream_1[:,:,i],
                                    num_channels=4,dtype=np.uint8)
            fg = pyfx.util.to_array(stream_2[:,:,i],
                                    num_channels=4,dtype=np.uint8)

            # Put mask
            fg[:,:,3] = trans_mask[:,:,i]

            # Alpha composite
            output[:,:,:,i] = pyfx.util.helper.alpha_composite(bg,fg)[:,:,:]

    def _create_masks(self,trans_mask,**kwargs):

        return trans_mask
