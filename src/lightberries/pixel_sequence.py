"""Color patterns and sequences."""

from __future__ import annotations

import datetime
import logging
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from lightberries.pixel import Pixel, PixelColor

if TYPE_CHECKING:

    from numpy.typing import NDArray

LOGGER = logging.getLogger("lightBerries")


class PixelSequence:
    """A pattern of lights."""

    DEFAULT_TWINKLE_COLOR = PixelColor.GRAY
    DEFAULT_BACKGROUND_COLOR = PixelColor.OFF
    ALL_SEQUENCES: ClassVar[dict[str, type[PixelSequence]]] = {}
    DEFAULT_COLOR_SEQUENCE: NDArray[np.int32] = np.array(
        [
            PixelColor.RED.array,
            PixelColor.GREEN.array,
            PixelColor.BLUE.array,
        ],
        dtype=np.int32,
    )

    def __init_subclass__(cls) -> None:
        cls.ALL_SEQUENCES[cls.__name__.replace("Sequence", "")] = cls

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Create a pattern of lights.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns

        """
        if name is None:
            name = PixelSequence.__name__
        self._sequence: NDArray[np.int32] = np.array(
            [PixelColor.OFF.array for _ in range(int(led_count))],
        )

    @staticmethod
    def pixel_array_to_numpy_array(
        color_sequence: Sequence[Pixel] | NDArray[np.int32],
    ) -> NDArray[np.int32]:
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
        if len(color_sequence) > 0:
            if isinstance(color_sequence, Sequence):
                return np.array([Pixel(p).array for p in color_sequence])
            return color_sequence
        return np.zeros((0, 3), dtype=np.int32)

    @property
    def sequence(self) -> NDArray[np.int32]:
        """Get the light sequence.

        Returns
        -------
            the light sequence

        """
        return self._sequence
        return self._sequence
        return self._sequence

    @classmethod
    def default_color_sequence_by_month(
        cls,
        month: int | None = None,
    ) -> NDArray[np.int32]:
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
        if month is None:
            date = datetime.datetime.now()  # noqa: DTZ005
            month = date.month
        return MONTHLY_COLOR_SEQUENCE[month]

    def get_random_boolean(self) -> bool:
        """Get a random true or false value.

        Returns
        -------
            True or False, randomly

        """
        return [True, False][random.randint(0, 1)]


MONTHLY_COLOR_SEQUENCE: dict[
    int,
    NDArray[np.int32],
] = {
    1: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.CYAN2,
            PixelColor.WHITE,
            PixelColor.CYAN,
            PixelColor.BLUE2,
            PixelColor.BLUE,
        ],
    ),
    2: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.PINK,
            PixelColor.WHITE,
            PixelColor.RED,
            PixelColor.WHITE,
        ],
    ),
    3: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.GREEN,
            PixelColor.WHITE,
            PixelColor.ORANGE,
            PixelColor.WHITE,
            PixelColor.YELLOW,
        ],
    ),
    4: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.PINK,
            PixelColor.CYAN,
            PixelColor.YELLOW,
            PixelColor.GREEN,
            PixelColor.WHITE,
        ],
    ),
    5: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.PINK,
            PixelColor.YELLOW,
            PixelColor.GREEN,
            PixelColor.WHITE,
        ],
    ),
    6: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.RED,
            PixelColor.WHITE,
            PixelColor.BLUE,
            PixelColor.GREEN,
        ],
    ),
    7: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.RED,
            PixelColor.WHITE,
            PixelColor.BLUE,
        ],
    ),
    8: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.ORANGE,
            PixelColor.WHITE,
            PixelColor.YELLOW,
            PixelColor.ORANGE2,
        ],
    ),
    9: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.RED,
            PixelColor.ORANGE,
            PixelColor.WHITE,
            PixelColor.YELLOW,
            PixelColor.ORANGE2,
            PixelColor.RED2,
        ],
    ),
    10: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.MIDNIGHT,
            PixelColor.RED,
            PixelColor.ORANGE,
            PixelColor.OFF,
        ],
    ),
    11: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.RED,
            PixelColor.MIDNIGHT,
            PixelColor.GRAY,
        ],
    ),
    12: PixelSequence.pixel_array_to_numpy_array(
        [
            PixelColor.RED,
            PixelColor.WHITE,
            PixelColor.GREEN,
        ],
    ),
}
