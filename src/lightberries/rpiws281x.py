"""Patches the rpi_ws281x module after import.

This allows easier interaction from the rest of LightBerries
"""

from __future__ import annotations

import sys

if sys.platform != "linux":
    from lightberries.rpiws281x_patch import (  # type: ignore  # noqa: F401, I001, PGH003, RUF100
        FakePixelStrip as PixelStrip,
    )
else:
    from rpi_ws281x import (
        PixelStrip as PixelStrip,  # type: ignore windows error #pragma: no cover
    )
