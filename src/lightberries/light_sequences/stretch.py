"""Takes a sequence of input colors and repeats each element the requested number of times."""

from __future__ import annotations

from typing import Any

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence
from lightberries.light_sequences.off import SequenceOff


class SequenceStretch(ArraySequence):
    """Takes a sequence of input colors and repeats each element the requested number of times."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Take a sequence of input colors and repeats each element the requested number of times.

        Args:
        ----
            name: the name of this pattern
            colorSequence: a list of pixels defining the desired colors in the output array
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightPatternException: if something bad happens

        """
        if name is None:
            name = SequenceStretch.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)
        try:
            input_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
            if "input_sequence" in kwargs:
                input_sequence = kwargs["input_sequence"].copy()
            color_sequence_length = input_sequence.shape[0]
            repeats = int(led_count / color_sequence_length)
            if led_count % color_sequence_length > 0:
                repeats += 1
            temp_array = SequenceOff(color_sequence_length * repeats).sequence
            for i in range(color_sequence_length):
                temp_array[i * repeats : (i + 1) * repeats] = input_sequence[i]
            self._sequence = temp_array[:led_count]
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
