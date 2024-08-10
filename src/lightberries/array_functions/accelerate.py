import random

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionAccelerate(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionAccelerate.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    """Do accelerate function things.

    Args:
        accelerate: tracking object

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightFunctionException: if something bad happens
    """

    def run(self):
        try:
            self.state.index_previous = self.state.index
            splash = False
            # increment delay counter
            self.state.delay_counter += 1
            # check delay counter, update index when it hits max
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # update step counter
                self.state.step_counter += 1
                # calculate next index
                self.state.index_next = int(
                    (self.state.index + (self.state.direction * self.state.step))
                )
                self.state.index = (
                    self.state.index_next % self.controller.virtualLEDCount
                )
                self.state.index_range = np.arange(
                    self.state.index_previous + self.state.direction,
                    self.state.index_next + self.state.direction,
                    self.state.direction,
                )
                modulo = np.where(
                    self.state.index_range >= (self.controller.realLEDCount)
                )
                self.state.index_range[modulo] -= self.controller.realLEDCount
                if self.state.color_cycle is True:
                    self.state.color = self.color_sequence_next
            # check index step counter, update speed state when it hits step count max
            if self.state.step_counter >= self.state.step_count_max:
                # reset step counter
                self.state.step_counter = 0
                # reduce delay max
                self.state.delay_count_max -= 1
                # increment step size every two delay reductions
                if (self.state.state % 2) == 0:
                    self.state.step += 1
                # set step counter to a random number of steps based on LED count
                self.state.step_count_max = random.randint(
                    int(self.controller.realLEDCount / 20),
                    int(self.controller.realLEDCount / 4),
                )
                # update state counter
                self.state.state += 1
            # check state counter, reset speed state when it hits max speed
            if self.state.state > self.state.state_max:
                # "splash" color when we hit the end
                splash = True
                #  create the "splash" index array before updating direction etc.
                splash_range = np.array(
                    list(
                        range(
                            self.state.index_previous,
                            self.state.index_next
                            + (self.state.step * self.state.direction * 4),
                            self.state.direction,
                        )
                    ),
                    dtype=np.int32,
                )
                # make sure that the splash doesn't go off the edge of the virtual led array
                modulo = np.where(splash_range >= (self.controller.realLEDCount))
                splash_range[modulo] %= self.controller.realLEDCount
                modulo = np.where(splash_range < 0)
                splash_range[modulo] += self.controller.realLEDCount
                # reset delay
                self.state.delay_counter = 0
                # set new delay max
                self.state.delay_count_max = random.randint(5, 10)
                # reset state max
                self.state.state_max = self.state.delay_count_max
                # randomize direction
                self.state.direction = self.controller.getRandomDirection()
                # reset state
                self.state.state = 0
                # reset step
                self.state.step = 1
                # reset step counter
                self.state.step_counter = 0
                # randomize starting index
                self.state.index = self.controller.getRandomIndex()
                self.state.index_previous = self.state.index
                self.state.index_range = np.arange(
                    self.state.index_previous, self.state.index + 1
                )
            # self.controller.virtualLEDBuffer[self.state.indexRange] = self.state.color
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
            if splash is True:
                self.controller.virtualLEDBuffer[splash_range, :] = (
                    self.controller.fadeColor(
                        self.state.color, self.controller.backgroundColor, 50
                    )
                )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
