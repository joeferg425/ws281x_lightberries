"""Turn all Pixels OFF."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from lightberries.transform import Transform

if TYPE_CHECKING:
    import numpy as np

    import lightberries.array_controller
    from lightberries.state import TransformState
    from lightberries.transform import Transform

LOGGER = logging.getLogger("lightBerries")


class TransformOff(Transform):
    """Turn all Pixels OFF."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
    ) -> None:
        """Turn all Pixels OFF.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformOff.__name__,
            controller=controller,
            state=state,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[Transform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        super().setup(
            color_sequence=color_sequence,
            state=state,
        )
        return [self]

    def transform(self) -> None:
        """Turn all Pixels OFF."""
        self.controller.virtual_led_buffer[:] *= 0
