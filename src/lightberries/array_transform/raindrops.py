"""Do raindrop function things."""

from __future__ import annotations

import logging
import random
from enum import IntEnum
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transform.fade_off import TransformFadeOff
from lightberries.constants import SHAPE_2D
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_transform import PixelTransform
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class RaindropStates(IntEnum):
    """Raindrop function states."""

    OFF = 0
    SPLASH = 1


class TransformRaindrop(PixelTransform):
    """Do raindrop function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Do raindrop function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        super().__init__(
            name=TransformRaindrop.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        max_size: int | None = None,
        raindrop_chance: float | None = None,
        step_size: int | None = None,
        max_raindrops: int | None = None,
        fade_amount: float | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Cause random "splashes" across the LED strand.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object
            max_size: max splash size
            raindrop_chance: chance of raindrop
            step_size: splash speed
            max_raindrops: number of raindrops
            fade_amount: amount to fade LED each refresh

        """
        if color_sequence is not None:
            self.color_sequence = self.color_sequence
        if state is not None:
            self.state = state
        else:
            self.state.size_max = random.randint(2, int(self.controller.virtual_led_count // 8))
            self.state.active_chance = random.uniform(0.005, 0.1)
            self.state.step_size_max = random.randint(2, 5)

        if max_size is not None:
            self.state.size_max = max_size
        if max_raindrops is None:
            max_raindrops = max(min(self.color_sequence_count, 10), 2)
        if step_size is not None:
            self.state.step_size_max = step_size
        if self.state.step_size_max > 3:
            self.state.active_chance /= 3.0
        self.state.set_fade_amount(((255 / max_size) / 255) * 2)
        raindrops: list[TransformRaindrop] = []
        for _ in range(max_raindrops):
            raindrop = TransformRaindrop(controller=self.controller, state=self.state.copy())
            # randomize start index
            raindrop.state.index = random.randint(0, self.controller.virtual_led_count - 1)
            # assign raindrop growth speed
            raindrop.state.step = step_size
            # max raindrop "splash"
            raindrop.state.size_max = max_size
            # max size
            raindrop.state.step_count_max = random.randint(2, raindrop.state.size_max)
            # chance of raindrop
            raindrop.state.active_chance = raindrop_chance
            # assign color
            raindrop.state.color = self.color_sequence_next
            raindrop.color_sequence = self.color_sequence
            raindrop.state.fade_amount = fade_amount
            # set raindrop to be inactive initially
            raindrop.state.state = RaindropStates.OFF.value
            raindrops.append(raindrop)
        # set first raindrop active
        raindrops[0].state.state = RaindropStates.SPLASH.value
        # add fading
        fade = TransformFadeOff(controller=self.controller)
        fade.state.fade_amount = fade_amount
        raindrops.insert(0, fade)
        return raindrops

    def transform(self) -> None:
        """Cause random "splashes" across the LED strand."""
        # if raindrop is off
        if self.state.state == RaindropStates.OFF.value:
            # randomly turn on
            if random.randint(0, 1000) / 1000 < self.state.active_chance:
                # set state on
                self.state.state = RaindropStates.SPLASH.value
                # set max width of this raindrop
                self.state.step_count_max = random.randint(
                    1,
                    max(self.state.size_max, 2),
                )
                # set fade amount
                self.state.fade_amount = ((255 / self.state.step_count_max) / 255) * 2
                self.state.color_scaler = (
                    self.state.step_count_max - self.state.step_counter
                ) / self.state.step_count_max
        # if raindrop is splashing
        elif self.state.state == RaindropStates.SPLASH.value:
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
                    self.controller.virtual_led_buffer[index_lower_min:index_lower_max] = [self.state.color] * (
                        index_lower_max - index_lower_min
                    )
                    if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                        self.controller.virtual_led_buffer[index_range] = self.state.color
                    else:
                        self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == index_range,
                            )
                        ] = self.state.color
                if (index_higher_max - index_higher_min) > 0:
                    index_range = list(range(index_higher_min, index_higher_max))
                    if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
                        self.controller.virtual_led_buffer[index_range] = self.state.color
                    else:
                        self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == index_range,
                            )
                        ] = self.state.color
                # scaled fading as splash grows
                self.state.color[:] = self.state.color * self.state.color_scaler
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
                    self.state.color = self.color_sequence_next
                # set state to off
                self.state.state = RaindropStates.OFF.value
