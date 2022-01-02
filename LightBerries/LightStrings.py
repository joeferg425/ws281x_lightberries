"""Defines basic light string data and functions."""
import os
import sys
import atexit
import inspect
import time
import logging
from typing import Any, Optional, Sequence, Union, overload
from nptyping import NDArray
import numpy as np
from LightBerries.LightBerryExceptions import LightStringException
from LightBerries.RpiWS281xPatch import rpi_ws281x
from LightBerries.LightPixels import Pixel, PixelColors

LOGGER = logging.getLogger("LightBerries")


class LightString(Sequence[np.int_]):
    """Defines basic LED array data and functions."""

    def __init__(
        self,
        ledCount: Optional[int] = None,
        pixelStrip: rpi_ws281x.PixelStrip = None,
    ) -> None:
        """Creates a pixel array using the rpipixelStrip library and Pixels.

        Args:
            ledCount: the number of LEDs desired in the LightString
            pixelStrip: the ws281x object that actually controls the LED signaling

        Raises:
            Warning: if something unexpected could happen
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightStringException: if something bad happens
        """
        # cant run GPIO stuff without root, tell the user if they forgot
        # linux check is just for debugging with fake GPIO on windows
        if sys.platform == "linux" and not os.getuid() == 0:  # pylint: disable = no-member
            raise LightStringException(
                "GPIO functionality requires root privilege. Please run command again as root"
            )

        # catch error cases first
        if ledCount is None and pixelStrip is None:
            raise LightStringException(
                "Cannot create LightString object without ledCount or " + "pixelStrip object being specified"
            )
        # catch error cases first
        if ledCount is not None and pixelStrip is not None:
            raise Warning(
                "ledCount is overridden when pixelStrip is and ledcount "
                + "are both passed to LightString constructor"
            )

        try:
            # use passed led count if it is valid
            if ledCount is not None:
                self._ledCount = ledCount

            # used passed pixel strip if it is not none
            if pixelStrip is not None:
                self.pixelStrip = pixelStrip
                self.pixelStrip.begin()
                self._ledCount = self.pixelStrip.numPixels()
            LOGGER.debug(
                "%s.%s Created WS281X object",
                self.__class__.__name__,
                inspect.stack()[0][3],
            )
        except SystemExit:  # pylint:disable=try-except-raise
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise LightStringException(str(ex)).with_traceback(ex.__traceback__)

        try:
            # validate led count
            if not isinstance(self._ledCount, int):
                raise LightStringException(
                    f'Cannot create LightString object with LED count "{self._ledCount}"',
                )
            # if led count is good, create our pixel sequence
            self.rgbArray: NDArray[(3, Any), np.int32] = np.zeros((self._ledCount, 3))
            self.rgbArray[:] = np.array([Pixel().array for i in range(self._ledCount)])
            LOGGER.debug(
                "%s.%s Created Numpy Light array",
                self.__class__.__name__,
                inspect.stack()[0][3],
            )
        except SystemExit:  # pylint:disable=try-except-raise
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise LightStringException(str(ex)).with_traceback(ex.__traceback__)

        # try to force cleanup of underlying c objects when user exits
        atexit.register(self.__del__)

    def __del__(
        self,
    ) -> None:
        """Properly disposes of the rpipixelStrip object.

        Prevents memory leaks (hopefully) that were happening in the rpi.PixelStrip module.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightStringException: if something bad happens
        """
        # check if pixel strip has been created
        if isinstance(self.pixelStrip, rpi_ws281x.PixelStrip):
            # turn off leds
            self.off()
            # cleanup c memory usage
            try:
                self.pixelStrip._cleanup()
            except SystemExit:  # pylint:disable=try-except-raise
                raise
            except KeyboardInterrupt:  # pylint:disable=try-except-raise
                raise
            except Exception as ex:
                LOGGER.exception("Failed to clean up WS281X object: %s", str(ex))
                raise LightStringException(str(ex)).with_traceback(ex.__traceback__)

    def __len__(
        self,
    ) -> int:
        """Return length of the light string (the number of LEDs).

        Returns:
            the number of LEDs in the array
        """
        if self.rgbArray is not None:
            return len(self.rgbArray)
        else:
            return 0

    @overload
    def __getitem__(  # noqa D105
        self,
        idx: int,
    ) -> NDArray[(3,), np.int32]:
        ...  # pylint: disable=pointless-statement

    @overload
    def __getitem__(  # noqa D105 # pylint: disable=function-redefined
        self,
        s: slice,
    ) -> NDArray[(3, Any), np.int32]:
        ...  # pylint: disable=pointless-statement

    def __getitem__(  # pylint: disable=function-redefined
        self, key: Union[int, slice]
    ) -> Union[NDArray[(3,), np.int32], NDArray[(3, Any), np.int32]]:
        """Return a LED index or slice from LED array.

        Args:
            key: an index of a single LED, or a slice specifying a range of LEDs

        Returns:
            the LED value or values as requested

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightStringException: if something bad happens
        """
        try:
            if isinstance(self.rgbArray, np.ndarray):
                return self.rgbArray[key].array
            else:
                raise LightStringException("Cannot index into uninitialized LightString object")
        except SystemExit:  # pylint:disable=try-except-raise
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except Exception as ex:
            LOGGER.exception('Failed to get key "%s" from %s: %s', key, self.rgbArray, ex)
            raise LightStringException(str(ex)).with_traceback(ex.__traceback__)

    def __setitem__(
        self,
        key: Union[int, slice],
        value: Union[NDArray[(3,), np.int32], NDArray[(3, Any), np.int32]],
    ) -> None:
        """Set LED value(s) in the array.

        Args:
            key: the index or slice specifying one or more LED indices
            value: the RGB value or values to assign to the given LED indices

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightStringException: if something bad happens
        """
        try:
            if isinstance(self.rgbArray, np.ndarray):
                if isinstance(key, slice):
                    if isinstance(value, np.ndarray):
                        self.rgbArray.__setitem__(key, value)
                    elif isinstance(value, Sequence):
                        self.rgbArray.__setitem__(key, [Pixel(v).array for v in value])
                    else:
                        raise LightStringException(
                            "Cannot assign multiple indices of LightString using a single value"
                        )
                else:
                    if isinstance(value, np.ndarray):
                        self.rgbArray.__setitem__(key, value)
                    elif isinstance(value, Pixel):
                        self.rgbArray.__setitem__(key, Pixel(value).array)
                    else:
                        raise LightStringException(
                            "Cannot assign single index of LightString using multiple values"
                        )
            else:
                raise LightStringException("Cannot index into uninitialized LightString object")
        except SystemExit:  # pylint:disable=try-except-raise
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except Exception as ex:
            LOGGER.exception("Failed to set light %s to value %s: %s", key, value, ex)
            raise LightStringException(str(ex)).with_traceback(ex.__traceback__)

    def __enter__(
        self,
    ) -> "LightString":
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

    def off(
        self,
    ) -> None:
        """Turn all of the LEDs in the LightString off.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightStringException: if something bad happens
        """
        for index in range(len(self.rgbArray)):
            try:
                self[index] = PixelColors.OFF.array
            except SystemExit:  # pylint:disable=try-except-raise
                raise
            except KeyboardInterrupt:  # pylint:disable=try-except-raise
                raise
            except Exception as ex:
                LOGGER.exception(
                    "Failed to set pixel %s in WS281X to value %s: %s",
                    index,
                    LightString(0),
                    ex,
                )
                raise LightStringException(str(ex)).with_traceback(ex.__traceback__)
        self.refresh()

    def refresh(
        self,
    ) -> None:
        """Update the ws281x signal using the numpy array.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightStringException: if something bad happens
        """
        try:
            # define callback for map method (fast iterator)
            def SetPixel(irgb):
                try:
                    i = irgb[0]
                    rgb = irgb[1]
                    value = (int(rgb[0]) << 16) + (int(rgb[1]) << 8) + int(rgb[2])
                    self.pixelStrip.setPixelColor(i, value)
                except SystemExit:  # pylint:disable=try-except-raise
                    raise
                except KeyboardInterrupt:  # pylint:disable=try-except-raise
                    raise
                except Exception as ex:
                    LOGGER.exception(
                        "Failed to set pixel %d in WS281X to value %d: %s",
                        i,
                        value,
                        str(ex),
                    )
                    raise LightStringException(str(ex)).with_traceback(ex.__traceback__)

            # copy this class's array into the ws281x array
            list(
                map(
                    SetPixel,
                    enumerate(self.rgbArray),
                )
            )
            # send the signal out
            self.pixelStrip.show()
        except SystemExit:  # pylint:disable=try-except-raise
            raise
        except KeyboardInterrupt:  # pylint:disable=try-except-raise
            raise
        except Exception as ex:
            LOGGER.exception('Function call "show" in WS281X object failed: %s', str(ex))
            raise LightStringException(str(ex)).with_traceback(ex.__traceback__)


if __name__ == "__main__":
    LOGGER.info("Running LightString")
    # the number of pixels in the light string
    PIXEL_COUNT = 100
    # GPIO pin to use for PWM signal
    GPIO_PWM_PIN = 18
    # DMA channel
    DMA_CHANNEL = 5
    # frequency to run the PWM signal at
    PWM_FREQUENCY = 800000
    GAMMA = None
    LED_STRIP_TYPE = None
    INVERT = False
    PWM_CHANNEL = 0
    with LightString(
        pixelStrip=rpi_ws281x.PixelStrip(
            num=PIXEL_COUNT,
            pin=GPIO_PWM_PIN,
            dma=DMA_CHANNEL,
            freq_hz=PWM_FREQUENCY,
            channel=PWM_CHANNEL,
            invert=INVERT,
            gamma=GAMMA,
            strip_type=LED_STRIP_TYPE,
        ),
    ) as liteStr:
        liteStr.refresh()
        p = Pixel((255, 0, 0))
        liteStr[4] = PixelColors.RED
        liteStr.refresh()
        time.sleep(1)
