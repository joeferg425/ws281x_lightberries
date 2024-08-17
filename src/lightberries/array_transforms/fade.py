"""Fade all Pixels."""

from __future__ import annotations

import logging
from math import ceil
from typing import TYPE_CHECKING, Any

from lightberries.constants import MAX_INT8
from lightberries.transform import Transform

if TYPE_CHECKING:
    import numpy as np

    import lightberries.array_controller
    from lightberries.state import TransformState
    from lightberries.transform import Transform

LOGGER = logging.getLogger("lightBerries")


class TransformFade(Transform):
    """Fade all Pixels."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Fade all Pixels.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.

        """
        super().__init__(
            name="Fade",
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[Transform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            fade_amount: amount to fade on each iteration

        Returns:
        -------
            list of transforms

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.set_fade_amount(fade_amount=fade_amount)

    def transform(self) -> None:
        """Fade all Pixels."""
        self.state.delay_counter += 1
        if self.state.delay_counter >= self.state.delay_count_max:
            fade_amount = ceil(self.state.fade_amount * MAX_INT8)
            if fade_amount < 0:
                fade_amount = 1
            elif fade_amount > MAX_INT8:
                fade_amount = MAX_INT8
            for i in range(self.controller.real_led_count):
                for rgb_index in range(len(self.state.color)):
                    if self.controller.virtual_led_buffer[i, rgb_index] != self.state.color[rgb_index]:
                        if self.controller.virtual_led_buffer[i, rgb_index] - fade_amount > self.state.color[rgb_index]:
                            self.controller.virtual_led_buffer[i, rgb_index] -= fade_amount
                        elif (
                            self.controller.virtual_led_buffer[i, rgb_index] + fade_amount < self.state.color[rgb_index]
                        ):
                            self.controller.virtual_led_buffer[i, rgb_index] += fade_amount
                        else:
                            self.controller.virtual_led_buffer[i, rgb_index] = self.state.color[rgb_index]
                            self.controller.virtual_led_buffer[i, rgb_index] = self.state.color[rgb_index]
