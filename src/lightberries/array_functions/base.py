"""This file defines functions that modify the LED patterns in interesting ways."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import  dataclass, field
from enum import IntEnum
from math import ceil
from typing import Any, Optional

import numpy as np

import lightberries.array_controller  # noqa : used in typing
from lightberries.array_patterns import ArrayPattern, ConvertPixelArrayToNumpyArray
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.pixel import LEDOrder, Pixel, PixelColors

# pylint: disable=no-member

LOGGER = logging.getLogger("lightBerries")


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
class FunctionState:
    controller: lightberries.array_controller.ArrayController
    state: int = 0
    state_max: int = 0
    direction: int = 1

    index: int = 0
    index_next: int = 0
    index_previous: int = 0
    index_min: int = 0
    index_max: int = 0
    index_updated: bool = False
    index_range: Optional[np.ndarray[(3, Any), np.int32]] = field(default_factory=list)

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
    collision_intersection: np.ndarray[(Any,), np.int32] =  field(default_factory=list)
    collision_with: Optional[ArrayFunction] = None
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
        self.index_next: int = self.index
        self.index_previous: int = (self.index - 1) % self.controller.realLEDCount
        self.index_min: int = self.index
        self.index_max: int = self.index

        self.color: np.ndarray[(3,), np.int32] = self.controller.colorSequence[0]


class ArrayFunction(ABC):
    """This class defines everything necessary to modify LED patterns in interesting ways."""

    ALL_FUNCTIONS: dict[str, ArrayFunction] = {}

    def __init__(
        self,
        name: str,
        controller: lightberries.array_controller.ArrayController,
        # funcPointer: Callable,
        color_sequence: np.ndarray[(3, Any), np.int32] = None,
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
            funcPointer: a function pointer that updates LEDs in the LightArrayController object.
            colorSequence: a sequence of RGB values.
        """
        self.controller = controller
        self.ALL_FUNCTIONS[name] = self

        self._color_sequence: np.ndarray[(3, Any), np.int32] = (
            ConvertPixelArrayToNumpyArray([])
        )
        self._color_sequence_count: int = 0
        self._color_sequence_index: int = 0

        if color_sequence is None or len(color_sequence) == 0:
            self._color_sequence = ArrayPattern.DefaultColorSequenceByMonth()
        else:
            self._color_sequence = color_sequence
        self._color_sequence_count = len(self._color_sequence)

        self._name: str = name
        self.state = FunctionState(controller=self.controller)
        # self.runFunction: Callable = funcPointer

    def __str__(
        self,
    ) -> str:
        """String representation of this object.

        Returns:
            String representation of this object
        """
        return f'[{self._index}]: "{self._name}" {Pixel(self._color, LEDOrder.RGB)}'

    def __repr__(
        self,
    ) -> str:
        """Return a string representation of this class(not de-serializable).

        Returns:
            string representation of this class(not de-serializable)
        """
        return f"<{self.__class__.__name__}> {str(self)}"

    @abstractmethod
    def run(self): ...

    @property
    def color_sequence(
        self,
    ) -> np.ndarray[(3, Any), np.int32]:
        """Return the color sequence.

        Returns:
            the color sequence
        """
        return self._color_sequence

    @color_sequence.setter
    def color_sequence(
        self,
        color_sequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Sets the color sequence.

        Args:
            colorSequence: desired color sequence
        """
        self._color_sequence = color_sequence
        self._color_sequence_count = len(self._color_sequence)
        self._color_sequence_index = 0

    @property
    def color_sequence_count(
        self,
    ) -> int:
        """Get the color sequence count.

        Returns:
            the color sequence count
        """
        return self._color_sequence_count

    @color_sequence_count.setter
    def color_sequence_count(
        self,
        colorSequenceCount: int,
    ) -> None:
        """Setter for color sequence count.

        Args:
            colorSequenceCount: the number of colors in the sequence
        """
        self._color_sequence_count = colorSequenceCount

    @property
    def color_sequence_index(
        self,
    ) -> int:
        """Color sequence index.

        Returns:
            the current color sequence index
        """
        return self._color_sequence_index

    @color_sequence_index.setter
    def color_sequence_index(
        self,
        colorSequenceIndex: int,
    ) -> None:
        """Color sequence index.

        Args:
            colorSequenceIndex: the current index being used for the color sequence
        """
        self._color_sequence_index = colorSequenceIndex

    @property
    def color_sequence_next(
        self,
    ) -> np.ndarray[(3,), np.int32]:
        """Get the next color in the sequence.

        Returns:
            the next color in the sequence
        """
        self._color_sequence_index += 1
        if self._color_sequence_index >= self._color_sequence_count:
            self._color_sequence_index = 0
        temp = self._color_sequence[self._color_sequence_index]
        return temp

    def do_fade(
        self,
    ) -> None:
        """Fade pixel colors.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            self.state.delay_counter += 1
            if self.state.delay_counter >= self.state.delay_count_max:
                _fadeAmount = ceil(self.state.fade_amount * 256)
                if _fadeAmount < 0:
                    _fadeAmount = 1
                elif _fadeAmount > 255:
                    _fadeAmount = 255
                for rgb_index in range(len(self.state.color)):
                    if self.state.color[rgb_index] != self.state.color_next[rgb_index]:
                        if (
                            self.state.color[rgb_index] - _fadeAmount
                            >= self.state.color_next[rgb_index]
                        ):
                            self.state.color[rgb_index] -= _fadeAmount
                        elif (
                            self.state.color[rgb_index] + _fadeAmount
                            <= self.state.color_next[rgb_index]
                        ):
                            self.state.color[rgb_index] += _fadeAmount
                        else:
                            self.state.color[rgb_index] = self.state.color_next[
                                rgb_index
                            ]
            if self.state.delay_counter >= self.state.delay_count_max:
                self.state.delay_counter = 0
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex

    def update_array_index(
        self,
    ) -> None:
        """Update the object index."""
        self.state.index_previous = self.state.index
        self.calc_range()
        self.state.index_previous = self.state.index
        self.state.index = int(self.state.index_range[-1])
        self.state.index_updated = True

    def calc_range(
        self,
    ) -> np.ndarray[(Any,), np.int32]:
        """Calculate index range.

        Args:
            indexFrom: from index
            indexTo: to index

        Returns:
            array of indices
        """
        new_index_no_modulo = self.state.index + (
            self.state.step * self.state.direction
        )
        self.state.index_range = np.array(
            list(
                range(
                    self.state.index_previous + self.state.direction,
                    new_index_no_modulo + self.state.direction,
                    self.state.direction,
                )
            )
        )
        modulo = np.where(self.state.index_range >= (self.controller.virtualLEDCount))[
            0
        ]
        while len(modulo):
            self.state.index_range[modulo] -= self.controller.virtualLEDCount
            modulo = np.where(
                self.state.index_range >= (self.controller.virtualLEDCount)
            )[0]
        modulo = np.where(self.state.index_range < 0)[0]
        while len(modulo):
            self.state.index_range[modulo] += self.controller.virtualLEDCount
            modulo = np.where(self.state.index_range < 0)[0]
        return self.state.index_range
