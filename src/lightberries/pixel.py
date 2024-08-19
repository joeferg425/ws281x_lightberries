"""Define basic RGB pixel data and objects."""

from __future__ import annotations

import enum
import logging
import random
from typing import TYPE_CHECKING, Callable, NamedTuple, Union, cast, overload

import numpy as np

from lightberries.constants import MAX_INT8, MAX_INT24, PIXEL_COLOR_COUNT
from lightberries.exceptions import PixelError

if TYPE_CHECKING:
    from numpy.typing import NDArray

LOGGER = logging.getLogger("lightBerries")


class Order(NamedTuple):
    """LED Order type."""

    red: int
    green: int
    blue: int


COLOR_COUNT = 3


class StaticPixelProperty:
    """Works like @property and @staticmethod combined."""

    def __init__(self, func: Callable[[], Pixel]) -> None:
        """Make decorator.

        Args:
        ----
            func: function pointer

        """
        self.func = func

    def __get__(self, inst: Pixel, owner: Pixel) -> Pixel:
        return self.func()


class LEDOrder(Order, enum.Enum):
    """LED order in the physical pixels.

    If your colors are all wrong, try a different enum.
    """

    RGB = (0, 1, 2)
    GRB = (1, 0, 2)


class Pixel:
    """A single LED pixel."""

    default_pixel_order: list[int] = LEDOrder.GRB.value

    def __init__(
        self,
        colors: Pixel | int | NDArray[np.int32] | tuple[int, int, int] | list[int] | None = None,
    ) -> None:
        """Create a single RGB LED pixel.

        Args:
        ----
            colors: pixel color definition
            order: enum determining the order of the colors (e.g. RGB vs GRB)

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPixelException: if something bad happens

        """
        # initialize to zero
        self.int32value: int = 0

        self._order = Pixel.default_pixel_order

        # none gets a zero
        if colors is None:
            self.int32value = 0

        # if it is an int and in range
        elif isinstance(colors, (int, np.integer)) and colors >= 0 and colors <= MAX_INT24:
            colors = int(colors)
            if self._order == LEDOrder.RGB.value:
                self.int32value = colors & MAX_INT24
            elif self._order == LEDOrder.GRB.value:
                self.int32value = ((colors & 0xFF0000) >> 8) + ((colors & 0x00FF00) << 8) + ((colors & 0x0000FF) >> 0)

        # this is an instance of this class, just use the value
        elif isinstance(colors, Pixel):
            self.int32value = colors.int32value

        # if it is a tuple, list, or numpy array
        elif (
            isinstance(colors, (tuple, list, np.ndarray))
            # and has length three
        ) and len(colors) == PIXEL_COLOR_COUNT:
            if colors[0] > MAX_INT8 or colors[1] > MAX_INT8 or colors[2] > MAX_INT8:
                msg = f"Invalid Pixel values: {colors}"
                raise PixelError(msg)
            # create a 3-byte int from the three bytes
            self.int32value = (
                # this is where the rgb order comes into play
                (int(colors[self._order[0]]) << 16)
                + (int(colors[self._order[1]]) << 8)
                + (int(colors[self._order[2]]))
            )

        # we've got an error boys!
        else:
            msg = f"Cannot assign pixel using value: {colors!s} ({type(colors)})"
            raise PixelError(msg)

    def __len__(
        self,
    ) -> int:
        """Return the length of the pixel color array.

        Returns
        -------
            the number of colors in the array

        """
        return len(self.array)

    def int32(
        self,
    ) -> int:
        """Return the pixel value as a single integer value.

        Returns
        -------
            the integer value of the RGB values

        """
        return self.int32value

    def __str__(
        self,
    ) -> str:
        """Return the value of the pixel as a string.

        Returns
        -------
            a string representation of the pixel

        """
        rgb_value = (
            (self.int32value & 0xFF0000) >> 16,
            (self.int32value & 0xFF00) >> 8,
            self.int32value & 0xFF,
        )
        return f"PX#{rgb_value[0]:02X}{rgb_value[1]:02X}{rgb_value[2]:02X}"

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns
        -------
            a string representation of the Pixel instance

        """
        return f"<{Pixel.__name__}> {self.__str__()} ({LEDOrder (self._order).name})"

    def __eq__(self, other: object) -> bool:
        """Text pixel equality with other objects.

        Args:
        ----
            other: another object

        Returns:
        -------
            true if objects are equal

        """
        if (
            isinstance(other, (int, Pixel))
            or (
                isinstance(other, tuple) and all(isinstance(e, int) for e in other) and len(other) >= COLOR_COUNT  # type: ignore  # noqa: PGH003
            )  # type: ignore  # noqa: PGH003
            or (
                isinstance(other, list) and all(isinstance(e, int) for e in other) and len(other) >= COLOR_COUNT  # type: ignore  # noqa: PGH003
            )  # type: ignore # noqa: PGH003
        ):
            other = cast("Union[int, Pixel, tuple[int, int, int], list[int]]", other)
            return self.pixel.int32value == Pixel(other).pixel.int32value
        return False
        # convert the pixel orders to the same order then compare

    @property
    def tuple(
        self,
    ) -> tuple[int, int, int]:
        """Return Pixel value as a tuple of ints.

        Returns
        -------
            the RGB value into tuple

        """
        rgb_tuple = (
            (self.int32value & 0xFF0000) >> 16,
            (self.int32value & 0xFF00) >> 8,
            self.int32value & 0xFF,
        )
        return (
            rgb_tuple[0],
            rgb_tuple[1],
            rgb_tuple[2],
        )

    @property
    def pixel(
        self,
    ) -> Pixel:
        """Return Pixel value with default RGB order.

        Returns
        -------
            this pixel with default RGB order

        """
        return Pixel(self.tuple)

    @property
    def array(
        self,
    ) -> NDArray[np.int32]:
        """Return Pixel value as a numpy array.

        Returns
        -------
            RGB value as a numpy array

        """
        return np.array(self.tuple)

    @property
    def rgb_array(
        self,
    ) -> NDArray[np.int32]:
        """Return Pixel value as a numpy array.

        Returns
        -------
            RGB value as a numpy array

        """
        return np.array(
            [
                self.array[self._order[0]],
                self.array[self._order[1]],
                self.array[self._order[2]],
            ],
        )

    @property
    def rgb_tuple(
        self,
    ) -> tuple[np.int32, np.int32, np.int32]:
        """Return Pixel value as a numpy array.

        Returns
        -------
            RGB value as a numpy array

        """
        return (
            self.array[self._order[0]],
            self.array[self._order[1]],
            self.array[self._order[2]],
        )

    @property
    def hex_str(self) -> str:
        """Returns the color value as an RGB hex strings regardless of underlying RGB order.

        Returns
        -------
            value as a hexadecimal string

        """
        rgb = self.tuple
        return f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def invert(self) -> Pixel:
        """Get inverted pixel value.

        Returns
        -------
            inverted pixel value

        """
        return Pixel([255 - a for a in self.array])

    def fade(
        self,
        color_next: Pixel | None = None,
        fade_amount: int | None = None,
    ) -> NDArray[np.int32]:
        """Fade an LED's color by the given amount and return the new RGB value.

        Args:
        ----
            color_next: desired color
            fade_amount: amount to adjust each RGB value by

        Returns:
        -------
            new RGB value

        """
        if color_next is None:
            color_next = PixelColor.OFF
        if fade_amount is None:
            fade_amount = 25
        color = self.array.copy()
        # copy it to make sure we don't change the original by reference
        for rgb_index in range(len(color)):
            # the values closest to the target color might match already
            if color[rgb_index] != color_next.array[rgb_index]:
                # subtract or add as appropriate in order to get closer to target color
                if color[rgb_index] - fade_amount > color_next.array[rgb_index]:
                    color[rgb_index] -= fade_amount
                elif color[rgb_index] + fade_amount < color_next.array[rgb_index]:
                    color[rgb_index] += fade_amount
                else:
                    color[rgb_index] = color_next.array[rgb_index]
        self.int32value = (
            (int(color[self._order[0]]) << 16) + (int(color[self._order[1]]) << 8) + (int(color[self._order[2]]))
        )
        return color

    def copy(self) -> Pixel:
        """Get a copy of this pixel.

        Returns
        -------
            a copy of this pixel

        """
        return Pixel(self.array)


class PixelColor(Pixel, enum.Enum):
    """List of commonly used colors for ease of use."""

    OFF = Pixel((0, 0, 0))
    RED4 = Pixel((31, 0, 0))
    RED3 = Pixel((63, 0, 0))
    RED2 = Pixel((127, 0, 0))
    RED = Pixel((255, 0, 0))
    ORANGE3 = Pixel((63, 63, 0))
    ORANGE2 = Pixel((127, 127, 0))
    ORANGE = Pixel((255, 127, 0))
    YELLOW = Pixel((255, 210, 80))
    LIME = Pixel((127, 255, 0))
    GREEN4 = Pixel((0, 31, 0))
    GREEN3 = Pixel((0, 63, 0))
    GREEN2 = Pixel((0, 127, 0))
    GREEN = Pixel((0, 255, 0))
    TEAL = Pixel((0, 255, 127))
    CYAN3 = Pixel((0, 63, 63))
    CYAN2 = Pixel((0, 127, 127))
    CYAN = Pixel((0, 255, 255))
    SKY = Pixel((0, 127, 255))
    BLUE = Pixel((0, 0, 255))
    BLUE2 = Pixel((0, 0, 127))
    BLUE3 = Pixel((0, 0, 63))
    BLUE4 = Pixel((0, 0, 31))
    VIOLET = Pixel((127, 0, 255))
    PURPLE = Pixel((127, 0, 127))
    PURPLE2 = Pixel((63, 0, 63))
    MIDNIGHT = Pixel((70, 0, 127))
    MAGENTA = Pixel((255, 0, 255))
    PINK = Pixel((255, 0, 127))
    WHITE = Pixel((255, 255, 255))
    GRAY = Pixel((127, 118, 108))
    GRAY2 = Pixel((64, 55, 50))

    @StaticPixelProperty
    def pseudo_random() -> Pixel:
        """Get pseudo-random pixel value from list of named colors.

        Returns
        -------
            pseudo-random pixel value from list of named colors

        """
        valid_colors = [
            getattr(PixelColor, p)
            for p in dir(PixelColor)
            if "__" not in p and "random" not in p.lower() and "off" not in p.lower()
        ]
        return valid_colors[random.randint(0, len(valid_colors) - 1)]

    @StaticPixelProperty
    def random() -> Pixel:
        """Get random pixel color.

        Returns
        -------
            random pixel color

        """
        return Pixel([random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])

    @overload
    def __getitem__(  # D105
        self,
        idx: int,
    ) -> int | list[int] | None: ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # D105
        self,
        idx: np.int32,
    ) -> int | list[int] | None: ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # D105 # pylint: disable=function-redefined
        self,
        idx: slice,
    ) -> int | list[int] | None: ...  # pylint: disable=pointless-statement  # pragma: no cover

    def __getitem__(  # pylint: disable=function-redefined # type: ignore  # noqa: PGH003
        self,
        idx: int | np.int32 | slice,
    ) -> int | list[int] | None:
        """Return a color's value by index.

        Args:
        ----
            idx: an index of a single color, or a slice specifying a range of colors

        Returns:
        -------
            the color value or values as requested

        """
        color: int | list[int] | None = None
        if isinstance(idx, int):
            color = self.tuple[idx]
        elif isinstance(idx, (np.integer)):
            color = self.tuple[int(idx)]
        else:
            color = list(self.tuple)[idx]
        return color

    def __setitem__(
        self,
        key: int | np.int32 | slice,
        value: int | list[int],
    ) -> None:
        """Set LED value(s) in the array.

        Args:
        ----
            key: the index or slice specifying one or more LED indices
            value: the RGB value or values to assign to the given LED indices

        """
        array = self.array.copy()
        array[key] = value
        self.int32value = (
            # this is where the rgb order comes into play
            (int(array[self._order[0]]) << 16)
            + (int(array[self._order[1]]) << 8)
            + (int(array[self._order[2]]))
        )
