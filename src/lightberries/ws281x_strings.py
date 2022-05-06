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
from lightberries.exceptions import WS281xStringException, LightBerryException
from lightberries.rpiws281x import rpi_ws281x
from lightberries.pixel import Pixel, PixelColors

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
        self.ws281xPixelStrip = None
        self.simulate = simulate
        # catch error cases first
        if ledCount is None or not isinstance(ledCount, int):
            raise WS281xStringException(f"Cannot create LightString with ledCount: {ledCount}.")
        # use passed led count if it is valid
        self._ledCount = ledCount
        if self.simulate:
            import lightberries.rpiws281x_patch as rpiws281x  # noqa

            # cant run GPIO stuff without root, tell the user if they forgot
            # linux check is just for debugging with fake GPIO on windows
        if not self.simulate:
            if sys.platform == "linux" and not os.getuid() == 0:  # pylint: disable = no-member  # pragma: no cover
                raise WS281xStringException(
                    "GPIO functionality requires root privilege. Please run command again as root"
                )
        self._instantiate_pixelstrip(
            pwmGPIOpin=pwmGPIOpin,
            channelDMA=channelDMA,
            ledCount=ledCount,
            frequencyPWM=frequencyPWM,
            channelPWM=channelPWM,
            invertSignalPWM=invertSignalPWM,
            gamma=gamma,
            stripTypeLED=stripTypeLED,
            ledBrightnessFloat=ledBrightnessFloat,
        )

    def _instantiate_pixelstrip(
        self,
        pwmGPIOpin: int,
        channelDMA: int,
        ledCount: int,
        frequencyPWM: int,
        channelPWM: int,
        invertSignalPWM: bool,
        gamma: float,
        stripTypeLED: Any,
        ledBrightnessFloat: Any,
    ) -> None:
        try:  # pragma: no cover
            # create ws281x pixel strip
            self.ws281xPixelStrip = rpi_ws281x.PixelStrip(  # pragma: no cover
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
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise WS281xStringException from ex

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
        if isinstance(self.ws281xPixelStrip, rpi_ws281x.PixelStrip):
            # turn off LEDs
            self.off()
            # cleanup c memory usage
            try:
                self.ws281xPixelStrip._cleanup()
            except SystemExit:  # pylint:disable=try-except-raise  # pragma: no cover
                raise
            except KeyboardInterrupt:  # pylint:disable=try-except-raise  # pragma: no cover
                raise
            except LightBerryException:  # pragma: no cover
                raise
            except Exception as ex:  # pragma: no cover
                raise WS281xStringException from ex

    def __len__(
        self,
    ) -> int:
        """Return length of the light string (the number of LEDs).

        Returns:
            the number of LEDs in the array
        """
        if self.ws281xPixelStrip:
            return self.ws281xPixelStrip.numPixels()

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
        try:
            if isinstance(key, int):
                if key >= len(self):
                    raise IndexError()
                return Pixel(self.ws281xPixelStrip.getPixelColor(key)).array
            elif isinstance(key, (np.int_, np.int32)):
                if int(key) >= len(self):
                    raise IndexError()
                return Pixel(self.ws281xPixelStrip.getPixelColor(int(key))).array
            else:
                return ConvertPixelArrayToNumpyArray(
                    [Pixel(self.ws281xPixelStrip.getPixelColor(k)) for k in range(self._ledCount)[key]]
                )
        except SystemExit:  # pylint:disable=try-except-raise  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except IndexError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise WS281xStringException from ex

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
        try:
            if isinstance(key, slice):
                for i, j in enumerate(range(self._ledCount)[key]):
                    p = Pixel(value[i, :])
                    self.ws281xPixelStrip.setPixelColor(j, p.int)
            elif isinstance(key, (np.int_, np.int32)):
                if int(key) >= len(self):
                    raise IndexError()
                p = Pixel(value)
                self.ws281xPixelStrip.setPixelColor(int(key), p.int)
            else:
                if key >= len(self):
                    raise IndexError()
                p = Pixel(value)
                self.ws281xPixelStrip.setPixelColor(key, p.int)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except IndexError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise WS281xStringException from ex

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
            except LightBerryException:  # pragma: no cover
                raise
            except Exception as ex:  # pragma: no cover
                raise WS281xStringException from ex
        self.refresh()
