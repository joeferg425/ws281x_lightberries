"""Do random change function things."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.fade_off import TransformFadeOff
from lightberries.array_transforms.off import TransformOff
from lightberries.constants import MAX_INT8, SHAPE_2D
from lightberries.state import ChangeStates, LEDFadeType, TransformState
from lightberries.transform import Transform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.transform import Transform

LOGGER = logging.getLogger("lightBerries")


class TransformRandomChange(Transform):
    """Do random change function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do random change function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformRandomChange.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        delay_count: int | None = None,
        change_count: int | None = None,
        fade_step_count: int | None = None,
        fade_type: LEDFadeType | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Randomly changes pixels from one color to the next.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object
            delay_count: refresh delay
            change_count: how many LEDs to have in the change queue at once
            fade_step_count: number of steps in the transition from one color to the next
            fade_type: set to fade colors, or instant on/off

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.delay_count_max = random.randint(30, 50)
            self.state.fade_type = LEDFadeType.get_random()

        if change_count is None:
            change_count = random.randint(
                self.controller.virtual_led_count // 5,
                self.controller.virtual_led_count,
            )

        if fade_step_count is None:
            fade_step_count = random.randint(5, 20)
        self.state.set_fade_amount(fade_step_count / MAX_INT8)
        if delay_count is not None:
            self.state.delay_count_max = delay_count
        if fade_type is not None:
            self.state.fade_type = fade_type
        # make comet trails
        fade = None
        if self.state.fade_type == LEDFadeType.FADE_OFF:
            fade = TransformOff(
                controller=self.controller,
                state=self.state.copy(),
            )
        elif self.state.fade_type == LEDFadeType.INSTANT_OFF:
            fade = TransformFadeOff(
                controller=self.controller,
                state=self.state.copy(),
            )
        drops: list[Transform] = []
        if fade is not None:
            drops.append(fade)
        # create a bunch of tracking objects
        for index in self.get_random_indices(int(change_count)):
            if index < self.controller.virtual_led_count:
                change = TransformRandomChange(
                    controller=self.controller,
                    state=self.state.copy(),
                )
                # set the index from our random number
                change.state.index = int(index)
                # copy the current color of this LED index
                if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                    change.state.color = np.copy(self.virtual_led_buffer[change.state.index])
                else:
                    change.state.color = self.controller.virtual_led_buffer[
                        np.where(
                            self.controller.virtual_led_index_buffer == change.state.index,
                        )
                    ]
                # randomly set the color we are fading toward
                if random.randint(0, 1) == 1:
                    change.state.color_next = self.color_sequence_next
                else:
                    change.state.color_next = change.state.color
                # we want all the delays random, so don't start them all at zero
                change.state.delay_counter = random.randint(0, change.state.delay_count_max)
                # add function to list
                drops.append(change)
        return drops

    def transform(self) -> None:
        """Randomly changes pixels from one color to the next."""
        # if the random change has completed
        if np.array_equal(self.state.color, self.state.color_next):
            # if the state is "fading on"
            if self.state.state == ChangeStates.FADING_ON.value:
                # just set next state to "on"
                self.state.state = ChangeStates.ON.value
            # if the state is "on"
            elif self.state.state == ChangeStates.ON.value:
                # increment delay counter
                self.state.delay_counter += 1
                # if we are done delaying
                if self.state.delay_counter >= self.state.delay_count_max:
                    # reset delay counter
                    self.state.delay_counter = random.randint(
                        0,
                        self.state.delay_count_max,
                    )
                    # randomly fading some LEDs to background color
                    if random.randint(0, 3) == 3:
                        # set next color to background color
                        self.state.color_next = self.controller.background_color
                        # set state to "fading off"
                        self.state.state = ChangeStates.FADING_OFF.value
                    # if not fading to background
                    else:
                        # go to wait state
                        self.state.state = ChangeStates.WAIT.value
            # if state is "fading off"
            elif self.state.state == ChangeStates.FADING_OFF.value:
                # increment delay counter
                self.state.delay_counter += 1
                # if we are done delaying
                if self.state.delay_counter >= self.state.delay_count_max:
                    # set state to "waiting"
                    self.state.state = ChangeStates.WAIT.value
                    # reset delay counter
                    self.state.delay_counter = random.randint(
                        0,
                        self.state.delay_count_max,
                    )
            # if state is "waiting"
            elif self.state.state == ChangeStates.WAIT.value:
                # increment delay counter
                self.state.delay_counter += 1
                # if we are done waiting
                if self.state.delay_counter >= self.state.delay_count_max:
                    # randomize next index
                    self.state.index = self.controller.get_random_index()
                    # get color of current LED index
                    if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                        self.state.color = self.controller.virtual_led_buffer[self.state.index]
                    else:
                        self.state.color = self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == self.state.index,
                            )
                        ]
                    # get next color
                    for _ in range(random.randint(1, 5)):
                        self.state.color_next = self.color_sequence_next
                    # set state to "fading on"
                    self.state.state = ChangeStates.FADING_ON.value
                    # randomize delay counter so they aren't synchronized
                    self.state.delay_counter = random.randint(
                        0,
                        self.state.delay_count_max,
                    )
        # if fading LEDs
        if self.state.fade_type == LEDFadeType.FADE_OFF:
            # fade the color
            self.state.color = self.controller.fade_color(
                self.state.color,
                self.state.color_next,
                self.state.fade_amount,
            )
        # if instant on/off
        else:
            # set the color
            self.state.color = self.state.color_next
        # assign LED color to LED string
        if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
            self.controller.virtual_led_buffer[self.state.index] = self.state.color
        else:
            self.controller.virtual_led_buffer[
                np.where(self.controller.virtual_led_index_buffer == self.state.index)
            ] = self.state.color
