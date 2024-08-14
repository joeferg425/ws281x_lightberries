import logging

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError

LOGGER = logging.getLogger("lightBerries")


class ArrayFunctionMerge(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionMerge.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    """Do merge function things.

    Args:
        merge: tracking object

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightFunctionException: if something bad happens
    """

    def _transform(self):
        try:
            self.state.delay_counter += 1
            # check delay counter
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # figure out how many segments there are
                segmentCount = int(self.controller.virtual_led_count // self.state.size)
                # this takes the 1-dimensional array
                # [0,1,2,3,4,5]
                # and creates a 2-dimensional matrix like
                # [[0,1,2],
                #  [3,4,5]]
                temp = np.reshape(
                    self.controller.virtual_led_index_buffer,
                    (segmentCount, self.state.size),
                )
                # now roll each row in a different direction and then undo
                # the matrixification of the array
                if temp[0][0] != temp[1][-1]:
                    temp[1] = np.flip(temp[0])
                    self.controller.virtual_led_buffer[range(self.state.size)] = self.state.color_sequence[
                        range(self.state.size)
                    ]
                temp[0] = np.roll(temp[0], self.state.step, 0)
                temp[1] = np.roll(temp[1], -self.state.step, 0)
                for i in range(self.controller.virtual_led_count // self.state.size):
                    if i % 2 == 0:
                        temp[i] = temp[0]
                    else:
                        temp[i] = temp[1]
                # turn the matrix back into an array
                self.controller.virtual_led_index_buffer = np.reshape(
                    temp,
                    (self.controller.virtual_led_count),
                )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
