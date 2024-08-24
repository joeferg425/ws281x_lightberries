"""Creates a repeating LightPattern from a given sequence."""

from __future__ import annotations

from typing import Any

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel import Pixel, PixelColor
from lightberries.pixel_sequence import PixelSequence


class SequenceRepeat(ArraySequence):
    """Creates a repeating LightPattern from a given sequence."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create a repeating LightPattern from a given sequence.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            pixel_array: array of pixels
            pixel_array: sequence of RGB tuples
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceRepeat.__name__

        if pixel_array is None:
            pixel_array = PixelSequence.default_color_sequence_by_month()
        elif isinstance(pixel_array, list):
            pixel_array = PixelSequence(pixel_array=pixel_array)

        if led_count is None:
            led_count = pixel_array.led_count

        _pixel_array: list[Pixel] = []
        if len(pixel_array) == 0:
            _pixel_array = [Pixel(PixelColor.OFF)]
        else:
            _pixel_array = list(SequenceOff(led_count=led_count))
            if led_count > pixel_array.led_count:
                _pixel_array[0 : pixel_array.led_count] = pixel_array
                for i in range(0, led_count, pixel_array.led_count):
                    if i + pixel_array.led_count <= led_count:
                        _pixel_array[i : i + pixel_array.led_count] = _pixel_array[0 : pixel_array.led_count]
                    else:
                        extra = (i + pixel_array.led_count) % led_count
                        end = (i + pixel_array.led_count) - extra
                        _pixel_array[i:end] = _pixel_array[0 : (pixel_array.led_count - extra)]
        super().__init__(
            name=name,
            led_count=led_count,
            pixel_array=_pixel_array,
            kwargs=kwargs,
        )
