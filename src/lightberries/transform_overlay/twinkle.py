"""Do temporary twinkle modifications."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.state import TransformState
from lightberries.transform_overlay.base import OverlayTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform
    from lightberries.state import TransformState


class TransformTwinkle(OverlayTransform):
    """Do temporary twinkle modifications."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Do temporary twinkle modifications.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            kwargs: extra args to the state object

        """
        super().__init__(
            name=TransformTwinkle.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )

    def setup(
        self,
        color_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        twinkle_chance: float | None = None,
    ) -> list[PixelTransform]:
        """Randomly sets some lights to 'twinkleColor' temporarily.

        Args:
        ----
            color_sequence: the list of colors to be used when briefly flashing an LED
            state: initial state. Defaults to None.
            twinkle_chance: chance of a twinkle

        """
        self.ACTIVE_TRANSFORMS.clear()
        self.ACTIVE_TRANSFORMS.append(self)
        if color_sequence is not None:
            self.state.color_sequence = self.state.color_sequence.copy()
        if state is not None:
            self.state = state
        else:
            self.state.random = random.uniform(0.991, 0.995)

        if twinkle_chance is not None:
            self.state.random = twinkle_chance
        return self.ACTIVE_TRANSFORMS

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
                self.state.color_sequence.advance_index()
                self.controller.overlay_dictionary[index] = self.state.color_sequence.pixel.array
