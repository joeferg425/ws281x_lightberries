"""Patches the rpi_ws281x module after import.

This allows easier interaction from the rest of LightBerries
"""
from __future__ import annotations
import logging
import sys

LOGGER = logging.getLogger("LightBerries")

if sys.platform != "linux":
    import lightberries.rpiws281x_patch as rpi_ws281x
else:
    import rpi_ws281x  # type: ignore windows error #pragma: no cover

    def _monkeypatch__setitem__(self, pos, value):  # pragma: no cover
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
                rpi_ws281x.ws2811_led_set(self.channel, index, int(value[index]))  # pylint: disable=no-member
                index += 1
        # Else assume the passed in value is a number to the position.
        else:
            return rpi_ws281x.ws2811_led_set(self.channel, pos, int(value))  # pylint: disable=no-member

    try:  # pragma: no cover
        rpi_ws281x.rpi_ws281x._LED_Data.__setitem__ = (
            _monkeypatch__setitem__  # pylint: disable = protected-access#pragma: no cover
        )
    except Exception as ex:  # pragma: no cover
        LOGGER.exception("Failed rpi_ws281x Monkey Patch: %s", str(ex))  # pragma: no cover
