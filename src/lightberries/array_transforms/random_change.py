import random

import numpy as np

import lightberries
from lightberries.array_transforms.base import ArrayTransform, ChangeStates, LEDFadeType
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionRandomChange(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionRandomChange.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )
        """Do random change function things.

        Args:
            change: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """

    def _transform(self):
        try:
            # if the random change has completed
            if np.array_equal(self.state.color, self.state.color_next):
                # if the state is "fading on"
                if self.state.state == ChangeStates.FADING_ON.value:
                    # just set next state to "on"
                    self.state.state = ChangeStates.ON.value
                # if the state is "on"
                elif self.state.state == ChangeStates.ON.value:
                    # increment delay counter
                    self.state.delay_counter += 1
                    # if we are done delaying
                    if self.state.delay_counter >= self.state.delay_count_max:
                        # reset delay counter
                        self.state.delay_counter = random.randint(
                            0,
                            self.state.delay_count_max,
                        )
                        # randomly fading some LEDs to background color
                        if random.randint(0, 3) == 3:
                            # set next color to background color
                            self.state.color_next = self.controller.background_color
                            # set state to "fading off"
                            self.state.state = ChangeStates.FADING_OFF.value
                        # if not fading to background
                        else:
                            # go to wait state
                            self.state.state = ChangeStates.WAIT.value
                # if state is "fading off"
                elif self.state.state == ChangeStates.FADING_OFF.value:
                    # increment delay counter
                    self.state.delay_counter += 1
                    # if we are done delaying
                    if self.state.delay_counter >= self.state.delay_count_max:
                        # set state to "waiting"
                        self.state.state = ChangeStates.WAIT.value
                        # reset delay counter
                        self.state.delay_counter = random.randint(
                            0,
                            self.state.delay_count_max,
                        )
                # if state is "waiting"
                elif self.state.state == ChangeStates.WAIT.value:
                    # increment delay counter
                    self.state.delay_counter += 1
                    # if we are done waiting
                    if self.state.delay_counter >= self.state.delay_count_max:
                        # randomize next index
                        self.state.index = self.controller.get_random_index()
                        # get color of current LED index
                        # change.color = np.copy(self.controller.virtualLEDBuffer[change.index])
                        if len(self.controller.virtualLEDBuffer.shape) == 2:
                            self.state.color = self.controller.virtualLEDBuffer[self.state.index]
                        else:
                            self.state.color = self.controller.virtualLEDBuffer[
                                np.where(
                                    self.controller.virtualLEDIndexBuffer == self.state.index,
                                )
                            ]
                        # get next color
                        for _ in range(random.randint(1, 5)):
                            self.state.color_next = self.color_sequence_next
                        # set state to "fading on"
                        self.state.state = ChangeStates.FADING_ON.value
                        # randomize delay counter so they aren't synchronized
                        self.state.delay_counter = random.randint(
                            0,
                            self.state.delay_count_max,
                        )
            # if fading LEDs
            if self.state.fade_type == LEDFadeType.FADE_OFF:
                # fade the color
                self.state.color = self.controller.fade_color(
                    self.state.color,
                    self.state.color_next,
                    self.state.fade_amount,
                )
            # if instant on/off
            else:
                # set the color
                self.state.color = self.state.color_next
            # assign LED color to LED string
            # self.controller.virtualLEDBuffer[change.index] = change.color
            if len(self.controller.virtualLEDBuffer.shape) == 2:
                self.controller.virtualLEDBuffer[self.state.index] = self.state.color
            else:
                self.controller.virtualLEDBuffer[
                    np.where(self.controller.virtualLEDIndexBuffer == self.state.index)
                ] = self.state.color
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
