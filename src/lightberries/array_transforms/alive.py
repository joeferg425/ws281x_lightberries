"""Do alive function things."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform
from lightberries.state import ThingColors, ThingMoves, ThingSizes, TransformState

if TYPE_CHECKING:
    import lightberries.array_controller

LOGGER = logging.getLogger("lightBerries")


class TransformAlive(PixelTransform):
    """Do alive function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do alive function things.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.

        """
        super().__init__(
            name=TransformAlive.__name__,
            controller=controller,
            state=state,
        )

    def setup(  # noqa: PLR0913
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
        size_max: int | None = None,
        step_count_max: int | None = None,
        step_size_max: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Configure the transformation.

        Args:
        ----
            color_sequence: _description_. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object
            fade_amount: amount of fade
            size_max: max size of LED pattern
            step_count_max: max duration of effect
            step_size_max: max speed

        Returns:
        -------
            list of transforms

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.fade_amount = random.uniform(0.20, 0.75)
            self.state.size_max = random.randint(
                self.controller.virtual_led_count // 6,
                self.controller.virtual_led_count // 3,
            )
            self.state.step_count_max = random.randint(
                self.controller.virtual_led_count // 10,
                self.controller.virtual_led_count,
            )
            self.state.step_size_max = random.randint(6, 10)

        if fade_amount is not None:
            self.state.fade_amount = fade_amount
        if size_max is not None:
            self.state.size_max = size_max
        if step_size_max is not None:
            self.state.step_count_max = step_size_max
        if fade_amount is not None:
            self.state.set_fade_amount(fade_amount=fade_amount)
        if step_count_max is not None:
            step_count_max = int(step_count_max)

        things: list[PixelTransform] = []
        for _ in range(random.randint(2, 5)):
            thing = TransformAlive(controller=self.controller, state=self.state.copy())
            # randomize start index
            thing.state.index = self.get_random_index()
            # randomize direction
            thing.state.direction = self.get_random_direction()
            # copy color sequence
            thing.color_sequence = self.color_sequence
            # assign color
            thing.state.color = thing.color_sequence_next
            # set max step count before possible state change
            thing.state.step_count_max = step_count_max
            # set max step size in normal condition
            thing.state.step_size_max = step_size_max
            # randomize speed
            thing.state.step = random.randint(1, thing.state.step_size_max)
            # set refresh speed
            thing.state.delay_count_max = random.randint(6, 15)
            # set initial size
            thing.state.size = random.randint(1, int(size_max // 2))
            # set max size
            thing.state.size_max = size_max
            # start the state at 1
            thing.state.state = ThingMoves.METEOR.value
            # calculate random next state immediately
            thing.state.step_counter = 1000
            thing.state.delay_counter = 1000
            things.append(thing)
        things[0].state.active = True
        # add a fade
        fade = TransformFadeOff(controller=self.controller)
        fade.state.fade_amount = fade_amount
        things.insert(0, fade)
        return things

    def transform(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Do alive function things."""
        # track last index
        self.state.index_previous = self.state.index
        # if we have hit our step goal
        if self.state.delay_counter >= self.state.delay_count_max:
            self.state.delay_counter = 0
            if self.state.step_counter < self.state.step_count_max:
                # if in meteor mode
                if self.state.state & ThingMoves.METEOR.value:
                    self.state.step = 1
                    # set next index
                    self.update_array_index()
                    # thing.indexNext = (
                    #     thing.index + (thing.step * thing.direction)
                    # ) % self.controller.virtualLEDCount
                    # randomly change direction
                    if random.randint(0, 99) > 95:
                        self.state.direction *= -1  # pragma: no cover
                # if in fast meteor mode
                elif self.state.state & ThingMoves.LIGHT_SPEED.value:
                    # artificially limit duration of this mode
                    if self.state.step_count_max >= self.state.period_short:
                        self.state.step_count_max = self.state.period_short
                    # randomize step size
                    self.state.step = random.randint(7, 12)
                    # set next index
                    self.update_array_index()
                    # thing.index = (
                    #     thing.index + (thing.step * thing.direction)
                    # ) % self.controller.virtualLEDCount
                    # randomly change direction
                    if random.randint(0, 99) > 95:
                        self.state.direction *= -1  # pragma: no cover
                # if slow meteor
                elif self.state.state & ThingMoves.TURTLE.value:
                    # set step to 1
                    self.state.step = 1
                    # randomly change direction
                    if random.randint(0, 99) > 80:
                        self.state.direction *= -1  # pragma: no cover
                    # set next index
                    self.update_array_index()
                    # thing.index = (
                    #     thing.index + (thing.step * thing.direction)
                    # ) % self.controller.virtualLEDCount
                # if we are growing
                if self.state.state & ThingSizes.GROW.value:
                    # artificially limit duration
                    if self.state.step_count_max > self.state.period_short:
                        self.state.step_count_max = self.state.period_short
                    # if we can still grow
                    if self.state.size < self.state.size_max:
                        # randomly grow
                        if random.randint(0, 99) > 80:
                            self.state.size += random.randint(
                                1,
                                5,
                            )  # pragma: no cover
                        # also randomly shrink a bit
                        if self.state.size > 2:
                            if random.randint(0, 99) > 90:
                                self.state.size -= 1  # pragma: no cover
                    # make sure we aren't overgrown
                    if self.state.size > self.state.size_max:
                        self.state.size = self.state.size_max
                    # make sure we still exist
                    elif self.state.size < 1:
                        self.state.size = 1
                # if we are shrinking
                elif self.state.state & ThingSizes.SHRINK.value:
                    # artificially limit duration
                    if self.state.step_count_max > self.state.period_short:
                        self.state.step_count_max = self.state.period_short
                    # if we can shrink
                    if self.state.size > 0:
                        # randomly shrink
                        if random.randint(0, 99) > 80:
                            self.state.size -= random.randint(1, 5)
                        # also randomly grow a bit
                        if self.state.size < self.state.size_max:
                            if random.randint(0, 99) > 90:
                                self.state.size += 1  # pragma: no cover
                    # make sure we aren't overgrown
                    if self.state.size >= self.state.size_max:
                        self.state.size = self.state.size_max
                    # also make sure we still exist
                    elif self.state.size < 1:
                        self.state.size = 1
                # if we are cycling through colors
                if self.state.state & ThingColors.CYCLE.value:
                    # artificially limit duration
                    if self.state.step_count_max >= self.state.period_short:
                        self.state.step_count_max = self.state.period_short
                    # randomly cycle through assign colors
                    if random.randint(0, 99) > 90:
                        for _ in range(random.randint(1, 3)):
                            self.state.color = self.color_sequence_next
                # calculate range of affected indices
                # index1 = thing.indexPrevious - (thing.size * thing.direction)
                # index2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
                # indexLower = min(index1, index2)
                # indexHigher = max(index1, index2)
                # calculate affected range
                # thing.indexRange = thing.calcRange()
                # increment step counter
                self.state.step_counter += 1
            # we hit our step goal, randomize next state
            else:
                # states are mutually exclusive bits, can just add one of each
                for _ in range(random.randint(1, 3)):
                    self.state.state = (
                        list(ThingMoves)[random.randint(0, len(ThingMoves) - 1)].value
                        + list(ThingSizes)[random.randint(0, len(ThingSizes) - 1)].value
                        + list(ThingColors)[random.randint(0, len(ThingColors) - 1)].value
                    )
                # reset step counter
                self.state.step_counter = 0
                # set step count to random value
                self.state.step_count_max = random.randint(
                    self.controller.virtual_led_count // 10,
                    self.controller.virtual_led_count,
                )
                # set delay count randomly
                self.state.delay_count_max = random.randint(6, 15)
                # randomize step size
                self.state.step = random.randint(1, 3)
                # randomize fade amount
                self.state.fade_amount = random.randint(80, 192)
                # randomize delays
                if self.state.state & ThingMoves.METEOR.value:
                    self.state.delay_count_max = random.randint(1, 3)
                elif self.state.state & ThingMoves.TURTLE.value:
                    self.state.delay_count_max = random.randint(15, 45)
                elif self.state.state & ThingMoves.LIGHT_SPEED.value:
                    self.state.delay_count_max = random.randint(0, 3)
                else:
                    self.state.delay_count_max = random.randint(1, 7)
                # calculate affected range
                # index1 = thing.indexPrevious - (thing.size * thing.direction)
                # index2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
                # indexLower = min(index1, index2)
                # indexHigher = max(index1, index2)
                # rng = np.array(range(_x1, _x2 + 1))
                self.state.index_range = self.calc_range()
        # increment delay
        self.state.delay_counter += 1
        # assign colors to indices
        # self.controller.virtualLEDBuffer[thing.indexRange] = thing.color
        if len(self.controller.virtual_led_buffer.shape) == 2:
            self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
        else:
            self.controller.virtual_led_buffer[
                np.where(
                    self.controller.virtual_led_index_buffer == self.state.index_range,
                )
            ] = self.state.color
