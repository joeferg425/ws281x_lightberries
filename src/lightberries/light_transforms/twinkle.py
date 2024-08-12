"""Do temporary twinkle modifications."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState


class ArrayFunctionTwinkle(ArrayTransform):
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
            name=ArrayFunctionTwinkle.__class__.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )

    def transform(self) -> None:
        """Do temporary twinkle modifications.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        try:
            for index in range(self.controller.real_led_count):
                if random.random() > self.state.random:
                    self.controller.overlay_dictionary[index] = self.color_sequence_next
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
