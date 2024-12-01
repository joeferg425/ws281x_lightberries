"""Do meteor function things."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np

from lightberries.base.constants import SHAPE_2D
from lightberries.base.logger import LOGGER
from lightberries.base.state import LEDFadeType, TransformState
from lightberries.overlay.collision_detection import TransformCollisionDetect
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.overlay.off import TransformOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence


class TransformMeteor(PixelTransform):
    """Do meteor function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do meteor function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformMeteor.__name__,
            controller=controller,
        )

    @staticmethod
    def create(  # noqa: C901, PGH003, PLR0912, PLR0913, PLR0915, RUF100 # type: ignore
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
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
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: _description_. Defaults to None.
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
        transform = TransformMeteor(controller=controller)
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        if state is not None:
            transform.state = state
        else:
            transform.state.set_fade_amount(random.randint(20, 40) / 100.0)
            transform.state.explode = transform.get_random_boolean()
            transform.state.collision_enabled = transform.get_random_boolean()
            transform.state.step_size_max = random.randint(1, 3)
            transform.state.step_size = transform.state.step_size_max
            transform.state.delay_count_max = random.randint(1, 3)
            transform.state.explode = transform.get_random_boolean()
            transform.state.color_cycle = transform.get_random_boolean()
            transform.state.fade_type = LEDFadeType.FADE_OFF

        if fade_amount is not None:
            if isinstance(fade_amount, str):
                fade_amount = float(fade_amount)
            transform.state.set_fade_amount(fade_amount=fade_amount)
            LOGGER.debug("fade_amount: %s", transform.state.fade_amount)
        if max_speed is not None:
            if isinstance(max_speed, str):
                max_speed = int(max_speed)
            transform.state.step_size_max = max_speed
            LOGGER.debug("max_step: %s", transform.state.step_size_max)
        if explode is not None:
            if isinstance(explode, str):
                explode = bool(explode)
            transform.state.explode = explode
            LOGGER.debug("explode: %s", transform.state.explode)
        if collide is not None:
            if isinstance(collide, str):
                collide = bool(collide)
            transform.state.collision_enabled = collide
            LOGGER.debug("collide: %s", transform.state.collision_enabled)
        if cycle_colors is not None:
            if isinstance(cycle_colors, str):
                cycle_colors = bool(cycle_colors)
            transform.state.color_cycle = cycle_colors
            LOGGER.debug("cycle: %s", transform.state.color_cycle)
        if delay_count is not None:
            if isinstance(delay_count, str):
                delay_count = int(delay_count)
            transform.state.delay_count_max = delay_count
            LOGGER.debug("max speed: %s", 1 / transform.state.delay_count_max)
        if fade_type is not None:
            if isinstance(fade_type, str):
                fade_type = LEDFadeType(fade_type)
            transform.state.fade_type = fade_type

        if meteor_count is None or isinstance(meteor_count, int) and meteor_count < 1:
            if (transform.state.pixel_sequence.led_count >= 2) and (  # noqa: PLR2004
                transform.state.pixel_sequence.led_count <= 6  # noqa: PLR2004
            ):
                meteor_count = transform.state.pixel_sequence.led_count
            else:
                meteor_count = random.randint(1, 3)
        elif isinstance(meteor_count, str):
            meteor_count = int(meteor_count)

        # make comet trails
        if transform.state.fade_type == LEDFadeType.FADE_OFF:
            TransformFadeOff.create(
                controller=transform.controller,
                fade_amount=fade_amount,
            )
        elif transform.state.fade_type == LEDFadeType.INSTANT_OFF:
            TransformOff.create(controller=transform.controller)

        # this object calculates collisions between other objects based on index and previous/next index
        if collide is True:
            # make sure there are at least two going to collide
            if (
                meteor_count > 1
                and transform.ACTIVE_TRANSFORMS[0].state.direction * transform.ACTIVE_TRANSFORMS[1].state.direction > 0
            ):
                transform.ACTIVE_TRANSFORMS[1].state.direction *= -1
            TransformCollisionDetect.create(controller=transform.controller)

        transform.state.pixel_sequence.get_random_index()
        LOGGER.debug("Transform: %s", transform)
        meteor = None
        for _ in range(meteor_count - 1):
            if meteor is None:
                meteor = transform
            else:
                meteor = transform.copy()
            meteor.state.pixel_sequence.get_random_index()
            # initialize "previous" index, for math's sake later
            meteor.state.index_previous = random.randint(0, transform.controller.virtual_led_count - 1)
            # set the maximum number of LEDs it could move in one step
            speed = 1
            for _ in range(5):
                speed = random.randint(1, max(2, meteor.state.step_size_max))
            meteor.state.step_size = speed
            # randomly initialize the direction
            meteor.state.direction = transform.get_random_direction()
            # randomly assign starting index
            meteor.state.index = (
                meteor.state.index + (meteor.state.step_size * meteor.state.direction)
            ) % transform.controller.virtual_led_count
            # add function to list
            transform.ACTIVE_TRANSFORMS.append(meteor)
        return transform.ACTIVE_TRANSFORMS

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
                self.state.pixel_sequence.advance_index()
            # assign LEDs to LED string
            if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.pixel_sequence.pixel.rgb_array
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.pixel_sequence.pixel.rgb_array
