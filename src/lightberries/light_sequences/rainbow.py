"""Create a color gradient array."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence
from lightberries.light_sequences.transition import ColorTransitionSequence
from lightberries.pixel import PixelColors


class RainbowSequence(ArraySequence):
    """Create a color gradient array."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create a color gradient array.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            wrap: set true to wrap the transition from the last color back to the first
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
            name = RainbowSequence.__name__
        super().__init__(name=name, led_count=led_count, kwargs=kwargs)
        wrap = False
        if "wrap" in kwargs:
            wrap = kwargs["wrap"]
        try:
            self._sequence = ColorTransitionSequence(
                led_count=led_count,
                color_sequence=np.array(
                    [
                        PixelColors.RED.array,
                        PixelColors.GREEN.array,
                        PixelColors.BLUE.array,
                        PixelColors.VIOLET.array,
                    ],
                ),
                wrap=wrap,
            )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
