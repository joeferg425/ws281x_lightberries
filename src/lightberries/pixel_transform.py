"""Modify LED strings in interesting ways."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from lightberries.array_sequence.base import ArraySequence
from lightberries.exceptions import ControllerError, LightBerryError
from lightberries.pixel import LEDOrder, Pixel
from lightberries.state import TransformState

if TYPE_CHECKING:
    from numpy.typing import NDArray

    import lightberries.array_controller

LOGGER = logging.getLogger("lightBerries")


class PixelTransform:
    """Modify LED strings in interesting ways."""

    ALL_TRANSFORMS: ClassVar[dict[str, type[PixelTransform]]] = {}

    def __init_subclass__(
        cls,
        **kwargs: dict[str, Any],
    ) -> None:
        cls.ALL_TRANSFORMS[cls.__name__.replace("Transform", "")] = cls

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        name: str | None = None,
        state: TransformState | None = None,
        **kwargs: dict[str, Any],  # noqa: ARG002
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
        ----
            name: name of the function
            controller: Array controller instance
            state: initial state. Defaults to None.
            kwargs: args for patterns

        """
        if name is None:
            name = PixelTransform.__name__
        self.controller = controller
        self._name = name
        if state is None:
            self.state = TransformState(controller=self.controller)
        else:
            self.state = state

        LOGGER.debug("Transform: %s", name)

    def __str__(
        self,
    ) -> str:
        return f'[{self.state.index}]: "{self._name}" {Pixel(self.state.color, LEDOrder.RGB)}'

    def __repr__(
        self,
    ) -> str:
        """Return a string representation of this class(not de-serializable).

        Returns
        -------
            string representation of this class(not de-serializable)

        """
        return f"<{PixelTransform.__name__}> {self!s}"

    def setup(
        self,
        color_sequence: NDArray[np.int32] | None = None,
        state: TransformState | None = None,
    ) -> list[PixelTransform]:
        """Configure the transformation.

        Args:
        ----
            color_sequence: color sequence. Defaults to None.
            state: initial state. Defaults to None.

        Returns:
        -------
            list of transforms

        """
        if state is not None:
            self.state = state
        self.state.color_sequence = ArraySequence.default_color_sequence_by_month()
        if color_sequence is not None:
            self.state.color_sequence = color_sequence
        return []

    def transform(self) -> None:
        """Run this array function's transformation."""

    @property
    def color_sequence(
        self,
    ) -> NDArray[np.int32]:
        """Return the color sequence.

        Returns
        -------
            the color sequence

        """
        return self.state.color_sequence

    @color_sequence.setter
    def color_sequence(
        self,
        color_sequence: NDArray[np.int32],
    ) -> None:
        """Set the color sequence.

        Args:
        ----
            color_sequence: desired color sequence

        """
        self.state.color_sequence = color_sequence
        self.state.color_sequence_count = len(self.state.color_sequence)
        self.state.color_sequence_index = 0
        self.state.color = self.state.color_sequence[0]

    @property
    def color_sequence_count(
        self,
    ) -> int:
        """Get the color sequence count.

        Returns
        -------
            the color sequence count

        """
        return self.state.color_sequence_count

    @color_sequence_count.setter
    def color_sequence_count(
        self,
        color_sequence_count: int,
    ) -> None:
        """Setter for color sequence count.

        Args:
        ----
            color_sequence_count: the number of colors in the sequence

        """
        self.state.color_sequence_count = color_sequence_count

    @property
    def color_sequence_index(
        self,
    ) -> int:
        """Color sequence index.

        Returns
        -------
            the current color sequence index

        """
        return self.state.color_sequence_index

    @color_sequence_index.setter
    def color_sequence_index(
        self,
        color_sequence_index: int,
    ) -> None:
        """Color sequence index.

        Args:
        ----
            color_sequence_index: the current index being used for the color sequence

        """
        self.state.color_sequence_index = color_sequence_index

    @property
    def color_sequence_next(
        self,
    ) -> NDArray[np.int32]:
        """Get the next color in the sequence.

        Returns
        -------
            the next color in the sequence

        """
        self.state.color_sequence_index += 1
        if self.state.color_sequence_index >= self.state.color_sequence_count:
            self.state.color_sequence_index = 0
        return self.state.color_sequence[self.state.color_sequence_index]

    def update_array_index(
        self,
    ) -> None:
        """Update the object index."""
        self.state.index_previous = self.state.index
        self.calc_range()
        self.state.index_previous = self.state.index
        self.state.index = int(self.state.index_range[-1])
        self.state.index_updated = True

    def calc_range(
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
        new_index_no_modulo = self.state.index + (self.state.step * self.state.direction)
        self.state.index_range = np.array(
            list(
                range(
                    self.state.index_previous + self.state.direction,
                    new_index_no_modulo + self.state.direction,
                    self.state.direction,
                ),
            ),
        )
        modulo = np.where(self.state.index_range >= (self.controller.virtual_led_count))[0]
        while len(modulo):
            self.state.index_range[modulo] -= self.controller.virtual_led_count
            modulo = np.where(
                self.state.index_range >= (self.controller.virtual_led_count),
            )[0]
        modulo = np.where(self.state.index_range < 0)[0]
        while len(modulo):
            self.state.index_range[modulo] += self.controller.virtual_led_count
            modulo = np.where(self.state.index_range < 0)[0]
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

    def get_random_direction(self) -> int:
        """Get a random one or negative one to determine direction for light functions.

        Returns
        -------
            one or negative one, randomly

        """
        return [-1, 1][random.randint(0, 1)]

    def get_random_boolean(self) -> bool:
        """Get a random true or false value.

        Returns
        -------
            True or False, randomly

        """
        return [True, False][random.randint(0, 1)]
