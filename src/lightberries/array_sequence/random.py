"""Creates an array of random colors."""

from __future__ import annotations

import random

from lightberries.array_sequence.array_sequence import ArraySequence
from lightberries.base.pixel import Pixel

RED = 0
GREEN = 1
BLUE = 2


class SequenceRandom(ArraySequence):
    """Creates an array of random colors."""

    def __init__(
        self,
        led_count: int | None = None,
        name: str | None = None,
    ) -> None:
        """Create an array of random colors.

        Args:
        ----
            name: the name of this pattern
            pixel_sequence: array of pixels
            led_count: the number of random colors to generate for the array

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceRandom.__name__
        super().__init__(
            led_count=led_count,
            name=name,
        )

        if led_count is None:
            led_count = self.get_monthly_color_sequence().led_count
        temp_array: list[Pixel] = []
        for _ in range(led_count):
            # prevent 255, 255, 255
            exclusion = random.randint(0, 2)
            if exclusion != RED:
                red_led = random.randint(0, 255)
            else:
                red_led = 0
            if exclusion != GREEN:
                green_led = random.randint(0, 255)
            else:
                green_led = 0
            if exclusion != BLUE:
                blue_led = random.randint(0, 255)
            else:
                blue_led = 0
            temp_array.append(Pixel([red_led, green_led, blue_led]))
        self._array = temp_array
