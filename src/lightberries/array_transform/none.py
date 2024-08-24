"""Basic function. It does nothing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformNone(PixelTransform):
    """Basic function. It does nothing."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do nothing.

        Args:
        ----
            controller: array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformNone.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        # create an object to put in the light data list so we don't just abort the run
        super().setup(
            pixel_sequence=pixel_sequence,
            state=state,
        )
        if pixel_sequence is not None:
            self.state.color_sequence = pixel_sequence
        if state is not None:
            self.state = state
        self.ran_once = False
        self.ACTIVE_TRANSFORMS.append(self)
        return self.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do nothing."""
        if not self.ran_once:
            self.ran_once = True
            if self.state.color_sequence.led_count <= self.controller.virtual_led_count:
                self.controller.virtual_led_buffer[: self.state.color_sequence.led_count] = self.state.color_sequence
            else:
                self.controller.virtual_led_buffer[: self.controller.virtual_led_count] = self.state.color_sequence
