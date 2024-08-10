from typing import Any

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionFadeOff(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray[Any, np.signedinteger[np._32Bit]] = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionFadeOff.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        """Fade all Pixels toward OFF.

        Args:
            fade: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            self.controller.virtualLEDBuffer[:] = self.controller.virtualLEDBuffer * (
                1 - self.state.fade_amount
            )
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
