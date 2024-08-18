"""Create a color gradient array."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.transition import SequenceTransition
from lightberries.pixel import PixelColor


class SequenceRainbow(ArraySequence):
    """Create a color gradient array."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        wrap: bool | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create a color gradient array.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            wrap: set true to wrap the transition from the last color back to the first
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceRainbow.__name__
        super().__init__(name=name, led_count=led_count, kwargs=kwargs)
        if wrap is None:
            wrap = self.get_random_boolean()
        self._array = SequenceTransition(
            led_count=led_count,
            color_sequence=np.array(
                [
                    PixelColor.RED.array,
                    PixelColor.GREEN.array,
                    PixelColor.BLUE.array,
                    PixelColor.VIOLET.array,
                ],
            ),
            wrap=wrap,
        ).ndarray
