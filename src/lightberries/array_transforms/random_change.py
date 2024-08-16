"""Do random change function things."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.base import ArrayTransform
from lightberries.state import ChangeStates, LEDFadeType, TransformState

if TYPE_CHECKING:
    import lightberries.array_controller

LOGGER = logging.getLogger("lightBerries")


class TransformRandomChange(ArrayTransform):
    """Do random change function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do random change function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformRandomChange.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
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
            delay_count: refresh delay
            change_count: how many LEDs to have in the change queue at once
            fade_step_count: number of steps in the transition from one color to the next
            fade_type: set to fade colors, or instant on/off

        """
        _changeCount: int = random.randint(
            self.virtual_led_count // 5,
            self.virtual_led_count,
        )
        _fadeStepCount: int = random.randint(5, 20)
        _delayCountMax: int = random.randint(30, 50)
        fadeTypes: list[LEDFadeType] = list(LEDFadeType)
        _fadeType: LEDFadeType = fadeTypes[random.randint(0, len(fadeTypes) - 1)]
        if change_count is not None:
            _changeCount = int(change_count)
        if fade_step_count is not None:
            _fadeStepCount = int(fade_step_count)
        _fadeAmount: float = _fadeStepCount / 255.0
        # make sure fade amount is valid
        if _fadeAmount > 0 and _fadeAmount < 1:
            # do nothing
            pass
        elif _fadeAmount > 0 and _fadeAmount < 256:
            _fadeAmount /= 255
        if _fadeAmount < 0 or _fadeAmount > 1:
            _fadeAmount = 0.1
        if delay_count is not None:
            _delayCountMax = int(delay_count)
        if fade_type is not None:
            _fadeType = LEDFadeType(fade_type)
        # make comet trails
        if _fadeType == LEDFadeType.FADE_OFF:
            fade: LightTransform = LightTransform(
                self,
                LightTransform.functionFadeOff,
                self.color_sequence,
            )
            fade._fade_amount = _fadeAmount
            self._transforms.append(fade)
        elif _fadeType == LEDFadeType.INSTANT_OFF:
            off: LightTransform = LightTransform(
                self,
                LightTransform.functionOff,
                self.color_sequence,
            )
            self._transforms.append(off)
        else:
            # do nothing
            pass
        # create a bunch of tracking objects
        for index in self.get_random_indices(int(_changeCount)):
            if index < self.virtual_led_count:
                change: LightTransform = LightTransform(
                    self,
                    LightTransform.functionRandomChange,
                    self.color_sequence,
                )
                # set the index from our random number
                change._index = int(index)
                # set the fade to off amount
                change._fade_amount = _fadeAmount
                # this is used to help calculate fade duration in the function
                change._step_count_max = _fadeStepCount
                # copy the current color of this LED index
                # change.color = np.copy(self.virtualLEDBuffer[change.index])
                if len(LightTransform.Controller.virtualLEDBuffer.shape) == 2:
                    change._color = np.copy(self.virtual_led_buffer[change._index])
                    # ArrayFunction.Controller.virtualLEDBuffer[accelerate.indexRange] = meteor.color
                else:
                    change._color = LightTransform.Controller.virtualLEDBuffer[
                        np.where(
                            LightTransform.Controller.virtualLEDIndexBuffer == change._index,
                        )
                    ]
                # randomly set the color we are fading toward
                if random.randint(0, 1) == 1:
                    change._color_next = self.color_sequence_next
                else:
                    change._color_next = change._color
                # set the refresh delay
                change._delay_count_max = _delayCountMax
                # we want all the delays random, so don't start them all at zero
                change._delay_counter = random.randint(0, change._delay_count_max)
                # set true to fade, false to "instant on/off"
                change._fade_type = _fadeType
                # add function to list
                self._transforms.append(change)

    def transform(self):
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
                    # change.color = np.copy(self.controller.virtualLEDBuffer[change.index])
                    if len(self.controller.virtual_led_buffer.shape) == 2:
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
        # self.controller.virtualLEDBuffer[change.index] = change.color
        if len(self.controller.virtual_led_buffer.shape) == 2:
            self.controller.virtual_led_buffer[self.state.index] = self.state.color
        else:
            self.controller.virtual_led_buffer[
                np.where(self.controller.virtual_led_index_buffer == self.state.index)
            ] = self.state.color
