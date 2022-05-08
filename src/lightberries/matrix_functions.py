from __future__ import annotations
import random
from typing import Any, Callable, ClassVar
import numpy as np
import logging
from lightberries.array_functions import ArrayFunction
import lightberries.matrix_controller
from lightberries.exceptions import LightBerryException, FunctionException
from lightberries.pixel import PixelColors
from math import ceil

LOGGER = logging.getLogger("lightBerries")


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
        self.columnIndex: int = 0
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
            ArrayFunction.Controller.virtualLEDBuffer[:, :] = ArrayFunction.Controller.virtualLEDBuffer * (
                1 - fade.fadeAmount
            )
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except SystemExit:  # pragma: no cover
            raise
        except LightBerryException:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            raise FunctionException from ex

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
            _fadeAmount = ceil(fade.fadeAmount * 256)
            if _fadeAmount < 0:
                _fadeAmount = 1
            elif _fadeAmount > 255:
                _fadeAmount = 255
            for x in range(ArrayFunction.Controller.realLEDYaxisRange):
                for y in range(ArrayFunction.Controller.realLEDXaxisRange):
                    for rgbIndex in range(len(fade.color)):
                        if ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex] != fade.color[rgbIndex]:
                            if (
                                ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex] - _fadeAmount
                                > fade.color[rgbIndex]
                            ):
                                ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex] -= _fadeAmount
                            elif (
                                ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex] + _fadeAmount
                                < fade.color[rgbIndex]
                            ):
                                ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex] += _fadeAmount
                            else:
                                ArrayFunction.Controller.virtualLEDBuffer[x, y, rgbIndex] = fade.colorNext[rgbIndex]
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            if flux.delayCounter >= flux.delayCountMax:
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
                flux.delayCounter = 0
            flux.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            if marquee.delayCounter >= marquee.delayCountMax:
                MatrixFunction.Controller.virtualLEDBuffer = np.roll(
                    MatrixFunction.Controller.virtualLEDBuffer,
                    -1,
                    roll_index,
                )
                marquee.delayCounter = 0
            marquee.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            if eye.delayCounter >= eye.delayCountMax:
                eye.rowIndex += random.randint(-5, 5)
                eye.columnIndex += random.randint(-5, 5)
                if eye.rowIndex < _min:
                    eye.rowIndex = _min
                elif eye.rowIndex >= eye.Controller.realLEDXaxisRange - _max:
                    eye.rowIndex = eye.Controller.realLEDXaxisRange - _max - 1
                if eye.columnIndex < _min:
                    eye.columnIndex = _min
                elif eye.columnIndex >= eye.Controller.realLEDYaxisRange - _max:
                    eye.columnIndex = eye.Controller.realLEDYaxisRange - _max - 1
                eye.Controller.virtualLEDBuffer *= 0
                eye.Controller.virtualLEDBuffer[eye.rowIndex, eye.columnIndex, :] = PixelColors.RED.array
                eye.delayCountMax = random.randint(10, 850)
                eye.delayCounter = 0
            eye.delayCounter += 1

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            if bounce.delayCounter >= bounce.delayCountMax:
                bounce.rowIndex += bounce.rowDirection * bounce.rowStep
                bounce.columnIndex += bounce.columnDirection * bounce.columnStep
                if bounce.rowIndex < _min:
                    bounce.rowIndex = _min
                    bounce.rowDirection *= -1
                    bounce.rowStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                elif bounce.rowIndex >= bounce.Controller.realLEDXaxisRange - _max:
                    bounce.rowIndex = bounce.Controller.realLEDXaxisRange - _max - 1
                    bounce.rowDirection *= -1
                    bounce.rowStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                if bounce.columnIndex < _min:
                    bounce.columnIndex = _min
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                elif bounce.columnIndex >= bounce.Controller.realLEDYaxisRange - _max:
                    bounce.columnIndex = bounce.Controller.realLEDYaxisRange - _max - 1
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                bounce.delayCounter = 0
            bounceRange = list(range(bounce.rowIndex, bounce.columnIndex))
            # bounce.Controller.virtualLEDBuffer[bounce.rowIndex, bounce.columnIndex, :] = bounce.color
            if len(ArrayFunction.Controller.virtualLEDBuffer.shape) == 2:
                ArrayFunction.Controller.virtualLEDBuffer[bounceRange] = bounce.color
            else:
                ArrayFunction.Controller.virtualLEDBuffer[
                    np.where(ArrayFunction.Controller.virtualLEDIndexBuffer == bounceRange)
                ] = bounce.color
            bounce.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            if firework.delayCounter >= firework.delayCountMax:
                if firework.size < firework.sizeMax:
                    firework.size += firework.step
                else:
                    firework.size = 1
                    firework.rowIndex = random.randint(0, firework.Controller.realLEDYaxisRange - 1)
                    firework.columnIndex = random.randint(0, firework.Controller.realLEDXaxisRange - 1)
                    firework.delayCountMax = random.randint(1, 5)
                    _sizeMax = min(
                        MatrixFunction.Controller.realLEDXaxisRange, MatrixFunction.Controller.realLEDYaxisRange
                    )
                    firework.sizeMax = random.randint(int(_sizeMax // 2), _sizeMax)
                    if firework.colorCycle:
                        firework.color = firework.colorSequenceNext
                firework.delayCounter = 0

            # _x = np.sin(np.linspace(0, np.pi, 1 + (4 * zoomy.size)) * (zoomy.size))
            x = (
                np.round(np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * firework.size))) * (firework.size)).astype(
                    dtype=np.int32
                )
                + firework.rowIndex
            )
            i1 = np.where((x >= firework.Controller.realLEDYaxisRange) | (x < 0))[0]
            y = (
                np.round(np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * firework.size))) * (firework.size)).astype(
                    dtype=np.int32
                )
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

            firework.Controller.virtualLEDBuffer[xy] = firework.color

            firework.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            y = radar.thetas[radar.stepCounter] * radar.x + radar.radius
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

            if random.random() < radar.activeChance:
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

            radar.delayCounter += 1
            if radar.delayCounter >= radar.delayCountMax:
                radar.stepCounter += 1
                if radar.stepCounter >= radar.stepCountMax:
                    radar.stepCounter = 0
                radar.delayCounter = 0
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex

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
            if snake.delayCounter >= snake.delayCountMax:
                if snake.stepCounter < snake.stepCountMax:
                    snake.stepCounter += 1
                snake.rowIndex = np.roll(snake.rowIndex, 1)
                snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                snake.columnIndex = np.roll(snake.columnIndex, 1)
                snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection

                attempts = 0
                ready = False
                while not ready and attempts < 3:
                    d = {}
                    collision = False
                    if snake.collision:
                        for ii in zip(snake.rowIndex[: snake.stepCounter], snake.columnIndex[: snake.stepCounter]):
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
                            snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection
                        else:
                            snake.rowDirection *= -1
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                    elif snake.rowIndex[0] < 0:
                        if attempts == 0:
                            snake.rowIndex[0] += 1
                            snake.rowDirection += 1
                            snake.columnDirection = [-1, 1][random.randint(0, 1)]
                            snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection
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
                            snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection
                    elif snake.columnIndex[0] < 0:
                        if attempts == 0:
                            snake.columnIndex[0] += 1
                            snake.columnDirection += 1
                            snake.rowDirection = [-1, 1][random.randint(0, 1)]
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                        else:
                            snake.columnDirection *= -1
                            snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection
                    elif collision:
                        if snake.rowDirection != 0:
                            snake.rowDirection *= -1
                            snake.rowIndex[0] = snake.rowIndex[1] + snake.rowDirection
                        elif snake.columnDirection != 0:
                            snake.columnDirection *= -1
                            snake.columnIndex[0] = snake.columnIndex[1] + snake.columnDirection
                    else:
                        ready = True
                    attempts += 1

                d = {}
                collision = False
                if snake.collision:
                    for ii in zip(snake.rowIndex[: snake.stepCounter], snake.columnIndex[: snake.stepCounter]):
                        if ii in d:
                            collision = True
                            break
                        else:
                            d[ii] = ii

                if collision or not ready:
                    snake.size = random.randint(int(snake.sizeMax / 2), snake.sizeMax)
                    snake.stepCountMax = snake.size
                    snake.rowIndex = np.ones((snake.size), dtype=np.int32) * random.randint(
                        0, snake.Controller.realLEDXaxisRange - 1
                    )
                    snake.columnIndex = np.ones((snake.size), dtype=np.int32) * random.randint(
                        0, snake.Controller.realLEDYaxisRange - 1
                    )
                    snake.stepCounter = 1
                    snake.delayCounter = 0
                    snake.color = snake.colorSequenceNext

            for i in range(snake.stepCounter):
                snake.Controller.virtualLEDBuffer[snake.rowIndex[i], snake.columnIndex[i]] = snake.color

            if random.random() > 0.9:
                if snake.rowDirection != 0:
                    snake.rowDirection = 0
                    snake.columnDirection = [-1, 1][random.randint(0, 1)]
                else:
                    snake.rowDirection = [-1, 1][random.randint(0, 1)]
                    snake.columnDirection = 0

            snake.delayCounter += 1
            if snake.delayCounter > snake.delayCountMax:
                snake.delayCounter = 0
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise FunctionException from ex
