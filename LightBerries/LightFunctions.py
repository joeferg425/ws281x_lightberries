from logging import Logger
from random import randint
import sys
import numpy as np
import time
import random
import logging
import inspect
from typing import Dict, List, Tuple, Optional, Callable, Union, Any
from nptyping import NDArray
from numpy.lib.arraysetops import isin
from LightBerries.rpi_ws281x_patch import rpi_ws281x
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightStrings import LightString
from LightBerries.LightPatterns import (
    PixelArray,
    SolidColorArray,
    ConvertPixelArrayToNumpyArray,
    RepeatingColorSequenceArray,
    ColorTransitionArray,
    RainbowArray,
    RepeatingRainbowArray,
    ReflectArray,
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_COLOR_SEQUENCE,
    DEFAULT_TWINKLE_COLOR,
    get_DEFAULT_COLOR_SEQUENCE,
)
from LightBerries.LightDatas import LightData

# setup logging
LOGGER = logging.getLogger()
logging.addLevelName(5, "VERBOSE")
if not LOGGER.handlers:
    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)
if sys.platform != "linux":
    fh = logging.FileHandler(__name__ + ".log")
else:
    fh = logging.FileHandler("/home/pi/" + __name__ + ".log")
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)

DEFAULT_TWINKLE_CHANCE = 0.0

DEFAULT_REFRESH_DELAY = 50


