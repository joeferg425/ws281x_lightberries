"""Creates a repeating LightPattern from a given sequence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from numpy.typing import NDArray


class SequenceRepeating(ArraySequence):
    """Creates a repeating LightPattern from a given sequence."""

    def __init__(
        self,
        led_count: int,
        color_sequence: PixelSequence | NDArray[np.int32] | None,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create a repeating LightPattern from a given sequence.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            color_sequence: sequence of RGB tuples
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
            **kwargs,
        )

        if color_sequence is None:
            color_sequence = PixelSequence.DEFAULT_COLOR_SEQUENCE
        elif isinstance(color_sequence, PixelSequence):
            color_sequence = color_sequence.ndarray.copy()
        else:
            color_sequence = color_sequence.copy()
        if len(color_sequence) == 0:
            self._array = np.zeros((0, 3), dtype=np.int32)
        else:
            sequence_length = len(color_sequence)
            temp_array = SequenceOff(led_count=led_count).ndarray
            if led_count > sequence_length:
                temp_array[0:sequence_length] = color_sequence
                for i in range(0, led_count, sequence_length):
                    if i + sequence_length <= led_count:
                        temp_array[i : i + sequence_length] = temp_array[0:sequence_length]
                    else:
                        extra = (i + sequence_length) % led_count
                        end = (i + sequence_length) - extra
                        temp_array[i:end] = temp_array[0 : (sequence_length - extra)]
            self._array = temp_array
