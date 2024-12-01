"""Fade all Pixels toward OFF."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lightberries.overlay.overlay_transform import OverlayTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform


class TransformFadeOff(OverlayTransform):
    """Fade all Pixels toward OFF."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
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
        )

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            fade_amount: amount to fade on each iteration

        Returns:
        -------
            list of transforms

        """
        transform = TransformFadeOff(controller=controller)
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence.copy()
        if state is not None:
            transform.state = state
        else:
            transform.state.set_fade_amount(fade_amount=random.uniform(0.01, 0.5))
            if fade_amount is not None:
                transform.state.set_fade_amount(fade_amount=fade_amount)
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence

        TransformFadeOff.ACTIVE_TRANSFORMS.append(transform)
        return TransformFadeOff.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Fade all Pixels toward OFF."""
        self.controller.virtual_led_buffer[:] = self.controller.virtual_led_buffer * (1 - self.state.fade_amount_float)
