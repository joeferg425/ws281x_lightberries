"""Patches the rpi_ws281x module after import.

This allows easier interaction from the rest of LightBerries
"""
from __future__ import annotations
import logging
import numpy as np

LOGGER = logging.getLogger("LightBerries")


class PixelStrip:
    """Fake class that lets me debug the ws281x code in windows."""

    rpi_ws281x = None

    def __init__(self, num: int, *_, **kwargs):
        self.fake = np.zeros((num), dtype=np.int32)
        """Fake method.

        Args:
            _: ignored
            kwargs: ignored
        """
        if "num" in kwargs:
            self.count = kwargs["num"]  # pragma: no cover

    @property
    def count(self) -> int:
        return len(self.fake)

    def begin(self):
        """Fake method."""
        pass  # pylint: disable = unnecessary-pass

    def setPixelColor(self, index: int, color: int):
        """Fake method.

        Args:
            index: ignored
            color: ignored
        """
        self.fake[index] = color

    def getPixelColor(self, index: int) -> int:
        """Fake method.

        Args:
            index: ignored

        Returns:
            ignored
        """
        return self.fake[index]

    def show(self):
        """Fake method."""
        pass  # pylint: disable = unnecessary-pass

    def _cleanup(self):
        """Fake method."""
        pass  # pylint: disable = unnecessary-pass

    def numPixels(self) -> int:
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
    return (channel, index, value)  # pragma: no cover
