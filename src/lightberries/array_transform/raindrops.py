"""Do raindrop function things."""

from __future__ import annotations

import random
from enum import IntFlag
from typing import TYPE_CHECKING

import numpy as np

from lightberries.base.constants import MAX_INT8, SHAPE_2D
from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence

MIN_FADE = 5
MAX_FADE = 50


class RaindropStates(IntFlag):
    """Raindrop function states."""

    OFF = 1
    SPLASH = 2


class TransformRaindrop(PixelTransform):
    """Do raindrop function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do raindrop function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformRaindrop.__name__,
            controller=controller,
        )

    @staticmethod
    def create(  # noqa: C901, PLR0912, PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        max_size: int | None = None,
        raindrop_chance: float | None = None,
        step_size: int | None = None,
        max_raindrops: int | None = None,
        fade_amount: float | None = None,
    ) -> list[PixelTransform]:
        """Cause random "splashes" across the LED strand.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object
            max_size: max splash size
            raindrop_chance: chance of raindrop
            step_size: splash speed
            max_raindrops: number of raindrops
            fade_amount: amount to fade LED each refresh

        """
        transform = TransformRaindrop(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.size_max = random.randint(2, int(transform.controller.virtual_led_count // 8))
            transform.state.active_chance = random.randint(5, 100)
            transform.state.secondary_count_step = random.randint(2, 5)

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence

        if max_size is not None:
            transform.state.size_max = max_size
        if max_raindrops is None:
            max_raindrops = max(min(transform.state.pixel_sequence.led_count, 10), 2)
        if step_size is not None:
            transform.state.secondary_count_step = step_size
        else:
            transform.state.secondary_count_step = random.randint(1, 5)
        # if transform.state.step_size_max > 3:  # noqa: PLR2004
        # transform.state.active_chance /= 3.0
        if raindrop_chance is not None and raindrop_chance > 0 and raindrop_chance < 1:
            transform.state.active_chance = raindrop_chance * 1000
        else:
            transform.state.active_chance = random.randint(10, 250)

        # assign raindrop growth speed
        # transform.state.step_size = transform.state.step_size_max
        if fade_amount is None:
            transform.state.set_fade_amount(((MAX_INT8 / transform.state.size_max) / MAX_INT8) * 2)
        else:
            transform.state.set_fade_amount(fade_amount=fade_amount)
        # chance of raindrop

        # raindrops: list[PixelTransform] = []
        TransformFadeOff.create(
            controller=controller,
            fade_amount=transform.state.fade_amount,
        )
        _transform = None
        for _ in range(max_raindrops):
            if _transform is None:
                _transform = transform
            else:
                _transform = transform.copy()
            # randomize start index
            _transform.state.index = random.randint(0, transform.controller.virtual_led_count - 1)
            # max size
            _transform.state.secondary_count_max = random.randint(2, _transform.state.size_max)
            _transform.state.set_fade_amount(random.randint(MIN_FADE, MAX_FADE))
            # set raindrop to be inactive initially
            _transform.state.flags = RaindropStates.OFF
            _transform.calc_sequence_range()
            PixelTransform.ACTIVE_TRANSFORMS.append(_transform)
        # set first raindrop active
        PixelTransform.ACTIVE_TRANSFORMS[0].state.flags = RaindropStates.OFF
        # add fading
        return PixelTransform.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Cause random "splashes" across the LED strand."""
        # if raindrop is off
        if self.state.flags is RaindropStates.OFF:
            # randomly turn on
            if random.randint(0, 1000) < self.state.active_chance:
                # set state on
                self.state.flags = RaindropStates.SPLASH
                # set max width of this raindrop
                self.state.secondary_count_max = random.randint(
                    1,
                    max(self.state.size_max, 2),
                )
                self.state.delay_count_max = random.randint(
                    5,
                    15,
                )
                self.state.secondary_count_max = random.randint(
                    1,
                    5,
                )
                # set fade amount
                # self.state.set_fade_amount(((MAX_INT8 / self.state.step_count_max) / MAX_INT8) * 2)
                self.state.set_fade_amount(random.randint(MIN_FADE, MAX_FADE))
                self.state.color_scaler = (
                    self.state.secondary_count_max - self.state.secondary_counter
                ) / self.state.secondary_count_max
        # if raindrop is splashing
        elif self.state.flags is RaindropStates.SPLASH:
            # if splash is still growing
            if self.state.secondary_counter <= self.state.secondary_count_max:
                # lower valued side of "splash"
                index_lower_min = max(
                    self.state.index - self.state.secondary_counter * self.state.secondary_counter,
                    0,
                )
                index_lower_max = max(
                    self.state.index + 1 - self.state.secondary_counter * self.state.secondary_counter,
                    0,
                )
                # higher valued side of "splash"
                index_higher_min = min(
                    self.state.index + self.state.secondary_counter,
                    self.controller.virtual_led_count,
                )
                index_higher_max = min(
                    self.state.index + self.state.secondary_counter + self.state.secondary_count_step,
                    self.controller.virtual_led_count,
                )
                if (index_lower_max - index_lower_min) > 0:
                    index_range = list(range(index_lower_min, index_lower_max))
                    self.controller.virtual_led_buffer[index_lower_min:index_lower_max] = [
                        self.state.pixel_sequence[self.state.pixel_sequence.led_index].array,
                    ] * (index_lower_max - index_lower_min)
                    if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                        self.controller.virtual_led_buffer[index_range] = self.state.pixel_sequence[
                            self.state.pixel_sequence.led_index
                        ].array
                    else:
                        self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == index_range,
                            )
                        ] = self.state.pixel_sequence[self.state.pixel_sequence.led_index].array
                if (index_higher_max - index_higher_min) > 0:
                    index_range = list(range(index_higher_min, index_higher_max))
                    if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                        self.controller.virtual_led_buffer[index_range] = self.state.pixel_sequence[
                            self.state.pixel_sequence.led_index
                        ].array
                    else:
                        self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == index_range,
                            )
                        ] = self.state.pixel_sequence[self.state.pixel_sequence.led_index].array
                # scaled fading as splash grows
                self.state.pixel_sequence.pixel[:] = (
                    self.state.pixel_sequence[self.state.pixel_sequence.led_index].array * self.state.color_scaler
                )
                # increment splash growth counter
                self.advance_delay_counter()
                if self.state.delay_count_reset:
                    self.state.secondary_counter += 1
            # splash is done growing
            else:
                # randomize next splash start index
                self.state.index = random.randint(
                    0,
                    self.controller.virtual_led_count - 1,
                )
                # reset growth counter
                self.state.secondary_counter = 0
                # semi-randomize next color
                for _ in range(1, random.randint(2, 4)):
                    self.state.pixel_sequence.advance_index()
                # set state to off
                self.state.flags = RaindropStates.OFF
        self.calc_sequence_range()
        self.assign_pixel_to_array()
