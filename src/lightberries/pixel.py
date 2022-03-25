"""Define basic RGB pixel data and objects."""
from __future__ import annotations
import enum
import logging
import random
from typing import Any
import numpy as np

from lightberries.exceptions import LightBerryException, LightPixelException

LOGGER = logging.getLogger("LightBerries")


class EnumLEDOrder(enum.Enum):
    """This enum is for LED order in the physical pixels.

    If your colors are all wrong, try a different enum.
    """

    RGB: list[int] = [0, 1, 2]
    GRB: list[int] = [1, 0, 2]


DEFAULT_PIXEL_ORDER: list[int] = EnumLEDOrder.GRB.value


class Pixel:
    """This class defines a single LED pixel."""

    def __init__(
        self,
        rgb: int | np.ndarray[(3), np.dtype[Any]] | "Pixel" | None = None,
        order: EnumLEDOrder = DEFAULT_PIXEL_ORDER,
    ) -> None:
        """Create a single RGB LED pixel.

        Args:
            rgb: pixel color definition
            order: enum determining the order of the colors (e.g. RGB vs GRB)

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propogating an exception
            LightPixelException: if something bad happens
        """
        try:
            # initialize to zero
            self._value: int = 0

            if isinstance(order, EnumLEDOrder):
                _order = order.value
            else:
                _order = order

            self._order = _order

            # none gets a zero
            if rgb is None:
                self._value = 0

            # if it is an int and in range
            elif isinstance(rgb, (int, np.int_)) and rgb >= 0 and rgb <= 0xFFFFFF:
                rgb = int(rgb)
                # convert to tuple
                value = (
                    ((rgb & 0xFF0000) >> 16),
                    ((rgb & 0x00FF00) >> 8),
                    ((rgb & 0x0000FF) >> 0),
                )
                self._value = (
                    # use order enum
                    (int(value[_order[0]]) << 16)
                    + (int(value[_order[1]]) << 8)
                    + (int(value[_order[2]]))
                )

            # if it is a tuple, list, or numpy array
            elif (
                isinstance(rgb, tuple)
                or isinstance(rgb, list)
                or isinstance(rgb, np.ndarray)
                # and has length three
            ) and len(rgb) == 3:
                if rgb[0] > 255 or rgb[1] > 255 or rgb[2] > 255:
                    raise LightPixelException(f"Invalid Pixel values: {rgb}")
                # create a 3-byte int from the three bytes
                self._value = (
                    # this is where the rgb order comes into play
                    (int(rgb[_order[0]]) << 16)
                    + (int(rgb[_order[1]]) << 8)
                    + (int(rgb[_order[2]]))
                )

            # i think this is old and unused
            # elif isinstance(rgb, PixelColors):
            # self._value = rgb.value._value

            # this is an instance of this class, just use the value
            elif isinstance(rgb, Pixel):
                self._value = rgb._value

            # we've got an error boys!
            else:
                raise LightPixelException(
                    f"Cannot assign pixel using value: {str(rgb)} ({type(rgb)})"
                )

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightPixelException from ex

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
        return self._value

    def __str__(
        self,
    ) -> str:
        """Return the value of the pixel as a string.

        Returns:
            a string representation of the pixel
        """
        rgbValue = (
            (self._value & 0xFF0000) >> 16,
            (self._value & 0xFF00) >> 8,
            self._value & 0xFF,
        )
        return (
            "PX #"
            + f"{rgbValue[self._order[0]]:02X}"
            + f"{rgbValue[self._order[1]]:02X}"
            + f"{rgbValue[self._order[2]]:02X}"
        )

    def __repr__(
        self,
    ) -> str:
        """Represent the Pixel class as a string.

        Returns:
            a string representation of the Pixel instance
        """
        return f"<{self.__class__.__name__}> {self.__str__()} ({self._value}/{self._order})"

    def __eq__(self, other: object) -> bool:
        """Text pixel equality with other objects.

        Args:
            other: another object

        Returns:
            true if objects are equal
        """
        if not isinstance(other, (int, np.ndarray, tuple, Pixel, None)):
            return False
        # convert the pixel orders to the same order then compare
        return self.pixel._value == Pixel(other).pixel._value

    @property
    def tuple(
        self,
    ) -> tuple[int]:
        """Return Pixel value as a tuple of ints.

        Returns:
            the RGB value into tuple
        """
        rgbTuple = (
            (self._value & 0xFF0000) >> 16,
            (self._value & 0xFF00) >> 8,
            self._value & 0xFF,
        )
        return (
            rgbTuple[self._order[0]],
            rgbTuple[self._order[1]],
            rgbTuple[self._order[2]],
        )

    @property
    def pixel(
        self,
    ) -> "Pixel":
        """Return Pixel value with defaul RGB order.

        Returns:
            this pixel with default RGB order
        """
        return Pixel(self.tuple, DEFAULT_PIXEL_ORDER)

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
    def hexstr(self):
        """Returns the color value as an RGB hex strings regardless of underlying RGB order.

        Returns:
            _type_: _description_
        """
        rgb = self.tuple
        return f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    @property
    def int(self) -> int:
        return self._value


