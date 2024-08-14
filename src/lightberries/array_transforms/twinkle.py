import logging
import random

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError

LOGGER = logging.getLogger("lightBerries")


class ArrayFunctionTwinkle(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do temporary twinkle modifications.

        Args:
        ----
            twinkle: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        super().__init__(
            name=ArrayFunctionTwinkle.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def _transform(self):
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
