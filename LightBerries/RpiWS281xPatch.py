"""Patches the rpi_ws281x module after import.

This allows easier interaction from the rest of LightBerries
"""
import logging
import sys

LOGGER = logging.getLogger("LightBerries")

if sys.platform != "linux":
    # this lets me debug the rpi code in windows
    class rpi_ws281x:  # pylint: disable = invalid-name
        """Fake class that lets me debug rpi code in windows."""

        class PixelStrip:
            """Fake class that lets me debug the ws281x code in windows."""

            rpi_ws281x = None

            def __init__(self, *_, **kwargs):
                """Fake method.

                Args:
                    _: ignored
                    kwargs: ignored
                """
                self.count = 0
                if "num" in kwargs:
                    self.count = kwargs["num"]

            def begin(self):
                """Fake method."""
                pass  # pylint: disable = unnecessary-pass

            def setPixelColor(self, index, color):
                """Fake method.

                Args:
                    index: ignored
                    color: ignored
                """
                pass  # pylint: disable = unnecessary-pass

            def show(self):
                """Fake method."""
                pass  # pylint: disable = unnecessary-pass

            def _cleanup(self):
                """Fake method."""
                pass  # pylint: disable = unnecessary-pass

            def numPixels(self):
                """Fake method.

                Returns:
                    count
                """
                return self.count

        @staticmethod
        def ws2811_led_set(channel, index, value):
            """Fake method.

            Args:
                channel: ignored
                index: ignored
                value: ignored

            Returns:
                garbage
            """
            return (channel, index, value)  # pylint: disable = unnecessary-pass

    RpiWS281xClass = rpi_ws281x

else:
    import rpi_ws281x  # pylint: disable = import-error
    import rpi_ws281x as RpiWS281xClass  # pylint: disable = import-error

    def _monkeypatch__setitem__(self, pos, value):  # pylint: disable = invalid-name
        """Set the 24-bit RGB color value at the position or slice.

        MONKEY PATCH: calls to 'ws2811_led_set' needed to have the
            third argument forced to int type

        Args:
            self: the self object
            pos: LED position (index)
            value: LED value (color)

        Returns:
            patch
        """
        # Handle if a slice of positions are passed in by setting the
        # appropriate LED data values to the provided values.
        if isinstance(pos, slice):
            index = 0
            for index in range(*pos.indices(self.size)):
                RpiWS281xClass.ws2811_led_set(  # pylint: disable=no-member
                    self.channel, index, int(value[index])
                )
                index += 1
        # Else assume the passed in value is a number to the position.
        else:
            return RpiWS281xClass.ws2811_led_set(self.channel, pos, int(value))  # pylint: disable=no-member

    try:
        rpi_ws281x.rpi_ws281x._LED_Data.__setitem__ = (  # pylint: disable = protected-access
            _monkeypatch__setitem__
        )
    except Exception as ex:
        LOGGER.exception("Failed rpi_ws281x Monkey Patch: %s", str(ex))
