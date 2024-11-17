"""A more versatile version of CreateRainbow."""

from __future__ import annotations

from math import ceil

import numpy as np

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.base.pixel import Pixel
from lightberries.pixel_sequence import PixelSequence


class SequenceTransition(ArraySequence):
    """A more versatile version of CreateRainbow."""

    def __init__(  # noqa: C901, PLR0912
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        wrap: bool | None = None,
    ) -> None:
        """More versatile version of CreateRainbow.

        The user specifies a color sequence and the number of steps (LEDs)
        in the transition from one color to the next.

        Args:
        ----
            name: the name of this pattern
            led_count: The total totalArrayLength of the final sequence in LEDs. This
                parameter is optional and defaults to LED_INDEX_COUNT
            wrap: set true to wrap the transition from the last color back to the first
            pixel_sequence: a sequence of colors to merge between
            kwargs: args for patterns

        """
        if name is None:
            name = SequenceTransition.__name__
        if pixel_sequence is None:
            pixel_sequence = self.get_monthly_color_sequence()
            if led_count is not None and led_count < pixel_sequence.led_count:
                pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence[:led_count])
        elif isinstance(pixel_sequence, list):
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence)
        if pixel_sequence.led_count == 0:
            pixel_sequence = self.get_monthly_color_sequence()
        if led_count is None:
            led_count = pixel_sequence.led_count
        count = 0
        transition_count = None
        wrap_offset = 0
        if wrap is None:
            wrap = self.get_random_boolean()
        if wrap is True:
            wrap_offset = 0
        else:
            wrap_offset = -1
        if pixel_sequence.led_count <= 1:
            wrap_offset = 0
        # figure out how many LEDs per color change
        if transition_count is None:
            transition_count = ceil(led_count / (pixel_sequence.led_count + wrap_offset))
        # create temporary array
        temp_array = SequenceOff(led_count=led_count).array
        this_color = pixel_sequence[0]
        next_color = pixel_sequence[1 % pixel_sequence.led_count]
        temp_pixels: list[Pixel] = []
        # step through color sequence
        if transition_count:
            for input_index, output_index in enumerate(range(0, led_count, transition_count)):
                if (output_index + transition_count) >= led_count:
                    transition_count = led_count - output_index
                # figure out the current and next colors
                if input_index < pixel_sequence.led_count or (wrap and input_index < pixel_sequence.led_count):
                    this_color = pixel_sequence[input_index % pixel_sequence.led_count]
                if (input_index + 1) < pixel_sequence.led_count or (wrap and input_index < pixel_sequence.led_count):
                    next_color = pixel_sequence[(input_index + 1) % pixel_sequence.led_count]
                # handle red, green, and blue individually
                for rgb_index in range(len(this_color)):
                    # linspace creates the array of values from arg1, to arg2, in exactly arg3 steps
                    temp_array[output_index : (output_index + transition_count), rgb_index] = np.linspace(
                        this_color.rgb_array[rgb_index],
                        next_color.rgb_array[rgb_index],
                        transition_count,
                    )
                count += transition_count
        temp_pixels: list[Pixel] = [Pixel(temp_array[i]) for i in range(len(temp_array))]
        super().__init__(
            name=name,
            led_count=led_count,
            pixel_sequence=temp_pixels,
        )
