"""Creates array of RGB tuples that are all off."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.pixel import Pixel, PixelColor, pixel_from_color

if TYPE_CHECKING:
    from lightberries.pixel_sequence import PixelSequence


class SequenceOff(ArraySequence):
    """Creates array of RGB tuples that are all off."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
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
            led_count = 1
        if pixel_sequence is None:
            self._array = [pixel_from_color(PixelColor.OFF) for _ in range(int(led_count))]
        super().__init__(
            name=name,
            pixel_sequence=pixel_sequence,
            led_count=led_count,
            **kwargs,
        )
