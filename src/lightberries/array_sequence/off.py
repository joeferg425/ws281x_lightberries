"""Creates array of RGB tuples that are all off."""

from __future__ import annotations

from lightberries.array_sequence.array_sequence import ArraySequence
from lightberries.base.pixel import Pixel, PixelColor
from lightberries.pixel_sequence import PixelSequence


class SequenceOff(ArraySequence):
    """Creates array of RGB tuples that are all off."""

    def __init__(
        self,
        led_count: int | None = None,
        name: str | None = None,
    ) -> None:
        """Create array of RGB tuples that are all off.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            pixel_sequence: array of pixels
            kwargs: args for patterns

        """
        if name is None:
            name = SequenceOff.__name__
        if led_count is None:
            led_count = len(PixelSequence.get_monthly_color_sequence())
        pixel_sequence = PixelSequence(
            pixel_sequence=[Pixel(PixelColor.OFF) for _ in range(led_count)],
        )
        super().__init__(
            name=name,
            pixel_sequence=pixel_sequence,
            led_count=led_count,
        )
