"""Creates an array of random colors."""

from __future__ import annotations

import random
from typing import Any

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence
from lightberries.light_sequences.off import OffSequence


class PseudoRandomSequence(ArraySequence):
    """Creates an array of random colors."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create an array of random colors.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of random colors to generate for the array
            color_sequence: optional parameter from which to draw the pseudo random colors from
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
            name = PseudoRandomSequence.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)
        try:
            input_sequence = None
            temp_array = OffSequence(led_count=led_count)
            input_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
            if "color_sequence" in kwargs:
                input_sequence = kwargs["color_sequence"].copy()
            input_sequence_length = input_sequence.shape[0]
            if input_sequence_length == 0:
                input_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
                input_sequence_length = input_sequence.shape[0]
            for i in range(led_count):
                temp_array[i] = input_sequence[random.randint(0, input_sequence_length - 1)]
            self._sequence = temp_array
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
