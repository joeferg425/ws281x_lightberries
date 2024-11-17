"""Generates an array where each repetition of the input. Sequence is reversed from the previous one."""

from __future__ import annotations

from typing import TYPE_CHECKING

from lightberries.array_sequence.base import ArraySequence
from lightberries.array_sequence.off import SequenceOff
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from lightberries.base.pixel import Pixel  # pragma: no cover


class SequenceReflect(ArraySequence):
    """Generates an array where each repetition of the input. Sequence is reversed from the previous one."""

    def __init__(  # noqa: C901, PLR0912
        self,
        led_count: int | None = None,
        pixel_sequence: PixelSequence | list[Pixel] | None = None,
        name: str | None = None,
        fold_length: int | None = None,
    ) -> None:
        """Generate an array where each repetition of the input. Sequence is reversed from the previous one.

        Args:
        ----
            name: the name of this pattern
            pixel_sequence: array of pixels
            led_count: the number of LEDs to involve in the rainbow
            pixel_sequence: an array of RGB tuples
            fold_length: the length of each segment wto be copied and reflected
            kwargs: args for patterns

        Returns:
        -------
            a list of Pixel objects in the pattern you requested

        """
        if name is None:
            name = SequenceReflect.__name__

        # if user didn't specify otherwise, fold in middle
        if pixel_sequence is None:
            pixel_sequence = PixelSequence.get_monthly_color_sequence()
            if fold_length is None and led_count is None:
                fold_length = pixel_sequence.led_count // 2
        elif isinstance(pixel_sequence, list):
            pixel_sequence = PixelSequence(pixel_sequence=pixel_sequence)

        if fold_length is None and led_count is not None:
            fold_length = led_count // 2
        if led_count is None:
            led_count = pixel_sequence.led_count
        if fold_length is None:
            fold_length = led_count // 2
        fold_length = int(fold_length)
        led_count = int(led_count)

        _pixel_array: list[Pixel] = []
        if pixel_sequence.led_count == 0 or led_count == 0:
            _pixel_array = []
        else:
            flip = False
            _pixel_array = list(SequenceOff(led_count=led_count))
            for seg_begin in range(0, led_count, fold_length):
                overflow = 0
                seg_end = 0
                if seg_begin + fold_length <= led_count and seg_begin + fold_length <= pixel_sequence.led_count:
                    seg_end = seg_begin + fold_length
                elif seg_begin + fold_length > led_count:
                    seg_end = seg_begin + fold_length
                    overflow = (seg_begin + fold_length) % led_count
                    seg_end = (seg_begin + fold_length) - overflow
                elif seg_begin + fold_length > pixel_sequence.led_count:
                    seg_end = seg_begin + pixel_sequence.led_count
                    overflow = (seg_begin + pixel_sequence.led_count) % pixel_sequence.led_count
                    seg_end = (seg_begin + pixel_sequence.led_count) - overflow
                if flip:
                    _pixel_array[seg_begin:seg_end] = pixel_sequence[fold_length - overflow - 1 :: -1]
                else:
                    _pixel_array[seg_begin:seg_end] = pixel_sequence[0 : fold_length - overflow]
                flip = not flip
        super().__init__(
            led_count=led_count,
            name=name,
            pixel_sequence=_pixel_array,
        )
