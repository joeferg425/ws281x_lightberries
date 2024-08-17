"""Function in which colorful lights accelerate across the string of lights repeatedly."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.fade_off import TransformFadeOff
from lightberries.constants import MAX_INT8, SHAPE_2D
from lightberries.state import TransformState
from lightberries.transform import Transform

LOGGER = logging.getLogger("lightBerries")

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState


class TransformAccelerate(Transform):
    """Function in which colorful lights accelerate across the string of lights repeatedly."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Accelerate across the string of lights repeatedly.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.

        """
        super().__init__(
            name=TransformAccelerate.__name__,
            controller=controller,
            state=state,
        )

    def setup(  # noqa: PLR0913
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        delay_count_max: int | None = None,
        step_count_max: int | None = None,
        fade_amount: float | None = None,
        color_cycle: bool | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[Transform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: _description_. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object
            delay_count_max: maximum number of iterations to delay for
            step_count_max: maximum number of steps to run for
            fade_amount: amount of fade
            color_cycle: set true to cycle through colors in sequence

        Returns:
        -------
            list of transforms

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            # set the number of updates during which the lights will stay constant
            self.state.delay_count_max = random.randint(5, 10)
            # this determines the maximum that the LED can jump in a single step as it speeds up
            self.state.step_count_max = random.randint(4, 10)
            # this determines the length of comet tails
            self.state.set_fade_amount(random.randint(15, 35) / MAX_INT8)
            # whether to cycle through colors
            self.state.color_cycle = self.get_random_boolean()
            # the number of times the comet will accelerate
            self.state.state_max = random.randint(5, 10)
            # randomize direction
            self.state.direction = self.get_random_direction()
            # randomize start index
            self.state.index = self.get_random_index()

        if delay_count_max is not None:
            self.state.delay_count_max = delay_count_max
        if step_count_max is not None:
            self.state.step_count_max = step_count_max
        if fade_amount is not None:
            self.state.set_fade_amount(fade_amount)
        # make sure fade amount is valid

        if color_cycle is not None:
            self.state.color_cycle = color_cycle

        fade = TransformFadeOff(
            controller=self.controller,
            state=self.state,
        )
        fade.setup(fade_amount=self.state.fade_amount)
        return [fade, self]

    def transform(self) -> None:
        """Accelerate across the string of lights repeatedly."""
        self.state.index_previous = self.state.index
        splash = False
        # increment delay counter
        self.state.delay_counter += 1
        # check delay counter, update index when it hits max
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # update step counter
            self.state.step_counter += 1
            # calculate next index
            self.state.index_next = int(
                self.state.index + (self.state.direction * self.state.step),
            )
            self.state.index = self.state.index_next % self.controller.virtual_led_count
            self.state.index_range = np.arange(
                self.state.index_previous + self.state.direction,
                self.state.index_next + self.state.direction,
                self.state.direction,
            )
            modulo = np.where(
                self.state.index_range >= (self.controller.real_led_count),
            )
            self.state.index_range[modulo] -= self.controller.real_led_count
            if self.state.color_cycle is True:
                self.state.color = self.color_sequence_next
        # check index step counter, update speed state when it hits step count max
        if self.state.step_counter >= self.state.step_count_max:
            # reset step counter
            self.state.step_counter = 0
            # reduce delay max
            self.state.delay_count_max -= 1
            # increment step size every two delay reductions
            if (self.state.state % 2) == 0:
                self.state.step += 1
            # set step counter to a random number of steps based on LED count
            self.state.step_count_max = random.randint(
                int(self.controller.real_led_count / 20),
                int(self.controller.real_led_count / 4),
            )
            # update state counter
            self.state.state += 1
        # check state counter, reset speed state when it hits max speed
        if self.state.state > self.state.state_max:
            # "splash" color when we hit the end
            splash = True
            #  create the "splash" index array before updating direction etc.
            splash_range = np.array(
                list(
                    range(
                        self.state.index_previous,
                        self.state.index_next + (self.state.step * self.state.direction * 4),
                        self.state.direction,
                    ),
                ),
                dtype=np.int32,
            )
            # make sure that the splash doesn't go off the edge of the virtual led array
            modulo = np.where(splash_range >= (self.controller.real_led_count))
            splash_range[modulo] %= self.controller.real_led_count
            modulo = np.where(splash_range < 0)
            splash_range[modulo] += self.controller.real_led_count
            # reset delay
            self.state.delay_counter = 0
            # set new delay max
            self.state.delay_count_max = random.randint(5, 10)
            # reset state max
            self.state.state_max = self.state.delay_count_max
            # randomize direction
            self.state.direction = self.controller.get_random_direction()
            # reset state
            self.state.state = 0
            # reset step
            self.state.step = 1
            # reset step counter
            self.state.step_counter = 0
            # randomize starting index
            self.state.index = self.controller.get_random_index()
            self.state.index_previous = self.state.index
            self.state.index_range = np.arange(
                self.state.index_previous,
                self.state.index + 1,
            )
        if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
            self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
        else:
            self.controller.virtual_led_buffer[
                np.where(
                    self.controller.virtual_led_index_buffer == self.state.index_range,
                )
            ] = self.state.color
        if splash is True:
            self.controller.virtual_led_buffer[splash_range, :] = self.controller.fade_color(
                self.state.color,
                self.controller.background_color,
                50,
            )
