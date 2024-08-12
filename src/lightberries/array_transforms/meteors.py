import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionMeteors(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionMeteors.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )
        """Do meteor function things.

        Args:
            meteor: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """

    def _transform(self):
        try:
            # update delay counter
            self.state.delay_counter += 1
            # check if we are done delaying
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # calculate index + step
                self.update_array_index()
                if self.state.color_cycle:
                    # assign the next color
                    self.state.color = self.color_sequence_next
                # assign LEDs to LED string
                if len(self.controller.virtualLEDBuffer.shape) == 2:
                    self.controller.virtualLEDBuffer[self.state.index_range] = self.state.color
                else:
                    self.controller.virtualLEDBuffer[
                        np.where(
                            self.controller.virtualLEDIndexBuffer == self.state.index_range,
                        )
                    ] = self.state.color
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
