import random

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction, RaindropStates
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionRaindrops(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do raindrop function things.

        Args:
            raindrop: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        super().__init__(
            name=ArrayFunctionRaindrops.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        try:
            # if raindrop is off
            if self.state.state == RaindropStates.OFF.value:
                # randomly turn on
                if random.randint(0, 1000) / 1000 < self.state.active_chance:
                    # set state on
                    self.state.state = RaindropStates.SPLASH.value
                    # set max width of this raindrop
                    self.state.step_count_max = random.randint(
                        1, max(self.state.size_max, 2)
                    )
                    # set fade amount
                    self.state.fade_amount = (
                        (255 / self.state.step_count_max) / 255
                    ) * 2
                    self.state.color_scaler = (
                        self.state.step_count_max - self.state.step_counter
                    ) / self.state.step_count_max
            # if raindrop is splashing
            elif self.state.state == RaindropStates.SPLASH.value:
                # if splash is still growing
                if self.state.step_counter <= self.state.step_count_max:
                    # lower valued side of "splash"
                    indexLowerMin = max(
                        self.state.index - self.state.step * self.state.step_counter, 0
                    )
                    indexLowerMax = max(
                        self.state.index
                        + 1
                        - self.state.step * self.state.step_counter,
                        0,
                    )
                    # higher valued side of "splash"
                    indexHigherMin = min(
                        self.state.index + self.state.step_counter,
                        self.controller.virtualLEDCount,
                    )
                    indexHigherMax = min(
                        self.state.index + self.state.step_counter + self.state.step,
                        self.controller.virtualLEDCount,
                    )
                    if (indexLowerMax - indexLowerMin) > 0:
                        indexRange = list(range(indexLowerMin, indexLowerMax))
                        self.controller.virtualLEDBuffer[
                            indexLowerMin:indexLowerMax
                        ] = [self.state.color] * (indexLowerMax - indexLowerMin)
                        if len(self.controller.virtualLEDBuffer.shape) == 2:
                            self.controller.virtualLEDBuffer[indexRange] = (
                                self.state.color
                            )
                        else:
                            self.controller.virtualLEDBuffer[
                                np.where(
                                    self.controller.virtualLEDIndexBuffer == indexRange
                                )
                            ] = self.state.color
                    if (indexHigherMax - indexHigherMin) > 0:
                        indexRange = list(range(indexHigherMin, indexHigherMax))
                        # self.controller.virtualLEDBuffer[indexHigherMin:indexHigherMax]
                        # = [raindrop.color] * (
                        # indexHigherMax - indexHigherMin
                        # )
                        if len(self.controller.virtualLEDBuffer.shape) == 2:
                            self.controller.virtualLEDBuffer[indexRange] = (
                                self.state.color
                            )
                        else:
                            self.controller.virtualLEDBuffer[
                                np.where(
                                    self.controller.virtualLEDIndexBuffer == indexRange
                                )
                            ] = self.state.color
                    # scaled fading as splash grows
                    self.state.color[:] = self.state.color * self.state.color_scaler
                    # increment splash growth counter
                    self.state.step_counter += self.state.step
                # splash is done growing
                else:
                    # randomize next splash start index
                    self.state.index = random.randint(
                        0, self.controller.virtualLEDCount - 1
                    )
                    # reset growth counter
                    self.state.step_counter = 0
                    # semi-randomize next color
                    for _ in range(1, random.randint(2, 4)):
                        self.state.color = self.color_sequence_next
                    # set state to off
                    self.state.state = RaindropStates.OFF.value
            # increment delay
            # raindrop.delayCounter += 1
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
