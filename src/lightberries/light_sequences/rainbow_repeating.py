"""Creates a repeating gradient."""

from __future__ import annotations

from typing import Any

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence
from lightberries.light_sequences.rainbow import SequenceRainbow
from lightberries.light_sequences.sequence_repeating import SequenceRepeating


class SequenceRainbowRepeating(ArraySequence):
    """Creates a repeating gradient."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Create a repeating gradient .

        Args:
        ----
            name: the name of this pattern
            led_count: the number of LEDs to involve in the rainbow
            segment_length: the length of each mini rainbow in the repeating sequence
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
            name = SequenceRainbowRepeating.__name__
        super().__init__(name=name, led_count=led_count, kwargs=kwargs)
        segment_length = led_count // 4
        if "segment_length" in kwargs:
            segment_length = kwargs["segment_length"]
        try:
            self._sequence = SequenceRepeating(
                led_count=led_count,
                color_sequence=SequenceRainbow(led_count=segment_length, wrap=True).sequence,
            ).sequence
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
