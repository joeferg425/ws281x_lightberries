"""Do raindrop function things."""

from __future__ import annotations

import random
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

from lightberries.constants import MAX_INT8, SHAPE_2D
from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay.fade_off import TransformFadeOff

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState



class RaindropStates(IntEnum):
    """Raindrop function states."""

    OFF = 0
    SPLASH = 1


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
    def setup(  # noqa: C901, PLR0912, PLR0913
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
            transform.state.active_chance = random.uniform(0.005, 0.1)
            transform.state.step_size_max = random.randint(2, 5)

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence

        if max_size is not None:
            transform.state.size_max = max_size
        if max_raindrops is None:
            max_raindrops = max(min(transform.state.pixel_sequence.led_count, 10), 2)
        if step_size is not None:
            transform.state.step_size_max = step_size
        if transform.state.step_size_max > 3:  # noqa: PLR2004
            transform.state.active_chance /= 3.0
        if raindrop_chance is None:
            raindrop_chance = random.uniform(0.01, 0.25)

        # assign raindrop growth speed
        transform.state.step = transform.state.step_size_max
        if fade_amount is None:
            transform.state.set_fade_amount(((MAX_INT8 / transform.state.size_max) / MAX_INT8) * 2)
        else:
            transform.state.set_fade_amount(fade_amount=fade_amount)
        # chance of raindrop
        transform.state.active_chance = raindrop_chance

        raindrops: list[PixelTransform] = []
        TransformFadeOff.setup(
            controller=controller,
            fade_amount=transform.state.fade_amount,
        )
        raindrop = None
        for _ in range(max_raindrops):
            if raindrop is None:
                raindrop = transform
            else:
                raindrop = transform.copy()
            # randomize start index
            raindrop.state.index = random.randint(0, transform.controller.virtual_led_count - 1)
            # max size
            raindrop.state.step_count_max = random.randint(2, raindrop.state.size_max)
            # set raindrop to be inactive initially
            raindrop.state.current_state = RaindropStates.OFF
            raindrops.append(raindrop)
        # set first raindrop active
        raindrops[0].state.current_state = RaindropStates.SPLASH
        # add fading
        return raindrops

    def transform(self) -> None:
        """Cause random "splashes" across the LED strand."""
        # if raindrop is off
        if self.state.current_state is RaindropStates.OFF:
            # randomly turn on
            if random.randint(0, 1000) / 1000 < self.state.active_chance:
                # set state on
                self.state.current_state = RaindropStates.SPLASH
                # set max width of this raindrop
                self.state.step_count_max = random.randint(
                    1,
                    max(self.state.size_max, 2),
                )
                # set fade amount
                self.state.set_fade_amount(((MAX_INT8 / self.state.step_count_max) / MAX_INT8) * 2)
                self.state.color_scaler = (
                    self.state.step_count_max - self.state.step_counter
                ) / self.state.step_count_max
        # if raindrop is splashing
        elif self.state.current_state is RaindropStates.SPLASH:
            # if splash is still growing
            if self.state.step_counter <= self.state.step_count_max:
                # lower valued side of "splash"
                index_lower_min = max(
                    self.state.index - self.state.step * self.state.step_counter,
                    0,
                )
                index_lower_max = max(
                    self.state.index + 1 - self.state.step * self.state.step_counter,
                    0,
                )
                # higher valued side of "splash"
                index_higher_min = min(
                    self.state.index + self.state.step_counter,
                    self.controller.virtual_led_count,
                )
                index_higher_max = min(
                    self.state.index + self.state.step_counter + self.state.step,
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
                self.state.step_counter += self.state.step
            # splash is done growing
            else:
                # randomize next splash start index
                self.state.index = random.randint(
                    0,
                    self.controller.virtual_led_count - 1,
                )
                # reset growth counter
                self.state.step_counter = 0
                # semi-randomize next color
                for _ in range(1, random.randint(2, 4)):
                    self.state.pixel_sequence.advance_index()
                # set state to off
                self.state.current_state = RaindropStates.OFF
