from __future__ import annotations
import random
from typing import Any, Callable, ClassVar
import numpy as np
import logging
from lightberries.array_functions import ArrayFunction
import lightberries.matrix_controller
from lightberries.exceptions import LightBerryError, FunctionError
from lightberries.pixel import PixelColors
from math import ceil
from enum import IntEnum

LOGGER = logging.getLogger("lightBerries")


class EyeMoveType(IntEnum):
    """Enumeration of types of LED fade for use in functions."""

    MOVE = 0
    TWITCH = 1
    BLINK = 2
    BLINKED = 3


class MatrixFunction(ArrayFunction):
    """This class defines everything necessary to modify LED patterns in interesting ways."""

    Controller: ClassVar["lightberries.matrix_controller.MatrixController"]

    def __init__(
        self,
        matrixController: "lightberries.matrix_controller.MatrixController",
        funcPointer: Callable,
        colorSequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
            funcPointer: a function pointer that updates LEDs in the LightController object.
            colorSequence: a sequence of RGB values.
        """
        super().__init__(matrixController, funcPointer, colorSequence)

        self.rowIndex: int = 0
        self.rowIndexLast: int = 0
        self.rowRange: list[int] = []
        self.columnIndex: int = 0
        self.columnIndexLast: int = 0
        self.columnRange: list[int] = []
        self.rowDirection: int = 1
        self.columnDirection: int = 1
        self.rowStep: int = 1
        self.columnStep: int = 1

    @staticmethod
    def functionMatrixFadeOff(
        fade: "ArrayFunction",
    ) -> None:
        """Fade all Pixels toward OFF.

        Args:
            fade: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            ArrayFunction.Controller.virtualLEDBuffer[:, :] = (
                ArrayFunction.Controller.virtualLEDBuffer * (1 - fade._fade_amount)
            )
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryError:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionError from ex

    @staticmethod
    def functionMatrixFade(
        fade: "ArrayFunction",
    ) -> None:
        """Fade all Pixels toward OFF.

        Args:
            fade: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            _fadeAmount = ceil(fade._fade_amount * 256)
            if _fadeAmount < 0:
                _fadeAmount = 1
            elif _fadeAmount > 255:
                _fadeAmount = 255
            for x in range(ArrayFunction.Controller.realLEDYaxisRange):
                for y in range(ArrayFunction.Controller.realLEDXaxisRange):
                    for rgbIndex in range(len(fade._color)):
                        if (
                            ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex]
                            != fade._color[rgbIndex]
                        ):
                            if (
                                ArrayFunction.Controller.virtualLEDBuffer[
                                    x, y, rgbIndex
                                ]
                                - _fadeAmount
                                > fade._color[rgbIndex]
                            ):
                                ArrayFunction.Controller.virtualLEDBuffer[
                                    x, y, rgbIndex
                                ] -= _fadeAmount
                            elif (
                                ArrayFunction.Controller.virtualLEDBuffer[
                                    x, y, rgbIndex
                                ]
                                + _fadeAmount
                                < fade._color[rgbIndex]
                            ):
                                ArrayFunction.Controller.virtualLEDBuffer[
                                    x, y, rgbIndex
                                ] += _fadeAmount
                            else:
                                ArrayFunction.Controller.virtualLEDBuffer[
                                    x, y, rgbIndex
                                ] = fade._color_next[rgbIndex]
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionMatrixColorFlux(
        flux: "MatrixFunction",
    ) -> None:
        """

        Args:
            flux: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            roll_index = 1
            if flux._delay_counter >= flux._delay_count_max:
                MatrixFunction.Controller.virtualLEDBuffer[:, :, 0] = np.roll(
                    MatrixFunction.Controller.virtualLEDBuffer[:, :, 0],
                    random.randint(-1, 0),
                    roll_index,
                )
                MatrixFunction.Controller.virtualLEDBuffer[:, :, 1] = np.roll(
                    MatrixFunction.Controller.virtualLEDBuffer[:, :, 1],
                    random.randint(-1, 0),
                    roll_index,
                )
                MatrixFunction.Controller.virtualLEDBuffer[:, :, 2] = np.roll(
                    MatrixFunction.Controller.virtualLEDBuffer[:, :, 2],
                    random.randint(-1, 0),
                    roll_index,
                )
                flux._delay_counter = 0
            flux._delay_counter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionMatrixMarquee(
        marquee: "MatrixFunction",
    ) -> None:
        """

        Args:
            marquee: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            roll_index = 0
            if marquee._delay_counter >= marquee._delay_count_max:
                MatrixFunction.Controller.virtualLEDBuffer = np.roll(
                    MatrixFunction.Controller.virtualLEDBuffer,
                    -1,
                    roll_index,
                )
                marquee._delay_counter = 0
            marquee._delay_counter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionMatrixEye(
        eye: "MatrixFunction",
    ) -> None:
        """

        Args:
            eye: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            _min = 1
            _max = 1
            if eye._delay_counter >= eye._delay_count_max:
                if eye._state == EyeMoveType.MOVE.value:
                    eye.rowIndexLast = eye.rowIndex
                    eye.rowIndex += random.randint(
                        -int(eye.Controller.realLEDXaxisRange / 2),
                        int(eye.Controller.realLEDXaxisRange / 2),
                    )
                    eye.columnIndexLast = eye.columnIndex
                    eye.columnIndex += random.randint(
                        -int(eye.Controller.realLEDYaxisRange / 2),
                        int(eye.Controller.realLEDYaxisRange / 2),
                    )
                    if eye.rowIndex < _min:
                        eye.rowIndex = _min
                    elif eye.rowIndex >= eye.Controller.realLEDXaxisRange - _max:
                        eye.rowIndex = eye.Controller.realLEDXaxisRange - _max - 1
                    if eye.columnIndex < _min:
                        eye.columnIndex = _min
                    elif eye.columnIndex >= eye.Controller.realLEDYaxisRange - _max:
                        eye.columnIndex = eye.Controller.realLEDYaxisRange - _max - 1

                    eye._delay_count_max = random.randint(0, 9)
                    if eye._delay_count_max >= 3:
                        eye._delay_count_max = random.randint(5, 20)
                    elif eye._delay_count_max >= 8:
                        eye._delay_count_max = random.randint(50, 100)
                    eye._delay_count_max = random.randint(0, 30)
                    r = random.randint(0, 4)
                    if r == 3:
                        eye._state = EyeMoveType.TWITCH.value
                    elif r == 4:
                        eye._state = EyeMoveType.BLINK.value
                elif eye._state == EyeMoveType.TWITCH.value:
                    r = eye.rowIndex
                    eye.rowIndex = eye.rowIndexLast
                    eye.rowIndexLast = r
                    r = eye.columnIndex
                    eye.columnIndex = eye.columnIndexLast
                    eye.columnIndexLast = r
                    eye._delay_count_max = random.randint(0, 5)
                    r = random.randint(0, 4)
                    if r == 3:
                        eye._state = EyeMoveType.MOVE.value
                    elif r == 4:
                        eye._state = EyeMoveType.BLINK.value
                elif eye._state == EyeMoveType.BLINK.value:
                    eye._delay_count_max = 2
                    if eye._step_counter > 1:
                        r = random.randint(0, 1)
                        if r == 0:
                            eye._state = EyeMoveType.MOVE.value
                            eye._step_counter = 0
                        elif r == 1:
                            eye._state = EyeMoveType.TWITCH.value
                            eye._step_counter = 0
                    else:
                        eye._state = EyeMoveType.BLINKED.value
                    eye._step_counter += 1
                elif eye._state == EyeMoveType.BLINKED.value:
                    eye._state = EyeMoveType.BLINK.value

                eye.Controller.virtualLEDBuffer *= 0

                if eye._state == EyeMoveType.BLINK.value:
                    xy = (tuple(eye.rowRange), tuple(eye.columnRange))
                    eye.Controller.virtualLEDBuffer[xy] = PixelColors.RED.array
                elif eye._state != EyeMoveType.BLINKED.value:
                    eye._size = 3
                    x = (
                        np.round(
                            np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * eye._size)))
                            * (eye._size)
                        ).astype(dtype=np.int32)
                        + eye.rowIndex
                    )
                    xi = np.where((x >= eye.Controller.realLEDYaxisRange) | (x < 0))[0]
                    y = (
                        np.round(
                            np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * eye._size)))
                            * (eye._size)
                        ).astype(dtype=np.int32)
                        + eye.columnIndex
                    )
                    yi = np.where((y >= eye.Controller.realLEDXaxisRange) | (y < 0))[0]
                    if len(xi) > 0 and len(yi) > 0:
                        i = np.concatenate((xi, yi))
                    elif len(xi) > 0:
                        i = xi
                    else:
                        i = yi
                    if len(i) > 0:
                        x = np.delete(x, i)
                        y = np.delete(y, i)
                    # xy = (tuple(x), tuple(y))
                    # eye.Controller.virtualLEDBuffer[xy] = PixelColors.RED.array
                    eye.rowRange = list(x)
                    eye.columnRange = list(y)

                    eye._size = 4
                    x = (
                        np.round(
                            np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * eye._size)))
                            * (eye._size)
                        ).astype(dtype=np.int32)
                        + eye.rowIndex
                    )
                    xi = np.where((x >= eye.Controller.realLEDYaxisRange) | (x < 0))[0]
                    y = (
                        np.round(
                            np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * eye._size)))
                            * (eye._size)
                        ).astype(dtype=np.int32)
                        + eye.columnIndex
                    )
                    yi = np.where((y >= eye.Controller.realLEDXaxisRange) | (y < 0))[0]
                    if len(xi) > 0 and len(yi) > 0:
                        i = np.concatenate((xi, yi))
                    elif len(xi) > 0:
                        i = xi
                    else:
                        i = yi
                    if len(i) > 0:
                        x = np.delete(x, i)
                        y = np.delete(y, i)
                    # xy = (tuple(x), tuple(y))
                    # eye.Controller.virtualLEDBuffer[xy] = PixelColors.RED.array
                    eye.rowRange.extend(list(x))
                    eye.columnRange.extend(list(y))

                    x = np.array(
                        [
                            eye.rowIndex - 2,
                            eye.rowIndex - 2,
                            eye.rowIndex + 2,
                            eye.rowIndex + 2,
                        ]
                    )
                    xi = np.where((x >= eye.Controller.realLEDYaxisRange) | (x < 0))[0]
                    y = np.array(
                        [
                            eye.columnIndex - 2,
                            eye.columnIndex + 2,
                            eye.columnIndex - 2,
                            eye.columnIndex + 2,
                        ]
                    )
                    yi = np.where((y >= eye.Controller.realLEDXaxisRange) | (y < 0))[0]
                    if len(xi) > 0 and len(yi) > 0:
                        i = np.concatenate((xi, yi))
                    elif len(xi) > 0:
                        i = xi
                    else:
                        i = yi
                    if len(i) > 0:
                        x = np.delete(x, i)
                        y = np.delete(y, i)
                    # xy = (tuple(x), tuple(y))
                    # eye.Controller.virtualLEDBuffer[xy] = PixelColors.RED.array
                    eye.rowRange.extend(list(x))
                    eye.columnRange.extend(list(y))

                    xy = (tuple(eye.rowRange), tuple(eye.columnRange))
                    eye.Controller.virtualLEDBuffer[xy] = PixelColors.RED.array

                eye._delay_counter = 0
            eye._delay_counter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionMatrixBounce(
        bounce: "MatrixFunction",
    ) -> None:
        """

        Args:
            bounce: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            _min = 1
            _max = 1
            if bounce._delay_counter >= bounce._delay_count_max:
                bounce.rowIndex += bounce.rowDirection * bounce.rowStep
                bounce.columnIndex += bounce.columnDirection * bounce.columnStep
                if bounce.rowIndex < _min:
                    bounce.rowIndex = _min
                    bounce.rowDirection *= -1
                    bounce.rowStep = random.randint(1, 2)
                    bounce._delay_count_max = random.randint(1, 5)
                    if bounce._color_cycle and random.randint(0, 10) >= 7:
                        bounce._color = bounce.color_sequence_next
                elif bounce.rowIndex >= bounce.Controller.realLEDXaxisRange - _max:
                    bounce.rowIndex = bounce.Controller.realLEDXaxisRange - _max - 1
                    bounce.rowDirection *= -1
                    bounce.rowStep = random.randint(1, 2)
                    bounce._delay_count_max = random.randint(1, 5)
                    if bounce._color_cycle and random.randint(0, 10) >= 7:
                        bounce._color = bounce.color_sequence_next
                if bounce.columnIndex < _min:
                    bounce.columnIndex = _min
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce._delay_count_max = random.randint(1, 5)
                    if bounce._color_cycle and random.randint(0, 10) >= 7:
                        bounce._color = bounce.color_sequence_next
                elif bounce.columnIndex >= bounce.Controller.realLEDYaxisRange - _max:
                    bounce.columnIndex = bounce.Controller.realLEDYaxisRange - _max - 1
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce._delay_count_max = random.randint(1, 5)
                    if bounce._color_cycle and random.randint(0, 10) >= 7:
                        bounce._color = bounce.color_sequence_next
                bounce._delay_counter = 0
            bounceRange = ((bounce.columnIndex), (bounce.rowIndex))
            if len(ArrayFunction.Controller.virtualLEDBuffer.shape) == 2:
                ArrayFunction.Controller.virtualLEDBuffer[bounceRange] = bounce._color
            else:
                ArrayFunction.Controller.virtualLEDBuffer[bounceRange] = bounce._color
            bounce._delay_counter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionMatrixFireworks(
        firework: "MatrixFunction",
    ) -> None:
        """
        Args:
            firework: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            if firework._delay_counter >= firework._delay_count_max:
                if firework._size < firework._size_max:
                    firework._size += firework._step
                else:
                    firework._size = 1
                    firework.rowIndex = random.randint(
                        0, firework.Controller.realLEDYaxisRange - 1
                    )
                    firework.columnIndex = random.randint(
                        0, firework.Controller.realLEDXaxisRange - 1
                    )
                    firework._delay_count_max = random.randint(1, 5)
                    _sizeMax = min(
                        MatrixFunction.Controller.realLEDXaxisRange,
                        MatrixFunction.Controller.realLEDYaxisRange,
                    )
                    firework._size_max = random.randint(int(_sizeMax // 2), _sizeMax)
                    if firework._color_cycle:
                        firework._color = firework.color_sequence_next
                firework._delay_counter = 0
            x = (
                np.round(
                    np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * firework._size)))
                    * (firework._size)
                ).astype(dtype=np.int32)
                + firework.rowIndex
            )
            i1 = np.where((x >= firework.Controller.realLEDYaxisRange) | (x < 0))[0]
            y = (
                np.round(
                    np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * firework._size)))
                    * (firework._size)
                ).astype(dtype=np.int32)
                + firework.columnIndex
            )
            i2 = np.where((y >= firework.Controller.realLEDXaxisRange) | (y < 0))[0]
            if len(i1) > 0 and len(i2) > 0:
                i = np.concatenate((i1, i2))
            elif len(i1) > 0:
                i = i1
            else:
                i = i2
            if len(i) > 0:
                x = np.delete(x, i)
                y = np.delete(y, i)
            xy = (tuple(x), tuple(y))

            firework.Controller.virtualLEDBuffer[xy] = firework._color

            firework._delay_counter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionsMatrixRadar(
        radar: "MatrixFunction",
    ) -> None:
        """
        Args:
            radar: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            x = radar.x + radar.radius
            y = radar.thetas[radar._step_counter] * radar.x + radar.radius
            # y = radar.thetas[radar.stepCounter] * radar.x + radar.stepCounter
            # y = radar.thetas[radar.stepCounter] * radar.x + (radar.stepCountMax - 1 - radar.stepCounter)
            y = y.astype(np.int32)
            i1 = np.where((x >= radar.Controller.realLEDXaxisRange) | (x < 0))[0]
            i2 = np.where((y >= radar.Controller.realLEDYaxisRange) | (y < 0))[0]
            if len(i1) > 0 and len(i2) > 0:
                i = np.concatenate((i1, i2))
            elif len(i1) > 0:
                i = i1
            else:
                i = i2
            if len(i) > 0:
                x = np.delete(x, i)
                y = np.delete(y, i)
            xy = (tuple(x), tuple(y))

            radar.Controller.virtualLEDBuffer[xy] = PixelColors.RED.array * 0.5

            if random.random() < radar._active_chance:
                duration = 20
                i = random.randint(0, len(x) - 1)
                if x[i] != radar.radius and y[i] != radar.radius:
                    # radar.enemy.append([duration, (x[i], y[i])])
                    radar.enemy.append(
                        [
                            duration,
                            (
                                (
                                    x[i],
                                    x[i],
                                    x[i - 1],
                                    x[i - 1],
                                ),
                                (
                                    y[i],
                                    y[i - 1],
                                    y[i - 1],
                                    y[i],
                                ),
                            ),
                        ]
                    )

            gone_enemies = []
            for enemy in radar.enemy:
                radar.Controller.virtualLEDBuffer[enemy[1]] = PixelColors.GREEN.array
                enemy[0] -= 1
                if enemy[0] <= 0:
                    gone_enemies.append(enemy)

            for enemy in gone_enemies:
                radar.enemy.remove(enemy)

            radar._delay_counter += 1
            if radar._delay_counter >= radar._delay_count_max:
                radar._step_counter += 1
                if radar._step_counter >= radar._step_count_max:
                    radar._step_counter = 0
                radar._delay_counter = 0
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex

    @staticmethod
    def functionsMatrixSnake(
        snake: "MatrixFunction",
    ) -> None:
        """
        Args:
            snake: the object used for tracking status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            if snake._delay_counter >= snake._delay_count_max:
                if snake._step_counter < snake._step_count_max:
                    snake._step_counter += 1
                snake.rowIndex = np.roll(snake.rowIndex, 1)
                snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                snake.columnIndex = np.roll(snake.columnIndex, 1)
                snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection

                attempts = 0
                ready = False
                while not ready and attempts < 3:
                    d = {}
                    collision = False
                    if snake._collision:
                        for ii in zip(
                            snake.rowIndex[: snake._step_counter],
                            snake.columnIndex[: snake._step_counter],
                        ):
                            if ii in d:
                                collision = True
                                break
                            else:
                                d[ii] = ii

                    if snake.rowIndex[0] > snake.Controller.realLEDXaxisRange - 1:
                        if attempts == 0:
                            snake.rowIndex[0] -= 1
                            snake.rowDirection -= 1
                            snake.columnDirection = [-1, 1][random.randint(0, 1)]
                            snake.columnIndex[0] = (
                                snake.columnIndex[1] + snake.columnDirection
                            )
                        else:
                            snake.rowDirection *= -1
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                    elif snake.rowIndex[0] < 0:
                        if attempts == 0:
                            snake.rowIndex[0] += 1
                            snake.rowDirection += 1
                            snake.columnDirection = [-1, 1][random.randint(0, 1)]
                            snake.columnIndex[0] = (
                                snake.columnIndex[1] + snake.columnDirection
                            )
                        else:
                            snake.rowDirection *= -1
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                    elif snake.columnIndex[0] > snake.Controller.realLEDYaxisRange - 1:
                        if attempts == 0:
                            snake.columnIndex[0] -= 1
                            snake.columnDirection -= 1
                            snake.rowDirection = [-1, 1][random.randint(0, 1)]
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                        else:
                            snake.columnDirection *= -1
                            snake.columnIndex[0] = (
                                snake.columnIndex[1] + snake.columnDirection
                            )
                    elif snake.columnIndex[0] < 0:
                        if attempts == 0:
                            snake.columnIndex[0] += 1
                            snake.columnDirection += 1
                            snake.rowDirection = [-1, 1][random.randint(0, 1)]
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                        else:
                            snake.columnDirection *= -1
                            snake.columnIndex[0] = (
                                snake.columnIndex[1] + snake.columnDirection
                            )
                    elif collision:
                        if snake.rowDirection != 0:
                            snake.rowDirection *= -1
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                        elif snake.columnDirection != 0:
                            snake.columnDirection *= -1
                            snake.columnIndex[0] = (
                                snake.columnIndex[1] + snake.columnDirection
                            )
                    else:
                        ready = True
                    attempts += 1

                d = {}
                collision = False
                if snake._collision:
                    for ii in zip(
                        snake.rowIndex[: snake._step_counter],
                        snake.columnIndex[: snake._step_counter],
                    ):
                        if ii in d:
                            collision = True
                            break
                        else:
                            d[ii] = ii

                if collision or not ready:
                    snake._size = random.randint(
                        int(snake._size_max / 2), snake._size_max
                    )
                    snake._step_count_max = snake._size
                    snake.rowIndex = np.ones(
                        (snake._size), dtype=np.int32
                    ) * random.randint(0, snake.Controller.realLEDXaxisRange - 1)
                    snake.columnIndex = np.ones(
                        (snake._size), dtype=np.int32
                    ) * random.randint(0, snake.Controller.realLEDYaxisRange - 1)
                    snake._step_counter = 1
                    snake._delay_counter = 0
                    snake._color = snake.color_sequence_next

            for i in range(snake._step_counter):
                snake.Controller.virtualLEDBuffer[
                    snake.rowIndex[i], snake.columnIndex[i]
                ] = snake._color

            if random.random() > 0.9:
                if snake.rowDirection != 0:
                    snake.rowDirection = 0
                    snake.columnDirection = [-1, 1][random.randint(0, 1)]
                else:
                    snake.rowDirection = [-1, 1][random.randint(0, 1)]
                    snake.columnDirection = 0

            snake._delay_counter += 1
            if snake._delay_counter > snake._delay_count_max:
                snake._delay_counter = 0
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise FunctionError from ex
