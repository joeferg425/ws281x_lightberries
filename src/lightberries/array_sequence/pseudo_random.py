"""Creates an array of random colors."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:

    from lightberries.pixel import Pixel


class SequencePseudoRandom(ArraySequence):
    """Creates an array of random colors."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create an array of random colors.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            pixel_array: array of pixels
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequencePseudoRandom.__name__
        if led_count is None:
            led_count = 1

        temp_array = SequenceOff(led_count=led_count)

        if pixel_array is None:
            pixel_array = self.default_color_sequence_by_month()
        elif isinstance(pixel_array, list):
            pixel_array = PixelSequence(pixel_array=pixel_array)
        if pixel_array.led_count == 0:
            pixel_array = self.default_color_sequence_by_month()

        for i in range(led_count):
            temp_array[i] = pixel_array[random.randint(0, pixel_array.led_count - 1)]

        super().__init__(
            pixel_array=temp_array,
            led_count=led_count,
            name=name,
            **kwargs,
        )
