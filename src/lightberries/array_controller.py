"""Class defines methods for interacting with Light Strings, Patterns, and Functions."""
from __future__ import annotations
from math import ceil
import sys
import time
import random
import logging
from typing import (
    Callable,
    Optional,
    Any,
)
import numpy as np
from lightberries.array_patterns import ArrayPattern, ConvertPixelArrayToNumpyArray
from lightberries.exceptions import (
    LightBerryException,
    ControllerException,
)
from lightberries.pixel import Pixel, PixelColors
from lightberries.ws281x_strings import WS281xString
from lightberries.array_functions import (
    ArrayFunction,
    LEDFadeType,
    RaindropStates,
    SpriteState,
    ThingMoves,
)


LOGGER = logging.getLogger("lightBerries")
DEFAULT_REFRESH_DELAY = 50


class ArrayController:
    """This library wraps the rpi_ws281x library and provides some lighting functions.

    See https://github.com/rpi-ws281x/rpi-ws281x-python for questions about rpi_ws281x library.

    Quick Start:
        1: Create a LightArrayController object specifying ledCount:int, pwmGPIOpin:int,
            channelDMA:int, frequencyPWM:int
                lights = LightArrayController(10, 18, 10, 800000)

        2: Choose a color pattern
                lights.useColorRainbow()

        3: Choose a function
                lights.useFunctionCylon()

        4: Choose a duration to run
                lights.secondsPerMode = 60

        5: Run
                lights.run()
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
        stripTypeLED: Any = None,
        gamma: Any = None,
        debug: bool = False,
        verbose: bool = False,
        refreshCallback: Callable = None,
        simulate: bool = False,
        testing: bool = False,
    ) -> None:
        """Create a LightArrayController object for running patterns across a rpi_ws281x LED string.

        Args:
            ledCount: the number of Pixels in your string of LEDs
            pwmGPIOpin: the GPIO pin number your lights are hooked up to
                (18 is a good choice since it does PWM)
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
            refreshCallback: callback method is called whenever new LED values are sent to LED string
            simulate: only call refreshCallback, don't use GPIO

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            # configure logging
            if debug is True or verbose is True:
                if not LOGGER.handlers:
                    streamHandler = logging.StreamHandler()
                    LOGGER.addHandler(streamHandler)
                LOGGER.setLevel(logging.INFO)
                if sys.platform != "linux":
                    fh = logging.FileHandler(__name__ + ".log")
                else:
                    fh = logging.FileHandler("/home/pi/" + __name__ + ".log")  # pragma: no cover
                fh.setLevel(logging.DEBUG)
                LOGGER.addHandler(fh)
                LOGGER.setLevel(logging.DEBUG)
            if verbose is True:
                LOGGER.setLevel(5)
            self.simulate = simulate
            # wrap pixel strip in my own interface object
            self._instantiate_WS281xString(
                ledCount=ledCount,
                pwmGPIOpin=pwmGPIOpin,
                channelDMA=channelDMA,
                frequencyPWM=frequencyPWM,
                invertSignalPWM=invertSignalPWM,
                ledBrightnessFloat=ledBrightnessFloat,
                channelPWM=channelPWM,
                stripTypeLED=stripTypeLED,
                gamma=gamma,
                simulate=simulate,
                testing=testing,
            )

            # initialize instance variables
            self.privateLEDCount: int = len(self.ws281xString)
            self.virtualLEDBuffer: np.ndarray[(3, Any), np.int32] = ArrayPattern.SolidColorArray(
                arrayLength=self.privateLEDCount,
                color=PixelColors.OFF.array,
            )
            self.virtualLEDIndexBuffer: np.ndarray[(Any,), np.int32] = np.array(range(len(self.ws281xString)))
            self.privateOverlayDict: dict[int, np.ndarray[(3,), np.int32]] = {}
            self.privateVirtualLEDCount: int = len(self.virtualLEDBuffer)
            self.privateVirtualLEDIndexCount: int = len(self.virtualLEDIndexBuffer)
            self.privateLastModeChange: float = time.time() - 1000
            self.privateNextModeChange: float = time.time()
            self.privateRefreshDelay: float = 0.001
            self.privateSecondsPerMode: float = 120.0
            self.privateBackgroundColor: np.ndarray[(3,), np.int32] = PixelColors.OFF.array
            self.privateColorSequence: np.ndarray[(3, Any), np.int32] = ArrayPattern.DefaultColorSequenceByMonth()
            self.privateColorSequenceCount: int = len(self.privateColorSequence)
            self.privateColorSequenceIndex: int = 0
            self.privateLoopForever: bool = False
            self.privateLightFunctions: list[ArrayFunction] = []

            # give LightFunction class a pointer to this class
            ArrayFunction.Controller = self

            self.running: bool = False
            self.refreshCallback: Callable = refreshCallback
            # initialize stuff
            self.reset()
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def _instantiate_WS281xString(
        self,
        ledCount: int,
        pwmGPIOpin: int,
        channelDMA: int,
        frequencyPWM: int,
        invertSignalPWM: bool,
        ledBrightnessFloat: float,
        channelPWM: int,
        stripTypeLED: Any,
        gamma: Any,
        simulate: bool,
        testing: bool = False,
    ) -> None:
        self.ws281xString: Optional[WS281xString] = WS281xString(
            ledCount=ledCount,
            pwmGPIOpin=pwmGPIOpin,
            channelDMA=channelDMA,
            frequencyPWM=frequencyPWM,
            invertSignalPWM=invertSignalPWM,
            ledBrightnessFloat=ledBrightnessFloat,
            channelPWM=channelPWM,
            stripTypeLED=stripTypeLED,
            gamma=gamma,
            simulate=simulate,
            testing=testing,
        )

    def __del__(
        self,
    ) -> None:
        """Disposes of the rpi_ws281x object (if it exists) to prevent memory leaks.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            if self.ws281xString is not None:
                self.off()
                self.copyVirtualLedsToWS281X()
                self.refreshLEDs()
                self.ws281xString.__del__()
                self.ws281xString = None
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    @property
    def virtualLEDCount(self) -> int:
        """The number of virtual LEDs. These include ones that won't display.

        Returns:
            the number of virtual LEDs
        """
        return self.privateVirtualLEDCount

    @property
    def realLEDCount(self) -> int:
        """The number of LEDs in the LED string.

        Returns:
            the number of actual LEDs in the string (as configured)
        """
        return self.privateLEDCount

    @property
    def refreshDelay(
        self,
    ) -> float:
        """The delay between starting LED refreshes.

        Returns:
            the delay between refreshes
        """
        return self.privateRefreshDelay

    @refreshDelay.setter
    def refreshDelay(
        self,
        delay: float,
    ) -> None:
        """Set the refresh delay.

        Args:
            delay: the delay in seconds
        """
        self.privateRefreshDelay = float(delay)

    @property
    def backgroundColor(
        self,
    ) -> np.ndarray[(3,), np.int32]:
        """The defined background, or "Off" color for the LED string.

        Returns:
            the rgb value
        """
        return self.privateBackgroundColor

    @backgroundColor.setter
    def backgroundColor(
        self,
        color: np.ndarray[(3,), np.int32],
    ) -> None:
        """Set the background color.

        Args:
            color: an RGB value
        """
        self.privateBackgroundColor = Pixel(color).array

    @property
    def secondsPerMode(
        self,
    ) -> float:
        """The number of seconds to run the configuration.

        Returns:
            the seconds to run the current configuration
        """
        return self.privateSecondsPerMode

    @secondsPerMode.setter
    def secondsPerMode(
        self,
        seconds: float,
    ) -> None:
        """Set the seconds per mode.

        Args:
            seconds: the number of seconds
        """
        self.privateSecondsPerMode = float(seconds)

    @property
    def colorSequence(
        self,
    ) -> np.ndarray[(3, Any), np.int32]:
        """The sequence of RGB values to use for generating patterns when using the functions.

        Returns:
            the sequence of RGB values
        """
        return self.privateColorSequence

    @colorSequence.setter
    def colorSequence(
        self,
        colorSequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Set the color sequence.

        Args:
            colorSequence: the sequence of RGB values
        """
        self.privateColorSequence = np.copy(ConvertPixelArrayToNumpyArray(colorSequence))
        self.colorSequenceCount = len(self.privateColorSequence)
        self.colorSequenceIndex = 0

    @property
    def colorSequenceCount(
        self,
    ) -> int:
        """The number of colors in the defined sequence.

        Returns:
            the number of LEDs in the sequence
        """
        return self.privateColorSequenceCount

    @colorSequenceCount.setter
    def colorSequenceCount(
        self,
        colorSequenceCount: int,
    ) -> None:
        """Set the Color sequence count.

        Args:
            colorSequenceCount: the number of colors in the sequence
        """
        self.privateColorSequenceCount = colorSequenceCount

    @property
    def colorSequenceIndex(
        self,
    ) -> int:
        """The index we are on in the current color sequence.

        Returns:
            the current index into the color sequence
        """
        return self.privateColorSequenceIndex

    @colorSequenceIndex.setter
    def colorSequenceIndex(
        self,
        colorSequenceIndex: int,
    ) -> None:
        """Set the color sequence index.

        Args:
            colorSequenceIndex: the new index
        """
        if colorSequenceIndex >= len(self.colorSequence):
            self.privateColorSequenceIndex = 0
        else:
            self.privateColorSequenceIndex = colorSequenceIndex

    @property
    def colorSequenceNext(
        self,
    ) -> np.ndarray[(3,), np.int32]:
        """Get the next color in the sequence.

        Returns:
            the next RGB value
        """
        temp = self.colorSequence[self.colorSequenceIndex]
        self.colorSequenceIndex += 1
        return temp

    @property
    def functionList(self) -> list[ArrayFunction]:
        """The list of function objects that will be used to modify the light pattern.

        Returns:
            the list of functions
        """
        return self.privateLightFunctions

    @property
    def overlayDictionary(self) -> dict[int, Any]:
        """The list of indices and associated colors to temporarily assign LEDs.

        Returns:
            the dictionary of LEDs and values
        """
        return self.privateOverlayDict

    def getColorMethodsList(self) -> list[str]:
        """Get the list of methods in this class (by name) that set the color sequence.

        Returns:
            a list of method name strings
        """
        attrs = list(dir(self))
        colors = [c for c in attrs if c[:8] == "useColor"]
        colors.sort()
        return colors

    def getFunctionMethodsList(self) -> list[str]:
        """Get the list of methods in this class (by name) that set the color functions.

        Returns:
            a list of method name strings
        """
        attrs = list(dir(self))
        functions = [f for f in attrs if f[:11] == "useFunction"]
        functions.sort()
        return functions

    def reset(
        self,
    ) -> None:
        """Reset class variables to default state.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.reset.__name__)
            self.privateLightFunctions = []
            if self.virtualLEDCount >= self.realLEDCount:
                self.setvirtualLEDBuffer(self.virtualLEDBuffer[: self.realLEDCount])
            elif self.virtualLEDCount < self.realLEDCount:
                array = ArrayPattern.SolidColorArray(arrayLength=self.realLEDCount, color=PixelColors.OFF.array)
                self.setvirtualLEDBuffer(array)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def setvirtualLEDBuffer(
        self,
        ledBuffer: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Assign a sequence of pixel data to the LED.

        Args:
            ledBuffer: array of RGB values

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            # make sure the passed LED array is the correct type
            _ledBuffer = ledBuffer
            _ledBufferLen = int(_ledBuffer.size / 3)

            # check assignment length
            if _ledBufferLen >= self.realLEDCount or len(_ledBuffer.shape) > 2 or len(self.virtualLEDBuffer.shape) > 2:
                self.virtualLEDBuffer = _ledBuffer
            else:
                self.virtualLEDBuffer[:_ledBufferLen] = _ledBuffer

            # assign new LED array to virtual LEDs
            self.privateVirtualLEDCount = _ledBufferLen
            # set our indices for virtual LEDs
            self.privateVirtualLEDIndexCount = self.virtualLEDCount
            # create array of index values for manipulation if needed
            self.virtualLEDIndexBuffer = np.arange(self.virtualLEDCount)
            # if the array is smaller than the actual light strand, make our entire strand addressable
            if self.privateVirtualLEDIndexCount < self.realLEDCount and len(self.virtualLEDBuffer.shape) < 3:
                self.privateVirtualLEDIndexCount = self.realLEDCount
                self.virtualLEDIndexBuffer = np.arange(self.privateVirtualLEDIndexCount)
                self.virtualLEDBuffer = np.concatenate(
                    (
                        self.virtualLEDBuffer,
                        np.array([PixelColors.OFF.tuple for i in range(self.realLEDCount - self.virtualLEDCount)]),
                    )
                )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def copyVirtualLedsToWS281X(
        self,
    ) -> None:
        """Sets each Pixel in the rpi_ws281x object to the buffered array value.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        # callback function to do work

        def SetPixel(i_rgb):
            self.ws281xString[i_rgb[0]] = i_rgb[1]

        # fast method of calling the callback method on each index of LED array
        list(
            map(
                SetPixel,
                enumerate(
                    self.virtualLEDBuffer[self.virtualLEDIndexBuffer][
                        np.where(self.virtualLEDIndexBuffer < self.realLEDCount)
                    ]
                ),
            )
        )

    def refreshLEDs(
        self,
    ) -> None:
        """Display current LED buffer.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            # call light string's refresh method to send the communications out to the addressable LEDs
            if isinstance(self.refreshCallback, Callable):
                self.refreshCallback()
            self.ws281xString.refresh()
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def off(
        self,
    ) -> None:
        """Set all Pixels to RGD background color.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            # clear all current values
            self.virtualLEDBuffer *= 0
            # set to background color
            self.virtualLEDBuffer[:] += self.backgroundColor
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def _runFunctions(
        self,
    ) -> None:
        """Run each function in the configured function list.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            # invoke the function pointer saved in the light data object
            for function in self.privateLightFunctions:
                function.runFunction(function)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def _copyOverlays(
        self,
    ):
        """Copy overlays directly to output array, bypassing the buffer.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            # iterate over the dictionary key-value pairs, assign LED values
            # directly to output buffer skipping the virtual LED copies.
            # This ensures that overlays are temporary and get overwritten
            # next refresh.
            for index, ledValue in self.privateOverlayDict.items():
                self.ws281xString[index] = ledValue
            self.privateOverlayDict = {}
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def getRandomIndex(
        self,
    ) -> int:
        """Retrieve a random Pixel index.

        Returns:
            a random index into the virtual LED buffer

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            return random.randint(0, (self.virtualLEDCount - 1))
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def getRandomIndices(
        self,
        count: int,
    ) -> np.ndarray[(Any), np.int32]:
        """Retrieve a random list of Pixel indices.

        Args:
            count: the number of random indices to get

        Returns:
            a list of random indices into the virtual LED buffer

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            temp = []
            for _ in range(count):
                temp.append(self.getRandomIndex())
            return np.array(temp, dtype=np.int32)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def getRandomDirection(self) -> int:
        """Get a random one or negative one to determine direction for light functions.

        Returns:
            one or negative one, randomly
        """
        return [-1, 1][random.randint(0, 1)]

    def getRandomBoolean(self) -> bool:
        """Get a random true or false value.

        Returns:
            True or False, randomly
        """
        return [True, False][random.randint(0, 1)]

    def fadeColor(
        self,
        color: np.ndarray[(3,), np.int32],
        colorNext: np.ndarray[(3,), np.int32],
        fadeAmount: float,
    ) -> np.ndarray[(3,), np.int32]:
        """Fade an LED's color by the given amount and return the new RGB value.

        Args:
            color: current color
            colorNext: desired color
            fadeCount: amount to adjust each RGB value by

        Returns:
            new RGB value
        """
        # copy it to make sure we don't change the original by reference
        _color: np.ndarray[(3,), np.int32] = np.copy(color)
        _fadeAmount = ceil(fadeAmount * 256)
        if _fadeAmount < 0:
            _fadeAmount = 1
        elif _fadeAmount > 255:
            _fadeAmount = 255
        # loop through RGB values
        for rgbIndex in range(len(_color)):
            # the values closest to the target color might match already
            if _color[rgbIndex] != colorNext[rgbIndex]:
                # subtract or add as appropriate in order to get closer to target color
                if _color[rgbIndex] - _fadeAmount > colorNext[rgbIndex]:
                    _color[rgbIndex] -= _fadeAmount
                elif _color[rgbIndex] + _fadeAmount < colorNext[rgbIndex]:
                    _color[rgbIndex] += _fadeAmount
                else:
                    _color[rgbIndex] = colorNext[rgbIndex]
        return _color

    def run(self):
        """Run the configured color pattern and function either forever or for self.secondsPerMode.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.run.__name__)
            # set start time
            self.privateLastModeChange = time.time()
            # set a target time to change
            if self.secondsPerMode is None:
                self.privateNextModeChange = self.privateLastModeChange + (random.uniform(30, 120))
            else:
                self.privateNextModeChange = self.privateLastModeChange + (self.secondsPerMode)
            # loop
            self.running = True
            while (time.time() < self.privateNextModeChange and self.running is True) or self.privateLoopForever:
                try:
                    # run the selected functions using LightFunction object callbacks
                    self._runFunctions()
                    # copy the resulting RGB values to the ws28xx LED buffer
                    self.copyVirtualLedsToWS281X()
                    # copy temporary changes (not buffered in this class) to the ws28xx LED buffer
                    self._copyOverlays()
                    # tell the ws28xx controller to transmit the new data
                    self.refreshLEDs()
                except KeyboardInterrupt:  # pragma: no cover
                    raise
                except SystemExit:  # pragma: no cover
                    raise
                except LightBerryException:  # pragma: no cover
                    raise
                except Exception as ex:  # pragma: no cover
                    raise ControllerException from ex
            self.privateLastModeChange = time.time()
            if self.secondsPerMode is None:
                self.privateNextModeChange = self.privateLastModeChange + (random.random(30, 120))
            else:
                self.privateNextModeChange = self.privateLastModeChange + (self.secondsPerMode)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.run.__name__,
                ex,
            )
            raise ControllerException from ex

    def useColorSingle(
        self,
        foregroundColor: Pixel = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the the color sequence used by light functions to a single color of your choice.

        Args:
            foregroundColor: the color that each pixel will be set to
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSingle.__name__)
        try:

            # defaults
            _sequence: np.ndarray[(Any, 3), np.int32] = ArrayPattern.DefaultColorSequenceByMonth()
            _foregroundColor: np.ndarray[(3,), np.int32] = _sequence[random.randint(0, len(_sequence) - 1)]
            _backgroundColor = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array

            # use the passed in color
            if foregroundColor is not None:
                _foregroundColor = Pixel(foregroundColor).array

            # use the passed in color
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array

            # assign temporary values to instance variables
            self.backgroundColor = _backgroundColor
            self.colorSequence = ConvertPixelArrayToNumpyArray([_foregroundColor])
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorSinglePseudoRandom(
        self,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the the color sequence used by light functions to a single random named color.

        Args:
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSinglePseudoRandom.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            # set background color
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array

            self.backgroundColor = _backgroundColor
            # set the color sequence
            self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.PSEUDO_RANDOM])
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorSingleRandom(
        self,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the the color sequence to a single random RGB value.

        Args:
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSingleRandom.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            # set the background color to the default values
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array

            self.backgroundColor = _backgroundColor
            # set the color sequence to a single random value
            self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.RANDOM])
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorSequence(
        self,
        colorSequence: list[Pixel] = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the the color sequence used by light functions to one of your choice.

        Args:
            colorSequence: list of colors in the pattern
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequence.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _colorSequence: np.ndarray[(Any, 3), np.int32] = ArrayPattern.DefaultColorSequenceByMonth()
            # set the color sequence to the default one for this month, or use the passed in argument
            if colorSequence is not None:
                _colorSequence = [Pixel(p) for p in colorSequence]
            # assign the background color its default value
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            self.backgroundColor = _backgroundColor
            # set the color sequence
            self.colorSequence = ConvertPixelArrayToNumpyArray(_colorSequence)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorSequencePseudoRandom(
        self,
        sequenceLength: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the color sequence used in light functions to a random list of named colors.

        Args:
            sequenceLength: the number of random colors to use in the generated sequence
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequencePseudoRandom.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _sequenceLength: int = random.randint(self.realLEDCount // 20, self.realLEDCount // 10)
            # either calculate a sequence length or use the passed value
            if sequenceLength is not None:
                _sequenceLength = int(sequenceLength)
            # set background color
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            # assign the color sequence
            self.backgroundColor = _backgroundColor
            self.colorSequence = ConvertPixelArrayToNumpyArray(
                [PixelColors.PSEUDO_RANDOM for i in range(_sequenceLength)]
            )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorSequenceRandom(
        self,
        sequenceLength: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the color sequence used in light functions to a random list of RGB values.

        Args:
            sequenceLength: the number of random colors to use in the generated sequence
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequenceRandom.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _sequenceLength: int = random.randint(self.realLEDCount // 20, self.realLEDCount // 10)
            # set background color
            if backgroundColor is not None:
                self.backgroundColor = Pixel(backgroundColor).array
            # calculate sequence length or use argument
            if sequenceLength is not None:
                _sequenceLength = int(sequenceLength)
            # create color sequence
            self.backgroundColor = _backgroundColor
            self.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.RANDOM for i in range(_sequenceLength)])
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorSequenceRepeating(
        self,
        colorSequence: list[Pixel] = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Sets the color sequence used by light functions.

        Repeats it across the entire light string. If the sequence will not
        fill perfectly when repeated, the virtual LED string is extended until it fits.

        Args:
            colorSequence: list of colors to in the pattern being shifted across the LED string
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorSequenceRepeating.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _colorSequence: np.ndarray[(Any, 3), np.int32] = ArrayPattern.DefaultColorSequenceByMonth()
            # use argument or default
            if colorSequence is not None:
                _colorSequence = [Pixel(p) for p in colorSequence]
            # use argument or default
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            # calculate required virtual LED count to allow for even multiple of this sequence
            _arrayLength: int = np.ceil(self.realLEDCount / len(_colorSequence)) * len(_colorSequence)
            self.backgroundColor = _backgroundColor
            # create color sequence
            self.colorSequence = ArrayPattern.RepeatingColorSequenceArray(
                arrayLength=_arrayLength, colorSequence=_colorSequence
            )
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorTransition(
        self,
        colorSequence: list[Pixel] = None,
        stepsPerTransition: int = None,
        wrap: bool = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Makes a smooth transition from one color to the next over the length specified.

        Args:
            colorSequence: list of colors to transition between
                stepsPerTransition:  how many pixels it takes to
                transition from one color to the next
            stepsPerTransition: number of steps to fade for
            wrap: if true, the last color of the sequence will
                transition to the first color as the final transition
            backgroundColor: the "off" color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransition.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _colorSequence: np.ndarray[(Any, 3), np.int32] = ArrayPattern.DefaultColorSequenceByMonth()
            _stepsPerTransition: int = random.randint(3, 7)
            _wrap: bool = self.getRandomBoolean()
            # set color sequence
            if colorSequence is not None:
                _colorSequence = colorSequence
            # set background color
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            if stepsPerTransition is not None:
                _stepsPerTransition = int(stepsPerTransition)
            if wrap is not None:
                _wrap = bool(wrap)
            self.backgroundColor = _backgroundColor
            self.colorSequence = ArrayPattern.ColorTransitionArray(
                arrayLength=len(_colorSequence) * int(_stepsPerTransition),
                colorSequence=_colorSequence,
                wrap=_wrap,
            )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorTransitionRepeating(
        self,
        colorSequence: list[Pixel] = None,
        stepsPerTransition: int = None,
        wrap: bool = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Makes a smooth transition from one color to the next over the length specified.

        Repeats the sequence as necessary

        Args:
            colorSequence: list of colors to in the pattern being shifted across the LED string
            stepsPerTransition: number of steps per transition
            wrap: wrap
            backgroundColor: off color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorTransitionRepeating.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _colorSequence: np.ndarray[(3, Any), np.int32] = ArrayPattern.DefaultColorSequenceByMonth()
            _stepsPerTransition: int = random.randint(3, 7)
            _wrap: bool = self.getRandomBoolean()
            if colorSequence is not None:
                _colorSequence = [Pixel(p) for p in colorSequence]
            if stepsPerTransition is not None:
                _stepsPerTransition = int(stepsPerTransition)
            if wrap is not None:
                _wrap = bool(wrap)
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            _tempColorSequence: np.ndarray[(3, Any), np.int32] = ArrayPattern.ColorTransitionArray(
                arrayLength=(len(_colorSequence) * _stepsPerTransition),
                colorSequence=_colorSequence,
                wrap=_wrap,
            )
            _arrayLength: int = np.ceil(self.realLEDCount / len(_tempColorSequence)) * len(_tempColorSequence)
            self.backgroundColor = _backgroundColor
            self.colorSequence = ArrayPattern.RepeatingColorSequenceArray(
                arrayLength=_arrayLength, colorSequence=_tempColorSequence
            )
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorRainbow(
        self,
        rainbowPixelCount: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Cycle through the colors of the rainbow.

        Args:
            rainbowPixelCount: when creating the rainbow gradient, make the
                transition through ROYGBIV take this many steps
            backgroundColor: off color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbow.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _rainbowPixelCount: int = random.randint(10, self.realLEDCount // 2)
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            if rainbowPixelCount is not None:
                _rainbowPixelCount = int(rainbowPixelCount)
            self.backgroundColor = _backgroundColor
            self.colorSequence = np.array(ArrayPattern.RainbowArray(arrayLength=_rainbowPixelCount))
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useColorRainbowRepeating(
        self,
        rainbowPixelCount: int = None,
        backgroundColor: Pixel = None,
    ) -> None:
        """Cycle through the colors of the rainbow repeatedly.

        Args:
            rainbowPixelCount: when creating the rainbow gradient, make the
                transition through ROYGBIV take this many steps
            backgroundColor: off color

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorRainbowRepeating.__name__)
        try:
            _backgroundColor: np.ndarray[(3,), np.int32] = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
            _rainbowPixelCount: int = random.randint(10, self.realLEDCount // 2)
            if backgroundColor is not None:
                _backgroundColor = Pixel(backgroundColor).array
            if rainbowPixelCount is not None:
                _rainbowPixelCount = int(rainbowPixelCount)
            _arrayLength: int = np.ceil(self.realLEDCount / _rainbowPixelCount) * _rainbowPixelCount
            self.backgroundColor = _backgroundColor
            self.colorSequence = np.copy(
                ArrayPattern.RepeatingRainbowArray(arrayLength=_arrayLength, segmentLength=_rainbowPixelCount)
            )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionNone(
        self,
    ) -> None:
        """Use the "do nothing" function.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionNone.__name__)
        try:
            # create an object to put in the light data list so we don't just abort the run
            nothing = ArrayFunction(self, ArrayFunction.functionNone, self.colorSequence)
            self.privateLightFunctions.append(nothing)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionSolidColorCycle(
        self,
        delayCount: int = None,
    ) -> None:
        """Set all LEDs to a single color at once, but cycle between entries in a list of colors.

        Args:
            delayCount: number of led updates between color updates

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionSolidColorCycle.__name__)
        try:
            _delayCount: int = random.randint(50, 100)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            cycle: ArrayFunction = ArrayFunction(self, ArrayFunction.functionSolidColorCycle, self.colorSequence)
            # set refresh counter
            cycle.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            cycle.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(cycle)
            # clear LEDs, assign first color in sequence to all LEDs
            self.virtualLEDBuffer *= 0
            self.virtualLEDBuffer += self.colorSequence[0, :]
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionMarquee(
        self,
        shiftAmount: int = None,
        delayCount: int = None,
        initialDirection: int = None,
    ) -> None:
        """Shifts a color pattern across the LED string marquee style.

        Args:
            shiftAmount: the number of pixels the marquee shifts on each update
            delayCount: number of refreshes to delay for each cycle
            initialDirection: a positive or negative value for marquee start direction

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMarquee.__name__)
        try:
            _shiftAmount: int = random.randint(1, 2)
            _delayCount: int = random.randint(0, 6)
            _initialDirection: int = self.getRandomDirection()
            if shiftAmount is not None:
                _shiftAmount = int(shiftAmount)
            if delayCount is not None:
                _delayCount = int(delayCount)
            if initialDirection is not None:
                _initialDirection: int = 1 if (initialDirection >= 1) else -1
            # turn off all LEDs every time so we can turn on new ones
            off: ArrayFunction = ArrayFunction(self, ArrayFunction.functionOff, self.colorSequence)
            # add this function to list
            self.privateLightFunctions.append(off)
            # create tracking object
            marquee: ArrayFunction = ArrayFunction(self, ArrayFunction.functionMarquee, self.colorSequence)
            # store the size of the color sequence being shifted back and forth
            marquee.size = self.colorSequenceCount
            # assign starting direction
            marquee.direction = _initialDirection
            # this is how much the LEDs will move by each time
            marquee.step = _shiftAmount
            # this is how many LED updates will be ignored before doing another LED shift
            marquee.delayCountMax = _delayCount
            # add this function to list
            self.privateLightFunctions.append(marquee)
            # this function just shifts the existing virtual LED buffer,
            # so make sure the virtual LED buffer is initialized here
            if self.colorSequenceCount >= self.virtualLEDCount - 10:
                array = ArrayPattern.SolidColorArray(
                    arrayLength=self.colorSequenceCount + 10, color=PixelColors.OFF.array
                )
                array[: self.colorSequenceCount] = self.colorSequence
                self.setvirtualLEDBuffer(array)
            else:
                self.setvirtualLEDBuffer(self.colorSequence)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionCylon(
        self,
        fadeAmount: int = None,
        delayCount: int = None,
    ) -> None:
        """Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        Args:
            fadeAmount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
            delayCount: number of delays

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionCylon.__name__)
        try:
            _fadeAmount: float = random.randint(5, 75) / 255.0
            _delayCount: int = random.randint(1, 6)
            if fadeAmount is not None:
                _fadeAmount = int(fadeAmount)
            # make sure fade is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if delayCount is not None:
                _delayCount = int(delayCount)
            # fade the whole LED strand
            fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
            # by this amount
            fade.fadeAmount = _fadeAmount
            # add function to list
            self.privateLightFunctions.append(fade)
            # use cylon function
            cylon: ArrayFunction = ArrayFunction(self, ArrayFunction.functionCylon, self.colorSequence)
            # shift eye by this much for each update
            cylon.size = self.colorSequenceCount
            # adjust virtual LED buffer if necessary so that the cylon can actually move
            if self.virtualLEDCount < cylon.size:
                array = ArrayPattern.SolidColorArray(arrayLength=cylon.size + 3, color=PixelColors.OFF.array)
                array[: self.virtualLEDCount] = self.virtualLEDBuffer
                self.setvirtualLEDBuffer(array)
            # set start and next indices
            cylon.index = self.virtualLEDCount - cylon.size - 3
            cylon.indexNext = cylon.index
            # set delay
            cylon.delayCounter = _delayCount
            cylon.delayCountMax = _delayCount
            # add function to function list
            self.privateLightFunctions.append(cylon)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionMerge(
        self,
        shiftAmount: int = None,
        delayCount: int = None,
    ) -> None:
        """Reflect a color sequence and shift the reflections toward each other in the middle.

        Args:
            shiftAmount: amount the merge will shift in each update
            delayCount: length of reflected segments

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMerge.__name__)
        try:
            _delayCount: int = random.randint(6, 12)
            _shiftAmount: int = 1
            if delayCount is not None:
                _delayCount = int(delayCount)
            if shiftAmount is not None:
                _shiftAmount = int(shiftAmount)
            # make sure doing a merge function would be visible
            if self.colorSequenceCount >= self.realLEDCount:
                # if sequence is too long, cut it in half
                self.colorSequence = self.colorSequence[: int(self.colorSequenceCount // 2)]
                # don't remember offhand why this is here
                if self.colorSequenceCount % 2 == 1:
                    if self.colorSequenceCount == 1:
                        self.colorSequence = np.concatenate(self.colorSequence, self.colorSequence)
                    else:
                        self.colorSequence = self.colorSequence[:-1]
            # calculate modulo length
            _arrayLength = np.ceil(self.realLEDCount / self.colorSequenceCount) * self.colorSequenceCount
            # update LED buffer with any changes we had to make
            self.setvirtualLEDBuffer(
                ArrayPattern.ReflectArray(
                    arrayLength=_arrayLength,
                    colorSequence=self.colorSequence,
                    foldLength=self.colorSequenceCount,
                )
            )
            # create tracking object
            merge: ArrayFunction = ArrayFunction(self, ArrayFunction.functionMerge, self.colorSequence)
            # set merge size
            merge.size = self.colorSequenceCount
            # set shift amount
            merge.step = _shiftAmount
            # set the number of LED refreshes to skip
            merge.delayCountMax = _delayCount
            # add function to list
            self.privateLightFunctions.append(merge)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionAccelerate(
        self,
        delayCountMax: int = None,
        stepCountMax: int = None,
        fadeAmount: float = None,
        cycleColors: bool = None,
    ) -> None:
        """Shifts a color pattern across the LED string accelerating as it goes.

        Args:
            delayCountMax: max delay between color updates
            stepCountMax: speed limit
            fadeAmount: speed of color fade
            cycleColors: set true to cycle as the LED goes across

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionAccelerate.__name__)
        try:
            _delayCountMax: int = random.randint(5, 10)
            _stepCountMax: int = random.randint(4, 10)
            _fadeAmount: float = random.randint(15, 35) / 255.0
            _cycleColors: bool = self.getRandomBoolean()
            if delayCountMax is not None:
                _delayCountMax = int(delayCountMax)
            if stepCountMax is not None:
                _stepCountMax = int(stepCountMax)
            if fadeAmount is not None:
                _fadeAmount = float(fadeAmount)
            # make sure fade amount is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if cycleColors is not None:
                _cycleColors = bool(cycleColors)
            # we want comet trails, so fade the buffer each time through
            fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.privateLightFunctions.append(fade)
            # create tracking object
            accelerate: ArrayFunction = ArrayFunction(self, ArrayFunction.functionAccelerate, self.colorSequence)
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
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionRandomChange(
        self,
        delayCount: int = None,
        changeCount: int = None,
        fadeStepCount: int = None,
        fadeType: LEDFadeType = None,
    ) -> None:
        """Randomly changes pixels from one color to the next.

        Args:
            delayCount: refresh delay
            changeCount: how many LEDs to have in the change queue at once
            fadeStepCount: number of steps in the transition from one color to the next
            fadeType: set to fade colors, or instant on/off

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionRandomChange.__name__)
        try:
            _changeCount: int = random.randint(self.virtualLEDCount // 5, self.virtualLEDCount)
            _fadeStepCount: int = random.randint(5, 20)
            _delayCountMax: int = random.randint(30, 50)
            fadeTypes: list[LEDFadeType] = list(LEDFadeType)
            _fadeType: LEDFadeType = fadeTypes[random.randint(0, len(fadeTypes) - 1)]
            if changeCount is not None:
                _changeCount = int(changeCount)
            if fadeStepCount is not None:
                _fadeStepCount = int(fadeStepCount)
            _fadeAmount: float = _fadeStepCount / 255.0
            # make sure fade amount is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if delayCount is not None:
                _delayCountMax = int(delayCount)
            if fadeType is not None:
                _fadeType = LEDFadeType(fadeType)
            # make comet trails
            if _fadeType == LEDFadeType.FADE_OFF:
                fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
                fade.fadeAmount = _fadeAmount
                self.privateLightFunctions.append(fade)
            elif _fadeType == LEDFadeType.INSTANT_OFF:
                off: ArrayFunction = ArrayFunction(self, ArrayFunction.functionOff, self.colorSequence)
                self.privateLightFunctions.append(off)
            else:
                # do nothing
                pass
            # create a bunch of tracking objects
            for index in self.getRandomIndices(int(_changeCount)):
                if index < self.virtualLEDCount:
                    change: ArrayFunction = ArrayFunction(self, ArrayFunction.functionRandomChange, self.colorSequence)
                    # set the index from our random number
                    change.index = int(index)
                    # set the fade to off amount
                    change.fadeAmount = _fadeAmount
                    # this is used to help calculate fade duration in the function
                    change.stepCountMax = _fadeStepCount
                    # copy the current color of this LED index
                    # change.color = np.copy(self.virtualLEDBuffer[change.index])
                    if len(ArrayFunction.Controller.virtualLEDBuffer.shape) == 2:
                        change.color = np.copy(self.virtualLEDBuffer[change.index])
                        # ArrayFunction.Controller.virtualLEDBuffer[accelerate.indexRange] = meteor.color
                    else:
                        change.color = ArrayFunction.Controller.virtualLEDBuffer[
                            np.where(ArrayFunction.Controller.virtualLEDIndexBuffer == change.index)
                        ]
                    # randomly set the color we are fading toward
                    if random.randint(0, 1) == 1:
                        change.colorNext = self.colorSequenceNext
                    else:
                        change.colorNext = change.color
                    # set the refresh delay
                    change.delayCountMax = _delayCountMax
                    # we want all the delays random, so don't start them all at zero
                    change.delayCounter = random.randint(0, change.delayCountMax)
                    # set true to fade, false to "instant on/off"
                    change.fadeType = _fadeType
                    # add function to list
                    self.privateLightFunctions.append(change)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionMeteors(
        self,
        fadeAmount: int = None,
        maxSpeed: int = None,
        explode: bool = True,
        meteorCount: int = None,
        collide: bool = None,
        cycleColors: bool = None,
        delayCount: int = None,
        fadeType: LEDFadeType = None,
    ) -> None:
        """Creates several 'meteors' that will fly around.

        Args:
            fadeAmount: the amount by which meteors are faded
            maxSpeed: the amount be which the meteor moves each refresh
            explode: if True, the meteors will light up in an explosion when they collide
            meteorCount: number of meteors
            collide: set true to make them bounce off each other randomly
            cycleColors: set true to make the meteors shift color as they move
            delayCount: refresh delay
            fadeType: set the type of fade to use using the enumeration

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMeteors.__name__)
        try:
            _fadeAmount: float = random.randint(20, 40) / 100.0
            _explode: bool = self.getRandomBoolean()
            _maxSpeed: int = random.randint(1, 3)
            _delayCount: int = random.randint(1, 3)
            _meteorCount: int = random.randint(2, 6)
            _collide: bool = self.getRandomBoolean()
            _cycleColors: bool = self.getRandomBoolean()
            fadeTypes: list[LEDFadeType] = list(LEDFadeType)
            _fadeType: LEDFadeType = fadeTypes[random.randint(0, len(fadeTypes) - 1)]
            if self.colorSequenceCount >= 2 and self.colorSequenceCount <= 6:
                _meteorCount = self.colorSequenceCount
            if fadeAmount is not None:
                _fadeAmount = float(fadeAmount)
            # make sure fade amount is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if explode is not None:
                _explode = bool(explode)
            if maxSpeed is not None:
                _maxSpeed = int(maxSpeed)
            if delayCount is not None:
                _delayCount = int(delayCount)
            if meteorCount is not None:
                _meteorCount = int(meteorCount)
            if collide is not None:
                _collide = bool(collide)
            if cycleColors is not None:
                _cycleColors = bool(cycleColors)
            if fadeType is not None:
                _fadeType = LEDFadeType(fadeType)
            # make comet trails
            if _fadeType == LEDFadeType.FADE_OFF:
                fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
                fade.fadeAmount = _fadeAmount
                self.privateLightFunctions.append(fade)
            elif _fadeType == LEDFadeType.INSTANT_OFF:
                off: ArrayFunction = ArrayFunction(self, ArrayFunction.functionOff, self.colorSequence)
                self.privateLightFunctions.append(off)
            else:
                # do nothing
                pass
            for _ in range(_meteorCount):
                meteor: ArrayFunction = ArrayFunction(self, ArrayFunction.functionMeteors, self.colorSequence)
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
                # add function to list
                self.privateLightFunctions.append(meteor)
            # make sure there are at least two going to collide
            if self.privateLightFunctions[0].direction * self.privateLightFunctions[1].direction > 0:
                self.privateLightFunctions[1].direction *= -1
            # this object calculates collisions between other objects based on index and previous/next index
            if _collide is True:
                collision = ArrayFunction(self, ArrayFunction.functionCollisionDetection, self.colorSequence)
                collision.explode = _explode
                self.privateLightFunctions.append(collision)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionSprites(
        self,
        fadeSteps: int = None,
    ) -> None:
        """Meteors fade in and out in short bursts of random length and direction.

        Args:
            fadeSteps: amount to fade

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionSprites.__name__)
        try:
            _fadeSteps: int = random.randint(1, 6)
            if fadeSteps is not None:
                _fadeSteps = int(fadeSteps)
            _fadeAmount = np.ceil(255 / _fadeSteps)
            # make sure fade amount is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            for _ in range(max(min(self.colorSequenceCount, 10), 2)):
                sprite: ArrayFunction = ArrayFunction(self, ArrayFunction.functionSprites, self.colorSequence)
                # randomize index
                sprite.index = random.randint(0, self.virtualLEDCount - 1)
                # initialize previous index
                sprite.indexPrevious = sprite.index
                # randomize direction
                sprite.direction = self.getRandomDirection()
                # assign the target color
                sprite.colorGoal = self.colorSequenceNext
                # initialize sprite to
                sprite.color = ArrayPattern.DEFAULT_BACKGROUND_COLOR.array
                # copy color sequence
                sprite.colorSequence = self.colorSequence
                # set next color
                sprite.colorNext = PixelColors.OFF.array
                # set fade step/amount
                sprite.fadeSteps = _fadeSteps
                sprite.fadeAmount = _fadeAmount
                sprite.state = SpriteState.OFF.value
                self.privateLightFunctions.append(sprite)
            # set one sprite to "fading on"
            self.privateLightFunctions[0].state = SpriteState.FADING_ON.value
            # add LED fading for comet trails
            fade = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.privateLightFunctions.append(fade)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionRaindrops(
        self,
        maxSize: int = None,
        raindropChance: float = None,
        stepSize: int = None,
        maxRaindrops: int = None,
        fadeAmount: float = None,
    ):
        """Cause random "splashes" across the LED strand.

        Args:
            maxSize: max splash size
            raindropChance: chance of raindrop
            stepSize: splash speed
            maxRaindrops: number of raindrops
            fadeAmount: amount to fade LED each refresh

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionRaindrops.__name__)
        try:
            _maxSize: int = random.randint(2, int(self.virtualLEDCount // 8))
            _raindropChance: float = random.uniform(0.005, 0.1)
            _stepSize: int = random.randint(2, 5)
            _fadeAmount: float = random.uniform(0.25, 0.65)
            _maxRaindrops: int = max(min(self.colorSequenceCount, 10), 2)
            if maxSize is not None:
                _maxSize = int(maxSize)
                _fadeAmount = ((255 / _maxSize) / 255) * 2
            if raindropChance is not None:
                _raindropChance = float(raindropChance)
            if stepSize is not None:
                _stepSize = int(stepSize)
            if _stepSize > 3:
                _raindropChance /= 3.0
            if fadeAmount is not None:
                _fadeAmount = float(fadeAmount)
            # make sure fade amount is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if maxRaindrops is not None:
                _maxRaindrops = int(maxRaindrops)
            for _ in range(_maxRaindrops):
                raindrop: ArrayFunction = ArrayFunction(self, ArrayFunction.functionRaindrops, self.colorSequence)
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
                # assign color
                raindrop.color = self.colorSequenceNext
                raindrop.colorSequence = self.colorSequence
                raindrop.fadeAmount = _fadeAmount
                # set raindrop to be inactive initially
                raindrop.state = RaindropStates.OFF.value
                self.privateLightFunctions.append(raindrop)
            # set first raindrop active
            self.privateLightFunctions[0].state = RaindropStates.SPLASH.value
            # add fading
            fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.privateLightFunctions.append(fade)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useFunctionAlive(
        self,
        fadeAmount: float = None,
        sizeMax: int = None,
        stepCountMax: int = None,
        stepSizeMax: int = None,
    ) -> None:
        """Use the function that uses a series of behaviors that move around in odd ways.

        Args:
            fadeAmount: amount of fade
            sizeMax: max size of LED pattern
            stepCountMax: max duration of effect
            stepSizeMax: max speed

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionAlive.__name__)
        try:
            _fadeAmount: float = random.uniform(0.20, 0.75)
            _sizeMax: int = random.randint(self.virtualLEDCount // 6, self.virtualLEDCount // 3)
            _stepCountMax: int = random.randint(self.virtualLEDCount // 10, self.virtualLEDCount)
            _stepSizeMax: int = random.randint(6, 10)
            if fadeAmount is not None:
                _fadeAmount = float(fadeAmount)
            # make sure fade amount is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if sizeMax is not None:
                _sizeMax = int(sizeMax)
            if stepCountMax is not None:
                _stepCountMax = int(stepCountMax)
            if stepSizeMax is not None:
                _stepSizeMax = int(stepSizeMax)
            for _ in range(random.randint(2, 5)):
                thing: ArrayFunction = ArrayFunction(self, ArrayFunction.functionAlive, self.colorSequence)
                # randomize start index
                thing.index = self.getRandomIndex()
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
                thing.size = random.randint(1, int(_sizeMax // 2))
                # set max size
                thing.sizeMax = _sizeMax
                # start the state at 1
                thing.state = ThingMoves.METEOR.value
                # calculate random next state immediately
                thing.stepCounter = 1000
                thing.delayCounter = 1000
                self.privateLightFunctions.append(thing)
            self.privateLightFunctions[0].active = True
            # add a fade
            fade = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
            fade.fadeAmount = _fadeAmount
            self.privateLightFunctions.append(fade)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useOverlayTwinkle(
        self,
        twinkleChance: float = None,
        colorSequence: np.ndarray[(3, Any), np.int32] = None,
    ) -> None:
        """Randomly sets some lights to 'twinkleColor' temporarily.

        Args:
            twinkleChance: chance of a twinkle
            colorSequence: the list of colors to be used when briefly flashing an LED

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useOverlayTwinkle.__name__)
        try:
            _twinkleChance: float = random.uniform(0.991, 0.995)
            _colorSequence = self.colorSequence.copy()
            if twinkleChance is not None:
                _twinkleChance = float(twinkleChance)
            if colorSequence is not None:
                _colorSequence = colorSequence
            twinkle: ArrayFunction = ArrayFunction(self, ArrayFunction.overlayTwinkle, _colorSequence)
            twinkle.random = _twinkleChance
            self.privateLightFunctions.append(twinkle)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def useOverlayBlink(
        self,
        blinkChance: float = None,
    ) -> None:
        """Use the overlay that causes all LEDs to light up the same color at once.

        Args:
            blinkChance: chance of a blink

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useOverlayBlink.__name__)
        try:
            _blinkChance: float = random.uniform(0.991, 0.995)
            if blinkChance is not None:
                _blinkChance = float(blinkChance)
            blink: ArrayFunction = ArrayFunction(self, ArrayFunction.overlayBlink, self.colorSequence)
            blink.random = _blinkChance
            blink.colorSequence = self.colorSequence
            self.privateLightFunctions.append(blink)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerException from ex

    def demo(
        self,
        secondsPerMode: float = 0.5,
        functionNames: list[str] = None,
        colorNames: list[str] = None,
        skipFunctions: list[str] = None,
        skipColors: list[str] = None,
    ):
        """Run colors and functions semi-randomly.

        Args:
            secondsPerMode: seconds to run current function
            functionNames: function names to run
            colorNames: color pattern names to run
            skipFunctions: function strings to omit (run if "skipFunction not in name")
            skipColors: color pattern strings to omit (run if "skipColor not in name")

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            _secondsPerMode: int = 60
            if secondsPerMode is not None:
                _secondsPerMode = int(secondsPerMode)
            self.secondsPerMode = _secondsPerMode

            if functionNames is None:
                functionNames = []
            elif not isinstance(functionNames, list):
                functionNames = [functionNames]
            if colorNames is None:
                colorNames = []
            elif not isinstance(colorNames, list):
                colorNames = [colorNames]
            if skipFunctions is None:
                skipFunctions = []
            elif not isinstance(skipFunctions, list):
                skipFunctions = [skipFunctions]
            if skipColors is None:
                skipColors = []
            elif not isinstance(skipColors, list):
                skipColors = [skipColors]

            functions = self.getFunctionMethodsList()
            colors = self.getColorMethodsList()
            # get methods that match user's string
            if len(functionNames) > 0:
                matches = []
                for name in functionNames:
                    matches.extend([f for f in functions if name.lower() in f.lower()])
                functions = matches
            # get methods that match user's string
            if len(colorNames) > 0:
                matches = []
                for name in colorNames:
                    matches.extend([f for f in colors if name.lower() in f.lower()])
                colors = matches
            # remove methods that user requested
            if len(skipFunctions) > 0:
                matches = []
                for name in skipFunctions:
                    for function in functions:
                        if name.lower() in function.lower():
                            functions.remove(function)
            # remove methods that user requested
            if len(skipColors) > 0:
                matches = []
                for name in skipColors:
                    for color in colors:
                        if name.lower() in color.lower():
                            colors.remove(color)

            if len(functions) == 0:
                raise ControllerException("No functions selected in demo")
            elif len(colors) == 0:
                raise ControllerException("No colors selected in demo")
            else:
                while True:
                    try:
                        # make a temporary copy (so we can go through each one)
                        functionsCopy = functions.copy()
                        colorsCopy = colors.copy()
                        # loop while we still have a color and a function
                        while (len(functionsCopy) * len(colorsCopy)) > 0:
                            # get a new function if there is one
                            if len(functionsCopy) > 0:
                                function = functionsCopy[random.randint(0, len(functionsCopy) - 1)]
                                functionsCopy.remove(function)
                            # get a new color pattern if there is one
                            if len(colorsCopy) > 0:
                                color = colorsCopy[random.randint(0, len(colorsCopy) - 1)]
                                colorsCopy.remove(color)
                            # reset
                            self.reset()
                            # apply color
                            getattr(self, color)()
                            # configure function
                            getattr(self, function)()
                            # run the combination
                            self.run()
                    except SystemExit:  # pragma: no cover
                        raise
                    except KeyboardInterrupt:  # pragma: no cover
                        raise
                    except Exception as ex:  # pragma: no cover
                        LOGGER.exception(
                            "%s.%s Exception: %s",
                            self.__class__.__name__,
                            self.demo.__name__,
                            ex,
                        )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.demo.__name__,
                ex,
            )
            raise ControllerException from ex
