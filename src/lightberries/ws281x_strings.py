"""Defines basic light string data and functions."""
from __future__ import annotations
from ctypes import Union
import os
import sys
import atexit
import logging
from typing import Any, Sequence, overload
import numpy as np
from numpy.typing import NDArray
from lightberries.array_patterns import ConvertPixelArrayToNumpyArray
from lightberries.exceptions import PermissionsError, WS281xStringError, LightBerryError
from lightberries.rpiws281x import rpi_ws281x
from lightberries.pixel import Pixel, PixelColors

LOGGER = logging.getLogger("lightBerries")


class WS281xString(Sequence[np.int_]):
    """Defines basic LED array data and functions."""

    def __init__(
        self,
        led_count: int,
        pwm_gpio_pin: int = 18,
        dma_channel: int = 10,
        pwm_frequency: int = 800000,
        pwm_invert_signal: bool = False,
        pwm_channel: int = 0,
        led_brightness: float = 0.75,
        led_strip_type: Any = None,
        led_gamma: Any = None,
        matrix_shape: tuple[int, int] = None,
        matrix_layout: NDArray[np.int32] | None = None,
        simulate: bool = False,
        testing: bool = False,
    ) -> None:
        """Creates a pixel array using the rpi_ws281x library.

        Args:
            ledCount: the number of LEDs desired in the LightString
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
            simulate: don't use GPIO

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens
        """
        self._ws281x_pixel_strip = None
        self._simulate = simulate
        self._testing = testing
        # catch error cases first
        if led_count is None or not isinstance(led_count, int):
            raise WS281xStringError(f"Cannot create LightString with ledCount: {led_count}.")
        # use passed led count if it is valid
        self._ledCount = led_count
        if self._testing:
            global rpi_ws281x
            # import lightberries.rpiws281x_patch as rpiws281x  # noqa
            import lightberries.rpiws281x_patch as rpi_ws281x  # noqa

            # cant run GPIO stuff without root, tell the user if they forgot
            # linux check is just for debugging with fake GPIO on windows
        if not self._simulate and not self._testing:
            if sys.platform == "linux" and not os.getuid() == 0:  # pylint: disable = no-member  # pragma: no cover
                raise PermissionsError(
                    "GPIO functionality requires root privilege. Please run command again as root"
                )
        self._instantiate_pixelstrip(
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

    def _instantiate_pixelstrip(
        self,
        led_count: int,
        pwm_gpio_pin: int,
        pwm_channel: int,
        pwm_invert_signal: bool,
        pwm_frequency: int,
        dma_channel: int,
        led_gamma: float,
        led_strip_type: Any,
        led_brightness: Any,
        matrix_shape: tuple[int, int] = None,
        matrix_layout: NDArray[np.int32] | None = None,
        testing: bool = False,
    ) -> None:
        try:  # pragma: no cover
            # create ws281x pixel strip
            self._ws281x_pixel_strip = rpi_ws281x.PixelStrip(  # pragma: no cover
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
            atexit.register(self.__del__)

            self._ws281x_pixel_strip.begin()
            self._ledCount = int(self._ws281x_pixel_strip.numPixels())
            LOGGER.debug(
                "%s Created WS281X object",
                self.__class__.__name__,
            )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise WS281xStringError from ex

    def __del__(
        self,
    ) -> None:
        """Properly disposes of the rpi_ws281x object.

        Prevents memory leaks (hopefully) that were happening in the rpi.PixelStrip module.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens
        """
        # check if pixel strip has been created
        if isinstance(self._ws281x_pixel_strip, rpi_ws281x.PixelStrip):
            # turn off LEDs
            self.off()
            # cleanup c memory usage
            try:
                self._ws281x_pixel_strip._cleanup()
            except SystemExit:  # pylint:disable=try-except-raise  # pragma: no cover
                raise
            except KeyboardInterrupt:  # pylint:disable=try-except-raise  # pragma: no cover
                raise
            except LightBerryError:  # pragma: no cover
                raise
            except Exception as ex:  # pragma: no cover
                raise WS281xStringError from ex

    def __len__(
        self,
    ) -> int:
        """Return length of the light string (the number of LEDs).

        Returns:
            the number of LEDs in the array
        """
        return self._ledCount

    @overload
    def __getitem__(  # noqa D105
        self,
        idx: int,
    ) -> np.ndarray[(3,), np.int32]:
        ...  # pylint: disable=pointless-statement  # pragma: no cover

    @overload
    def __getitem__(  # noqa D105 # pylint: disable=function-redefined
        self,
        s: slice,
    ) -> np.ndarray[(3, Any), np.int32]:
        ...  # pylint: disable=pointless-statement  # pragma: no cover

    def __getitem__(  # pylint: disable=function-redefined
        self, key: int | slice
    ) -> Union[np.ndarray[(3,), np.int32], np.ndarray[(3, Any), np.int32]]:
        """Return a LED index or slice from LED array.

        Args:
            key: an index of a single LED, or a slice specifying a range of LEDs

        Returns:
            the LED value or values as requested

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens
        """
        if isinstance(key, int):
            return Pixel(self._ws281x_pixel_strip.getPixelColor(key)).array
        elif isinstance(key, (np.int_, np.int32)):
            return Pixel(self._ws281x_pixel_strip.getPixelColor(int(key))).array
        else:
            return ConvertPixelArrayToNumpyArray(
                [Pixel(self._ws281x_pixel_strip.getPixelColor(k)) for k in range(self._ledCount)[key]]
            )

    def __setitem__(
        self,
        key: int | slice,
        value: np.ndarray[(3,), np.int32] | np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Set LED value(s) in the array.

        Args:
            key: the index or slice specifying one or more LED indices
            value: the RGB value or values to assign to the given LED indices

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens
        """
        if isinstance(key, slice):
            for i, j in enumerate(range(self._ledCount)[key]):
                p = Pixel(value[i, :])
                self._ws281x_pixel_strip.setPixelColor(j, p.int_value)
        elif isinstance(key, (np.int_, np.int32)):
            if int(key) >= self._ledCount:
                raise IndexError()
            p = Pixel(value)
            self._ws281x_pixel_strip.setPixelColor(int(key), p.int_value)
        else:
            if key >= self._ledCount:
                raise IndexError()
            p = Pixel(value)
            self._ws281x_pixel_strip.setPixelColor(key, p.int_value)

    def __enter__(
        self,
    ) -> "WS281xString":
        """Get an instance of this object object.

        Returns:
            an instance of LightString
        """
        return self

    def __exit__(
        self,
        *args,
    ) -> None:
        """Cleanup the instance of this object.

        Args:
            args: ignored
        """
        self.__del__()

    def refresh(self):
        if self._ws281x_pixel_strip:
            self._ws281x_pixel_strip.show()

    def off(
        self,
    ) -> None:
        """Turn all of the LEDs in the LightString off.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightStringException: if something bad happens
        """
        for index in range(len(self)):
            try:
                self[index] = PixelColors.OFF
            except SystemExit:  # pragma: no cover
                raise
            except KeyboardInterrupt:  # pragma: no cover
                raise
            except LightBerryError:  # pragma: no cover
                raise
            except Exception as ex:  # pragma: no cover
                raise WS281xStringError from ex
        self.refresh()
