import sys
import numpy as np
import time
import random
import logging
from enum import IntEnum
from nptyping import NDArray
from numpy.core.fromnumeric import size
from LightBerries.rpi_ws281x_patch import rpi_ws281x
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightStrings import LightString
from LightBerries.LightFunctions import LightFunction
from typing import (
    Dict,
    List,
    Optional,
    Union,
    Any,
)
from LightBerries.LightPatterns import (
    PixelArray,
    SolidColorArray,
    ConvertPixelArrayToNumpyArray,
    RepeatingColorSequenceArray,
    ColorTransitionArray,
    RainbowArray,
    RepeatingRainbowArray,
    ReflectArray,
    get_DEFAULT_COLOR_SEQUENCE,
    DEFAULT_BACKGROUND_COLOR,
)

try:
    from numba import jit
except:
    print("install numba for possible speed boost")

LOGGER = logging.getLogger("LightBerries")
DEFAULT_REFRESH_DELAY = 50


class LightController:
    """
    This library wraps the rpi_ws281x library and provides some lighting functions.
    see https://github.com/rpi-ws281x/rpi-ws281x-python for questions about that library

    Quick Start:
            1: Create a LightController object specifying ledCount:int, pwmGPIOpin:int, channelDMA:int, frequencyPWM:int
                    lf = LightController(10, 18, 10, 800000)

            2: Choose a color pattern
                    lf.useColorRainbow()

            3: Choose a function
                    lf.useFunctionCylon()

            4: Choose a duration to run
                    lf.secondsPerMode = 60

            5: Run
                    lf.run()

    """

    def __init__(
        self,
        ledCount: int,
        pwmGPIOpin: int,
        channelDMA: int,
        frequencyPWM: int,
        invertSignalPWM: bool = False,
        ledBrightnessFloat: float = 0.75,
        channelPWM: int = 0,
        stripTypeLED=None,
        gamma=None,
        debug: bool = False,
        verbose: bool = False,
    ) -> None:
        """
        Create a LightController object for running patterns across a rpi_ws281x LED string

        ledCount: the number of Pixels in your string of LEDs
        pwmGPIOpin: the GPIO pin number your lights are hooked up to (18 is a good choice since it does PWM)
        channelDMA: the DMA channel to use (5 is a good option)
        frequencyPWM: try 800,000
        invertSignalPWM: set true to invert the PWM signal
        ledBrightnessFloat: set to a value between 0.0 (OFF), and 1.0 (ON).
                This setting tends to introduce flicker the lower it is
        channelPWM: defaults to 0, see https://github.com/rpi-ws281x/rpi-ws281x-python
        stripTypeLED: see https://github.com/rpi-ws281x/rpi-ws281x-python
        gamma: see https://github.com/rpi-ws281x/rpi-ws281x-python
        debug: set true for some debugging messages
        verbose: set true for even more information
        """
        try:
            if True == debug or True == verbose:
                LOGGER.setLevel(logging.DEBUG)
            if True == verbose:
                LOGGER.setLevel(5)
            pixelStrip = rpi_ws281x.PixelStrip(
                pin=pwmGPIOpin,
                dma=channelDMA,
                num=ledCount,
                freq_hz=frequencyPWM,
                channel=channelPWM,
                invert=invertSignalPWM,
                gamma=gamma,
                strip_type=stripTypeLED,
                brightness=int(255 * ledBrightnessFloat),
            )
            self.ws28xxLightString: Optional[LightString] = LightString(
                pixelStrip=pixelStrip,
                debug=verbose,
            )

            if True == verbose:
                self.ws28xxLightString.setDebugLevel(5)
            self.__LEDCount: int = len(self.ws28xxLightString)
            self._VirtualLEDArray: NDArray[(3, Any), np.int32] = SolidColorArray(
                arrayLength=self.__LEDCount,
                color=PixelColors.OFF,
            )
            self.__OverlayDict: Dict[int, NDArray[(3,), np.int32]] = {}
            self.__VirtualLEDCount: int = len(self._VirtualLEDArray)
            self._VirtualLEDIndexArray: NDArray[(Any,), np.int32] = np.array(
                range(len(self.ws28xxLightString))
            )
            self.__VirtualLEDIndexCount: int = len(self._VirtualLEDIndexArray)
            self.__LastModeChange: float = time.time() - 1000
            self.__NextModeChange: float = time.time()

            self.__refreshDelay: float = 0.001
            self.__secondsPerMode: float = 120.0
            self.__backgroundColor: NDArray[(3,), np.int32] = PixelColors.OFF.array
            self.__colorSequence: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([])
            self.__colorSequenceCount: int = 0
            self.__colorSequenceIndex: int = 0
            self.__LoopForever: bool = False
            self.__LightFunctions: List[LightFunction] = []

            LightFunction.Controller = self

            self.reset()
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                "__init__",
                ex,
            )
            raise

    def __del__(
        self,
    ) -> None:
        """
        disposes of the rpi_ws281x object (if it exists) to prevent memory leaks
        """
        try:
            if hasattr(self, "_LEDArray") and not self.ws28xxLightString is None:
                self._off()
                self._copyVirtualLedsToWS281X()
                self._refreshLEDs()
                self.ws28xxLightString.__del__()
                self.ws28xxLightString = None
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.__del__.__name__,
                ex,
            )
            raise

    @property
    def virtualLEDCount(self) -> int:
        return self.__VirtualLEDCount

    @property
    def LEDCount(self) -> int:
        return self.__LEDCount

    @property
    def refreshDelay(
        self,
    ) -> float:
        """ """
        return self.__refreshDelay

    @refreshDelay.setter
    def refreshDelay(
        self,
        delay: float,
    ) -> None:
        """ """
        self.__refreshDelay = float(delay)

    @property
    def backgroundColor(
        self,
    ) -> NDArray[(3,), np.int32]:
        """ """
        return self.__backgroundColor

    @backgroundColor.setter
    def backgroundColor(
        self,
        color: NDArray[(3,), np.int32],
    ) -> None:
        """ """
        self.__backgroundColor = Pixel(color).array

    @property
    def secondsPerMode(
        self,
    ) -> float:
        """ """
        return self.__secondsPerMode

    @secondsPerMode.setter
    def secondsPerMode(
        self,
        seconds: float,
    ) -> None:
        """ """
        self.__secondsPerMode = float(seconds)

    @property
    def colorSequence(
        self,
    ) -> NDArray[(3, Any), np.int32]:
        """ """
        return self.__colorSequence

    @colorSequence.setter
    def colorSequence(
        self,
        colorSequence: NDArray[(3, Any), np.int32],
    ) -> None:
        """ """
        self.__colorSequence = np.copy(ConvertPixelArrayToNumpyArray(colorSequence))
        self.colorSequenceCount = len(self.__colorSequence)
        self.colorSequenceIndex = 0

    @property
    def colorSequenceCount(
        self,
    ) -> int:
        """ """
        return self.__colorSequenceCount

    @colorSequenceCount.setter
    def colorSequenceCount(
        self,
        colorSequenceCount: int,
    ) -> None:
        """ """
        self.__colorSequenceCount = colorSequenceCount

    @property
    def colorSequenceIndex(
        self,
    ) -> int:
        """ """
        return self.__colorSequenceIndex

    @colorSequenceIndex.setter
    def colorSequenceIndex(
        self,
        colorSequenceIndex: int,
    ) -> None:
        """ """
        self.__colorSequenceIndex = colorSequenceIndex

    @property
    def colorSequenceNext(
        self,
    ) -> NDArray[(3,), np.int32]:
        """ """
        if not callable(self.colorSequence):
            temp = self.colorSequence[self.colorSequenceIndex]
            self.colorSequenceIndex += 1
            if self.colorSequenceIndex >= self.colorSequenceCount:
                self.colorSequenceIndex = 0
        else:
            temp = self.colorSequence()
        if isinstance(temp, Pixel):
            return temp.array
        else:
            return temp

    @property
    def functionList(self) -> List[LightFunction]:
        return self.__LightFunctions

    @property
    def overlayDictionary(self) -> Dict[int, Any]:
        return self.__OverlayDict

    def reset(
        self,
    ) -> None:
        """
        reset class variables to default state
        """
        try:
            self.__LightFunctions = []
            if self.virtualLEDCount > self.LEDCount:
                self._setVirtualLEDArray(self._VirtualLEDArray[: self.LEDCount])
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.reset.__name__,
                ex,
            )
            raise

    def _setVirtualLEDArray(
        self,
        ledArray: Union[List[Pixel], NDArray[(3, Any), np.int32]],
    ) -> None:
        """Assign a sequence of pixel data to the LED buffer"""
        try:
            # make sure the passed LED array is the correct type
            if isinstance(ledArray, list):
                _ledArray = ConvertPixelArrayToNumpyArray(ledArray)
            elif isinstance(ledArray, np.ndarray):
                _ledArray = ledArray
            else:
                _ledArray = SolidColorArray(arrayLength=self.LEDCount, color=self.backgroundColor)

            # check assignment length
            if len(_ledArray) >= self.LEDCount:
                self._VirtualLEDArray = _ledArray
            else:
                self._VirtualLEDArray[: len(_ledArray)] = _ledArray

            # assign new LED array to virtual LEDs
            self.__VirtualLEDCount = len(self._VirtualLEDArray)
            # set our indices for virtual LEDs
            self.__VirtualLEDIndexCount = self.__VirtualLEDCount
            # create array of index values for manipulation if needed
            self._VirtualLEDIndexArray = np.array(range(self.__VirtualLEDIndexCount))
            # if the array is smaller than the actual light strand, make our entire strand addressable
            if self.__VirtualLEDIndexCount < self.LEDCount:
                self.__VirtualLEDIndexCount = self.LEDCount
                self._VirtualLEDIndexArray = np.array(range(self.__VirtualLEDIndexCount))
                self._VirtualLEDArray = np.concatenate(
                    (
                        self._VirtualLEDArray,
                        np.array(
                            [PixelColors.OFF.tuple for i in range(self.LEDCount - self.virtualLEDCount)]
                        ),
                    )
                )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._setVirtualLEDArray.__name__,
                ex,
            )
            raise

    def _copyVirtualLedsToWS281X(
        self,
    ) -> None:
        """
        Sets each Pixel in the rpi_ws281x object to the buffered array value
        """
        try:
            # callback function to do work
            def set_pixel(irgb):
                i = irgb[0]
                rgb = irgb[1]
                if i < self.LEDCount:
                    self.ws28xxLightString[i] = rgb

            # fast method of calling the callback method on each index of LED array
            list(
                map(
                    set_pixel,
                    enumerate(
                        self._VirtualLEDArray[self._VirtualLEDIndexArray][
                            np.where(self._VirtualLEDIndexArray < self.LEDCount)
                        ]
                    ),
                )
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._copyVirtualLedsToWS281X.__name__,
                ex,
            )
            raise

    def _refreshLEDs(
        self,
    ) -> None:
        """
        Display current LED buffer
        """
        try:
            # call light string's refresh method to send the communications out to the addressable LEDs
            if self.ws28xxLightString is not None:
                self.ws28xxLightString.refresh()
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._refreshLEDs.__name__,
                ex,
            )
            raise

    def _off(
        self,
    ) -> None:
        """
        set all Pixels to RGD background color
        """
        try:
            # clear all current values
            self._VirtualLEDArray *= 0
            # set to background color
            self._VirtualLEDArray[:] += self.backgroundColor
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._off.__name__,
                ex,
            )
            raise

    def _runFunctions(
        self,
    ) -> None:
        """
        Run each function in the configured function list
        """
        try:
            # invoke the function pointer saved in the light data object
            for function in self.__LightFunctions:
                function.runFunction(function)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._runFunctions.__name__,
                ex,
            )
            raise

    def _copyOverlays(
        self,
    ):
        """ """
        try:
            # iterate over the dictionary key-value pairs, assign LED values
            # directly to output buffer skipping the virtual LED copies.
            # This ensures that overlays are temporary and get overwritten
            # next refresh.
            for index, ledValue in self.__OverlayDict.items():
                self.ws28xxLightString[index] = ledValue
            self.__OverlayDict = {}
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._runFunctions.__name__,
                ex,
            )
            raise

    def getRandomIndex(
        self,
    ) -> int:
        """
        retrieve a random Pixel index
        """
        try:
            return random.randint(0, (self.virtualLEDCount - 1))
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.getRandomIndex.__name__,
                ex,
            )
            raise

    def getRandomIndices(
        self,
        count: int,
    ) -> NDArray[(Any), np.int32]:
        """
        retrieve a random list of Pixel indices
        """
        try:
            temp = []
            for i in range(count):
                temp.append(self.getRandomIndex())
            return np.array(temp)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.getRandomIndices.__name__,
                ex,
            )
            raise

    def getRandomDirection(self) -> int:
        """"""
        return [-1, 1][random.randint(0, 1)]

    def _fadeColor(
        self, color: NDArray[(3,), np.int32], colorNext: NDArray[(3,), np.int32], fadeCount: int
    ) -> NDArray[(3,), np.int32]:
        """fade an LED's color by the given amount and return the new RGB values"""
        # copy it to make sure we dont change the original by reference
        _color = np.copy(color)
        # loop through RGB values
        for rgbIndex in range(len(_color)):
            # the values closest to the target color might match already
            if _color[rgbIndex] != colorNext[rgbIndex]:
                # subtract or add as appropriate in order to get closer to target color
                if _color[rgbIndex] - fadeCount > colorNext[rgbIndex]:
                    _color[rgbIndex] -= fadeCount
                elif _color[rgbIndex] + fadeCount < colorNext[rgbIndex]:
                    _color[rgbIndex] += fadeCount
                else:
                    _color[rgbIndex] = colorNext[rgbIndex]
        return _color

    def run(self):
        """
        Run the configured color pattern and function either forever or for self.secondsPerMode
        """
        try:
            LOGGER.info("%s.%s:", self.__class__.__name__, self.run.__name__)
            # set start time
            self.__LastModeChange = time.time()
            # set a target time to change
            if self.secondsPerMode is None:
                self.__NextModeChange = self.__LastModeChange + (random.uniform(30, 120))
            else:
                self.__NextModeChange = self.__LastModeChange + (self.secondsPerMode)
            # loop
            while time.time() < self.__NextModeChange or self.__LoopForever:
                try:
                    # run the selected functions using LightFunction object callbacks
                    self._runFunctions()
                    # copy the resulting RGB values to the ws28xx LED buffer
                    self._copyVirtualLedsToWS281X()
                    # copy temporary changes (not buffered in this class) to the ws28xx LED buffer
                    self._copyOverlays()
                    # tell the ws28xx controller to transmit the new data
                    self._refreshLEDs()
                except KeyboardInterrupt:
                    raise
                except SystemExit:
                    raise
                except Exception as ex:
                    LOGGER.exception("_Run Loop Error: {}".format(ex))
                    raise
            self.__LastModeChange = time.time()
            if self.secondsPerMode is None:
                self.__NextModeChange = self.__LastModeChange + (random.random(30, 120))
            else:
                self.__NextModeChange = self.__LastModeChange + (self.secondsPerMode)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.run.__name__,
                ex,
            )
            raise

    def useColorSingle(
        self,
        foregroundColor: Pixel = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Sets the the color sequence used by light functions to a single color of your choice

        foregroundColor: the color that each pixel will be set to
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSingle.__name__)

            # either calculate forground color or use the passed in one
            if foregroundColor is None:
                s = get_DEFAULT_COLOR_SEQUENCE()
                _foregroundColor = s[random.randint(0, len(s) - 1)]
            else:
                _foregroundColor = Pixel(foregroundColor).array

            # set the background color to the default
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # set the new color sequence using the foreground color
            self.colorSequence = ConvertPixelArrayToNumpyArray([_foregroundColor])
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSingle.__name__,
                ex,
            )
            raise

    def useColorSinglePseudoRandom(
        self,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Sets the the color sequence used by light functions to a single random named color
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSinglePseudoRandom.__name__)

            # set background color
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # set the color sequence
            self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.pseudoRandom()])
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSinglePseudoRandom.__name__,
                ex,
            )
            raise

    def useColorSingleRandom(
        self,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Sets the the color sequence to a single random RGB value
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSingleRandom.__name__)

            # set the background color to the default values
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # set the color sequence to a single random value
            self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.random()])
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSingleRandom.__name__,
                ex,
            )
            raise

    def useColorSequence(
        self,
        colorSequence: List[Pixel] = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Sets the the color sequence used by light functions to one of your choice

        colorSequence: list of colors in the pattern
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequence.__name__)

            # set the color sequence to the default one for this month, or use the passed in argument
            if colorSequence is None:
                _colorSequence = get_DEFAULT_COLOR_SEQUENCE()
            else:
                _colorSequence = [Pixel(p) for p in colorSequence]

            # assign the background color its default value
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # set the color sequence
            self.colorSequence = ConvertPixelArrayToNumpyArray(_colorSequence)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSequence.__name__,
                ex,
            )
            raise

    def useColorSequencePseudoRandom(
        self,
        sequenceLength: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Sets the color sequence used in light functions to a random list of named colors

        sequenceLength: the number of random colors to use in the generated sequence
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequencePseudoRandom.__name__)

            # either calculate a sequence length or use the passed value
            if sequenceLength is None:
                _sequenceLength = random.randint(self.LEDCount // 20, self.LEDCount // 10)
            else:
                _sequenceLength = int(sequenceLength)

            # set background color
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # assign the color sequence
            self.colorSequence = ConvertPixelArrayToNumpyArray(
                [PixelColors.pseudoRandom() for i in range(_sequenceLength)]
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSequencePseudoRandom.__name__,
                ex,
            )
            raise

    def useColorSequenceRandom(
        self,
        sequenceLength: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Sets the color sequence used in light functions to a random list of RGB values

        sequenceLength: the number of random colors to use in the generated sequence
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequenceRandom.__name__)

            # set background color
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # calculate sequence length or use argument
            if sequenceLength is None:
                _sequenceLength = random.randint(self.LEDCount // 20, self.LEDCount // 10)
            else:
                _sequenceLength = int(sequenceLength)

            # create color sequence
            self.colorSequence = ConvertPixelArrayToNumpyArray(
                [PixelColors.random() for i in range(_sequenceLength)]
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSequenceRandom.__name__,
                ex,
            )
            raise

    def useColorSequenceRepeating(
        self, colorSequence: List[Pixel] = None, backgroundColor: Pixel = None
    ) -> None:
        """
        Sets the color sequence used by light functions to the sequence given, buts repeats it across the entire light string
        If the sequence will not fill perfectly when repeated, the virtual LED string is extended until it fits

        colorSequence: list of colors to in the pattern being shifted across the LED string
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequenceRepeating.__name__)

            # use argument or default
            if colorSequence is None:
                _colorSequence = get_DEFAULT_COLOR_SEQUENCE()
            else:
                _colorSequence = [Pixel(p) for p in colorSequence]

            # use argument or default
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # calculate required virtual LED count to allow for even multiple of this sequence
            _arrayLength = np.ceil(self.LEDCount / len(_colorSequence)) * len(_colorSequence)

            # create color sequence
            self.colorSequence = RepeatingColorSequenceArray(
                arrayLength=_arrayLength, colorSequence=_colorSequence
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorSequenceRepeating.__name__,
                ex,
            )
            raise

    def useColorTransition(
        self,
        colorSequence: List[Pixel] = None,
        stepsPerTransition: int = None,
        wrap: bool = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        sets the color sequence used by light functions to the one specified in the argument, but
        makes a smooth transition from one color to the next over the length specified

        colorSequence: list of colors to transition between
        stepsPerTransition:  how many pixels it takes to transition from one color to the next
        wrap: if true, the last color of the sequence will transition to the first color as the final transition
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransition.__name__)

            # set color sequence
            if colorSequence is None:
                _colorSequence = get_DEFAULT_COLOR_SEQUENCE()
            else:
                _colorSequence = colorSequence

            # set background color
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            if stepsPerTransition is None:
                _stepsPerTransition = random.randint(3, 7)
            else:
                _stepsPerTransition = int(stepsPerTransition)

            if wrap is None:
                _wrap = [True, False][random.randint(0, 1)]
            else:
                _wrap = bool(wrap)

            self.colorSequence = ColorTransitionArray(
                arrayLength=len(_colorSequence) * int(_stepsPerTransition),
                wrap=_wrap,
                colorSequence=_colorSequence,
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorTransition.__name__,
                ex,
            )
            raise

    def useColorTransitionRepeating(
        self,
        colorSequence: List[Pixel] = None,
        stepsPerTransition: int = None,
        wrap: bool = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        colorSequence: list of colors to in the pattern being shifted across the LED string
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransitionRepeating.__name__)

            if colorSequence is None:
                _colorSequence = get_DEFAULT_COLOR_SEQUENCE()
            else:
                _colorSequence = [Pixel(p) for p in colorSequence]

            if stepsPerTransition is None:
                _stepsPerTransition = random.randint(3, 7)
            else:
                _stepsPerTransition = int(stepsPerTransition)

            if wrap is None:
                _wrap = [True, False][random.randint(0, 1)]
            else:
                _wrap = bool(wrap)

            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            _tempColorSequence = ColorTransitionArray(
                arrayLength=(len(_colorSequence) * _stepsPerTransition),
                wrap=_wrap,
                colorSequence=_colorSequence,
            )

            _arrayLength = np.ceil(self.LEDCount / len(_tempColorSequence)) * len(_tempColorSequence)

            self.colorSequence = RepeatingColorSequenceArray(
                arrayLength=_arrayLength, colorSequence=_tempColorSequence
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorTransitionRepeating.__name__,
                ex,
            )
            raise

    def useColorRainbow(
        self,
        rainbowPixelCount: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

        rainbowPixels: when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbow.__name__)

            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            if rainbowPixelCount is None:
                _rainbowPixelCount = random.randint(10, self.LEDCount // 2)
            else:
                _rainbowPixelCount = int(rainbowPixelCount)

            self.colorSequence = np.array(RainbowArray(arrayLength=_rainbowPixelCount))
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorRainbow.__name__,
                ex,
            )
            raise

    def useColorRainbowRepeating(
        self,
        rainbowPixelCount: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """
        Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

        rainbowPixels: when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbowRepeating.__name__)

            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            if rainbowPixelCount is None:
                _rainbowPixelCount = random.randint(10, self.LEDCount // 2)
            else:
                _rainbowPixelCount = int(rainbowPixelCount)

            _arrayLength = np.ceil(self.LEDCount / _rainbowPixelCount) * _rainbowPixelCount

            self.colorSequence = np.copy(
                RepeatingRainbowArray(arrayLength=_arrayLength, segmentLength=_rainbowPixelCount)
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorRainbowRepeating.__name__,
                ex,
            )
            raise

    def useFunctionNone(
        self,
    ) -> None:
        """ """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionNone.__name__)
            # create an object to put in the light data list so we dont just abort the run
            nothing = LightFunction(LightFunction.functionNone, self.colorSequence)
            self.__LightFunctions.append(nothing)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionNone.__name__,
                ex,
            )
            raise

    def useFunctionSolidColorCycle(
        self,
        delayCount: int = None,
    ) -> None:
        """
        Set all LEDs to a single color at once, but cycle between entries in a list of colors

        delayCount: number of led updates between color updates
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionSolidColorCycle.__name__)

            if delayCount is None:
                _delayCount = random.randint(50, 100)
            else:
                _delayCount = int(delayCount)

            # create the tracking object
            cycle = LightFunction(LightFunction.functionSolidColorCycle, self.colorSequence)
            # set refresh counter
            cycle.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            cycle.delayCountMax = _delayCount

            # clear LEDs, assign first color in sequence to all LEDs
            self.__LightFunctions.append(cycle)
            self._VirtualLEDArray *= 0
            self._VirtualLEDArray += self.colorSequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionSolidColorCycle.__name__,
                ex,
            )
            raise

    def useFunctionMarquee(
        self,
        shiftAmount: int = None,
        delayCount: int = None,
    ) -> None:
        """
        Shifts a color pattern across the LED string marquee style.
        Uses the provided sequence of colors.

        shiftAmount: the number of pixels the marquee shifts on each update
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMarquee.__name__)

            if shiftAmount is None:
                _shiftAmount = random.randint(1, 2)
            else:
                _shiftAmount = int(shiftAmount)

            if delayCount is None:
                _delayCount = random.randint(0, 6)
            else:
                _delayCount = int(delayCount)

            # turn off all LEDs every time so we can turn on new ones
            off = LightFunction(LightFunction.functionOff, self.colorSequence)
            # add this function to list
            self.__LightFunctions.append(off)

            # create tracking object
            marquee = LightFunction(LightFunction.functionMarquee, self.colorSequence)
            # store the size of the color sequence being shifted back and forth
            marquee.size = self.colorSequenceCount
            # assign starting direction
            marquee.direction = 1
            # this is how much the LEDs will move by each time
            marquee.step = _shiftAmount
            # this is how many LED updates will be ignored before doing another LED shift
            marquee.delayCountMax = _delayCount
            # add this function to list
            self.__LightFunctions.append(marquee)

            # this function just shifts the existing buffer, so make sure the buffer is initialized here
            self._setVirtualLEDArray(self.colorSequence)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionMarquee.__name__,
                ex,
            )
            raise

    def useFunctionCylon(
        self,
        fadeAmount: int = None,
        delayCount: int = None,
    ) -> None:
        """
        Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        fadeAmount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionCylon.__name__)
            if fadeAmount is None:
                _fadeAmount = random.randint(5, 75) / 255.0
            else:
                _fadeAmount = int(fadeAmount)

            if delayCount is None:
                _delayCount = random.randint(1, 6)
            else:
                _delayCount = int(delayCount)

            # fade the whole LED strand
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            # by this amount
            fade.fadeAmount = _fadeAmount
            self.__LightFunctions.append(fade)

            # # use marquee function
            # for i in range(self.colorSequenceCount):
            #     # Create cylon tracking object
            #     cylon = LightFunction(
            #         LightFunction.functionMarquee, ConvertPixelArrayToNumpyArray([self.colorSequenceNext])
            #     )
            #     # shift eye by this much for each update
            #     cylon.index = i
            #     # cylon.color=self.colorSequenceNext
            #     # set counter limit for skipping LED refreshes
            #     cylon.delayCountMax = _delayCount
            #     self.__LightFunctions.append(cylon)

            # use cylon function
            cylon = LightFunction(LightFunction.functionCylon, self.colorSequence)

            # shift eye by this much for each update
            # cylon.step = i
            cylon.size = self.colorSequenceCount
            # set counter limit for skipping LED refreshes

            cylon.index = self.virtualLEDCount - cylon.size - 3
            cylon.indexNext = cylon.index
            cylon.delayCounter = _delayCount
            cylon.delayCountMax = _delayCount
            self.__LightFunctions.append(cylon)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionCylon.__name__,
                ex,
            )
            raise

    def useFunctionMerge(
        self,
        delayCount: int = None,
    ) -> None:
        """
        Reflect a color sequence and shift the reflections toward each other in the middle

        mergeSegmentLength: length of reflected segments
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMerge.__name__)

            if delayCount is None:
                _delayCount = random.randint(6, 12)
            else:
                _delayCount = int(delayCount)

            # make sure doing a merge function would be visible
            if self.colorSequenceCount >= self.LEDCount:
                # if seqeuence is too long, cut it in half
                self.colorSequence = self.colorSequence[: int(self.colorSequenceCount // 2)]
                # dont remember offhand why this is here
                if self.colorSequenceCount % 2 == 1:
                    if self.colorSequenceCount == 1:
                        self.colorSequence = np.concatenate(self.colorSequence, self.colorSequence)
                    else:
                        self.colorSequence = self.colorSequence[:-1]
            # calculate modulo length
            _arrayLength = np.ceil(self.LEDCount / self.colorSequenceCount) * self.colorSequenceCount
            # update LED buffer with any changes we had to make
            self._setVirtualLEDArray(
                ReflectArray(
                    arrayLength=_arrayLength,
                    colorSequence=self.colorSequence,
                    foldLength=self.colorSequenceCount,
                )
            )
            # create tracking object
            merge = LightFunction(LightFunction.functionMerge, self.colorSequence)
            # set merge size
            merge.size = self.colorSequenceCount
            # set shift amount
            merge.step = 1
            # set the number of LED refreshes to skip
            merge.delayCountMax = _delayCount
            self.__LightFunctions.append(merge)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionMerge.__name__,
                ex,
            )
            raise

    def useFunctionAccelerate(
        self,
        delayCountMax: int = None,
        stepCountMax: int = None,
        fadeAmount: float = None,
        cycleColors: bool = None,
    ) -> None:
        """
        Shifts a color pattern across the LED string marquee style, but accelerates as it goes.
        Uses the provided sequence of colors.

        beginDelay: initial delay between color updates
        endDelay: final delay between color updates
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionAccelerate.__name__)

            if delayCountMax is None:
                _delayCountMax = random.randint(5, 10)
            else:
                _delayCountMax = int(delayCountMax)

            if stepCountMax is None:
                _stepCountMax = random.randint(4, 10)
            else:
                _stepCountMax = int(stepCountMax)

            if fadeAmount is None:
                _fadeAmount = random.randint(15, 35) / 255.0
            else:
                _fadeAmount = float(fadeAmount)

            if cycleColors is None:
                _cycleColors = [True, False][random.randint(0, 1)]
            else:
                _cycleColors = bool(cycleColors)

            # we want comet trails, so fade the buffer each time through
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.__LightFunctions.append(fade)

            # create tracking object
            accelerate = LightFunction(LightFunction.functionAccelerate, self.colorSequence)
            # this determines the maximum that the LED can jump in a single step as it speeds up
            accelerate.stepCountMax = _stepCountMax
            # set the number of updates to skip
            accelerate.delayCountMax = _delayCountMax
            # this determines the number of times the LED will speed up
            accelerate.stateMax = accelerate.delayCountMax
            # set color cycle setting
            accelerate.colorCycle = _cycleColors
            # randomize direction
            accelerate.direction = self.getRandomDirection()
            # randomize start index
            accelerate.index = self.getRandomIndex()
            # add to list
            self.__LightFunctions.append(accelerate)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionAccelerate.__name__,
                ex,
            )
            raise

    def useFunctionRandomChange(
        self,
        delayCount: int = None,
        changeCount: int = None,
        fadeStepCount: int = None,
        fade: bool = None,
    ) -> None:
        """
        Randomly changes pixels on the string to one of the provided colors by fading from one color to the next

        changeChance: chance that any one pixel will change colors each update (from 0.0, to 1.0)
        fadeStepCount: number of steps in the transition from one color to the next
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionRandomChange.__name__)

            if changeCount is None:
                _changeCount = random.randint(self.virtualLEDCount // 5, self.virtualLEDCount)
            else:
                _changeCount = int(changeCount)

            if fadeStepCount is None:
                _fadeStepCount = random.randint(5, 20)
            else:
                _fadeStepCount = int(fadeStepCount)

            if delayCount is None:
                _delayCountMax = random.randint(30, 50)
            else:
                _delayCountMax = int(delayCount)

            if fade is None:
                _fade = [True, False][random.randint(0, 1)]
            else:
                _fade = bool(fade)

            _fadeAmount = _fadeStepCount / 255.0

            # create a bunch of tracking objects
            for index in self.getRandomIndices(int(_changeCount)):
                if index < self.virtualLEDCount:
                    change = LightFunction(LightFunction.functionRandomChange, self.colorSequence)
                    # set the index from our random number
                    change.index = int(index)
                    # set the fade to off amount
                    change.fadeAmount = _fadeAmount
                    # set the color fade
                    change.colorFade = _fadeStepCount
                    # this is used to help calculate fade duration in the function
                    change.stepCountMax = _fadeStepCount
                    # copy the current color of this LED index
                    change.color = np.copy(self._VirtualLEDArray[change.index])
                    # set the color we are fading to randomly
                    if random.randint(0, 1) == 1:
                        change.colorNext = self.colorSequenceNext
                    else:
                        change.colorNext = change.color
                    # set the refresh delay
                    change.delayCountMax = _delayCountMax
                    # we want all the delays random, so dont start them all at zero
                    change.delayCounter = random.randint(0, change.delayCountMax)
                    # set true to fade, false to "instant on/off"
                    change.fade = _fade
                    self.__LightFunctions.append(change)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionRandomChange.__name__,
                ex,
            )
            raise

    def useFunctionMeteors(
        self,
        fadeAmount: int = None,
        maxSpeed: int = None,
        explode: bool = True,
        meteorCount: int = None,
        collide: bool = None,
        cycleColors: bool = None,
        delayCount: int = None,
    ) -> None:
        """
        Creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail.
        In this version each meteor contains all colors of the colorSequence.

        fadeAmount: the amount by which meteors are faded
        maxSpeed: the amount be which the meteor moves each refresh
        explode: if True, the meteors will light up in an explosion when they collide
        collide:
        cycleColors:
        delayCount:
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMeteors.__name__)

            if fadeAmount is None:
                _fadeAmount = random.randint(20, 40) / 100.0
            else:
                _fadeAmount = float(fadeAmount)

            if explode is None:
                _explode = [True, False][random.randint(0, 1)]
            else:
                _explode = bool(explode)

            if maxSpeed is None:
                _maxSpeed = random.randint(1, 3)
            else:
                _maxSpeed = int(maxSpeed)

            if delayCount is None:
                _delayCount = random.randint(1, 3)
            else:
                _delayCount = int(delayCount)

            if meteorCount is None:
                if self.colorSequenceCount >= 2 and self.colorSequenceCount <= 6:
                    _meteorCount = self.colorSequenceCount
                else:
                    _meteorCount = random.randint(2, 6)
            else:
                _meteorCount = int(meteorCount)

            if collide is None:
                _collide = [True, False][random.randint(0, 1)]
            else:
                _collide = bool(collide)

            if cycleColors is None:
                _cycleColors = random.randint(0, 99) > 50
            else:
                _cycleColors = bool(cycleColors)

            for index in range(_meteorCount):
                meteor = LightFunction(LightFunction.functionMeteors, self.colorSequence)
                # assign meteor color
                meteor.color = self.colorSequenceNext
                # initialize "previous" index, for math's sake later
                meteor.indexPrevious = random.randint(0, self.virtualLEDCount - 1)
                # set the number of LEDs it will move in one step
                meteor.stepSizeMax = _maxSpeed
                # set the maximum number of LEDs it could move in one step
                meteor.step = random.randint(1, max(2, meteor.stepSizeMax))
                # randomly initialize the direction
                meteor.direction = self.getRandomDirection()
                # set the refresh delay
                meteor.delayCountMax = _delayCount
                # randomly assign starting index
                meteor.index = (meteor.index + (meteor.step * meteor.direction)) % self.virtualLEDCount
                # set boolean to cycle each meteor through the color sequence as it moves
                meteor.colorCycle = _cycleColors
                # assign the color sequence
                meteor.colorSequence = np.copy(self.colorSequence)
                self.__LightFunctions.append(meteor)

            # make sure there are at least two going to collide
            if self.__LightFunctions[0].direction * self.__LightFunctions[1].direction > 0:
                self.__LightFunctions[1].direction *= -1

            # make comet trails
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.__LightFunctions.append(fade)

            # this object calculates collisions between other objects based on index and previous/next index
            if _collide == True:
                collision = LightFunction(LightFunction.functionCollisionDetection, self.colorSequence)
                collision.explode = _explode
                self.__LightFunctions.append(collision)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionMeteors.__name__,
                ex,
            )
            raise

    def useFunctionPaint(
        self,
        maxDelay: int = None,
    ) -> None:
        """
        wipes colors in the current sequence across the pixel strand in random directions and amounts
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionPaint.__name__)

            if maxDelay is None:
                _maxDelay = random.randint(2, 10)
            else:
                _maxDelay = int(maxDelay)

            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                paintBrush = LightFunction(LightFunction.functionPaint, self.colorSequence)
                # randomly initialize starting index
                paintBrush.index = random.randint(0, self.virtualLEDCount - 1)
                # randomly initialize the direction
                paintBrush.direction = (-1, 1)[random.randint(0, 1)]
                # set refresh delay
                paintBrush.delayCountMax = _maxDelay
                # set max brush stroke of paintbrush
                paintBrush.stepCountMax = random.randint(2, self.virtualLEDCount * 2)
                # assign the paintbrush a color
                for i in range(random.randint(1, 5)):
                    paintBrush.color = self.colorSequenceNext
                # copy the color sequence
                paintBrush.colorSequence = self.colorSequence
                self.__LightFunctions.append(paintBrush)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionPaint.__name__,
                ex,
            )
            raise

    def useFunctionSprites(
        self,
        fadeSteps: int = None,
    ) -> None:
        """
        Uses colors in the current list to fly meteor style across
        the pixel strand in short bursts of random length and direction.

        fadeSteps:
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionSprites.__name__)
            if fadeSteps is None:
                _fadeSteps = random.randint(1, 6)
            else:
                _fadeSteps = int(fadeSteps)
            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                sprite = LightFunction(LightFunction.functionSprites, self.colorSequence)
                # randomize index
                sprite.index = random.randint(0, self.virtualLEDCount - 1)
                # initialize previous index
                sprite.indexPrevious = sprite.index
                # randomize direction
                sprite.direction = self.getRandomDirection()
                # assign the target color
                sprite.colorGoal = self.colorSequenceNext
                # initialize sprite to
                sprite.color = DEFAULT_BACKGROUND_COLOR.array
                # copy color sequence
                sprite.colorSequence = self.colorSequence
                # set next color
                sprite.colorNext = PixelColors.OFF.array
                # set fade step/amount
                sprite.fadeSteps = _fadeSteps
                sprite.fadeAmount = np.ceil(255 / _fadeSteps)
                self.__LightFunctions.append(sprite)
            # set one sprite to "fading on"
            self.__LightFunctions[0].state = 1
            # add LED fading for comet trails
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = 25 / 255.0
            self.__LightFunctions.append(fade)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionSprites.__name__,
                ex,
            )
            raise

    def useFunctionRaindrops(
        self,
        maxSize: int = None,
        fadeAmount: int = None,
        raindropChance: float = None,
        stepSize: int = None,
        delayCount: int = None,
    ):
        """
        Uses colors in the current list to cause random "splats" across the led strand
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionRaindrops.__name__)

            if maxSize is None:
                _maxSize = random.randint(2, int(self.virtualLEDCount // 8))
            else:
                _maxSize = int(maxSize)

            if fadeAmount is None:
                _fadeAmount = random.randint(50, 100)
            else:
                _fadeAmount = int(fadeAmount)

            if raindropChance is None:
                _raindropChance = random.uniform(0.005, 0.1)
            else:
                _raindropChance = int(raindropChance)

            if stepSize is None:
                _stepSize = random.randint(2, 5)
            else:
                _stepSize = int(stepSize)

            if delayCount is None:
                _delayCount = random.randint(2, 5)
            else:
                _delayCount = int(delayCount)

            if _stepSize > 3:
                _raindropChance /= 3.0

            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                raindrop = LightFunction(LightFunction.functionRaindrops, self.colorSequence)
                # randomize start index
                raindrop.index = random.randint(0, self.virtualLEDCount - 1)
                # assign raindrop growth speed
                raindrop.step = _stepSize
                # max raindrop "splash"
                raindrop.sizeMax = _maxSize
                # max size
                raindrop.stepCountMax = random.randint(2, raindrop.sizeMax)
                # chance of raindrop
                raindrop.activeChance = _raindropChance
                # delay between refreshes to LEDs
                raindrop.delayCountMax = _delayCount
                # assign color
                raindrop.color = self.colorSequenceNext
                raindrop.colorSequence = self.colorSequence
                # raindrop.fadeAmount = int((255 - _fadeAmount) // 255)
                raindrop.fadeAmount = ((255 / raindrop.stepCountMax) / 255) * 2
                # set raindrop to be inactive initially
                raindrop.active = False
                self.__LightFunctions.append(raindrop)
            # set first raindrop active
            self.__LightFunctions[0].state = 1
            # add fading
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = 25 / 255.0
            self.__LightFunctions.append(fade)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionRaindrops.__name__,
                ex,
            )
            raise

    def useOverlayTwinkle(
        self,
        twinkleChance: float = None,
    ) -> None:
        """
        Randomly sets some lights to 'twinkleColor' temporarily

        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useOverlayTwinkle.__name__)

            if twinkleChance is None:
                _twinkleChance = 1 - (random.randint(1, 5) / 1000.0)
            else:
                _twinkleChance = float(twinkleChance)

            twinkle = LightFunction(LightFunction.overlayTwinkle, self.colorSequence)
            twinkle.random = _twinkleChance
            twinkle.colorSequence = self.colorSequence
            self.__LightFunctions.append(twinkle)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useOverlayTwinkle.__name__,
                ex,
            )
            raise

    def useOverlayBlink(
        self,
        blinkChance: float = None,
    ) -> None:
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useOverlayBlink.__name__)
            if blinkChance is None:
                _blinkChance = 1 - (random.randint(1, 5) / 1000.0)
            else:
                _blinkChance = float(blinkChance)

            blink = LightFunction(LightFunction.overlayBlink, self.colorSequence)
            blink.random = _blinkChance
            blink.colorSequence = self.colorSequence
            self.__LightFunctions.append(blink)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useOverlayBlink.__name__,
                ex,
            )
            raise

    def useFunctionAlive(
        self,
        fadeAmount: float = None,
        sizeMax: int = None,
        stepCountMax: int = None,
        stepSizeMax: int = None,
        # delayCountMax: int = None,
    ) -> None:
        """ """
        if fadeAmount is None:
            _fadeAmount = random.randint(20, 50) / 255.0
        else:
            _fadeAmount = float(fadeAmount)

        if sizeMax is None:
            _sizeMax = random.randint(self.virtualLEDCount // 6, self.virtualLEDCount // 3)
        else:
            _sizeMax = int(sizeMax)

        if stepCountMax is None:
            _stepCountMax = random.randint(self.virtualLEDCount // 10, self.virtualLEDCount)
        else:
            _stepCountMax = int(stepCountMax)

        if stepSizeMax is None:
            _stepSizeMax = random.randint(6, 10)
        else:
            _stepSizeMax = int(stepSizeMax)

        # if delayCountMax is None:
        # _delayCountMax = random.randint(10, 25)
        # else:
        # _delayCountMax = int(delayCountMax)

        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionAlive.__name__)
            for i in range(random.randint(2, 5)):
                thing = LightFunction(LightFunction.functionAlive, self.colorSequence)
                # randomize start index
                thing.index = random.randint(0, self.virtualLEDCount - 1)
                # randomize direction
                thing.direction = self.getRandomDirection()
                # copy color sequence
                thing.colorSequence = self.colorSequence
                # assign color
                thing.color = thing.colorSequenceNext
                # set max step count before possible state change
                thing.stepCountMax = _stepCountMax
                # set max step size in normal condition
                thing.stepSizeMax = _stepSizeMax
                # randomize speed
                thing.step = random.randint(1, thing.stepSizeMax)
                # set refresh speed
                thing.delayCountMax = random.randint(6, 15)
                # set initial size
                thing.size = 1
                # set max size
                thing.sizeMax = _sizeMax
                # start the state at 1
                thing.state = 1
                # calculate random next state immediately
                thing.stepCounter = 1000
                thing.delayCounter = 1000
                self.__LightFunctions.append(thing)
            self.__LightFunctions[0].active = True
            # add a fade
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.__LightFunctions.append(fade)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionAlive.__name__,
                ex,
            )
            raise

    def demo(
        self,
        secondsPerMode: int = 20,
    ) -> None:
        """
        do random color sequences and random functions.

        secondsPerMode: how many seconds to run each combination for before switching things up
        """
        try:
            self.secondsPerMode = secondsPerMode
            omitted = [
                LightController.useFunctionNone.__name__,
                LightController.useColorSingle.__name__,
                LightController.useColorSinglePseudoRandom.__name__,
                LightController.useColorSingleRandom.__name__,
                LightController.useOverlayBlink.__name__,
            ]
            attrs = list(dir(self))
            attrs = [a for a in attrs if not a in omitted]
            funcs = [f for f in attrs if f[:11] == "useFunction"]
            colors = [c for c in attrs if c[:8] == "useColor"]
            funcs.sort()
            colors.sort()
            while True:
                funcs_copy = funcs.copy()
                colors_copy = colors.copy()
                try:
                    while len(funcs_copy) > 0 and len(colors_copy) > 0:
                        self.reset()
                        if len(colors_copy) > 1:
                            clr = colors_copy[random.randint(0, len(colors_copy) - 1)]
                        else:
                            clr = colors_copy[0]
                        colors_copy.remove(clr)
                        getattr(self, clr)()
                        if len(funcs_copy) > 1:
                            fnc = funcs_copy[random.randint(0, len(funcs_copy) - 1)]
                        else:
                            fnc = funcs_copy[0]
                        funcs_copy.remove(fnc)
                        getattr(self, fnc)()
                        self.run()
                except Exception as ex:
                    LOGGER.exception(ex)
        except SystemExit:
            pass
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.demo.__name__,
                ex,
            )
            raise

    def test(
        self,
        secondsPerMode: float = 0.5,
        function_names: List[str] = [],
        color_names: List[str] = [],
        skip_functions: List[str] = [],
        skip_colors: List[str] = [],
    ):
        """
        run colors and functions semi-randomly. can use arguments as filters.
        """
        try:
            self.secondsPerMode = secondsPerMode
            attrs = list(dir(self))
            funcs = [f for f in attrs if f[:11] == "useFunction"]
            colors = [c for c in attrs if c[:8] == "useColor"]
            funcs.sort()
            colors.sort()
            if len(function_names) > 0:
                matches = []
                for name in function_names:
                    matches.extend([f for f in funcs if name.lower() in f.lower()])
                funcs = matches
            if len(color_names) > 0:
                matches = []
                for name in color_names:
                    matches.extend([f for f in colors if name.lower() in f.lower()])
                colors = matches
            if len(skip_functions) > 0:
                matches = []
                for name in skip_functions:
                    for f in funcs:
                        if name.lower() in f.lower():
                            funcs.remove(f)
            if len(skip_colors) > 0:
                matches = []
                for name in skip_colors:
                    for c in colors:
                        if name.lower() in c.lower():
                            colors.remove(c)
            if len(funcs) == 0:
                LOGGER.error("No functions selected")
            elif len(colors) == 0:
                LOGGER.error("No colors selected")
            else:
                while (len(funcs) * len(colors)) > 0:
                    if len(funcs) > 0:
                        f = funcs[random.randint(0, len(funcs) - 1)]
                        funcs.remove(f)
                    if len(colors) > 0:
                        c = colors[random.randint(0, len(colors) - 1)]
                        colors.remove(c)
                    # for f in funcs:
                    # for c in colors:
                    self.reset()
                    getattr(self, c)()
                    getattr(self, f)()
                    self.run()
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.test.__name__,
                ex,
            )
            raise
