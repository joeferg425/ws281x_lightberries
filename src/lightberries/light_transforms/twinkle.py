"""Do temporary twinkle modifications."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.state import TransformState
from lightberries.transform import Transform

if TYPE_CHECKING:
    import numpy as np

    import lightberries.array_controller
    from lightberries.state import TransformState
    from lightberries.transform import Transform


class TransformTwinkle(Transform):
    """Do temporary twinkle modifications."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Do temporary twinkle modifications.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            kwargs: extra args to the state object

        """
        super().__init__(
            name=TransformTwinkle.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
    ) -> list[Transform]:
        """Create one or more transform instances.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            one or more transform instances

        """

    def setup(
        self,
        twinkle_chance: float | None = None,
        color_sequence: np.ndarray[(3, Any), np.int32] | None = None,
    ) -> None:
        """Randomly sets some lights to 'twinkleColor' temporarily.

        Args:
        ----
            twinkleChance: chance of a twinkle
            colorSequence: the list of colors to be used when briefly flashing an LED

        """
        if twinkle_chance is not None:
            twinkle_chance = random.uniform(0.991, 0.995)
        if color_sequence is not None:
            color_sequence = self.color_sequence.copy()
        self.state.random = twinkle_chance
        return [self]

    def transform(self) -> None:
        """Do temporary twinkle modifications.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        for index in range(self.controller.real_led_count):
            if random.random() > self.state.random:
                self.controller.overlay_dictionary[index] = self.color_sequence_next
