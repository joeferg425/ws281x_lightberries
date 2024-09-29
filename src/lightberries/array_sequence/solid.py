"""Creates array of RGB tuples that are all one color."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_sequence._array_sequence import ArraySequence
from lightberries.logger import LOGGER
from lightberries.pixel import Pixel, PixelColor

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from lightberries.pixel_sequence import PixelSequence



class SequenceSolid(ArraySequence):
    """Creates array of RGB tuples that are all one color."""

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        color: Pixel | PixelColor | NDArray[np.int32] | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Create array of RGB tuples that are all one color.

        Args:
        ----
            name: the name of this pattern
            led_count: the total desired length of the return array
            pixel_sequence: array of pixels
            color: a pixel object defining the rgb values you want in the pattern
            kwargs: args for patterns


        """
        if name is None:
            name = SequenceSolid.__name__
        if color is None:
            pixel = self.default_color_sequence_by_month()[0]
        elif isinstance(color, PixelColor):
            pixel = color.value
        elif isinstance(color, np.ndarray):
            pixel = Pixel(color)
        else:
            pixel = color
        if pixel_sequence is None:
            if led_count is not None:
                pixel_sequence = [pixel for _ in range(int(led_count))]
            else:
                pixel_sequence = [pixel]
        else:
            pixel_sequence = [pixel]
        super().__init__(
            name=name,
            pixel_sequence=pixel_sequence,
        )
        LOGGER.debug("%s %d : %s", SequenceSolid.__name__, led_count, pixel)
