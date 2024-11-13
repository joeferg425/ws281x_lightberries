"""Patches the rpi_ws281x module after import.

This allows easier interaction from the rest of LightBerries
"""

from __future__ import annotations

from typing import cast

import numpy as np


class FakePixelStrip:
    """Fake class that lets me debug the ws281x code in windows."""

    rpi_ws281x = None

    def __init__(self, num: int, *_, **kwargs) -> None:  # type: ignore  # noqa: ANN002, ANN003, D107, PGH003
        self.fake = np.zeros((num), dtype=np.int32)
        """Fake method."""
        if "num" in kwargs:
            self.size: int = cast("int", kwargs["num"])  # pragma: no cover

    def __len__(self) -> int:
        return len(self.fake)

    def begin(self) -> None:
        """Fake method."""
        # pylint: disable = unnecessary-pass # pragma: no cover

    def setPixelColor(self, n: int, color: int) -> None:  # noqa: N802
        """Fake method."""
        self.fake[n] = color

    def setPixelColorRGB(self, n: int, red: int, green: int, blue: int, white: int = 0) -> None:  # noqa: N802
        """Fake method."""

    def getPixelColor(self, index: int) -> int:  # noqa: N802
        """Fake method."""
        return self.fake[index]

    def show(self) -> None:
        """Fake method."""

    def _cleanup(self) -> None:
        """Fake method."""

    def __getitem__(self, pos: int | slice) -> int | list[int]:
        """Fake method."""
        return 0

    def __setitem__(self, pos: int | slice, value: int | list[int]) -> None:
        """Fake method."""
