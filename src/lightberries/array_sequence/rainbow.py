"""Create a color gradient array."""

from __future__ import annotations

from typing import Any

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.transition import SequenceTransition
from lightberries.pixel import Pixel, PixelColor, pixel_from_color
from lightberries.pixel_sequence import PixelSequence


class SequenceRainbow(ArraySequence):
    """Create a color gradient array."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        wrap: bool | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create a color gradient array.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            pixel_array: array of pixels
            wrap: set true to wrap the transition from the last color back to the first
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceRainbow.__name__
        if wrap is None:
            wrap = self.get_random_boolean()
        if pixel_array is None:
            pixel_array = PixelSequence(
                pixel_array=[
                    pixel_from_color(PixelColor.RED),
                    pixel_from_color(PixelColor.GREEN),
                    pixel_from_color(PixelColor.BLUE),
                    pixel_from_color(PixelColor.VIOLET),
                ],
            )
        super().__init__(
            name=name,
            pixel_array=SequenceTransition(
                led_count=led_count,
                pixel_array=pixel_array,
                wrap=wrap,
            ),
            kwargs=kwargs,
        )
