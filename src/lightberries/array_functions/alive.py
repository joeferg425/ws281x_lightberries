from random import random

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import (
    ArrayFunction,
    ThingColors,
    ThingMoves,
    ThingSizes,
)
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionAlive(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do alive function things.

        Args:
            thing: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        super().__init__(
            name=ArrayFunctionAlive.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        try:
            # track last index
            self.state.index_previous = self.state.index
            # if we have hit our step goal
            if self.state.delay_counter >= self.state.delay_count_max:
                self.state.delay_counter = 0
                if self.state.step_counter < self.state.step_count_max:
                    # if in meteor mode
                    if self.state.state & ThingMoves.METEOR.value:
                        self.state.step = 1
                        # set next index
                        self.update_array_index()
                        # thing.indexNext = (
                        #     thing.index + (thing.step * thing.direction)
                        # ) % self.controller.virtualLEDCount
                        # randomly change direction
                        if random.randint(0, 99) > 95:
                            self.state.direction *= -1  # pragma: no cover
                    # if in fast meteor mode
                    elif self.state.state & ThingMoves.LIGHT_SPEED.value:
                        # artificially limit duration of this mode
                        if self.state.step_count_max >= self.state.period_short:
                            self.state.step_count_max = self.state.period_short
                        # randomize step size
                        self.state.step = random.randint(7, 12)
                        # set next index
                        self.update_array_index()
                        # thing.index = (
                        #     thing.index + (thing.step * thing.direction)
                        # ) % self.controller.virtualLEDCount
                        # randomly change direction
                        if random.randint(0, 99) > 95:
                            self.state.direction *= -1  # pragma: no cover
                    # if slow meteor
                    elif self.state.state & ThingMoves.TURTLE.value:
                        # set step to 1
                        self.state.step = 1
                        # randomly change direction
                        if random.randint(0, 99) > 80:
                            self.state.direction *= -1  # pragma: no cover
                        # set next index
                        self.update_array_index()
                        # thing.index = (
                        #     thing.index + (thing.step * thing.direction)
                        # ) % self.controller.virtualLEDCount
                    # if we are growing
                    if self.state.state & ThingSizes.GROW.value:
                        # artificially limit duration
                        if self.state.step_count_max > self.state.period_short:
                            self.state.step_count_max = self.state.period_short
                        # if we can still grow
                        if self.state.size < self.state.size_max:
                            # randomly grow
                            if random.randint(0, 99) > 80:
                                self.state.size += random.randint(
                                    1, 5
                                )  # pragma: no cover
                            # also randomly shrink a bit
                            if self.state.size > 2:
                                if random.randint(0, 99) > 90:
                                    self.state.size -= 1  # pragma: no cover
                        # make sure we aren't overgrown
                        if self.state.size > self.state.size_max:
                            self.state.size = self.state.size_max
                        # make sure we still exist
                        elif self.state.size < 1:
                            self.state.size = 1
                    # if we are shrinking
                    elif self.state.state & ThingSizes.SHRINK.value:
                        # artificially limit duration
                        if self.state.step_count_max > self.state.period_short:
                            self.state.step_count_max = self.state.period_short
                        # if we can shrink
                        if self.state.size > 0:
                            # randomly shrink
                            if random.randint(0, 99) > 80:
                                self.state.size -= random.randint(1, 5)
                            # also randomly grow a bit
                            if self.state.size < self.state.size_max:
                                if random.randint(0, 99) > 90:
                                    self.state.size += 1  # pragma: no cover
                        # make sure we aren't overgrown
                        if self.state.size >= self.state.size_max:
                            self.state.size = self.state.size_max
                        # also make sure we still exist
                        elif self.state.size < 1:
                            self.state.size = 1
                    # if we are cycling through colors
                    if self.state.state & ThingColors.CYCLE.value:
                        # artificially limit duration
                        if self.state.step_count_max >= self.state.period_short:
                            self.state.step_count_max = self.state.period_short
                        # randomly cycle through assign colors
                        if random.randint(0, 99) > 90:
                            for _ in range(0, random.randint(1, 3)):
                                self.state.color = self.color_sequence_next
                    # calculate range of affected indices
                    # index1 = thing.indexPrevious - (thing.size * thing.direction)
                    # index2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
                    # indexLower = min(index1, index2)
                    # indexHigher = max(index1, index2)
                    # calculate affected range
                    # thing.indexRange = thing.calcRange()
                    # increment step counter
                    self.state.step_counter += 1
                # we hit our step goal, randomize next state
                else:
                    # states are mutually exclusive bits, can just add one of each
                    for _ in range(random.randint(1, 3)):
                        self.state.state = (
                            list(ThingMoves)[
                                random.randint(0, len(ThingMoves) - 1)
                            ].value
                            + list(ThingSizes)[
                                random.randint(0, len(ThingSizes) - 1)
                            ].value
                            + list(ThingColors)[
                                random.randint(0, len(ThingColors) - 1)
                            ].value
                        )
                    # reset step counter
                    self.state.step_counter = 0
                    # set step count to random value
                    self.state.step_count_max = random.randint(
                        self.controller.virtualLEDCount // 10,
                        self.controller.virtualLEDCount,
                    )
                    # set delay count randomly
                    self.state.delay_count_max = random.randint(6, 15)
                    # randomize step size
                    self.state.step = random.randint(1, 3)
                    # randomize fade amount
                    self.state.fade_amount = random.randint(80, 192)
                    # randomize delays
                    if self.state.state & ThingMoves.METEOR.value:
                        self.state.delay_count_max = random.randint(1, 3)
                    elif self.state.state & ThingMoves.TURTLE.value:
                        self.state.delay_count_max = random.randint(15, 45)
                    elif self.state.state & ThingMoves.LIGHT_SPEED.value:
                        self.state.delay_count_max = random.randint(0, 3)
                    else:
                        self.state.delay_count_max = random.randint(1, 7)
                    # calculate affected range
                    # index1 = thing.indexPrevious - (thing.size * thing.direction)
                    # index2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
                    # indexLower = min(index1, index2)
                    # indexHigher = max(index1, index2)
                    # rng = np.array(range(_x1, _x2 + 1))
                    self.state.index_range = self.calc_range()
            # increment delay
            self.state.delay_counter += 1
            # assign colors to indices
            # self.controller.virtualLEDBuffer[thing.indexRange] = thing.color
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
