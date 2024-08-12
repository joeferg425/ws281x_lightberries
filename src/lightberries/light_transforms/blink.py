"""Randomly set all lights in the string to the same color without changing the virtual LED buffer."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.transform import LightTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState


class ArrayFunctionBlink(LightTransform):
    """Randomly set all lights in the string to the same color without changing the virtual LED buffer."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Randomly set all lights in the string to the same color without changing the virtual LED buffer.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            kwargs: extra args to the state object

        """
        super().__init__(
            name=ArrayFunctionBlink.__class__.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )

    def transform(self) -> None:
        """Randomly set all lights in the string to the same color without changing the virtual LED buffer.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        try:
            if random.random() > self.state.random:
                color = self.color_sequence_next
                for index in range(self.controller.real_led_count):
                    self.controller.overlay_dictionary[index] = color
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
