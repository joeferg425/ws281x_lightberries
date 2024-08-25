"""Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_sequence.solid import SequenceSolid
from lightberries.pixel import Pixel, PixelColor
from lightberries.pixel_transform import PixelTransform
from lightberries.transform_overlay.fade_off import TransformFadeOff

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformShift(PixelTransform):
    """Move the LEDs in the color sequence from one end of the LED string to the other continuously."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
    ) -> None:
        """Move the LEDs in the color sequence from one end of the LED string to the other continuously.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformShift.__name__,
            controller=controller,
            pixel_sequence=pixel_sequence,
            state=state,
        )

    def setup(  # noqa: D417, PLR0913
        self,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = 0.0,
        shift_amount: int | None = None,
        delay_count: int | None = None,
        initial_direction: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            shift_amount: the number of pixels the marquee shifts on each update
            delay_count: number of refreshes to delay for each cycle
            initial_direction: a positive or negative value for marquee start direction
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        if pixel_sequence is not None:
            self.state.pixel_sequence = pixel_sequence
        if state is not None:
            self.state = state
        else:
            self.state.step = random.randint(1, 2)
            self.state.delay_count_max = random.randint(10, 50)
            self.state.direction = self.get_random_direction()

        if shift_amount is not None:
            self.state.step = shift_amount
        if delay_count is not None:
            self.state.delay_count_max = delay_count
        if initial_direction is not None:
            self.state.direction = 1 if (initial_direction >= 1) else -1
        if fade_amount is None:
            self.state.set_fade_amount(random.uniform(0.01, 0.1))

        # this function just shifts the existing virtual LED buffer,
        # so make sure the virtual LED buffer is initialized here
        if self.state.pixel_sequence.led_count > self.controller.virtual_led_count:
            array = SequenceSolid(
                led_count=self.state.pixel_sequence.led_count,
                color=Pixel(PixelColor.OFF),
            )
            array[: self.state.pixel_sequence.led_count] = list(self.state.pixel_sequence)
            self.controller.virtual_led_buffer[:] = array
        else:
            self.controller.virtual_led_buffer[:] = self.state.pixel_sequence

        # if self.state.fade_amount > 0.0:
        #     # turn off all LEDs every time so we can turn on new ones
        #     fade_off = TransformFadeOff(controller=self.controller, state=state)
        #     self.ACTIVE_TRANSFORMS.append(fade_off)
        self.ACTIVE_TRANSFORMS.append(self)
        return self.ACTIVE_TRANSFORMS

    def transform(self) -> None:
        """Do nothing."""
        # increment delay counter
        self.state.delay_counter += 1
        # wait for several LED cycles to change LEDs
        if self.state.delay_counter >= self.state.delay_count_max:
            self.state.delay_counter = 0
            # reset delay counter
            # update LEDs with new values
            self.controller.virtual_led_buffer = np.roll(self.controller.virtual_led_buffer, self.state.step, 0)
