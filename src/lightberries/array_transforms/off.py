from typing import Any

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionOff(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray[Any, np.signedinteger[np._32Bit]] = None,
    ) -> None:
        """Turn all Pixels OFF.

        Args:
        ----
            off: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        super().__init__(
            name=ArrayFunctionOff.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def _transform(self) -> None:
        try:
            self.controller.virtualLEDBuffer[:] *= 0
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
