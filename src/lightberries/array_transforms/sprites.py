"""Do sprite function things."""

from __future__ import annotations

import logging
import random
from enum import IntEnum
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.fade_off import TransformFadeOff
from lightberries.constants import SHAPE_2D
from lightberries.pixel import PixelColor
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    from numpy.typing import NDArray

    import lightberries.array_controller
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class SpriteState(IntEnum):
    """Sprite function enum."""

    OFF = 0
    FADING_ON = 1
    ON = 2
    FADING_OFF = 3


class TransformSprites(PixelTransform):
    """Do sprite function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do sprite function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformSprites.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: NDArray[np.int32] | None = None,
        state: TransformState | None = None,
        *,
        fade_steps: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Meteors fade in and out in short bursts of random length and direction.

        Args:
        ----
            fadeSteps: amount to fade

        """
        if color_sequence is not None:
            self.color_sequence = color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.set_fade_amount(np.ceil(255 / random.randint(1, 6)))

        if fade_steps is not None:
            self.state.set_fade_amount(np.ceil(255 / fade_steps))

        sprites: list[PixelTransform] = []
        for _ in range(max(min(self.color_sequence_count, 10), 2)):
            sprite = TransformSprites(
                controller=self.controller,
                state=self.state.copy(),
            )
            # randomize index
            sprite.state.index = random.randint(0, self.controller.virtual_led_count - 1)
            # initialize previous index
            sprite.state.index_previous = random.randint(0, self.controller.virtual_led_count - 1)
            # randomize direction
            sprite.state.direction = self.get_random_direction()
            # assign the target color
            sprite.state.color_next = self.color_sequence_next
            # initialize sprite to
            sprite.state.color = PixelSequence.DEFAULT_BACKGROUND_COLOR.array
            # copy color sequence
            sprite.state.color_sequence = self.color_sequence
            sprite.state.state = SpriteState.OFF.value
            sprites.append(sprite)
        # set one sprite to "fading on"
        sprites[0].state.state = SpriteState.FADING_ON.value
        # add LED fading for comet trails
        fade = TransformFadeOff(
            controller=self.controller,
            state=self.state.copy(),
        )
        sprites.insert(0, fade)
        return sprites

    def transform(self) -> None:
        """Meteors fade in and out in short bursts of random length and direction."""
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
                self.state.color = self.state.fade_color()
                # if we are done fading, then change state
                if np.array_equal(self.state.color, self.state.color_next):
                    self.state.state = SpriteState.OFF.value
            # if we are fading on
            if self.state.state == SpriteState.FADING_ON.value:
                # fade the color
                self.state.color = self.state.fade_color()
                # if we are done fading
                if np.array_equal(self.state.color, self.state.color_next):
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
            self.state.direction = self.get_random_direction()
            # randomize start index
            self.state.index = self.get_random_index()
            # set previous (prevent artifacts)
            self.state.index_previous = self.state.index
            # set target color
            self.state.color_next = self.color_sequence_next
            # set current color
            self.state.color = PixelColor.OFF.array
        # if we changed the index
        if self.state.index_updated is True:
            # reset flag
            self.state.index_updated = False
            # assign LEDs to LED string
            if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.color
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.color
