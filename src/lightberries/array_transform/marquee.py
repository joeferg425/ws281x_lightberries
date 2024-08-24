"""Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_sequence.solid import SequenceSolid
from lightberries.pixel import Pixel, PixelColor
from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay.fade_off import TransformFadeOff

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformMarquee(PixelTransform):
    """Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Move the LEDs in the color sequence from one end of the LED string to the other continuously.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformMarquee.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        shift_amount: int | None = None,
        delay_count: int | None = None,
        initial_direction: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
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
        if pixel_sequence is not None:
            self.state.color_sequence = pixel_sequence
        if state is not None:
            self.state = state
        else:
            self.state.step = random.randint(1, 2)
            self.state.delay_count_max = random.randint(0, 6)
            self.state.direction = self.get_random_direction()
        if shift_amount is not None:
            self.state.step = shift_amount
        if delay_count is not None:
            self.state.delay_count_max = delay_count
        if initial_direction is not None:
            self.state.direction = 1 if (initial_direction >= 1) else -1
        # store the size of the color sequence being shifted back and forth
        self.state.size = self.state.color_sequence.led_count
        # this function just shifts the existing virtual LED buffer,
        # so make sure the virtual LED buffer is initialized here
        if self.state.color_sequence.led_count >= self.controller.virtual_led_count - 10:
            array = SequenceSolid(
                led_count=self.state.color_sequence.led_count + 10,
                color=Pixel(PixelColor.OFF),
            )
            array[: self.state.color_sequence.led_count] = list(self.state.color_sequence)
            self.controller.set_virtual_led_buffer(array)
        else:
            self.controller.set_virtual_led_buffer(self.state.color_sequence)
        # turn off all LEDs every time so we can turn on new ones
        transform_off = TransformFadeOff(controller=self.controller)
        transform_off.setup(
            pixel_sequence=self.state.color_sequence,
            state=self.state,
        )
        return [transform_off, self]

    def transform(self) -> None:
        """Do nothing."""
        # increment delay counter
        self.state.delay_counter += 1
        # wait for several LED cycles to change LEDs
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # calculate possible next index
            self.state.index_next = self.state.index + (self.state.step * self.state.direction)
            # calculate max index we will update
            self.state.index_max = self.state.index_next + self.state.size
            # if we are going to overshoot
            if self.state.index_max >= self.controller.virtual_led_count:
                # switch direction
                self.state.direction *= -1
                # set index to either the next step or the max possible
                # (accounts for step sizes > 1)
                self.state.index = max(
                    self.state.index + (self.state.step * self.state.direction),
                    self.controller.virtual_led_count - self.state.size,
                )
            # if we will undershoot
            elif self.state.index_max < self.state.size:
                # TODO: should make a wrap-around version
                # switch direction
                self.state.direction *= -1
                # set index to either the next step or zero
                # (accounts for step sizes > 1)
                self.state.index = max(
                    self.state.index + (self.state.step * self.state.direction),
                    0,
                )
            else:
                # next index is valid, use it
                self.state.index = self.state.index_next
        # calculate color sequence range
        self.state.index_range = np.arange(
            self.state.index,
            self.state.index + self.state.size,
        )
        # update LEDs with new values
        self.controller.virtual_led_buffer[np.sort(self.state.index_range)] = self.state.color_sequence
