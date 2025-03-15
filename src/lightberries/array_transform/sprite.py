"""Do sprite function things."""

from __future__ import annotations

import random
from enum import IntFlag
from typing import TYPE_CHECKING

import numpy as np

from lightberries.base.pixel import PixelColor, pixel_from_color
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence


class SpriteState(IntFlag):
    """Sprite function enum."""

    OFF = 16
    FADING_ON = 32
    ON = 64
    FADING_OFF = 128


class TransformSprite(PixelTransform):
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
            name=f"{TransformSprite.__name__}[{len(self.ACTIVE_TRANSFORMS)}]",
            controller=controller,
        )

    @staticmethod
    def create(  # noqa: C901, PLR0912, PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_steps: int | None = None,
        instance_count: int | None = None,
        delay_counter: int | None = None,
    ) -> list[PixelTransform]:
        """Meteors fade in and out in short bursts of random length and direction.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            fade_steps: amount to fade
            instance_count:the number of sprites to render
            delay_counter: run function [delay_counter] times before updating to slow it down

        """
        transform = TransformSprite(controller=controller)
        if state is not None:
            transform.state = state
        else:
            if random.randint(1, 99) > 90:  # noqa: PLR2004
                # randomly dont fade
                transform.state.set_fade_amount(255)
            else:
                # randomly fade
                transform.state.set_fade_amount(np.ceil(255 / random.randint(5, 15)))
            transform.state.delay_counter = random.randint(10, 25)

        if pixel_sequence is not None:
            pixel_sequence.advance_index()
            transform.state.pixel_sequence = pixel_sequence.copy()

        if instance_count is None or instance_count < 1 or instance_count > 10:  # noqa: PLR2004
            instance_count = max(min(transform.state.pixel_sequence.led_count, 10), 2)

        if fade_steps is not None and fade_steps != 0:
            transform.state.set_fade_amount(np.ceil(255 / fade_steps))
        else:
            transform.state.fade_amount = 255
        if delay_counter is not None:
            transform.state.delay_counter = delay_counter

        if fade_steps != 0:
            TransformFadeOff.create(
                controller=transform.controller,
                fade_amount=transform.state.fade_amount,
            )
        sprite = None
        for _ in range(instance_count):
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
            transform.state.pixel_sequence.pixel = pixel_from_color(PixelColor.OFF)
            # randomize the delays
            if delay_counter is None:
                transform.state.delay_counter = random.randint(5, 15)
            sprite.state.flags = SpriteState.OFF
            transform.ACTIVE_TRANSFORMS.append(sprite)
        # set one sprite to "fading on"
        transform.ACTIVE_TRANSFORMS[0].state.flags = SpriteState.FADING_ON
        # add LED fading for comet trails
        return transform.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Meteors fade in and out in short bursts of random length and direction."""
        # if not off
        super().transform()
        if self.state.flags & SpriteState.ON:
            # semi-randomly die
            if random.randint(0, 100) > 85:  # noqa: PLR2004
                # unset off
                self.state.flags &= ~SpriteState.ON
                # set fading off
                self.state.flags |= SpriteState.FADING_OFF
                self.state.pixel_sequence.pixel_next = pixel_from_color(PixelColor.OFF)
            # only update LED string when we change the index
            self.state.index_updated = False
            # if we are done delaying
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # move index
                self.advance_index()
            # if we are fading off
        elif SpriteState.FADING_OFF & self.state.flags:
            # fade the color
            self.state.pixel_sequence.pixel = self.state.pixel_sequence.pixel.fade(
                color_next=pixel_from_color(PixelColor.OFF),
                fade_amount=self.state.fade_amount,
            )
            # if we are done fading, then change state
            if self.state.pixel_sequence.pixel == pixel_from_color(PixelColor.OFF):
                # unset fading off
                self.state.flags &= ~SpriteState.FADING_OFF
                # set off
                self.state.flags |= SpriteState.OFF
                self.state.pixel_sequence.pixel_next = self.state.pixel_sequence.pixel_next
        # if we are fading on
        elif self.state.flags & SpriteState.FADING_ON:
            # fade the color
            self.state.pixel_sequence.pixel = self.state.pixel_sequence.pixel.fade(
                color_next=self.state.pixel_sequence.pixel_next,
                fade_amount=self.state.fade_amount,
            )
            # if we are done fading
            if self.state.pixel_sequence.pixel == self.state.pixel_sequence.pixel_next:
                # unset fading on
                self.state.flags &= ~SpriteState.FADING_ON
                # set on
                self.state.flags |= SpriteState.ON
        # when sprite is in "off" state
        elif self.state.flags & SpriteState.OFF and random.randint(0, 999) > 800:  # noqa: PLR2004
            # set state to fade on
            self.state.flags &= ~SpriteState.OFF
            self.state.flags |= SpriteState.FADING_ON
            # randomize step sizes
            self.state.step_size = random.randint(1, 3)
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
            self.state.pixel_sequence.pixel_next = self.state.pixel_sequence.pixel
            self.state.pixel_sequence.pixel = pixel_from_color(PixelColor.OFF)
            self.state.delay_counter = random.randint(10, 25)
        # increment duration counter
        self.state.step_counter += 1
        self.calc_sequence_range()
        self.assign_pixel_to_array()

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {self.state.pixel_sequence.pixel} {self.state.flags!s}'
