"""State tracking info for transform functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_patterns.array_patterns import ArrayPattern
from lightberries.pixel import PixelColors

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.transform import LightTransform


class LEDFadeType(IntEnum):
    """Enumeration of types of LED fade for use in functions."""

    FADE_OFF = 0
    INSTANT_OFF = 1
    DONT = 2


class SpriteState(IntEnum):
    """Sprite function enum."""

    OFF = 0
    FADING_ON = 1
    ON = 2
    FADING_OFF = 3


class RaindropStates(IntEnum):
    """Raindrop function states."""

    OFF = 0
    SPLASH = 1


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

    color_sequence: np.ndarray[(3, Any), np.int32] = field(default_factory=np.array)
    color_sequence_count: int = 0
    color_sequence_index: int = 0

    state: int = 0
    state_max: int = 0
    direction: int = 1

    index: int = 0
    index_next: int = 0
    index_previous: int = 0
    index_min: int = 0
    index_max: int = 0
    index_updated: bool = False
    index_range: np.ndarray[(3, Any), np.int32] = field(default_factory=np.array([], dtype=np.int32))

    color: np.ndarray[(3,), np.int32] = PixelColors.OFF
    color_begin: np.ndarray[(3,), np.int32] = PixelColors.OFF.array
    color_next: np.ndarray[(3,), np.int32] = PixelColors.OFF.array
    color_goal: np.ndarray[(3,), np.int32] = PixelColors.OFF.array
    color_scaler: float = 0
    color_cycle: bool = False

    fade_type: LEDFadeType = LEDFadeType.FADE_OFF
    fade_amount: float = 0.5
    fade_steps: int = 0

    delay_counter: int = 0
    delay_count_max: int = 0

    step: int = 1
    step_last: int = 0
    step_counter: int = 0
    step_count_max: int = 0
    step_size_max: int = 1

    collision: bool = False
    collision_enabled: bool = False
    collision_intersection: np.ndarray[(Any,), np.int32] = field(default_factory=np.array)
    collision_with: LightTransform | None = None
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
        self.color_sequence = ArrayPattern.default_color_sequence_by_month()
        self.color_sequence_count = len(self.color_sequence)

        self.index_next: int = self.index
        self.index_previous: int = (self.index - 1) % self.controller.real_led_count
        self.index_min: int = self.index
        self.index_max: int = self.index

        self.color: np.ndarray[(3,), np.int32] = self.controller.color_sequence[0]
