import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import FunctionError, LightBerryError


class ArrayFunctionMarquee(ArrayTransform):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        super().__init__(
            name=ArrayFunctionMarquee.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )
        """Move the LEDs in the color sequence from one end of the LED string to the other continuously.

        Args:
            marquee: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """

    def _transform(self):
        try:
            # increment delay counter
            self.state.delay_counter += 1
            # wait for several LED cycles to change LEDs
            if self.state.delay_counter >= self.state.delay_count_max:
                # reset delay counter
                self.state.delay_counter = 0
                # calculate possible next index
                self.state.index_next = self.state.index + (self.state.step * self.state.direction)
                # calculate max index we will update
                self.state.index_max = self.state.index_next + self.state.size
                # if we are going to overshoot
                if self.state.index_max >= self.controller.virtual_led_count:
                    # switch direction
                    self.state.direction *= -1
                    # set index to either the next step or the max possible
                    # (accounts for step sizes > 1)
                    self.state.index = max(
                        self.state.index + (self.state.step * self.state.direction),
                        self.controller.virtual_led_count - self.state.size,
                    )
                # if we will undershoot
                elif self.state.index_max < self.state.size:
                    # TODO: should make a wrap-around version
                    # switch direction
                    self.state.direction *= -1
                    # set index to either the next step or zero
                    # (accounts for step sizes > 1)
                    self.state.index = max(
                        self.state.index + (self.state.step * self.state.direction),
                        0,
                    )
                else:
                    # next index is valid, use it
                    self.state.index = self.state.index_next
            # calculate color sequence range
            self.state.index_range = np.arange(
                self.state.index,
                self.state.index + self.state.size,
            )
            # update LEDs with new values
            self.controller.virtualLEDBuffer[np.sort(self.state.index_range)] = self.color_sequence
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
