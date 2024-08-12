"""Function in which colorful lights accelerate across the string of lights repeatedly."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_transforms.base import ArrayTransform
from lightberries.array_transforms.fade_off import ArrayTransformFadeOff
from lightberries.exceptions import ControllerError, FunctionError, LightBerryError

LOGGER = logging.getLogger("lightBerries")

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState


class ArrayFunctionAccelerate(ArrayTransform):
    """Function in which colorful lights accelerate across the string of lights repeatedly."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """Accelerate across the string of lights repeatedly.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            delay_count_max: max delay between color updates
            step_count_max: speed limit
            fade_amount: speed of color fade
            cycle_colors: set true to cycle as the LED goes across

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        super().__init__(
            name=ArrayFunctionAccelerate.__class__.__name__,
            controller=controller,
            state=state,
            kwargs=kwargs,
        )
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionAccelerate.__name__,
        )
        try:
            """===========================================================================
            default values
            ==========================================================================="""
            # set the number of updates during which the lights will stay constant
            self.state.delay_count_max = random.randint(5, 10)
            # this determines the maximum that the LED can jump in a single step as it speeds up
            self.state.step_count_max = random.randint(4, 10)
            # this determines the length of comet tails
            self.state.fade_amount = random.randint(15, 35) / 255.0
            # whether to cycle through colors
            self.state.color_cycle = self.get_random_boolean()
            # the number of times the comet will accelerate
            self.state.state_max = random.randint(5, 10)
            # randomize direction
            self.state.direction = self.get_random_direction()
            # randomize start index
            self.state.index = self.get_random_index()

            """===========================================================================
            update values based on args
            ==========================================================================="""
            if "delay_count_max" in kwargs:
                self.state.delay_count_max = int(kwargs["delay_count_max"])
            if "step_count_max" in kwargs:
                self.state.step_count_max = int(kwargs["step_count_max"])
            if "fade_amount" in kwargs:
                self.state.fade_amount = float(kwargs["fade_amount"])
            # make sure fade amount is valid
            if self.state.fade_amount > 0 and self.state.fade_amount < 256:
                self.state.fade_amount /= 255
            if self.state.fade_amount < 0 or self.state.fade_amount > 1:
                self.state.fade_amount = 0.1
            if "color_cycle" in kwargs:
                self.state.color_cycle = bool(kwargs["color_cycle"])

            """===========================================================================
            add functions to array controller
            ==========================================================================="""
            # we want comet trails, so fade the buffer each time through
            self.privateLightFunctions.append(
                ArrayTransformFadeOff(
                    kwargs={"fade_amount": self.state.fade_amount},
                ),
            )
            self.controller.privateLightFunctions.append(self)
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def transform(self) -> None:
        """Accelerate across the string of lights repeatedly.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens

        """
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
                    self.state.index + (self.state.direction * self.state.step),
                )
                self.state.index = self.state.index_next % self.controller.virtual_led_count
                self.state.index_range = np.arange(
                    self.state.index_previous + self.state.direction,
                    self.state.index_next + self.state.direction,
                    self.state.direction,
                )
                modulo = np.where(
                    self.state.index_range >= (self.controller.real_led_count),
                )
                self.state.index_range[modulo] -= self.controller.real_led_count
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
                    int(self.controller.real_led_count / 20),
                    int(self.controller.real_led_count / 4),
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
                            self.state.index_next + (self.state.step * self.state.direction * 4),
                            self.state.direction,
                        ),
                    ),
                    dtype=np.int32,
                )
                # make sure that the splash doesn't go off the edge of the virtual led array
                modulo = np.where(splash_range >= (self.controller.real_led_count))
                splash_range[modulo] %= self.controller.real_led_count
                modulo = np.where(splash_range < 0)
                splash_range[modulo] += self.controller.real_led_count
                # reset delay
                self.state.delay_counter = 0
                # set new delay max
                self.state.delay_count_max = random.randint(5, 10)
                # reset state max
                self.state.state_max = self.state.delay_count_max
                # randomize direction
                self.state.direction = self.controller.get_random_direction()
                # reset state
                self.state.state = 0
                # reset step
                self.state.step = 1
                # reset step counter
                self.state.step_counter = 0
                # randomize starting index
                self.state.index = self.controller.get_random_index()
                self.state.index_previous = self.state.index
                self.state.index_range = np.arange(
                    self.state.index_previous,
                    self.state.index + 1,
                )
            if len(self.controller.virtualLEDBuffer.shape) == 2:
                self.controller.virtualLEDBuffer[self.state.index_range] = self.state.color
            else:
                self.controller.virtualLEDBuffer[
                    np.where(
                        self.controller.virtualLEDIndexBuffer == self.state.index_range,
                    )
                ] = self.state.color
            if splash is True:
                self.controller.virtualLEDBuffer[splash_range, :] = self.controller.fade_color(
                    self.state.color,
                    self.controller.background_color,
                    50,
                )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
