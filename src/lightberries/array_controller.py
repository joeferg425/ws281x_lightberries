"""Class defines methods for interacting with Light Strings, Patterns, and Functions."""

from __future__ import annotations

import contextlib
import logging
import random
import time
from pathlib import Path
from typing import Any, Callable, cast

import numpy as np
from numpy.typing import NDArray

from lightberries.array_sequence.all_sequences import *  # noqa: F403 - import all of them for the demo
from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.named import SequenceName, get_named_sequence
from lightberries.array_sequence.solid import SequenceSolid
from lightberries.array_transform.all_functions import *  # noqa: F403 - import all of them for the demo
from lightberries.base.constants import SHAPE_2D, SHAPE_3D
from lightberries.base.exceptions import ControllerError
from lightberries.base.logger import LOGGER
from lightberries.base.pixel import LEDOrder, Pixel, PixelColor
from lightberries.base.ws281x_strings import WS281xString
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

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
        led_order: LEDOrder = LEDOrder.GRB,
        *,
        pwm_invert_signal: bool = False,
        debug: bool = False,
        verbose: bool = False,
        simulate: bool = False,
        testing: bool = False,
        log_file: str | Path | None = None,
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

        """
        Pixel.default_pixel_order = led_order
        # configure logging
        if debug is True or verbose is True:
            if not LOGGER.handlers:
                stream_handler = logging.StreamHandler()
                LOGGER.addHandler(stream_handler)
            LOGGER.setLevel(logging.DEBUG)
        if verbose is True:
            LOGGER.setLevel(5)
        if log_file is not None:
            log_file = Path(log_file)
            fh = logging.FileHandler(filename=log_file, mode="a")
            fh.setLevel(logging.DEBUG)
            LOGGER.addHandler(fh)
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
        self._led_count: int = len(self._ws281x_string)
        self.virtual_led_buffer: NDArray[np.int32] = SequenceSolid(
            led_count=self._led_count,
            color=Pixel(PixelColor.OFF),
        ).array
        self.virtual_led_index_buffer: NDArray[np.int32] = np.array(
            range(len(self._ws281x_string)),
        )
        self._overlay_dict: dict[int, NDArray[np.int32]] = {}
        self._virtual_led_count: int = len(self.virtual_led_buffer)
        self._virtual_led_index_count: int = len(self.virtual_led_index_buffer)
        self._last_mode_change: float = time.time() - 1000
        self._next_mode_change: float = time.time()
        self._refresh_delay: float = 0.001
        self._seconds_per_mode: float = 120.0
        self._background_color: Pixel = Pixel(PixelColor.OFF)
        self._color_sequence: PixelSequence = PixelSequence.get_monthly_color_sequence()
        self._color_sequence_count: int = len(self._color_sequence)
        self._color_sequence_index: int = 0
        self._loop_forever: bool = False

        self.running: bool = False
        self.refresh_callback: Callable[[], None] | None = refresh_callback

        # initialize stuff
        self.reset()

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
        self._ws281x_string: WS281xString = WS281xString(
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
        self._ws281x_string.off()

    def __del__(
        self,
    ) -> None:
        """Disposes of the rpi_ws281x object (if it exists) to prevent memory leaks."""
        if hasattr(self, "ws281xString"):
            with contextlib.suppress(Exception):
                self._ws281x_string.__del__()

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
    ) -> Pixel:
        """The defined background, or "Off" color for the LED string.

        Returns
        -------
            the rgb value

        """
        return self._background_color

    @background_color.setter
    def background_color(
        self,
        color: Pixel,
    ) -> None:
        """Set the background color.

        Args:
        ----
            color: an RGB value

        """
        self._background_color = color.copy()

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
    ) -> PixelSequence:
        """The sequence of RGB values to use for generating patterns when using the functions.

        Returns
        -------
            the sequence of RGB values

        """
        return self._color_sequence

    @color_sequence.setter
    def color_sequence(
        self,
        color_sequence: PixelSequence,
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
    ) -> Pixel:
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
        return PixelTransform.ACTIVE_TRANSFORMS

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
        """Reset class variables to default state."""
        LOGGER.debug("%s.%s:", ArrayController.__name__, self.reset.__name__)
        PixelTransform.ACTIVE_TRANSFORMS.clear()
        if self.virtual_led_count >= self.real_led_count:
            self.set_virtual_led_buffer(self.virtual_led_buffer[: self.real_led_count])
        elif self.virtual_led_count < self.real_led_count:
            array = SequenceSolid(
                led_count=self.real_led_count,
                color=Pixel(PixelColor.OFF),
            )
            self.set_virtual_led_buffer(array)

    def set_virtual_led_buffer(
        self,
        led_buffer: NDArray[np.int32] | PixelSequence,
    ) -> None:
        """Assign a sequence of pixel data to the LED.

        Args:
        ----
            led_buffer: array of RGB values

        """
        # make sure the passed LED array is the correct type
        if isinstance(led_buffer, PixelSequence):
            _led_buffer = led_buffer.array
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
                        [Pixel(PixelColor.OFF) for _ in range(self.real_led_count - self.virtual_led_count)],
                    ),
                ),
            )

    def copy_virtual_leds_to_ws281x(
        self,
    ) -> None:
        """Set each Pixel in the rpi_ws281x object to the buffered array value."""
        # callback function to do work

        def set_pixel(i_rgb: tuple[int, NDArray[np.int32]]) -> None:
            """Set pixel value in ws281x object.

            Args:
            ----
                i_rgb: pixel color value and gamma

            """
            self._ws281x_string[i_rgb[0]] = i_rgb[1]

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
        """Display current LED buffer."""
        # call light string's refresh method to send the communications out to the addressable LEDs
        if isinstance(self.refresh_callback, Callable):
            self.refresh_callback()
        self._ws281x_string.refresh()

    def off(
        self,
    ) -> None:
        """Set all Pixels to RGD background color."""
        LOGGER.debug("%s.%s:", ArrayController.__name__, self.off.__name__)
        # clear all current values
        self.virtual_led_buffer *= 0
        # set to background color
        self.virtual_led_buffer[:] += self.background_color.rgb_array
        LOGGER.debug("Turning Off.")

    def _run_functions(
        self,
    ) -> None:
        """Run each function in the configured function list."""
        # invoke the function pointer saved in the light data object
        for function in PixelTransform.ACTIVE_TRANSFORMS:
            function.transform()

    def _copy_overlays(
        self,
    ) -> None:
        """Copy overlays directly to output array, bypassing the buffer."""
        # iterate over the dictionary key-value pairs, assign LED values
        # directly to output buffer skipping the virtual LED copies.
        # This ensures that overlays are temporary and get overwritten
        # next refresh.
        for index, led_value in self._overlay_dict.items():
            self._ws281x_string[index] = led_value
        self._overlay_dict = {}

    def run(
        self,
    ) -> None:
        """Run the configured color pattern and function either forever or for self.secondsPerMode."""
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

    def demo(  # noqa: C901, PLR0912, PLR0915
        self,
        seconds_per_mode: float | None = 0.5,
        function_names: list[str] | None = None,
        color_names: list[str] | None = None,
        skip_functions: list[str] | None = None,
        skip_colors: list[str] | None = None,
        kwargs: dict[str, Any] = {},
    ) -> None:
        """Run colors and functions semi-randomly.

        Args:
        ----
            seconds_per_mode: seconds to run current function
            function_names: function names to run
            color_names: color pattern names to run
            skip_functions: function strings to omit (run if "skipFunction not in name")
            skip_colors: color pattern strings to omit (run if "skipColor not in name")

        """
        LOGGER.debug("%s.%s:", ArrayController.__name__, self.demo.__name__)
        _seconds_per_mode: int = 60
        if seconds_per_mode is not None:
            _seconds_per_mode = int(seconds_per_mode)
        self.seconds_per_mode = _seconds_per_mode
        if seconds_per_mode == 0.0:
            self._loop_forever = True

        if function_names is None:
            function_names = []
        if color_names is None:
            color_names = []
        if skip_functions is None:
            skip_functions = []
        if skip_colors is None:
            skip_colors = []

        transform_functions = list(PixelTransform.ALL_TRANSFORMS)
        color_functions = list(PixelSequence.ALL_SEQUENCES)
        color_sequences = list(SequenceName._member_names_)
        # get methods that match user's string
        if len(function_names) > 0:
            matches: list[str] = []
            for name in function_names:
                matches.extend([f for f in PixelTransform.ALL_TRANSFORMS if name.lower() == f.lower()])
            transform_functions = matches
        # get methods that match user's string
        if len(color_names) > 0:
            matches: list[str] = []
            for name in color_names:
                matches.extend([f for f in PixelSequence.ALL_SEQUENCES if name.lower() == f.lower()])
            color_functions = matches
        # get methods that match user's string
        if len(color_names) > 0:
            matches: list[str] = []
            for name in color_names:
                matches.extend([f for f in SequenceName._member_names_ if name.lower() == f.lower()])
            color_sequences = matches
        # remove methods that user requested
        if len(skip_functions) > 0:
            matches = []
            for name in skip_functions:
                for transform_function in transform_functions:
                    if name.lower() in transform_function.lower():
                        transform_functions.remove(transform_function)
        # remove methods that user requested
        if len(skip_colors) > 0:
            matches = []
            for name in skip_colors:
                for color_function in color_functions:
                    if name.lower() in color_function.lower():
                        color_functions.remove(color_function)

        if len(transform_functions) == 0:
            msg = "No functions selected in demo"
            raise ControllerError(msg)
        if len(color_functions) == 0 and len(color_sequences) == 0:
            msg = "No colors selected in demo"
            raise ControllerError(msg)
        while True:
            # make a temporary copy (so we can go through each one)
            transform_functions_copy = transform_functions.copy()
            color_functions_copy = color_functions.copy()
            color_sequences_copy = color_sequences.copy()
            transform_function = transform_functions_copy[random.randint(0, len(transform_functions_copy) - 1)]
            color_function = None
            color_sequence = None
            if color_functions:
                color_function = color_functions_copy[random.randint(0, len(color_functions_copy) - 1)]
            if color_sequences:
                color_sequence = color_sequences_copy[random.randint(0, len(color_sequences_copy) - 1)]
            # if not color_function and any(name.lower() in SequenceName._member_names_ for name in color_names):
            #     color_functions_copy = color_names
            #     color_function = color_names[0]
            # loop while we still have a color and a function
            while len(transform_functions_copy) > 0 and (len(color_functions_copy) or len(color_sequences_copy) > 0):
                # get a new function if there is one
                if len(transform_functions_copy) > 0:
                    transform_function = transform_functions_copy[random.randint(0, len(transform_functions_copy) - 1)]
                    transform_functions_copy.remove(transform_function)
                # get a new color pattern if there is one
                if len(color_functions_copy) > 0:
                    color_function = color_functions_copy[random.randint(0, len(color_functions_copy) - 1)]
                    color_functions_copy.remove(color_function)
                # get a new color pattern if there is one
                if len(color_sequences_copy) > 0:
                    color_sequence = color_sequences_copy[random.randint(0, len(color_sequences_copy) - 1)]
                    color_sequences_copy.remove(color_sequence)
                # reset
                self.reset()
                # apply color
                clr = None
                if color_function:
                    LOGGER.info("Color: %s", color_function)
                    clr = PixelSequence.ALL_SEQUENCES[color_function](
                        led_count=random.randint(
                            1,
                            self.real_led_count,
                        ),
                    )
                elif color_sequence:
                    LOGGER.info("Color: %s", color_sequence)
                    clr = get_named_sequence(
                        name=SequenceName[color_sequence],
                        led_count=random.randint(
                            1,
                            self.real_led_count,
                        ),
                    )
                else:
                    LOGGER.info("Color: %s", "default monthly sequence")
                    clr = PixelSequence.get_monthly_color_sequence()
                # configure function
                LOGGER.info("Function: %s", transform_function)
                PixelTransform.ALL_TRANSFORMS[transform_function].create(
                    controller=self,
                    pixel_sequence=clr,
                )

                # run the combination
                self.run()
