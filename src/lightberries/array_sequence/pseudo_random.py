"""Creates an array of random colors."""

from __future__ import annotations

from typing import Any

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.base.pixel import Pixel
from lightberries.pixel_sequence import PixelColor, PixelSequence


class SequencePseudoRandom(ArraySequence):
    """Creates an array of random colors."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create an array of random colors.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            pixel_sequence: array of pixels
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

        if pixel_sequence is None:
            pixel_sequence = self.default_color_sequence_by_month()
        elif isinstance(pixel_sequence, list):
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence)
        if pixel_sequence.led_count == 0:
            pixel_sequence = self.default_color_sequence_by_month()

        for i in range(led_count):
            temp_array[i] = Pixel(PixelColor.pseudo_random())

        super().__init__(
            pixel_sequence=temp_array,
            led_count=led_count,
            name=name,
            **kwargs,
        )
