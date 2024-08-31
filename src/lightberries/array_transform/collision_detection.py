"""Perform collision detection on the list of light function objects."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

import numpy as np

from lightberries.pixel import Pixel, PixelColor
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    import lightberries.array_controller
    from lightberries.pixel_sequence import PixelSequence
    from lightberries.state import TransformState

LOGGER = logging.getLogger("lightBerries")


class TransformCollisionDetect(PixelTransform):
    """Perform collision detection on the list of light function objects."""

    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
    ) -> None:
        """Perform collision detection on the list of light function objects.

        Args:
        ----
            controller: Array controller instance
            state: initial state. Defaults to None.
            pixel_sequence: a sequence of pixels

        """
        super().__init__(
            name=TransformCollisionDetect.__name__,
            controller=controller,
        )

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
            pixel_sequence: _description_. Defaults to None.
            state: initial state. Defaults to None.
            kwargs: extra args to the state object

        Returns:
        -------
            list of transforms

        """
        transform = TransformCollisionDetect(controller=controller)
        if state is not None:
            transform.state = state
        if pixel_sequence is not None:
            transform.state.pixel_sequence = pixel_sequence
        TransformCollisionDetect.ACTIVE_TRANSFORMS.append(transform)
        return TransformCollisionDetect.ACTIVE_TRANSFORMS

    def transform(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Perform collision detection on the list of light function objects."""
        found_collision = False
        light_functions = self.controller.function_list
        intersection: int | None = None
        if len(light_functions) > 1:
            for object1 in light_functions:
                object1.state.collision = False
                object1.state.collision_with = None
            for index1, object1 in enumerate(light_functions):
                object1.state.collision = False
                if object1.state.collision_enabled and index1 + 1 < len(light_functions):
                    for object2 in light_functions[index1 + 1 :]:
                        if object2.state.collision_enabled:
                            # this detects the intersection of two self._LightDataObjects'
                            # movements across LEDs

                            _intersection = np.intersect1d(
                                object1.state.index_range,
                                object2.state.index_range,
                            ).astype(np.int32)
                            if len(_intersection) > 0:
                                intersection = int(_intersection[0])
                            if intersection and (
                                object1.state.collision_randomizer is False or random.randint(0, 4) != 0
                            ):
                                object1.state.collision = True
                                object1.state.collision_private = True
                                object1.state.collision_with = object2
                                object1.state.step_last = object1.state.step
                                object1.state.collision_intersection = intersection
                                object2.state.collision_private = True
                                object2.state.collision = True
                                object2.state.collision_with = object1
                                object2.state.step_last = object2.state.step
                                object2.state.collision_intersection = intersection
                                found_collision = True
        explosion_indices: list[int] = []
        explosion_colors: list[Pixel] = []
        if found_collision is True:
            for object1 in light_functions:
                if (
                    object1.state.collision_enabled
                    and object1.state.collision_private is True
                    and isinstance(object1.state.collision_with, PixelTransform)
                ):
                    object2 = object1.state.collision_with
                    if (object1.state.direction * object2.state.direction) < 0:
                        object1.state.direction *= -1
                        object2.state.direction *= -1
                        object1.state.index = int(
                            int(object1.state.collision_intersection + object1.state.direction)
                            % self.controller.virtual_led_count,
                        )
                        object2.state.index = int(
                            int(
                                object2.state.collision_intersection + object2.state.direction,
                            )
                            % self.controller.virtual_led_count,
                        )
                    else:
                        temp = object2.state.step
                        object2.state.step = object1.state.step
                        object1.state.step = temp
                        object1_delta = object1.state.step - object2.state.step
                        object2_delta = object2.state.step - object1.state.step
                        if object1.state.step > object2.state.step:
                            object2_delta += object2.state.direction
                        else:
                            object1_delta += object1.state.direction
                        object1.state.index = (
                            int(object1.state.index + object1_delta) % self.controller.virtual_led_count
                        )
                        object2.state.index = (
                            int(object2.state.index + object2_delta) % self.controller.virtual_led_count
                        )
                    object1.state.index_previous = object1.state.collision_intersection
                    object2.state.index_previous = object2.state.collision_intersection
                    object1.state.collision_private = False
                    object2.state.collision_private = False
                    middle = object1.state.collision_intersection
                    if self.state.explode:
                        if isinstance(
                            object1.state.collision_intersection,
                            np.ndarray,
                        ):
                            middle = object1.state.collision_intersection[
                                len(object1.state.collision_intersection) // 2
                            ]
                        radius = self.controller.real_led_count // 20
                        if radius == 0:
                            radius = 1
                        explosion_indices.append(middle)
                        explosion_colors.append(Pixel(PixelColor.YELLOW))
                        for i in range(1, radius + 1):
                            explosion_indices.append(
                                (middle - i) % self.controller.virtual_led_count,
                            )
                            explosion_colors.append(
                                Pixel(np.array(PixelColor.YELLOW) * ((radius - i) / radius)),
                            )

                            explosion_indices.append(
                                (middle + i) % self.controller.virtual_led_count,
                            )
                            explosion_colors.append(
                                Pixel(np.array(PixelColor.YELLOW) * ((radius - i) / radius)),
                            )
                        self.controller.virtual_led_buffer[explosion_indices] = np.array(explosion_colors)
