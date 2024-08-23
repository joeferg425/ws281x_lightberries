"""Cycle the entire light string's color at once."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformSolidColorCycle(PixelTransform):
    """Cycle the entire light string's color at once."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Cycle the entire light string's color at once.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformSolidColorCycle.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        delay_count: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            delay_count: number of delays

        Returns:
        -------
            list of transforms

        """
        if color_sequence is not None:
            self.state.color_sequence = color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.delay_count_max = random.randint(50, 100)
            self.state.delay_counter = self.state.delay_count_max

        if delay_count is not None:
            self.state.delay_count_max = delay_count
            self.state.delay_counter = self.state.delay_count_max
        return [self]

    def transform(self) -> None:
        """Set all pixels to the next color.

        Args:
        ----
            cycle: tracking object

        """
        # wait for delay count before changing LEDs
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # remove any current color
            self.controller.virtual_led_buffer *= 0
            # add new color
            self.controller.virtual_led_buffer += self.state.color_sequence.pixel_next.array
            self.state.color_sequence.advance_index()
        # increment delay counter
        self.state.delay_counter += 1
        self.state.delay_counter += 1
        self.state.delay_counter += 1
        self.state.delay_counter += 1
