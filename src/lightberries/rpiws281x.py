"""Patches the rpi_ws281x module after import.

This allows easier interaction from the rest of LightBerries
"""

from __future__ import annotations

import logging
import sys

LOGGER = logging.getLogger("LightBerries")

if sys.platform != "linux":
    from lightberries.rpiws281x_patch import FakePixelStrip as PixelStrip  # type: ignore  # noqa: F401, I001, PGH003, RUF100
else:
    from rpi_ws281x import PixelStrip as PixelStrip  # type: ignore windows error #pragma: no cover
