"""Do temporary twinkle modifications."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lightberries.base.state import TransformState
from lightberries.transform_overlay._overlay_transform import OverlayTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform


class TransformTwinkle(OverlayTransform):
    """Do temporary twinkle modifications."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do temporary twinkle modifications.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a pixel sequence
            kwargs: extra args to the state object

        """
        super().__init__(
            name=TransformTwinkle.__name__,
            controller=controller,
        )

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        twinkle_chance: float | None = None,
    ) -> list[PixelTransform]:
        """Randomly sets some lights to 'twinkleColor' temporarily.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: the list of colors to be used when briefly flashing an LED
            state: initial state. Defaults to None.
            twinkle_chance: chance of a twinkle

        """
        transform = TransformTwinkle(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.random = random.uniform(0.991, 0.995)
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence.copy()

        if twinkle_chance is not None:
            transform.state.random = twinkle_chance
        TransformTwinkle.ACTIVE_TRANSFORMS.append(transform)
        return TransformTwinkle.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do temporary twinkle modifications.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        for index in range(self.controller.real_led_count):
            if random.random() > self.state.random:
                self.state.pixel_sequence.advance_index()
                self.controller.overlay_dictionary[index] = self.state.pixel_sequence.pixel.array
