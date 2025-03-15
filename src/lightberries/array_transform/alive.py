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

FAST_SPEED = (25, 65)
MEDIUM_SPEED = (65, 105)
SLOW_SPEED = (105, 145)


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
    def create(  # noqa: C901, PLR0913
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
        *,
        fade_amount: float | None = None,
        size_max: int | None = None,
        step_count_max: int | None = None,
        step_size_max: int | None = None,
        instance_count: int | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: _description_. Defaults to None.
            state: initial state. Defaults to None.
            fade_amount: amount of fade
            size_max: max size of LED pattern
            step_count_max: max duration of effect
            step_size_max: max speed
            instance_count: make n copies of this transform

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
            alive.state.delay_count_max = random.randint(*MEDIUM_SPEED)

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
        if instance_count is None:
            instance_count = random.randint(1, 5)

        TransformFadeOff.create(controller=controller, fade_amount=alive.state.fade_amount)
        transform = None
        # for _ in range(random.randint(2, 5)):
        for _ in range(instance_count):
            if transform is None:
                transform = alive
            else:
                transform = alive.copy()

            # randomize start index
            transform.state.index = alive.get_random_index()
            # randomize direction
            transform.state.direction = alive.get_random_direction()
            transform.state.re_init()
            # copy color sequence
            transform.state.pixel_sequence = alive.state.pixel_sequence.copy()
            # randomize speed
            transform.state.step_size = random.randint(1, transform.state.step_size_max_setting)
            # randomize refresh speed
            transform.state.delay_count_max = random.randint(*MEDIUM_SPEED)
            # randomize initial size
            transform.state.size = random.randint(1, int(transform.state.size_max // 2))
            # start the state at 1
            transform.state.flags = AliveStates.SIZE_GROW  # ThingMoves.METEOR
            # calculate random next state immediately
            transform.state.step_counter = 1000
            transform.state.delay_counter = 1000
            TransformAlive.ACTIVE_TRANSFORMS.append(transform)
            transform.calc_sequence_range()
        TransformAlive.ACTIVE_TRANSFORMS[0].state.active = True
        # add a fade
        return TransformAlive.ACTIVE_TRANSFORMS

    def transform(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Do alive function things."""
        super().transform()
        # track last index
        if self.state.delay_count_reset:
            self.state.delay_counter = 0
            self.advance_step_counter()
        if not self.state.step_count_reset:
            # if in meteor mode
            if self.state.flags & AliveStates.SPEED_NORMAL:
                self.state.step_size = 1
                # randomly change direction
                if random.randint(0, 99) > 95:  # noqa: PLR2004
                    self.state.direction *= -1  # pragma: no cover
                # set next index
                self.advance_index()
            # if in fast meteor mode
            elif self.state.flags & AliveStates.SPEED_FAST:
                # artificially limit duration of this mode
                self.state.step_count_max = min(self.state.period_short, self.state.step_count_max)
                # randomize step size
                self.state.step_size = random.randint(7, 12)
                # set next index
                self.advance_index()
            # if slow meteor
            elif self.state.flags & AliveStates.SPEED_SLOW:
                # set step to 1
                self.state.step_size = 1
                # randomly change direction
                if random.randint(0, 99) > 80:  # noqa: PLR2004
                    self.state.direction *= -1  # pragma: no cover
                # set next index
                self.advance_index()
            # if we are growing
            if self.state.flags & AliveStates.SIZE_GROW:
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
            # if we are shrinking
            elif self.state.flags & AliveStates.SIZE_SHRINK:
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
            # if we are cycling through colors
            if self.state.flags & AliveStates.COLOR_CYCLE:
                # artificially limit duration
                self.state.step_count_max = min(self.state.period_short, self.state.step_count_max)
                # randomly cycle through assigned colors
                if random.randint(0, 99) > 90:  # noqa: PLR2004
                    for _ in range(random.randint(1, 3)):
                        self.state.pixel_sequence.advance_index()
            # increment step counter
            self.state.step_counter += 1
        # we hit our step goal, randomize next state
        else:
            self.state.step_count_reset = False
            self.state.delay_counter = 0
            next_state: IntFlag = IntFlag(0)
            speeds = [
                AliveStates.SPEED_STOPPED,
                AliveStates.SPEED_SLOW,
                AliveStates.SPEED_NORMAL,
                AliveStates.SPEED_FAST,
            ]
            speed = speeds[random.randint(0, len(speeds) - 1)]
            if not (speed & self.state.flags):
                next_state = speed
            else:
                next_state = AliveStates.SPEED_NORMAL
            if random.randint(0, 99) > 70:  # noqa: PLR2004
                sizes = [AliveStates.SIZE_SHRINK, AliveStates.SIZE_FIXED, AliveStates.SIZE_GROW]
                size = sizes[random.randint(0, len(sizes) - 1)]
                if not (size & self.state.flags):
                    next_state |= size
                else:
                    next_state |= AliveStates.SIZE_FIXED
            colors = [AliveStates.COLOR_FIXED, AliveStates.COLOR_CYCLE]
            color = colors[random.randint(0, len(colors) - 1)]
            if not (color & self.state.flags):
                next_state |= color
            else:
                next_state |= AliveStates.COLOR_FIXED
            self.state.flags = next_state
            # reset step counter
            self.state.step_counter = 0
            # set step count to random value
            self.state.step_count_max = random.randint(
                self.controller.virtual_led_count // 10,
                self.controller.virtual_led_count,
            )
            # set delay count randomly
            self.state.delay_count_max = random.randint(*MEDIUM_SPEED)
            # randomize step size
            self.state.step_size = random.randint(1, 3)
            # randomize fade amount
            self.state.fade_amount = random.randint(80, 192)
            # randomize delays
            if self.state.flags & AliveStates.SPEED_NORMAL:
                self.state.delay_count_max = random.randint(*MEDIUM_SPEED)
            elif self.state.flags & AliveStates.SPEED_SLOW:
                self.state.delay_count_max = random.randint(*SLOW_SPEED)
            elif self.state.flags & AliveStates.SPEED_FAST:
                self.state.delay_count_max = random.randint(*FAST_SPEED)
            else:
                self.state.delay_count_max = random.randint(*MEDIUM_SPEED)
            # calculate affected range
        self.calc_sequence_range()
        self.assign_pixel_to_array()

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {self.state.pixel_sequence.pixel} {self.state.flags!s}'
