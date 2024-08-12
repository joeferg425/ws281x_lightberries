"""Color patterns and sequences."""

from __future__ import annotations

import datetime
import logging
from typing import Any, ClassVar

import numpy as np

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_pattern import LightPattern
from lightberries.pixel import PixelColors

LOGGER = logging.getLogger("lightBerries")


class ArrayPattern(LightPattern):
    """A pattern of lights."""

    DEFAULT_COLOR_SEQUENCE = LightPattern.pixel_array_to_numpy_array(
        [
            PixelColors.RED,
            PixelColors.GREEN,
            PixelColors.BLUE,
        ],
    )
    ARRAY_PATTERNS: ClassVar[dict[str, ArrayPattern]] = {}

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create a pattern of lights.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns

        """
        if name is None:
            name = ArrayPattern.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)
        self.ARRAY_PATTERNS[name] = self
        self._sequence: np.ndarray[(3, Any), np.int32] = np.array(
            [PixelColors.OFF.array for i in range(int(led_count))],
        )

    @classmethod
    def default_color_sequence_by_month(
        cls,
        month: int | None = None,
    ) -> np.ndarray[(3, Any), np.int32]:
        """Get the default sequence of colors defined for this month.

        Returns
        -------
            the default sequence of colors as determined by the current month

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPatternException: if something bad happens

        """
        try:
            if month is None:
                date = datetime.datetime.now()  # noqa: DTZ005
                month = date.month
            return MONTHLY_COLOR_SEQUENCE[month]
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
        return ArrayPattern.DEFAULT_COLOR_SEQUENCE


MONTHLY_COLOR_SEQUENCE: dict[int, np.ndarray[(3, Any), np.int32]] = {
    1: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.CYAN2,
            PixelColors.WHITE,
            PixelColors.CYAN,
            PixelColors.BLUE2,
            PixelColors.BLUE,
        ],
    ),
    2: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.PINK,
            PixelColors.WHITE,
            PixelColors.RED,
            PixelColors.WHITE,
        ],
    ),
    3: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.GREEN,
            PixelColors.WHITE,
            PixelColors.ORANGE,
            PixelColors.WHITE,
            PixelColors.YELLOW,
        ],
    ),
    4: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.PINK,
            PixelColors.CYAN,
            PixelColors.YELLOW,
            PixelColors.GREEN,
            PixelColors.WHITE,
        ],
    ),
    5: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.PINK,
            PixelColors.YELLOW,
            PixelColors.GREEN,
            PixelColors.WHITE,
        ],
    ),
    6: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.RED,
            PixelColors.WHITE,
            PixelColors.BLUE,
            PixelColors.GREEN,
        ],
    ),
    7: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.RED,
            PixelColors.WHITE,
            PixelColors.BLUE,
        ],
    ),
    8: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.ORANGE,
            PixelColors.WHITE,
            PixelColors.YELLOW,
            PixelColors.ORANGE2,
        ],
    ),
    9: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.RED,
            PixelColors.ORANGE,
            PixelColors.WHITE,
            PixelColors.YELLOW,
            PixelColors.ORANGE2,
            PixelColors.RED2,
        ],
    ),
    10: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.MIDNIGHT,
            PixelColors.RED,
            PixelColors.ORANGE,
            PixelColors.OFF,
        ],
    ),
    11: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.RED,
            PixelColors.MIDNIGHT,
            PixelColors.GRAY,
        ],
    ),
    12: ArrayPattern.pixel_array_to_numpy_array(
        [
            PixelColors.RED,
            PixelColors.WHITE,
            PixelColors.GREEN,
        ],
    ),
}
