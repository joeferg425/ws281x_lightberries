"""Turn all Pixels OFF."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay._overlay_transform import OverlayTransform

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformOff(OverlayTransform):
    """Turn all Pixels OFF."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Turn all Pixels OFF.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformOff.__name__,
            controller=controller,
        )

    @staticmethod
    def setup(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        transform = TransformOff(controller=controller)
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence.copy()
        if state is not None:
            transform.state = state
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence

        TransformOff.ACTIVE_TRANSFORMS.append(transform)
        return TransformOff.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Turn all Pixels OFF."""
        self.controller.virtual_led_buffer[:] *= 0
