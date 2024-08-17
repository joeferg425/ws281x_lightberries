"""Class defines methods for interacting with Light Strings, Patterns, and Functions."""

from __future__ import annotations

import contextlib
import logging
import random
import time
from typing import Any, Callable, cast

import numpy as np
from numpy.typing import NDArray

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.solid import SequenceSolid
from lightberries.constants import SHAPE_2D, SHAPE_3D
from lightberries.exceptions import ControllerError, LightBerryError
from lightberries.pixel import Pixel, PixelColor
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform
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

    def __init__(  # noqa: PLR0913
        self,
        led_count: int = 100,
        pwm_gpio_pin: int = 18,
        dma_channel: int = 10,
        pwm_frequency: int = 800000,
        led_brightness: float = 0.75,
        pwm_channel: int = 0,
        led_strip_type: Any = None,  # noqa: ANN401
        gamma: Any = None,  # noqa: ANN401
        refresh_callback: Callable[[], None] | None = None,
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
            testing: when testing

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
                LOGGER.setLevel(logging.DEBUG)
            if verbose is True:
                LOGGER.setLevel(5)
            self.simulate = simulate
            # wrap pixel strip in my own interface object
            self._instantiate_ws281x_string(
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
            self.virtual_led_buffer: NDArray[np.int32] = SequenceSolid(
                led_count=self._led_count,
                color=PixelColor.OFF.array,
            ).sequence
            self.virtual_led_index_buffer: NDArray[np.int32] = np.array(
                range(len(self.ws281xString)),
            )
            self._overlay_dict: dict[int, NDArray[np.int32]] = {}
            self._virtual_led_count: int = len(self.virtual_led_buffer)
            self._virtual_led_index_count: int = len(self.virtual_led_index_buffer)
            self._last_mode_change: float = time.time() - 1000
            self._next_mode_change: float = time.time()
            self._refresh_delay: float = 0.001
            self._seconds_per_mode: float = 120.0
            self._background_color: NDArray[np.int32] = PixelColor.OFF.array
            self._color_sequence: NDArray[np.int32] = ArraySequence.default_color_sequence_by_month()
            self._color_sequence_count: int = len(self._color_sequence)
            self._color_sequence_index: int = 0
            self._loop_forever: bool = False
            self._transforms: list[PixelTransform] = []

            self.running: bool = False
            self.refresh_callback: Callable[[], None] | None = refresh_callback

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

    def _instantiate_ws281x_string(  # noqa: PLR0913
        self,
        led_count: int,
        pwm_gpio_pin: int,
        dma_channel: int,
        pwm_frequency: int,
        pwm_invert_signal: bool,  # noqa: FBT001
        led_brightness: float,
        pwm_channel: int,
        led_strip_type: Any,  # noqa: ANN401
        gamma: Any,  # noqa: ANN401
        simulate: bool,  # noqa: FBT001
        testing: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        self.ws281xString: WS281xString = WS281xString(
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
        if hasattr(self, "ws281xString"):
            with contextlib.suppress(Exception):
                self.off()
            with contextlib.suppress(Exception):
                self.copy_virtual_leds_to_ws281x()
            with contextlib.suppress(Exception):
                self.refresh_leds()
            with contextlib.suppress(Exception):
                self.ws281xString.__del__()

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
    ) -> NDArray[np.int32]:
        """The defined background, or "Off" color for the LED string.

        Returns
        -------
            the rgb value

        """
        return self._background_color

    @background_color.setter
    def background_color(
        self,
        color: NDArray[np.int32],
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
    ) -> float | None:
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
    ) -> NDArray[np.int32]:
        """The sequence of RGB values to use for generating patterns when using the functions.

        Returns
        -------
            the sequence of RGB values

        """
        return self._color_sequence

    @color_sequence.setter
    def color_sequence(
        self,
        color_sequence: NDArray[np.int32],
    ) -> None:
        """Set the color sequence.

        Args:
        ----
            color_sequence: the sequence of RGB values

        """
        self._color_sequence = cast(
            NDArray[np.int32],
            np.copy(
                a=ArraySequence.pixel_array_to_numpy_array(color_sequence),
            ),  # type: ignore  # noqa: PGH003
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
            color_sequence_index: the new index

        """
        if color_sequence_index >= len(self.color_sequence):
            self._color_sequence_index = 0
        else:
            self._color_sequence_index = color_sequence_index

    @property
    def color_sequence_next(
        self,
    ) -> NDArray[np.int32]:
        """Get the next color in the sequence.

        Returns
        -------
            the next RGB value

        """
        temp = self.color_sequence[self.color_sequence_index]
        self.color_sequence_index += 1
        return temp

    @property
    def function_list(self) -> list[PixelTransform]:
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
            LOGGER.debug("%s.%s:", ArrayController.__name__, self.reset.__name__)
            self._transforms = []
            if self.virtual_led_count >= self.real_led_count:
                self.set_virtual_led_buffer(self.virtual_led_buffer[: self.real_led_count])
            elif self.virtual_led_count < self.real_led_count:
                array = SequenceSolid(
                    led_count=self.real_led_count,
                    color=PixelColor.OFF,
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
        led_buffer: NDArray[np.int32] | PixelSequence,
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
            if isinstance(led_buffer, PixelSequence):
                _led_buffer = led_buffer.sequence
            else:
                _led_buffer = led_buffer
            _led_buffer_length = int(_led_buffer.size / 3)

            # check assignment length
            if (
                _led_buffer_length >= self.real_led_count
                or len(_led_buffer.shape) > SHAPE_2D
                or len(self.virtual_led_buffer.shape) > SHAPE_2D
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
            if self._virtual_led_index_count < self.real_led_count and len(self.virtual_led_buffer.shape) < SHAPE_3D:
                self._virtual_led_index_count = self.real_led_count
                self.virtual_led_index_buffer = np.arange(self._virtual_led_index_count)
                self.virtual_led_buffer = np.concatenate(
                    (
                        self.virtual_led_buffer,
                        np.array(
                            [PixelColor.OFF.tuple for _ in range(self.real_led_count - self.virtual_led_count)],
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

        def set_pixel(i_rgb: tuple[int, NDArray[np.int32]]) -> None:
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
                ),  # type: ignore  # noqa: PGH003
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
            if isinstance(self.refresh_callback, Callable):
                self.refresh_callback()
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
        # invoke the function pointer saved in the light data object
        for function in self._transforms:
            function.transform()

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

    def run(self):
        """Run the configured color pattern and function either forever or for self.secondsPerMode.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        LOGGER.debug("%s.%s:", ArrayController.__name__, self.run.__name__)
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
            # run the selected functions using LightFunction object callbacks
            self._run_functions()
            # copy the resulting RGB values to the ws28xx LED buffer
            self.copy_virtual_leds_to_ws281x()
            # copy temporary changes (not buffered in this class) to the ws28xx LED buffer
            self._copy_overlays()
            # tell the ws28xx controller to transmit the new data
            self.refresh_leds()
        self._last_mode_change = time.time()
        if self.seconds_per_mode is None:
            self._next_mode_change = self._last_mode_change + (random.randint(30, 120))
        else:
            self._next_mode_change = self._last_mode_change + (self.seconds_per_mode)

    def demo(
        self,
        seconds_per_mode: float | None = 0.5,
        function_names: list[str] | None = None,
        color_names: list[str] | None = None,
        skip_functions: list[str] | None = None,
        skip_colors: list[str] | None = None,
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
        _seconds_per_mode: int = 60
        if seconds_per_mode is not None:
            _seconds_per_mode = int(seconds_per_mode)
        self.seconds_per_mode = _seconds_per_mode

        if function_names is None:
            function_names = []
        if color_names is None:
            color_names = []
        if skip_functions is None:
            skip_functions = []
        if skip_colors is None:
            skip_colors = []

        functions = list(PixelTransform.ALL_TRANSFORMS)
        colors = list(PixelSequence.ALL_SEQUENCES)
        # get methods that match user's string
        if len(function_names) > 0:
            matches: list[str] = []
            for name in function_names:
                matches.extend([f for f in PixelTransform.ALL_TRANSFORMS if name.lower() in f.lower()])
            functions = matches
        # get methods that match user's string
        if len(color_names) > 0:
            matches: list[str] = []
            for name in color_names:
                matches.extend([f for f in PixelSequence.ALL_SEQUENCES if name.lower() in f.lower()])
            colors = matches
        # remove methods that user requested
        if len(skip_functions) > 0:
            matches = []
            for name in skip_functions:
                for function in functions:
                    if name.lower() in function.lower():
                        functions.remove(function)
        # remove methods that user requested
        if len(skip_colors) > 0:
            matches = []
            for name in skip_colors:
                for color in colors:
                    if name.lower() in color.lower():
                        colors.remove(color)

        if len(functions) == 0:
            msg = "No functions selected in demo"
            raise ControllerError(msg)
        if len(colors) == 0:
            msg = "No colors selected in demo"
            raise ControllerError(msg)
        while True:
            # make a temporary copy (so we can go through each one)
            functions_copy = functions.copy()
            colors_copy = colors.copy()
            function = functions_copy[random.randint(0, len(functions_copy) - 1)]
            color = colors_copy[random.randint(0, len(colors_copy) - 1)]
            # loop while we still have a color and a function
            while (len(functions_copy) * len(colors_copy)) > 0:
                # get a new function if there is one
                if len(functions_copy) > 0:
                    function = functions_copy[random.randint(0, len(functions_copy) - 1)]
                    functions_copy.remove(function)
                # get a new color pattern if there is one
                if len(colors_copy) > 0:
                    color = colors_copy[random.randint(0, len(colors_copy) - 1)]
                    colors_copy.remove(color)
                # reset
                self.reset()
                # apply color
                clr = PixelSequence.ALL_SEQUENCES[color](led_count=self.real_led_count)
                # configure function
                self._transforms = PixelTransform.ALL_TRANSFORMS[function](controller=self).setup(
                    color_sequence=clr.sequence
                )

                # run the combination
                self.run()
