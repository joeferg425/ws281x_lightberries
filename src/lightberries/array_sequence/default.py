"""Creates an array of random colors."""

from __future__ import annotations

from lightberries.array_sequence.array_sequence import ArraySequence
from lightberries.array_sequence.repeat import SequenceRepeat
from lightberries.pixel_sequence import PixelSequence


class SequenceDefault(ArraySequence):
    """Creates an array of default colors."""

    def __init__(
        self,
        led_count: int | None = None,
        name: str | None = None,
    ) -> None:
        """Create an array of default colors.

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
            name = SequenceDefault.__name__
        pixel_sequence = self.get_monthly_color_sequence()
        if led_count is None:
            led_count = len(pixel_sequence)
        if led_count > pixel_sequence.led_count:
            pixel_sequence = SequenceRepeat(led_count=led_count, pixel_sequence=pixel_sequence)
        elif led_count < pixel_sequence.led_count:
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence[:led_count])
        super().__init__(
            pixel_sequence=pixel_sequence,
            led_count=led_count,
            name=name,
        )
