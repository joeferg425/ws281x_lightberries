import random

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionTwinkle(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do temporary twinkle modifications.

        Args:
            twinkle: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        super().__init__(
            name=ArrayFunctionTwinkle.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        try:
            for index in range(self.controller.realLEDCount):
                if random.random() > self.state.random:
                    self.controller.overlayDictionary[index] = self.color_sequence_next
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
