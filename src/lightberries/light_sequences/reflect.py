"""Generates an array where each repetition of the input. Sequence is reversed from the previous one."""

from __future__ import annotations

from typing import Any

import numpy as np

from lightberries.array_patterns.base import ArrayPattern
from lightberries.array_patterns.off import ArrayPatternOff
from lightberries.exceptions import LightBerryError, PatternError


class ReflectArray(ArrayPattern):
    """Generates an array where each repetition of the input. Sequence is reversed from the previous one."""

    def __init__(self, led_count: int, name: str | None = None, **kwargs: dict[str, Any]) -> None:
        """Generate an array where each repetition of the input. Sequence is reversed from the previous one.

        Args:
        ----
            name: the name of this pattern
            led_count: the number of LEDs to involve in the rainbow
            color_sequence: an array of RGB tuples
            fold_length: the length of each segment wto be copied and reflected
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
            name = ReflectArray.__name__
        super().__init__(led_count=led_count, name=name, kwargs=kwargs)
        # if user didn't specify otherwise, fold in middle
        try:
            input_sequence = ArrayPattern.DEFAULT_COLOR_SEQUENCE
            if "color_sequence" in kwargs:
                input_sequence = kwargs["color_sequence"].copy()
            color_sequence_length = input_sequence.shape[0]
            fold_length = led_count // 2
            if "fold_length" in kwargs:
                fold_length = kwargs["fold_length"]
            if color_sequence_length == 0 or led_count == 0:
                self.sequence = np.zeros((0, 3))
            else:
                if fold_length > color_sequence_length:
                    temp = ArrayPatternOff(fold_length).sequence
                    temp[fold_length - color_sequence_length :] = input_sequence
                    input_sequence = temp
                    color_sequence_length = len(input_sequence)
                flip = False
                temp_array = ArrayPatternOff(led_count).sequence
                for seg_begin in range(0, led_count, fold_length):
                    overflow = 0
                    seg_end = 0
                    if seg_begin + fold_length <= led_count and seg_begin + fold_length <= color_sequence_length:
                        seg_end = seg_begin + fold_length
                    elif seg_begin + fold_length > led_count:
                        seg_end = seg_begin + fold_length
                        overflow = (seg_begin + fold_length) % led_count
                        seg_end = (seg_begin + fold_length) - overflow
                    elif seg_begin + fold_length > color_sequence_length:
                        seg_end = seg_begin + color_sequence_length
                        overflow = (seg_begin + color_sequence_length) % color_sequence_length
                        seg_end = (seg_begin + color_sequence_length) - overflow
                    if flip:
                        temp_array[seg_begin:seg_end] = input_sequence[fold_length - overflow - 1 :: -1]
                    else:
                        temp_array[seg_begin:seg_end] = input_sequence[0 : fold_length - overflow]
                    flip = not flip
                self._sequence = temp_array
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise PatternError from ex
