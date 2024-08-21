"""Color patterns and sequences."""

from __future__ import annotations

import datetime
import logging
import random
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, ClassVar, overload

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

    def __init_subclass__(cls) -> None:
        cls.ALL_SEQUENCES[cls.__name__.replace("Sequence", "")] = cls

    def __init__(
        self,
        led_count: int | None = None,
        pixel_array: list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Create a pattern of lights.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns
            pixel_array: a list of pixels

        """
        if name is None:
            name = PixelSequence.__name__
        self._name = name
        LOGGER.debug("Sequence: %s", name)
        if pixel_array is not None:
            self._array = pixel_array
            self._led_count = len(pixel_array)
        elif led_count is not None:
            self._led_count = led_count
            self._array: list[Pixel] = [PixelColor.OFF for _ in range(int(self._led_count))]
        else:
            self._led_count = 0
            self._array: list[Pixel] = [PixelColor.OFF for _ in range(int(self._led_count))]
        self._index: int = 0
        if self._led_count:
            self._pixel: Pixel = self._array[0].copy()
        else:
            self._pixel: Pixel = PixelColor.OFF
        if self._led_count > 1:
            self._pixel_next: Pixel = self._array[1].copy()
        else:
            self._pixel_next: Pixel = self._pixel.copy()

    def __len__(self) -> int:
        return self._led_count

    @overload
    def __getitem__(  # D105
        self,
        idx: int,
    ) -> Pixel: ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # D105
        self,
        idx: np.int32,
    ) -> Pixel: ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # D105 # pylint: disable=function-redefined
        self,
        idx: slice,
    ) -> list[Pixel]: ...  # pylint: disable=pointless-statement  # pragma: no cover

    def __getitem__(  # pylint: disable=function-redefined # type: ignore  # noqa: PGH003
        self,
        idx: int | np.int32 | slice,
    ) -> Pixel | list[Pixel]:
        """Return a pixel value by index.

        Args:
        ----
            idx: an index of a pixel, or a slice specifying a range of pixels

        Returns:
        -------
            the pixel value or values as requested

        """
        pixels: Pixel | list[Pixel] | None = None
        if isinstance(idx, int):
            pixels = self._array[idx]
        elif isinstance(idx, (np.integer)):
            pixels = self._array[int(idx)]
        else:
            pixels = self._array[idx]
        return pixels

    def __setitem__(
        self,
        key: int | np.int32 | slice,
        value: Pixel | list[Pixel],
    ) -> None:
        """Set LED value(s) in the array.

        Args:
        ----
            key: the index or slice specifying one or more LED indices
            value: the RGB value or values to assign to the given LED indices

        """
        if isinstance(key, np.integer) and isinstance(value, Pixel):
            self._array[int(key)] = value
        elif isinstance(key, int) and isinstance(value, Pixel):  # noqa: SIM114
            self._array[key] = value
        elif isinstance(key, slice) and isinstance(value, list):
            self._array[key] = value
        else:
            msg = f"Pixel setitem failed for key/value: {key}/{value}"
            raise TypeError(msg)

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
        return self._pixel

    @pixel.setter
    def pixel(self, pixel: Pixel) -> None:
        self._pixel = pixel

    @property
    def pixel_next(self) -> Pixel:
        """Get the color currently being manipulated.

        Returns
        -------
            the color currently being manipulated

        """
        return self._pixel_next

    @pixel_next.setter
    def pixel_next(self, pixel: Pixel) -> None:
        self._pixel_next = pixel

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
        pixel_sequence._array = pixel_list  # noqa: SLF001
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
        sequence = PixelSequence(name=self._name, pixel_array=self._array)
        sequence._index = self.index  # noqa: SLF001
        sequence._pixel = self._pixel  # noqa: SLF001
        sequence._pixel_next = self._pixel_next  # noqa: SLF001
        sequence.pixel = self.pixel
        sequence.pixel_next = self.pixel_next
        return sequence

    def advance_index(self, *, keep_current: bool = False) -> Pixel:
        """Advance index, update current pixel object.

        Returns
        -------
            next pixel object

        """
        self.index = self.index_next
        if keep_current:
            self._pixel = self._array[self.index].copy()
        self._pixel_next = self._array[self.index_next].copy()
        return self.pixel

    def __str__(
        self,
    ) -> str:
        """Return the value of the pixel as a string.

        Returns
        -------
            a string representation of the pixel

        """
        chunks: list[str] = []
        end = min(3, self._led_count)
        for i in range(end):
            index = (self.index + i) % self._led_count
            chunks.append(str(self._array[index]))
        s = ", ".join(chunks)
        if self._led_count > end:
            s += ",..."
        else:
            s += "]"
        return f"SQX#{self._led_count}[{s}"

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns
        -------
            a string representation of the Pixel instance

        """
        return f"<{PixelSequence.__name__}> {self.__str__()}"


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
