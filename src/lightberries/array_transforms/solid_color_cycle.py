"""Cycle the entire light string's color at once."""

import logging

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError

LOGGER = logging.getLogger("lightBerries")


class ArrayFunctionSolidColorCycle(ArrayTransform):
    """Cycle the entire light string's color at once."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Cycle the entire light string's color at once.

        Args:
        ----
            controller: _description_
            color_sequence: _description_. Defaults to None.

        """
        super().__init__(
            name=ArrayFunctionSolidColorCycle.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionSolidColorCycle.__name__,
        )
        try:
            _delayCount: int = random.randint(50, 100)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            cycle: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionSolidColorCycle,
                self.color_sequence,
            )
            # set refresh counter
            cycle._delay_counter = _delayCount
            # set refresh limit (after which this function will execute)
            cycle._delay_count_max = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(cycle)
            # clear LEDs, assign first color in sequence to all LEDs
            self.virtualLEDBuffer *= 0
            self.virtualLEDBuffer += self.color_sequence[0, :]
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def _transform(self):
        """Set all pixels to the next color.

        Args:
        ----
            cycle: tracking object

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
        try:
            # wait for delay count before changing LEDs
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # remove any current color
                self.controller.virtual_led_buffer *= 0
                # add new color
                self.controller.virtual_led_buffer += self.color_sequence_next
            # increment delay counter
            self.state.delay_counter += 1
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
