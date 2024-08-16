"""Define basic RGB pixel data and objects."""

from __future__ import annotations

import enum
import logging
import random
from typing import Any, NamedTuple

import numpy as np

from lightberries.constants import MAX_INT8, MAX_INT24, PIXEL_COLOR_COUNT
from lightberries.exceptions import PixelError

LOGGER = logging.getLogger("lightBerries")


class Order(NamedTuple):
    """LED Order type."""

    red: int
    green: int
    blue: int


class StaticPixelProperty:
    """Works like @property and @staticmethod combined."""

    def __init__(self, func: callable[None]) -> None:
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

    RGB: list[int] = Order(red=0, green=1, blue=2)
    GRB: list[int] = Order(red=1, green=0, blue=2)


class Pixel:
    """A single LED pixel."""

    DEFAULT_PIXEL_ORDER: list[int] = LEDOrder.GRB.value

    def __init__(
        self,
        rgb: int | np.ndarray[(3), np.dtype[Any]] | Pixel | None = None,
        order: LEDOrder | list | None = None,
    ) -> None:
        """Create a single RGB LED pixel.

        Args:
        ----
            rgb: pixel color definition
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

        self._order = Pixel.DEFAULT_PIXEL_ORDER
        if isinstance(order, LEDOrder):
            self._order = order.value
        elif isinstance(order, list):
            self._order = order
        else:
            self._order = Pixel.DEFAULT_PIXEL_ORDER

        # none gets a zero
        if rgb is None:
            self.int32value = 0

        # if it is an int and in range
        elif isinstance(rgb, (int, np.int32, np.int32)) and rgb >= 0 and rgb <= MAX_INT24:
            rgb = int(rgb)
            if self._order == LEDOrder.RGB.value:
                self.int32value = rgb & MAX_INT24
            elif self._order == LEDOrder.GRB.value:
                self.int32value = ((rgb & 0xFF0000) >> 8) + ((rgb & 0x00FF00) << 8) + ((rgb & 0x0000FF) >> 0)

        # this is an instance of this class, just use the value
        elif isinstance(rgb, Pixel):
            self.int32value = rgb.int32value

        # if it is a tuple, list, or numpy array
        elif (
            isinstance(rgb, (tuple, list, np.ndarray))
            # and has length three
        ) and len(rgb) == PIXEL_COLOR_COUNT:
            if rgb[0] > MAX_INT8 or rgb[1] > MAX_INT8 or rgb[2] > MAX_INT8:
                msg = f"Invalid Pixel values: {rgb}"
                raise PixelError(msg)
            # create a 3-byte int from the three bytes
            self.int32value = (
                # this is where the rgb order comes into play
                (int(rgb[self._order[0]]) << 16)
                + (int(rgb[self._order[1]]) << 8)
                + (int(rgb[self._order[2]]))
            )

        # we've got an error boys!
        else:
            msg = f"Cannot assign pixel using value: {rgb!s} ({type(rgb)})"
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

    def __int32_(
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
        return "PX #" + f"{rgb_value[0]:02X}" + f"{rgb_value[1]:02X}" + f"{rgb_value[2]:02X}"

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns
        -------
            a string representation of the Pixel instance

        """
        return f"<{self.__class__.__name__}> {self.__str__()} ({self.int32value}/{LEDOrder (self._order).name})"

    def __eq__(self, other: object) -> bool:
        """Text pixel equality with other objects.

        Args:
        ----
            other: another object

        Returns:
        -------
            true if objects are equal

        """
        if other is None or not isinstance(other, (int, np.ndarray, tuple, Pixel)):
            return False
        # convert the pixel orders to the same order then compare
        return self.pixel.int32value == Pixel(other, LEDOrder.RGB).pixel.int32value

    @property
    def tuple(
        self,
    ) -> tuple[int]:
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
        return Pixel(self.tuple, self.DEFAULT_PIXEL_ORDER)

    @property
    def array(
        self,
    ) -> np.ndarray[(3,), np.int32]:
        """Return Pixel value as a numpy array.

        Returns
        -------
            RGB value as a numpy array

        """
        return np.array(self.tuple)

    @property
    def rgb_array(
        self,
    ) -> np.ndarray[(3,), np.int32]:
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


class PixelColors:
    """List of commonly used colors for ease of use."""

    OFF = Pixel((0, 0, 0), order=LEDOrder.RGB)
    RED4 = Pixel((31, 0, 0), order=LEDOrder.RGB)
    RED3 = Pixel((63, 0, 0), order=LEDOrder.RGB)
    RED2 = Pixel((127, 0, 0), order=LEDOrder.RGB)
    RED = Pixel((255, 0, 0), order=LEDOrder.RGB)
    ORANGE3 = Pixel((63, 63, 0), order=LEDOrder.RGB)
    ORANGE2 = Pixel((127, 127, 0), order=LEDOrder.RGB)
    ORANGE = Pixel((255, 127, 0), order=LEDOrder.RGB)
    YELLOW = Pixel((255, 210, 80), order=LEDOrder.RGB)
    LIME = Pixel((127, 255, 0), order=LEDOrder.RGB)
    GREEN4 = Pixel((0, 31, 0), order=LEDOrder.RGB)
    GREEN3 = Pixel((0, 63, 0), order=LEDOrder.RGB)
    GREEN2 = Pixel((0, 127, 0), order=LEDOrder.RGB)
    GREEN = Pixel((0, 255, 0), order=LEDOrder.RGB)
    TEAL = Pixel((0, 255, 127), order=LEDOrder.RGB)
    CYAN3 = Pixel((0, 63, 63), order=LEDOrder.RGB)
    CYAN2 = Pixel((0, 127, 127), order=LEDOrder.RGB)
    CYAN = Pixel((0, 255, 255), order=LEDOrder.RGB)
    SKY = Pixel((0, 127, 255), order=LEDOrder.RGB)
    BLUE = Pixel((0, 0, 255), order=LEDOrder.RGB)
    BLUE2 = Pixel((0, 0, 127), order=LEDOrder.RGB)
    BLUE3 = Pixel((0, 0, 63), order=LEDOrder.RGB)
    BLUE4 = Pixel((0, 0, 31), order=LEDOrder.RGB)
    VIOLET = Pixel((127, 0, 255), order=LEDOrder.RGB)
    PURPLE = Pixel((127, 0, 127), order=LEDOrder.RGB)
    PURPLE2 = Pixel((63, 0, 63), order=LEDOrder.RGB)
    MIDNIGHT = Pixel((70, 0, 127), order=LEDOrder.RGB)
    MAGENTA = Pixel((255, 0, 255), order=LEDOrder.RGB)
    PINK = Pixel((255, 0, 127), order=LEDOrder.RGB)
    WHITE = Pixel((255, 255, 255), order=LEDOrder.RGB)
    GRAY = Pixel((127, 118, 108), order=LEDOrder.RGB)
    GRAY2 = Pixel((64, 55, 50), order=LEDOrder.RGB)

    @StaticPixelProperty
    def pseudo_random() -> Pixel:
        """Get pseudo-random pixel value from list of named colors.

        Returns
        -------
            pseudo-random pixel value from list of named colors

        """
        valid_colors = [
            getattr(PixelColors, p)
            for p in dir(PixelColors)
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
