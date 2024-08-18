"""Randomly set all lights in the string to the same color without changing the virtual LED buffer."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.state import TransformState
from lightberries.transform_overlay.base import OverlayTransform

if TYPE_CHECKING:

    import numpy as np
    from numpy.typing import NDArray

    import lightberries.array_controller
    from lightberries.pixel_transform import PixelTransform
    from lightberries.state import TransformState


class TransformBlink(OverlayTransform):
    """Randomly set all lights in the string to the same color without changing the virtual LED buffer."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Randomly set all lights in the string to the same color without changing the virtual LED buffer.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            kwargs: extra args to the state object

        """
        super().__init__(
            name=TransformBlink.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )

    def setup(
        self,
        color_sequence: NDArray[np.int32] | None = None,
        state: TransformState | None = None,
        blink_chance: float | None = None,
    ) -> list[PixelTransform]:
        """Use the overlay that causes all LEDs to light up the same color at once.

        Args:
        ----
            color_sequence: the list of colors to be used when briefly flashing an LED
            state: initial state. Defaults to None.
            blink_chance: chance of a blink

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence.copy()
        if state is not None:
            self.state = state
        else:
            self.state.random = random.uniform(0.991, 0.995)

        if blink_chance is not None:
            self.state.random = blink_chance

        return [self]

    def transform(self) -> None:
        """Randomly set all lights in the string to the same color without changing the virtual LED buffer.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        if random.random() > self.state.random:
            color = self.color_sequence_next
            for index in range(self.controller.real_led_count):
                self.controller.overlay_dictionary[index] = color
                self.controller.overlay_dictionary[index] = color
