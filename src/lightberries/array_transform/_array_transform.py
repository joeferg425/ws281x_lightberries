"""Functions that modify the LED patterns in interesting ways."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:

    import lightberries.array_controller


LOGGER = logging.getLogger("lightBerries")


class ArrayTransform(PixelTransform):
    """Modify LED patterns in interesting ways."""

    ALL_ARRAY_TRANSFORMS: ClassVar[dict[str, type[ArrayTransform]]] = {}

    def __init_subclass__(
        cls,
        **kwargs: dict[str, Any],
    ) -> None:
        super().__init_subclass__(kwargs=kwargs)
        cls.ALL_ARRAY_TRANSFORMS[cls.__name__.replace("Transform", "")] = cls

    def __init__(
        self,
        name: str,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
        ----
            name: name of the function
            controller: Array controller instance
            pixel_sequence: a sequence of pixels
            state: initial state. Defaults to None.

        """
        super().__init__(
            name=name,
            controller=controller,
        )
