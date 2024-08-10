import random

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionBlink(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Randomly sets some lights to 'twinkleColor' without changing the virtual LED buffer.

        Args:
            blink: object for tracking blinking

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        super().__init__(
            name=ArrayFunctionBlink.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        try:
            if random.random() > self.state.random:
                color = self.color_sequence_next
                for index in range(self.controller.realLEDCount):
                    self.controller.overlayDictionary[index] = color
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
