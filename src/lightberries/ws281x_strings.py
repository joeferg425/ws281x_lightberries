"""Defines basic light string data and functions."""
from __future__ import annotations
from ctypes import Union
import os
import sys
import atexit
import logging
from typing import Any, Sequence, overload
import numpy as np
from lightberries.array_patterns import ConvertPixelArrayToNumpyArray
from lightberries.exceptions import LightStringException, LightBerryException
from lightberries.rpi_ws281x_patch import rpi_ws281x
from lightberries.pixel import EnumLEDOrder, Pixel, PixelColors

LOGGER = logging.getLogger("LightBerries")


class WS281xString(Sequence[np.int_]):
    """Defines basic LED array data and functions."""

    def __init__(
        self,
        ledCount: int,
        pwmGPIOpin: int = 18,
        channelDMA: int = 10,
        frequencyPWM: int = 800000,
        invertSignalPWM: bool = False,
        ledBrightnessFloat: float = 0.75,
        channelPWM: int = 0,
        stripTypeLED: Any = None,
        gamma: Any = None,
        simulate: bool = False,
    ) -> None:
        """Creates a pixel array using the rpipixelStrip library and Pixels.

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
            simulate: dont use GPIO

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propogating an exception
            LightStringException: if something bad happens
        """
        self.ws281xPixelStrip = None
        self.simulated_ws281xPixelStrip = None
        self.simulate = simulate
        # catch error cases first
        if ledCount is None:
            raise LightStringException(
                "Cannot create LightString object without ledCount."
            )
        # use passed led count if it is valid
        if ledCount is not None:
            self._ledCount = ledCount
        if self.simulate:
            self.simulated_ws281xPixelStrip = np.zeros((ledCount), dtype=np.int32)
        else:
            # cant run GPIO stuff without root, tell the user if they forgot
            # linux check is just for debugging with fake GPIO on windows
            if (
                sys.platform == "linux" and not os.getuid() == 0
            ):  # pylint: disable = no-member
                raise LightStringException(
                    "GPIO functionality requires root privilege. Please run command again as root"
                )

            try:
                # create ws281x pixel strip
                self.ws281xPixelStrip = rpi_ws281x.PixelStrip(
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
                # try to force cleanup of underlying c objects when user exits
                atexit.register(self.__del__)

                self.ws281xPixelStrip.begin()
                self._ledCount = self.ws281xPixelStrip.numPixels()
                LOGGER.debug(
                    "%s Created WS281X object",
                    self.__class__.__name__,
                )
            except SystemExit:
                raise
            except KeyboardInterrupt:
                raise
            except LightBerryException:
                raise
            except Exception as ex:
                raise LightStringException from ex

    def __del__(
        self,
    ) -> None:
        """Properly disposes of the rpipixelStrip object.

        Prevents memory leaks (hopefully) that were happening in the rpi.PixelStrip module.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propogating an exception
            LightStringException: if something bad happens
        """
        # check if pixel strip has been created
        if isinstance(self.ws281xPixelStrip, rpi_ws281x.PixelStrip):
            # turn off leds
            self.off()
            # cleanup c memory usage
            try:
                self.ws281xPixelStrip._cleanup()
            except SystemExit:  # pylint:disable=try-except-raise
                raise
            except KeyboardInterrupt:  # pylint:disable=try-except-raise
                raise
            except LightBerryException:
                raise
            except Exception as ex:
                raise LightStringException from ex

    def __len__(
        self,
    ) -> int:
        """Return length of the light string (the number of LEDs).

        Returns:
            the number of LEDs in the array
        """
        if self.ws281xPixelStrip:
            return self.ws281xPixelStrip.numPixels()
        elif self.simulated_ws281xPixelStrip is not None:
            return len(self.simulated_ws281xPixelStrip)
        else:
            return 0

    @overload
    def __getitem__(  # noqa D105
        self,
        idx: int,
    ) -> np.ndarray[(3,), np.int32]:
        ...  # pylint: disable=pointless-statement

    @overload
    def __getitem__(  # noqa D105 # pylint: disable=function-redefined
        self,
        s: slice,
    ) -> np.ndarray[(3, Any), np.int32]:
        ...  # pylint: disable=pointless-statement

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
            LightBerryException: if propogating an exception
            LightStringException: if something bad happens
        """
        try:
            if isinstance(key, int):
                if self.ws281xPixelStrip:
                    return Pixel(self.ws281xPixelStrip.getPixelColor(key)).array
                elif self.simulated_ws281xPixelStrip is not None:
                    return Pixel(self.simulated_ws281xPixelStrip[key]).array
            else:
                if self.ws281xPixelStrip:
                    return ConvertPixelArrayToNumpyArray(
                        [Pixel(self.ws281xPixelStrip.getPixelColor(k)) for k in key]
                    )
                elif self.simulated_ws281xPixelStrip is not None:
                    return ConvertPixelArrayToNumpyArray(
                        [Pixel(self.simulated_ws281xPixelStrip[k]) for k in key]
                    )
        except SystemExit:  # pylint:disable=try-except-raise
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightStringException from ex

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
            LightBerryException: if propogating an exception
            LightStringException: if something bad happens
        """
        try:
            if isinstance(key, slice):
                for i, k in enumerate(key):
                    p = Pixel(value[i, :], EnumLEDOrder.RGB)
                    if self.ws281xPixelStrip:
                        self.ws281xPixelStrip.setPixelColor(key, p.int)
                    else:
                        self.simulated_ws281xPixelStrip[key] = p.int
            else:
                p = Pixel(value, EnumLEDOrder.RGB)
                if self.ws281xPixelStrip:
                    self.ws281xPixelStrip.setPixelColor(key, p.int)
                else:
                    self.simulated_ws281xPixelStrip[key] = p.int

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightStringException from ex

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
        if self.ws281xPixelStrip:
            self.ws281xPixelStrip.show()

    def off(
        self,
    ) -> None:
        """Turn all of the LEDs in the LightString off.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propogating an exception
            LightStringException: if something bad happens
        """
        for index in range(len(self)):
            try:
                self[index] = PixelColors.OFF
            except SystemExit:
                raise
            except KeyboardInterrupt:
                raise
            except LightBerryException:
                raise
            except Exception as ex:
                raise LightStringException from ex
        self.refresh()
