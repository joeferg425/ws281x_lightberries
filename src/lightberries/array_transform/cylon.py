"""Do cylon eye things."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np

from lightberries.array_sequence.solid import SequenceSolid
from lightberries.base.constants import MAX_INT8, SHAPE_2D
from lightberries.base.pixel import Pixel, PixelColor, pixel_from_color
from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay.fade_off import TransformFadeOff

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence


class TransformCylon(PixelTransform):
    """Do cylon eye things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do cylon eye things.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformCylon.__name__,
            controller=controller,
        )

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: int | None = None,
        delay_count: int | None = None,
    ) -> list[PixelTransform]:
        """Shift a pixel across the LED string marquee style and then bounce back leaving a comet tail.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            fade_amount: how much each pixel fades per refresh
                smaller numbers = larger tails on the cylon eye fade
            delay_count: number of delays

        """
        transform = TransformCylon(controller=controller)
        if state is not None:
            transform.state = state
        else:
            transform.state.set_fade_amount(random.randint(5, 75) / MAX_INT8)
            transform.state.delay_count_max = random.randint(10, 60)

        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        if fade_amount is not None:
            transform.state.set_fade_amount(fade_amount=fade_amount)
        if delay_count is not None:
            transform.state.delay_count_max = delay_count

        # fade the whole LED strand
        TransformFadeOff.create(
            controller=controller,
            fade_amount=transform.state.fade_amount,
        )

        # shift eye by this much for each update
        transform.state.size = transform.state.pixel_sequence.led_count
        # adjust virtual LED buffer if necessary so that the cylon can actually move
        if transform.controller.virtual_led_count <= controller.real_led_count:
            array = SequenceSolid(
                led_count=controller.real_led_count + 3,
                color=pixel_from_color(PixelColor.OFF),
            )
            array[: transform.state.pixel_sequence.led_count] = [Pixel(x) for x in transform.state.pixel_sequence]
            transform.controller.set_virtual_led_buffer(array)
        if transform.controller.virtual_led_count <= transform.state.pixel_sequence.led_count:
            array = SequenceSolid(
                led_count=transform.state.pixel_sequence.led_count + 3,
                color=pixel_from_color(PixelColor.OFF),
            )
            array[: transform.state.pixel_sequence.led_count] = [Pixel(x) for x in transform.state.pixel_sequence]
            transform.controller.set_virtual_led_buffer(array)
        # set start and next indices
        transform.state.index = transform.controller.virtual_led_count - transform.state.size - 3
        transform.state.index_next = transform.state.index

        TransformCylon.ACTIVE_TRANSFORMS.append(transform)
        return TransformCylon.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do alive function things."""
        # update delay counter
        self.state.delay_counter += 1
        # wait for several LED cycles to change LEDs
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # check direction
            if self.state.direction > 0:
                # calculate index array going from min to max
                self.state.index_next = self.state.index + (self.state.direction * self.state.step)
                self.state.index_min = self.state.index_next
                self.state.index_max = self.state.index_next + (self.state.size * self.state.direction)
                self.state.index_range = np.arange(
                    self.state.index_min,
                    self.state.index_max,
                    self.state.direction,
                )
            else:
                # calculate index array going from max to min
                self.state.index_next = self.state.index + (self.state.direction * self.state.step)
                self.state.index_min = self.state.index_next + (self.state.size * self.state.direction)
                self.state.index_max = self.state.index_next
                self.state.index_range = np.arange(
                    self.state.index_max,
                    self.state.index_min,
                    self.state.direction,
                )
            # check if color sequence would go off of far end of light string
            if self.state.index_max >= self.controller.virtual_led_count:
                # if the last LED is headed off the end
                if self.state.index_next >= self.controller.virtual_led_count:
                    # reverse direction
                    self.state.direction = -1
                    # fix next index
                    self.state.index_next = self.controller.virtual_led_count - 2
                # find where LEDs go off the end
                over = np.where(
                    self.state.index_range >= (self.controller.virtual_led_count),
                )[0]
                # reverse their direction
                self.state.index_range[over] = np.arange(
                    -1,
                    (len(over) + 1) * -1,
                    -1,
                ) + (self.controller.virtual_led_count - 1)
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
        if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
            self.controller.virtual_led_buffer[self.state.index_range] = self.state.pixel_sequence.pixel.array
        else:
            self.controller.virtual_led_buffer[
                np.where(
                    self.controller.virtual_led_index_buffer == self.state.index_range,
                )
            ] = self.state.pixel_sequence.pixel.array
