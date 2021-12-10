"""define basic RGB pixel data and objects"""
import enum
import logging
import random
import inspect
from typing import List, Optional, Tuple, Union
from nptyping import NDArray
import numpy as np

LOGGER = logging.getLogger("LightBerries")


class EnumLEDOrder(enum.Enum):
    """This enum is for LED order in the physical pixels

    If your colors are all wrong, try a different enum
    """

    RGB: List[int] = [0, 1, 2]
    GRB: List[int] = [1, 0, 2]


DEFAULT_PIXEL_ORDER: List[int] = EnumLEDOrder.GRB.value


class Pixel:
    """This class defines a single LED pixel"""

    def __init__(
        self,
        rgb: Optional[Union[int, tuple, list, NDArray, "Pixel"]] = None,
        order: Union[EnumLEDOrder, List[int]] = DEFAULT_PIXEL_ORDER,
    ):
        """Create a single RGB LED pixel.

        rgb: pixel color definition

        order: enum determining the order of the colors (e.g. RGB vs GRB)
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
            elif isinstance(rgb, int) and rgb >= 0 and rgb <= 0xFFFFFF:
                self._value = rgb

            # if it is a tuple, list, or numpy array
            elif (
                isinstance(rgb, tuple)
                or isinstance(rgb, list)
                or isinstance(rgb, np.ndarray)
                # and has length three
            ) and len(rgb) == 3:
                if rgb[0] > 255 or rgb[1] > 255 or rgb[2] > 255:
                    raise Exception(f"Invalid Pixel values: {rgb}")
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
                raise Exception(
                    f"{self.__class__.__name__}.{'__init__'} Exception: "
                    + "Cannot assign pixel using value: {rgb}"
                )

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def __len__(self) -> int:
        """return the length of the pixel color array"""
        return len(self.array)

    def __int__(self) -> int:
        """return the pixel value as a single integer value"""
        return self._value

    def __str__(self) -> str:
        """return value of pixel as a string"""
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

    def __repr__(self) -> str:
        """represent Pixel class as a string"""
        return f"<{self.__class__.__name__}> {self.__str__()}"

    @property
    def tuple(self) -> Tuple[int, int, int]:
        """return Pixel value as a tuple of ints"""
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
    def array(self) -> NDArray[(3,), np.int32]:
        """return Pixel value as a numpy array"""
        return np.array(self.tuple)


class PixelColors:
    """List of commonly used colors for ease of use"""

    OFF = Pixel((0, 0, 0), order=EnumLEDOrder.RGB)
    RED2 = Pixel((128, 0, 0), order=EnumLEDOrder.RGB)
    RED = Pixel((255, 0, 0), order=EnumLEDOrder.RGB)
    ORANGE2 = Pixel((128, 128, 0), order=EnumLEDOrder.RGB)
    ORANGE = Pixel((255, 128, 0), order=EnumLEDOrder.RGB)
    YELLOW = Pixel((255, 210, 80), order=EnumLEDOrder.RGB)
    LIME = Pixel((128, 255, 0), order=EnumLEDOrder.RGB)
    GREEN2 = Pixel((0, 128, 0), order=EnumLEDOrder.RGB)
    GREEN = Pixel((0, 255, 0), order=EnumLEDOrder.RGB)
    TEAL = Pixel((0, 255, 128), order=EnumLEDOrder.RGB)
    CYAN2 = Pixel((0, 128, 128), order=EnumLEDOrder.RGB)
    CYAN = Pixel((0, 255, 255), order=EnumLEDOrder.RGB)
    SKY = Pixel((0, 128, 255), order=EnumLEDOrder.RGB)
    BLUE = Pixel((0, 0, 255), order=EnumLEDOrder.RGB)
    BLUE2 = Pixel((0, 0, 128), order=EnumLEDOrder.RGB)
    VIOLET = Pixel((128, 0, 255), order=EnumLEDOrder.RGB)
    PURPLE = Pixel((128, 0, 128), order=EnumLEDOrder.RGB)
    MIDNIGHT = Pixel((70, 0, 128), order=EnumLEDOrder.RGB)
    MAGENTA = Pixel((255, 0, 255), order=EnumLEDOrder.RGB)
    PINK = Pixel((255, 0, 128), order=EnumLEDOrder.RGB)
    WHITE = Pixel((255, 255, 255), order=EnumLEDOrder.RGB)
    GRAY = Pixel((128, 118, 108), order=EnumLEDOrder.RGB)

    @classmethod
    def pseudoRandom(cls) -> NDArray[(3,), np.int32]:
        """get a random color from the list of defined colors"""
        clrs = list(dir(PixelColors))
        clrs = [p for p in clrs if "__" not in p and "random" not in p.lower()]
        randomColor = clrs[random.randint(0, len(clrs) - 1)]
        while randomColor == "OFF":
            randomColor = clrs[random.randint(0, len(clrs) - 1)]
        return getattr(PixelColors, randomColor).array

    @classmethod
    def random(cls) -> NDArray[(3,), np.int32]:
        """get a randomly generated pixel value"""
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
