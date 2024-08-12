from __future__ import annotations

from typing import Any

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.state import TransformState


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
            self.controller.virtualLEDBuffer[:] = self.controller.virtualLEDBuffer * (1 - self.state.fade_amount)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
