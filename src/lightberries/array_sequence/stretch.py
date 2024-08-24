"""Takes a sequence of input colors and repeats each element the requested number of times."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:

    from lightberries.pixel import Pixel


class SequenceStretch(ArraySequence):
    """Takes a sequence of input colors and repeats each element the requested number of times."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Take a sequence of input colors and repeats each element the requested number of times.

        Args:
        ----
            name: the name of this pattern
            led_count: The total totalArrayLength of the final sequence in LEDs. This
                parameter is optional and defaults to LED_INDEX_COUNT
            pixel_array: a list of pixels defining the desired colors in the output array
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceStretch.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)

        if pixel_array is None:
            pixel_array = self.default_color_sequence_by_month()
        if isinstance(pixel_array, list):
            pixel_array = PixelSequence(pixel_array=pixel_array)
        if led_count is None:
            led_count = pixel_array.led_count
        repeats = int(led_count / pixel_array.led_count)
        if led_count % pixel_array.led_count > 0:
            repeats += 1
        temp_array = SequenceOff(pixel_array.led_count * repeats)
        for i in range(pixel_array.led_count):
            temp_array[i * repeats : (i + 1) * repeats] = pixel_array[i]
        self._array = temp_array[:led_count]
