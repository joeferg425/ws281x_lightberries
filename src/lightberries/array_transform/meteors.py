"""Do meteor function things."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transform.collision_detection import TransformCollisionDetect
from lightberries.array_transform.fade_off import TransformFadeOff
from lightberries.constants import SHAPE_2D
from lightberries.pixel_transform import PixelTransform
from lightberries.state import LEDFadeType, TransformState
from lightberries.transform_overlay.off import TransformOff

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence

LOGGER = logging.getLogger("lightBerries")


class TransformMeteor(PixelTransform):
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

    def setup(  # noqa: C901, PGH003, PLR0912, PLR0913, PLR0915, RUF100 # type: ignore
        self,
        color_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | str | None = None,
        max_speed: int | str | None = None,
        explode: bool | str | None = None,
        meteor_count: int | str | None = None,
        collide: bool | str | None = None,
        cycle_colors: bool | str | None = None,
        delay_count: int | str | None = None,
        fade_type: LEDFadeType | str | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
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
        self.ACTIVE_TRANSFORMS.clear()
        if color_sequence is not None:
            self.state.color_sequence = color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.set_fade_amount(random.randint(20, 40) / 100.0)
            self.state.explode = self.get_random_boolean()
            self.state.collision_enabled = self.get_random_boolean()
            self.state.step_size_max = random.randint(1, 3)
            self.state.step = self.state.step_size_max
            self.state.delay_count_max = random.randint(1, 3)
            self.state.explode = self.get_random_boolean()
            self.state.color_cycle = self.get_random_boolean()
            self.state.fade_type = LEDFadeType.FADE_OFF

        if fade_amount is not None:
            if isinstance(fade_amount, str):
                fade_amount = float(fade_amount)
            self.state.set_fade_amount(fade_amount=fade_amount)
        if max_speed is not None:
            if isinstance(max_speed, str):
                max_speed = int(max_speed)
            self.state.step_size_max = max_speed
        if explode is not None:
            if isinstance(explode, str):
                explode = bool(explode)
            self.state.explode = explode
        if collide is not None:
            if isinstance(collide, str):
                collide = bool(collide)
            self.state.collision_enabled = collide
        if cycle_colors is not None:
            if isinstance(cycle_colors, str):
                cycle_colors = bool(cycle_colors)
            self.state.color_cycle = cycle_colors
        if delay_count is not None:
            if isinstance(delay_count, str):
                delay_count = int(delay_count)
            self.state.delay_count_max = delay_count
        if fade_type is not None:
            if isinstance(fade_type, str):
                fade_type = LEDFadeType(fade_type)
            self.state.fade_type = fade_type

        if meteor_count is None or isinstance(meteor_count, int) and meteor_count < 1:
            if self.state.color_sequence.led_count >= 2 and self.state.color_sequence.led_count <= 6:  # noqa: PLR2004
                meteor_count = self.state.color_sequence.led_count
            else:
                meteor_count = random.randint(1, 3)
        elif isinstance(meteor_count, str):
            meteor_count = int(meteor_count)

        # make comet trails
        if self.state.fade_type == LEDFadeType.FADE_OFF:
            fade = TransformFadeOff(controller=self.controller)
            fade.setup(
                state=self.state,
                fade_amount=fade_amount,
            )
            self.ACTIVE_TRANSFORMS.append(fade)
        elif self.state.fade_type == LEDFadeType.INSTANT_OFF:
            fade = TransformOff(controller=self.controller)
            fade.setup(
                color_sequence=self.state.color_sequence,
                state=self.state,
            )
            self.ACTIVE_TRANSFORMS.append(fade)

        self.state.color_sequence.random_index()
        self.ACTIVE_TRANSFORMS.append(self)
        for _ in range(meteor_count - 1):
            meteor = TransformMeteor(controller=self.controller, state=self.state.copy())
            self.state.color_sequence.random_index()
            # initialize "previous" index, for math's sake later
            meteor.state.index_previous = random.randint(0, self.controller.virtual_led_count - 1)
            # set the maximum number of LEDs it could move in one step
            speed = 1
            for _ in range(5):
                speed = random.randint(1, max(2, meteor.state.step_size_max))
            meteor.state.step = speed
            # randomly initialize the direction
            meteor.state.direction = self.get_random_direction()
            # randomly assign starting index
            meteor.state.index = (
                meteor.state.index + (meteor.state.step * meteor.state.direction)
            ) % self.controller.virtual_led_count
            # add function to list
            self.ACTIVE_TRANSFORMS.append(meteor)
        # this object calculates collisions between other objects based on index and previous/next index
        if collide is True:
            # make sure there are at least two going to collide
            if (
                meteor_count > 1
                and self.ACTIVE_TRANSFORMS[0].state.direction * self.ACTIVE_TRANSFORMS[1].state.direction > 0
            ):
                self.ACTIVE_TRANSFORMS[1].state.direction *= -1
            collision = TransformCollisionDetect(controller=self.controller, state=self.state.copy())
            self.ACTIVE_TRANSFORMS.insert(0, collision)
        return self.ACTIVE_TRANSFORMS

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
                self.state.color_sequence.advance_index()
            # assign LEDs to LED string
            if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.color_sequence.pixel.array
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.color_sequence.pixel.array
