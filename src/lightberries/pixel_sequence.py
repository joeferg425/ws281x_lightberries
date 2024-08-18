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
        led_count: int = 0,
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
        LOGGER.debug("Sequence: %s", name)
        self._array: list[Pixel] = [PixelColor.OFF for _ in range(int(led_count))]
        self._led_count = led_count
        self._index: int = 0
        if self._led_count:
            self._color: Pixel = self._array[0].copy()
        else:
            self._color: Pixel = PixelColor.OFF

    def __len__(self) -> int:
        return self._led_count

    @property
    def index(self) -> int:
        """Get the sequence index.

        Returns
        -------
            the sequence index

        """
        return self._index

    @index.setter
    def index(self, index: int) -> None:
        self._index = index % self.count

    @property
    def index_next(self) -> int:
        """Get the next valid sequence index.

        Returns
        -------
            the next valid sequence index

        """
        return (self.index + 1) % self.count

    @property
    def pixel(self) -> Pixel:
        """Get the color currently being manipulated.

        Returns
        -------
            the color currently being manipulated

        """
        return self._color

    @pixel.setter
    def pixel(self, pixel: Pixel) -> None:
        self._color = pixel

    @property
    def color_current(self) -> Pixel:
        """Get the current color.

        Returns
        -------
            the current color

        """
        return self._array[self.index]

    @property
    def color_next(self) -> Pixel:
        """Get the next color.

        Returns
        -------
            the next color

        """
        return self._array[self.index_next]

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
    def ndarray(self) -> NDArray[np.int32]:
        """Get the light sequence.

        Returns
        -------
            the light sequence

        """
        return np.array([p.array for p in self._array], dtype=np.int32)

    @property
    def count(self) -> int:
        """Get the Pixel count.

        Returns
        -------
            the Pixel count

        """
        return self._led_count

    @staticmethod
    def from_list(pixel_list: list[Pixel]) -> PixelSequence:
        """Turn a list of pixels into a PixelSequence object.

        Args:
        ----
            pixel_list: a list of pixels

        Returns:
        -------
            pixel sequence object

        """
        pixel_sequence = PixelSequence(led_count=len(pixel_list))
        for pxl_index, pxl in enumerate(pixel_list):
            pixel_sequence.ndarray[pxl_index] = pxl.array
        return pixel_sequence

    @staticmethod
    def default_color_sequence_by_month(
        month: int | None = None,
    ) -> PixelSequence:
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

    def copy(self) -> PixelSequence:
        """Make a copy of the sequence.

        Returns
        -------
            a copy of the sequence

        """
        sequence = PixelSequence(led_count=self._led_count)
        sequence._array = self._array.copy()  # noqa: SLF001
        return sequence

    def advance_index(self) -> Pixel:
        """Advance index, update current pixel object.

        Returns
        -------
            next pixel object

        """
        self.index = self.index_next
        self._color = self._array[self.index].copy()
        return self.pixel


MONTHLY_COLOR_SEQUENCE: dict[
    int,
    PixelSequence,
] = {
    1: PixelSequence.from_list(
        [
            PixelColor.CYAN2,
            PixelColor.WHITE,
            PixelColor.CYAN,
            PixelColor.BLUE2,
            PixelColor.BLUE,
        ],
    ),
    2: PixelSequence.from_list(
        [
            PixelColor.PINK,
            PixelColor.WHITE,
            PixelColor.RED,
            PixelColor.WHITE,
        ],
    ),
    3: PixelSequence.from_list(
        [
            PixelColor.GREEN,
            PixelColor.WHITE,
            PixelColor.ORANGE,
            PixelColor.WHITE,
            PixelColor.YELLOW,
        ],
    ),
    4: PixelSequence.from_list(
        [
            PixelColor.PINK,
            PixelColor.CYAN,
            PixelColor.YELLOW,
            PixelColor.GREEN,
            PixelColor.WHITE,
        ],
    ),
    5: PixelSequence.from_list(
        [
            PixelColor.PINK,
            PixelColor.YELLOW,
            PixelColor.GREEN,
            PixelColor.WHITE,
        ],
    ),
    6: PixelSequence.from_list(
        [
            PixelColor.RED,
            PixelColor.WHITE,
            PixelColor.BLUE,
            PixelColor.GREEN,
        ],
    ),
    7: PixelSequence.from_list(
        [
            PixelColor.RED,
            PixelColor.WHITE,
            PixelColor.BLUE,
        ],
    ),
    8: PixelSequence.from_list(
        [
            PixelColor.ORANGE,
            PixelColor.WHITE,
            PixelColor.YELLOW,
            PixelColor.ORANGE2,
        ],
    ),
    9: PixelSequence.from_list(
        [
            PixelColor.RED,
            PixelColor.ORANGE,
            PixelColor.WHITE,
            PixelColor.YELLOW,
            PixelColor.ORANGE2,
            PixelColor.RED2,
        ],
    ),
    10: PixelSequence.from_list(
        [
            PixelColor.MIDNIGHT,
            PixelColor.RED,
            PixelColor.ORANGE,
            PixelColor.OFF,
        ],
    ),
    11: PixelSequence.from_list(
        [
            PixelColor.RED,
            PixelColor.MIDNIGHT,
            PixelColor.GRAY,
        ],
    ),
    12: PixelSequence.from_list(
        [
            PixelColor.RED,
            PixelColor.WHITE,
            PixelColor.GREEN,
        ],
    ),
}
