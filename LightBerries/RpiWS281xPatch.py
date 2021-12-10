"""patches the module after import to allow easier
interaction from the rest of LightBerries"""
import logging
import sys

LOGGER = logging.getLogger("LightBerries")

if sys.platform != "linux":
    # this lets me debug the rpi code in windows
    class rpi_ws281x:  # pylint: disable = invalid-name
        """fake class"""

        class PixelStrip:
            """fake class also"""

            rpi_ws281x = None

            def __init__(self, *_, **kwargs):
                """fake method"""
                self.count = 0
                if "num" in kwargs:
                    self.count = kwargs["num"]

            def begin(self):
                """fake method"""
                pass  # pylint: disable = unnecessary-pass

            def setPixelColor(self, index, color):
                """fake method"""
                pass  # pylint: disable = unnecessary-pass

            def show(self):
                """fake method"""
                pass  # pylint: disable = unnecessary-pass

            def _cleanup(self):
                """fake method"""
                pass  # pylint: disable = unnecessary-pass

            def numPixels(self):
                """fake method"""
                return self.count

    RpiWS281xClass = rpi_ws281x

else:
    import rpi_ws281x  # pylint: disable = import-error
    import rpi_ws281x as RpiWS281xClass  # pylint: disable = import-error

    def _monkeypatch__setitem__(self, pos, value):  # pylint: disable = invalid-name
        """Set the 24-bit RGB color value at the provided position or slice of
            positions.

        joeferg425: MONKEY PATCH: calls to 'ws2811_led_set' needed to have the
            third argument forced to int type
        """
        # Handle if a slice of positions are passed in by setting the
        # appropriate LED data values to the provided values.
        if isinstance(pos, slice):
            index = 0
            for index in range(*pos.indices(self.size)):
                RpiWS281xClass.ws2811_led_set(self.channel, index, int(value[index]))
                index += 1
        # Else assume the passed in value is a number to the position.
        else:
            return RpiWS281xClass.ws2811_led_set(self.channel, pos, int(value))

    try:
        rpi_ws281x.rpi_ws281x._LED_Data.__setitem__ = (  # pylint: disable = protected-access
            _monkeypatch__setitem__
        )
    except Exception as ex:
        LOGGER.exception("Failed rpi_ws281x Monkey Patch: %s", str(ex))