class PixelColors:
    """List of commonly used colors for ease of use."""

    OFF = Pixel((0, 0, 0), order=EnumLEDOrder.RGB).pixel.array
    RED3 = Pixel((64, 0, 0), order=EnumLEDOrder.RGB).pixel.array
    RED2 = Pixel((128, 0, 0), order=EnumLEDOrder.RGB).pixel.array
    RED = Pixel((255, 0, 0), order=EnumLEDOrder.RGB).pixel.array
    ORANGE3 = Pixel((64, 64, 0), order=EnumLEDOrder.RGB).pixel.array
    ORANGE2 = Pixel((128, 128, 0), order=EnumLEDOrder.RGB).pixel.array
    ORANGE = Pixel((255, 128, 0), order=EnumLEDOrder.RGB).pixel.array
    YELLOW = Pixel((255, 210, 80), order=EnumLEDOrder.RGB).pixel.array
    LIME = Pixel((128, 255, 0), order=EnumLEDOrder.RGB).pixel.array
    GREEN3 = Pixel((0, 64, 0), order=EnumLEDOrder.RGB).pixel.array
    GREEN2 = Pixel((0, 128, 0), order=EnumLEDOrder.RGB).pixel.array
    GREEN = Pixel((0, 255, 0), order=EnumLEDOrder.RGB).pixel.array
    TEAL = Pixel((0, 255, 128), order=EnumLEDOrder.RGB).pixel.array
    CYAN3 = Pixel((0, 64, 64), order=EnumLEDOrder.RGB).pixel.array
    CYAN2 = Pixel((0, 128, 128), order=EnumLEDOrder.RGB).pixel.array
    CYAN = Pixel((0, 255, 255), order=EnumLEDOrder.RGB).pixel.array
    SKY = Pixel((0, 128, 255), order=EnumLEDOrder.RGB).pixel.array
    BLUE = Pixel((0, 0, 255), order=EnumLEDOrder.RGB).pixel.array
    BLUE2 = Pixel((0, 0, 128), order=EnumLEDOrder.RGB).pixel.array
    BLUE3 = Pixel((0, 0, 64), order=EnumLEDOrder.RGB).pixel.array
    VIOLET = Pixel((128, 0, 255), order=EnumLEDOrder.RGB).pixel.array
    PURPLE = Pixel((128, 0, 128), order=EnumLEDOrder.RGB).pixel.array
    PURPLE2 = Pixel((64, 0, 64), order=EnumLEDOrder.RGB).pixel.array
    MIDNIGHT = Pixel((70, 0, 128), order=EnumLEDOrder.RGB).pixel.array
    MAGENTA = Pixel((255, 0, 255), order=EnumLEDOrder.RGB).pixel.array
    PINK = Pixel((255, 0, 128), order=EnumLEDOrder.RGB).pixel.array
    WHITE = Pixel((255, 255, 255), order=EnumLEDOrder.RGB).pixel.array
    GRAY = Pixel((128, 118, 108), order=EnumLEDOrder.RGB).pixel.array

    @classmethod
    def pseudoRandom(
        cls,
    ) -> np.ndarray[(3,), np.int_]:
        """Get a random color from the list of defined colors.

        Returns:
            a single random color from the list of defined colors
        """
        clrs = list(dir(PixelColors))
        clrs = [p for p in clrs if "__" not in p and "random" not in p.lower()]
        randomColor = clrs[random.randint(0, len(clrs) - 1)]
        while randomColor == "OFF":
            randomColor = clrs[random.randint(0, len(clrs) - 1)]
        return getattr(PixelColors, randomColor)

    @classmethod
    def random(
        cls,
    ) -> np.ndarray[(3,), np.int_]:
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
        return Pixel([redLED, greenLED, blueLED]).array
