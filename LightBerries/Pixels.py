import enum
import logging
import random
import inspect
from nptyping import NDArray
from typing import List, Optional, Tuple, Union, Any
import numpy as np

LOGGER = logging.getLogger("LightBerries")


class LED_ORDER(enum.Enum):
    """This enum is for LED order in the physical pixels

    If your colors are all wrong, try a different enum
    """

    RGB: List[int] = [0, 1, 2]
    GRB: List[int] = [1, 0, 2]


DEFAULT_PIXEL_ORDER = LED_ORDER.GRB


class Pixel:
    """This class defines a single LED pixel"""

    def __init__(
        self,
        rgb: Optional[Union[int, tuple, list, NDArray, "Pixel"]] = None,
        order: LED_ORDER = DEFAULT_PIXEL_ORDER,
    ):
        """Create a single RGB LED pixel.

        rgb: pixel color definition

        order: enum determining the order of the colors (e.g. RGB vs GRB)
        """
        try:
            # initialize to zero
            self._value: int = 0

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
                    raise Exception("Invalid Pixel values: {}".format(rgb))
                # create a 3-byte int from the three bytes
                self._value = (
                    # this is where the rgb order comes into play
                    (int(rgb[order.value[0]]) << 16)
                    + (int(rgb[order.value[1]]) << 8)
                    + (int(rgb[order.value[2]]))
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
                    "%s.%s Exception: Cannot assign pixel using value: %s"
                    % (self.__class__.__name__, inspect.stack()[0][3], rgb)
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
        x = (
            (self._value & 0xFF0000) >> 16,
            (self._value & 0xFF00) >> 8,
            self._value & 0xFF,
        )
        return "PX #{:02X}{:02X}{:02X}".format(
            x[DEFAULT_PIXEL_ORDER.value[0]],
            x[DEFAULT_PIXEL_ORDER.value[1]],
            x[DEFAULT_PIXEL_ORDER.value[2]],
        )

    def __repr__(self) -> str:
        """represent Pixel class as a string"""
        return "<{}> {}".format(self.__class__.__name__, self.__str__())

    @property
    def tuple(self) -> Tuple[int, int, int]:
        """return Pixel value as a tuple of ints"""
        x = (
            (self._value & 0xFF0000) >> 16,
            (self._value & 0xFF00) >> 8,
            self._value & 0xFF,
        )
        return (
            x[DEFAULT_PIXEL_ORDER.value[0]],
            x[DEFAULT_PIXEL_ORDER.value[1]],
            x[DEFAULT_PIXEL_ORDER.value[2]],
        )

    @property
    def array(self) -> NDArray[(3,), np.int32]:
        """return Pixel value as a numpy array"""
        return np.array(self.tuple)


class PixelColors:
    """List of commonly used colors for ease of use"""

    OFF = Pixel((0, 0, 0), order=LED_ORDER.RGB)
    RED2 = Pixel((128, 0, 0), order=LED_ORDER.RGB)
    RED = Pixel((255, 0, 0), order=LED_ORDER.RGB)
    ORANGE2 = Pixel((128, 128, 0), order=LED_ORDER.RGB)
    ORANGE = Pixel((255, 128, 0), order=LED_ORDER.RGB)
    YELLOW = Pixel((255, 210, 80), order=LED_ORDER.RGB)
    LIME = Pixel((128, 255, 0), order=LED_ORDER.RGB)
    GREEN2 = Pixel((0, 128, 0), order=LED_ORDER.RGB)
    GREEN = Pixel((0, 255, 0), order=LED_ORDER.RGB)
    TEAL = Pixel((0, 255, 128), order=LED_ORDER.RGB)
    CYAN2 = Pixel((0, 128, 128), order=LED_ORDER.RGB)
    CYAN = Pixel((0, 255, 255), order=LED_ORDER.RGB)
    SKY = Pixel((0, 128, 255), order=LED_ORDER.RGB)
    BLUE = Pixel((0, 0, 255), order=LED_ORDER.RGB)
    BLUE2 = Pixel((0, 0, 128), order=LED_ORDER.RGB)
    VIOLET = Pixel((128, 0, 255), order=LED_ORDER.RGB)
    PURPLE = Pixel((128, 0, 128), order=LED_ORDER.RGB)
    MIDNIGHT = Pixel((70, 0, 128), order=LED_ORDER.RGB)
    MAGENTA = Pixel((255, 0, 255), order=LED_ORDER.RGB)
    PINK = Pixel((255, 0, 128), order=LED_ORDER.RGB)
    WHITE = Pixel((255, 255, 255), order=LED_ORDER.RGB)
    GRAY = Pixel((128, 118, 108), order=LED_ORDER.RGB)

    @classmethod
    def pseudoRandom(self) -> NDArray[(3,), np.int32]:
        """get a random color from the list of defined colors"""
        clrs = list(dir(PixelColors))
        clrs = [p for p in clrs if "__" not in p and "random" not in p.lower()]
        randomColor = clrs[random.randint(0, len(clrs) - 1)]
        while randomColor == "OFF":
            randomColor = clrs[random.randint(0, len(clrs) - 1)]
        return getattr(PixelColors, randomColor).array

    @classmethod
    def random(self) -> NDArray[(3,), np.int32]:
        """get a randomly generated pixel value"""
        x = random.randint(0, 2)
        y = random.randint(0, 3)
        if x != 0 or y == 0:
            redLED = random.randint(0, 255)
        else:
            redLED = 0
        if x != 1 or y == 0:
            greenLED = random.randint(0, 255)
        else:
            greenLED = 0
        if x != 2 or y == 0:
            blueLED = random.randint(0, 255)
        else:
            blueLED = 0
        return Pixel([redLED, greenLED, blueLED]).array
