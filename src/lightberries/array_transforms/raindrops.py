"""Do raindrop function things."""

from __future__ import annotations

import logging
import random
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

from lightberries.array_transforms.base import ArrayTransform
from lightberries.array_transforms.fade_off import TransformFadeOff

if TYPE_CHECKING:
    import lightberries.array_controller

LOGGER = logging.getLogger("lightBerries")


class RaindropStates(IntEnum):
    """Raindrop function states."""

    OFF = 0
    SPLASH = 1


class TransformRaindrop(ArrayTransform):
    """Do raindrop function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do raindrop function things.

        Args:
        ----
            raindrop: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        super().__init__(
            name=TransformRaindrop.state.__name__,
            controller=controller,
        )

    def setup(
        self,
        max_size: int | None = None,
        raindrop_chance: float | None = None,
        step_size: int | None = None,
        max_raindrops: int | None = None,
        fade_amount: float | None = None,
    ):
        """Cause random "splashes" across the LED strand.

        Args:
        ----
            maxSize: max splash size
            raindropChance: chance of raindrop
            stepSize: splash speed
            maxRaindrops: number of raindrops
            fadeAmount: amount to fade LED each refresh

        """
        if max_size is None:
            max_size = random.randint(2, int(self.virtual_led_count // 8))
        if raindrop_chance is None:
            raindrop_chance: float = random.uniform(0.005, 0.1)
        if step_size is None:
            step_size = random.randint(2, 5)
        # fade_amount: float = random.uniform(0.25, 0.65)
        if fade_amount is None:
            fade_amount = ((255 / max_size) / 255) * 2
        if max_raindrops is None:
            max_raindrops = max(min(self.color_sequence_count, 10), 2)
        if step_size > 3:
            raindrop_chance /= 3.0
        # make sure fade amount is valid
        if fade_amount > 0 and fade_amount < 1:
            # do nothing
            pass
        elif fade_amount > 0 and fade_amount < 256:
            fade_amount /= 255
        if fade_amount < 0 or fade_amount > 1:
            fade_amount = 0.1
        raindrops: list[TransformRaindrop] = []
        for _ in range(max_raindrops):
            raindrop = TransformRaindrop(controller=self.controller)
            # randomize start index
            raindrop.state.index = random.randint(0, self.virtual_led_count - 1)
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
            raindrop.state = RaindropStates.OFF.value
            raindrops.append(raindrop)
        # set first raindrop active
        raindrops[0].state.state = RaindropStates.SPLASH.value
        # add fading
        fade = TransformFadeOff(controller=self.controller)
        fade.state.fade_amount = fade_amount
        raindrops.insert(0, fade)
        return raindrops

    def transform(self):
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
                indexLowerMin = max(
                    self.state.index - self.state.step * self.state.step_counter,
                    0,
                )
                indexLowerMax = max(
                    self.state.index + 1 - self.state.step * self.state.step_counter,
                    0,
                )
                # higher valued side of "splash"
                indexHigherMin = min(
                    self.state.index + self.state.step_counter,
                    self.controller.virtual_led_count,
                )
                indexHigherMax = min(
                    self.state.index + self.state.step_counter + self.state.step,
                    self.controller.virtual_led_count,
                )
                if (indexLowerMax - indexLowerMin) > 0:
                    indexRange = list(range(indexLowerMin, indexLowerMax))
                    self.controller.virtual_led_buffer[indexLowerMin:indexLowerMax] = [self.state.color] * (
                        indexLowerMax - indexLowerMin
                    )
                    if len(self.controller.virtual_led_buffer.shape) == 2:
                        self.controller.virtual_led_buffer[indexRange] = self.state.color
                    else:
                        self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == indexRange,
                            )
                        ] = self.state.color
                if (indexHigherMax - indexHigherMin) > 0:
                    indexRange = list(range(indexHigherMin, indexHigherMax))
                    # self.controller.virtualLEDBuffer[indexHigherMin:indexHigherMax]
                    # = [raindrop.color] * (
                    # indexHigherMax - indexHigherMin
                    # )
                    if len(self.controller.virtual_led_buffer.shape) == 2:
                        self.controller.virtual_led_buffer[indexRange] = self.state.color
                    else:
                        self.controller.virtual_led_buffer[
                            np.where(
                                self.controller.virtual_led_index_buffer == indexRange,
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
        # increment delay
        # raindrop.delayCounter += 1
