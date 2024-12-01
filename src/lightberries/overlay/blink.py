"""Randomly set all lights in the string to the same color without changing the virtual LED buffer."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lightberries.base.state import TransformState
from lightberries.overlay.overlay_transform import OverlayTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform


class OverlayBlink(OverlayTransform):
    """Randomly set all lights in the string to the same color without changing the virtual LED buffer."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Randomly set all lights in the string to the same color without changing the virtual LED buffer.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels
            kwargs: extra args to the state object

        """
        super().__init__(
            name=OverlayBlink.__name__,
            controller=controller,
        )

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        blink_chance: float | None = None,
    ) -> list[PixelTransform]:
        """Use the overlay that causes all LEDs to light up the same color at once.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: the list of colors to be used when briefly flashing an LED
            state: initial state. Defaults to None.
            blink_chance: chance of a blink

        """
        transform = OverlayBlink(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.random = random.uniform(0.991, 0.995)
        if pixel_sequence is not None:
            transform.state.pixel_sequence = transform.state.pixel_sequence.copy()

        if blink_chance is not None:
            transform.state.random = blink_chance

        OverlayBlink.ACTIVE_TRANSFORMS.append(transform)
        return OverlayBlink.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Randomly set all lights in the string to the same color without changing the virtual LED buffer.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        if random.random() > self.state.random:
            self.state.pixel_sequence.advance_index()
            for index in range(self.controller.real_led_count):
                self.controller.overlay_dictionary[index] = self.state.pixel_sequence.pixel.array
