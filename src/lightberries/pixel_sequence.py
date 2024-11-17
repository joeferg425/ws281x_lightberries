"""Color patterns and sequences."""

from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Any, ClassVar, overload

import numpy as np

from lightberries.base.logger import LOGGER
from lightberries.base.pixel import Pixel, PixelColor

if TYPE_CHECKING:
    from numpy.typing import NDArray  # pragma: no cover


class PixelSequence(Sequence[Pixel]):
    """A pattern of lights."""

    ALL_SEQUENCES: ClassVar[dict[str, type[PixelSequence]]] = {}

    def __init_subclass__(cls) -> None:
        cls_name = cls.__name__.replace("Sequence", "")
        if cls_name not in ("Pixel", "Array", "Off"):
            cls.ALL_SEQUENCES[cls_name] = cls

    def __init__(
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Create a pattern of lights.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of pixels desired in the returned pixel array
            kwargs: args for patterns
            pixel_sequence: a list of pixels

        """
        if name is None:
            name = PixelSequence.__name__
        self._name = name
        if pixel_sequence is not None:
            if isinstance(pixel_sequence, PixelSequence):
                self._array = list(pixel_sequence)
            else:
                self._array = pixel_sequence
            self._led_count = len(pixel_sequence)
        elif led_count is not None:
            self._led_count = led_count
            self._array: list[Pixel] = [Pixel(PixelColor.OFF) for _ in range(int(self._led_count))]
        else:
            self._led_count = 0
            self._array: list[Pixel] = [Pixel(PixelColor.OFF) for _ in range(int(self._led_count))]
        self._led_index: int = 0
        if self._led_count:
            self._pixel: Pixel = self._array[0].copy()
        else:
            self._pixel: Pixel = Pixel(PixelColor.OFF)
        if self._led_count > 1:
            self._pixel_next: Pixel = self._array[1].copy()
        else:
            self._pixel_next: Pixel = self._pixel.copy()
        LOGGER.debug(self)

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

    @overload
    def __getitem__(  # D105 # pylint: disable=function-redefined
        self,
        idx: Iterable[int],
    ) -> list[Pixel]: ...  # pylint: disable=pointless-statement  # pragma: no cover

    def __getitem__(  # pylint: disable=function-redefined # type: ignore  # noqa: PGH003
        self,
        idx: int | np.int32 | slice | list[int],
    ) -> Pixel | list[Pixel]:
        """Return a pixel value by led_index.

        Args:
        ----
            idx: an led_index of a pixel, or a slice specifying a range of pixels

        Returns:
        -------
            the pixel value or values as requested

        """
        pixels: Pixel | list[Pixel] | None = None
        if isinstance(idx, int):
            pixels = self._array[idx]
        elif isinstance(idx, (np.integer)):
            pixels = self._array[int(idx)]
        elif isinstance(idx, (slice)):
            pixels = self._array[idx]
        else:
            pixels = [self._array[i] for i in idx]
        return pixels

    def __setitem__(
        self,
        key: int | np.int32 | slice | Iterable[int],
        value: Pixel | list[Pixel],
    ) -> None:
        """Set LED value(s) in the array.

        Args:
        ----
            key: the led_index or slice specifying one or more LED indices
            value: the RGB value or values to assign to the given LED indices

        """
        if isinstance(key, np.integer) and isinstance(value, Pixel):
            self._array[int(key)] = value
        elif isinstance(key, int) and isinstance(value, Pixel):  # noqa: SIM114
            self._array[key] = value
        elif isinstance(key, slice) and isinstance(value, list):
            self._array[key] = value
        elif isinstance(key, list) and isinstance(value, list):
            for i in key:
                self._array[i] = value[i]
        else:
            msg = f"Pixel setitem failed for key/value: {key}/{value}"
            raise TypeError(msg)

    @property
    def led_index(self) -> int:
        """Get the sequence led_index.

        Returns
        -------
            the sequence led_index

        """
        return self._led_index

    @led_index.setter
    def led_index(self, led_index: int) -> None:
        self._led_index = led_index % self.led_count

    @property
    def index_next(self) -> int:
        """Get the next valid sequence led_index.

        Returns
        -------
            the next valid sequence led_index

        """
        return (self.led_index + 1) % self.led_count

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
        color_sequence: Sequence[Pixel] | PixelSequence,
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
            return np.array([Pixel(p).array for p in color_sequence])
        return np.zeros((0, 3), dtype=np.int32)

    @property
    def array(self) -> NDArray[np.int32]:
        """Get the light sequence.

        Returns
        -------
            the light sequence

        """
        if self._array:
            return np.array([p.rgb_array for p in self._array], dtype=np.int32)
        return np.zeros((0, 3), dtype=np.int32)

    @property
    def list(self) -> list[Pixel]:
        """Get the light sequence.

        Returns
        -------
            the light sequence

        """
        return list(self._array)

    def count(self, value: Pixel) -> int:
        """Count instances of the pixel value.

        Args:
        ----
            value: a pixel instance

        Returns:
        -------
            count of the value

        """
        return self._array.count(value)

    @property
    def led_count(self) -> int:
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

    def get_random_boolean(self) -> bool:
        """Get a random true or false value.

        Returns
        -------
            True or False, randomly

        """
        return [True, False][random.randint(0, 1)]

    def random_index(self) -> int:
        """Get a random index.

        Returns
        -------
            random index

        """
        _led_index = random.randint(0, self.led_count - 1)
        self._set_index(_led_index)
        return self._led_index

    def copy(self) -> PixelSequence:
        """Make a copy of the sequence.

        Returns
        -------
            a copy of the sequence

        """
        sequence = PixelSequence(name=self._name, pixel_sequence=self._array)
        sequence._led_index = self.led_index  # noqa: SLF001
        sequence._pixel = self._pixel  # noqa: SLF001
        sequence._pixel_next = self._pixel_next  # noqa: SLF001
        sequence.pixel = self.pixel
        sequence.pixel_next = self.pixel_next
        return sequence

    def advance_index(self, *, keep_current: bool = False) -> Pixel:
        """Advance led_index, update current pixel object.

        Returns
        -------
            next pixel object

        """
        _pixel = self._pixel
        self._set_index(self.index_next)
        if keep_current:
            self._pixel = _pixel
        return self.pixel

    def _set_index(self, index: int) -> None:
        self._led_index = index
        self._pixel = self._array[self.led_index].copy()
        self._pixel_next = self._array[self.index_next].copy()

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
            led_index = (self.led_index + i) % self._led_count
            chunks.append(str(self._array[led_index]))
        s = ", ".join(chunks)
        if self._led_count > end:
            s += ",..."
        else:
            s += "]"
        return f"{self._name.replace('Sequence','')}: SQX#{self._led_count}[{s}"

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns
        -------
            a string representation of the Pixel instance

        """
        return f"{self.__str__()}"

    @staticmethod
    def get_monthly_color_sequence(month: int | datetime | None = None) -> PixelSequence:
        """Get the sequence for each month.

        Args:
        ----
            month: the month as an integer

        Returns:
        -------
            pixel sequence

        """
        if month is None:
            date = datetime.now()  # noqa: DTZ005
            month = Month(date.month)
        elif isinstance(month, datetime):
            month = Month(month.month)
        else:
            month = Month(month)
        return MonthSequences[month]


class Month(IntEnum):
    """Month enum so linters stop hating me."""

    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


MonthSequences = {
    Month.January: PixelSequence.from_list(
        [
            Pixel(PixelColor.CYAN2),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.CYAN),
            Pixel(PixelColor.BLUE2),
            Pixel(PixelColor.BLUE),
        ],
    ),
    Month.February: PixelSequence.from_list(
        [
            Pixel(PixelColor.PINK),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.RED),
            Pixel(PixelColor.WHITE),
        ],
    ),
    Month.March: PixelSequence.from_list(
        [
            Pixel(PixelColor.GREEN),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.ORANGE),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.YELLOW),
        ],
    ),
    Month.April: PixelSequence.from_list(
        [
            Pixel(PixelColor.PINK),
            Pixel(PixelColor.CYAN),
            Pixel(PixelColor.YELLOW),
            Pixel(PixelColor.GREEN),
            Pixel(PixelColor.WHITE),
        ],
    ),
    Month.May: PixelSequence.from_list(
        [
            Pixel(PixelColor.PINK),
            Pixel(PixelColor.YELLOW),
            Pixel(PixelColor.GREEN),
            Pixel(PixelColor.WHITE),
        ],
    ),
    Month.June: PixelSequence.from_list(
        [
            Pixel(PixelColor.RED),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.BLUE),
            Pixel(PixelColor.GREEN),
        ],
    ),
    Month.July: PixelSequence.from_list(
        [
            Pixel(PixelColor.RED),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.BLUE),
        ],
    ),
    Month.August: PixelSequence.from_list(
        [
            Pixel(PixelColor.ORANGE),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.YELLOW),
            Pixel(PixelColor.ORANGE2),
        ],
    ),
    Month.September: PixelSequence.from_list(
        [
            Pixel(PixelColor.RED),
            Pixel(PixelColor.ORANGE),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.YELLOW),
            Pixel(PixelColor.ORANGE2),
            Pixel(PixelColor.RED2),
        ],
    ),
    Month.October: PixelSequence.from_list(
        [
            Pixel(PixelColor.MIDNIGHT),
            Pixel(PixelColor.RED),
            Pixel(PixelColor.ORANGE),
            Pixel(PixelColor.OFF),
        ],
    ),
    Month.November: PixelSequence.from_list(
        [
            Pixel(PixelColor.RED),
            Pixel(PixelColor.MIDNIGHT),
            Pixel(PixelColor.GRAY),
        ],
    ),
    Month.December: PixelSequence.from_list(
        [
            Pixel(PixelColor.RED),
            Pixel(PixelColor.WHITE),
            Pixel(PixelColor.GREEN),
        ],
    ),
}
