

import pyfx
from .base import Effect
import numpy as np

class TextBox(Effect):
    """
    Widget

    line_resolution:

    """

    def __init__(self,
                 videoclip,
                 box_mask,
                 background=None,
                 advance_rate=5):
        """
        box_mask: image with location in which to draw text.  Should be non-zero
                  for region to draw, 0 for region to not draw.  Note, assumes
                  rectangle.

        background: background image on which to write the text.  If None,
                    non-text values are set to alpha = 0.
        """

        # text

        ## CHECK DIM
        x_stack = np.prod(box_mask != 0,1)
        y_stack = np.prod(box_mask != 0,0)

        x_range = np.arange(len(x_stack),dtype=np.int)[x_stack]
        self._x_min = np.min(x_range)
        self._x_max = np.max(x_range)

        y_range = np.arange(len(y_stack),dtype=np.int)[y_stack]
        self._y_min = np.min(y_range)
        self._y_max = np.max(y_range)


        self._default_waypoint = {"text":"",
                                  "font":"",
                                  "size":"",
                                  "color":""}

        super().__init__(videoclip)


    def bake(self):
        """

        text_stack = [[text0],
                      [text0],
                      [text0,text1],
                      [text0,text1,text2],
                      ...]
        text_position = [[-5],
                         [-4],
                         [-3,-8],
                         [-2,-7,-12],
                         ...]

        0 is bottom of box
        -5 is below bottom edge


        """

        self._interpolate_waypoints()

        # Lists holding text and positions for each frame
        text_stack = []
        text_positions = []

        current_text = self.text[0]
        if current_text is None:
            text_stack.append([])
        else:
            text_stack.append([current_text])

        for i in range(1,len(self.t)):

            # Copy previous text_stack and text_position into this time point
            text_stack.append(text_stack[-1])
            text_positions.append(text_positions[-1])

            # If the text has changed, append the text to the text_stack with
            # a negative text position
            if self.text[i] != current_text:
                current_text = self.text[i]
                text_stack[-1].insert(0,current_text)

                starting_pos = text_positions[-1][0] - (self._advance_rate + 1)
                text_positions[-1].insert(0,starting_pos)

            # If first position is negative, add one to each text position
            if text_positions[-1][0] < 0:
                for j in range(text_positions[-1]):
                    text_positions[-1][j] += 1

        #somehow map numbers to actual coordinates

        self._baked = True


    def render(self,img):

        text_on_image(img,text,location=(0,0),size=100,color=(0,0,0)):
