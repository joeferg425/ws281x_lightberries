"""Color patterns and sequences."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.pixel import Pixel, PixelColors

if TYPE_CHECKING:
    from collections.abc import Sequence

LOGGER = logging.getLogger("lightBerries")


class PixelSequence:
    """A pattern of lights."""

    DEFAULT_TWINKLE_COLOR = PixelColors.GRAY
    DEFAULT_BACKGROUND_COLOR = PixelColors.OFF
    ALL_PATTERNS: ClassVar[dict[str, PixelSequence]] = {}

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:  # noqa: ARG002
        """Create a pattern of lights.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns

        """
        if name is None:
            name = PixelSequence.__name__
        self.ALL_PATTERNS[name] = self
        self._sequence: np.ndarray[(3, Any), np.int32] = np.array(
            [PixelColors.OFF.array for i in range(int(led_count))],
        )

    @staticmethod
    def pixel_array_to_numpy_array(
        color_sequence: Sequence[Pixel],
    ) -> np.ndarray[(3, Any), np.int32]:
        """Convert an array of Pixels into a numpy array of rgb arrays.

        Args:
        ----
            color_sequence: a list of Pixel objects

        Returns:
        -------
            a numpy array of int arrays representing a string of rgb values

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPatternException: if something bad happens

        """
        try:
            if len(color_sequence) > 0:
                return np.array([Pixel(p).array for p in color_sequence])
            return np.zeros((0, 3))
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex

    def sequence(self) -> np.ndarray[(3, Any), np.int32]:
        """Get the light sequence.

        Returns
        -------
            the light sequence

        """
        return self._sequence
