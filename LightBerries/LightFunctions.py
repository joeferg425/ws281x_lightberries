from logging import Logger
from random import randint
import sys
import numpy as np
import time
import random
import logging

try:
    from numba import jit
except:
    print("install numba for possible speed boost")
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
    ) -> None:
        """
        Create a LightFunction object for running patterns across a rpi_ws281x LED string

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
            self._LEDArray: Optional[LightString] = LightString(
                pixelStrip=pixelStrip,
                debug=verbose,
            )

            if True == verbose:
                self._LEDArray.setDebugLevel(5)
            self._LEDCount: int = len(self._LEDArray)
            self._VirtualLEDArray: NDArray = SolidColorArray(
                arrayLength=self._LEDCount,
                color=PixelColors.OFF,
            )
            self._VirtualLEDBuffer: NDArray = np.copy(self._VirtualLEDArray)
            self._VirtualLEDCount: int = len(self._VirtualLEDArray)
            self._VirtualLEDIndexArray: NDArray = np.array(range(len(self._LEDArray)))
            self._VirtualLEDIndexCount: int = len(self._VirtualLEDIndexArray)
            self._LastModeChange: float = time.time() - 1000
            self._NextModeChange: float = time.time()

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
            self._LightDataObjects: List[LightData] = []
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
                "__init__",
                ex,
            )
            raise

    def __del__(self) -> None:
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
                self.__del__.__name__,
                ex,
            )
            raise

    @property
    def refreshDelay(self) -> float:
        return self.__refreshDelay

    @refreshDelay.setter
    def refreshDelay(self, delay: float):
        self.__refreshDelay = float(delay)

    @property
    def backgroundColor(self) -> NDArray[(3,), np.int32]:
        return self.__backgroundColor

    @backgroundColor.setter
    def backgroundColor(self, color: NDArray[(3,), np.int32]):
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
    def colorSequence(self, colorSequence: NDArray[(3, Any), np.int32]):
        self.__colorSequence = np.copy(ConvertPixelArrayToNumpyArray(colorSequence))
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
    def colorSequenceNext(self) -> NDArray[(3,), np.int32]:
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
    def overlayColorSequence(self) -> NDArray[(3, Any), np.int32]:
        return self.__overlayColorSequence

    @overlayColorSequence.setter
    def overlayColorSequence(self, overlayColorSequence: NDArray[(3, Any), np.int32]):
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
    def overlayColorSequenceNext(self) -> NDArray[(3,), np.int32]:
        if not callable(self.overlayColorSequence):
            temp = self.overlayColorSequence[self.overlayColorSequenceIndex]
            self.overlayColorSequenceIndex += 1
            if self.overlayColorSequenceIndex >= self.overlayColorSequenceCount:
                self.overlayColorSequenceIndex = 0
        else:
            temp = self.overlayColorSequence().array
        return temp

    def reset(self) -> None:
        """
        reset class variables to default state
        """
        try:
            self._LightDataObjects = []
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

    def _initializeFunction(
        self, refreshDelay, functionPointer, configurationPointer, *args, **kwargs
    ) -> None:
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
                self._initializeFunction.__name__,
                ex,
            )
            raise

    def _initializeOverlay(self, functionPointer, configurationPointer, *args, **kwargs) -> None:
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
                self._initializeOverlay.__name__,
                ex,
            )
            raise

    def _setVirtualLEDArray(
        self,
        ledArray: Union[List[Pixel], NDArray],
    ) -> None:
        """ """
        try:
            if isinstance(ledArray, list):
                _ledArray = ConvertPixelArrayToNumpyArray(ledArray)
            elif isinstance(ledArray, np.ndarray):
                _ledArray = ledArray
            else:
                _ledArray = SolidColorArray(arrayLength=self._LEDCount, color=self.backgroundColor)
            if len(_ledArray) >= self._LEDCount:
                self._VirtualLEDArray = _ledArray
            else:
                self._VirtualLEDArray[: len(_ledArray)] = _ledArray
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
                self._setVirtualLEDArray.__name__,
                ex,
            )
            raise

    def _copyVirtualLedsToWS281X(self) -> None:
        """
        Sets each Pixel in the rpi_ws281x object to the buffered array value
        """
        try:
            # update the WS281X strand using the RGB array and the virtual LED indices
            def set_pixel(irgb):
                i = irgb[0]
                rgb = irgb[1]
                self._LEDArray[i] = rgb

            list(
                map(
                    set_pixel,
                    enumerate(self._VirtualLEDArray[self._VirtualLEDIndexArray]),
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

    def _refreshLEDs(self) -> None:
        """
        Display current LED buffer
        """
        try:
            if self._LEDArray is not None:
                self._LEDArray.refresh()
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
        off: LightData,
    ) -> None:
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
                self._off.__name__,
                ex,
            )
            raise

    def _runFunctions(self) -> None:
        """
        Run each function in the configured function list
        """
        try:
            for lData in self._LightDataObjects:
                lData.runFunction(lData)
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

    def _getRandomIndex(self) -> int:
        """
        retrieve a random Pixel index
        """
        try:
            return random.randint(0, (self._VirtualLEDCount - 1))
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._getRandomIndices.__name__,
                ex,
            )
            raise

    def _getRandomIndices(
        self,
        getChance: float = 0.1,
    ) -> List[int]:
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
                self._getRandomIndices.__name__,
                ex,
            )
            raise

    def _fadeOff(
        self,
        fade: LightData,
    ) -> None:
        """
        Fade all Pixels toward OFF
        """
        self._VirtualLEDArray[:] = self._VirtualLEDArray * (1 - fade.fadeAmount)

    def _fadeLight(
        self,
        fadeLED: LightData,
    ) -> None:
        """
        fade pixel colors
        """
        try:
            if fadeLED.delayCounter >= fadeLED.delayCountMax:
                fadeLED.delayCounter = 0
                for rgbIndex in range(len(fadeLED.color)):
                    if fadeLED.color[rgbIndex] != fadeLED.colorNext[rgbIndex]:
                        if fadeLED.color[rgbIndex] - fadeLED.colorFade > fadeLED.colorNext[rgbIndex]:
                            fadeLED.color[rgbIndex] -= fadeLED.colorFade
                        elif fadeLED.color[rgbIndex] + fadeLED.colorFade < fadeLED.colorNext[rgbIndex]:
                            fadeLED.color[rgbIndex] += fadeLED.colorFade
                        else:
                            fadeLED.color[rgbIndex] = fadeLED.colorNext[rgbIndex]
            fadeLED.delayCounter += 1
            self._VirtualLEDArray[fadeLED.index] = np.copy(fadeLED.color)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._fadeLight.__name__,
                ex,
            )
            raise

    def _fadeColor(
        self, color: NDArray[(3,), np.int32], colorNext: NDArray[(3,), np.int32], fadeCount: int
    ) -> NDArray[(3,), np.int32]:
        _color = np.copy(color)
        for rgbIndex in range(len(_color)):
            if _color[rgbIndex] != colorNext[rgbIndex]:
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
            self._LastModeChange = time.time()
            if self.secondsPerMode is None:
                self._NextModeChange = self._LastModeChange + (random.uniform(30, 120))
            else:
                self._NextModeChange = self._LastModeChange + (self.secondsPerMode)
            while time.time() < self._NextModeChange or self._LoopForever:
                try:
                    self._runFunctions()
                    self._copyVirtualLedsToWS281X()
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
                self.run.__name__,
                ex,
            )
            raise

    def useColorSingle(
        self,
        foregroundColor: Pixel = None,
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the the color sequence used by light functions to a single color of your choice

        foregroundColor: the color that each pixel will be set to
        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay

        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSingle.__name__)
            if foregroundColor is None:
                s = get_DEFAULT_COLOR_SEQUENCE()
                foregroundColor = s[random.randint(0, len(s) - 1)]
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray([foregroundColor])
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray([foregroundColor])
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
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the the color sequence used by light functions to a single random named color

        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSinglePseudoRandom)
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR.array
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.pseudoRandom()])
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray([PixelColors.pseudoRandom()])
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
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the the color sequence used by light functions to a single random RGB value

        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSingleRandom.__name__)
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.random()])
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray([PixelColors.random()])
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
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the the color sequence used by light functions to one of your choice

        colorSequence: list of colors in the pattern
        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequence.__name__)
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
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

    def useColorPseudoRandomSequence(
        self,
        sequenceLength: int = None,
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the color sequence used in light functions to a random list of named colors

        sequenceLength: the number of random colors to use in the generated sequence
        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorPseudoRandomSequence.__name__)
            if sequenceLength is None:
                sequenceLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
            self.backgroundColor = backgroundColor = PixelColors.OFF.array
            if twinkleColors == False:
                self.colorSequence = ConvertPixelArrayToNumpyArray(
                    [PixelColors.pseudoRandom() for i in range(sequenceLength)]
                )
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
            elif twinkleColors == True:
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray(
                    [PixelColors.pseudoRandom() for i in range(sequenceLength)]
                )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorPseudoRandomSequence.__name__,
                ex,
            )
            raise

    def useColorPseudoRandom(
        self,
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the color sequence to generate a random named color every time one is needed in a function

        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorPseudoRandom.__name__)
            self.backgroundColor = PixelColors.OFF.array
            if twinkleColors == False:
                colorSequenceCount = random.randint(2, 7)
                colorSequence = []
                for i in range(colorSequenceCount):
                    colorSequence.append(PixelColors.pseudoRandom())
                self.colorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
                self._setVirtualLEDArray(PixelArray(self._LEDCount))
            elif twinkleColors == True:
                colorSequenceCount = random.randint(2, 7)
                colorSequence = []
                for i in range(colorSequenceCount):
                    colorSequence.append(PixelColors.pseudoRandom())
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorPseudoRandom.__name__,
                ex,
            )
            raise

    def useColorRandomSequence(
        self,
        sequenceLength: int = None,
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the color sequence used in light functions to a random list of RGB values

        sequenceLength: the number of random colors to use in the generated sequence
        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRandomSequence.__name__)
            self.backgroundColor = backgroundColor = PixelColors.OFF.array
            if twinkleColors == False:
                if sequenceLength is None:
                    sequenceLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
                self.colorSequence = ConvertPixelArrayToNumpyArray(
                    [PixelColors.random() for i in range(sequenceLength)]
                )
                if self.colorSequenceCount < self._LEDCount:
                    self._setVirtualLEDArray(PixelArray(self._LEDCount))
                else:
                    self._setVirtualLEDArray(PixelArray(self.colorSequenceCount))
            elif twinkleColors == True:
                if sequenceLength is None:
                    sequenceLength = random.randint(self._LEDCount // 20, self._LEDCount // 10)
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray(
                    [PixelColors.random() for i in range(sequenceLength)]
                )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorRandomSequence.__name__,
                ex,
            )
            raise

    def useColorRandom(
        self,
        twinkleColors: bool = False,
    ) -> None:
        """
        Sets the color sequence to generate a random RGB value every time one is needed in a function

        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRandom.__name__)
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            if twinkleColors == False:
                colorSequenceCount = random.randint(2, 7)
                colorSequence = []
                for i in range(colorSequenceCount):
                    colorSequence.append(PixelColors.random())
                self.colorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
            elif twinkleColors == True:
                colorSequenceCount = random.randint(2, 7)
                colorSequence = []
                for i in range(colorSequenceCount):
                    colorSequence.append(PixelColors.random())
                self.overlayColorSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorRandom.__name__,
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

        colorSequence: list of colors to in the pattern being shifted across the LED string
        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequenceRepeating.__name__)
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
            elif twinkleColors == True:
                arrayLength = np.ceil(self._LEDCount / len(colorSequence)) * len(colorSequence)
                self.overlayColorSequence = RepeatingColorSequenceArray(
                    arrayLength=arrayLength, colorSequence=colorSequence
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
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        stepsPerTransition: int = 5,
        wrap: bool = True,
        twinkleColors: bool = False,
    ) -> None:
        """
        sets the color sequence used by light functions to the one specified in the argument, but
        makes a smooth transition from one color to the next over the length specified

        colorSequence: list of colors to transition between
        stepsPerTransition:  how many pixels it takes to transition from one color to the next
        wrap: if true, the last color of the sequence will transition to the first color as the final transition
        twinkleColors: set to true when assigning these colors to be used in a twinkle overlay
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransition.__name__)
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
            elif twinkleColors == True:
                self.overlayColorSequence = ColorTransitionArray(
                    arrayLength=len(colorSequence) * int(stepsPerTransition),
                    wrap=False,
                    colorSequence=colorSequence,
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
        colorSequence: List[Pixel] = get_DEFAULT_COLOR_SEQUENCE(),
        stepsPerTransition: int = 5,
        wrap: bool = True,
        twinkleColors: bool = False,
    ) -> None:
        """
        colorSequence: list of colors to in the pattern being shifted across the LED string
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransitionRepeating.__name__)
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
        rainbowPixels: int = None,
        twinkleColors: bool = False,
    ) -> None:
        """
        Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

        rainbowPixels: when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbow.__name__)
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            pixelCount: int = 0
            if isinstance(rainbowPixels, int):
                pixelCount = rainbowPixels
            else:
                pixelCount = random.randint(10, self._LEDCount // 2)
            if twinkleColors == False:
                self.colorSequence = np.array(RainbowArray(arrayLength=pixelCount))
            elif twinkleColors == True:
                self.overlayColorSequence = RainbowArray(arrayLength=pixelCount)
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
        rainbowPixels: int = None,
        twinkleColors: bool = False,
    ) -> None:
        """
        Set the entire LED string to a single color, but cycle through the colors of the rainbow a bit at a time

        rainbowPixels: when creating the rainbow gradient, make the transition through ROYGBIV take this many steps
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbowRepeating.__name__)
            self.backgroundColor = DEFAULT_BACKGROUND_COLOR
            pixelCount: int = 0
            if isinstance(rainbowPixels, int):
                pixelCount = rainbowPixels
            else:
                pixelCount = random.randint(10, self._LEDCount // 2)
            if twinkleColors == False:
                arrayLength = np.ceil(self._LEDCount / pixelCount) * pixelCount
                self.colorSequence = np.copy(
                    RepeatingRainbowArray(arrayLength=arrayLength, segmentLength=pixelCount)
                )
            elif twinkleColors == True:
                colorSequence = RainbowArray(arrayLength=pixelCount)
                arrayLength = np.ceil(self._LEDCount / pixelCount) * pixelCount
                self.overlayColorSequence = RepeatingRainbowArray(
                    arrayLength=arrayLength, segmentLength=pixelCount
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

    def functionNone(self) -> None:
        """ """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionNone.__name__)
            nothing = LightData(self.functionNone.__name__, self._None_Function)
            self._LightDataObjects.append(nothing)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionNone.__name__,
                ex,
            )
            raise

    def _None_Function(
        self,
        nothing: LightData,
    ) -> None:
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
                self._None_Function.__name__,
                ex,
            )
            raise

    def functionSolidColorCycle(
        self,
        delayCount: int = None,
    ) -> None:
        """
        Set all LEDs to a single color at once, but cycle between entries in a list of colors

        delayCount: number of led updates between color updates
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionSolidColorCycle.__name__)
            if delayCount is None:
                _delayCount = random.randint(15, 40)
            else:
                _delayCount = int(delayCount)
            cycle = LightData(self.functionSolidColorCycle.__name__, self._SolidColorCycle_Function)
            cycle.delayCounter = _delayCount
            cycle.delayCountMax = _delayCount
            self._LightDataObjects.append(cycle)
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
                self.functionSolidColorCycle.__name__,
                ex,
            )
            raise

    def _SolidColorCycle_Function(
        self,
        colorCycle: LightData,
    ) -> None:
        """
        set all pixels to the next color
        """
        try:
            colorCycle.delayCounter += 1
            if colorCycle.delayCounter >= colorCycle.delayCountMax:
                self._VirtualLEDArray *= 0
                self._VirtualLEDArray += self.colorSequenceNext
                colorCycle.delayCounter = 0
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._SolidColorCycle_Function.__name__,
                ex,
            )
            raise

    def functionMarquee(
        self,
        shiftAmount: int = None,
    ) -> None:
        """
        Shifts a color pattern across the LED string marquee style.
        Uses the provided sequence of colors.

        shiftAmount: the number of pixels the marquee shifts on each update
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionMarquee.__name__)
            if shiftAmount is None:
                shiftAmount = random.randint(0, 2)
            self._LightDataObjects = []
            marqueePixel = LightData(self.functionMarquee.__name__, self._Marquee_Function)
            marqueePixel.direction = [-1, 1][random.randint(0, 1)]
            marqueePixel.step = 1
            marqueePixel.delayCounter = shiftAmount
            marqueePixel.delayCountMax = shiftAmount
            self._LightDataObjects.append(marqueePixel)
            self._off(marqueePixel)
            self._setVirtualLEDArray(self.colorSequence)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionMarquee.__name__,
                ex,
            )
            raise

    def _Marquee_Function(
        self,
        marqueePixel: LightData,
    ) -> None:
        """ """
        try:
            if marqueePixel.delayCounter >= marqueePixel.delayCountMax:
                marqueePixel.delayCounter = 0
                marqueePixel.stepCounter += marqueePixel.step * marqueePixel.direction
                if (marqueePixel.stepCounter + self.colorSequenceCount >= self._VirtualLEDCount) or (
                    marqueePixel.stepCounter < 0
                ):
                    marqueePixel.direction *= -1
                self._VirtualLEDArray = np.roll(
                    self._VirtualLEDArray,
                    (marqueePixel.step * marqueePixel.direction),
                    0,
                )
            marqueePixel.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._Marquee_Function.__name__,
                ex,
            )
            raise

    def functionCylon(
        self,
        fadeAmount: int = None,
    ) -> None:
        """
        Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        fadeAmount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionCylon.__name__)
            _fadeAmount: float = 15.0 / 255.0
            if fadeAmount is None:
                _fadeAmount = random.randint(5, 75) / 255.0
            else:
                _fadeAmount = fadeAmount

            fade = LightData(self._fadeOff.__name__, self._fadeOff)
            fade.fadeAmount = _fadeAmount
            self._LightDataObjects.append(fade)

            cylon = LightData(self.functionCylon.__name__, self._Cylon_Function)
            cylon.step = 1
            cylon.index = 0
            cylon.delayCountMax = random.randint(0, 3)
            cylon.direction = 1
            cylon.fadeAmount = _fadeAmount
            self._LightDataObjects.append(cylon)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionCylon.__name__,
                ex,
            )
            raise

    def _Cylon_Function(
        self,
        cylon: LightData,
    ) -> None:
        """ """
        try:
            next_index = cylon.index + (cylon.direction * cylon.step)
            if next_index >= self._VirtualLEDCount:
                next_index = self._VirtualLEDCount - 1
                cylon.direction = -1
            elif next_index < 0:
                next_index = 1
                cylon.direction = 1
            cylon.index = next_index
            if cylon.direction == 1:
                indices = list(
                    range(cylon.index, min((cylon.index + self.colorSequenceCount), self._VirtualLEDCount))
                )
                if (cylon.index + self.colorSequenceCount) > self._VirtualLEDCount:
                    overlap = (cylon.index + self.colorSequenceCount) - self._VirtualLEDCount
                    idxs = list(
                        range(
                            (self._VirtualLEDCount - 1),
                            (self._VirtualLEDCount - 1 - overlap),
                            -1,
                        )
                    )
                    indices.extend(idxs)
            else:
                indices = list(range(cylon.index, max((cylon.index - self.colorSequenceCount), 0), -1))
                if (cylon.index - self.colorSequenceCount) < 0:
                    overlap = 0 - (cylon.index - self.colorSequenceCount)
                    idxs = list(
                        range(
                            (1),
                            (1 + overlap),
                        )
                    )
                    indices.extend(idxs)

            self._VirtualLEDArray[indices, :] = self.colorSequence[: self.colorSequenceCount]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._Cylon_Function.__name__,
                ex,
            )
            raise

    def functionMerge(
        self,
        mergeSegmentLength: int = None,
        shiftAmount: int = None,
    ) -> None:
        """
        Reflect a color sequence and shift the reflections toward each other in the middle

        mergeSegmentLength: length of reflected segments
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionMerge.__name__)
            if shiftAmount is None:
                shiftAmount = random.randint(1, 6)
            arrayLength = np.ceil(self._LEDCount / self.colorSequenceCount) * self.colorSequenceCount
            if self.colorSequenceCount >= self._LEDCount:
                self.colorSequence = self.colorSequence[: int(self.colorSequenceCount // 2)]
            self._setVirtualLEDArray(
                ReflectArray(
                    arrayLength=arrayLength,
                    colorSequence=self.colorSequence,
                    foldLength=self.colorSequenceCount,
                )
            )
            merge = LightData(self.functionMerge.__name__, self._Merge_Function)
            merge.size = self.colorSequenceCount
            merge.step = 1
            self._LightDataObjects.append(merge)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionMerge.__name__,
                ex,
            )
            raise

    def _Merge_Function(
        self,
        merge: LightData,
    ) -> None:
        """ """
        try:
            # this takes
            # [0,1,2,3,4,5]
            # and creates
            # [[0,1,2]
            #  [3,4,5]]
            # out of it
            segmentCount = int(self._VirtualLEDIndexCount // merge.size)
            temp = np.reshape(self._VirtualLEDIndexArray, (segmentCount, merge.size))
            # now i can roll each row in a different direction and then undo
            # the matrixification of the array
            if temp[0][0] != temp[1][-1]:
                temp[1] = np.flip(temp[0])
                self._VirtualLEDArray[range(merge.size)] = self.colorSequence[range(merge.size)]
            temp[0] = np.roll(temp[0], merge.step, 0)
            temp[1] = np.roll(temp[1], -merge.step, 0)
            for i in range(self._VirtualLEDIndexCount // merge.size):
                if i % 2 == 0:
                    temp[i] = temp[0]
                else:
                    temp[i] = temp[1]
            # turn the matrix back into an array
            self._VirtualLEDIndexArray = np.reshape(temp, (self._VirtualLEDIndexCount))
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._Merge_Function.__name__,
                ex,
            )
            raise

    def functionAccelerate(
        self,
        beginDelay: float = None,
        endDelay: float = None,
    ) -> None:
        """
        Shifts a color pattern across the LED string marquee style, but accelerates as it goes.
        Uses the provided sequence of colors.

        beginDelay: initial delay between color updates
        endDelay: final delay between color updates
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionAccelerate.__name__)

            # off = LightData(self._off.__name__, self._off)
            # self._LightDataObjects.append(off)

            fade = LightData(self._fadeOff.__name__, self._fadeOff)
            fade.fadeAmount = 25 / 255.0
            self._LightDataObjects.append(fade)

            accelerate = LightData(self.functionAccelerate.__name__, self._Accelerate_Function)
            accelerate.step = 1
            accelerate.direction = 1
            accelerate.stepCountMax = random.randint(int(self._LEDCount / 20), int(self._LEDCount / 4))
            accelerate.delayCounter = 0
            accelerate.delayCountMax = random.randint(5, 10)
            accelerate.stateMax = accelerate.delayCountMax
            self._LightDataObjects.append(accelerate)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionAccelerate.__name__,
                ex,
            )
            raise

    def _Accelerate_Function(
        self,
        accelerate: LightData,
    ) -> None:
        """ """
        try:
            last_index = accelerate.index
            if accelerate.delayCounter >= accelerate.delayCountMax:
                accelerate.delayCounter = 0
                accelerate.stepCounter += 1
                accelerate.index = int(
                    (accelerate.index + (accelerate.direction * accelerate.step)) % self._VirtualLEDCount
                )
            if accelerate.stepCounter >= accelerate.stepCountMax:
                accelerate.stepCounter = 0
                accelerate.delayCountMax -= 1
                if (accelerate.state % 2) == 0:
                    accelerate.step += 1
                accelerate.stepCountMax = random.randint(int(self._LEDCount / 20), int(self._LEDCount / 4))
                accelerate.state += 1
            if accelerate.state >= accelerate.stateMax:
                accelerate.delayCountMax = random.randint(5, 10)
                accelerate.stateMax = accelerate.delayCountMax
                accelerate.direction = [-1, 1][random.randint(0, 1)]
                accelerate.state = 0
                accelerate.step = 1
            accelerate.delayCounter += 1

            self._VirtualLEDArray[last_index : accelerate.index, :] = self.colorSequenceNext
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._Accelerate_Function.__name__,
                ex,
            )
            raise

    def functionRandomChange(
        self,
        delay: int = None,
        changeChance: float = None,
    ) -> None:
        """
        Randomly changes pixels on the string to one of the provided colors

        changeChance: chance that any one pixel will change colors each update (from 0.0, to 1.0)
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionRandomChange.__name__)
            change = LightData(self.functionRandomChange.__name__, self._RandomChange_Function)
            if changeChance is None:
                change.random = random.uniform(0.005, 0.05)
            else:
                change.random = changeChance
            if delay is None:
                change.delayCountMax = random.randint(1, 20)
            else:
                change.delayCountMax = delay
            self._LightDataObjects.append(change)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionRandomChange.__name__,
                ex,
            )
            raise

    def _RandomChange_Function(
        self,
        change: LightData,
    ) -> None:
        """ """
        try:
            maxVal = 1000
            if change.delayCounter >= change.delayCountMax:
                change.delayCounter = 0
                for LEDIndex in range(self._VirtualLEDIndexCount):
                    onLight = random.randint(0, maxVal)
                    if onLight > maxVal * (1.0 - change.random):
                        self._VirtualLEDArray[LEDIndex] = self.colorSequenceNext
                    offLight = random.randint(0, maxVal)
                    if offLight > maxVal * (1.0 - change.random):
                        self._VirtualLEDArray[LEDIndex] = self.backgroundColor
            change.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._RandomChange_Function.__name__,
                ex,
            )
            raise

    def functionRandomFadeChange(
        self,
        delay: int = None,
        changeChance: float = None,
        fadeStepCount: int = None,
    ) -> None:
        """
        Randomly changes pixels on the string to one of the provided colors by fading from one color to the next

        changeChance: chance that any one pixel will change colors each update (from 0.0, to 1.0)
        fadeStepCount: number of steps in the transition from one color to the next
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionRandomFadeChange.__name__)
            change = LightData(self.functionRandomFadeChange.__name__, self._RandomFadeChange_Function)
            if changeChance is None:
                _random = random.uniform(0.3, 0.5)
            else:
                _random = changeChance
            if fadeStepCount is None:
                _colorFade = random.randint(5, 20)
            elif fadeStepCount > 1:
                _colorFade = fadeStepCount
            elif fadeStepCount > 0:
                _colorFade = random.randint(5, 20)
            _fadeAmount = change.colorFade / 255.0
            if delay is None:
                _delayCountMax = random.randint(0, 10)
            else:
                _delayCountMax = delay

            changeIndices = np.array(self._getRandomIndices(_random * 3))
            defaultIndices = np.array(self._getRandomIndices(_random / 3))
            x = np.intersect1d(changeIndices, defaultIndices)
            defaultIndices = np.array([i for i in defaultIndices if not i in x])

            for index in changeIndices:
                if index < self._VirtualLEDCount:
                    fade = LightData(self.functionRandomFadeChange.__name__, self._RandomFadeChange_Function)
                    fade.index = int(index)
                    fade.fadeAmount = _fadeAmount
                    fade.stepCountMax = _colorFade
                    fade.color = np.copy(self._VirtualLEDArray[fade.index])
                    fade.colorNext = self.colorSequenceNext
                    self._LightDataObjects.append(fade)
            for index in changeIndices:
                if index < self._VirtualLEDCount:
                    fade = LightData(self.functionRandomFadeChange.__name__, self._RandomFadeChange_Function)
                    fade.index = int(index)
                    fade.fadeAmount = _fadeAmount
                    fade.stepCountMax = _colorFade
                    fade.color = np.copy(self._VirtualLEDArray[fade.index])
                    fade.colorNext = self.backgroundColor
                    self._LightDataObjects.append(fade)

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionRandomFadeChange.__name__,
                ex,
            )
            raise

    def _RandomFadeChange_Function(
        self,
        change: LightData,
    ) -> None:
        """ """
        try:
            self._fadeLight(change)
            if np.array_equal(change.color, change.colorNext):
                if np.array_equal(change.color, self.backgroundColor):
                    change.index = self._getRandomIndex()
                    change.color = np.copy(self._VirtualLEDArray[change.index])
                    change.colorNext = self.backgroundColor
                else:
                    change.index = self._getRandomIndex()
                    change.color = np.copy(self._VirtualLEDArray[change.index])
                    change.colorNext = self.colorSequenceNext
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._RandomFadeChange_Function.__name__,
                ex,
            )
            raise

    def functionMeteors(
        self,
        fadeAmount: int = None,
        maxSpeed: int = None,
        explode: bool = True,
        meteorCount: int = None,
        collide: bool = None,
        cycleColors: bool = None,
    ) -> None:
        """
        Creates several 'meteors' from the given color list that will fly around the light string leaving a comet trail.
        In this version each meteor contains all colors of the colorSequence.

        fadeAmount: the amount by which meteors are faded
        maxSpeed: the amount be which the meteor moves each refresh
        explode: if True, the meteors will light up in an explosion when they collide
        collide:
        cycleColors:
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionMeteors.__name__)
            if fadeAmount is None:
                _fadeAmount = random.randint(50, 90)
            else:
                _fadeAmount = fadeAmount
            if explode is None:
                _explode = [True, False][random.randint(0, 1)]
            else:
                _explode = explode
            if maxSpeed is None:
                _maxSpeed = random.randint(1, 3)
            else:
                _maxSpeed = maxSpeed

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
                _collide = collide

            if cycleColors is None:
                _cycleColors = random.randint(0, 99) > 50
            else:
                _cycleColors = cycleColors

            otherSpeeds = []
            for index in range(_meteorCount):
                meteor = LightData(self.functionMeteors.__name__, self._Meteors_Function)
                meteor.color = self.colorSequenceNext
                meteor.indexPrevious = random.randint(0, self._VirtualLEDCount - 1)
                meteor.stepSizeMax = _maxSpeed
                meteor.step = random.randint(1, max(2, meteor.stepSizeMax))
                meteor.direction = [-1, 1][random.randint(0, 1)]
                if meteor.step == 1:
                    meteor.delayCountMax = random.randint(0, 3)
                while abs(meteor.step) in otherSpeeds:
                    meteor.step += 1
                meteor.index = (meteor.index + (meteor.step * meteor.direction)) % self._VirtualLEDCount
                meteor.colorCycle = _cycleColors
                meteor.colors = np.copy(self.colorSequence)
                otherSpeeds.append(abs(meteor.step))
                self._LightDataObjects.append(meteor)
            # make sure there are at least two going to collide
            if self._LightDataObjects[0].direction * self._LightDataObjects[1].direction > 0:
                self._LightDataObjects[1].direction *= -1

            fade = LightData(self._fadeOff.__name__, self._fadeOff)
            fade.fadeAmount = 0.3
            self._LightDataObjects.append(fade)

            if _collide == True:
                collision = LightData(self._collision.__name__, self._collision)
                collision.explode = _explode
                self._LightDataObjects.append(collision)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionMeteors.__name__,
                ex,
            )
            raise

    def _Meteors_Function(
        self,
        meteor: LightData,
    ) -> None:
        """ """
        try:
            if meteor.delayCounter >= meteor.delayCountMax:
                meteor.delayCounter = 0
                oldIndex = meteor.index
                newIndex = meteor.index + (meteor.step * meteor.direction)
                newLocation = (meteor.index + (meteor.step * meteor.direction)) % self._VirtualLEDCount
                # save previous index
                meteor.indexPrevious = meteor.index
                # assign new index
                meteor.index = newLocation
                # positive step
                meteor.moveRange = np.array(
                    list(
                        range(
                            meteor.indexPrevious,
                            newIndex,
                            meteor.direction,
                        )
                    )
                )
                modulo = np.where(meteor.moveRange >= self._VirtualLEDCount)
                meteor.moveRange[modulo] -= self._VirtualLEDCount
                modulo = np.where(meteor.moveRange < 0)
                meteor.moveRange[modulo] += self._VirtualLEDCount

                if meteor.colorCycle:
                    meteor.colorIndex = (meteor.colorIndex + (meteor.direction * meteor.step)) % len(
                        meteor.colors
                    )

                self._VirtualLEDArray[meteor.moveRange] = meteor.color

            meteor.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._Meteors_Function.__name__,
                ex,
            )
            raise

    def _collision(
        self,
        collision: LightData,
    ) -> None:
        foundBounce = False
        if len(self._LightDataObjects) > 1:
            for index1, meteor1 in enumerate(self._LightDataObjects):
                if meteor1.runFunction == self._Meteors_Function:
                    if index1 + 1 < len(self._LightDataObjects):
                        for index2, meteor2 in enumerate(self._LightDataObjects[index1 + 1 :]):
                            if meteor2.runFunction == self._Meteors_Function:
                                if isinstance(meteor1.moveRange, np.ndarray) and isinstance(
                                    meteor2.moveRange, np.ndarray
                                ):
                                    # this detects the intersection of two self._LightDataObjects' movements across LEDs
                                    intersection = np.intersect1d(meteor1.moveRange, meteor2.moveRange)
                                    if len(intersection) > 0 and random.randint(0, 4) != 0:
                                        meteor1.bounce = True
                                        meteor1.collideWith = meteor2
                                        meteor1.stepLast = meteor1.step
                                        meteor1.collideIntersect = int(intersection[0])
                                        meteor2.bounce = True
                                        meteor2.collideWith = meteor1
                                        meteor2.stepLast = meteor2.step
                                        meteor2.collideIntersect = int(intersection[0])
                                        foundBounce = True
        explosion_indices = []
        explosion_colors = []
        if foundBounce == True:
            for index, meteor in enumerate(self._LightDataObjects):
                if meteor.runFunction == self._Meteors_Function:
                    if meteor.bounce is True:
                        previous = int(meteor.step)
                        meteor.direction *= -1
                        meteor.index = (
                            meteor.collideIntersect + (meteor.step * meteor.direction)
                        ) % self._VirtualLEDCount
                        meteor.indexPrevious = meteor.collideIntersect
                        meteor.bounce = False
                        meteor.collideWith = None
                        if collision.explode:
                            middle = meteor.moveRange[len(meteor.moveRange) // 2]
                            r = self._LEDCount // 20
                            for i in range(r):
                                explosion_indices.append(
                                    (middle - i) % self._VirtualLEDCount,
                                )
                                explosion_colors.append(
                                    Pixel(PixelColors.YELLOW).array * (r - i) / r,
                                )

                                explosion_indices.append(
                                    (middle + i) % self._VirtualLEDCount,
                                )
                                explosion_colors.append(
                                    Pixel(PixelColors.YELLOW).array * (r - i) / r,
                                )
                            self._VirtualLEDArray[explosion_indices] = np.array(explosion_colors)

    def functionPaint(
        self,
        maxDelay: int = None,
    ) -> None:
        """
        wipes colors in the current sequence across the pixel strand in random directions and amounts
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionPaint.__name__)
            if maxDelay is None:
                maxDelay = random.randint(2, 10)
            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                paintBrush = LightData(self.functionPaint.__name__, self._Paint_Function)
                paintBrush.index = random.randint(0, self._VirtualLEDCount - 1)
                paintBrush.step = (-1, 1)[random.randint(0, 1)]
                paintBrush.delayCountMax = random.randint(min(0, maxDelay), max(0, maxDelay))
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
                self.functionPaint.__name__,
                ex,
            )
            raise

    def _Paint_Function(
        self,
        paintBrush: LightData,
    ) -> None:
        """ """
        try:
            # loop through objects
            # for paintBrush in self._LightDataObjects:
            paintBrush.delayCounter += 1
            if paintBrush.delayCounter >= paintBrush.delayCountMax:
                paintBrush.delayCounter = 0
                paintBrush.index = (paintBrush.index + paintBrush.step) % self._VirtualLEDCount
                paintBrush.stepCounter += 1
                if paintBrush.stepCounter >= paintBrush.stepCountMax:
                    paintBrush.stepCounter = 0
                    paintBrush.step = (-1, 1)[random.randint(-1, 1)]
                    paintBrush.delayCountMax = random.randint(0, paintBrush.delayCountMax)
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
                self._Paint_Function.__name__,
                ex,
            )
            raise

    def functionSprites(
        self,
        fadeSteps: int = None,
    ) -> None:
        """
        Uses colors in the current list to fly meteor style across
        the pixel strand in short bursts of random length and direction.

        fadeSteps:
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionSprites.__name__)
            if fadeSteps is None:
                fadeSteps = random.randint(1, 6)
            for i in range(max(min(self.colorSequenceCount, 10), 2)):
                sprite = LightData(self.functionSprites.__name__, self._Sprites_Function)
                sprite.color = self.colorSequenceNext
                sprite.colors = self.colorSequence
                sprite.colorNext = PixelColors.OFF.array
                sprite.active = False
                sprite.dying = False
                sprite.index = random.randint(0, self._VirtualLEDCount - 1)
                sprite.indexPrevious = sprite.index
                sprite.direction = [-1, 1][random.randint(0, 1)]
                sprite.colorSequenceIndex = i
                sprite.fadeSteps = fadeSteps
                sprite.fadeAmount = np.ceil(255 / fadeSteps)
                # sprite.LightDataObjects = []
                self._LightDataObjects.append(sprite)
            self._LightDataObjects[0].active = True

            fade = LightData(self._fadeOff.__name__, self._fadeOff)
            fade.fadeAmount = 25 / 255.0
            self._LightDataObjects.append(fade)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionSprites.__name__,
                ex,
            )
            raise

    # def _Sprites_Configuration(self, fadeSteps: int):
    #     """ """
    #     try:
    #         LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
    #         self._fadeSteps = fadeSteps
    #         self._fadeAmount = np.ceil(255 / fadeSteps)
    #         self._LightDataObjects = []
    #         for i in range(max(min(self.colorSequenceCount, 10), 2)):
    #             sprite = LightData(self.colorSequenceNext)
    #             sprite.active = False
    #             sprite.dying = False
    #             sprite.index = random.randint(0, self._VirtualLEDCount - 1)
    #             sprite.lastindex = sprite.index
    #             sprite.direction = [-1, 1][random.randint(0, 1)]
    #             sprite.colorSequenceIndex = i
    #             self._LightDataObjects.append(sprite)
    #         self._LightDataObjects[0].active = True
    #     except SystemExit:
    #         raise
    #     except KeyboardInterrupt:
    #         raise
    #     except Exception as ex:
    #         LOGGER.exception(
    #             "%s.%s Exception: %s",
    #             self.__class__.__name__,
    #             inspect.stack()[0][3],
    #             ex,
    #         )
    #         raise

    def _Sprites_Function(
        self,
        sprite: LightData,
    ) -> None:
        """ """
        try:
            # self._fadeOff()
            # for sprite in self._LightDataObjects:
            if sprite.active:
                if not sprite.dying:
                    sprite.dying = random.randint(6, self._VirtualLEDCount // 2) < sprite.duration
                # if sprite.active:
                sprite.indexPrevious = sprite.index
                step_size = random.randint(1, 3) * sprite.direction
                mi = min(sprite.index, sprite.index + step_size)
                ma = max(sprite.index, sprite.index + step_size)
                first = True
                if sprite.direction > 0:
                    for index in range(mi + 1, ma + 1):
                        index = index % self._VirtualLEDCount
                        sprite.index = index
                        self._VirtualLEDArray[sprite.index] = sprite.color
                        # if not first:
                        # self._fadeLED(index, self.backgroundColor, self._fadeAmount)
                        first - False
                else:
                    for index in range(ma - 1, mi - 1, -1):
                        index = index % self._VirtualLEDCount
                        sprite.index = index
                        self._VirtualLEDArray[sprite.index] = sprite.color
                        # if not first:
                        # self._fadeLED(index, self.backgroundColor, self._fadeAmount)
                        first - False
                if sprite.dying:
                    sprite.color = self._fadeColor(sprite.color, sprite.colorNext, 25)
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
                    sprite.indexPrevious = sprite.index
                    sprite.color = self.colorSequenceNext
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self._Sprites_Function.__name__,
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
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionRaindrops.__name__)
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
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionRaindrops.__name__,
                ex,
            )
            raise

    # def _Raindrops_Configuration(self, fadeAmount: int, maxSize: int, raindropChance: float, stepSize: int):
    #     """ """
    #     try:
    #         LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
    #         self._fadeAmount = int((255 - fadeAmount) // 255)
    #         self._LightDataObjects = []
    #         for i in range(max(min(self.colorSequenceCount, 10), 2)):
    #             raindrop = LightData(self.colorSequenceNext)
    #             raindrop.sizeMax = maxSize
    #             raindrop.index = random.randint(0, self._VirtualLEDCount - 1)
    #             raindrop.stepCountMax = random.randint(2, raindrop.sizeMax)
    #             raindrop.step = stepSize
    #             raindrop.fadeAmount = ((255 / raindrop.stepCountMax) / 255) * 2
    #             raindrop.active = False
    #             raindrop.activeChance = raindropChance
    #             self._LightDataObjects.append(raindrop)
    #         self._LightDataObjects[0].active = True
    #     except SystemExit:
    #         raise
    #     except KeyboardInterrupt:
    #         raise
    #     except Exception as ex:
    #         LOGGER.exception(
    #             "%s.%s Exception: %s",
    #             self.__class__.__name__,
    #             inspect.stack()[0][3],
    #             ex,
    #         )
    #         raise

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
                self._Raindrops_Function.__name__,
                ex,
            )
            raise

    def functionTwinkle(self, refreshDelay: float = None, twinkleChance: float = 0.02):
        """
        Randomly sets some lights to 'twinkleColor' temporarily

        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.functionTwinkle.__name__)
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionTwinkle.__name__,
                ex,
            )
            raise

    # def _Twinkle_Configuration(self, twinkleChance: float):
    #     """ """
    #     try:
    #         LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
    #         self._TwinkleChance = float(twinkleChance)
    #         if isinstance(self._colorFunction, dict):
    #             self._overlayColorFunction = {k: v for k, v in self._colorFunction.items()}
    #             self._overlayColorFunction["twinkleColors"] = True
    #         else:
    #             # TODO: make this exception useful
    #             raise Exception("")
    #         self.useColorSingle(PixelColors.OFF)
    #     except SystemExit:
    #         raise
    #     except KeyboardInterrupt:
    #         raise
    #     except Exception as ex:
    #         LOGGER.exception(
    #             "%s.%s Exception: %s",
    #             self.__class__.__name__,
    #             inspect.stack()[0][3],
    #             ex,
    #         )
    #         raise

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
                self._Twinkle_Overlay.__name__,
                ex,
            )
            raise

    def functionBlink(self, refreshDelay: float = None, blinkChance: float = 0.02):
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, self.functionBlink.__name__)
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 50
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionBlink.__name__,
                ex,
            )
            raise

    # def _Blink_Configuration(self, blinkChance: float):
    #     try:
    #         LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
    #         self._BlinkChance = float(blinkChance)
    #         if isinstance(self._colorFunction, dict):
    #             self._overlayColorFunction = {k: v for k, v in self._colorFunction.items()}
    #             self._overlayColorFunction["twinkleColors"] = True
    #         else:
    #             # TODO: make this exception useful
    #             raise Exception("")
    #         self.useColorSingle(PixelColors.OFF)
    #     except SystemExit:
    #         raise
    #     except KeyboardInterrupt:
    #         raise
    #     except Exception as ex:
    #         LOGGER.exception(
    #             "%s.%s Exception: %s",
    #             self.__class__.__name__,
    #             inspect.stack()[0][3],
    #             ex,
    #         )
    #         raise

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
                self._Blink_Overlay.__name__,
                ex,
            )
            raise

    def functionItsAlive(self, refreshDelay: float = None):
        try:
            LOGGER.log(5, "%s.%s:", self.__class__.__name__, self.functionItsAlive.__name__)
            if refreshDelay is None:
                refreshDelay = (DEFAULT_REFRESH_DELAY / self._LEDCount) / 5
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.functionItsAlive.__name__,
                ex,
            )
            raise

    # def _itsAlive_Configuration(self):
    #     """ """
    #     try:
    #         LOGGER.log(5, "%s.%s:", self.__class__.__name__, inspect.stack()[0][3])
    #         self._LightDataObjects = []
    #         for i in range(1):
    #             thing = LightData(self.colorSequenceNext.copy())
    #             thing.index = random.randint(0, self._VirtualLEDCount - 1)
    #             thing.stepCountMax = random.randint(self._VirtualLEDCount // 10, self._VirtualLEDCount)
    #             thing.fadeAmount = 255 / thing.stepCountMax
    #             thing.sizeMax = self._VirtualLEDCount // 3
    #             thing.size = 1
    #             thing.fadeAmount = random.randint(80, 192)
    #             thing.direction = [-1, 1][random.randint(0, 1)]
    #             thing.step = random.randint(1, 3)
    #             thing.state = 1
    #             thing.delayCountMax = random.randint(6, 15)
    #             self._LightDataObjects.append(thing)
    #         self._LightDataObjects[0].active = True
    #     except SystemExit:
    #         raise
    #     except KeyboardInterrupt:
    #         raise
    #     except Exception as ex:
    #         LOGGER.exception(
    #             "%s.%s Exception: %s",
    #             self.__class__.__name__,
    #             inspect.stack()[0][3],
    #             ex,
    #         )
    #         raise

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
                thing.indexPrevious = thing.index
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
                    x1 = thing.indexPrevious - (thing.size * thing.direction)
                    x2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
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
                self._itsAlive_Function.__name__,
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
                        # c = self._colorFunction.copy()
                        # c.pop("function")
                        # self._colorFunction["function"](**c)
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
                self.test.__name__,
                ex,
            )
            raise
