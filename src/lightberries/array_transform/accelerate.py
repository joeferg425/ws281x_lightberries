"""Function in which colorful lights accelerate across the string of lights repeatedly."""

from __future__ import annotations

import random
from enum import IntFlag
from typing import TYPE_CHECKING

import numpy as np

from lightberries.array_transform.array_transform import ArrayTransform
from lightberries.base.constants import MAX_INT8
from lightberries.base.state import TransformState
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller  # pragma: no cover
    from lightberries.base.state import TransformState  # pragma: no cover
    from lightberries.pixel_sequence import PixelSequence  # pragma: no cover


class AccelerateState(IntFlag):
    """Acceleration."""

    Normal = 0b0001
    Fast = 0b0010
    Faster = 0b0100
    Speeb = 0b1000


class TransformAccelerate(ArrayTransform):
    """Function in which colorful lights accelerate across the string of lights repeatedly."""

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

    @staticmethod
    def create(  # noqa: PLR0913
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
        PixelTransform.clear_active()
        transform = TransformAccelerate(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.current_state = AccelerateState.Normal
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
            transform.state.re_init()
            transform.state.index_range = transform.calc_range()

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

        TransformFadeOff.create(
            controller=controller,
            state=transform.state,
            fade_amount=transform.state.fade_amount,
        )
        TransformAccelerate.ACTIVE_TRANSFORMS.append(transform)
        return TransformAccelerate.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Accelerate across the string of lights repeatedly."""
        super().transform()
        splash_range = np.zeros([], dtype=np.int32)
        splash = False
        # check delay counter, update index when it hits max
        if self.state.delay_count_reset:
            self.advance_index()
            if self.state.color_cycle is True:
                self.state.pixel_sequence.advance_index()
            self.state.index_range = self.calc_sequence_range()
        # check index step counter, update speed state when it hits step count max
        if self.state.step_count_reset:
            # reduce delay max
            self.state.delay_count_max -= 1
            # increment step size every two delay reductions
            self.state.step_size += 1
            # set step counter to a random number of steps based on LED count
            self.state.step_count_max = random.randint(
                int(self.controller.real_led_count / 10),
                int(self.controller.real_led_count * 2),
            )
            # update state counter
            if self.state.current_state & AccelerateState.Normal:
                self.state.current_state = AccelerateState.Fast
            elif self.state.current_state & AccelerateState.Fast:
                self.state.current_state = AccelerateState.Faster
            elif self.state.current_state & AccelerateState.Faster:
                self.state.current_state = AccelerateState.Speeb
            elif self.state.current_state & AccelerateState.Speeb:
                # "splash" color when we hit the end
                splash = True
                #  create the "splash" index array before updating direction etc.
                splash_range = np.array(
                    list(
                        range(
                            self.state.index_previous,
                            self.state.index_next + (self.state.step_size * self.state.direction * 4),
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
                self.state.current_state = AccelerateState.Normal
                # reset step
                self.state.step_size = 1
                # reset step counter
                self.state.step_counter = 0
                # randomize starting index
                self.state.index = self.get_random_index()
                self.state.index_previous = self.state.index
                self.state.index_range = self.calc_sequence_range()
        self.assign_pixel()
        if splash is True:
            self.controller.virtual_led_buffer[splash_range, :] = self.state.fade_color()

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {self.state.pixel_sequence.pixel} {self.state.current_state.value} {self.state.index_range}'  # noqa: E501
