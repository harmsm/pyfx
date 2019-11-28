
import pyfx

class Transition:

    def __init__(self):
        pass

    def apply(self,stream_1,stream_2,**kwargs):

        if stream_1.shape != stream_2.shape:
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
            output[:,:,:,i] = pyfx.util.alpha_composite(bg,fg)[:,:,:]


    def _create_masks(self,trans_mask,**kwargs):

        return trans_mask
