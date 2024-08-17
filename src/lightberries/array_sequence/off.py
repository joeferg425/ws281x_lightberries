"""Creates array of RGB tuples that are all off."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.array_sequence.base import ArraySequence
from lightberries.pixel import PixelColor


class SequenceOff(ArraySequence):
    """Creates array of RGB tuples that are all off."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create array of RGB tuples that are all off.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPatternException: if something bad happens

        """
        if name is None:
            name = SequenceOff.__name__
        super().__init__(
            name=name,
            led_count=led_count,
            **kwargs,
        )
        if led_count > 0:
            self._sequence = np.array([PixelColor.OFF.array for _ in range(int(led_count))])
        else:
            self._sequence = np.zeros((0, 3), dtype=np.int32)
