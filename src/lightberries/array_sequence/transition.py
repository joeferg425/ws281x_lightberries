"""A more versatile version of CreateRainbow."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel import Pixel
from lightberries.pixel_sequence import PixelSequence


class SequenceTransition(ArraySequence):
    """A more versatile version of CreateRainbow."""

    def __init__(  # noqa: C901
        self,
        led_count: int | None = None,
        pixel_array: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        wrap: bool | None = None,
        **kwargs: dict[str, Any],
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
            pixel_array: a sequence of colors to merge between
            kwargs: args for patterns

        """
        if name is None:
            name = SequenceTransition.__name__
        super().__init__(
            name=name,
            led_count=led_count,
            kwargs=kwargs,
        )
        if pixel_array is None:
            pixel_array = self.default_color_sequence_by_month()
        elif isinstance(pixel_array, list):
            pixel_array = PixelSequence(pixel_array=pixel_array)
        if pixel_array.led_count == 0 or led_count == 0:
            pixel_array = self.default_color_sequence_by_month()
        if led_count is None:
            led_count = pixel_array.led_count
        count = 0
        step_count = None
        previous_step_count = 0
        wrap_offset = 0
        if wrap is None:
            wrap = self.get_random_boolean()
        if wrap is True:
            wrap_offset = 0
        else:
            wrap_offset = 1
        # figure out how many LEDs per color change
        if step_count is None:
            step_count = led_count // (pixel_array.led_count - wrap_offset)
            previous_step_count = step_count
        # create temporary array
        temp_array = SequenceOff(led_count).ndarray
        # step through color sequence
        for color_index in range(led_count - wrap_offset):
            if color_index == led_count - 1 or color_index == led_count - 2:
                step_count = led_count - count
            # figure out the current and next colors
            this_color = pixel_array[color_index]
            next_color = pixel_array[(color_index + 1) % led_count]
            # handle red, green, and blue individually
            for rgb_index in range(len(this_color)):
                i = color_index * previous_step_count
                # linspace creates the array of values from arg1, to arg2, in exactly arg3 steps
                temp_array[i : (i + step_count), rgb_index] = np.linspace(
                    this_color.array[rgb_index],
                    next_color.array[rgb_index],
                    step_count,
                )
            count += step_count
        self._array = [Pixel(temp_array[i]) for i in range(temp_array)]
