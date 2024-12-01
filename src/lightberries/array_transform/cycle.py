"""Cycle the entire light string's color at once."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence


class TransformCycle(PixelTransform):
    """Cycle the entire light string's color at once."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Cycle the entire light string's color at once.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformCycle.__name__,
            controller=controller,
        )

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        delay_count: int | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            delay_count: number of delays

        Returns:
        -------
            list of transforms

        """
        transform = TransformCycle(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.delay_count_max = random.randint(50, 100)
            transform.state.delay_counter = transform.state.delay_count_max

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence

        if delay_count is not None:
            transform.state.delay_count_max = delay_count
            transform.state.delay_counter = transform.state.delay_count_max
        TransformCycle.ACTIVE_TRANSFORMS.append(transform)
        return TransformCycle.ACTIVE_TRANSFORMS

    def next_step(self) -> None:
        """Set all pixels to the next color.

        Args:
        ----
            cycle: tracking object

        """
        # wait for delay count before changing LEDs
        if self.state.delay_count_reset:
            # remove any current color
            self.controller.virtual_led_buffer *= 0
            # add new color
            self.controller.virtual_led_buffer += self.state.pixel_sequence.pixel_next.array
            self.state.pixel_sequence.advance_index()
