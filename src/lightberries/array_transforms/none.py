"""Basic function. It does nothing."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lightberries.array_transforms.base import ArrayTransform

if TYPE_CHECKING:
    import numpy as np

    import lightberries.array_controller
    from lightberries.state import TransformState
    from lightberries.transform import LightTransform

LOGGER = logging.getLogger("lightBerries")


class TransformNone(ArrayTransform):
    """Basic function. It does nothing."""

    def __init__(self, controller: lightberries.array_controller.ArrayController) -> None:
        """Do nothing.

        Args:
        ----
            controller: array controller instance

        """
        super().__init__(
            name=TransformNone.__class__.__name__,
            controller=controller,
        )

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
        # create an object to put in the light data list so we don't just abort the run
        super().setup(
            color_sequence=color_sequence,
            state=state,
        )
        return [self]

    def transform(self) -> None:
        """Do nothing."""
