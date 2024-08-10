from random import random

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction, SpriteState
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.pixel import PixelColors


class ArrayFunctionSprites(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do sprite function things.

        Args:
            sprite: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        super().__init__(
            name=ArrayFunctionSprites.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        try:
            # if not off
            if self.state.state != SpriteState.OFF.value:
                # semi-randomly die
                _min = min(int(self.state.step_counter // 3), 5)
                _max = max(int(self.state.step_counter // 3), 6)
                if random.randint(_min, _max) < self.state.step_counter:
                    self.state.state = SpriteState.FADING_OFF.value
                # randomize step sizes
                self.state.step = random.randint(1, 3)
                # only update LED string when we change the index
                self.state.index_updated = False
                # if we are done delaying
                if self.state.delay_counter >= self.state.delay_count_max:
                    # reset delay counter
                    self.state.delay_counter = 0
                    # move index
                    self.update_array_index()
                # if we are fading off
                if self.state.state == SpriteState.FADING_OFF.value:
                    # fade the color
                    self.state.color = self.controller.fadeColor(
                        self.state.color, self.state.color_next, self.state.fade_amount
                    )
                    # if we are done fading, then change state
                    if np.array_equal(self.state.color, self.state.color_next):
                        self.state.state = SpriteState.OFF.value
                # if we are fading on
                if self.state.state == SpriteState.FADING_ON.value:
                    # fade the color
                    self.state.color = self.controller.fadeColor(
                        self.state.color, self.state.color_goal, self.state.fade_amount
                    )
                    # if we are done fading
                    if np.array_equal(self.state.color, self.state.color_goal):
                        # change state
                        self.state.state = SpriteState.ON.value
                # increment duration counter
                self.state.step_counter += 1
            # when sprite is in "off" state
            else:
                # randomly start fading on
                if random.randint(0, 999) > 800:
                    # set state to fade on
                    self.state.state = SpriteState.FADING_ON.value
                    # reset step counter
                    self.state.step_counter = 0
                    # randomize direction
                    self.state.direction = self.controller.getRandomDirection()
                    # randomize start index
                    self.state.index = self.controller.getRandomIndex()
                    # set previous (prevent artifacts)
                    self.state.index_previous = self.state.index
                    # set target color
                    self.state.color_goal = self.color_sequence_next
                    # set current color
                    self.state.color = PixelColors.OFF.array
                    # set next color
                    self.state.color_next = PixelColors.OFF.array
            # if we changed the index
            if self.state.index_updated is True and isinstance(
                self.state.index_range, np.ndarray
            ):
                # reset flag
                self.state.index_updated = False
                # assign LEDs to LED string
                # self.controller.virtualLEDBuffer[sprite.indexRange] = [sprite.color] * len(sprite.indexRange)
                if len(self.controller.virtualLEDBuffer.shape) == 2:
                    self.controller.virtualLEDBuffer[self.state.index_range] = (
                        self.state.color
                    )
                else:
                    self.controller.virtualLEDBuffer[
                        np.where(
                            self.controller.virtualLEDIndexBuffer
                            == self.state.index_range
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
