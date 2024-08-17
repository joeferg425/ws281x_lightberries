"""Creates an array of random colors."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.off import SequenceOff

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class SequencePseudoRandom(ArraySequence):
    """Creates an array of random colors."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        color_sequence: NDArray[np.int32] | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create an array of random colors.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of random colors to generate for the array
            color_sequence: optional parameter from which to draw the pseudo random colors from
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequencePseudoRandom.__name__
        super().__init__(
            led_count=led_count,
            name=name,
            **kwargs,
        )
        temp_array = SequenceOff(led_count=led_count).sequence
        if color_sequence is None:
            color_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
        input_sequence_length = color_sequence.shape[0]
        if input_sequence_length == 0:
            color_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
            input_sequence_length = color_sequence.shape[0]
        for i in range(led_count):
            temp_array[i] = color_sequence[random.randint(0, input_sequence_length - 1)]
        self._sequence = temp_array
