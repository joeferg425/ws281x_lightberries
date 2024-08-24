"""Creates an array of random colors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lightberries.array_sequence._array_sequence import ArraySequence

if TYPE_CHECKING:

    from lightberries.pixel import Pixel
    from lightberries.pixel_sequence import PixelSequence


class SequenceDefault(ArraySequence):
    """Creates an array of default colors."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create an array of default colors.

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
            name = SequenceDefault.__name__
        if pixel_array is None:
            pixel_array = self.default_color_sequence_by_month()
        super().__init__(
            pixel_array=pixel_array,
            led_count=led_count,
            name=name,
            **kwargs,
        )
