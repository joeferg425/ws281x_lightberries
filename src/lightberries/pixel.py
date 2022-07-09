"""Define basic RGB pixel data and objects."""
from __future__ import annotations
import enum
import logging
import random
from typing import Any
import numpy as np

from lightberries.exceptions import PixelException

LOGGER = logging.getLogger("lightBerries")


class LEDOrder(enum.Enum):
    """This enum is for LED order in the physical pixels.

    If your colors are all wrong, try a different enum.
    """

    RGB: list[int] = [0, 1, 2]
    GRB: list[int] = [1, 0, 2]


class Pixel:
    """This class defines a single LED pixel."""

    DEFAULT_PIXEL_ORDER: list[int] = LEDOrder.GRB.value

    def __init__(
        self,
        rgb: int | np.ndarray[(3), np.dtype[Any]] | "Pixel" | None = None,
        order: LEDOrder | None = None,
    ) -> None:
        """Create a single RGB LED pixel.

        Args:
            rgb: pixel color definition
            order: enum determining the order of the colors (e.g. RGB vs GRB)

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPixelException: if something bad happens
        """
        # initialize to zero
        self.int_value: int = 0

        if order is None:
            self._order = Pixel.DEFAULT_PIXEL_ORDER
        elif isinstance(order, LEDOrder):
            self._order = order.value
        elif isinstance(order, list):
            self._order = order
        else:
            raise PixelException(f"Unknown RGB order: {order}")

        # none gets a zero
        if rgb is None:
            self.int_value = 0

        # if it is an int and in range
        elif isinstance(rgb, (int, np.int_, np.int32)) and rgb >= 0 and rgb <= 0xFFFFFF:
            rgb = int(rgb)
            if self._order == LEDOrder.RGB.value:
                self.int_value = rgb & 0xFFFFFF
            elif self._order == LEDOrder.GRB.value:
                self.int_value = ((rgb & 0xFF0000) >> 8) + ((rgb & 0x00FF00) << 8) + ((rgb & 0x0000FF) >> 0)

        # this is an instance of this class, just use the value
        elif isinstance(rgb, Pixel):
            self.int_value = rgb.int_value

        # if it is a tuple, list, or numpy array
        elif (
            isinstance(rgb, tuple)
            or isinstance(rgb, list)
            or isinstance(rgb, np.ndarray)
            # and has length three
        ) and len(rgb) == 3:
            if rgb[0] > 255 or rgb[1] > 255 or rgb[2] > 255:
                raise PixelException(f"Invalid Pixel values: {rgb}")
            # create a 3-byte int from the three bytes
            self.int_value = (
                # this is where the rgb order comes into play
                (int(rgb[self._order[0]]) << 16)
                + (int(rgb[self._order[1]]) << 8)
                + (int(rgb[self._order[2]]))
            )

        # we've got an error boys!
        else:
            raise PixelException(f"Cannot assign pixel using value: {str(rgb)} ({type(rgb)})")

    def __len__(
        self,
    ) -> int:
        """Return the length of the pixel color array.

        Returns:
            the number of colors in the array
        """
        return len(self.array)

    def __int__(
        self,
    ) -> int:
        """Return the pixel value as a single integer value.

        Returns:
            the integer value of the RGB values
        """
        return self.int_value

    def __str__(
        self,
    ) -> str:
        """Return the value of the pixel as a string.

        Returns:
            a string representation of the pixel
        """
        rgbValue = (
            (self.int_value & 0xFF0000) >> 16,
            (self.int_value & 0xFF00) >> 8,
            self.int_value & 0xFF,
        )
        return "PX #" + f"{rgbValue[0]:02X}" + f"{rgbValue[1]:02X}" + f"{rgbValue[2]:02X}"

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns:
            a string representation of the Pixel instance
        """
        return f"<{self.__class__.__name__}> {self.__str__()} ({self.int_value}/{LEDOrder (self._order).name})"

    def __eq__(self, other: object) -> bool:
        """Text pixel equality with other objects.

        Args:
            other: another object

        Returns:
            true if objects are equal
        """
        if other is None or not isinstance(other, (int, np.ndarray, tuple, Pixel)):
            return False
        # convert the pixel orders to the same order then compare
        return self.pixel.int_value == Pixel(other, LEDOrder.RGB).pixel.int_value

    @property
    def tuple(
        self,
    ) -> tuple[int]:
        """Return Pixel value as a tuple of ints.

        Returns:
            the RGB value into tuple
        """
        rgbTuple = (
            (self.int_value & 0xFF0000) >> 16,
            (self.int_value & 0xFF00) >> 8,
            self.int_value & 0xFF,
        )
        return (
            rgbTuple[0],
            rgbTuple[1],
            rgbTuple[2],
        )

    @property
    def pixel(
        self,
    ) -> "Pixel":
        """Return Pixel value with default RGB order.

        Returns:
            this pixel with default RGB order
        """
        return Pixel(self.tuple, self.DEFAULT_PIXEL_ORDER)

    @property
    def array(
        self,
    ) -> np.ndarray[(3,), np.int_]:
        """Return Pixel value as a numpy array.

        Returns:
            RGB value as a numpy array
        """
        return np.array(self.tuple)

    @property
    def rgb_array(
        self,
    ) -> np.ndarray[(3,), np.int_]:
        """Return Pixel value as a numpy array.

        Returns:
            RGB value as a numpy array
        """
        return np.array(
            [
                self.array[self._order[0]],
                self.array[self._order[1]],
                self.array[self._order[2]],
            ]
        )

    @property
    def rgb_tuple(
        self,
    ) -> tuple[np.int_, np.int_, np.int_]:
        """Return Pixel value as a numpy array.

        Returns:
            RGB value as a numpy array
        """
        return (
            self.array[self._order[0]],
            self.array[self._order[1]],
            self.array[self._order[2]],
        )

    @property
    def hexstr(self):
        """Returns the color value as an RGB hex strings regardless of underlying RGB order.

        Returns:
            _type_: _description_
        """
        rgb = self.tuple
        return f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def invert(self) -> Pixel:
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
    DARKGRAY = Pixel((64, 55, 50), order=LEDOrder.RGB)

    @classmethod
    def pseudoRandom(
        cls,
    ) -> Pixel:
        """Get a random color from the list of defined colors.

        Returns:
            a single random color from the list of defined colors
        """
        colors = list(dir(PixelColors))
        colors = [p for p in colors if "__" not in p and "random" not in p.lower() and "off" not in p.lower()]
        randomColor = colors[random.randint(0, len(colors) - 1)]
        return getattr(PixelColors, randomColor)

    @classmethod
    def random(
        cls,
    ) -> Pixel:
        """Get a randomly generated pixel value.

        Returns:
            a truly random RGB values int the range ([0,255], [0,255], [0,255])
        """
        colorOne = random.randint(0, 2)
        colorTwo = random.randint(0, 3)
        if colorOne != 0 or colorTwo == 0:
            redLED = random.randint(0, 255)
        else:
            redLED = 0
        if colorOne != 1 or colorTwo == 0:
            greenLED = random.randint(0, 255)
        else:
            greenLED = 0
        if colorOne != 2 or colorTwo == 0:
            blueLED = random.randint(0, 255)
        else:
            blueLED = 0
        return Pixel([redLED, greenLED, blueLED])
