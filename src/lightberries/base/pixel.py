"""Define basic RGB pixel data and objects."""

from __future__ import annotations

import enum
import random
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Union, cast, overload

import numpy as np

from lightberries.base.constants import MAX_INT8, MAX_INT24, PIXEL_COLOR_COUNT
from lightberries.base.exceptions import PixelError

if TYPE_CHECKING:
    from numpy.typing import NDArray  # pragma: no cover


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
        self.func = func  # pragma: no cover

    def __get__(self, inst: Pixel, owner: Pixel) -> Pixel:
        return self.func()  # pragma: no cover


class LEDOrder(Order, enum.Enum):
    """LED order in the physical pixels.

    If your colors are all wrong, try a different enum.
    """

    RGB = (0, 1, 2)
    GRB = (1, 0, 2)


class Pixel:
    """A single LED pixel."""

    default_pixel_order: LEDOrder = LEDOrder.GRB

    def __init__(
        self,
        colors: Pixel | int | NDArray[Any] | tuple[int, int, int] | list[int] | None = None,
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
        for i in self._order:
            if i < 0 or i > 3:  # noqa: PLR2004
                msg = f"Invalid Pixel order: {self._order}"
                raise PixelError(msg)

        # none gets a zero
        if colors is None:
            self.int32value = 0

        # if it is an int and in range
        elif isinstance(colors, (int, np.integer)) and colors >= 0 and colors <= MAX_INT24:
            colors = int(colors)
            # if self._order == LEDOrder.RGB.value:
            self.int32value = colors & MAX_INT24

        # this is an instance of this class, just use the value
        elif isinstance(colors, Pixel):
            self.int32value = (
                # this is where the rgb order comes into play
                (int(colors.array[self.order[0]]) << 16)
                + (int(colors.array[self.order[1]]) << 8)
                + (int(colors.array[self.order[2]]))
            )

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
                (int(colors[0]) << 16) + (int(colors[1]) << 8) + (int(colors[2]))
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

    @property
    def int32(
        self,
    ) -> int:
        """Return the pixel value as a single integer value.

        Returns
        -------
            the integer value of the RGB values

        """
        return self.int32value

    @property
    def order(self) -> LEDOrder:
        """Get the LED order of this pixel object."""
        return self._order

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
        return f"PX#{rgb_value[0]:02X}{rgb_value[1]:02X}{rgb_value[2]:02X}:{self._order.name}"

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns
        -------
            a string representation of the Pixel instance

        """
        return self.__str__()

    def __eq__(self, other: object) -> bool:
        """Text pixel equality with other objects.

        Args:
        ----
            other: another object

        Returns:
        -------
            true if objects are equal

        """
        if isinstance(other, (Pixel)):
            return self.int32value == other.int32value
        if isinstance(other, (int)):
            return self.int32value == other
        if (
            (
                isinstance(other, tuple) and all(isinstance(e, int) for e in other) and len(other) >= COLOR_COUNT  # type: ignore  # noqa: PGH003
            )  # type: ignore  # noqa: PGH003
            or (
                isinstance(other, list) and all(isinstance(e, int) for e in other) and len(other) >= COLOR_COUNT  # type: ignore  # noqa: PGH003
            )  # type: ignore # noqa: PGH003
        ):
            other = cast("Union[int, Pixel, tuple[int, int, int], list[int]]", other)
            return self.int32value == Pixel(other).int32value
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
                self.array[self._order.red],
                self.array[self._order.green],
                self.array[self._order.blue],
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
        return Pixel([255 - a for a in self.rgb_array])

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
            color_next = pixel_from_color(PixelColor.OFF)
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
        value: int | list[int] | NDArray[Any],
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
            (int(array[self._order[0]]) << 16) + (int(array[self._order[1]]) << 8) + (int(array[self._order[2]]))
        )

    def __int__(self) -> int:
        return self.int32


class _Pixel(NamedTuple):
    """LEDs type."""

    red: int
    green: int
    blue: int


_pixels: dict[PixelColor, Pixel] = {}


def pixel_from_color(color: PixelColor) -> Pixel:
    """Get the pixel object with colors in the specified order.

    Args:
    ----
        color: color specification

    Returns:
    -------
        pixel object

    """
    if color not in _pixels:
        _pixels[color] = Pixel(color)
    return _pixels[color]


class PixelColor(_Pixel, enum.Enum):
    """List of commonly used colors for ease of use."""

    OFF = (0, 0, 0)
    RED4 = (31, 0, 0)
    RED3 = (63, 0, 0)
    RED2 = (127, 0, 0)
    RED = (255, 0, 0)
    ORANGE3 = (63, 63, 0)
    ORANGE2 = (127, 127, 0)
    ORANGE = (255, 127, 0)
    YELLOW = (255, 210, 80)
    LIME = (127, 255, 0)
    GREEN4 = (0, 31, 0)
    GREEN3 = (0, 63, 0)
    GREEN2 = (0, 127, 0)
    GREEN = (0, 255, 0)
    TEAL = (0, 255, 127)
    CYAN3 = (0, 63, 63)
    CYAN2 = (0, 127, 127)
    CYAN = (0, 255, 255)
    SKY = (0, 127, 255)
    BLUE = (0, 0, 255)
    BLUE2 = (0, 0, 127)
    BLUE3 = (0, 0, 63)
    BLUE4 = (0, 0, 31)
    VIOLET = (127, 0, 255)
    PURPLE = (127, 0, 127)
    PURPLE2 = (63, 0, 63)
    MIDNIGHT = (70, 0, 127)
    MAGENTA = (255, 0, 255)
    PINK = (255, 0, 127)
    WHITE = (255, 255, 255)
    GRAY = (127, 118, 108)
    GRAY2 = (64, 55, 50)

    @staticmethod
    def get_PSEUDO_RANDOM() -> _Pixel:  # noqa: N802
        """Get pseudo-random pixel value from list of named colors.

        Returns
        -------
            pseudo-random pixel value from list of named colors

        """
        valid_colors: list[PixelColor] = [
            getattr(PixelColor, p)
            for p in dir(PixelColor)
            if "__" not in p and "random" not in p.lower() and "off" not in p.lower()
        ]
        return _Pixel(*valid_colors[random.randint(0, len(valid_colors) - 1)].value)

    @staticmethod
    def get_RANDOM() -> _Pixel:  # noqa: N802
        """Get random pixel color.

        Returns
        -------
            random pixel color

        """
        return _Pixel(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
        )  # type: ignore  # noqa: PGH003
