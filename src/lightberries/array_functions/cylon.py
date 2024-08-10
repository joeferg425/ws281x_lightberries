import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionCylon(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionCylon.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )
        """Do cylon eye things.

        Args:
            cylon: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """

    def run(self):
        try:
            # update delay counter
            self.state.delay_counter += 1
            # wait for several LED cycles to change LEDs
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # check direction
                if self.state.direction > 0:
                    # calculate index array going from min to max
                    self.state.index_next = self.state.index + (
                        self.state.direction * self.state.step
                    )
                    self.state.index_min = self.state.index_next
                    self.state.index_max = self.state.index_next + (
                        self.state.size * self.state.direction
                    )
                    self.state.index_range = np.arange(
                        self.state.index_min, self.state.index_max, self.state.direction
                    )
                else:
                    # calculate index array going from max to min
                    self.state.index_next = self.state.index + (
                        self.state.direction * self.state.step
                    )
                    self.state.index_min = self.state.index_next + (
                        self.state.size * self.state.direction
                    )
                    self.state.index_max = self.state.index_next
                    self.state.index_range = np.arange(
                        self.state.index_max, self.state.index_min, self.state.direction
                    )
                # check if color sequence would go off of far end of light string
                if self.state.index_max >= self.controller.virtualLEDCount:
                    # if the last LED is headed off the end
                    if self.state.index_next >= self.controller.virtualLEDCount:
                        # reverse direction
                        self.state.direction = -1
                        # fix next index
                        self.state.index_next = self.controller.virtualLEDCount - 2
                    # find where LEDs go off the end
                    over = np.where(
                        self.state.index_range >= (self.controller.virtualLEDCount)
                    )[0]
                    # reverse their direction
                    self.state.index_range[over] = np.arange(
                        -1, (len(over) + 1) * -1, -1
                    ) + (self.controller.virtualLEDCount - 1)
                # if LEDs go off the other end
                elif self.state.index_min < 0:
                    # if the last LED is headed off the end
                    if self.state.index_next < 0:
                        # reverse direction
                        self.state.direction *= -1
                        # fix next index
                        self.state.index_next = 1
                    # find where LEDs go off the end
                    over = np.where(self.state.index_range < 0)[0]
                    # reverse their direction
                    self.state.index_range[over] = np.arange(1, (len(over) + 1), 1)
            # update index
            self.state.index = self.state.index_next
            # update LEDs with new values
            # self.controller.virtualLEDBuffer[cylon.indexRange] = cylon.colorSequence[
            #     : self.controller.virtualLEDCount
            # ]
            if len(self.controller.virtualLEDBuffer.shape) == 2:
                self.controller.virtualLEDBuffer[self.state.index_range] = (
                    self.state.color
                )
            else:
                self.controller.virtualLEDBuffer[
                    np.where(
                        self.controller.virtualLEDIndexBuffer == self.state.index_range
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
