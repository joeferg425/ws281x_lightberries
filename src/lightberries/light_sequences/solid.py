"""Creates array of RGB tuples that are all one color."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence


class SequenceSolid(ArraySequence):
    """Creates array of RGB tuples that are all one color."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Create array of RGB tuples that are all one color.

        Args:
        ----
            name: the name of this pattern
            led_count: the total desired length of the return array
            color: a pixel object defining the rgb values you want in the pattern
            kwargs: args for patterns


        """
        if name is None:
            name = SequenceSolid.__name__
        super().__init__(
            name=name,
            led_count=led_count,
            kwargs=kwargs,
        )
        color = self.DEFAULT_COLOR_SEQUENCE[0]
        if "color" in kwargs:
            color = kwargs["color"]
        if led_count > 0:
            self._sequence = np.array([color for i in range(int(led_count))])
        else:
            self._sequence = np.zeros((0, 3))
