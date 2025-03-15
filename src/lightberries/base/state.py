"""State tracking info for transform functions."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import IntFlag
from typing import TYPE_CHECKING

import numpy as np

from lightberries.base.constants import MAX_INT8

if TYPE_CHECKING:
    from numpy.typing import NDArray

    import lightberries.array_controller
    from lightberries.base.pixel import Pixel
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.pixel_transform import PixelTransform


class LEDFadeType(IntFlag):
    """Enumeration of types of LED fade for use in functions."""

    FADE_OFF = 0
    INSTANT_OFF = 1
    DONT = 2

    @staticmethod
    def get_random() -> LEDFadeType:
        """Get a random one.

        Returns
        -------
            a random one

        """
        fade_types: list[LEDFadeType] = list(LEDFadeType)
        return fade_types[random.randint(0, len(fade_types) - 1)]


class ChangeStates(IntFlag):
    """States for random change."""

    FADING_ON = 0
    ON = 1
    FADING_OFF = 2
    WAIT = 3


@dataclass
class TransformState:
    """State tracking info for transform functions."""

    controller: lightberries.array_controller.ArrayController

    pixel_sequence: PixelSequence
    color_cycle: bool = False
    color_cycle_randomize: bool = False
    color_scaler: float = 0.5

    flags: IntFlag = 0  # type: ignore  # noqa: PGH003
    state_max: int = 0
    direction: int = 1
    direction_previous: int = 1
    ran_once: bool = False

    index: int = 0
    index_no_modulo: int = 0
    index_next: int = 0
    index_next_no_modulo: int = 0
    index_previous: int = 0
    index_updated: bool = False
    index_range: NDArray[np.int32] = field(default_factory=lambda: np.zeros([0], dtype=np.int32))
    index_bounce: bool = False

    fade_type: LEDFadeType = LEDFadeType.FADE_OFF
    fade_amount: int = 128
    fade_amount_float: float = 0.5

    delay_counter: int = 0
    delay_count_max: int = 0
    delay_count_reset: bool = False
    delay_count_max_setting: int = 0

    step_size: int = 1
    step_size_max_setting: int = 1

    step_counter: int = 0
    step_count_previous: int = 0
    step_count_max: int = 0
    step_count_reset: bool = False

    secondary_counter: int = 0
    secondary_count_step: int = 0
    secondary_count_max: int = 1
    secondary_count_reset_value: int = 1

    collision: bool = False
    collision_enabled: bool = False
    collision_intersection: int = 0
    collision_with: PixelTransform | None = None
    collision_randomizer: bool = False
    collision_private: bool = False

    size: int = 1
    size_min: int = 1
    size_max: int = 1

    active: bool = True
    active_chance: float = 100.0

    explode: bool = False
    dying: bool = False
    waking: bool = False
    duration: int = 0
    random: float = 0.5
    flip_length: int = 0

    first: bool = True

    period_short: int = 10

    def __post_init__(self) -> None:
        self.re_init()

    def re_init(self) -> None:
        """Do some initialization for the state."""
        self.index_no_modulo = self.index
        self.index_next_no_modulo = self.index + (self.direction * self.step_size)
        if self.index_next_no_modulo >= self.controller.virtual_led_count:
            if self.index_bounce is True:
                self.direction *= -1
                self.index_next = self.index_next_no_modulo % (self.controller.virtual_led_count - 1)
            else:
                self.index_next = self.index_next_no_modulo % self.controller.virtual_led_count
        elif self.index_next_no_modulo <= 0:
            self.index_next = self.index_next_no_modulo % self.controller.virtual_led_count
            if self.index_bounce is True:
                self.direction *= -1
                self.index_next += self.controller.virtual_led_count - 1
        else:
            self.index_next = self.index_next_no_modulo

        self.index_next = self.index + self.step_size
        self.index_previous: int = (self.index - self.step_size) % self.controller.real_led_count

    def set_fade_amount(self, fade_amount: float) -> None:
        """Make sure fade amount is valid.

        Args:
        ----
            fade_amount: a float in range [0.0, 1.0] or an int in range [0, 255]

        """
        if fade_amount > 0 and fade_amount < 1:
            self.fade_amount = int(fade_amount * MAX_INT8)
        elif fade_amount > 0 and fade_amount <= MAX_INT8:
            self.fade_amount = int(fade_amount)
        if self.fade_amount < 0:
            self.fade_amount = int(0.1 * MAX_INT8)
        elif self.fade_amount > MAX_INT8:
            self.fade_amount = int(0.9 * MAX_INT8)
        self.fade_amount_float = self.fade_amount / MAX_INT8

    def copy(self) -> TransformState:
        """Get a copy of this object.

        Returns
        -------
            a copy of this object

        """
        t = TransformState(**self.__dict__)
        t.pixel_sequence = self.pixel_sequence.copy()
        return t

    def fade_color(
        self,
    ) -> Pixel:
        """Fade an LED's color by the given amount and return the new RGB value.

        Args:
        ----
            color: current color
            colorNext: desired color
            fadeCount: amount to adjust each RGB value by

        Returns:
        -------
            new RGB value

        """
        # copy it to make sure we don't change the original by reference
        return self.pixel_sequence.pixel.fade(
            color_next=self.pixel_sequence.pixel_next,
            fade_amount=self.fade_amount,
        )
