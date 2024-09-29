"""Fade all Pixels."""

from __future__ import annotations

import random
from math import ceil
from typing import TYPE_CHECKING

from lightberries.constants import MAX_INT8
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState



class TransformFade(PixelTransform):
    """Fade all Pixels."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Fade all Pixels.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name="Fade",
            controller=controller,
        )

    @staticmethod
    def setup(
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
        transform = TransformFade(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.set_fade_amount(fade_amount=random.uniform(0.01, 0.5))

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        if fade_amount is not None:
            transform.state.set_fade_amount(fade_amount=fade_amount)

        TransformFade.ACTIVE_TRANSFORMS.append(transform)
        return TransformFade.ACTIVE_TRANSFORMS

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
                for rgb_index in range(len(self.state.pixel_sequence.pixel)):
                    if self.controller.virtual_led_buffer[i, rgb_index] != self.state.pixel_sequence.pixel[rgb_index]:
                        if (
                            self.controller.virtual_led_buffer[i, rgb_index] - fade_amount
                            > self.state.pixel_sequence.pixel[rgb_index]
                        ):
                            self.controller.virtual_led_buffer[i, rgb_index] -= fade_amount
                        elif (
                            self.controller.virtual_led_buffer[i, rgb_index] + fade_amount
                            < self.state.pixel_sequence.pixel[rgb_index]
                        ):
                            self.controller.virtual_led_buffer[i, rgb_index] += fade_amount
                        else:
                            self.controller.virtual_led_buffer[i, rgb_index] = self.state.pixel_sequence.pixel[
                                rgb_index
                            ]
