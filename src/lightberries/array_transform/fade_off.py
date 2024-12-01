"""Fade all Pixels toward OFF."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

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

    def create(
        self,
        color_sequence: PixelSequence | None = None,
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
        self.ACTIVE_TRANSFORMS.clear()
        if color_sequence is not None:
            self.state.color_sequence = color_sequence.copy()
        if state is not None:
            self.state = state
        else:
            self.state.set_fade_amount(fade_amount=random.uniform(0.01, 0.5))
            if fade_amount is not None:
                self.state.set_fade_amount(fade_amount=fade_amount)

        self.ACTIVE_TRANSFORMS.append(self)
        return self.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Fade all Pixels toward OFF."""
        self.controller.virtual_led_buffer[:] = self.controller.virtual_led_buffer * (1 - self.state.fade_amount_float)
