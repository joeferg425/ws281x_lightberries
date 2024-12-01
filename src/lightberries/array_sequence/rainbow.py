"""Create a color gradient array."""

from __future__ import annotations

from lightberries.array_sequence.array_sequence import ArraySequence
from lightberries.array_sequence.transition import SequenceTransition
from lightberries.base.pixel import PixelColor
from lightberries.pixel_sequence import PixelSequence


class SequenceRainbow(ArraySequence):
    """Create a color gradient array."""

    def __init__(
        self,
        led_count: int | None = None,
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
        if led_count is None:
            led_count = self.get_monthly_color_sequence().led_count
        pixel_sequence = PixelSequence(
            pixel_sequence=[
                PixelColor.RED,
                PixelColor.GREEN,
                PixelColor.BLUE,
                PixelColor.VIOLET,
            ],
        )
        super().__init__(
            name=name,
            pixel_sequence=SequenceTransition(
                led_count=led_count,
                pixel_sequence=pixel_sequence,
                wrap=wrap,
            ),
        )
