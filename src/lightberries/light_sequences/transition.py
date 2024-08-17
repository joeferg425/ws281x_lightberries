"""A more versatile version of CreateRainbow."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.exceptions import LightBerryError, PatternError
from lightberries.light_sequences.base import ArraySequence
from lightberries.light_sequences.off import SequenceOff


class SequenceTransition(ArraySequence):
    """A more versatile version of CreateRainbow."""

    def __init__(
        self,
        led_count: int,
        name: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """More versatile version of CreateRainbow.

        The user specifies a color sequence and the number of steps (LEDs)
        in the transition from one color to the next.

        Args:
        ----
            name: the name of this pattern
            led_count: The total totalArrayLength of the final sequence in LEDs. This
                parameter is optional and defaults to LED_INDEX_COUNT
            wrap: set true to wrap the transition from the last color back to the first
            color_sequence: a sequence of colors to merge between
            kwargs: args for patterns

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightPatternException: if something bad happens

        """
        if name is None:
            name = SequenceTransition.__name__
        super().__init__(
            name=name,
            led_count=led_count,
            kwargs=kwargs,
        )
        try:
            input_sequence = ArraySequence.DEFAULT_COLOR_SEQUENCE
            if "color_sequence" in kwargs:
                input_sequence = kwargs["color_sequence"].copy()
            # get length of sequence
            if len(input_sequence.shape):
                sequence_length = input_sequence.shape[0]
            if sequence_length == 0 or led_count == 0:
                self._sequence = np.zeros((0, 3))
            count = 0
            step_count = None
            previous_step_count = 0
            wrap_offset = 0
            if "wrap" in kwargs:
                if bool(kwargs["wrap"]):
                    wrap_offset = 0
                else:
                    wrap_offset = 1
            # figure out how many LEDs per color change
            if step_count is None:
                step_count = led_count // (sequence_length - wrap_offset)
                previous_step_count = step_count
            # create temporary array
            temp_array = SequenceOff(led_count).sequence
            # step through color sequence
            for color_index in range(sequence_length - wrap_offset):
                if color_index == sequence_length - 1 or color_index == sequence_length - 2:
                    step_count = led_count - count
                # figure out the current and next colors
                this_color = input_sequence[color_index]
                next_color = input_sequence[(color_index + 1) % sequence_length]
                # handle red, green, and blue individually
                for rgb_index in range(len(this_color)):
                    i = color_index * previous_step_count
                    # linspace creates the array of values from arg1, to arg2, in exactly arg3 steps
                    temp_array[i : (i + step_count), rgb_index] = np.linspace(
                        this_color[rgb_index],
                        next_color[rgb_index],
                        step_count,
                    )
                count += step_count
            self._sequence = temp_array.astype(int)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
