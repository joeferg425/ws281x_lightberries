"""State tracking info for transform functions."""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

from lightberries.constants import MAX_INT8
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from numpy.typing import NDArray

    import lightberries.array_controller
    from lightberries.pixel_transform import PixelTransform

LOGGER = logging.getLogger("lightBerries")


class LEDFadeType(IntEnum):
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


class ThingMoves(IntEnum):
    """States for thing movement."""

    NOTHING = 0x0
    METEOR = 0x1
    LIGHT_SPEED = 0x2
    TURTLE = 0x4


class ThingSizes(IntEnum):
    """States for thing sizes."""

    NOTHING = 0x0
    GROW = 0x10
    SHRINK = 0x20


class ThingColors(IntEnum):
    """States for thing colors."""

    NOTHING = 0x0
    CYCLE = 0x100


class ChangeStates(IntEnum):
    """States for random change."""

    FADING_ON = 0
    ON = 1
    FADING_OFF = 2
    WAIT = 3


@dataclass
class TransformState:
    """State tracking info for transform functions."""

    controller: lightberries.array_controller.ArrayController

    color_sequence: PixelSequence = field(default_factory=PixelSequence)
    color_cycle: bool = False
    color_scaler: float = 0.5

    current_state: int = 0
    state_max: int = 0
    direction: int = 1

    index: int = 0
    index_next: int = 0
    index_previous: int = 0
    index_min: int = 0
    index_max: int = 0
    index_updated: bool = False
    index_range: NDArray[np.int32] = field(default_factory=lambda: np.zeros([3, 0], dtype=np.int32))

    fade_type: LEDFadeType = LEDFadeType.FADE_OFF
    fade_amount: int = 128
    fade_amount_float: float = 0.5

    delay_counter: int = 0
    delay_count_max: int = 0
    delay_count_limit: int = 0

    step: int = 1
    step_last: int = 0
    step_counter: int = 0
    step_count_max: int = 0
    step_size_max: int = 1

    collision: bool = False
    collision_enabled: bool = False
    collision_intersection: NDArray[np.int32] = field(default_factory=lambda: np.zeros([3, 0], dtype=np.int32))
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
        self.color_sequence = PixelSequence.default_color_sequence_by_month()

        self.index_next: int = self.index
        self.index_previous: int = (self.index - 1) % self.controller.real_led_count
        self.index_min: int = self.index
        self.index_max: int = self.index

    def set_fade_amount(self, fade_amount: float) -> None:
        """Make sure fade amount is valid.

        Args:
        ----
            fade_amount: a float in range [0.0, 1.0] or an int in range [0, 255]

        """
        if fade_amount > 0 and fade_amount < 1:
            self.fade_amount = int(fade_amount * MAX_INT8)
        elif fade_amount > 0 and fade_amount <= MAX_INT8:
            self.fade_amount = int(fade_amount / MAX_INT8)
        if fade_amount < 0:
            self.fade_amount = int(0.1 * MAX_INT8)
        elif fade_amount > 1:
            self.fade_amount = int(0.9 * MAX_INT8)
        self.fade_amount_float = self.fade_amount / MAX_INT8

    def copy(self) -> TransformState:
        """Get a copy of this object.

        Returns
        -------
            a copy of this object

        """
        t = TransformState(**self.__dict__)
        t.color_sequence = self.color_sequence.copy()
        return t

    def fade_color(
        self,
    ) -> NDArray[np.int32]:
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
        return self.color_sequence.pixel.fade(
            color_next=self.color_sequence.pixel_next,
            fade_amount=self.fade_amount,
        )
