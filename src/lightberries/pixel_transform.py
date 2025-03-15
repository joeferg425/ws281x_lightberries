"""Modify LED strings in interesting ways."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from lightberries.base.constants import SHAPE_2D
from lightberries.base.exceptions import ControllerError, LightBerryError
from lightberries.base.logger import LOGGER
from lightberries.base.state import TransformState
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from numpy.typing import NDArray  # pragma: no cover

    import lightberries.array_controller  # pragma: no cover


class PixelTransform:
    """Modify LED strings in interesting ways."""

    ALL_TRANSFORMS: ClassVar[dict[str, type[PixelTransform]]] = {}
    ACTIVE_TRANSFORMS: ClassVar[list[PixelTransform]] = []
    _instance_count: ClassVar[int] = 0

    def __init_subclass__(
        cls,
        **kwargs: dict[str, Any],
    ) -> None:
        cls_name = cls.__name__.replace("Transform", "")
        if cls_name not in (
            "Overlay",
            "Array",
            "Off",
            "FadeOff",
            "CollisionDetect",
            "None",
            "Fade",
            "Blink",
            "Twinkle",
        ):
            cls.ALL_TRANSFORMS[cls_name] = cls

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        name: str | None = None,
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
        ----
            name: name of the function
            controller: Array controller instance
            pixel_sequence: a pixel sequence
            state: initial state. Defaults to None.
            kwargs: args for patterns

        """
        if name is None:
            name = PixelTransform.__name__
        PixelTransform._instance_count += 1
        self._instance_id = PixelTransform._instance_count
        self.controller = controller
        self._name = name
        self.state = TransformState(
            controller=self.controller,
            pixel_sequence=PixelSequence.get_monthly_color_sequence(),
        )

        LOGGER.debug("Transform: %s", self)

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {self.state.pixel_sequence.pixel}'

    def __repr__(
        self,
    ) -> str:
        """Return a string representation of this class(not de-serializable).

        Returns
        -------
            string representation of this class(not de-serializable)

        """
        return f"<{PixelTransform.__name__}> {self!s}"

    def __eq__(self, value: object) -> bool:
        if isinstance(value, PixelTransform):
            return self._instance_id == value.instance_id
        return False

    @property
    def name(self) -> str:
        """Get name of transform."""
        return self._name

    @property
    def instance_id(self) -> int:
        """Get id of transform."""
        return self._instance_id

    @staticmethod
    def create(
        controller: lightberries.array_controller.ArrayController,
        pixel_sequence: PixelSequence | None = None,
        state: TransformState | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            controller: Array controller instance
            pixel_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.

        Returns:
        -------
            list of transforms

        """
        if pixel_sequence is None:
            pixel_sequence = PixelSequence.get_monthly_color_sequence()
        if state is None:
            state = TransformState(controller=controller, pixel_sequence=pixel_sequence)
        return []

    @staticmethod
    def get_random_direction() -> int:
        """Get a random one or negative one to determine direction for light functions.

        Returns
        -------
            one or negative one, randomly

        """
        return [-1, 1][random.randint(0, 1)]

    @staticmethod
    def get_random_boolean() -> bool:
        """Get a random true or false value.

        Returns
        -------
            True or False, randomly

        """
        return [True, False][random.randint(0, 1)]

    def transform(self) -> None:
        """Run this array function's transformation."""
        self.advance_delay_counter()
        LOGGER.debug("%s", self)

    # def calc_range(
    #     self,
    # ) -> NDArray[np.int32]:
    #     """Calculate index range.

    #     Args:
    #     ----
    #         indexFrom: from index
    #         indexTo: to index

    #     Returns:
    #     -------
    #         array of indices

    #     """
    #     self.state.index_range = np.arange(
    #         self.state.index_no_modulo + self.state.direction,
    #         self.state.index_next_no_modulo + self.state.direction,
    #         self.state.direction,
    #         dtype=np.int32,
    #     )
    #     modulo = np.where(self.state.index_range >= (self.controller.virtual_led_count))[0]
    #     if len(modulo) != 0:
    #         for _ in range(5):
    #             self.state.index_range[modulo] -= self.controller.virtual_led_count
    #             if self.state.index_bounce and len(modulo):
    #                 self.state.index_range[modulo] += 1
    #                 self.state.index_range[modulo] *= -1
    #                 self.state.index_range[modulo] += self.controller.virtual_led_count - 1
    #             modulo = np.where(
    #                 self.state.index_range >= (self.controller.virtual_led_count),
    #             )[0]
    #             if len(modulo) == 0:
    #                 break
    #     modulo = np.where(self.state.index_range < 0)[0]
    #     if len(modulo) != 0:
    #         for _ in range(5):
    #             self.state.index_range[modulo] += self.controller.virtual_led_count
    #             if self.state.index_bounce and len(modulo):
    #                 self.state.index_range[modulo] -= 1
    #                 self.state.index_range[modulo] *= -1
    #                 self.state.index_range[modulo] += self.controller.virtual_led_count - 1
    #             modulo = np.where(self.state.index_range < 0)[0]
    #             if len(modulo) == 0:
    #                 break
    #     return self.state.index_range

    def calc_sequence_range(  # noqa: C901
        self,
    ) -> NDArray[np.int32]:
        """Calculate index range.

        Args:
        ----
            indexFrom: from index
            indexTo: to index

        Returns:
        -------
            array of indices

        """
        reverse = False
        if self.state.direction != self.state.direction_previous:
            self.state.index_range = np.arange(
                self.state.index_next_no_modulo - (self.state.direction_previous * (self.state.step_size)),
                self.state.index_no_modulo
                - (self.state.direction_previous * (self.state.step_size + self.state.size - 1)),
                -self.state.direction_previous,
                dtype=np.int32,
            )
        else:
            self.state.index_range = np.arange(
                self.state.index_next_no_modulo - (self.state.direction * (self.state.step_size)),
                self.state.index_no_modulo - (self.state.direction * (self.state.step_size + self.state.size - 1)),
                -self.state.direction,
                dtype=np.int32,
            )
        modulo = np.where(self.state.index_range >= (self.controller.virtual_led_count))[0]
        if len(modulo) != 0:
            reverse = True
            for _ in range(5):
                self.state.index_range[modulo] -= self.controller.virtual_led_count
                if (self.state.index_bounce or self.state.index_bounce) and len(modulo):
                    self.state.index_range[modulo] += 1
                    self.state.index_range[modulo] *= -1
                    self.state.index_range[modulo] += self.controller.virtual_led_count - 1
                modulo = np.where(
                    self.state.index_range >= (self.controller.virtual_led_count),
                )[0]
                if len(modulo) == 0:
                    break
        modulo = np.where(self.state.index_range < 0)[0]
        if len(modulo) != 0:
            reverse = True
            for _ in range(5):
                self.state.index_range[modulo] += self.controller.virtual_led_count
                if self.state.index_bounce and len(modulo):
                    self.state.index_range[modulo] -= 1
                    self.state.index_range[modulo] *= -1
                    self.state.index_range[modulo] += self.controller.virtual_led_count - 1
                modulo = np.where(self.state.index_range < 0)[0]
                if len(modulo) == 0:
                    break
        if reverse and (
            self.state.index_bounce
            and (
                self.state.index + (self.state.step_size * self.state.direction) >= self.controller.virtual_led_count
                or self.state.index + (self.state.step_size * self.state.direction) <= 0
            )
        ):
            self.state.direction *= -1

        return self.state.index_range

    def get_random_index(
        self,
    ) -> int:
        """Retrieve a random Pixel index.

        Returns
        -------
            a random index into the virtual LED buffer

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            return random.randint(0, (self.controller.virtual_led_count - 1))
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def get_random_indices(
        self,
        count: int,
    ) -> NDArray[np.int32]:
        """Retrieve a random list of Pixel indices.

        Args:
        ----
            count: the number of random indices to get

        Returns:
        -------
            a list of random indices into the virtual LED buffer

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightBerryException: if propagating an exception
            LightControlException: if something bad happens

        """
        try:
            return np.array([self.get_random_index() for _ in range(count)], dtype=np.int32)
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise ControllerError from ex

    def copy(self) -> PixelTransform:
        """Get a copy of this transform.

        Returns
        -------
            a copy of this transform

        """
        transform = type(self)(
            controller=self.controller,
        )
        transform.state = self.state.copy()
        # instantiation incremented the counter above, set the value here
        transform._instance_id = transform._instance_count  # type: ignore  # noqa: PGH003, SLF001
        return transform

    @staticmethod
    def clear_active() -> None:
        """Clear the list of active transforms."""
        PixelTransform.ACTIVE_TRANSFORMS.clear()

    def advance_delay_counter(self) -> None:
        """Advance delay counter, advance step when done delaying."""
        self.state.delay_counter += 1
        self.state.delay_count_reset = False
        # check delay counter, update index when it hits max
        if self.state.delay_counter >= self.state.delay_count_max:
            # reset delay counter
            self.state.delay_counter = 0
            self.state.delay_count_reset = True

    def advance_step_counter(self) -> None:
        """Advance delay counter."""
        self.state.step_counter += 1
        self.state.step_count_reset = False
        # check delay counter, update index when it hits max
        if self.state.step_counter >= self.state.step_count_max:
            # reset delay counter
            self.state.step_counter = 0
            self.state.step_count_reset = True

    def advance_index(self) -> None:  # noqa: PLR0912
        """Calculate next transform indices."""
        self.state.index_previous = self.state.index
        self.state.index_no_modulo = self.state.index + (self.state.step_size * self.state.direction)
        self.state.index_next_no_modulo = self.state.index_no_modulo + (self.state.step_size * self.state.direction)
        self.state.direction_previous = self.state.direction
        if self.state.index_no_modulo > (self.controller.virtual_led_count - 1):
            if self.state.index_bounce is True:
                self.state.direction *= -1
                self.state.index -= self.state.index_no_modulo % (self.controller.virtual_led_count - 1)
            else:
                self.state.index = self.state.index_no_modulo % self.controller.virtual_led_count
        elif self.state.index_no_modulo < 0:
            if self.state.index_bounce is True:
                self.state.direction *= -1
            else:
                self.state.index = self.state.index_no_modulo % self.controller.virtual_led_count
        else:
            self.state.index = self.state.index_no_modulo
        if self.state.index_next_no_modulo > (self.controller.virtual_led_count - 1):
            if self.state.index_bounce is True:
                self.state.index_next -= self.state.index_next_no_modulo % (self.controller.virtual_led_count - 1)
            else:
                self.state.index_next = self.state.index_next_no_modulo % self.controller.virtual_led_count
        elif self.state.index_next_no_modulo < 0:
            if self.state.index_bounce is True:
                self.state.index_next = self.state.index_next_no_modulo * -1
            else:
                self.state.index_next = self.state.index_next_no_modulo % self.controller.virtual_led_count
        else:
            self.state.index_next = self.state.index_next_no_modulo
        self.state.index_updated = self.state.index_previous != self.state.index
        self.calc_sequence_range()

    # def assign_pixel(self) -> None:
    #     """Assign colors to indices."""
    #     if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
    #         self.controller.virtual_led_buffer[self.state.index_range] = self.state.pixel_sequence.pixel
    #     else:
    #         self.controller.virtual_led_buffer[
    #             np.where(
    #                 self.controller.virtual_led_index_buffer == self.state.index_range,
    #             )
    #         ] = self.state.pixel_sequence.pixel

    def assign_pixel_to_array(self) -> None:
        """Assign colors to indices."""
        if len(self.controller.virtual_led_buffer.shape) == SHAPE_2D:
            self.controller.virtual_led_buffer[self.state.index_range] = self.state.pixel_sequence.pixel
        else:
            self.controller.virtual_led_buffer[
                np.where(
                    self.controller.virtual_led_index_buffer == self.state.index_range,
                )
            ] = self.state.pixel_sequence.array
