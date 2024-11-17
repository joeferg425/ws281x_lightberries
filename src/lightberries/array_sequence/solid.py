"""Creates array of RGB tuples that are all one color."""

from __future__ import annotations

from lightberries.array_sequence.base import ArraySequence
from lightberries.base.logger import LOGGER
from lightberries.base.pixel import Pixel, PixelColor
from lightberries.pixel_sequence import PixelSequence


class SequenceSolid(ArraySequence):
    """Creates array of RGB tuples that are all one color."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        color: Pixel | PixelColor | None = None,
    ) -> None:
        """Create array of RGB tuples that are all one color.

        Args:
        ----
            name: the name of this pattern
            led_count: the total desired length of the return array
            pixel_sequence: array of pixels
            color: a pixel object defining the rgb values you want in the pattern
            kwargs: args for patterns


        """
        if name is None:
            name = SequenceSolid.__name__
        if color is None:
            pixel = self.get_monthly_color_sequence()[0]
        elif isinstance(color, PixelColor):
            pixel = Pixel(color)
        else:
            pixel = color
        if pixel_sequence is None:
            if led_count is not None:
                sqnc = [pixel for _ in range(int(led_count))]
            else:
                sqnc = [pixel for _ in self.get_monthly_color_sequence()]
            pixel_sequence = PixelSequence(pixel_sequence=sqnc)
        elif isinstance(pixel_sequence, list):
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence)
        if led_count is None:
            led_count = pixel_sequence.led_count
        if led_count > pixel_sequence.led_count:
            pixel_sequence = PixelSequence(pixel_sequence=[pixel for _ in range(int(led_count))])
        super().__init__(
            name=name,
            pixel_sequence=pixel_sequence,
        )
        LOGGER.debug("%s %d : %s", SequenceSolid.__name__, led_count, pixel)
