"""Do cylon eye things."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lightberries.array_sequence.solid import SequenceSolid
from lightberries.base.constants import MAX_INT8
from lightberries.base.pixel import Pixel, PixelColor, pixel_from_color
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence


class TransformCylon(PixelTransform):
    """Do cylon eye things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do cylon eye things.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformCylon.__name__,
            controller=controller,
        )

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: int | None = None,
        delay_count: int | None = None,
    ) -> list[PixelTransform]:
        """Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            fade_amount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
            delay_count: number of delays

        """
        transform = TransformCylon(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.set_fade_amount(random.randint(5, 75) / MAX_INT8)
            transform.state.delay_count_max = random.randint(2, 30)

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        if fade_amount is not None:
            transform.state.set_fade_amount(fade_amount=fade_amount)
        if delay_count is not None:
            transform.state.delay_count_max = delay_count

        # fade the whole LED strand
        TransformFadeOff.create(
            controller=controller,
            fade_amount=transform.state.fade_amount,
        )

        # shift eye by this much for each update
        transform.state.size = transform.state.pixel_sequence.led_count
        # adjust virtual LED buffer if necessary so that the cylon can actually move
        if transform.controller.virtual_led_count <= transform.state.pixel_sequence.led_count:
            array = SequenceSolid(
                led_count=transform.state.pixel_sequence.led_count,
                color=pixel_from_color(PixelColor.OFF),
            )
            array[: transform.state.pixel_sequence.led_count] = [Pixel(x) for x in transform.state.pixel_sequence]
            transform.controller.set_virtual_led_buffer(array)
        if transform.controller.virtual_led_count <= controller.real_led_count:
            array = SequenceSolid(
                led_count=controller.real_led_count,
                color=pixel_from_color(PixelColor.OFF),
            )
            array[: transform.state.pixel_sequence.led_count] = [Pixel(x) for x in transform.state.pixel_sequence]
            transform.controller.set_virtual_led_buffer(array)
        # set start and next indices
        transform.state.index_bounce = True
        transform.state.index_previous = 0
        transform.state.index = 1
        transform.state.direction = 1
        transform.state.direction_previous = 1
        transform.state.delay_count_max = 1
        transform.advance_index()

        TransformCylon.ACTIVE_TRANSFORMS.append(transform)
        return TransformCylon.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do alive function things."""
        super().transform()
        if self.state.delay_count_reset:
            self.advance_index()
        self.assign_pixel()
