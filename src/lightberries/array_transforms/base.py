"""Functions that modify the LED patterns in interesting ways."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from lightberries.light_sequences.base import ArraySequence
from lightberries.transform import LightTransform

if TYPE_CHECKING:
    import numpy as np

    import lightberries.array_controller
    from lightberries.state import TransformState


LOGGER = logging.getLogger("lightBerries")


class ArrayTransform(LightTransform):
    """Modify LED patterns in interesting ways."""

    ALL_ARRAY_TRANSFORMS: ClassVar[dict[str, ArrayTransform]] = {}

    def __init__(
        self,
        name: str,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
        ----
            name: name of the function
            controller: Array controller instance
            state: initial state. Defaults to None.

        """
        super().__init__(
            name=name,
            controller=controller,
            state=state,
        )
        self.ALL_ARRAY_TRANSFORMS[name] = self

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
    ) -> list[LightTransform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.

        Returns:
        -------
            list of transforms

        """
        if state is not None:
            self.state = state
        self.state.color_sequence = ArraySequence.default_color_sequence_by_month()
        if color_sequence is not None:
            self.state.color_sequence = color_sequence
        return []
