"""Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.base import ArrayTransform
from lightberries.array_transforms.off import TransformOff
from lightberries.light_sequences.solid import SolidSequence
from lightberries.pixel import PixelColors

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState
    from lightberries.transform import LightTransform

LOGGER = logging.getLogger("lightBerries")


class ArrayFunctionMarquee(ArrayTransform):
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
            kwargs: extra args to the state object
            shift_amount: the number of pixels the marquee shifts on each update
            delay_count: number of refreshes to delay for each cycle
            initial_direction: a positive or negative value for marquee start direction
            kwargs: extra args to the state object

        """
        super().__init__(
            name=ArrayFunctionMarquee.__name__,
            controller=controller,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        shift_amount: int | None = None,
        delay_count: int | None = None,
        initial_direction: int | None = None,
    ) -> list[LightTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
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
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state

        shift_amount: int = random.randint(1, 2)
        delay_count: int = random.randint(0, 6)
        initial_direction: int = self.get_random_direction()
        if shift_amount is not None:
            shift_amount = int(shift_amount)
        if delay_count is not None:
            delay_count = int(delay_count)
        if initial_direction is not None:
            initial_direction = 1 if (initial_direction >= 1) else -1
        # store the size of the color sequence being shifted back and forth
        self.state.size = self.color_sequence_count
        # assign starting direction
        self.state.direction = initial_direction
        # this is how much the LEDs will move by each time
        self.state.step = shift_amount
        # this is how many LED updates will be ignored before doing another LED shift
        self.state.delay_count_max = delay_count
        # this function just shifts the existing virtual LED buffer,
        # so make sure the virtual LED buffer is initialized here
        if self.color_sequence_count >= self.controller.virtual_led_count - 10:
            array = SolidSequence(
                arrayLength=self.color_sequence_count + 10,
                color=PixelColors.OFF.array,
            )
            array[: self.color_sequence_count] = self.color_sequence
            self.controller.set_virtual_led_buffer(array)
        else:
            self.controller.set_virtual_led_buffer(self.color_sequence)
        # turn off all LEDs every time so we can turn on new ones
        transform_off = TransformOff(controller=self.controller)
        transform_off.setup(
            color_sequence=self.color_sequence,
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
        self.controller.virtual_led_buffer[np.sort(self.state.index_range)] = self.color_sequence
