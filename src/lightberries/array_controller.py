"""Class defines methods for interacting with Light Strings, Patterns, and Functions."""

from __future__ import annotations

import logging
import random
import time
from math import ceil
from typing import Any, Callable

import numpy as np

from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import (
    ControllerError,
    LightBerryError,
    PermissionsError,
    WS281xStringError,
)
from lightberries.light_sequences.base import ArraySequence
from lightberries.pixel import Pixel, PixelColors
from lightberries.state import LEDFadeType, RaindropStates, SpriteState, ThingMoves
from lightberries.ws281x_strings import WS281xString

LOGGER = logging.getLogger("lightBerries")
DEFAULT_REFRESH_DELAY = 50


class ArrayController:
    """Library wraps the rpi_ws281x library and provides some lighting functions.

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
        led_count: int = 100,
        pwm_gpio_pin: int = 18,
        dma_channel: int = 10,
        pwm_frequency: int = 800000,
        led_brightness: float = 0.75,
        pwm_channel: int = 0,
        led_strip_type: Any = None,
        gamma: Any = None,
        refresh_callback: Callable = None,
        *,
        pwm_invert_signal: bool = False,
        debug: bool = False,
        verbose: bool = False,
        simulate: bool = False,
        testing: bool = False,
    ) -> None:
        """Create a LightArrayController object for running patterns across a rpi_ws281x LED string.

        Args:
        ----
            led_count: the number of Pixels in your string of LEDs
            pwm_gpio_pin: the GPIO pin number your lights are hooked up to
                (18 is a good choice since it does PWM)
            dma_channel: the DMA channel to use (5 is a good option)
            pwm_frequency: try 800,000
            pwm_invert_signal: set true to invert the PWM signal
            led_brightness: set to a value between 0.0 (OFF), and 1.0 (ON).
                    This setting tends to introduce flicker the lower it is
            pwm_channel: defaults to 0, see https://github.com/rpi-ws281x/rpi-ws281x-python
            led_strip_type: see https://github.com/rpi-ws281x/rpi-ws281x-python
            gamma: see https://github.com/rpi-ws281x/rpi-ws281x-python
            debug: set true for some debugging messages
            verbose: set true for even more information
            refresh_callback: callback method is called whenever new LED values are sent to LED string
            simulate: only call refreshCallback, don't use GPIO

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            # configure logging
            if debug is True or verbose is True:
                if not LOGGER.handlers:
                    stream_handler = logging.StreamHandler()
                    LOGGER.addHandler(stream_handler)
                LOGGER.setLevel(logging.INFO)
                # if sys.platform != "linux":
                #     fh = logging.FileHandler(__name__ + ".log")
                # else:
                #     fh = logging.FileHandler("/home/pi/" + __name__ + ".log")  # pragma: no cover
                # fh.setLevel(logging.DEBUG)
                # LOGGER.addHandler(fh)
                LOGGER.setLevel(logging.DEBUG)
            if verbose is True:
                LOGGER.setLevel(5)
            self.simulate = simulate
            # wrap pixel strip in my own interface object
            self._instantiate_WS281xString(
                led_count=led_count,
                pwm_gpio_pin=pwm_gpio_pin,
                dma_channel=dma_channel,
                pwm_frequency=pwm_frequency,
                pwm_invert_signal=pwm_invert_signal,
                led_brightness=led_brightness,
                pwm_channel=pwm_channel,
                led_strip_type=led_strip_type,
                gamma=gamma,
                simulate=simulate,
                testing=testing,
            )

            # initialize instance variables
            self._led_count: int = len(self.ws281xString)
            self.virtual_led_buffer: np.ndarray[(3, Any), np.int32] = ArraySequence.SolidSequence(
                arrayLength=self._led_count,
                color=PixelColors.OFF.array,
            )
            self.virtual_led_index_buffer: np.ndarray[(Any,), np.int32] = np.array(
                range(len(self.ws281xString)),
            )
            self._overlay_dict: dict[int, np.ndarray[(3,), np.int32]] = {}
            self._virtual_led_count: int = len(self.virtual_led_buffer)
            self._virtual_led_index_count: int = len(self.virtual_led_index_buffer)
            self._last_mode_change: float = time.time() - 1000
            self._next_mode_change: float = time.time()
            self._refresh_delay: float = 0.001
            self._seconds_per_mode: float = 120.0
            self._background_color: np.ndarray[(3,), np.int32] = PixelColors.OFF.array
            self._color_sequence: np.ndarray[(3, Any), np.int32] = ArraySequence.default_color_sequence_by_month()
            self._color_sequence_count: int = len(self._color_sequence)
            self._color_sequence_index: int = 0
            self._loop_forever: bool = False
            self._transforms: list[ArrayTransform] = []

            # # give LightFunction class a pointer to this class
            # ArrayTransform.Controller = self

            self.running: bool = False
            self.refreshCallback: Callable = refresh_callback
            # initialize stuff
            self.reset()
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def _instantiate_WS281xString(
        self,
        led_count: int,
        pwm_gpio_pin: int,
        dma_channel: int,
        pwm_frequency: int,
        pwm_invert_signal: bool,
        led_brightness: float,
        pwm_channel: int,
        led_strip_type: Any,
        gamma: Any,
        simulate: bool,
        testing: bool = False,
    ) -> None:
        self.ws281xString: WS281xString | None = WS281xString(
            led_count=led_count,
            pwm_gpio_pin=pwm_gpio_pin,
            dma_channel=dma_channel,
            pwm_frequency=pwm_frequency,
            pwm_invert_signal=pwm_invert_signal,
            led_brightness=led_brightness,
            pwm_channel=pwm_channel,
            led_strip_type=led_strip_type,
            led_gamma=gamma,
            simulate=simulate,
            testing=testing,
        )

    def __del__(
        self,
    ) -> None:
        """Disposes of the rpi_ws281x object (if it exists) to prevent memory leaks.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            if hasattr(self, "ws281xString") and self.ws281xString is not None:
                self.off()
                self.copy_virtual_leds_to_ws281x()
                self.refresh_leds()
                self.ws281xString.__del__()
                self.ws281xString = None
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except PermissionsError:
            raise
        except WS281xStringError:
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError(
                "Failed to clean up LightBerries ArrayController",
            ) from ex

    @property
    def virtual_led_count(self) -> int:
        """The number of virtual LEDs. These include ones that won't display.

        Returns
        -------
            the number of virtual LEDs

        """
        return self._virtual_led_count

    @property
    def real_led_count(self) -> int:
        """The number of LEDs in the LED string.

        Returns
        -------
            the number of actual LEDs in the string (as configured)

        """
        return self._led_count

    @property
    def refresh_delay(
        self,
    ) -> float:
        """The delay between starting LED refreshes.

        Returns
        -------
            the delay between refreshes

        """
        return self._refresh_delay

    @refresh_delay.setter
    def refresh_delay(
        self,
        delay: float,
    ) -> None:
        """Set the refresh delay.

        Args:
        ----
            delay: the delay in seconds

        """
        self._refresh_delay = float(delay)

    @property
    def background_color(
        self,
    ) -> np.ndarray[(3,), np.int32]:
        """The defined background, or "Off" color for the LED string.

        Returns
        -------
            the rgb value

        """
        return self._background_color

    @background_color.setter
    def background_color(
        self,
        color: np.ndarray[(3,), np.int32],
    ) -> None:
        """Set the background color.

        Args:
        ----
            color: an RGB value

        """
        self._background_color = Pixel(color).array

    @property
    def seconds_per_mode(
        self,
    ) -> float:
        """The number of seconds to run the configuration.

        Returns
        -------
            the seconds to run the current configuration

        """
        return self._seconds_per_mode

    @seconds_per_mode.setter
    def seconds_per_mode(
        self,
        seconds: float,
    ) -> None:
        """Set the seconds per mode.

        Args:
        ----
            seconds: the number of seconds

        """
        self._seconds_per_mode = float(seconds)

    @property
    def color_sequence(
        self,
    ) -> np.ndarray[(3, Any), np.int32]:
        """The sequence of RGB values to use for generating patterns when using the functions.

        Returns
        -------
            the sequence of RGB values

        """
        return self._color_sequence

    @color_sequence.setter
    def color_sequence(
        self,
        color_sequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Set the color sequence.

        Args:
        ----
            color_sequence: the sequence of RGB values

        """
        self._color_sequence = np.copy(
            ArraySequence.ArrayPattern.pixel_array_to_numpy_array(color_sequence),
        )
        self.color_sequence_count = len(self._color_sequence)
        self.color_sequence_index = 0

    @property
    def color_sequence_count(
        self,
    ) -> int:
        """The number of colors in the defined sequence.

        Returns
        -------
            the number of LEDs in the sequence

        """
        return self._color_sequence_count

    @color_sequence_count.setter
    def color_sequence_count(
        self,
        color_sequence_count: int,
    ) -> None:
        """Set the Color sequence count.

        Args:
        ----
            color_sequence_count: the number of colors in the sequence

        """
        self._color_sequence_count = color_sequence_count

    @property
    def color_sequence_index(
        self,
    ) -> int:
        """The index we are on in the current color sequence.

        Returns
        -------
            the current index into the color sequence

        """
        return self._color_sequence_index

    @color_sequence_index.setter
    def color_sequence_index(
        self,
        color_sequence_index: int,
    ) -> None:
        """Set the color sequence index.

        Args:
        ----
            colorSequenceIndex: the new index

        """
        if color_sequence_index >= len(self.color_sequence):
            self._color_sequence_index = 0
        else:
            self._color_sequence_index = color_sequence_index

    @property
    def color_sequence_next(
        self,
    ) -> np.ndarray[(3,), np.int32]:
        """Get the next color in the sequence.

        Returns
        -------
            the next RGB value

        """
        temp = self.color_sequence[self.color_sequence_index]
        self.color_sequence_index += 1
        return temp

    @property
    def function_list(self) -> list[ArrayTransform]:
        """The list of function objects that will be used to modify the light pattern.

        Returns
        -------
            the list of functions

        """
        return self._transforms

    @property
    def overlay_dictionary(self) -> dict[int, Any]:
        """The list of indices and associated colors to temporarily assign LEDs.

        Returns
        -------
            the dictionary of LEDs and values

        """
        return self._overlay_dict

    def get_color_methods_list(self) -> list[str]:
        """Get the list of methods in this class (by name) that set the color sequence.

        Returns
        -------
            a list of method name strings

        """
        attrs = list(dir(self))
        colors = [c for c in attrs if c[:8] == "useColor"]
        colors.sort()
        return colors

    def get_function_methods_list(self) -> list[str]:
        """Get the list of methods in this class (by name) that set the color functions.

        Returns
        -------
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

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.reset.__name__)
            self._transforms = []
            if self.virtual_led_count >= self.real_led_count:
                self.set_virtual_led_buffer(self.virtual_led_buffer[: self.real_led_count])
            elif self.virtual_led_count < self.real_led_count:
                array = ArraySequence.SolidSequence(
                    arrayLength=self.real_led_count,
                    color=PixelColors.OFF.array,
                )
                self.set_virtual_led_buffer(array)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def set_virtual_led_buffer(
        self,
        led_buffer: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Assign a sequence of pixel data to the LED.

        Args:
        ----
            led_buffer: array of RGB values

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            # make sure the passed LED array is the correct type
            _led_buffer = led_buffer
            _led_buffer_length = int(_led_buffer.size / 3)

            # check assignment length
            if (
                _led_buffer_length >= self.real_led_count
                or len(_led_buffer.shape) > 2
                or len(self.virtual_led_buffer.shape) > 2
            ):
                self.virtual_led_buffer = _led_buffer
            else:
                self.virtual_led_buffer[:_led_buffer_length] = _led_buffer

            # assign new LED array to virtual LEDs
            self._virtual_led_count = _led_buffer_length
            # set our indices for virtual LEDs
            self._virtual_led_index_count = self.virtual_led_count
            # create array of index values for manipulation if needed
            self.virtual_led_index_buffer = np.arange(self.virtual_led_count)
            # if the array is smaller than the actual light strand, make our entire strand addressable
            if self._virtual_led_index_count < self.real_led_count and len(self.virtual_led_buffer.shape) < 3:
                self._virtual_led_index_count = self.real_led_count
                self.virtual_led_index_buffer = np.arange(self._virtual_led_index_count)
                self.virtual_led_buffer = np.concatenate(
                    (
                        self.virtual_led_buffer,
                        np.array(
                            [PixelColors.OFF.tuple for i in range(self.real_led_count - self.virtual_led_count)],
                        ),
                    ),
                )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def copy_virtual_leds_to_ws281x(
        self,
    ) -> None:
        """Set each Pixel in the rpi_ws281x object to the buffered array value.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        # callback function to do work

        def set_pixel(i_rgb: tuple[int]) -> None:
            """Set pixel value in ws281x object.

            Args:
            ----
                i_rgb: pixel color value and gamma

            """
            self.ws281xString[i_rgb[0]] = i_rgb[1]

        # fast method of calling the callback method on each index of LED array
        list(
            map(
                set_pixel,
                enumerate(
                    self.virtual_led_buffer[self.virtual_led_index_buffer][
                        np.where(self.virtual_led_index_buffer < self.real_led_count)
                    ],
                ),
            ),
        )

    def refresh_leds(
        self,
    ) -> None:
        """Display current LED buffer.

        Raises
        ------
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
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def off(
        self,
    ) -> None:
        """Set all Pixels to RGD background color.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            # clear all current values
            self.virtual_led_buffer *= 0
            # set to background color
            self.virtual_led_buffer[:] += self.background_color
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def _run_functions(
        self,
    ) -> None:
        """Run each function in the configured function list.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            # invoke the function pointer saved in the light data object
            for function in self._transforms:
                function.transform()
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def _copy_overlays(
        self,
    ) -> None:
        """Copy overlays directly to output array, bypassing the buffer.

        Raises
        ------
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
            for index, led_value in self._overlay_dict.items():
                self.ws281xString[index] = led_value
            self._overlay_dict = {}
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def fade_color(
        self,
        color: np.ndarray[(3,), np.int32],
        color_next: np.ndarray[(3,), np.int32],
        fade_amount: float,
    ) -> np.ndarray[(3,), np.int32]:
        """Fade an LED's color by the given amount and return the new RGB value.

        Args:
        ----
            color: current color
            colorNext: desired color
            fadeCount: amount to adjust each RGB value by

        Returns:
        -------
            new RGB value

        """
        # copy it to make sure we don't change the original by reference
        _color: np.ndarray[(3,), np.int32] = np.copy(color)
        _fadeAmount = ceil(fade_amount * 256)
        if _fadeAmount < 0:
            _fadeAmount = 1
        elif _fadeAmount > 255:
            _fadeAmount = 255
        # loop through RGB values
        for rgbIndex in range(len(_color)):
            # the values closest to the target color might match already
            if _color[rgbIndex] != color_next[rgbIndex]:
                # subtract or add as appropriate in order to get closer to target color
                if _color[rgbIndex] - _fadeAmount > color_next[rgbIndex]:
                    _color[rgbIndex] -= _fadeAmount
                elif _color[rgbIndex] + _fadeAmount < color_next[rgbIndex]:
                    _color[rgbIndex] += _fadeAmount
                else:
                    _color[rgbIndex] = color_next[rgbIndex]
        return _color

    def run(self):
        """Run the configured color pattern and function either forever or for self.secondsPerMode.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.run.__name__)
            # set start time
            self._last_mode_change = time.time()
            # set a target time to change
            if self.seconds_per_mode is None:
                self._next_mode_change = self._last_mode_change + (random.uniform(30, 120))
            else:
                self._next_mode_change = self._last_mode_change + (self.seconds_per_mode)
            # loop
            self.running = True
            while (time.time() < self._next_mode_change and self.running is True) or self._loop_forever:
                try:
                    # run the selected functions using LightFunction object callbacks
                    self._run_functions()
                    # copy the resulting RGB values to the ws28xx LED buffer
                    self.copy_virtual_leds_to_ws281x()
                    # copy temporary changes (not buffered in this class) to the ws28xx LED buffer
                    self._copy_overlays()
                    # tell the ws28xx controller to transmit the new data
                    self.refresh_leds()
                except KeyboardInterrupt:  # pragma: no cover
                    raise
                except SystemExit:  # pragma: no cover
                    raise
                except LightBerryError:  # pragma: no cover
                    raise
                except Exception as ex:  # pragma: no cover
                    raise ControllerError from ex
            self._last_mode_change = time.time()
            if self.seconds_per_mode is None:
                self._next_mode_change = self._last_mode_change + (random.random(30, 120))
            else:
                self._next_mode_change = self._last_mode_change + (self.seconds_per_mode)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.run.__name__,
                ex,
            )
            raise ControllerError from ex

    def useFunctionCylon(
        self,
        fadeAmount: int = None,
        delayCount: int = None,
    ) -> None:
        """Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        Args:
        ----
            fadeAmount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
            delayCount: number of delays

        Raises:
        ------
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
            fade: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionFadeOff,
                self.color_sequence,
            )
            # by this amount
            fade._fade_amount = _fadeAmount
            # add function to list
            self._transforms.append(fade)
            # use cylon function
            cylon: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionCylon,
                self.color_sequence,
            )
            # shift eye by this much for each update
            cylon._size = self.color_sequence_count
            # adjust virtual LED buffer if necessary so that the cylon can actually move
            if self.virtual_led_count < cylon._size:
                array = ArraySequence.SolidSequence(
                    arrayLength=cylon._size + 3,
                    color=PixelColors.OFF.array,
                )
                array[: self.virtual_led_count] = self.virtual_led_buffer
                self.set_virtual_led_buffer(array)
            # set start and next indices
            cylon._index = self.virtual_led_count - cylon._size - 3
            cylon._index_next = cylon._index
            # set delay
            cylon._delay_counter = _delayCount
            cylon._delay_count_max = _delayCount
            # add function to function list
            self._transforms.append(cylon)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def useFunctionMerge(
        self,
        shiftAmount: int = None,
        delayCount: int = None,
    ) -> None:
        """Reflect a color sequence and shift the reflections toward each other in the middle.

        Args:
        ----
            shiftAmount: amount the merge will shift in each update
            delayCount: length of reflected segments

        Raises:
        ------
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
            if self.color_sequence_count >= self.real_led_count:
                # if sequence is too long, cut it in half
                self.color_sequence = self.color_sequence[: int(self.color_sequence_count // 2)]
                # don't remember offhand why this is here
                if self.color_sequence_count % 2 == 1:
                    if self.color_sequence_count == 1:
                        self.color_sequence = np.concatenate(
                            self.color_sequence,
                            self.color_sequence,
                        )
                    else:
                        self.color_sequence = self.color_sequence[:-1]
            # calculate modulo length
            _arrayLength = np.ceil(self.real_led_count / self.color_sequence_count) * self.color_sequence_count
            # update LED buffer with any changes we had to make
            self.set_virtual_led_buffer(
                ArraySequence.ReflectArray(
                    arrayLength=_arrayLength,
                    colorSequence=self.color_sequence,
                    foldLength=self.color_sequence_count,
                ),
            )
            # create tracking object
            merge: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionMerge,
                self.color_sequence,
            )
            # set merge size
            merge._size = self.color_sequence_count
            # set shift amount
            merge._step = _shiftAmount
            # set the number of LED refreshes to skip
            merge._delay_count_max = _delayCount
            # add function to list
            self._transforms.append(merge)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def useFunctionRandomChange(
        self,
        delayCount: int = None,
        changeCount: int = None,
        fadeStepCount: int = None,
        fadeType: LEDFadeType = None,
    ) -> None:
        """Randomly changes pixels from one color to the next.

        Args:
        ----
            delayCount: refresh delay
            changeCount: how many LEDs to have in the change queue at once
            fadeStepCount: number of steps in the transition from one color to the next
            fadeType: set to fade colors, or instant on/off

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionRandomChange.__name__,
        )
        try:
            _changeCount: int = random.randint(
                self.virtual_led_count // 5,
                self.virtual_led_count,
            )
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
                fade: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionFadeOff,
                    self.color_sequence,
                )
                fade._fade_amount = _fadeAmount
                self._transforms.append(fade)
            elif _fadeType == LEDFadeType.INSTANT_OFF:
                off: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionOff,
                    self.color_sequence,
                )
                self._transforms.append(off)
            else:
                # do nothing
                pass
            # create a bunch of tracking objects
            for index in self.get_random_indices(int(_changeCount)):
                if index < self.virtual_led_count:
                    change: ArrayTransform = ArrayTransform(
                        self,
                        ArrayTransform.functionRandomChange,
                        self.color_sequence,
                    )
                    # set the index from our random number
                    change._index = int(index)
                    # set the fade to off amount
                    change._fade_amount = _fadeAmount
                    # this is used to help calculate fade duration in the function
                    change._step_count_max = _fadeStepCount
                    # copy the current color of this LED index
                    # change.color = np.copy(self.virtualLEDBuffer[change.index])
                    if len(ArrayTransform.Controller.virtualLEDBuffer.shape) == 2:
                        change._color = np.copy(self.virtual_led_buffer[change._index])
                        # ArrayFunction.Controller.virtualLEDBuffer[accelerate.indexRange] = meteor.color
                    else:
                        change._color = ArrayTransform.Controller.virtualLEDBuffer[
                            np.where(
                                ArrayTransform.Controller.virtualLEDIndexBuffer == change._index,
                            )
                        ]
                    # randomly set the color we are fading toward
                    if random.randint(0, 1) == 1:
                        change._color_next = self.color_sequence_next
                    else:
                        change._color_next = change._color
                    # set the refresh delay
                    change._delay_count_max = _delayCountMax
                    # we want all the delays random, so don't start them all at zero
                    change._delay_counter = random.randint(0, change._delay_count_max)
                    # set true to fade, false to "instant on/off"
                    change._fade_type = _fadeType
                    # add function to list
                    self._transforms.append(change)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

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
        ----
            fadeAmount: the amount by which meteors are faded
            maxSpeed: the amount be which the meteor moves each refresh
            explode: if True, the meteors will light up in an explosion when they collide
            meteorCount: number of meteors
            collide: set true to make them bounce off each other randomly
            cycleColors: set true to make the meteors shift color as they move
            delayCount: refresh delay
            fadeType: set the type of fade to use using the enumeration

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMeteors.__name__,
        )
        try:
            _fadeAmount: float = random.randint(20, 40) / 100.0
            _explode: bool = self.get_random_boolean()
            _maxSpeed: int = random.randint(1, 3)
            _delayCount: int = random.randint(1, 3)
            _meteorCount: int = random.randint(2, 6)
            _collide: bool = self.get_random_boolean()
            _cycleColors: bool = self.get_random_boolean()
            fadeTypes: list[LEDFadeType] = list(LEDFadeType)
            _fadeType: LEDFadeType = fadeTypes[random.randint(0, len(fadeTypes) - 1)]
            if self.color_sequence_count >= 2 and self.color_sequence_count <= 6:
                _meteorCount = self.color_sequence_count
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
                fade: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionFadeOff,
                    self.color_sequence,
                )
                fade._fade_amount = _fadeAmount
                self._transforms.append(fade)
            elif _fadeType == LEDFadeType.INSTANT_OFF:
                off: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionOff,
                    self.color_sequence,
                )
                self._transforms.append(off)
            else:
                # do nothing
                pass
            for _ in range(_meteorCount):
                meteor: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionMeteors,
                    self.color_sequence,
                )
                # assign meteor color
                meteor._color = self.color_sequence_next
                # initialize "previous" index, for math's sake later
                meteor._index_previous = random.randint(0, self.virtual_led_count - 1)
                # set the number of LEDs it will move in one step
                meteor._step_size_max = _maxSpeed
                # set the maximum number of LEDs it could move in one step
                meteor._step = random.randint(1, max(2, meteor._step_size_max))
                # randomly initialize the direction
                meteor._direction = self.get_random_direction()
                # set the refresh delay
                meteor._delay_count_max = _delayCount
                # randomly assign starting index
                meteor._index = (meteor._index + (meteor._step * meteor._direction)) % self.virtual_led_count
                # set boolean to cycle each meteor through the color sequence as it moves
                meteor._color_cycle = _cycleColors
                # assign the color sequence
                meteor.color_sequence = np.copy(self.color_sequence)
                # add function to list
                self._transforms.append(meteor)
            # make sure there are at least two going to collide
            if self._transforms[0]._direction * self._transforms[1]._direction > 0:
                self._transforms[1]._direction *= -1
            # this object calculates collisions between other objects based on index and previous/next index
            if _collide is True:
                collision = ArrayTransform(
                    self,
                    ArrayTransform.functionCollisionDetection,
                    self.color_sequence,
                )
                collision._explode = _explode
                self._transforms.append(collision)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def useFunctionSprites(
        self,
        fadeSteps: int = None,
    ) -> None:
        """Meteors fade in and out in short bursts of random length and direction.

        Args:
        ----
            fadeSteps: amount to fade

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionSprites.__name__,
        )
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
            for _ in range(max(min(self.color_sequence_count, 10), 2)):
                sprite: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionSprites,
                    self.color_sequence,
                )
                # randomize index
                sprite._index = random.randint(0, self.virtual_led_count - 1)
                # initialize previous index
                sprite._index_previous = sprite._index
                # randomize direction
                sprite._direction = self.get_random_direction()
                # assign the target color
                sprite._color_goal = self.color_sequence_next
                # initialize sprite to
                sprite._color = ArraySequence.DEFAULT_BACKGROUND_COLOR.array
                # copy color sequence
                sprite.color_sequence = self.color_sequence
                # set next color
                sprite._color_next = PixelColors.OFF.array
                # set fade step/amount
                sprite._fade_steps = _fadeSteps
                sprite._fade_amount = _fadeAmount
                sprite.state = SpriteState.OFF.value
                self._transforms.append(sprite)
            # set one sprite to "fading on"
            self._transforms[0].state = SpriteState.FADING_ON.value
            # add LED fading for comet trails
            fade = ArrayTransform(
                self,
                ArrayTransform.functionFadeOff,
                self.color_sequence,
            )
            fade._fade_amount = _fadeAmount
            self._transforms.append(fade)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

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
        ----
            maxSize: max splash size
            raindropChance: chance of raindrop
            stepSize: splash speed
            maxRaindrops: number of raindrops
            fadeAmount: amount to fade LED each refresh

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionRaindrops.__name__,
        )
        try:
            _maxSize: int = random.randint(2, int(self.virtual_led_count // 8))
            _raindropChance: float = random.uniform(0.005, 0.1)
            _stepSize: int = random.randint(2, 5)
            _fadeAmount: float = random.uniform(0.25, 0.65)
            _maxRaindrops: int = max(min(self.color_sequence_count, 10), 2)
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
                raindrop: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionRaindrops,
                    self.color_sequence,
                )
                # randomize start index
                raindrop._index = random.randint(0, self.virtual_led_count - 1)
                # assign raindrop growth speed
                raindrop._step = _stepSize
                # max raindrop "splash"
                raindrop._size_max = _maxSize
                # max size
                raindrop._step_count_max = random.randint(2, raindrop._size_max)
                # chance of raindrop
                raindrop._active_chance = _raindropChance
                # assign color
                raindrop._color = self.color_sequence_next
                raindrop.color_sequence = self.color_sequence
                raindrop._fade_amount = _fadeAmount
                # set raindrop to be inactive initially
                raindrop.state = RaindropStates.OFF.value
                self._transforms.append(raindrop)
            # set first raindrop active
            self._transforms[0].state = RaindropStates.SPLASH.value
            # add fading
            fade: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionFadeOff,
                self.color_sequence,
            )
            fade._fade_amount = _fadeAmount
            self._transforms.append(fade)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def useFunctionAlive(
        self,
        fadeAmount: float = None,
        sizeMax: int = None,
        stepCountMax: int = None,
        stepSizeMax: int = None,
    ) -> None:
        """Use the function that uses a series of behaviors that move around in odd ways.

        Args:
        ----
            fadeAmount: amount of fade
            sizeMax: max size of LED pattern
            stepCountMax: max duration of effect
            stepSizeMax: max speed

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionAlive.__name__)
        try:
            _fadeAmount: float = random.uniform(0.20, 0.75)
            _sizeMax: int = random.randint(
                self.virtual_led_count // 6,
                self.virtual_led_count // 3,
            )
            _stepCountMax: int = random.randint(
                self.virtual_led_count // 10,
                self.virtual_led_count,
            )
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
                thing: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionAlive,
                    self.color_sequence,
                )
                # randomize start index
                thing._index = self.get_random_index()
                # randomize direction
                thing._direction = self.get_random_direction()
                # copy color sequence
                thing.color_sequence = self.color_sequence
                # assign color
                thing._color = thing.color_sequence_next
                # set max step count before possible state change
                thing._step_count_max = _stepCountMax
                # set max step size in normal condition
                thing._step_size_max = _stepSizeMax
                # randomize speed
                thing._step = random.randint(1, thing._step_size_max)
                # set refresh speed
                thing._delay_count_max = random.randint(6, 15)
                # set initial size
                thing._size = random.randint(1, int(_sizeMax // 2))
                # set max size
                thing._size_max = _sizeMax
                # start the state at 1
                thing.state = ThingMoves.METEOR.value
                # calculate random next state immediately
                thing._step_counter = 1000
                thing._delay_counter = 1000
                self._transforms.append(thing)
            self._transforms[0]._active = True
            # add a fade
            fade = ArrayTransform(
                self,
                ArrayTransform.functionFadeOff,
                self.color_sequence,
            )
            fade._fade_amount = _fadeAmount
            self._transforms.append(fade)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def useOverlayTwinkle(
        self,
        twinkleChance: float = None,
        colorSequence: np.ndarray[(3, Any), np.int32] = None,
    ) -> None:
        """Randomly sets some lights to 'twinkleColor' temporarily.

        Args:
        ----
            twinkleChance: chance of a twinkle
            colorSequence: the list of colors to be used when briefly flashing an LED

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useOverlayTwinkle.__name__)
        try:
            _twinkleChance: float = random.uniform(0.991, 0.995)
            _colorSequence = self.color_sequence.copy()
            if twinkleChance is not None:
                _twinkleChance = float(twinkleChance)
            if colorSequence is not None:
                _colorSequence = colorSequence
            twinkle: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.overlayTwinkle,
                _colorSequence,
            )
            twinkle._random = _twinkleChance
            self._transforms.append(twinkle)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def useOverlayBlink(
        self,
        blinkChance: float = None,
    ) -> None:
        """Use the overlay that causes all LEDs to light up the same color at once.

        Args:
        ----
            blinkChance: chance of a blink

        Raises:
        ------
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
            blink: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.overlayBlink,
                self.color_sequence,
            )
            blink._random = _blinkChance
            blink.color_sequence = self.color_sequence
            self._transforms.append(blink)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

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
        ----
            secondsPerMode: seconds to run current function
            functionNames: function names to run
            colorNames: color pattern names to run
            skipFunctions: function strings to omit (run if "skipFunction not in name")
            skipColors: color pattern strings to omit (run if "skipColor not in name")

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        try:
            _secondsPerMode: int = 60
            if secondsPerMode is not None:
                _secondsPerMode = int(secondsPerMode)
            self.seconds_per_mode = _secondsPerMode

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

            functions = self.get_function_methods_list()
            colors = self.get_color_methods_list()
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
                raise ControllerError("No functions selected in demo")
            elif len(colors) == 0:
                raise ControllerError("No colors selected in demo")
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
            raise ControllerError from ex
