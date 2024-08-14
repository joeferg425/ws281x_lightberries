"""Creates an array of random colors."""

from __future__ import annotations

import random
from typing import Any

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence


class RandomSequence(ArraySequence):
    """Creates an array of random colors."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create an array of random colors.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of random colors to generate for the array
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPatternException: if something bad happens

        """
        if name is None:
            name = RandomSequence.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)
        try:
            temp_array = ArraySequence.PixelArrayOff(led_count)
            for i in range(led_count):
                # prevent 255, 255, 255
                exclusion = random.randint(0, 2)
                if exclusion != 0:
                    red_led = random.randint(0, 255)
                else:
                    red_led = 0
                if exclusion != 1:
                    green_led = random.randint(0, 255)
                else:
                    green_led = 0
                if exclusion != 2:
                    blue_led = random.randint(0, 255)
                else:
                    blue_led = 0
                temp_array[i] = [red_led, green_led, blue_led]
            self._sequence = temp_array
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
