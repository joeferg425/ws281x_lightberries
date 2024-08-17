"""Creates a repeating LightPattern from a given sequence."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence
from lightberries.light_sequences.off import SequenceOff


class SequenceRepeating(ArraySequence):
    """Creates a repeating LightPattern from a given sequence."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create a repeating LightPattern from a given sequence.

        Args:
        ----
            name: the name of this pattern
            led_count: The length of the gradient array to create. (the number of LEDs in the rainbow)
            color_sequence: sequence of RGB tuples
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
            name = SequenceRepeating.__name__
        super().__init__(name=name, led_count=led_count, kwargs=kwargs)
        try:
            input_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
            if "color_sequence" in kwargs:
                input_sequence = kwargs["color_sequence"].copy()
            if len(input_sequence) == 0:
                self.sequence = np.zeros((0, 3))
            else:
                sequence_length = len(input_sequence)
                temp_array = SequenceOff(led_count=led_count).sequence
                if led_count > sequence_length:
                    temp_array[0:sequence_length] = input_sequence
                    for i in range(0, led_count, sequence_length):
                        if i + sequence_length <= led_count:
                            temp_array[i : i + sequence_length] = temp_array[0:sequence_length]
                        else:
                            extra = (i + sequence_length) % led_count
                            end = (i + sequence_length) - extra
                            temp_array[i:end] = temp_array[0 : (sequence_length - extra)]
                self._sequence = temp_array
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
