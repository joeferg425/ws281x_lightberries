"""Modify LED strings in interesting ways."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from lightberries.exceptions import ControllerError, LightBerryError
from lightberries.pixel_sequence import PixelSequence
from lightberries.state import TransformState

if TYPE_CHECKING:
    from numpy.typing import NDArray

    import lightberries.array_controller

LOGGER = logging.getLogger("lightBerries")


class PixelTransform:
    """Modify LED strings in interesting ways."""

    ALL_TRANSFORMS: ClassVar[dict[str, type[PixelTransform]]] = {}
    ACTIVE_TRANSFORMS: ClassVar[list[PixelTransform]] = []
    _instance_count: ClassVar[int] = 0

    def __init_subclass__(
        cls,
        **kwargs: dict[str, Any],
    ) -> None:
        cls.ALL_TRANSFORMS[cls.__name__.replace("Transform", "")] = cls

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
        name = f"{name}[{self._instance_count}]"
        self.controller = controller
        self._name = name
        self.state = TransformState(
            controller=self.controller,
            pixel_sequence=PixelSequence.default_color_sequence_by_month(),
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

    @staticmethod
    def setup(
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
            pixel_sequence = PixelSequence.default_color_sequence_by_month()
        if state is None:
            state = TransformState(controller=controller, pixel_sequence=pixel_sequence)
        return []

    def transform(self) -> None:
        """Run this array function's transformation."""

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

    def copy(self) -> PixelTransform:
        """Get a copy of this transform.

        Returns
        -------
            a copy of this transform

        """
        transform = PixelTransform(
            controller=self.controller,
            name=self._name,
        )
        transform.state = self.state.copy()
        return transform

    @staticmethod
    def clear_active() -> None:
        """Clear the list of active transforms."""
        PixelTransform.ACTIVE_TRANSFORMS.clear()
