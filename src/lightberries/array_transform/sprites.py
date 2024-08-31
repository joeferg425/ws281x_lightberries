"""Do sprite function things."""

from __future__ import annotations

import logging
import random
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

from lightberries.constants import SHAPE_2D
from lightberries.pixel import PixelColor, pixel_from_color
from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay.fade_off import TransformFadeOff

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
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
    ) -> None:
        """Do sprite function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=f"{TransformSprites.__name__}[{len(self.ACTIVE_TRANSFORMS)}]",
            controller=controller,
        )

    @staticmethod
    def setup(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_steps: int | None = None,
        sprite_count: int | None = None,
    ) -> list[PixelTransform]:
        """Meteors fade in and out in short bursts of random length and direction.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            fade_steps: amount to fade
            sprite_count:the number of sprites to render

        """
        transform = TransformSprites(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.set_fade_amount(np.ceil(255 / random.randint(1, 6)))

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence.copy()

        if sprite_count is None or sprite_count < 1 or sprite_count > 10:  # noqa: PLR2004
            sprite_count = max(min(transform.state.pixel_sequence.led_count, 10), 2)

        if fade_steps is not None:
            transform.state.set_fade_amount(np.ceil(255 / fade_steps))

        TransformFadeOff.setup(
            controller=transform.controller,
            fade_amount=transform.state.fade_amount,
        )
        sprite = None
        for _ in range(sprite_count - 1):
            if sprite is None:
                sprite = transform
            else:
                sprite = transform.copy()
            # randomize index
            sprite.state.index = random.randint(0, transform.controller.virtual_led_count - 1)
            # initialize previous index
            sprite.state.index_previous = random.randint(0, transform.controller.virtual_led_count - 1)
            # randomize direction
            sprite.state.direction = transform.get_random_direction()
            # copy color sequence
            sprite.state.pixel_sequence = transform.state.pixel_sequence.copy()
            # advance the color sequence
            transform.state.pixel_sequence.advance_index()
            sprite.state.current_state = SpriteState.OFF.value
            transform.ACTIVE_TRANSFORMS.append(sprite)
        # set one sprite to "fading on"
        transform.ACTIVE_TRANSFORMS[0].state.current_state = SpriteState.FADING_ON.value
        # add LED fading for comet trails
        return transform.ACTIVE_TRANSFORMS

    def transform(self) -> None:  # noqa: C901
        """Meteors fade in and out in short bursts of random length and direction."""
        # if not off
        if self.state.current_state != SpriteState.OFF:
            # semi-randomly die
            _min = min(int(self.state.step_counter // 3), 5)
            _max = max(int(self.state.step_counter // 3), 6)
            if random.randint(_min, _max) < self.state.step_counter:
                self.state.current_state = SpriteState.FADING_OFF.value
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
            if self.state.current_state == SpriteState.FADING_OFF.value:
                # fade the color
                self.state.pixel_sequence.pixel.fade(
                    color_next=pixel_from_color(PixelColor.OFF),
                    fade_amount=self.state.fade_amount,
                )
                # if we are done fading, then change state
                if self.state.pixel_sequence.pixel == pixel_from_color(PixelColor.OFF):
                    self.state.current_state = SpriteState.OFF.value
            # if we are fading on
            if self.state.current_state == SpriteState.FADING_ON.value:
                # fade the color
                self.state.pixel_sequence.pixel.fade(
                    color_next=self.state.pixel_sequence.pixel,
                    fade_amount=self.state.fade_amount,
                )
                # if we are done fading
                if self.state.pixel_sequence.pixel == self.state.pixel_sequence.pixel_next:
                    # change state
                    self.state.current_state = SpriteState.ON.value
            # increment duration counter
            self.state.step_counter += 1
        # when sprite is in "off" state
        elif random.randint(0, 999) > 800:  # noqa: PLR2004
            # set state to fade on
            self.state.current_state = SpriteState.FADING_ON.value
            # reset step counter
            self.state.step_counter = 0
            # randomize direction
            self.state.direction = self.get_random_direction()
            # randomize start index
            self.state.index = self.get_random_index()
            # set previous (prevent artifacts)
            self.state.index_previous = self.state.index
            # set target color
            self.state.pixel_sequence.advance_index()
            self.state.pixel_sequence = self.state.pixel_sequence
            # set current color
            self.state.pixel_sequence.pixel = pixel_from_color(PixelColor.OFF)
        # if we changed the index
        if self.state.index_updated is True:
            # reset flag
            self.state.index_updated = False
            # assign LEDs to LED string
            if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                self.controller.virtual_led_buffer[self.state.index_range] = self.state.pixel_sequence.pixel.array
            else:
                self.controller.virtual_led_buffer[
                    np.where(
                        self.controller.virtual_led_index_buffer == self.state.index_range,
                    )
                ] = self.state.pixel_sequence.pixel.array
