"""Functions that modify the LED patterns in interesting ways."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from lightberries.transform import LightTransform

if TYPE_CHECKING:
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
        **kwargs: dict[str, Any],
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
        ----
            name: name of the function
            controller: Array controller instance
            state: the initial or previous state of the light string
            kwargs: extra args to the state object

        """
        super().__init__(name=name, controller=controller, state=state, kwargs=kwargs)
        self.ALL_ARRAY_TRANSFORMS[name] = self
