import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionSolidColorCycle(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionSolidColorCycle.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        """Set all pixels to the next color.

        Args:
            cycle: tracking object

        Raises:
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
                self.controller.virtualLEDBuffer *= 0
                # add new color
                self.controller.virtualLEDBuffer += self.color_sequence_next
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
