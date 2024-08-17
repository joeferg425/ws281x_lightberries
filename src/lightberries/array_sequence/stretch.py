"""Takes a sequence of input colors and repeats each element the requested number of times."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.off import SequenceOff

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class SequenceStretch(ArraySequence):
    """Takes a sequence of input colors and repeats each element the requested number of times."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        color_sequence: NDArray[np.int32] | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Take a sequence of input colors and repeats each element the requested number of times.

        Args:
        ----
            name: the name of this pattern
            led_count: The total totalArrayLength of the final sequence in LEDs. This
                parameter is optional and defaults to LED_INDEX_COUNT
            color_sequence: a list of pixels defining the desired colors in the output array
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceStretch.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)

        if color_sequence is None:
            color_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
        color_sequence_length = color_sequence.shape[0]
        repeats = int(led_count / color_sequence_length)
        if led_count % color_sequence_length > 0:
            repeats += 1
        temp_array = SequenceOff(color_sequence_length * repeats).sequence
        for i in range(color_sequence_length):
            temp_array[i * repeats : (i + 1) * repeats] = color_sequence[i]
        self._sequence = temp_array[:led_count]
