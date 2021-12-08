import os
import sys
import atexit
import inspect
import numpy as np
import time
import logging
from typing import Any, Optional, Sequence, Union, List, overload
from LightBerries.rpi_ws281x_patch import rpi_ws281x
from LightBerries.Pixels import Pixel, PixelColors
from nptyping import NDArray

LOGGER = logging.getLogger("LightBerries")


class LightString(Sequence[np.int_]):
    def __init__(
        self,
        ledCount: Optional[int] = None,
        pixelStrip: rpi_ws281x.PixelStrip = None,
        debug: bool = False,
    ):
        """
        Creates a pixel array using the rpipixelStrip library and Pixels.

        ledCount: int
            the number of LEDs desired in the LightString

        pixelStrip: rpipixelStrip.PixelStrip
            the ws281x object that actually controls the LED signaling

        debug: bool
            set true for debug messages
        """

        # use debug setting
        if debug is True:
            LOGGER.setLevel(logging.DEBUG)
            LOGGER.debug("%s.%s Debugging mode", self.__class__.__name__, inspect.stack()[0][3])

        # cant run GPIO stuff without root, tell the user if they forgot
        # linux check is just for debugging with fake GPIO on windows
        if sys.platform == "linux" and not os.getuid() == 0:
            raise Exception("GPIO functionality requires root privilege. Please run command again as root")

        # catch error cases first
        if ledCount is None and pixelStrip is None:
            raise Exception(
                "Cannot create LightString object without ledCount or " + "pixelStrip object being specified"
            )
        # catch error cases first
        if ledCount is not None and pixelStrip is not None:
            raise Warning(
                "ledCount is overridden when pixelStrip is and ledcount are both passed to LightString constructor"
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
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

        try:
            # validate led count
            if not isinstance(self._ledCount, int):
                raise Exception(
                    'Cannot create LightString object with LED count "{}"'.format(self._ledCount),
                )
            # if led count is good, create our pixel sequence
            else:
                self._lights: NDArray[(3, Any), np.int32] = np.zeros((self._ledCount, 3))
                self._lights[:] = np.array([Pixel().array for i in range(self._ledCount)])
                LOGGER.debug(
                    "%s.%s Created Numpy Light array",
                    self.__class__.__name__,
                    inspect.stack()[0][3],
                )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                inspect.stack()[0][3],
                ex,
            )
            raise

        # try to force cleanup of underlying c objects when user exits
        atexit.register(self.__del__)

    def __del__(self) -> None:
        """
        Properly disposes of the rpipixelStrip object.
        Prevents (hopefully) memory leaks that were happening in the rpipixelStrip module.
        """
        # check if pixel strip has been created
        if isinstance(self.pixelStrip, rpi_ws281x.PixelStrip):
            # turn off leds
            self.off()
            # cleanup c memory usage
            try:
                self.pixelStrip._cleanup()
            except SystemExit:
                raise
            except KeyboardInterrupt:
                raise
            except Exception as ex:
                LOGGER.exception("Failed to clean up WS281X object: {}".format(ex))
                raise

    def __len__(self) -> int:
        """
        return length of the light string (the number of LEDs)
        """
        if self._lights is not None:
            return len(self._lights)
        else:
            return 0

    @overload
    def __getitem__(self, idx: int) -> NDArray[(3,), np.int32]:
        """for mypy"""
        ...

    @overload
    def __getitem__(self, s: slice) -> NDArray[(3, Any), np.int32]:
        """for mypy"""
        ...

    def __getitem__(
        self, key: Union[int, slice]
    ) -> Union[NDArray[(3,), np.int32], NDArray[(3, Any), np.int32]]:
        """
        return a LED(s) from array
        """
        try:
            if isinstance(self._lights, np.ndarray):
                return self._lights[key].array
            else:
                raise Exception("Cannot index into uninitialized LightString object")
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception('Failed to get key "%s" from %s: %s', key, self._lights, ex)
            raise

    def __setitem__(
        self, key: Union[int, slice], value: Union[NDArray[(3,), np.int32], NDArray[(3, Any), np.int32]]
    ) -> None:
        """
        set LED value(s) in array
        """
        try:
            if isinstance(self._lights, np.ndarray):
                if isinstance(key, slice):
                    if isinstance(value, np.ndarray):
                        self._lights.__setitem__(key, value)
                    elif isinstance(value, Sequence):
                        self._lights.__setitem__(key, [Pixel(v).array for v in value])
                    else:
                        raise Exception("Cannot assign multiple indices of LightString using a single value")
                else:
                    if isinstance(value, np.ndarray):
                        self._lights.__setitem__(key, value)
                    elif isinstance(value, Pixel):
                        self._lights.__setitem__(key, Pixel(value).array)
                    else:
                        raise Exception("Cannot assign single index of LightString using multiple values")
            else:
                raise Exception("Cannot index into uninitialized LightString object")
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception("Failed to set light %s to value %s: %s", key, value, ex)
            raise

    def __enter__(self) -> "LightString":
        """ """
        return self

    def __exit__(self, *args) -> None:
        """ """
        self.__del__()

    def setDebugLevel(self, level: int):
        """
        set the logging level
        """
        LOGGER.setLevel(level)

    def off(self):
        """
        turn all of the LEDs in the LightString off
        """
        for index in range(len(self._lights)):
            try:
                self[index] = PixelColors.OFF.array
            except SystemExit:
                raise
            except KeyboardInterrupt:
                raise
            except Exception as ex:
                LOGGER.exception(
                    "Failed to set pixel %s in WS281X to value %s: %s",
                    index,
                    LightString(0),
                    ex,
                )
                raise
        self.refresh()

    def refresh(self):
        """
        update ws281x signal using the numpy array
        """
        # should be faster than method below?
        def set_pixel(irgb):
            i = irgb[0]
            rgb = irgb[1]
            value = (int(rgb[0]) << 16) + (int(rgb[1]) << 8) + int(rgb[2])
            self.pixelStrip.setPixelColor(i, value)

        list(
            map(
                set_pixel,
                enumerate(self._lights),
            )
        )

        # for index, light in enumerate(self._lights):
        #     try:
        #         if index > 0:
        #             self.pixelStrip.setPixelColor(int(index), light._value)
        #         else:
        #             self.pixelStrip.setPixelColor(int(index), 0)
        #     except SystemExit:
        #         raise
        #     except KeyboardInterrupt:
        #         raise
        #     except Exception as ex:
        #         LOGGER.exception(
        #             "Failed to set pixel %s in WS281X to value %s: %s",
        #             index,
        #             light._value,
        #             ex,
        #         )
        #         raise
        try:
            self.pixelStrip.show()
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception('Function call "show" in WS281X object failed: {}'.format(ex))
            raise


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
        debug=True,
    ) as liteStr:
        liteStr.refresh()
        p = Pixel((255, 0, 0))
        liteStr[4] = PixelColors.RED
        liteStr.refresh()
        time.sleep(1)
