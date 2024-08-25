"""Reflect a color sequence and shift the reflections toward each other in the middle."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any

import numpy as np

from lightberries.array_sequence.reflect import SequenceReflect
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformMerge(PixelTransform):
    """Reflect a color sequence and shift the reflections toward each other in the middle."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
    ) -> None:
        """Do merge function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformMerge.__name__,
            controller=controller,
            pixel_sequence=pixel_sequence,
            state=state,
        )

    def setup(
        self,
        pixel_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        shift_amount: int | None = None,
        delay_count: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Reflect a color sequence and shift the reflections toward each other in the middle.

        Args:
        ----
            pixel_sequence: color sequence. Defaults to None.
            state: the initial or previous state of the light string
            kwargs: extra args to the state object
            shift_amount: amount the merge will shift in each update
            delay_count: length of reflected segments

        """
        if pixel_sequence is not None:
            self.pixel_sequence = self.pixel_sequence
        if state is not None:
            self.state = state
        else:
            self.state.delay_count_max = random.randint(6, 12)
            self.state.step = 1
        if delay_count is not None:
            self.state.delay_count_max = delay_count
        if shift_amount is not None:
            self.state.step = shift_amount
        # make sure doing a merge function would be visible
        if self.color_sequence_count >= self.controller.real_led_count:
            # if sequence is too long, cut it in half
            self.pixel_sequence = self.pixel_sequence[: int(self.color_sequence_count // 2)]
            # don't remember offhand why this is here
            if self.color_sequence_count % 2 == 1:
                if self.color_sequence_count == 1:
                    self.pixel_sequence = np.concatenate(
                        self.pixel_sequence,
                        self.pixel_sequence,
                    )
                else:
                    self.pixel_sequence = self.pixel_sequence[:-1]
        # calculate modulo length
        array_length = np.ceil(self.controller.real_led_count / self.color_sequence_count) * self.color_sequence_count
        # update LED buffer with any changes we had to make
        self.controller.set_virtual_led_buffer(
            SequenceReflect(
                arrayLength=array_length,
                colorSequence=self.pixel_sequence,
                foldLength=self.color_sequence_count,
            ),
        )
        # set merge size
        self.state.size = self.color_sequence_count
        # set shift amount
        self.state.step = shift_amount
        # set the number of LED refreshes to skip
        self.state.delay_count_max = delay_count
        # add function to list
        return [self]

    def transform(self) -> None:
        """Do nothing."""
        self.state.delay_counter += 1
        # check delay counter
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # figure out how many segments there are
            segment_count = int(self.controller.virtual_led_count // self.state.size)
            """
            this takes the 1-dimensional array
            [0,1,2,3,4,5]
            and creates a 2-dimensional matrix like
            [[0,1,2],
            [3,4,5]]
            """
            temp = np.reshape(
                self.controller.virtual_led_index_buffer,
                (segment_count, self.state.size),
            )
            # now roll each row in a different direction and then undo
            # the matrixification of the array
            if temp[0][0] != temp[1][-1]:
                temp[1] = np.flip(temp[0])
                self.controller.virtual_led_buffer[range(self.state.size)] = self.state.pixel_sequence[
                    range(self.state.size)
                ]
            temp[0] = np.roll(temp[0], self.state.step, 0)
            temp[1] = np.roll(temp[1], -self.state.step, 0)
            for i in range(self.controller.virtual_led_count // self.state.size):
                if i % 2 == 0:
                    temp[i] = temp[0]
                else:
                    temp[i] = temp[1]
            # turn the matrix back into an array
            self.controller.virtual_led_index_buffer = np.reshape(
                temp,
                (self.controller.virtual_led_count),
            )
