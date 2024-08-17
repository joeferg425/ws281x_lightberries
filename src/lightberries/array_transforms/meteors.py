"""Do meteor function things."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.collision_detection import TransformCollisionDetect
from lightberries.array_transforms.fade_off import TransformFadeOff
from lightberries.array_transforms.off import TransformOff
from lightberries.constants import MAX_INT8, SHAPE_2D
from lightberries.state import LEDFadeType, TransformState
from lightberries.transform import Transform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.transform import Transform

LOGGER = logging.getLogger("lightBerries")


class TransformMeteor(Transform):
    """Do meteor function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do meteor function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformMeteor.__name__,
            controller=controller,
            state=state,
        )

    def setup(
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
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.fade_amount = random.randint(20, 40) / 100.0
            self.state.explode = self.get_random_boolean()
            self.state.collision_enabled = self.get_random_boolean()
            self.state.step_size_max = random.randint(1, 3)
            self.state.step = self.state.step_size_max
            self.state.delay_count_max = random.randint(1, 3)
            self.state.explode = self.get_random_boolean()
            self.state.color_cycle = self.get_random_boolean()
            self.state.fade_type = LEDFadeType.get_random()

        if meteor_count is None:
            meteor_count = random.randint(1, 3)

        if fade_amount is not None:
            self.state.set_fade_amount(fade_amount=fade_amount)
        if max_speed is not None:
            self.state.step_size_max = max_speed
        if explode is not None:
            self.state.explode = explode
        if collide is not None:
            self.state.collision_enabled = collide
        if cycle_colors is not None:
            self.state.color_cycle = cycle_colors
        if delay_count is not None:
            self.state.delay_count_max = delay_count
        if fade_type is not None:
            self.state.fade_type = fade_type

        if self.color_sequence_count >= 2 and self.color_sequence_count <= 6:
            meteor_count = self.color_sequence_count
        # make sure fade amount is valid
        if fade_amount > 0 and fade_amount < 1:
            pass
        elif fade_amount > 0 and fade_amount <= MAX_INT8:
            fade_amount /= MAX_INT8
        if fade_amount < 0 or fade_amount > 1:
            fade_amount = 0.1

        # make comet trails
        fade = None
        if fade_type == LEDFadeType.FADE_OFF:
            fade = TransformFadeOff(controller=self.controller)
            fade.setup(
                color_sequence=self.color_sequence,
                state=self.state,
                fade_amount=fade_amount,
            )
        elif fade_type == LEDFadeType.INSTANT_OFF:
            fade = TransformOff(controller=self.controller)
            fade.setup(
                color_sequence=self.color_sequence,
                state=self.state,
                fade_amount=fade_amount,
            )
        transforms: list[Transform] = []
        if fade is not None:
            transforms.append(fade)
        for _ in range(meteor_count):
            meteor = TransformMeteor(controller=self.controller, state=state.copy())
            meteor.state.color = self.color_sequence_next
            # initialize "previous" index, for math's sake later
            meteor.state.index_previous = random.randint(0, self.controller.virtual_led_count - 1)
            # set the number of LEDs it will move in one step
            meteor.state.step_size_max = max_speed
            # set the maximum number of LEDs it could move in one step
            meteor.state.step = random.randint(1, max(2, meteor.state.step_size_max))
            # randomly initialize the direction
            meteor.state.direction = self.get_random_direction()
            # set the refresh delay
            meteor.state.delay_count_max = delay_count
            # randomly assign starting index
            meteor.state.index = (
                meteor.state.index + (meteor.state.step * meteor.state.direction)
            ) % self.controller.virtual_led_count
            # set boolean to cycle each meteor through the color sequence as it moves
            meteor.state.color_cycle = cycle_colors
            # assign the color sequence
            meteor.color_sequence = np.copy(self.color_sequence)
            # add function to list
            transforms.append(meteor)
        # make sure there are at least two going to collide
        if transforms[0].state.direction * transforms[1].state.direction > 0:
            transforms[1].state.direction *= -1
        # this object calculates collisions between other objects based on index and previous/next index
        if collide is True:
            collision = TransformCollisionDetect(controller=self.controller, state=self.state.copy())
            collision.state.explode = explode
            transforms.append(collision)
        return transforms

    def transform(self) -> None:
        """Do meteor function things."""
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
            if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.color