class LightFunction:
    """
    This library wraps the rpi_ws281x library and provides some lighting functions.
    see https://github.com/rpi-ws281x/rpi-ws281x-python for questions about that library

    Quick Start:
            1: Create a LightFunction object specifying ledCount:int, pwmGPIOpin:int, channelDMA:int, frequencyPWM:int
                    lf = LightFunction(10, 18, 10, 800000)

            2: Choose a color pattern
                    lf.useColorRainbow()

            3: Choose a function
                    lf.functionCylon()

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
    ):
        """
        Create a LightFunction object for running patterns across a rpi_ws281x LED string

        ledCount: int
                the number of Pixels in your string of LEDs
        pwmGPIOpin: int
                the GPIO pin number your lights are hooked up to (18 is a good choice since it does PWM)
        channelDMA: int
                the DMA channel to use (5 is a good option)
        frequencyPWM: int
                try 800,000
        invertSignalPWM: bool
                set true to invert the PWM signal
        ledBrightnessFloat: float
                set to a value between 0.0 (OFF), and 1.0 (ON)
                This setting tends to introduce flicker the lower it is
        channelPWM: int
                defaults to 0, see https://github.com/rpi-ws281x/rpi-ws281x-python
        stripTypeLED:
                see https://github.com/rpi-ws281x/rpi-ws281x-python
        gamma:
                see https://github.com/rpi-ws281x/rpi-ws281x-python
        debug: bool
                set true for some debugging messages
        verbose: bool
                set true for even more information
        """
        try:
            if True == debug or True == verbose:
                LOGGER.setLevel(logging.DEBUG)
            if True == verbose:
                LOGGER.setLevel(5)
            pixelStrip = pixelStrip = rpi_ws281x.PixelStrip(
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
            self._LEDArray = LightString(
                pixelStrip=pixelStrip,
                debug=verbose,
            )

            if True == verbose:
                self._LEDArray.setDebugLevel(5)
            self._LEDCount: int = len(self._LEDArray)
            self._VirtualLEDArray: NDArray = SolidColorArray(
                arrayLength=self._LEDCount, color=PixelColors.OFF
            )
            self._VirtualLEDBuffer: NDArray = np.copy(self._VirtualLEDArray)
            self._VirtualLEDCount: int = len(self._VirtualLEDArray)
            self._VirtualLEDIndexArray: NDArray = np.array(range(len(self._LEDArray)))
            self._VirtualLEDIndexCount: int = len(self._VirtualLEDIndexArray)
            self._LastModeChange = None
            self._NextModeChange: Optional[float] = None
            self._FunctionList: List[Callable] = []
            self._colorFunction: Optional[Dict[str, Any]] = None
            self._overlayColorFunction: Optional[Dict[str, Any]] = None

            self.__refreshDelay: float = 0.001
            self.__secondsPerMode: float = 120.0
            self.__backgroundColor: NDArray = PixelColors.OFF.array
            self.__colorSequence: NDArray = ConvertPixelArrayToNumpyArray([])
            self.__colorSequenceCount: int = 0
            self.__colorSequenceIndex: int = 0
            self.__overlayColorSequence: NDArray = ConvertPixelArrayToNumpyArray([])
            self.__overlayColorSequenceCount: int = 0
            self.__overlayColorSequenceIndex: int = 0

            self._LoopForever: bool = False
            self._OverlayList: List[Tuple[Callable, Callable, Any]] = []
            self._TwinkleChance: float = 0.0
            self._BlinkChance: float = 0.0
            self._BlinkColorList: List[Pixel] = [PixelColors.OFF]
            self._Blink: bool = False
            self._RandomColors: bool = False
            self._ShiftAmount: int = 0
            self._ShiftCount: int = 0
            self._ShiftCounter: int = 0
            self._flipLength: int = 0
            self._RandomChangeChance: float = 0.0
            self._AccelerateIndex: int = 0
            self._AccelerateDirection: int = 0
            self._MeteorCount: int = 0
            self._LightDataObjects: List[LightData] = []
            self._MaxSpeed: int = 0
            self._CycleColors: bool = False
            self._fadeAmount: int = 0
            self._PreviousIndices: np.ndarray = np.array([])

            self.reset()
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

    def __del__(self):
        """
        disposes of the rpi_ws281x object (if it exists) to prevent memory leaks
        """
        try:
            if hasattr(self, "_LEDArray") and not self._LEDArray is None:
                del self._LEDArray
                self._LEDArray = None
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

    @property
    def refreshDelay(self) -> float:
        return self.__refreshDelay

    @refreshDelay.setter
    def refreshDelay(self, delay):
        self.__refreshDelay = float(delay)

    @property
    def backgroundColor(self) -> NDArray:
        return self.__backgroundColor

    @backgroundColor.setter
    def backgroundColor(self, color: Pixel):
        self.__backgroundColor = Pixel(color).array

    @property
    def secondsPerMode(self) -> float:
        return self.__secondsPerMode

    @secondsPerMode.setter
    def secondsPerMode(self, seconds: float):
        self.__secondsPerMode = float(seconds)

    @property
    def colorSequence(self) -> NDArray[(3, Any), np.int32]:
        return self.__colorSequence

    @colorSequence.setter
    def colorSequence(self, colorSequence: List[Pixel]):
        self.__colorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        self.colorSequenceCount = len(self.__colorSequence)
        self.colorSequenceIndex = 0

    @property
    def colorSequenceCount(self) -> int:
        return self.__colorSequenceCount

    @colorSequenceCount.setter
    def colorSequenceCount(self, colorSequenceCount: int):
        self.__colorSequenceCount = colorSequenceCount

    @property
    def colorSequenceIndex(self) -> int:
        return self.__colorSequenceIndex

    @colorSequenceIndex.setter
    def colorSequenceIndex(self, colorSequenceIndex: int):
        self.__colorSequenceIndex = colorSequenceIndex

    @property
    def colorSequenceNext(self):
        if not callable(self.colorSequence):
            temp = self.colorSequence[self.colorSequenceIndex]
            self.colorSequenceIndex += 1
            if self.colorSequenceIndex >= self.colorSequenceCount:
                self.colorSequenceIndex = 0
        else:
            temp = self.colorSequence().array
        return temp

    @property
    def overlayColorSequence(self) -> NDArray[(3, Any), np.int32]:
        return self.__overlayColorSequence

    @overlayColorSequence.setter
    def overlayColorSequence(self, overlayColorSequence: List[Pixel]):
        self.__overlayColorSequence = ConvertPixelArrayToNumpyArray(overlayColorSequence)
        self.overlayColorSequenceCount = len(self.__overlayColorSequence)
        self.overlayColorSequenceIndex = 0

    @property
    def overlayColorSequenceCount(self) -> int:
        return self.__overlayColorSequenceCount

    @overlayColorSequenceCount.setter
    def overlayColorSequenceCount(self, overlayColorSequenceCount: int):
        self.__overlayColorSequenceCount = overlayColorSequenceCount

    @property
    def overlayColorSequenceIndex(self) -> int:
        return self.__overlayColorSequenceIndex

    @overlayColorSequenceIndex.setter
    def overlayColorSequenceIndex(self, overlayColorSequenceIndex: int):
        self.__overlayColorSequenceIndex = overlayColorSequenceIndex

    @property
    def overlayColorSequenceNext(self):
        if not callable(self.overlayColorSequence):
            temp = self.overlayColorSequence[self.overlayColorSequenceIndex]
            self.overlayColorSequenceIndex += 1
            if self.overlayColorSequenceIndex >= self.overlayColorSequenceCount:
                self.overlayColorSequenceIndex = 0
        else:
            temp = self.overlayColorSequence().array
        return temp

    def reset(self):
        """
        reset class variables to default state
        """
        try:
            self._FunctionList = []
            self._OverlayList = []
            self._TwinkleColorList = []
            self._BlinkColorList = []
            self._LightDataObjects = []
            self._TwinkleChance = 0
            self._BlinkChance = 0
            self._colorFunction = None
            self._overlayColorFunction = None
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

    def _initializeFunction(self, refreshDelay, functionPointer, configurationPointer, *args, **kwargs):
        """ """
        try:
            self.refreshDelay = refreshDelay
            self._FunctionList = [(functionPointer, configurationPointer, args, kwargs)]
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

    def _initializeOverlay(self, functionPointer, configurationPointer, *args, **kwargs):
        """ """
        try:
            self._OverlayList = [(functionPointer, configurationPointer, args, kwargs)]
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

    def _setVirtualLEDArray(self, ledArray: Union[List[Pixel], NDArray]) -> None:
        """ """
        try:
            if isinstance(ledArray, list):
                _ledArray = ConvertPixelArrayToNumpyArray(ledArray)
            elif isinstance(ledArray, np.ndarray):
                _ledArray = ledArray
            else:
                _ledArray = SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor)
            if len(_ledArray) > self._LEDCount:
                self._VirtualLEDArray = _ledArray[: self._VirtualLEDCount]
            elif len(_ledArray) < self._LEDCount:
                self._VirtualLEDArray[: len(_ledArray)] = _ledArray
            else:
                self._VirtualLEDArray = _ledArray
            # assign new LED array to virtual LEDs
            self._VirtualLEDBuffer = np.copy(self._VirtualLEDArray)
            self._VirtualLEDCount = len(self._VirtualLEDArray)
            # set our indices for virtual LEDs
            self._VirtualLEDIndexCount = self._VirtualLEDCount
            self._VirtualLEDIndexArray = np.array(range(self._VirtualLEDIndexCount))
            # if the array is smaller than the actual light strand, make our entire strand addressable
            if self._VirtualLEDIndexCount < self._LEDCount:
                self._VirtualLEDIndexCount = self._LEDCount
                self._VirtualLEDIndexArray = np.array(range(self._VirtualLEDIndexCount))
                self._VirtualLEDArray = np.concatenate(
                    (
                        self._VirtualLEDArray,
                        np.array(
                            [
                                PixelColors.OFF.tuple
                                for i in range(self._LEDCount - len(self._VirtualLEDArray))
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
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _copyVirtualLedsToWS281X(self):
        """
        Sets each Pixel in the rpi_ws281x object to the buffered array value
        """
        try:
            # update the WS281X strand using the RGB array and the virtual LED indices
            self._LEDArray[:] = [
                self._VirtualLEDArray[self._VirtualLEDIndexArray[i]] for i in range(self._LEDCount)
            ]
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

    def _refreshLEDs(self):
        """
        Display current LED buffer
        """
        try:
            self._LEDArray.refresh()
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

    def _off(self):
        """
        set buffered Pixel values to off state
        """
        try:
            self._VirtualLEDArray *= 0
            self._VirtualLEDArray[:] += self.backgroundColor
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

    def _runConfigurations(self):
        """
        calling useColor functions saves pointers to them.
        Sometimes a function will modify the configuration for better functionality.
        This function calls the confguration over again with any modifications that were made.
        """
        try:
            for function in self._FunctionList:
                function[1](*function[2], **function[3])
            for function in self._OverlayList:
                function[1](*function[2], **function[3])
            self._colorFunction["function"](
                **{k: v for k, v in self._colorFunction.items() if k != "function"}
            )
            if not self._overlayColorFunction is None:
                self._overlayColorFunction["function"](
                    **{k: v for k, v in self._overlayColorFunction.items() if k != "function"}
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

    def _runFunctions(self):
        """
        Run each function in the configured function list
        """
        try:
            for function in self._FunctionList:
                function[0]()
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

    def _runOverlays(self):
        """
        Run each overlay in the configured list
        """
        try:
            for overlay in self._OverlayList:
                overlay[0]()
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

    def _getRandomIndices(self, getChance: float = 0.1):
        """
        retrieve a random list of Pixel indices
        """
        try:
            maxVal = 1000
            temp = []
            for LEDIndex in range(self._VirtualLEDCount):
                doLight = random.randint(0, maxVal)
                if doLight > maxVal * (1.0 - getChance):
                    temp.append(LEDIndex)
            return temp
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

    def _fade(
        self,
        fadeIndices: List[int] = None,
        fadeAmount: int = None,
        fadeColor: Union[Pixel, NDArray] = None,
    ):
        """
        fade the Pixels
        """
        if fadeIndices is None:
            fadeIndices = [i for i in range(self._VirtualLEDCount)]
        if fadeAmount is None:
            fadeAmount = self._fadeAmount
        if isinstance(fadeColor, Pixel):
            _fadeColor = fadeColor.array
        elif isinstance(fadeColor, np.ndarray):
            _fadeColor = fadeColor
        else:
            _fadeColor = self.backgroundColor
        try:
            [self._fadeLED(i, _fadeColor, fadeAmount) for i in fadeIndices]
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

    def _fadeOff(self, fadeAmount=None, recalc=True):
        """
        Fade all Pixels toward OFF
        """
        if fadeAmount is None:
            fadeAmount = self._fadeAmount
        if recalc == True:
            fadeAmount = (255 - fadeAmount) / 255
        self._VirtualLEDArray[:] = self._VirtualLEDArray * fadeAmount

    def _fadeLED(
        self,
        led_index: int,
        offColor: Optional[NDArray] = None,
        fadeAmount: Optional[int] = None,
    ):
        """
        fade individual pixels
        """
        try:
            if offColor is None:
                _offColor = self.backgroundColor
            else:
                _offColor = offColor
            if fadeAmount is None:
                fadeAmount = self._fadeAmount
            # offColor = Pixel(offColor).array
            self._VirtualLEDArray[led_index] = self._fadeColor(
                self._VirtualLEDArray[led_index], _offColor, fadeAmount
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

    def _fadeColor(
        self,
        color: NDArray,
        offColor: Optional[NDArray] = None,
        fadeAmount: Optional[int] = None,
    ):
        """
        fade pixel colors
        """
        try:
            if offColor is None:
                _offColor = self.backgroundColor
            else:
                _offColor = offColor
            if fadeAmount is None:
                fadeAmount = self._fadeAmount
            # color = Pixel(color).array
            # offColor = Pixel(offColor).array
            for rgbIndex in range(len(color)):
                if color[rgbIndex] != _offColor[rgbIndex]:
                    if color[rgbIndex] - fadeAmount > _offColor[rgbIndex]:
                        color[rgbIndex] -= fadeAmount
                    elif color[rgbIndex] + fadeAmount < _offColor[rgbIndex]:
                        color[rgbIndex] += fadeAmount
                    else:
                        color[rgbIndex] = _offColor[rgbIndex]
            return color
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

    def run(self):
        """
        Run the configured color pattern and function either forever or for self.secondsPerMode
        """
        try:
            LOGGER.info("%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if self._NextModeChange is None:
                self._LastModeChange = time.time()
                if self.secondsPerMode is None:
                    self._NextModeChange = self._LastModeChange + (random.uniform(30, 120))
                else:
                    self._NextModeChange = self._LastModeChange + (self.secondsPerMode)
            self._runConfigurations()
            while time.time() < self._NextModeChange or self._LoopForever:
                try:
                    self._runFunctions()
                    self._copyVirtualLedsToWS281X()
                    self._runOverlays()
                    self._refreshLEDs()
                    time.sleep(self.refreshDelay)
                except KeyboardInterrupt:
                    raise
                except SystemExit:
                    raise
                except Exception as ex:
                    LOGGER.exception("_Run Loop Error: {}".format(ex))
                    raise
            self._LastModeChange = time.time()
            if self.secondsPerMode is None:
                self._NextModeChange = self._LastModeChange + (random.random(30, 120))
            else:
                self._NextModeChange = self._LastModeChange + (self.secondsPerMode)
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

    def useColorSingle(self, foregroundColor: Pixel = None, twinkleColors: bool = False) -> None:
        """
        Sets the the color sequence used by light functions to a single color of your choice

        foregroundColor:Pixel
                the color that each pixel will be set to

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if foregroundColor is None:
                s = get_DEFAULT_COLOR_SEQUENCE()
                foregroundColor = s[random.randint(0, len(s) - 1)]
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray([foregroundColor])
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
                self._colorFunction = {
                    "function": self.useColorSingle,
                    "foregroundColor": self.colorSequence[0],
                }
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray([foregroundColor])
                self._overlayColorFunction = {
                    "function": self.useColorSingle,
                    "foregroundColor": self.colorSequence[0],
                    "twinkleColors": True,
                }
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

    def useColorSinglePseudoRandom(self, twinkleColors: bool = False) -> None:
        """
        Sets the the color sequence used by light functions to a single random named color

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            if twinkleColors == False:
                self.colorSequence = [PixelColors.pseudoRandom()]
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
                self._colorFunction = {"function": self.useColorSinglePseudoRandom}
            elif twinkleColors == True:
                self.overlayColorSequence = [PixelColors.pseudoRandom()]
                self._overlayColorFunction = {
                    "function": self.useColorSinglePseudoRandom,
                    "twinkleColors": True,
                }
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

    def useColorSingleRandom(self, twinkleColors: bool = False) -> None:
        """
        Sets the the color sequence used by light functions to a single random RGB value

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                self.colorSequence = [PixelColors.random()]
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
                self._colorFunction = {"function": self.useColorSingleRandom}
            elif twinkleColors == True:
                self.overlayColorSequence = [PixelColors.random()]
                self._overlayColorFunction = {
                    "function": self.useColorSingleRandom,
                    "twinkleColors": True,
                }
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

    def useColorSequence(
        self,
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the the color sequence used by light functions to one of your choice

        colorSequence:List[Pixel]
                list of colors in the pattern

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
                # for color in self.colorSequence:
                # LOGGER.debug('{}'.format(Pixel(color)))
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorSequence,
                    "colorSequence": self.colorSequence,
                }
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
                self._overlayColorFunction = {
                    "function": self.useColorSequence,
                    "colorSequence": self.colorSequence,
                    "twinkleColors": True,
                }
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def useColorPseudoRandomSequence(self, sequenceLength: int = None, twinkleColors: bool = False) -> None:
        """
        Sets the color sequence used in light functions to a random list of named colors

        sequenceLength:int
                the number of random colors to use in the generated sequence

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if sequenceLength is None:
                sequenceLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
            self.backgroundColor = backgroundColor = PixelColors.OFF
            if twinkleColors == False:
                self.colorSequence = [PixelColors.pseudoRandom() for i in range(sequenceLength)]
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorPseudoRandomSequence,
                    "sequenceLength": sequenceLength,
                }
            elif twinkleColors == True:
                self.overlayColorSequence = [PixelColors.pseudoRandom() for i in range(sequenceLength)]
                self._overlayColorFunction = {
                    "function": self.useColorPseudoRandomSequence,
                    "sequenceLength": sequenceLength,
                    "twinkleColors": True,
                }
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

    def useColorPseudoRandom(self, twinkleColors: bool = False) -> None:
        """
        Sets the color sequence to generate a random named color every time one is needed in a function

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = backgroundColor = PixelColors.OFF
            if twinkleColors == False:
                self.colorSequence = PixelColors.pseudoRandom
                self.colorSequenceCount = random.randint(2, 7)
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
                self._colorFunction = {"function": self.useColorPseudoRandom}
            elif twinkleColors == True:
                self.overlayColorSequence = PixelColors.pseudoRandom
                self.overlayColorSequenceCount = random.randint(2, 7)
                self._overlayColorFunction = {
                    "function": self.useColorPseudoRandom,
                    "twinkleColors": True,
                }
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

    def useColorRandomSequence(self, sequenceLength: int = None, twinkleColors: bool = False) -> None:
        """
        Sets the color sequence used in light functions to a random list of RGB values

        sequenceLength:int
                the number of random colors to use in the generated sequence

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = backgroundColor = PixelColors.OFF
            if twinkleColors == False:
                if sequenceLength is None:
                    sequenceLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
                self.colorSequence = [PixelColors.random() for i in range(sequenceLength)]
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorRandomSequence,
                    "sequenceLength": sequenceLength,
                }
            elif twinkleColors == True:
                if sequenceLength is None:
                    sequenceLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
                self.overlayColorSequence = [PixelColors.random() for i in range(sequenceLength)]
                self._overlayColorFunction = {
                    "function": self.useColorRandomSequence,
                    "sequenceLength": sequenceLength,
                    "twinkleColors": True,
                }
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

    def useColorRandom(self, twinkleColors: bool = False) -> None:
        """
        Sets the color sequence to generate a random RGB value every time one is needed in a function

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                self.colorSequence = PixelColors.random
                self.colorSequenceCount = random.randint(2, 7)
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
                self._colorFunction = {"function": self.useColorRandom}
            elif twinkleColors == True:
                self.overlayColorSequence = PixelColors.random
                self.overlayColorSequenceCount = random.randint(2, 7)
                self._overlayColorFunction = {
                    "function": self.useColorRandom,
                    "twinkleColors": True,
                }
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

    def useColorSequenceRepeating(
        self,
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the color sequence used by light functions to the sequence given, buts repeats it across the entire light string

        If the sequence will not fill perfectly when repeated, the virtual LED string is extended until it fits

        colorSequence:List[Pixel]
                list of colors to in the pattern being shifted across the LED string

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
                self.colorSequence = RepeatingColorSequenceArray(
                    arrayLength=arrayLength, colorSequence=colorSequence
                )
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorSequenceRepeating,
                    "colorSequence": self.colorSequence,
                }
            elif twinkleColors == True:
                arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
                self.overlayColorSequence = RepeatingColorSequenceArray(
                    arrayLength=arrayLength, colorSequence=colorSequence
                )
                self._overlayColorFunction = {
                    "function": self.useColorSequenceRepeating,
                    "colorSequence": self.colorSequence,
                    "twinkleColors": True,
                }
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def useColorTransition(
        self,
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        stepsPerTransition: int = 5,
        wrap: bool = True,
        twinkleColors: bool = False,
    ) -> None:
        """
        sets the color sequence used by light functions to the one specified in the argument, but
        makes a smooth transition from one color to the next over the length specified

        colorSequence:List[Pixel]
                list of colors to transition between

        stepsPerTransition: int
                how many pixels it takes to transition from one color to the next

        wrap: bool
                if true, the last color of the sequence will transition to the first color as the final transition

        twinkleColors:bool
                set to true when assigning these colors to be used in a twinkle overlay

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                self.colorSequence = ColorTransitionArray(
                    arrayLength=len(colorSequence) * int(stepsPerTransition),
                    wrap=False,
                    colorSequence=colorSequence,
                )
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorTransition,
                    "colorSequence": self.colorSequence,
                    "stepsPerTransition": stepsPerTransition,
                    "wrap": wrap,
                }
            elif twinkleColors == True:
                self.overlayColorSequence = ColorTransitionArray(
                    arrayLength=len(colorSequence) * int(stepsPerTransition),
                    wrap=False,
                    colorSequence=colorSequence,
                )
                self._overlayColorFunction = {
                    "function": self.useColorTransition,
                    "colorSequence": self.colorSequence,
                    "stepsPerTransition": stepsPerTransition,
                    "wrap": wrap,
                    "twinkleColors": True,
                }
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

    def useColorTransitionRepeating(
        self,
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        stepsPerTransition: int = 5,
        wrap: bool = True,
        twinkleColors: bool = False,
    ):
        """
        colorSequence:List[Pixel]
                list of colors to in the pattern being shifted across the LED string
        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                colorSequence = ColorTransitionArray(
                    arrayLength=(len(colorSequence) * stepsPerTransition),
                    wrap=wrap,
                    colorSequence=colorSequence,
                )
                arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
                self.colorSequence = RepeatingColorSequenceArray(
                    arrayLength=arrayLength, colorSequence=colorSequence
                )
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorTransitionRepeating,
                    "colorSequence": self.colorSequence,
                    "stepsPerTransition": stepsPerTransition,
                    "wrap": wrap,
                }
            elif twinkleColors == True:
                colorSequence = ColorTransitionArray(
                    arrayLength=(len(colorSequence) * stepsPerTransition),
                    wrap=wrap,
                    colorSequence=colorSequence,
                )
                arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
                self.overlayColorSequence = RepeatingColorSequenceArray(
                    arrayLength=arrayLength, colorSequence=colorSequence
                )
                self._overlayColorFunction = {
                    "function": self.useColorTransitionRepeating,
                    "colorSequence": self.colorSequence,
                    "stepsPerTransition": stepsPerTransition,
                    "wrap": wrap,
                    "twinkleColors": True,
                }
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def useColorRainbow(self, rainbowPixels: int = None, twinkleColors: bool = False):
        """
        Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

        rainbowPixels:int
                when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            pixelCount: int = 0
            if isinstance(rainbowPixels, int):
                pixelCount = rainbowPixels
            else:
                pixelCount = random.randint(10, self._LEDCount // 2)
            if twinkleColors == False:
                self.colorSequence = RainbowArray(arrayLength=pixelCount)
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
                self._colorFunction = {
                    "function": self.useColorRainbow,
                    "rainbowPixels": rainbowPixels,
                }
            elif twinkleColors == True:
                self.overlayColorSequence = RainbowArray(arrayLength=pixelCount)
                self._overlayColorFunction = {
                    "function": self.useColorRainbow,
                    "rainbowPixels": rainbowPixels,
                    "twinkleColors": True,
                }
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

    def useColorRainbowRepeating(self, rainbowPixels: int = None, twinkleColors: bool = False):
        """
        Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

        rainbowPixels:int
                when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            pixelCount: int = 0
            if isinstance(rainbowPixels, int):
                pixelCount = rainbowPixels
            else:
                rainbowPixels = random.randint(10, self._LEDCount // 2)
            if twinkleColors == False:
                arrayLength = np.ceil(self._LEDCount / pixelCount) * pixelCount
                self.colorSequence = RepeatingRainbowArray(arrayLength=arrayLength, segmentLength=pixelCount)
                self.__colorSequenceCount = pixelCount
                if self.colorSequence.shape[0] < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(self.colorSequence)
                self._colorFunction = {
                    "function": self.useColorRainbowRepeating,
                    "rainbowPixels": pixelCount,
                }
            elif twinkleColors == True:
                colorSequence = RainbowArray(arrayLength=pixelCount)
                arrayLength = np.ceil(self._LEDCount / pixelCount) * pixelCount
                self.overlayColorSequence = RepeatingRainbowArray(
                    arrayLength=arrayLength, segmentLength=pixelCount
                )
                self._overlayColorFunction = {
                    "function": self.useColorRainbowRepeating,
                    "rainbowPixels": pixelCount,
                    "twinkleColors": True,
                }
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

    def functionNone(self, refreshDelay: float = None):
        """
        Set all Pixels to the same color

        refreshDelay: float
                delay between color updates
                in this function it is only relevant if there is an overlay active

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._None_Function,
                configurationPointer=self._None_Configuration,
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

    def _None_Configuration(self):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._setVirtualLEDArray(
                SolidColorArray(arrayLength=self._LEDCount, color=self.colorSequenceNext)
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _None_Function(self):
        """
        do nothing
        """
        try:
            pass
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def functionSolidColorCycle(self, refreshDelay: float = None):
        """
        Set all LEDs to a single color at once, but cycle between entries in a list of colors

        refreshDelay: float
                delay between color updates

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) * 5
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._SolidColorCycle_Function,
                configurationPointer=self._SolidColorCycle_Configuration,
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

    def _SolidColorCycle_Configuration(self):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._setVirtualLEDArray(
                SolidColorArray(arrayLength=self._LEDCount, color=self.colorSequenceNext)
            )
            if self.colorSequenceCount < 2:
                self._NextModeChange = time.time()
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

    def _SolidColorCycle_Function(self):
        """
        set all pixels to the next color
        """
        try:
            self._VirtualLEDArray *= 0
            self._VirtualLEDArray += self.colorSequenceNext
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

    def functionMarquee(self, refreshDelay: float = None, shiftAmount: int = None):
        """
        Shifts a color pattern across the LED string marquee style.
        Uses the provided sequence of colors.

        refreshDelay: float
                delay between color updates

        shiftAmount: int
                the number of pixels the marquee shifts on each update

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
            if shiftAmount is None:
                shiftAmount = random.randint(1, 5)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Marquee_Function,
                configurationPointer=self._Marquee_Configuration,
                shiftAmount=shiftAmount,
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _Marquee_Configuration(self, shiftAmount: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._ShiftAmount = shiftAmount
            # colorSequence = []
            self._LightDataObjects = []
            direction = [-1, 1][random.randint(0, 1)]
            for i in range(self.colorSequenceCount):
                marqueePixel = LightData(self.colorSequenceNext)
                marqueePixel.step = shiftAmount
                marqueePixel.direction = direction
                marqueePixel.index = i
                self._LightDataObjects.append(marqueePixel)
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

    def _Marquee_Function(self):
        """ """
        try:
            self._off()
            for marqueePixel in self._LightDataObjects:
                marqueePixel.index = (
                    marqueePixel.index + (marqueePixel.direction * marqueePixel.step)
                ) % self._VirtualLEDCount
                self._VirtualLEDArray[marqueePixel.index] = marqueePixel.color
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

    def functionAlternate(self, refreshDelay: float = None, shiftAmount: int = None):
        """
        Shift a color pattern across the Pixel string marquee style and then bounce back.

        refreshDelay: float
                delay between color updates

        shiftAmount: int
                each time the pattern shifts, shift it by this many LEDs

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 35
            if shiftAmount is None:
                shiftAmount = random.randint(1, 5)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Alternate_Function,
                configurationPointer=self._Alternate_Configuration,
                shiftAmount=shiftAmount,
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _Alternate_Configuration(self, shiftAmount: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._LightDataObjects = []
            for i in range(self.colorSequenceCount):
                alternator = LightData(self.colorSequenceNext)
                alternator.index = i
                alternator.step = shiftAmount
                alternator.direction = 1
                self._LightDataObjects.append(alternator)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _Alternate_Function(self):
        """ """
        try:
            self._off()
            for alternator in self._LightDataObjects:
                self._VirtualLEDArray[alternator.index] = alternator.color
                if (
                    alternator.index + (alternator.direction * alternator.step) >= self._VirtualLEDCount
                    or alternator.index + (alternator.direction * alternator.step) < 0
                ):
                    alternator.stepCounter = 0
                    alternator.direction = alternator.direction * -1
                else:
                    alternator.stepCounter += 1
                alternator.index += alternator.direction * alternator.step
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def functionCylon(self, refreshDelay: float = None, fadeAmount: int = None):
        """
        Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        refreshDelay: float
                delay between color updates

        fadeAmount: int
                how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10
            if fadeAmount is None:
                fadeAmount = random.randint(35, 55)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Cylon_Function,
                configurationPointer=self._Cylon_Configuration,
                fadeAmount=fadeAmount,
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

    def _Cylon_Configuration(self, fadeAmount: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._LightDataObjects = []
            for index in range(self.colorSequenceCount):
                color = self.colorSequenceNext
                eye = LightData(color)
                eye.index = index
                eye.step = 3
                eye.direction = 1
                eye.fadeAmount = fadeAmount
                self._LightDataObjects.append(eye)
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

    def _Cylon_Function(self):
        """ """
        try:
            self._fadeOff(fadeAmount=self._LightDataObjects[0].fadeAmount)
            for eye in self._LightDataObjects:
                last_index = eye.index
                next_index = eye.index + (eye.direction * eye.step)
                if next_index >= self._VirtualLEDCount:
                    next_index = self._VirtualLEDCount - 1
                    eye.direction = -1
                elif next_index < 0:
                    next_index = 1
                    eye.direction = 1
                eye.index = next_index
                for i in np.linspace(last_index, next_index, abs(last_index - next_index) + 1, dtype=int):
                    self._VirtualLEDArray[i] = eye.color
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

    def functionMerge(
        self,
        refreshDelay: float = None,
        mergeSegmentLength: int = None,
        shiftAmount: int = None,
    ):
        """
        Reflect a color sequence and shift the reflections toward each other in the middle

        refreshDelay: float
                delay between color updates

        mergeSegmentLength: int
                length of reflected segments

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = random.uniform(0.0, 0.05)
            if shiftAmount is None:
                shiftAmount = random.randint(1, 6)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Merge_Function,
                configurationPointer=self._Merge_Configuration,
                mergeSegmentLength=mergeSegmentLength,
                shiftAmount=shiftAmount,
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _Merge_Configuration(self, mergeSegmentLength: int, shiftAmount: int):
        """
        splits the array into sections and shifts each section in the opposite direction

        mergeSegmentLength: int
                the length of the segments to split the array into
        """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if mergeSegmentLength is None:
                if not self.__colorSequenceCount is None:
                    mergeSegmentLength = self.__colorSequenceCount
                else:
                    mergeSegmentLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
            self._MergeLength = int(mergeSegmentLength)
            self._ShiftAmount = int(shiftAmount)
            arrayLength = np.ceil(self._LEDCount / self._MergeLength) * self._MergeLength
            colorSequence = []
            if self.colorSequenceCount >= self._LEDCount:
                self.colorSequenceCount = self.colorSequenceCount // 2
            for i in range(self.colorSequenceCount):
                colorSequence.append(self.colorSequenceNext)
            self._setVirtualLEDArray(
                ReflectArray(
                    arrayLength=arrayLength,
                    colorSequence=colorSequence,
                    foldLength=self.colorSequenceCount,
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
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _Merge_Function(self):
        """ """
        try:
            # this takes
            # [0,1,2,3,4,5]
            # and creates
            # [[0,1,2]
            #  [3,4,5]]
            # out of it
            segmentCount = int(self._VirtualLEDIndexCount // self._MergeLength)
            temp = np.reshape(self._VirtualLEDIndexArray, (segmentCount, self._MergeLength))
            # now i can roll each row in a different direction and then undo
            # the matrixification of the array
            if temp[0][0] != temp[1][-1]:
                temp[1] = np.flip(temp[0])
                self._VirtualLEDArray[range(self._MergeLength)] = self.colorSequence[range(self._MergeLength)]
            temp[0] = np.roll(temp[0], self._ShiftAmount, 0)
            temp[1] = np.roll(temp[1], -self._ShiftAmount, 0)
            for i in range(self._VirtualLEDIndexCount // self._MergeLength):
                if i % 2 == 0:
                    temp[i] = temp[0]
                else:
                    temp[i] = temp[1]
            # turn the matrix back into an array
            self._VirtualLEDIndexArray = np.reshape(temp, (self._VirtualLEDIndexCount))
            # for i in range(self._VirtualLEDCount):
            # self._VirtualLEDArray[i] = self._VirtualLEDArray[self._VirtualLEDIndexArray[i]]
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

    def functionAccelerate(self, beginDelay: float = None, endDelay: float = None):
        """
        Shifts a color pattern across the LED string marquee style, but accelerates as it goes.
        Uses the provided sequence of colors.

        beginDelay: float
                initial delay between color updates
        endDelay: float
                final delay between color updates
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if beginDelay is None:
                beginDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
            if endDelay is None:
                endDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10000
            self._initializeFunction(
                refreshDelay=beginDelay,
                functionPointer=self._Accelerate_Function,
                configurationPointer=self._Accelerate_Configuration,
                shiftAmount=1,
                beginDelay=beginDelay,
                endDelay=endDelay,
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

    def _Accelerate_Configuration(self, shiftAmount: int, beginDelay: float, endDelay: float):
        """
        incrementally decreases the amount of self.refreshDelay between each shift
        for 'delaySteps' then maintains 'endDelay'

        shiftAmount: int
                the amount to shift each time

        beginDelay: float
                the number of seconds to delay at the beginning

        endDelay: float
                the number of seconds to delay at the end
        """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            delaySteps = self._VirtualLEDCount // 2
            self._ShiftAmount = 1
            self._BeginDelay = beginDelay
            self._EndDelay = endDelay
            self._DelaySteps = delaySteps
            self._DelayRange = (
                np.log(np.linspace(np.e, 1, self._DelaySteps)) * (self._BeginDelay - self._EndDelay)
                + self._EndDelay
            )
            if self._DelaySteps < self._VirtualLEDIndexCount:
                self._DelayRange = np.concatenate(
                    (
                        self._DelayRange,
                        np.ones(self._VirtualLEDIndexCount - self._DelaySteps) * self._EndDelay,
                    )
                )
            self._AccelerateIndex = 0
            self._AccelerateDirection = 1
            self._LightDataObjects = []
            direction = [-1, 1][random.randint(0, 1)]
            for i in range(self.colorSequenceCount):
                marqueePixel = LightData(self.colorSequenceNext)
                marqueePixel.step = shiftAmount
                marqueePixel.direction = direction
                marqueePixel.index = i
                self._LightDataObjects.append(marqueePixel)
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

    def _Accelerate_Function(self):
        """ """
        try:
            self._off()
            for marqueePixel in self._LightDataObjects:
                if (self._AccelerateIndex / self._DelaySteps) >= 0.8:
                    marqueePixel.step = 3
                elif (self._AccelerateIndex / self._DelaySteps) >= 0.6:
                    marqueePixel.step = 2
                else:
                    marqueePixel.step = 1

                marqueePixel.index = (
                    marqueePixel.index + (marqueePixel.direction * marqueePixel.step)
                ) % self._VirtualLEDCount
                self._VirtualLEDArray[marqueePixel.index] = marqueePixel.color
            if self._AccelerateDirection > 0:
                self._AccelerateIndex += 1
            else:
                self._AccelerateIndex -= 1

            if self._AccelerateIndex >= (len(self._DelayRange) - 1) or self._AccelerateIndex <= 0:
                if self._AccelerateDirection < 0 and random.randint(0, 10) > 8:
                    self._ShiftAmount *= -1
                self._AccelerateDirection *= -1
            self.refreshDelay = self._DelayRange[self._AccelerateIndex]
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

    def functionRandomChange(self, refreshDelay: float = None, changeChance: float = None):
        """
        Randomly changes pixels on the string to one of the provided colors

        refreshDelay: float
                delay between color updates

        changeChance: float
                chance that any one pixel will change colors each update (from 0.0, to 1.0)

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
            if changeChance is None:
                changeChance = random.uniform(0.005, 0.05)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._RandomChange_Function,
                configurationPointer=self._RandomChange_Configuration,
                changeChance=changeChance,
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

    def _RandomChange_Configuration(self, changeChance: float):
        """

        changeChance: float
                a floating point number specifying the chance of
                modifying any given LED's value
        """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._RandomChangeChance = changeChance
            if self.colorSequenceCount < 2:
                self._NextModeChange = time.time()
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

    def _RandomChange_Function(self):
        """ """
        try:
            maxVal = 1000
            for LEDIndex in range(self._VirtualLEDIndexCount):
                doLight = random.randint(0, maxVal)
                if doLight > maxVal * (1.0 - self._RandomChangeChance):
                    self._VirtualLEDArray[LEDIndex] = self.colorSequenceNext
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

    def functionRandomFadeChange(
        self,
        refreshDelay: float = None,
        changeChance: float = None,
        fadeStepCount: int = None,
    ):
        """
        Randomly changes pixels on the string to one of the provided colors by fading from one color to the next

        refreshDelay: float
                delay between color updates

        changeChance: float
                chance that any one pixel will change colors each update (from 0.0, to 1.0)

        fadeStepCount: int
                number of steps in the transition from one color to the next

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
            if changeChance is None:
                changeChance = random.uniform(0.1, 0.3)
            if fadeStepCount is None:
                fadeStepCount = random.randint(20, 50)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._RandomFadeChange_Function,
                configurationPointer=self._RandomFadeChange_Configuration,
                fadeInChance=changeChance,
                fadeStepCount=fadeStepCount,
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

    def _RandomFadeChange_Configuration(self, fadeInChance: float, fadeStepCount: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._fadeChance = fadeInChance
            self._fadeStepCount = fadeStepCount
            self._fadeAmount = 255 // self._fadeStepCount
            self._fadeStepCounter = 0
            _PreviousIndices = []
            indices = self._getRandomIndices(self._fadeChance)
            self._LightDataObjects = []
            for index in indices:
                _PreviousIndices.append(index)
                randomfade = LightData(self.colorSequenceNext)
                randomfade.index = index
                randomfade.fadeAmount = self._fadeAmount
                randomfade.stepCountMax = self._fadeStepCount
                self._LightDataObjects.append(randomfade)
            self._PreviousIndices = np.array(_PreviousIndices)
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

    def _RandomFadeChange_Function(self):
        """ """
        try:
            for randomFade in self._LightDataObjects:
                self._fadeLED(
                    led_index=randomFade.index,
                    offColor=randomFade.color,
                    fadeAmount=randomFade.fadeAmount,
                )
                randomFade.stepCounter += 1
                if randomFade.stepCounter >= randomFade.stepCountMax:
                    randomFadeIndices = np.array(self._getRandomIndices(self._fadeChance))
                    x = np.intersect1d(self._PreviousIndices, randomFadeIndices)
                    randomFadeIndices = [i for i in randomFadeIndices if not i in x]
                    defaultIndices = np.array(self._getRandomIndices(self._fadeChance))
                    x = np.intersect1d(self._PreviousIndices, defaultIndices)
                    defaultIndices = [i for i in defaultIndices if not i in x]
                    x = np.intersect1d(randomFadeIndices, defaultIndices)
                    defaultIndices = [i for i in defaultIndices if not i in x]
                    self._PreviousIndices = []
                    self._LightDataObjects = []
                    for index in randomFadeIndices:
                        if index < self._VirtualLEDCount:
                            self._PreviousIndices.append(index)
                            randomfade = LightData(self.colorSequenceNext)
                            randomfade.index = index
                            randomfade.fadeAmount = self._fadeAmount
                            randomfade.stepCountMax = self._fadeStepCount
                            self._LightDataObjects.append(randomfade)
                    for index in defaultIndices:
                        if index < self._VirtualLEDCount:
                            randomfade = LightData(self.backgroundColor)
                            randomfade.index = index
                            randomfade.fadeAmount = self._fadeAmount
                            randomfade.stepCountMax = self._fadeStepCount
                            self._LightDataObjects.append(randomfade)
                    self._PreviousIndices = np.array(self._PreviousIndices)
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

    def functionMeteors(
        self,
        refreshDelay: float = None,
        fadeStepCount: int = None,
        maxSpeed: int = None,
    ):
        """
        creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail

        refreshDelay: float
                delay between color updates

        fadeStepCount: int
                this is the length of the meteor trail

        maxSpeed: int
                the amount be which the meteor moves each refresh

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
            if fadeStepCount is None:
                fadeStepCount = random.randint(3, 10)
            if maxSpeed is None:
                maxSpeed = random.randint(1, 5)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Meteors_Function,
                configurationPointer=self._Meteors_Configuration,
                fadeStepCount=fadeStepCount,
                maxSpeed=maxSpeed,
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

    def _Meteors_Configuration(self, fadeStepCount: int, maxSpeed: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._LightDataObjects = []
            rnge = [i for i in range(-maxSpeed, maxSpeed + 1)]
            for index in range(min(self.colorSequenceCount, 4)):
                meteor = LightData(self.colorSequenceNext)
                meteor.index = random.randint(0, self._VirtualLEDIndexCount - 1)
                meteor.fadeAmount = np.ceil(255 / fadeStepCount)
                meteor.step = rnge[random.randint(0, len(rnge) - 1)]
                meteor.active = True
                meteor.dying = False
                while meteor.step == 0:
                    meteor.step = rnge[random.randint(0, len(rnge) - 1)]
                meteor.stepCountMax = random.randint(2, self._VirtualLEDIndexCount - 1)
                self._LightDataObjects.append(meteor)
            self._fadeAmount = int(255 / fadeStepCount)
            self._MaxSpeed = maxSpeed
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

    def _Meteors_Function(self):
        """ """
        try:
            oldLocation = 0
            newLocation = 0
            newLocationx = 0
            rnge = [i for i in range(-self._MaxSpeed, self._MaxSpeed + 1)]
            self._fadeOff(fadeAmount=self._LightDataObjects[0].fadeAmount)
            for meteor in self._LightDataObjects:
                if meteor.alive:
                    oldLocation = meteor.index
                    newLocationx = meteor.index + meteor.step
                    newLocation = (meteor.index + meteor.step) % self._VirtualLEDIndexCount
                    meteor.index = newLocation
                    if meteor.dying:
                        meteor.color = self._fadeColor(meteor.color, self.backgroundColor, 15)
                        if sum(meteor.color) == 0:
                            meteor.alive = False
                else:
                    if random.randint(0, 99) > 95:
                        meteor.stepCounter = 0
                        meteor.step = rnge[random.randint(0, len(rnge) - 1)]
                        while meteor.step == 0:
                            meteor.step = rnge[random.randint(0, len(rnge) - 1)]
                        meteor.stepCountMax = random.randint(2, self._VirtualLEDIndexCount * 2)
                        meteor.color = self.colorSequenceNext
                        meteor.index = random.randint(0, self._VirtualLEDIndexCount - 1)
                        meteor.alive = True
                        meteor.dying = False
                        oldLocation = meteor.index
                        newLocationx = meteor.index + meteor.step
                        newLocation = (meteor.index + meteor.step) % self._VirtualLEDIndexCount
                if meteor.alive:
                    meteor.stepCounter += 1
                    rng = range(oldLocation, newLocationx + 1)
                    for i in rng:
                        i = i % self._VirtualLEDCount
                        self._VirtualLEDArray[i] = meteor.color
                    if meteor.stepCounter >= meteor.stepCountMax:
                        meteor.dying = True
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

    def functionMeteorsFancy(
        self,
        refreshDelay: float = None,
        fadeAmount: int = None,
        maxSpeed: int = None,
        cycleColors: bool = None,
        meteorCount: int = None,
    ):
        """
        Creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail.
        In this version each meteor contains all colors of the colorSequence.

        refreshDelay: float
                delay between color updates

        fadeAmount: int
                the amount by which meteors are faded

        maxSpeed: int
                the amount be which the meteor moves each refresh

        cycleColors: bool
                if True, the meteors transition through the color sequence as they travel

        meteorCount: int
                the number of meteors flying around

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
            if cycleColors is None:
                cycleColors = random.randint(0, 99) > 50
            if meteorCount is None:
                meteorCount = random.randint(2, 5)
            if fadeAmount is None:
                fadeAmount = random.randint(50, 90)
            if maxSpeed is None:
                maxSpeed = random.randint(1, 5)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._MeteorsFancy_Function,
                configurationPointer=self._MeteorsFancy_Configuration,
                meteorCount=meteorCount,
                maxSpeed=maxSpeed,
                fadeAmount=fadeAmount,
                cycleColors=cycleColors,
                randomColorCount=None,
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

    def _MeteorsFancy_Configuration(
        self,
        meteorCount: int,
        maxSpeed: int,
        fadeAmount: int,
        cycleColors: bool,
        randomColorCount: int,
    ):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._MeteorCount = meteorCount
            self._fadeAmount = fadeAmount
            self._CycleColors = cycleColors
            self._MaxSpeed = maxSpeed
            for i in range(self._MeteorCount):
                colorSequence = ConvertPixelArrayToNumpyArray(
                    [self.colorSequenceNext for i in range(self.colorSequenceCount)]
                )
                meteor = LightData(colorSequence[::-1])
                meteor.index = random.randint(0, self._VirtualLEDCount - 1)
                meteor.step = (-maxSpeed, maxSpeed)[random.randint(0, 1)]
                meteor.direction = [-1, 1][random.randint(0, 1)]
                meteor.stepCountMax = random.randint(2, self._VirtualLEDCount * 2)
                self._LightDataObjects.append(meteor)
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

    def _MeteorsFancy_Function(self):
        """ """
        try:
            self._fadeOff()
            for meteor in self._LightDataObjects:
                oldIndex = meteor.index
                newIndex = meteor.index + meteor.step
                meteor.index = (meteor.index + meteor.step) % self._VirtualLEDCount
                meteor.stepCounter += 1
                if meteor.stepCounter >= meteor.stepCountMax:
                    meteor.stepCounter = 0
                    meteor.step = (-self._MaxSpeed, self._MaxSpeed)[random.randint(0, 1)]
                    meteor.stepCountMax = random.randint(2, self._VirtualLEDCount * 2)
                    colorSequence = ConvertPixelArrayToNumpyArray(
                        [self.colorSequenceNext for i in range(self.colorSequenceCount)]
                    )
                    meteor.colors = colorSequence[::-1]
                if not self._CycleColors:
                    for idx_clr in range(0, len(meteor.colors)):
                        x1 = meteor.index + meteor.direction * (idx_clr + meteor.step)
                        x2 = meteor.index + meteor.direction * idx_clr
                        mi = min(x1, x2)
                        ma = max(x1, x2)
                        for idx_pixel in range(mi, ma):
                            idx_pixel = idx_pixel % self._VirtualLEDCount
                            self._VirtualLEDArray[idx_pixel] = meteor.colors[idx_clr]
                else:
                    for idx_clr in range(0, len(meteor.colors)):
                        x1 = meteor.index + meteor.direction * (idx_clr + meteor.step)
                        x2 = meteor.index + meteor.direction * idx_clr
                        mi = min(x1, x2)
                        ma = max(x1, x2)
                        for idx_pixel in range(mi, ma):
                            idx_pixel = idx_pixel % self._VirtualLEDCount
                            self._VirtualLEDArray[idx_pixel] = meteor.colors[
                                (meteor.colorIndex + idx_clr) % len(meteor.colors)
                            ]
                if self._CycleColors:
                    meteor.colorIndex = (meteor.colorIndex + (meteor.direction * meteor.step)) % len(
                        meteor.colors
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

    def functionMeteorsBouncy(
        self,
        refreshDelay: float = None,
        fadeAmount: int = 80,
        maxSpeed: int = 1,
        explode: bool = True,
    ):
        """
        Creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail.
        In this version each meteor contains all colors of the colorSequence.

        refreshDelay: float
                delay between color updates

        fadeAmount: int
                the amount by which meteors are faded

        maxSpeed: int
                the amount be which the meteor moves each refresh

        explode: bool
                if True, the meteors will light up in an explosion when they collide

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 10
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._MeteorsBouncy_Function,
                configurationPointer=self._MeteorsBouncy_Configuration,
                fadeAmount=fadeAmount,
                maxSpeed=maxSpeed,
                explode=explode,
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

    def _MeteorsBouncy_Configuration(self, fadeAmount: int, maxSpeed: int, explode: bool):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._fadeAmount = fadeAmount
            self._Explode = explode
            otherSpeeds = []
            self._LightDataObjects = []
            for index in range(max(min(self.colorSequenceCount, 4), 2)):
                meteor = LightData(self.colorSequenceNext)
                meteor.index = random.randint(0, self._VirtualLEDCount - 1)
                meteor.previousIndex = meteor.index
                meteor.step = (-maxSpeed, maxSpeed)[random.randint(0, 1)]
                while abs(meteor.step) in otherSpeeds:
                    if meteor.step > 0:
                        meteor.step += 1
                    else:
                        meteor.step -= 1
                otherSpeeds.append(abs(meteor.step))
                self._LightDataObjects.append(meteor)
            # make sure there are at least two going to collide
            if self._LightDataObjects[0].step * self._LightDataObjects[1].step > 0:
                self._LightDataObjects[1].step *= -1
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

    def _MeteorsBouncy_Function(self):
        """ """
        try:
            self._fadeOff()
            # move the meteors
            for meteor in self._LightDataObjects:
                # calculate next index
                oldIndex = meteor.index
                newIndex = meteor.index + meteor.step
                newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
                # save previous index
                meteor.previousIndex = meteor.index
                # assign new index
                meteor.index = newLocation
                # positive step
                if meteor.previousIndex < meteor.index:
                    # wrap around LED string
                    if abs(meteor.previousIndex - meteor.index) > abs(meteor.step) + 1:
                        meteor.moveRange = [
                            r % self._VirtualLEDCount
                            for r in range(
                                meteor.index,
                                meteor.previousIndex + self._VirtualLEDCount + 1,
                            )
                        ]
                    # not wrapping around
                    else:
                        meteor.moveRange = range(meteor.previousIndex, meteor.index + 1)
                # negative step
                else:
                    # wrap around LED string
                    if abs(meteor.previousIndex - meteor.index) > abs(meteor.step) + 1:
                        meteor.moveRange = [
                            r % self._VirtualLEDCount
                            for r in range(
                                meteor.previousIndex,
                                meteor.index + self._VirtualLEDCount + 1,
                            )
                        ]
                    # not wrapping around
                    else:
                        meteor.moveRange = range(meteor.index, meteor.previousIndex + 1)
                if meteor.index > self._VirtualLEDCount:
                    meteor.index = self._VirtualLEDCount
            # detect collision of self._LightDataObjects
            foundBounce = False
            if len(self._LightDataObjects) > 1:
                for index1, meteor1 in enumerate(self._LightDataObjects):
                    if index1 + 1 < len(self._LightDataObjects):
                        for index2, meteor2 in enumerate(self._LightDataObjects[index1 + 1 :]):
                            # this detects the intersection of two self._LightDataObjects' movements across LEDs
                            if (
                                len(list(set(meteor1.moveRange) & set(meteor2.moveRange))) > 0
                                and random.randint(0, 1000) > 200
                            ):
                                meteor1.bounce = meteor2
                                meteor1.oldStep = meteor1.step
                                meteor2.bounce = meteor1
                                meteor2.oldStep = meteor2.step
                                foundBounce = True
            # handle collision of self._LightDataObjects
            explosions = []
            if foundBounce == True:
                for index, meteor in enumerate(self._LightDataObjects):
                    if meteor.bounce:
                        previous = int(meteor.step)
                        meteor.step = meteor.bounce.oldStep * -1
                        newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
                        meteor.index = newLocation + random.randint(0, 3)
                        meteor.previousIndex = newLocation
                        if random.randint(0, 1000) > 800:
                            meteor.color = self.colorSequenceNext
                        meteor.bounce = False
                        if self._Explode:
                            middle = meteor.moveRange[len(meteor.moveRange) // 2]
                            r = self._LEDCount // 20
                            for i in range(r):
                                explosions.append(
                                    (
                                        (middle - i) % self._VirtualLEDCount,
                                        Pixel(PixelColors.YELLOW).array * (r - i) / r,
                                    )
                                )
                                explosions.append(
                                    (
                                        (middle + i) % self._VirtualLEDCount,
                                        Pixel(PixelColors.YELLOW).array * (r - i) / r,
                                    )
                                )
            for index, meteor in enumerate(self._LightDataObjects):
                try:
                    if meteor.index > self._VirtualLEDCount - 1:
                        meteor.index = meteor.index % (self._VirtualLEDCount)
                    for i in meteor.moveRange:
                        self._VirtualLEDArray[i] = meteor.color
                except:
                    raise
            if self._Explode and len(explosions) > 0:
                for x in explosions:
                    self._VirtualLEDArray[x[0]] = x[1]
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

    def functionMeteorsAgain(self, refreshDelay: float = None, maxDelay: int = 5, fadeSteps: int = 10):
        """
        These meteors can go slower than the others

        refreshDelay: float
                delay between color updates
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 1000
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._MeteorsAgain_Function,
                configurationPointer=self._MeteorsAgain_Configuration,
                maxDelay=maxDelay,
                fadeSteps=fadeSteps,
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

    def _MeteorsAgain_Configuration(self, maxDelay: int, fadeSteps: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._MaxDelay = maxDelay
            self._fadeSteps = fadeSteps
            self._fadeAmount = np.ceil(255 / fadeSteps)
            self._LightDataObjects = []
            for index in range(max(min(self.colorSequenceCount, 5), 2)):
                meteor = LightData(self.colorSequenceNext)
                meteor.index = random.randint(0, self._VirtualLEDCount - 1)
                meteor.direction = (-1, 1)[random.randint(0, 1)]
                meteor.step = (-1, 1)[random.randint(0, 1)]
                meteor.delayCountMax = random.randint(0, maxDelay)
                meteor.stepCountMax = random.randint(2, self._VirtualLEDCount * 6)
                meteor.colorSequenceIndex = index
                self._LightDataObjects.append(meteor)
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

    def _MeteorsAgain_Function(self):
        """ """
        try:
            for meteor in self._LightDataObjects:
                meteor.delayCounter += 1
                if meteor.delayCounter >= meteor.delayCountMax:
                    meteor.delayCounter = 0
                    newLocation = (meteor.index + meteor.step) % self._VirtualLEDCount
                    meteor.index = newLocation
                    meteor.stepCounter += 1
                    if meteor.stepCounter >= meteor.stepCountMax:
                        meteor.stepCounter = 0
                        meteor.step = (-1, 1)[random.randint(0, 1)]
                        meteor.delayCountMax = random.randint(0, self._MaxDelay)
                        meteor.stepCountMax = random.randint(self._VirtualLEDCount, self._VirtualLEDCount * 4)
            self._fadeOff()
            for meteor in self._LightDataObjects:
                self._VirtualLEDArray[meteor.index] = meteor.color
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

    def functionPaint(self, refreshDelay: float = None, maxDelay: int = None):
        """
        wipes colors in the current sequence across the pixel strand in random directions and amounts

        refreshDelay: float
                delay between color updates

        returns: None
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 1000
            if maxDelay is None:
                maxDelay = random.randint(2, 10)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Paint_Function,
                configurationPointer=self._Paint_Configuration,
                maxDelay=maxDelay,
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

    def _Paint_Configuration(self, maxDelay: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._MaxDelay = maxDelay
            self._LightDataObjects = []
            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                paintBrush = LightData(self.colorSequenceNext)
                paintBrush.index = random.randint(0, self._VirtualLEDCount - 1)
                paintBrush.step = (-1, 1)[random.randint(0, 1)]
                paintBrush.delayCountMax = random.randint(min(0, self._MaxDelay), max(0, self._MaxDelay))
                paintBrush.stepCountMax = random.randint(2, self._VirtualLEDCount * 2)
                paintBrush.colorSequenceIndex = i
                self._LightDataObjects.append(paintBrush)
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

    def _Paint_Function(self):
        """ """
        try:
            for paintBrush in self._LightDataObjects:
                paintBrush.delayCounter += 1
                if paintBrush.delayCounter >= paintBrush.delayCountMax:
                    paintBrush.delayCounter = 0
                    newLocation = (paintBrush.index + paintBrush.step) % self._VirtualLEDCount
                    paintBrush.index = newLocation
                    paintBrush.stepCounter += 1
                    if paintBrush.stepCounter >= paintBrush.stepCountMax:
                        paintBrush.stepCounter = 0
                        paintBrush.step = (-1, 1)[random.randint(-1, 1)]
                        paintBrush.delayCountMax = random.randint(0, self._MaxDelay)
                        paintBrush.stepCountMax = random.randint(2, self._VirtualLEDCount * 2)
                        if paintBrush.random:
                            paintBrush.color = self.colorSequenceNext
                self._VirtualLEDArray[paintBrush.index] = paintBrush.color
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

    def functionSprites(self, refreshDelay: float = None, fadeSteps: int = None):
        """
        Uses colors in the current list to fly meteor style across
        the pixel strand in short bursts of random length and direction.

        refreshDelay: float
                delay between color updates

        fadeSteps: int
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 20
            if fadeSteps is None:
                fadeSteps = random.randint(1, 6)
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Sprites_Function,
                configurationPointer=self._Sprites_Configuration,
                fadeSteps=fadeSteps,
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

    def _Sprites_Configuration(self, fadeSteps: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._fadeSteps = fadeSteps
            self._fadeAmount = np.ceil(255 / fadeSteps)
            self._LightDataObjects = []
            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                sprite = LightData(self.colorSequenceNext)
                sprite.active = False
                sprite.dying = False
                sprite.index = random.randint(0, self._VirtualLEDCount - 1)
                sprite.lastindex = sprite.index
                sprite.direction = [-1, 1][random.randint(0, 1)]
                sprite.colorSequenceIndex = i
                self._LightDataObjects.append(sprite)
            self._LightDataObjects[0].active = True
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

    def _Sprites_Function(self):
        """ """
        try:
            self._fadeOff()
            for sprite in self._LightDataObjects:
                if sprite.active:
                    if not sprite.dying:
                        sprite.dying = random.randint(6, self._VirtualLEDCount // 2) < sprite.duration
                    # if sprite.active:
                    sprite.lastindex = sprite.index
                    step_size = random.randint(1, 3) * sprite.direction
                    mi = min(sprite.index, sprite.index + step_size)
                    ma = max(sprite.index, sprite.index + step_size)
                    first = True
                    if sprite.direction > 0:
                        for index in range(mi + 1, ma + 1):
                            index = index % self._VirtualLEDCount
                            sprite.index = index
                            self._VirtualLEDArray[sprite.index] = sprite.color
                            if not first:
                                self._fadeLED(index, self.backgroundColor, self._fadeAmount)
                            first - False
                    else:
                        for index in range(ma - 1, mi - 1, -1):
                            index = index % self._VirtualLEDCount
                            sprite.index = index
                            self._VirtualLEDArray[sprite.index] = sprite.color
                            if not first:
                                self._fadeLED(index, self.backgroundColor, self._fadeAmount)
                            first - False
                    if sprite.dying:
                        sprite.color = self._fadeColor(sprite.color, PixelColors.OFF, 25)
                    sprite.duration += 1
                    if sum(sprite.color) == 0:
                        sprite.active = False
                    # else:
                    # sprite.active = False
                else:
                    if random.randint(0, 999) > 800:
                        next_sprite = random.randint(0, (len(self._LightDataObjects) - 1))
                        sprite = self._LightDataObjects[next_sprite]
                        sprite.active = True
                        sprite.duration = 0
                        sprite.direction = [-1, 1][random.randint(0, 1)]
                        sprite.index = random.randint(0, self._VirtualLEDCount - 1)
                        sprite.lastindex = sprite.index
                        sprite.color = self.colorSequenceNext
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

    def functionRaindrops(
        self,
        refreshDelay: float = None,
        maxSize: int = None,
        fadeAmount: int = None,
        raindropChance: float = None,
        stepSize: int = None,
    ):
        """
        Uses colors in the current list to cause random "splats" across the led strand
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = 0
            if maxSize is None:
                maxSize = random.randint(2, int(self._VirtualLEDCount // 8))
            if fadeAmount is None:
                fadeAmount = random.randint(50, 100)
            if raindropChance is None:
                raindropChance = random.uniform(0.005, 0.1)
            if stepSize is None:
                stepSize = random.randint(1, 5)
                if stepSize > 3:
                    raindropChance /= 3
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._Raindrops_Function,
                configurationPointer=self._Raindrops_Configuration,
                fadeAmount=fadeAmount,
                maxSize=maxSize,
                raindropChance=raindropChance,
                stepSize=stepSize,
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

    def _Raindrops_Configuration(self, fadeAmount: int, maxSize: int, raindropChance: float, stepSize: int):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._fadeAmount = int((255 - fadeAmount) // 255)
            self._LightDataObjects = []
            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                raindrop = LightData(self.colorSequenceNext)
                raindrop.sizeMax = maxSize
                raindrop.index = random.randint(0, self._VirtualLEDCount - 1)
                raindrop.stepCountMax = random.randint(2, raindrop.sizeMax)
                raindrop.step = stepSize
                raindrop.fadeAmount = ((255 / raindrop.stepCountMax) / 255) * 2
                raindrop.active = False
                raindrop.activeChance = raindropChance
                self._LightDataObjects.append(raindrop)
            self._LightDataObjects[0].active = True
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

    def _Raindrops_Function(self):
        """ """
        try:
            self._fadeOff(self._fadeAmount, False)
            for raindrop in self._LightDataObjects:
                if not raindrop.active:
                    chance = random.randint(0, 1000) / 1000
                    if chance < raindrop.activeChance:
                        raindrop.active = True
                        raindrop.stepCountMax = random.randint(2, raindrop.sizeMax)
                        raindrop.fadeAmount = ((255 / raindrop.stepCountMax) / 255) * 2
                        raindrop.colorScaler = (
                            raindrop.stepCountMax - raindrop.stepCounter
                        ) / raindrop.stepCountMax
                if raindrop.active:
                    if raindrop.stepCounter < raindrop.stepCountMax:
                        s1 = max(raindrop.index - raindrop.stepCounter - raindrop.step, 0)
                        s2 = max(raindrop.index - raindrop.stepCounter, 0)
                        e1 = min(raindrop.index + raindrop.stepCounter, self._VirtualLEDCount)
                        e2 = min(
                            raindrop.index + raindrop.stepCounter + raindrop.step,
                            self._VirtualLEDCount,
                        )
                        # self._VirtualLEDArray[(raindrop.index + raindrop.stepCounter) % self._VirtualLEDCount] = raindrop.color
                        # self._VirtualLEDArray[(raindrop.index - raindrop.stepCounter) % self._VirtualLEDCount] = raindrop.color
                        if (s2 - s1) > 0:
                            self._VirtualLEDArray[s1:s2] = [raindrop.color] * (s2 - s1)
                        if (e2 - e1) > 0:
                            self._VirtualLEDArray[e1:e2] = [raindrop.color] * (e2 - e1)
                        raindrop.color[:] = raindrop.color * raindrop.colorScaler
                        # p = Pixel(raindrop.color)
                        raindrop.stepCounter += raindrop.step
                    else:
                        raindrop.index = random.randint(0, self._VirtualLEDCount - 1)
                        raindrop.stepCounter = 0
                        raindrop.color = self.colorSequenceNext.copy()
                        raindrop.active = False
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

    def functionTwinkle(self, refreshDelay: float = None, twinkleChance: float = 0.02):
        """
        Randomly sets some lights to 'twinkleColor' temporarily

        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._None_Function,
                configurationPointer=self._None_Configuration,
            )
            self._initializeOverlay(
                functionPointer=self._Twinkle_Overlay,
                configurationPointer=self._Twinkle_Configuration,
                twinkleChance=twinkleChance,
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

    def _Twinkle_Configuration(self, twinkleChance: float):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._TwinkleChance = float(twinkleChance)
            if isinstance(self._colorFunction, dict):
                self._overlayColorFunction = {k: v for k, v in self._colorFunction.items()}
                self._overlayColorFunction["twinkleColors"] = True
            else:
                # TODO: make this exception useful
                raise Exception("")
            self.useColorSingle(PixelColors.OFF)
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

    def _Twinkle_Overlay(self):
        """ """
        try:
            maxVal = 1000
            if self._TwinkleChance > 0.0:
                for LEDIndex in range(self._LEDCount):
                    doLight = random.randint(0, maxVal)
                    if doLight > maxVal * (1.0 - self._TwinkleChance):
                        self._LEDArray[LEDIndex] = self.overlayColorSequenceNext
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

    def functionBlink(self, refreshDelay: float = None, blinkChance: float = 0.02):
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._None_Function,
                configurationPointer=self._None_Configuration,
            )
            self._initializeOverlay(
                functionPointer=self._Blink_Overlay,
                configurationPointer=self._Blink_Configuration,
                blinkChance=blinkChance,
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

    def _Blink_Configuration(self, blinkChance: float):
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._BlinkChance = float(blinkChance)
            if isinstance(self._colorFunction, dict):
                self._overlayColorFunction = {k: v for k, v in self._colorFunction.items()}
                self._overlayColorFunction["twinkleColors"] = True
            else:
                # TODO: make this exception useful
                raise Exception("")
            self.useColorSingle(PixelColors.OFF)
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

    def _Blink_Overlay(self):
        """
        Randomly sets some lights to 'twinkleColor' without changing
        the _VirtualLEDArray buffer

        Parameters:
                twinkleChance: float
                        chance of of any LED being set to 'twinkleColor'

                twinkleColor: tuple(int,int,int)
                        the RGB color tuple to be used as the twinkle color
        """
        try:
            self._Blink = not self._Blink
            if self._Blink and self._BlinkChance > 0.0:
                for i in range(self.overlayColorSequenceCount):
                    color = self.overlayColorSequenceNext
                    maxVal = 1000
                    doBlink = random.randint(0, maxVal)
                    if doBlink > maxVal * (1.0 - self._BlinkChance):
                        for LEDIndex in range(self._LEDCount):
                            self._LEDArray[LEDIndex] = color
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

    def functionItsAlive(self, refreshDelay: float = None):
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
            self._initializeFunction(
                refreshDelay=refreshDelay,
                functionPointer=self._itsAlive_Function,
                configurationPointer=self._itsAlive_Configuration,
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

    def _itsAlive_Configuration(self):
        """ """
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
            self._LightDataObjects = []
            for i in range(1):
                thing = LightData(self.colorSequenceNext.copy())
                thing.index = random.randint(0, self._VirtualLEDCount - 1)
                thing.stepCountMax = random.randint(self._VirtualLEDCount // 10, self._VirtualLEDCount)
                thing.fadeAmount = 255 / thing.stepCountMax
                thing.sizeMax = self._VirtualLEDCount // 3
                thing.size = 1
                thing.fadeAmount = random.randint(80, 192)
                thing.direction = [-1, 1][random.randint(0, 1)]
                thing.step = random.randint(1, 3)
                thing.state = 1
                thing.delayCountMax = random.randint(6, 15)
                self._LightDataObjects.append(thing)
            self._LightDataObjects[0].active = True
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

    def _itsAlive_Function(self):
        """ """
        METEOR = 0x1
        LIGHTSPEED = 0x2
        TURTLE = 0x4
        functions = [
            METEOR,
            LIGHTSPEED,
            TURTLE,
        ]
        GROW = 0x10
        SHRINK = 0x20
        modifications = [
            0,
            GROW,
            SHRINK,
        ]
        CYCLE = 0x100
        color_modifications = [
            0,
            CYCLE,
        ]

        SHORT_PERIOD = 10

        try:
            self._fadeOff(self._LightDataObjects[0].fadeAmount)
            for thing in self._LightDataObjects:
                thing.lastindex = thing.index
                if thing.stepCounter < thing.stepCountMax:
                    if thing.state & METEOR:
                        newLocation = (
                            thing.index + (thing.step * thing.direction)
                        ) % self._VirtualLEDIndexCount
                        thing.index = newLocation
                    if thing.state & LIGHTSPEED:
                        if thing.stepCountMax > SHORT_PERIOD:
                            thing.stepCountMax = SHORT_PERIOD
                        thing.step = 15
                        thing.index = (thing.index + (thing.step * thing.direction)) % self._VirtualLEDCount
                        if random.randint(0, 99) > 95:
                            thing.direction *= -1
                    if thing.state & TURTLE:
                        thing.step = 0
                        if thing.delayCounter > thing.delayCountMax:
                            thing.delayCounter = 0
                            thing.step = 1
                            if random.randint(0, 99) > 80:
                                thing.direction *= -1
                        thing.delayCounter += 1
                        thing.index = (thing.index + (thing.step * thing.direction)) % self._VirtualLEDCount
                    if thing.state & GROW:
                        if thing.stepCountMax > SHORT_PERIOD:
                            thing.stepCountMax = SHORT_PERIOD
                        if thing.size < thing.sizeMax:
                            if random.randint(0, 99) > 80:
                                thing.size += random.randint(1, 5)
                            elif thing.size > 2:
                                if random.randint(0, 99) > 90:
                                    thing.size -= 1
                        if thing.size > thing.sizeMax:
                            thing.size = thing.sizeMax
                        elif thing.size < 1:
                            thing.size = 1
                    if thing.state & SHRINK:
                        if thing.stepCountMax > SHORT_PERIOD:
                            thing.stepCountMax = SHORT_PERIOD
                        if thing.size > 0:
                            if random.randint(0, 99) > 80:
                                thing.size -= random.randint(1, 5)
                            elif thing.size < thing.sizeMax:
                                if random.randint(0, 99) > 90:
                                    thing.size += 1
                        if thing.size > thing.sizeMax:
                            thing.size = thing.sizeMax
                        elif thing.size < 1:
                            thing.size = 1
                    if thing.state & CYCLE:
                        if thing.stepCountMax > SHORT_PERIOD:
                            thing.stepCountMax = SHORT_PERIOD
                        if random.randint(0, 99) > 90:
                            thing.color = self.colorSequenceNext
                    x1 = thing.lastindex - (thing.size * thing.direction)
                    x2 = thing.lastindex + ((thing.step + thing.size) * thing.direction)
                    _x1 = min(x1, x2)
                    _x2 = max(x1, x2)
                    for i in range(_x1, _x2 + 1):
                        idx = i % self._VirtualLEDCount
                        self._VirtualLEDArray[idx] = thing.color
                    thing.stepCounter += 1
                else:
                    thing.state = (
                        functions[random.randint(0, len(functions) - 1)]
                        + modifications[random.randint(0, len(modifications) - 1)]
                        + color_modifications[random.randint(0, len(color_modifications) - 1)]
                    )
                    thing.stepCounter = 0
                    if thing.state == 0:
                        thing.stepCountMax = random.randint(
                            self._VirtualLEDCount // 10, self._VirtualLEDCount
                        )
                        thing.delayCountMax = random.randint(6, 15)
                        if random.randint(0, 99) > 75:
                            thing.direction *= -1
                        thing.step = random.randint(1, 3)
                        thing.fadeAmount = random.randint(80, 192)
                        thing.color = self.colorSequenceNext.copy()
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

    def demo(self, secondsPerMode=20):
        try:
            self.secondsPerMode = secondsPerMode
            omitted = [
                LightFunction.functionNone.__name__,
                LightFunction.useColorSingle.__name__,
                LightFunction.useColorSinglePseudoRandom.__name__,
                LightFunction.useColorSingleRandom.__name__,
                LightFunction.functionBlink.__name__,
            ]
            attrs = list(dir(self))
            attrs = [a for a in attrs if not a in omitted]
            funcs = [f for f in attrs if f[:8] == "function"]
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
                        c = self._colorFunction.copy()
                        c.pop("function")
                        self._colorFunction["function"](**c)
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
                inspect.stack()[0][3],
                ex,
            )
            raise

    def test(
        self,
        secondsPerMode=0.5,
        function_names=[],
        color_names=[],
        skip_functions=[],
        skip_colors=[],
    ):
        try:
            self.secondsPerMode = secondsPerMode
            attrs = list(dir(self))
            funcs = [f for f in attrs if f[:8] == "function"]
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
                    for f in colors:
                        if name.lower() in f.lower():
                            colors.remove(f)
            for f in funcs:
                for c in colors:
                    self.reset()
                    getattr(self, c)()
                    getattr(self, f)()
                    self.run()
        except SystemExit:
            pass
        except KeyboardInterrupt:
            pass
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise
