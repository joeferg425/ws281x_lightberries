"""Creates an array of random colors."""

from __future__ import annotations

from lightberries.array_sequence.array_sequence import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.base.pixel import Pixel
from lightberries.pixel_sequence import PixelColor, PixelSequence


class SequencePseudoRandom(ArraySequence):
    """Creates an array of random colors."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | list[PixelColor] | None = None,
        name: str | None = None,
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

        temp_array = SequenceOff(led_count=led_count)

        if isinstance(pixel_sequence, list):
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence)

        if led_count is None:
            led_count = self.get_monthly_color_sequence().led_count

        if pixel_sequence is None or pixel_sequence.led_count == 0:
            for i in range(led_count):
                temp_array[i] = Pixel(PixelColor.get_PSEUDO_RANDOM())
        else:
            for i in range(led_count):
                temp_array[i] = pixel_sequence.get_random_pixel()

        super().__init__(
            pixel_sequence=temp_array,
            led_count=led_count,
            name=name,
        )
