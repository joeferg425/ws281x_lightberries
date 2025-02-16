"""Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from lightberries.array_sequence.solid import SequenceSolid
from lightberries.base.pixel import Pixel, PixelColor
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence


class TransformMarquee(PixelTransform):
    """Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Move the LEDs in the color sequence from one end of the LED string to the other continuously.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformMarquee.__name__,
            controller=controller,
        )

    @staticmethod
    def create(  # noqa: D417, PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
        shift_amount: int | None = None,
        delay_count: int | None = None,
        initial_direction: int | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            shift_amount: the number of pixels the marquee shifts on each update
            delay_count: number of refreshes to delay for each cycle
            initial_direction: a positive or negative value for marquee start direction
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        transform = TransformMarquee(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.step_size = random.randint(1, 2)
            transform.state.delay_count_max = random.randint(0, 6)
            transform.state.direction = transform.get_random_direction()

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        if shift_amount is not None:
            transform.state.step_size = shift_amount
        if delay_count is not None:
            transform.state.delay_count_max = delay_count
        if initial_direction is not None:
            transform.state.direction = 1 if (initial_direction >= 1) else -1
        if fade_amount is None:
            transform.state.set_fade_amount(random.uniform(0.01, 0.1))
        # store the size of the color sequence being shifted back and forth
        transform.state.size = transform.state.pixel_sequence.led_count
        # this function just shifts the existing virtual LED buffer,
        # so make sure the virtual LED buffer is initialized here
        if transform.controller.real_led_count <= transform.controller.virtual_led_count + 10:
            array = SequenceSolid(
                led_count=transform.controller.real_led_count + 10,
                color=Pixel(PixelColor.OFF),
            )
        else:
            array = SequenceSolid(
                led_count=transform.controller.real_led_count + 10,
                color=Pixel(PixelColor.OFF),
            )
        array[: transform.state.pixel_sequence.led_count] = [Pixel(x) for x in transform.state.pixel_sequence]
        transform.controller.set_virtual_led_buffer(array)
        transform.state.index = 1
        transform.state.index_bounce = True
        transform.advance_index()
        # turn off all LEDs every time so we can turn on new ones
        TransformFadeOff.create(
            controller=controller,
            fade_amount=transform.state.fade_amount,
        )
        transform.ACTIVE_TRANSFORMS.append(transform)
        return transform.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do nothing."""
        super().transform()
        # wait for several LED cycles to change LEDs
        if self.state.delay_count_reset:
            self.advance_index()
            # calculate possible next index
        #     self.state.index_next = self.state.index + (self.state.step_size * self.state.direction)
        #     # calculate max index we will update
        #     self.state.index_max = self.state.index_next + self.state.size
        #     # if we are going to overshoot
        #     if self.state.index_max >= self.controller.virtual_led_count:
        #         # switch direction
        #         self.state.direction *= -1
        #         # set index to either the next step or the max possible
        #         # (accounts for step sizes > 1)
        #         self.state.index = max(
        #             self.state.index + (self.state.step_size * self.state.direction),
        #             self.controller.virtual_led_count - self.state.size,
        #         )
        #     # if we will undershoot
        #     elif self.state.index_max < self.state.size:
        #         # TODO: should make a wrap-around version
        #         # switch direction
        #         self.state.direction *= -1
        #         # set index to either the next step or zero
        #         # (accounts for step sizes > 1)
        #         self.state.index = max(
        #             self.state.index + (self.state.step_size * self.state.direction),
        #             0,
        #         )
        #     else:
        #         # next index is valid, use it
        #         self.state.index = self.state.index_next
        # # calculate color sequence range
        # self.state.index_range = np.arange(
        #     self.state.index,
        #     self.state.index + self.state.size,
        # )
        # # update LEDs with new values
        # self.controller.virtual_led_buffer[np.sort(self.state.index_range)] = self.state.pixel_sequence
        self.assign_pixel_sequence()
