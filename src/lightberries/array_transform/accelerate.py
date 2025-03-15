"""Function in which colorful lights accelerate across the string of lights repeatedly."""

from __future__ import annotations

import random
from enum import IntFlag
from typing import TYPE_CHECKING

import numpy as np

from lightberries.array_transform.base import ArrayTransform
from lightberries.base.constants import MAX_INT8
from lightberries.base.state import TransformState
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller  # pragma: no cover
    from lightberries.base.state import TransformState  # pragma: no cover
    from lightberries.pixel_sequence import PixelSequence  # pragma: no cover

MIN_DELAY = 20
MAX_DELAY = 35


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
        self.state.flags = AccelerateState.Normal

    @staticmethod
    def create(  # noqa: PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        delay_count: int | None = None,
        step_count: int | None = None,
        fade_amount: float | None = None,
        color_cycle: bool | None = None,
        instance_count: int | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: _description_. Defaults to None.
            state: initial state. Defaults to None.
            delay_count: maximum number of iterations to delay for
            step_count: maximum number of steps to run for
            fade_amount: amount of fade
            color_cycle: set true to cycle through colors in sequence
            instance_count: make this many of this transform

        Returns:
        -------
            list of transforms

        """
        PixelTransform.clear_active()
        transform = TransformAccelerate(controller=controller)
        if state is not None:
            transform.state = state
        else:
            # start in slow, normal speed
            transform.state.flags = AccelerateState.Normal
            # set the number of updates during which the lights will stay constant
            transform.state.delay_count_max = random.randint(MIN_DELAY, MAX_DELAY)
            # set a random number of steps after which we will speed up
            transform.state.secondary_count_max = random.randint(
                transform.controller.real_led_count // 2,
                transform.controller.real_led_count * 3,
            )
            transform.state.secondary_count_reset_value = transform.state.secondary_count_max
            # this determines the length of comet tails
            transform.state.set_fade_amount(random.randint(15, 35) / MAX_INT8)
            # whether to cycle through colors
            transform.state.color_cycle = transform.get_random_boolean()
            # randomize direction
            transform.state.direction = transform.get_random_direction()
            # randomize start index
            transform.state.index = transform.get_random_index()
            transform.state.re_init()
            transform.calc_sequence_range()
            transform.state.pixel_sequence.get_random_index()
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        if delay_count is not None:
            transform.state.delay_count_max = delay_count
        if step_count is not None:
            transform.state.step_count_max = step_count
        if fade_amount is not None:
            transform.state.set_fade_amount(fade_amount)
        if instance_count is None:
            instance_count = random.randint(1, 8)

        if color_cycle is not None:
            transform.state.color_cycle = color_cycle
            transform.state.color_cycle_randomize = False
        else:
            transform.state.color_cycle_randomize = True

        TransformFadeOff.create(
            controller=controller,
            state=transform.state,
            fade_amount=transform.state.fade_amount,
        )
        for _ in range(instance_count):
            transform.state.pixel_sequence.advance_index()
            transform = transform.copy()
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
            self.advance_step_counter()
            if self.state.color_cycle is True:
                self.state.pixel_sequence.advance_index()
            self.calc_sequence_range()
            self.state.secondary_counter += 1
            # randomly speed up a little
            self.state.step_size += 1 if random.randint(0, 1000) >= 990 else 0  # noqa: PLR2004
            self.state.delay_count_max -= 1 if random.randint(0, 100) >= 90 else 0  # noqa: PLR2004
        if self.state.secondary_counter > self.state.secondary_count_max:
            self.state.secondary_counter = 0
            self.state.secondary_count_max //= 2
            if self.state.flags & AccelerateState.Normal:
                self.state.flags = AccelerateState.Fast
                self.state.delay_count_max //= random.randint(1, 2)
            elif self.state.flags & AccelerateState.Fast:
                self.state.flags = AccelerateState.Faster
                self.state.delay_count_max //= random.randint(1, 2)
            elif self.state.flags & AccelerateState.Faster:
                self.state.flags = AccelerateState.Speeb
                self.state.delay_count_max //= random.randint(1, 2)
            elif self.state.flags & AccelerateState.Speeb:
                # "splash" color when we hit the end
                splash = True
                self.state.secondary_count_max = self.state.secondary_count_reset_value
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
                # set the number of updates during which the lights will stay constant
                self.state.delay_count_max = random.randint(MIN_DELAY, MAX_DELAY)
                self.state.set_fade_amount(random.randint(15, 35) / MAX_INT8)
                # randomize direction
                self.state.direction = self.get_random_direction()
                # reset state
                self.state.flags = AccelerateState.Normal
                # reset step
                self.state.step_size = 1
                # randomize starting index
                self.state.index = self.get_random_index()
                self.state.pixel_sequence.get_random_index()
                if self.state.color_cycle_randomize:
                    self.state.color_cycle = self.get_random_boolean()
                self.state.index_previous = self.state.index
                self.calc_sequence_range()
            # reset delay
            self.state.delay_counter = 0
            # reset step counter
            self.state.step_counter = 0
        self.assign_pixel_to_array()
        if splash is True:
            self.controller.virtual_led_buffer[splash_range, :] = self.state.fade_color()

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {self.state.pixel_sequence.pixel} {str(self.state.flags) if self.state.flags != 0 else ""}'  # type: ignore  # noqa: E501, PGH003
