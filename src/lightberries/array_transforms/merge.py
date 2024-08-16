"""Reflect a color sequence and shift the reflections toward each other in the middle."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

import lightberries.array_controller
from lightberries.array_transforms.base import ArrayTransform
from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformMerge(ArrayTransform):
    """Reflect a color sequence and shift the reflections toward each other in the middle."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray = None,
    ) -> None:
        """Do merge function things.

        Args:
        ----
            controller: Array controller instance
            state: the initial or previous state of the light string

        """
        super().__init__(
            name=TransformMerge.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def setup(
        self,
        color_sequence: np.ndarray[Any, np.int32] | None = None,
        state: TransformState | None = None,
        *,
        shift_amount: int | None = None,
        delay_count: int | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Reflect a color sequence and shift the reflections toward each other in the middle.

        Args:
        ----
            shiftAmount: amount the merge will shift in each update
            delayCount: length of reflected segments

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        _delayCount: int = random.randint(6, 12)
        _shiftAmount: int = 1
        if delay_count is not None:
            _delayCount = int(delay_count)
        if shift_amount is not None:
            _shiftAmount = int(shift_amount)
        # make sure doing a merge function would be visible
        if self.color_sequence_count >= self.real_led_count:
            # if sequence is too long, cut it in half
            self.color_sequence = self.color_sequence[: int(self.color_sequence_count // 2)]
            # don't remember offhand why this is here
            if self.color_sequence_count % 2 == 1:
                if self.color_sequence_count == 1:
                    self.color_sequence = np.concatenate(
                        self.color_sequence,
                        self.color_sequence,
                    )
                else:
                    self.color_sequence = self.color_sequence[:-1]
        # calculate modulo length
        _arrayLength = np.ceil(self.real_led_count / self.color_sequence_count) * self.color_sequence_count
        # update LED buffer with any changes we had to make
        self.set_virtual_led_buffer(
            ArraySequence.ReflectArray(
                arrayLength=_arrayLength,
                colorSequence=self.color_sequence,
                foldLength=self.color_sequence_count,
            ),
        )
        # create tracking object
        merge: LightTransform = LightTransform(
            self,
            LightTransform.functionMerge,
            self.color_sequence,
        )
        # set merge size
        merge._size = self.color_sequence_count
        # set shift amount
        merge._step = _shiftAmount
        # set the number of LED refreshes to skip
        merge._delay_count_max = _delayCount
        # add function to list
        self._transforms.append(merge)

    def transform(self):
        self.state.delay_counter += 1
        # check delay counter
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            # figure out how many segments there are
            segmentCount = int(self.controller.virtual_led_count // self.state.size)
            # this takes the 1-dimensional array
            # [0,1,2,3,4,5]
            # and creates a 2-dimensional matrix like
            # [[0,1,2],
            #  [3,4,5]]
            temp = np.reshape(
                self.controller.virtual_led_index_buffer,
                (segmentCount, self.state.size),
            )
            # now roll each row in a different direction and then undo
            # the matrixification of the array
            if temp[0][0] != temp[1][-1]:
                temp[1] = np.flip(temp[0])
                self.controller.virtual_led_buffer[range(self.state.size)] = self.state.color_sequence[
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
