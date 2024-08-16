"""Do meteor function things."""

from __future__ import annotations

import logging
import random
from typing import Any

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.array_transforms.fade import TransformFade
from lightberries.array_transforms.fade_off import TransformFadeOff
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.state import LEDFadeType, TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformMeteors(ArrayTransform):
    """Do meteor function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do meteor function things.

        Args:
        ----
            meteor: tracking object

        """
        super().__init__(
            name=TransformMeteors.__class__.__name__,
            controller=controller,
        )

    def useFunctionMeteors(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
        max_speed: int | None = None,
        explode: bool | None = None,
        meteor_count: int | None = None,
        collide: bool | None = None,
        cycle_colors: bool | None = None,
        delay_count: int | None = None,
        fade_type: LEDFadeType | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Configure the transformation.

        Args:
        ----
            color_sequence: _description_. Defaults to None.
            state: _description_. Defaults to None.
            kwargs: extra args to the state object
            fade_amount: the amount by which meteors are faded
            max_speed: the amount be which the meteor moves each refresh
            explode: if True, the meteors will light up in an explosion when they collide
            meteor_count: number of meteors
            collide: set true to make them bounce off each other randomly
            cycle_colors: set true to make the meteors shift color as they move
            delay_count: refresh delay
            fade_type: set the type of fade to use using the enumeration

        Returns:
        -------
            list of transforms

        """
        if fade_amount is None:
            fade_amount = random.randint(20, 40) / 100.0
        if explode is None:
            explode = self.get_random_boolean()
        if max_speed is None:
            max_speed = random.randint(1, 3)
        if delay_count is None:
            delay_count = random.randint(1, 3)
        if meteor_count is None:
            meteor_count: int = random.randint(2, 6)
        if collide is None:
            collide = self.get_random_boolean()
        if cycle_colors is None:
            cycle_colors: bool = self.get_random_boolean()
        if fade_type is None:
            fade_types: list[LEDFadeType] = list(LEDFadeType)
            fade_type: LEDFadeType = fade_types[random.randint(0, len(fade_types) - 1)]

        if self.color_sequence_count >= 2 and self.color_sequence_count <= 6:
            meteor_count = self.color_sequence_count
        # make sure fade amount is valid
        if fade_amount > 0 and fade_amount < 1:
            pass
        elif fade_amount > 0 and fade_amount < 256:
            fade_amount /= 255
        if fade_amount < 0 or fade_amount > 1:
            fade_amount = 0.1

        # make comet trails
        fade = TransformFadeOff(controller=self.controller)
        fade.set
        if fade_type == LEDFadeType.FADE_OFF:
            fade: LightTransform = LightTransform(
                self,
                LightTransform.functionFadeOff,
                self.color_sequence,
            )
            fade._fade_amount = fade_amount
            self._transforms.append(fade)
        elif fade_type == LEDFadeType.INSTANT_OFF:
            off: LightTransform = LightTransform(
                self,
                LightTransform.functionOff,
                self.color_sequence,
            )
            self._transforms.append(off)
        else:
            # do nothing
            pass
        for _ in range(meteor_count):
            meteor: LightTransform = LightTransform(
                self,
                LightTransform.functionMeteors,
                self.color_sequence,
            )
            # assign meteor color
            meteor._color = self.color_sequence_next
            # initialize "previous" index, for math's sake later
            meteor._index_previous = random.randint(0, self.virtual_led_count - 1)
            # set the number of LEDs it will move in one step
            meteor._step_size_max = max_speed
            # set the maximum number of LEDs it could move in one step
            meteor._step = random.randint(1, max(2, meteor._step_size_max))
            # randomly initialize the direction
            meteor._direction = self.get_random_direction()
            # set the refresh delay
            meteor._delay_count_max = delay_count
            # randomly assign starting index
            meteor._index = (meteor._index + (meteor._step * meteor._direction)) % self.virtual_led_count
            # set boolean to cycle each meteor through the color sequence as it moves
            meteor._color_cycle = cycle_colors
            # assign the color sequence
            meteor.color_sequence = np.copy(self.color_sequence)
            # add function to list
            self._transforms.append(meteor)
        # make sure there are at least two going to collide
        if self._transforms[0]._direction * self._transforms[1]._direction > 0:
            self._transforms[1]._direction *= -1
        # this object calculates collisions between other objects based on index and previous/next index
        if collide is True:
            collision = LightTransform(
                self,
                LightTransform.functionCollisionDetection,
                self.color_sequence,
            )
            collision._explode = explode
            self._transforms.append(collision)

    def transform(self):
        # update delay counter
        self.state.delay_counter += 1
        # check if we are done delaying
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # calculate index + step
            self.update_array_index()
            if self.state.color_cycle:
                # assign the next color
                self.state.color = self.color_sequence_next
            # assign LEDs to LED string
            if len(self.controller.virtual_led_buffer.shape) == 2:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.color
