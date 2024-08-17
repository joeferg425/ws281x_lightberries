"""Fade all Pixels toward OFF."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import numpy as np

    import lightberries.array_controller
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformFadeOff(PixelTransform):
    """Fade all Pixels toward OFF."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Fade all Pixels toward OFF.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.

        """
        super().__init__(
            name=TransformFadeOff.__name__,
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
    ) -> list[PixelTransform]:
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
        """Fade all Pixels toward OFF."""
        self.controller.virtual_led_buffer[:] = self.controller.virtual_led_buffer * (1 - self.state.fade_amount)
        self.controller.virtual_led_buffer[:] = self.controller.virtual_led_buffer * (1 - self.state.fade_amount)
