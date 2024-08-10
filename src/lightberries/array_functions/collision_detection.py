import random
from typing import Any

import numpy as np

import lightberries.array_controller
from lightberries.array_functions.base import ArrayFunction
from lightberries.exceptions import FunctionError, LightBerryError
from lightberries.pixel import PixelColors


class ArrayFunctionCollisionDetection(ArrayFunction):
    def __init__(
        self,
        controller: lightberries.array_controller.ArrayController,
        color_sequence: np.ndarray[Any, np.signedinteger[np._32Bit]] = None,
    ) -> None:
        """Perform collision detection on the list of light function objects.

        Args:
            collision: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        super().__init__(
            name=ArrayFunctionCollisionDetection.__class__.__name__,
            controller=controller,
            color_sequence=color_sequence,
        )

    def run(self):
        try:
            found_collision = False
            light_functions = self.controller.functionList
            if len(light_functions) > 1:
                for object1 in light_functions:
                    object1.state.collision = False
                    object1.state.collision_with = None
                for index1, object1 in enumerate(light_functions):
                    object1.state.collision = False
                    if object1.state.collision_enabled:
                        if index1 + 1 < len(light_functions):
                            for object2 in light_functions[index1 + 1 :]:
                                if object2.state.collision_enabled:
                                    if isinstance(
                                        object1.state.index_range, np.ndarray
                                    ) and isinstance(
                                        object2.state.index_range, np.ndarray
                                    ):
                                        # this detects the intersection of two self._LightDataObjects'
                                        # movements across LEDs
                                        intersection = np.intersect1d(
                                            object1.state.index_range,
                                            object2.state.index_range,
                                        )
                                        if len(intersection) > 0 and (
                                            object1.state.collision_randomizer is False
                                            or random.randint(0, 4) != 0
                                        ):
                                            object1.state.collision = True
                                            object1.state.collision_private = True
                                            object1.state.collision_with = object2
                                            object1.state.step_last = object1.state.step
                                            object1.state.collision_intersection = (
                                                intersection
                                            )
                                            object2.state.collision_private = True
                                            object2.state.collision = True
                                            object2.state.collision_with = object1
                                            object2.state.step_last = object2.state.step
                                            object2.state.collision_intersection = (
                                                intersection.copy()
                                            )
                                            found_collision = True
            explosionIndices = []
            explosionColors = []
            if found_collision is True:
                for object1 in light_functions:
                    if object1.state.collision_enabled:
                        if object1.state.collision_private is True:
                            if isinstance(object1.state.collision_with, ArrayFunction):
                                object2 = object1.state.collision_with
                                # previous = int(meteor.step)
                                if (
                                    object1.state.direction * object2.state.direction
                                ) < 0:
                                    object1.state.direction *= -1
                                    object2.state.direction *= -1
                                    object1.state.index = int(
                                        int(
                                            object1.state.collision_intersection[0]
                                            + object1.state.direction
                                        )
                                        % self.controller.virtualLEDCount
                                    )
                                    object2.state.index = int(
                                        int(
                                            object2.state.collision_intersection[0]
                                            + object2.state.direction
                                        )
                                        % self.controller.virtualLEDCount
                                    )
                                else:
                                    temp = object2.state.step
                                    object2.state.step = object1.state.step
                                    object1.state.step = temp
                                    object1_delta = (
                                        object1.state.step - object2.state.step
                                    )
                                    object2_delta = (
                                        object2.state.step - object1.state.step
                                    )
                                    if object1.state.step > object2.state.step:
                                        object2_delta += object2.state.direction
                                    else:
                                        object1_delta += object1.state.direction
                                    object1.state.index = (
                                        int(object1.state.index + object1_delta)
                                        % self.controller.virtualLEDCount
                                    )
                                    object2.state.index = (
                                        int(object2.state.index + object2_delta)
                                        % self.controller.virtualLEDCount
                                    )
                                object1.state.index_previous = (
                                    object1.state.collision_intersection
                                )
                                object2.state.index_previous = (
                                    object2.state.collision_intersection
                                )
                                object1.state.collision_private = False
                                object2.state.collision_private = False
                                if self.state.explode:
                                    if isinstance(
                                        object1.state.collision_intersection,
                                        np.ndarray,
                                    ):
                                        middle = object1.state.collision_intersection[
                                            len(object1.state.collision_intersection)
                                            // 2
                                        ]
                                    radius = self.controller.realLEDCount // 20
                                    if radius == 0:
                                        radius = 1
                                    explosionIndices.append(middle)
                                    explosionColors.append(PixelColors.YELLOW.array)
                                    for i in range(1, radius + 1):
                                        explosionIndices.append(
                                            (middle - i)
                                            % self.controller.virtualLEDCount,
                                        )
                                        explosionColors.append(
                                            PixelColors.YELLOW.array
                                            * ((radius - i) / radius),
                                        )

                                        explosionIndices.append(
                                            (middle + i)
                                            % self.controller.virtualLEDCount,
                                        )
                                        explosionColors.append(
                                            PixelColors.YELLOW.array
                                            * ((radius - i) / radius),
                                        )
                                    self.controller.virtualLEDBuffer[
                                        explosionIndices
                                    ] = np.array((explosionColors))
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex
