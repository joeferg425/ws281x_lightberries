"""Creates a repeating gradient."""

from __future__ import annotations

from typing import Any

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.array_sequence.rainbow import SequenceRainbow
from lightberries.array_sequence.repeat import SequenceRepeat


class SequenceRainbowRepeating(ArraySequence):
    """Creates a repeating gradient."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        segment_length: int | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create a repeating gradient .

        Args:
        ----
            name: the name of this pattern
            led_count: the number of LEDs to involve in the rainbow
            segment_length: the length of each mini rainbow in the repeating sequence
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceRainbowRepeating.__name__
        super().__init__(
            name=name,
            led_count=led_count,
            **kwargs,
        )
        if segment_length is None:
            segment_length = led_count // 4
        self._array = SequenceRepeat(
            led_count=led_count,
            color_sequence=SequenceRainbow(led_count=segment_length, wrap=True).ndarray,
        ).ndarray
