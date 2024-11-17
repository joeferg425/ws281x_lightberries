"""Creates a repeating LightPattern from a given sequence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from lightberries.base.pixel import Pixel


class SequenceRepeating(ArraySequence):
    """Creates a repeating LightPattern from a given sequence."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
    ) -> None:
        """Create a repeating LightPattern from a given sequence.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            pixel_sequence: sequence of RGB tuples
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceRepeating.__name__

        super().__init__(
            name=name,
            led_count=led_count,
        )

        if pixel_sequence is None:
            pixel_sequence = PixelSequence.get_monthly_color_sequence().list
        elif isinstance(pixel_sequence, PixelSequence):
            pixel_sequence = pixel_sequence.copy().list
        else:
            pixel_sequence = pixel_sequence.copy()

        if led_count is None:
            led_count = len(pixel_sequence)

        if len(pixel_sequence) == 0:
            self._array = []
        else:
            sequence_length = len(pixel_sequence)
            temp_array = SequenceOff(led_count=led_count).list
            if led_count > sequence_length:
                temp_array[0:sequence_length] = pixel_sequence
                for i in range(0, led_count, sequence_length):
                    if i + sequence_length <= led_count:
                        temp_array[i : i + sequence_length] = temp_array[0:sequence_length]
                    else:
                        extra = (i + sequence_length) % led_count
                        end = (i + sequence_length) - extra
                        temp_array[i:end] = temp_array[0 : (sequence_length - extra)]
            self._array = temp_array
