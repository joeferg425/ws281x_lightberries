"""Class defines methods for interacting with Light Strings, Patterns, and Functions"""
import time
import random
import logging
from typing import (
    Dict,
    List,
    Optional,
    Union,
    Any,
)
from nptyping import NDArray

try:
    from numba import jit  # pylint: disable = unused-import
except ImportError:
    print("install numba for possible speed boost")
import numpy as np
from LightBerries.RpiWS281xPatch import rpi_ws281x
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightStrings import LightString
from LightBerries.LightFunctions import LightFunction
from LightBerries.LightPatterns import (
    SolidColorArray,
    ConvertPixelArrayToNumpyArray,
    RepeatingColorSequenceArray,
    ColorTransitionArray,
    RainbowArray,
    RepeatingRainbowArray,
    ReflectArray,
    DefaultColorSequence,
    DEFAULT_BACKGROUND_COLOR,
)


LOGGER = logging.getLogger("LightBerries")
DEFAULT_REFRESH_DELAY = 50


class LightController:
    """
    This library wraps the rpi_ws281x library and provides some lighting functions.
    see https://github.com/rpi-ws281x/rpi-ws281x-python for questions about that library

    Quick Start:
            1: Create a LightController object specifying ledCount:int, pwmGPIOpin:int,
                channelDMA:int, frequencyPWM:int
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
        ledCount: int = 100,
        pwmGPIOpin: int = 18,
        channelDMA: int = 10,
        frequencyPWM: int = 800000,
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
            if debug is True or verbose is True:
                LOGGER.setLevel(logging.DEBUG)
            if verbose is True:
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

            if verbose is True:
                self.ws28xxLightString.setDebugLevel(5)
            self.privateLEDCount: int = len(self.ws28xxLightString)
            self.virtualLEDArray: NDArray[(3, Any), np.int32] = SolidColorArray(
                arrayLength=self.privateLEDCount,
                color=PixelColors.OFF,
            )
            self.privateOverlayDict: Dict[int, NDArray[(3,), np.int32]] = {}
            self.privateVirtualLEDCount: int = len(self.virtualLEDArray)
            self.virtualLEDIndexArray: NDArray[(Any,), np.int32] = np.array(
                range(len(self.ws28xxLightString))
            )
            self.privateVirtualLEDIndexCount: int = len(self.virtualLEDIndexArray)
            self.privateLastModeChange: float = time.time() - 1000
            self.privateNextModeChange: float = time.time()

            self.privateRefreshDelay: float = 0.001
            self.privateSecondsPerMode: float = 120.0
            self.privateBackgroundColor: NDArray[(3,), np.int32] = PixelColors.OFF.array
            self.privateColorSequence: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([])
            self.privateColorSequenceCount: int = 0
            self.privateColorSequenceIndex: int = 0
            self.privateLoopForever: bool = False
            self.privateLightFunctions: List[LightFunction] = []

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
                self.off()
                self.copyVirtualLedsToWS281X()
                self.refreshLEDs()
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
        """The number of virtual LEDs. These include ones that won't display."""
        return self.privateVirtualLEDCount

    @property
    def realLEDCount(self) -> int:
        """The number of LEDs in the LED string"""
        return self.privateLEDCount

    @property
    def refreshDelay(
        self,
    ) -> float:
        """The delay between starting LED refreshes"""
        return self.privateRefreshDelay

    @refreshDelay.setter
    def refreshDelay(
        self,
        delay: float,
    ) -> None:
        """ """
        self.privateRefreshDelay = float(delay)

    @property
    def backgroundColor(
        self,
    ) -> NDArray[(3,), np.int32]:
        """The defined background, or "Off" color for the LED string"""
        return self.privateBackgroundColor

    @backgroundColor.setter
    def backgroundColor(
        self,
        color: NDArray[(3,), np.int32],
    ) -> None:
        """ """
        self.privateBackgroundColor = Pixel(color).array

    @property
    def secondsPerMode(
        self,
    ) -> float:
        """The number of seconds to run the configuration"""
        return self.privateSecondsPerMode

    @secondsPerMode.setter
    def secondsPerMode(
        self,
        seconds: float,
    ) -> None:
        """ """
        self.privateSecondsPerMode = float(seconds)

    @property
    def colorSequence(
        self,
    ) -> NDArray[(3, Any), np.int32]:
        """The sequence of RGB values to use for generating patterns when using the functions"""
        return self.privateColorSequence

    @colorSequence.setter
    def colorSequence(
        self,
        colorSequence: NDArray[(3, Any), np.int32],
    ) -> None:
        """ """
        self.privateColorSequence = np.copy(ConvertPixelArrayToNumpyArray(colorSequence))
        self.colorSequenceCount = len(self.privateColorSequence)
        self.colorSequenceIndex = 0

    @property
    def colorSequenceCount(
        self,
    ) -> int:
        """The number of colors in the defined sequence"""
        return self.privateColorSequenceCount

    @colorSequenceCount.setter
    def colorSequenceCount(
        self,
        colorSequenceCount: int,
    ) -> None:
        """ """
        self.privateColorSequenceCount = colorSequenceCount

    @property
    def colorSequenceIndex(
        self,
    ) -> int:
        """The index we are on in the current color sequence"""
        return self.privateColorSequenceIndex

    @colorSequenceIndex.setter
    def colorSequenceIndex(
        self,
        colorSequenceIndex: int,
    ) -> None:
        """ """
        self.privateColorSequenceIndex = colorSequenceIndex

    @property
    def colorSequenceNext(
        self,
    ) -> NDArray[(3,), np.int32]:
        """Get the next color in the sequence"""
        temp = self.colorSequence[self.colorSequenceIndex]
        self.colorSequenceIndex += 1
        if self.colorSequenceIndex >= self.colorSequenceCount:
            self.colorSequenceIndex = 0
        if isinstance(temp, Pixel):
            return temp.array
        else:
            return temp

    @property
    def functionList(self) -> List[LightFunction]:
        """The list of function objects that will be used to modify the light pattern"""
        return self.privateLightFunctions

    @property
    def overlayDictionary(self) -> Dict[int, Any]:
        """the list of indices and associated colors to temporarily assign LEDs"""
        return self.privateOverlayDict

    def reset(
        self,
    ) -> None:
        """
        reset class variables to default state
        """
        try:
            self.privateLightFunctions = []
            if self.virtualLEDCount > self.realLEDCount:
                self.setVirtualLEDArray(self.virtualLEDArray[: self.realLEDCount])
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

    def setVirtualLEDArray(
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
                _ledArray = SolidColorArray(arrayLength=self.realLEDCount, color=self.backgroundColor)

            # check assignment length
            if len(_ledArray) >= self.realLEDCount:
                self.virtualLEDArray = _ledArray
            else:
                self.virtualLEDArray[: len(_ledArray)] = _ledArray

            # assign new LED array to virtual LEDs
            self.privateVirtualLEDCount = len(self.virtualLEDArray)
            # set our indices for virtual LEDs
            self.privateVirtualLEDIndexCount = self.privateVirtualLEDCount
            # create array of index values for manipulation if needed
            self.virtualLEDIndexArray = np.array(range(self.privateVirtualLEDIndexCount))
            # if the array is smaller than the actual light strand, make our entire strand addressable
            if self.privateVirtualLEDIndexCount < self.realLEDCount:
                self.privateVirtualLEDIndexCount = self.realLEDCount
                self.virtualLEDIndexArray = np.array(range(self.privateVirtualLEDIndexCount))
                self.virtualLEDArray = np.concatenate(
                    (
                        self.virtualLEDArray,
                        np.array(
                            [PixelColors.OFF.tuple for i in range(self.realLEDCount - self.virtualLEDCount)]
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
                self.setVirtualLEDArray.__name__,
                ex,
            )
            raise

    def copyVirtualLedsToWS281X(
        self,
    ) -> None:
        """
        Sets each Pixel in the rpi_ws281x object to the buffered array value
        """
        try:
            # callback function to do work
            def SetPixel(irgb):
                i = irgb[0]
                rgb = irgb[1]
                if i < self.realLEDCount:
                    self.ws28xxLightString[i] = rgb

            # fast method of calling the callback method on each index of LED array
            list(
                map(
                    SetPixel,
                    enumerate(
                        self.virtualLEDArray[self.virtualLEDIndexArray][
                            np.where(self.virtualLEDIndexArray < self.realLEDCount)
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
                self.copyVirtualLedsToWS281X.__name__,
                ex,
            )
            raise

    def refreshLEDs(
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
                self.refreshLEDs.__name__,
                ex,
            )
            raise

    def off(
        self,
    ) -> None:
        """
        set all Pixels to RGD background color
        """
        try:
            # clear all current values
            self.virtualLEDArray *= 0
            # set to background color
            self.virtualLEDArray[:] += self.backgroundColor
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.off.__name__,
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
            for function in self.privateLightFunctions:
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
            for index, ledValue in self.privateOverlayDict.items():
                self.ws28xxLightString[index] = ledValue
            self.privateOverlayDict = {}
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
            for _ in range(count):
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
        """Get a random one or negative one to determine direction for light functions"""
        return [-1, 1][random.randint(0, 1)]

    def fadeColor(
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
            self.privateLastModeChange = time.time()
            # set a target time to change
            if self.secondsPerMode is None:
                self.privateNextModeChange = self.privateLastModeChange + (random.uniform(30, 120))
            else:
                self.privateNextModeChange = self.privateLastModeChange + (self.secondsPerMode)
            # loop
            while time.time() < self.privateNextModeChange or self.privateLoopForever:
                try:
                    # run the selected functions using LightFunction object callbacks
                    self._runFunctions()
                    # copy the resulting RGB values to the ws28xx LED buffer
                    self.copyVirtualLedsToWS281X()
                    # copy temporary changes (not buffered in this class) to the ws28xx LED buffer
                    self._copyOverlays()
                    # tell the ws28xx controller to transmit the new data
                    self.refreshLEDs()
                except KeyboardInterrupt:
                    raise
                except SystemExit:
                    raise
                except Exception as ex:
                    LOGGER.exception("_Run Loop Error: %s", (str(ex),))
                    raise
            self.privateLastModeChange = time.time()
            if self.secondsPerMode is None:
                self.privateNextModeChange = self.privateLastModeChange + (random.random(30, 120))
            else:
                self.privateNextModeChange = self.privateLastModeChange + (self.secondsPerMode)
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
                _sequence = DefaultColorSequence()
                _foregroundColor = _sequence[random.randint(0, len(_sequence) - 1)]
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
                _colorSequence = DefaultColorSequence()
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
                _sequenceLength = random.randint(self.realLEDCount // 20, self.realLEDCount // 10)
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
                _sequenceLength = random.randint(self.realLEDCount // 20, self.realLEDCount // 10)
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
        Sets the color sequence used by light functions to the sequence given,
        buts repeats it across the entire light string
        If the sequence will not fill perfectly when repeated,
        the virtual LED string is extended until it fits

        colorSequence: list of colors to in the pattern being
        shifted across the LED string
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequenceRepeating.__name__)

            # use argument or default
            if colorSequence is None:
                _colorSequence = DefaultColorSequence()
            else:
                _colorSequence = [Pixel(p) for p in colorSequence]

            # use argument or default
            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            # calculate required virtual LED count to allow for even multiple of this sequence
            _arrayLength = np.ceil(self.realLEDCount / len(_colorSequence)) * len(_colorSequence)

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
        sets the color sequence used by light functions to
        the one specified in the argument, but
        makes a smooth transition from one color to the
        next over the length specified

        colorSequence: list of colors to transition between
            stepsPerTransition:  how many pixels it takes to
            transition from one color to the next
        wrap: if true, the last color of the sequence will
            transition to the first color as the final transition
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransition.__name__)

            # set color sequence
            if colorSequence is None:
                _colorSequence = DefaultColorSequence()
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
                _colorSequence = DefaultColorSequence()
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

            _arrayLength = np.ceil(self.realLEDCount / len(_tempColorSequence)) * len(_tempColorSequence)

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
        Set the entire LED string to a single color, but cycle
        through the colors of the rainbow a bit at a time

        rainbowPixels: when creating the rainbow gradient, make the
        transition through ROYGBIV take this many steps
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbow.__name__)

            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            if rainbowPixelCount is None:
                _rainbowPixelCount = random.randint(10, self.realLEDCount // 2)
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
        Set the entire LED string to a single color, but cycle
        through the colors of the rainbow a bit at a time

        rainbowPixels: when creating the rainbow gradient, make
            the transition through ROYGBIV take this many steps
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbowRepeating.__name__)

            if backgroundColor is None:
                self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            else:
                self.backgroundColor = Pixel(backgroundColor).array

            if rainbowPixelCount is None:
                _rainbowPixelCount = random.randint(10, self.realLEDCount // 2)
            else:
                _rainbowPixelCount = int(rainbowPixelCount)

            _arrayLength = np.ceil(self.realLEDCount / _rainbowPixelCount) * _rainbowPixelCount

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
        """Use the "do nothing" function"""
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionNone.__name__)
            # create an object to put in the light data list so we dont just abort the run
            nothing = LightFunction(LightFunction.functionNone, self.colorSequence)
            self.privateLightFunctions.append(nothing)
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
            self.privateLightFunctions.append(cycle)
            self.virtualLEDArray *= 0
            self.virtualLEDArray += self.colorSequence[0, :]
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
            self.privateLightFunctions.append(off)

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
            self.privateLightFunctions.append(marquee)

            # this function just shifts the existing buffer, so make sure the buffer is initialized here
            self.setVirtualLEDArray(self.colorSequence)
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
            self.privateLightFunctions.append(fade)

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
            self.privateLightFunctions.append(cylon)
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
            if self.colorSequenceCount >= self.realLEDCount:
                # if seqeuence is too long, cut it in half
                self.colorSequence = self.colorSequence[: int(self.colorSequenceCount // 2)]
                # dont remember offhand why this is here
                if self.colorSequenceCount % 2 == 1:
                    if self.colorSequenceCount == 1:
                        self.colorSequence = np.concatenate(self.colorSequence, self.colorSequence)
                    else:
                        self.colorSequence = self.colorSequence[:-1]
            # calculate modulo length
            _arrayLength = np.ceil(self.realLEDCount / self.colorSequenceCount) * self.colorSequenceCount
            # update LED buffer with any changes we had to make
            self.setVirtualLEDArray(
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
            self.privateLightFunctions.append(merge)
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
            self.privateLightFunctions.append(fade)

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
            self.privateLightFunctions.append(accelerate)
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
        Randomly changes pixels on the string to one of the
        provided colors by fading from one color to the next

        changeChance: chance that any one pixel will change
            colors each update (from 0.0, to 1.0)
        fadeStepCount: number of steps in the transition from
            one color to the next
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
                    change.color = np.copy(self.virtualLEDArray[change.index])
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
                    self.privateLightFunctions.append(change)
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
        Creates several 'meteors' from the given color list that will
        fly around the light string leaving a comet trail.
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

            for _ in range(_meteorCount):
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
                self.privateLightFunctions.append(meteor)

            # make sure there are at least two going to collide
            if self.privateLightFunctions[0].direction * self.privateLightFunctions[1].direction > 0:
                self.privateLightFunctions[1].direction *= -1

            # make comet trails
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.privateLightFunctions.append(fade)

            # this object calculates collisions between other objects based on index and previous/next index
            if _collide is True:
                collision = LightFunction(LightFunction.functionCollisionDetection, self.colorSequence)
                collision.explode = _explode
                self.privateLightFunctions.append(collision)
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

            for _ in range(max(min(self.colorSequenceCount, 10), 2)):
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
                for _ in range(random.randint(1, 5)):
                    paintBrush.color = self.colorSequenceNext
                # copy the color sequence
                paintBrush.colorSequence = self.colorSequence
                self.privateLightFunctions.append(paintBrush)
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
            for _ in range(max(min(self.colorSequenceCount, 10), 2)):
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
                self.privateLightFunctions.append(sprite)
            # set one sprite to "fading on"
            self.privateLightFunctions[0].state = 1
            # add LED fading for comet trails
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = 25 / 255.0
            self.privateLightFunctions.append(fade)
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

            for _ in range(max(min(self.colorSequenceCount, 10), 2)):
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
                self.privateLightFunctions.append(raindrop)
            # set first raindrop active
            self.privateLightFunctions[0].state = 1
            # add fading
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = 25 / 255.0
            self.privateLightFunctions.append(fade)
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
            self.privateLightFunctions.append(twinkle)
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
        """Use the overlay that causes all LEDs to light up the same color at once"""
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useOverlayBlink.__name__)
            if blinkChance is None:
                _blinkChance = 1 - (random.randint(1, 5) / 1000.0)
            else:
                _blinkChance = float(blinkChance)

            blink = LightFunction(LightFunction.overlayBlink, self.colorSequence)
            blink.random = _blinkChance
            blink.colorSequence = self.colorSequence
            self.privateLightFunctions.append(blink)
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
        """Use the function that uses a series of behaviors that
        move around in odd ways"""
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
            for _ in range(random.randint(2, 5)):
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
                self.privateLightFunctions.append(thing)
            self.privateLightFunctions[0].active = True
            # add a fade
            fade = LightFunction(LightFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.privateLightFunctions.append(fade)
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
                funcsCopy = funcs.copy()
                colorsCopy = colors.copy()
                try:
                    while len(funcsCopy) > 0 and len(colorsCopy) > 0:
                        self.reset()
                        if len(colorsCopy) > 1:
                            clr = colorsCopy[random.randint(0, len(colorsCopy) - 1)]
                        else:
                            clr = colorsCopy[0]
                        colorsCopy.remove(clr)
                        getattr(self, clr)()
                        if len(funcsCopy) > 1:
                            fnc = funcsCopy[random.randint(0, len(funcsCopy) - 1)]
                        else:
                            fnc = funcsCopy[0]
                        funcsCopy.remove(fnc)
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
        functionNames: List[str] = None,
        colorNames: List[str] = None,
        skipFunctions: List[str] = None,
        skipColors: List[str] = None,
    ):
        """
        run colors and functions semi-randomly. can use arguments as filters.
        """
        try:
            self.secondsPerMode = secondsPerMode
            attrs = list(dir(self))
            functions = [f for f in attrs if f[:11] == "useFunction"]
            colors = [c for c in attrs if c[:8] == "useColor"]
            functions.sort()
            colors.sort()

            if functionNames is None:
                functionNames = []
            if colorNames is None:
                colorNames = []
            if skipFunctions is None:
                skipFunctions = []
            if skipColors is None:
                skipColors = []

            if len(functionNames) > 0:
                matches = []
                for name in functionNames:
                    matches.extend([f for f in functions if name.lower() in f.lower()])
                functions = matches
            if len(colorNames) > 0:
                matches = []
                for name in colorNames:
                    matches.extend([f for f in colors if name.lower() in f.lower()])
                colors = matches
            if len(skipFunctions) > 0:
                matches = []
                for name in skipFunctions:
                    for function in functions:
                        if name.lower() in function.lower():
                            functions.remove(function)
            if len(skipColors) > 0:
                matches = []
                for name in skipColors:
                    for color in colors:
                        if name.lower() in color.lower():
                            colors.remove(color)
            if len(functions) == 0:
                LOGGER.error("No functions selected")
            elif len(colors) == 0:
                LOGGER.error("No colors selected")
            else:
                while (len(functions) * len(colors)) > 0:
                    if len(functions) > 0:
                        function = functions[random.randint(0, len(functions) - 1)]
                        functions.remove(function)
                    if len(colors) > 0:
                        color = colors[random.randint(0, len(colors) - 1)]
                        colors.remove(color)
                    # for f in funcs:
                    # for c in colors:
                    self.reset()
                    getattr(self, color)()
                    getattr(self, function)()
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
