"""Do alive function things."""

from __future__ import annotations

import random
from enum import IntFlag
from typing import TYPE_CHECKING

from lightberries.overlay.fade_off import TransformFadeOff
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.base.state import TransformState
    from lightberries.pixel_sequence import PixelSequence


class AliveStates(IntFlag):
    """States for thing movement."""

    SPEED_STOPPED = 1
    SPEED_SLOW = 2
    SPEED_NORMAL = 4
    SPEED_FAST = 8
    SIZE_SHRINK = 16
    SIZE_FIXED = 32
    SIZE_GROW = 64
    COLOR_FIXED = 128
    COLOR_CYCLE = 256


class TransformAlive(PixelTransform):
    """Do alive function things."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Do alive function things.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformAlive.__name__,
            controller=controller,
        )

    @staticmethod
    def create(  # noqa: PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
        size_max: int | None = None,
        step_count_max: int | None = None,
        step_size_max: int | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: _description_. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object
            fade_amount: amount of fade
            size_max: max size of LED pattern
            step_count_max: max duration of effect
            step_size_max: max speed

        Returns:
        -------
            list of transforms

        """
        PixelTransform.clear_active()
        alive = TransformAlive(controller=controller)
        if state is not None:
            alive.state = state
        else:
            alive.state.set_fade_amount(random.uniform(0.20, 0.75))
            alive.state.size_max = random.randint(
                alive.controller.virtual_led_count // 6,
                alive.controller.virtual_led_count // 3,
            )
            alive.state.step_count_max = random.randint(
                alive.controller.virtual_led_count // 10,
                alive.controller.virtual_led_count,
            )
            alive.state.step_size_max_setting = random.randint(6, 10)

        if pixel_sequence is not None:
            alive.state.pixel_sequence = pixel_sequence

        if fade_amount is not None:
            alive.state.set_fade_amount(fade_amount)
        if size_max is not None:
            alive.state.size_max = size_max
        if step_size_max is not None:
            alive.state.step_count_max = step_size_max
        if fade_amount is not None:
            alive.state.set_fade_amount(fade_amount=fade_amount)
        if step_count_max is not None:
            step_count_max = int(step_count_max)

        TransformFadeOff.create(controller=controller, fade_amount=alive.state.fade_amount)
        thing = None
        # for _ in range(random.randint(2, 5)):
        for _ in range(1):
            if thing is None:
                thing = alive
            else:
                thing = alive.copy()

            # randomize start index
            thing.state.index = alive.get_random_index()
            # randomize direction
            thing.state.direction = alive.get_random_direction()
            thing.state.re_init()
            thing.state.index_range = thing.calc_sequence_range()
            # copy color sequence
            thing.state.pixel_sequence = alive.state.pixel_sequence.copy()
            # randomize speed
            thing.state.step_size = random.randint(1, thing.state.step_size_max_setting)
            # randomize refresh speed
            thing.state.delay_count_max = 10  # random.randint(6, 15)
            # randomize initial size
            thing.state.size = random.randint(1, int(thing.state.size_max // 2))
            # start the state at 1
            thing.state.current_state = AliveStates.SIZE_GROW  # ThingMoves.METEOR
            # calculate random next state immediately
            thing.state.step_counter = 1000
            thing.state.delay_counter = 1000
            TransformAlive.ACTIVE_TRANSFORMS.append(thing)
        TransformAlive.ACTIVE_TRANSFORMS[0].state.active = True
        # add a fade
        return TransformAlive.ACTIVE_TRANSFORMS

    def transform(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Do alive function things."""
        super().transform()
        # track last index
        if self.state.delay_count_reset:
            self.advance_step_counter()
        if not self.state.step_count_reset:
            # if in meteor mode
            if self.state.current_state & AliveStates.SPEED_NORMAL:
                self.state.step_size = 1
                # set next index
                self.advance_index()
                self.state.index_range = self.calc_sequence_range()
                # randomly change direction
                if random.randint(0, 99) > 95:  # noqa: PLR2004
                    self.state.direction *= -1  # pragma: no cover
            # if in fast meteor mode
            elif self.state.current_state & AliveStates.SPEED_FAST:
                # artificially limit duration of this mode
                self.state.step_count_max = min(self.state.period_short, self.state.step_count_max)
                # randomize step size
                self.state.step_size = random.randint(7, 12)
                # set next index
                self.advance_index()
                self.state.index_range = self.calc_sequence_range()
                # randomly change direction
                if random.randint(0, 99) > 95:  # noqa: PLR2004
                    self.state.direction *= -1  # pragma: no cover
            # if slow meteor
            elif self.state.current_state & AliveStates.SPEED_SLOW:
                # set step to 1
                self.state.step_size = 1
                # randomly change direction
                if random.randint(0, 99) > 80:  # noqa: PLR2004
                    self.state.direction *= -1  # pragma: no cover
                # set next index
                self.advance_index()
                self.state.index_range = self.calc_sequence_range()
            # if we are growing
            if self.state.current_state & AliveStates.SIZE_GROW:
                # artificially limit duration
                self.state.step_count_max = min(self.state.period_short, self.state.step_count_max)
                # if we can still grow
                if self.state.size < self.state.size_max:
                    # randomly grow
                    if random.randint(0, 99) > 80:  # noqa: PLR2004
                        self.state.size += random.randint(
                            1,
                            5,
                        )  # pragma: no cover
                    # also randomly shrink a bit
                    if self.state.size > 2 and random.randint(0, 99) > 90:  # noqa: PLR2004
                        self.state.size -= 1  # pragma: no cover
                # make sure we aren't overgrown
                if self.state.size > self.state.size_max:
                    self.state.size = self.state.size_max
                # make sure we still exist
                elif self.state.size < 1:
                    self.state.size = 1
                self.state.index_range = self.calc_sequence_range()
            # if we are shrinking
            elif self.state.current_state & AliveStates.SIZE_SHRINK:
                # artificially limit duration
                self.state.step_count_max = min(self.state.period_short, self.state.step_count_max)
                # if we can shrink
                if self.state.size > 0:
                    # randomly shrink
                    if random.randint(0, 99) > 80:  # noqa: PLR2004
                        self.state.size -= random.randint(1, 5)
                    # also randomly grow a bit
                    if self.state.size < self.state.size_max and random.randint(0, 99) > 90:  # noqa: PLR2004
                        self.state.size += 1  # pragma: no cover
                # make sure we aren't overgrown
                if self.state.size >= self.state.size_max:
                    self.state.size = self.state.size_max
                # also make sure we still exist
                elif self.state.size < 1:
                    self.state.size = 1
                self.state.index_range = self.calc_sequence_range()
            # if we are cycling through colors
            if self.state.current_state & AliveStates.COLOR_CYCLE:
                # artificially limit duration
                self.state.step_count_max = min(self.state.period_short, self.state.step_count_max)
                # randomly cycle through assign colors
                if random.randint(0, 99) > 90:  # noqa: PLR2004
                    for _ in range(random.randint(1, 3)):
                        self.state.pixel_sequence.advance_index()
            # increment step counter
            self.state.step_counter += 1
        # we hit our step goal, randomize next state
        else:
            # states are mutually exclusive bits, can just add one of each
            # for _ in range(random.randint(1, 3)):
            # self.state.current_state = (
            next_state: IntFlag = IntFlag(0)
            speeds = [
                AliveStates.SPEED_STOPPED,
                AliveStates.SPEED_SLOW,
                AliveStates.SPEED_NORMAL,
                AliveStates.SPEED_FAST,
            ]
            speed = speeds[random.randint(0, len(speeds) - 1)]
            if not (speed & self.state.current_state):
                next_state = speed
            else:
                next_state = AliveStates.SPEED_NORMAL
            sizes = [AliveStates.SIZE_SHRINK, AliveStates.SIZE_FIXED, AliveStates.SIZE_GROW]
            size = sizes[random.randint(0, len(sizes) - 1)]
            if not (size & self.state.current_state):
                next_state |= size
            else:
                next_state |= AliveStates.SIZE_FIXED
            colors = [AliveStates.COLOR_FIXED, AliveStates.COLOR_CYCLE]
            color = colors[random.randint(0, len(colors) - 1)]
            if not (color & self.state.current_state):
                next_state |= color
            else:
                next_state |= AliveStates.COLOR_FIXED
            self.state.current_state = next_state
            # reset step counter
            self.state.step_counter = 0
            # set step count to random value
            self.state.step_count_max = random.randint(
                self.controller.virtual_led_count // 10,
                self.controller.virtual_led_count,
            )
            # set delay count randomly
            self.state.delay_count_max = random.randint(6, 15)
            # randomize step size
            self.state.step_size = random.randint(1, 3)
            # randomize fade amount
            self.state.fade_amount = random.randint(80, 192)
            # randomize delays
            if self.state.current_state & AliveStates.SPEED_NORMAL:
                self.state.delay_count_max = random.randint(1, 3)
            elif self.state.current_state & AliveStates.SPEED_SLOW:
                self.state.delay_count_max = random.randint(15, 45)
            elif self.state.current_state & AliveStates.SPEED_FAST:
                self.state.delay_count_max = random.randint(0, 3)
            else:
                self.state.delay_count_max = random.randint(1, 7)
            # calculate affected range
            self.state.index_range = self.calc_range()
            self.state.index_range = self.calc_sequence_range()
        self.assign_pixel()

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {self.state.pixel_sequence.pixel} {self.state.current_state!s}'
