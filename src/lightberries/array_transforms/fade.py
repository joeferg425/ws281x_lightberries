import logging
from math import ceil
from typing import Any

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError

LOGGER = logging.getLogger("lightBerries")


class ArrayFunctionFade(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray[Any, np.signedinteger[np._32Bit]] = None,
    ) -> None:
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
        super().__init__(
            name="Fade",
            controller=controller,
            color_sequence=color_sequence,
        )

    def _transform(self):
        try:
            self.state.delay_counter += 1
            if self.state.delay_counter >= self.state.delay_count_max:
                _fadeAmount = ceil(self.state.fade_amount * 256)
                if _fadeAmount < 0:
                    _fadeAmount = 1
                elif _fadeAmount > 255:
                    _fadeAmount = 255
                for i in range(self.controller.real_led_count):
                    for rgbIndex in range(len(self.state.color)):
                        if self.controller.virtual_led_buffer[i, rgbIndex] != self.state.color[rgbIndex]:
                            if (
                                self.controller.virtual_led_buffer[i, rgbIndex] - _fadeAmount
                                > self.state.color[rgbIndex]
                            ):
                                self.controller.virtual_led_buffer[i, rgbIndex] -= _fadeAmount
                            elif (
                                self.controller.virtual_led_buffer[i, rgbIndex] + _fadeAmount
                                < self.state.color[rgbIndex]
                            ):
                                self.controller.virtual_led_buffer[i, rgbIndex] += _fadeAmount
                            else:
                                self.controller.virtual_led_buffer[i, rgbIndex] = self.state.color[rgbIndex]
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
