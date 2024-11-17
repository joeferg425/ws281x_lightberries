"""Defines basic light string data and functions."""

from __future__ import annotations

import atexit
import os
import sys
from collections.abc import Sequence
from typing import Any, overload

import numpy as np
from numpy.typing import NDArray

from lightberries.array_sequence.base import ArraySequence
from lightberries.base.exceptions import PermissionsError, WS281xStringError
from lightberries.base.logger import LOGGER
from lightberries.base.pixel import Pixel, PixelColor, pixel_from_color
from lightberries.base.rpiws281x import PixelStrip


class WS281xString(Sequence[NDArray[np.int32]]):
    """Defines basic LED array data and functions."""

    def __init__(  # noqa: PLR0913
        self,
        led_count: int,
        dma_channel: int = 10,
        pwm_gpio_pin: int = 18,
        pwm_frequency: int = 800000,
        pwm_channel: int = 0,
        led_brightness: float = 0.75,
        led_strip_type: Any = None,  # noqa: ANN401
        led_gamma: Any = None,  # noqa: ANN401
        matrix_shape: tuple[int, int] | None = None,
        matrix_layout: NDArray[np.int32] | None = None,
        *,
        pwm_invert_signal: bool = False,
        simulate: bool = False,
        testing: bool = False,
    ) -> None:
        """Create a pixel array using the rpi_ws281x library.

        Args:
        ----
            led_count: the number of LEDs desired in the LightString
            pwm_gpio_pin: the GPIO pin number your lights are hooked up to
                (18 is a good choice since it does PWM)
            dma_channel: the DMA channel to use (5 is a good option)
            pwm_frequency: try 800,000
            pwm_invert_signal: set true to invert the PWM signal
            led_brightness: set to a value between 0.0 (OFF), and 1.0 (ON).
                    This setting tends to introduce flicker the lower it is
            pwm_channel: defaults to 0, see https://github.com/rpi-ws281x/rpi-ws281x-python
            led_strip_type: see https://github.com/rpi-ws281x/rpi-ws281x-python
            led_gamma: see https://github.com/rpi-ws281x/rpi-ws281x-python
            simulate: don't use GPIO
            matrix_shape: matrix shape
            matrix_layout: layout of a matrix made up of smaller LED matrices
            testing: set true if only testing

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens

        """
        self._ws281x_pixel_strip: PixelStrip
        self._simulate = simulate
        self._testing = testing
        # use passed led count if it is valid
        self._ledCount = led_count
        if not isinstance(led_count, int):  # type: ignore  # noqa: PGH003
            msg = "Cannot instantiate WS281X string, LED count argument is required."
            raise WS281xStringError(msg)
        if self._testing:
            global rpi_ws281x  # noqa: PLW0603
            import lightberries.base.rpiws281x_patch as rpi_ws281x  # pragma: no cover

            # cant run GPIO stuff without root, tell the user if they forgot
            # linux check is just for debugging with fake GPIO on windows
        if (not self._simulate and not self._testing) and sys.platform == "linux" and os.getuid() != 0:
            msg = "GPIO functionality requires root privilege. Please run command again as root"  # pragma: no cover
            raise PermissionsError(msg)  # pragma: no cover
        self._instantiate_pixel_strip(
            pwm_gpio_pin=pwm_gpio_pin,
            dma_channel=dma_channel,
            led_count=led_count,
            pwm_frequency=pwm_frequency,
            pwm_channel=pwm_channel,
            pwm_invert_signal=pwm_invert_signal,
            led_gamma=led_gamma,
            led_strip_type=led_strip_type,
            led_brightness=led_brightness,
            matrix_shape=matrix_shape,
            matrix_layout=matrix_layout,
            testing=testing,
        )

    def _instantiate_pixel_strip(  # noqa: PLR0913
        self,
        led_count: int,
        pwm_gpio_pin: int,
        pwm_channel: int,
        pwm_frequency: int,
        dma_channel: int,
        led_gamma: float,
        led_strip_type: Any,  # noqa: ANN401
        led_brightness: Any,  # noqa: ANN401
        matrix_shape: tuple[int, int] | None = None,  # noqa: ARG002
        matrix_layout: NDArray[np.int32] | None = None,  # noqa: ARG002
        *,
        pwm_invert_signal: bool = False,
        testing: bool = False,  # noqa: ARG002
    ) -> None:
        """Instantiate the underlying object.

        Args:
        ----
            led_count: the number of LEDs desired in the LightString
            pwm_gpio_pin: the GPIO pin number your lights are hooked up to
                (18 is a good choice since it does PWM)
            dma_channel: the DMA channel to use (5 is a good option)
            pwm_frequency: try 800,000
            pwm_invert_signal: set true to invert the PWM signal
            led_brightness: set to a value between 0.0 (OFF), and 1.0 (ON).
                    This setting tends to introduce flicker the lower it is
            pwm_channel: defaults to 0, see https://github.com/rpi-ws281x/rpi-ws281x-python
            led_strip_type: see https://github.com/rpi-ws281x/rpi-ws281x-python
            led_gamma: see https://github.com/rpi-ws281x/rpi-ws281x-python
            simulate: don't use GPIO
            matrix_shape: matrix shape
            matrix_layout: layout of a matrix made up of smaller LED matrices
            testing: set true if only testing

        Raises:
        ------
            WS281xStringError: _description_

        """
        self._ws281x_pixel_strip = PixelStrip(  # pragma: no cover
            pin=pwm_gpio_pin,
            dma=dma_channel,
            num=led_count,
            freq_hz=pwm_frequency,
            channel=pwm_channel,
            invert=pwm_invert_signal,
            gamma=led_gamma,
            strip_type=led_strip_type,
            brightness=int(255 * led_brightness),
        )
        # try to force cleanup of underlying c objects when user exits
        atexit.register(self.__del__)  # pragma: no cover

        self._ws281x_pixel_strip.begin()  # pragma: no cover
        self._ledCount = len(self._ws281x_pixel_strip)  # pragma: no cover
        LOGGER.debug("Created %s", WS281xString.__name__)  # pragma: no cover

    def __del__(
        self,
    ) -> None:
        """Properly disposes of the rpi_ws281x object.

        Prevents memory leaks (hopefully) that were happening in the rpi.PixelStrip module.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens

        """
        # check if pixel strip has been created
        if hasattr(self, "_ws281x_pixel_strip"):
            # turn off LEDs
            self.off()
            # cleanup c memory usage
            self._ws281x_pixel_strip._cleanup()  # type: ignore  # noqa: PGH003, SLF001

    def __len__(
        self,
    ) -> int:
        """Return length of the light string (the number of LEDs).

        Returns
        -------
            the number of LEDs in the array

        """
        return self._ledCount

    @overload
    def __getitem__(  # D105
        self,
        idx: int,
    ) -> NDArray[np.int32] | None: ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # D105
        self,
        idx: np.int32,
    ) -> NDArray[np.int32] | None: ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # D105 # pylint: disable=function-redefined
        self,
        idx: slice,
    ) -> NDArray[np.int32] | None: ...  # pylint: disable=pointless-statement  # pragma: no cover

    def __getitem__(  # pylint: disable=function-redefined # type: ignore  # noqa: PGH003
        self,
        idx: int | np.int32 | slice,
    ) -> NDArray[np.int32] | None:
        """Return a LED index or slice from LED array.

        Args:
        ----
            idx: an index of a single LED, or a slice specifying a range of LEDs

        Returns:
        -------
            the LED value or values as requested

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens

        """
        pixel: NDArray[np.int32]
        if isinstance(idx, int):
            pixel = Pixel(self._ws281x_pixel_strip.getPixelColor(idx)).array
        elif isinstance(idx, (np.integer)):
            pixel = Pixel(self._ws281x_pixel_strip.getPixelColor(int(idx))).array
        else:
            pixel = ArraySequence.pixel_array_to_numpy_array(
                [Pixel(self._ws281x_pixel_strip.getPixelColor(k)) for k in range(self._ledCount)[idx]],
            )
        return pixel

    def __setitem__(
        self,
        key: int | np.int32 | slice,
        value: NDArray[np.int32],
    ) -> None:
        """Set LED value(s) in the array.

        Args:
        ----
            key: the index or slice specifying one or more LED indices
            value: the RGB value or values to assign to the given LED indices

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens

        """
        if isinstance(key, slice):
            for i, j in enumerate(range(self._ledCount)[key]):
                p = Pixel(value[i, Pixel.default_pixel_order])
                self._ws281x_pixel_strip.setPixelColor(j, p.int32value)
        elif isinstance(key, (np.integer)):
            if int(key) >= self._ledCount:
                raise IndexError
            p = Pixel(value)
            self._ws281x_pixel_strip.setPixelColor(int(key), p.int32value)
        else:
            if key >= self._ledCount:
                raise IndexError
            p = Pixel(value)
            self._ws281x_pixel_strip.setPixelColor(key, p.int32value)

    def __enter__(  # noqa: PYI034
        self,
    ) -> WS281xString:
        """Get an instance of this object object.

        Returns
        -------
            an instance of LightString

        """
        return self

    def __exit__(
        self,
        *args: object,
    ) -> None:
        """Cleanup the instance of this object.

        Args:
        ----
            args: ignored

        """
        self.__del__()

    def refresh(self) -> None:
        """Refresh the LED output."""
        if self._ws281x_pixel_strip:
            self._ws281x_pixel_strip.show()

    def off(
        self,
    ) -> None:
        """Turn all of the LEDs in the LightString off.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens

        """
        for index in range(len(self)):
            self[index] = pixel_from_color(PixelColor.OFF).array
        self.refresh()
        self.refresh()
        self.refresh()
