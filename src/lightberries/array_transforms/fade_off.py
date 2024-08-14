from __future__ import annotations

import logging
from typing import Any

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class ArrayTransformFadeOff(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        super().__init__(
            name=ArrayTransformFadeOff.__class__.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )

    def _transform(self):
        """Fade all Pixels toward OFF.

        Args:
        ----
            fade: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        try:
            self.controller.virtual_led_buffer[:] = self.controller.virtual_led_buffer * (1 - self.state.fade_amount)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
