"""Create a color gradient array."""

from __future__ import annotations

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.transition import SequenceTransition
from lightberries.base.pixel import Pixel, PixelColor, pixel_from_color
from lightberries.pixel_sequence import PixelSequence


class SequenceRainbow(ArraySequence):
    """Create a color gradient array."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        wrap: bool | None = None,
    ) -> None:
        """Create a color gradient array.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            pixel_sequence: array of pixels
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
        if pixel_sequence is None:
            pixel_sequence = PixelSequence(
                pixel_sequence=[
                    pixel_from_color(PixelColor.RED),
                    pixel_from_color(PixelColor.GREEN),
                    pixel_from_color(PixelColor.BLUE),
                    pixel_from_color(PixelColor.VIOLET),
                ],
            )
            if led_count is not None and led_count < pixel_sequence.led_count:
                pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence[:led_count])
        elif isinstance(pixel_sequence, list):
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence)
        if led_count is None:
            led_count = pixel_sequence.led_count
        super().__init__(
            name=name,
            pixel_sequence=SequenceTransition(
                led_count=led_count,
                pixel_sequence=pixel_sequence,
                wrap=wrap,
            ),
        )
