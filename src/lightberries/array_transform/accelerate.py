"""Function in which colorful lights accelerate across the string of lights repeatedly."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from lightberries.array_transform.base import ArrayTransform
from lightberries.base.constants import MAX_INT8, SHAPE_2D
from lightberries.state import TransformState
from lightberries.transform_overlay.fade_off import TransformFadeOff

if TYPE_CHECKING:

    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform
    from lightberries.state import TransformState


class TransformAccelerate(ArrayTransform):
    """Function in which colorful lights accelerate across the string of lights repeatedly."""

    INSTANCES: ClassVar[dict[int, TransformAccelerate]] = {}

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Accelerate across the string of lights repeatedly.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformAccelerate.__name__,
            controller=controller,
        )
        self.INSTANCES[len(self.INSTANCES)] = self

    @staticmethod
    def setup(  # noqa: PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        delay_count_max: int | None = None,
        step_count_max: int | None = None,
        fade_amount: float | None = None,
        color_cycle: bool | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: _description_. Defaults to None.
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
        transform = TransformAccelerate(controller=controller)
        if state is not None:
            transform.state = state
        else:
            # set the number of updates during which the lights will stay constant
            transform.state.delay_count_max = random.randint(5, 10)
            # this determines the maximum that the LED can jump in a single step as it speeds up
            transform.state.step_count_max = random.randint(4, 10)
            # this determines the length of comet tails
            transform.state.set_fade_amount(random.randint(15, 35) / MAX_INT8)
            # whether to cycle through colors
            transform.state.color_cycle = transform.get_random_boolean()
            # the number of times the comet will accelerate
            transform.state.state_max = random.randint(5, 10)
            # randomize direction
            transform.state.direction = transform.get_random_direction()
            # randomize start index
            transform.state.index = transform.get_random_index()

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence

        if delay_count_max is not None:
            transform.state.delay_count_max = delay_count_max
        if step_count_max is not None:
            transform.state.step_count_max = step_count_max
        if fade_amount is not None:
            transform.state.set_fade_amount(fade_amount)
        # make sure fade amount is valid

        if color_cycle is not None:
            transform.state.color_cycle = color_cycle

        TransformFadeOff.setup(
            controller=controller,
            state=transform.state,
            fade_amount=transform.state.fade_amount,
        )
        TransformAccelerate.ACTIVE_TRANSFORMS.append(transform)
        return TransformAccelerate.ACTIVE_TRANSFORMS

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
                self.state.pixel_sequence.advance_index()
        # check index step counter, update speed state when it hits step count max
        if self.state.step_counter >= self.state.step_count_max:
            # reset step counter
            self.state.step_counter = 0
            # reduce delay max
            self.state.delay_count_max -= 1
            # increment step size every two delay reductions
            if (self.state.current_state % 2) == 0:
                self.state.step += 1
            # set step counter to a random number of steps based on LED count
            self.state.step_count_max = random.randint(
                int(self.controller.real_led_count / 20),
                int(self.controller.real_led_count / 4),
            )
            # update state counter
            self.state.current_state += 1
        # check state counter, reset speed state when it hits max speed
        splash_range = np.zeros([], dtype=np.int32)
        if self.state.current_state > self.state.state_max:
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
            self.state.direction = self.get_random_direction()
            # reset state
            self.state.current_state = 0
            # reset step
            self.state.step = 1
            # reset step counter
            self.state.step_counter = 0
            # randomize starting index
            self.state.index = self.get_random_index()
            self.state.index_previous = self.state.index
            self.state.index_range = np.arange(
                self.state.index_previous,
                self.state.index + 1,
            )
        if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
            self.controller.virtual_led_buffer[self.state.index_range] = self.state.pixel_sequence.pixel
        else:
            self.controller.virtual_led_buffer[
                np.where(
                    self.controller.virtual_led_index_buffer == self.state.index_range,
                )
            ] = self.state.pixel_sequence.pixel
        if splash is True:
            self.controller.virtual_led_buffer[splash_range, :] = self.state.fade_color()
