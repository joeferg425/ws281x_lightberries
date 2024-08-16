"""Do sprite function things."""

from __future__ import annotations

import logging
from enum import IntEnum
from random import random

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.pixel import PixelColors

LOGGER = logging.getLogger("lightBerries")


class SpriteState(IntEnum):
    """Sprite function enum."""

    OFF = 0
    FADING_ON = 1
    ON = 2
    FADING_OFF = 3


class TransformSprites(ArrayTransform):
    """Do sprite function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do sprite function things.

        Args:
        ----
            sprite: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        super().__init__(
            name=TransformSprites.__class__.__name__,
            controller=controller,
        )

    def setup(
        self,
        fade_steps: int | None = None,
    ) -> None:
        """Meteors fade in and out in short bursts of random length and direction.

        Args:
        ----
            fadeSteps: amount to fade

        """
        if fade_steps is None:
            fade_steps = random.randint(1, 6)
        fade_amount = np.ceil(255 / fade_steps)
        # make sure fade amount is valid
        if fade_amount > 0 and fade_amount < 1:
            # do nothing
            pass
        elif fade_amount > 0 and fade_amount < 256:
            fade_amount /= 255
        if fade_amount < 0 or fade_amount > 1:
            fade_amount = 0.1
        for _ in range(max(min(self.color_sequence_count, 10), 2)):
            sprite: LightTransform = LightTransform(
                self,
                LightTransform.functionSprites,
                self.color_sequence,
            )
            # randomize index
            sprite._index = random.randint(0, self.virtual_led_count - 1)
            # initialize previous index
            sprite._index_previous = sprite._index
            # randomize direction
            sprite._direction = self.get_random_direction()
            # assign the target color
            sprite._color_goal = self.color_sequence_next
            # initialize sprite to
            sprite._color = ArraySequence.DEFAULT_BACKGROUND_COLOR.array
            # copy color sequence
            sprite.color_sequence = self.color_sequence
            # set next color
            sprite._color_next = PixelColors.OFF.array
            # set fade step/amount
            sprite._fade_steps = fade_steps
            sprite._fade_amount = fade_amount
            sprite.state = SpriteState.OFF.value
            self._transforms.append(sprite)
        # set one sprite to "fading on"
        self._transforms[0].state = SpriteState.FADING_ON.value
        # add LED fading for comet trails
        fade = LightTransform(
            self,
            LightTransform.functionFadeOff,
            self.color_sequence,
        )
        fade._fade_amount = fade_amount
        self._transforms.append(fade)

    def transform(self):
        # if not off
        if self.state.state != SpriteState.OFF.value:
            # semi-randomly die
            _min = min(int(self.state.step_counter // 3), 5)
            _max = max(int(self.state.step_counter // 3), 6)
            if random.randint(_min, _max) < self.state.step_counter:
                self.state.state = SpriteState.FADING_OFF.value
            # randomize step sizes
            self.state.step = random.randint(1, 3)
            # only update LED string when we change the index
            self.state.index_updated = False
            # if we are done delaying
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # move index
                self.update_array_index()
            # if we are fading off
            if self.state.state == SpriteState.FADING_OFF.value:
                # fade the color
                self.state.color = self.controller.fade_color(
                    self.state.color,
                    self.state.color_next,
                    self.state.fade_amount,
                )
                # if we are done fading, then change state
                if np.array_equal(self.state.color, self.state.color_next):
                    self.state.state = SpriteState.OFF.value
            # if we are fading on
            if self.state.state == SpriteState.FADING_ON.value:
                # fade the color
                self.state.color = self.controller.fade_color(
                    self.state.color,
                    self.state.color_goal,
                    self.state.fade_amount,
                )
                # if we are done fading
                if np.array_equal(self.state.color, self.state.color_goal):
                    # change state
                    self.state.state = SpriteState.ON.value
            # increment duration counter
            self.state.step_counter += 1
        # when sprite is in "off" state
        elif random.randint(0, 999) > 800:
            # set state to fade on
            self.state.state = SpriteState.FADING_ON.value
            # reset step counter
            self.state.step_counter = 0
            # randomize direction
            self.state.direction = self.controller.get_random_direction()
            # randomize start index
            self.state.index = self.controller.get_random_index()
            # set previous (prevent artifacts)
            self.state.index_previous = self.state.index
            # set target color
            self.state.color_goal = self.color_sequence_next
            # set current color
            self.state.color = PixelColors.OFF.array
            # set next color
            self.state.color_next = PixelColors.OFF.array
        # if we changed the index
        if self.state.index_updated is True and isinstance(
            self.state.index_range,
            np.ndarray,
        ):
            # reset flag
            self.state.index_updated = False
            # assign LEDs to LED string
            # self.controller.virtualLEDBuffer[sprite.indexRange] = [sprite.color] * len(sprite.indexRange)
            if len(self.controller.virtual_led_buffer.shape) == 2:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.color
