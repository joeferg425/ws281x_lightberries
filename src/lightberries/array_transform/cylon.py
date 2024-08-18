"""Do cylon eye things."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_sequence.solid import SequenceSolid
from lightberries.array_transform.fade_off import TransformFadeOff
from lightberries.constants import MAX_INT8, SHAPE_2D
from lightberries.pixel import PixelColor
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformCylon(PixelTransform):
    """Do cylon eye things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do cylon eye things.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.

        """
        super().__init__(
            name=TransformCylon.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: int | None = None,
        delay_count: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            fade_amount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
            delay_count: number of delays

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.set_fade_amount(random.randint(5, 75) / MAX_INT8)
            self.state.delay_count_max = random.randint(1, 6)

            if color_sequence is not None:
                self.state.color_sequence = self.color_sequence
            if fade_amount is not None:
                self.state.set_fade_amount(fade_amount=fade_amount)
            if delay_count is None:
                self.state.delay_count_max = random.randint(1, 6)

        # fade the whole LED strand
        fade = TransformFadeOff(
            color_sequence=self.color_sequence,
            controller=self.controller,
        )
        # by this amount
        fade.setup(fade_amount=self.state.fade_amount)
        # shift eye by this much for each update
        self.state.size = self.color_sequence_count
        # adjust virtual LED buffer if necessary so that the cylon can actually move
        if self.controller.virtual_led_count < self.state.size:
            array = SequenceSolid(
                arrayLength=self.state.size + 3,
                color=PixelColor.OFF.array,
            )
            array[: self.controller.virtual_led_count] = self.controller.virtual_led_buffer
            self.controller.set_virtual_led_buffer(array)
        # set start and next indices
        self.state.index = self.controller.virtual_led_count - self.state.size - 3
        self.state.index_next = self.state.index
        # set delay
        self.state.delay_counter = delay_count
        self.state.delay_count_max = delay_count
        # add function to function list
        return [self]

    def transform(self) -> None:
        """Do alive function things."""
        # update delay counter
        self.state.delay_counter += 1
        # wait for several LED cycles to change LEDs
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # check direction
            if self.state.direction > 0:
                # calculate index array going from min to max
                self.state.index_next = self.state.index + (self.state.direction * self.state.step)
                self.state.index_min = self.state.index_next
                self.state.index_max = self.state.index_next + (self.state.size * self.state.direction)
                self.state.index_range = np.arange(
                    self.state.index_min,
                    self.state.index_max,
                    self.state.direction,
                )
            else:
                # calculate index array going from max to min
                self.state.index_next = self.state.index + (self.state.direction * self.state.step)
                self.state.index_min = self.state.index_next + (self.state.size * self.state.direction)
                self.state.index_max = self.state.index_next
                self.state.index_range = np.arange(
                    self.state.index_max,
                    self.state.index_min,
                    self.state.direction,
                )
            # check if color sequence would go off of far end of light string
            if self.state.index_max >= self.controller.virtual_led_count:
                # if the last LED is headed off the end
                if self.state.index_next >= self.controller.virtual_led_count:
                    # reverse direction
                    self.state.direction = -1
                    # fix next index
                    self.state.index_next = self.controller.virtual_led_count - 2
                # find where LEDs go off the end
                over = np.where(
                    self.state.index_range >= (self.controller.virtual_led_count),
                )[0]
                # reverse their direction
                self.state.index_range[over] = np.arange(
                    -1,
                    (len(over) + 1) * -1,
                    -1,
                ) + (self.controller.virtual_led_count - 1)
            # if LEDs go off the other end
            elif self.state.index_min < 0:
                # if the last LED is headed off the end
                if self.state.index_next < 0:
                    # reverse direction
                    self.state.direction *= -1
                    # fix next index
                    self.state.index_next = 1
                # find where LEDs go off the end
                over = np.where(self.state.index_range < 0)[0]
                # reverse their direction
                self.state.index_range[over] = np.arange(1, (len(over) + 1), 1)
        # update index
        self.state.index = self.state.index_next
        if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
            self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
        else:
            self.controller.virtual_led_buffer[
                np.where(
                    self.controller.virtual_led_index_buffer == self.state.index_range,
                )
            ] = self.state.color
