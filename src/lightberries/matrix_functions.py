import random
from typing import Any, Callable, ClassVar
import numpy as np
import logging
from lightberries.array_functions import ArrayFunction
import lightberries.matrix_controller

from lightberries.exceptions import LightBerryException, LightFunctionException
from lightberries.pixel import PixelColors

LOGGER = logging.getLogger("lightberries")


class LightMatrixFunction(ArrayFunction):
    """This class defines everything necessary to modify LED patterns in interesting ways."""

    Controller: ClassVar["lightberries.LightMatrixControls.LightMatrixController"]

    def __init__(
        self,
        funcPointer: Callable,
        colorSequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
            funcPointer: a function pointer that updates LEDs in the LightController object.
            colorSequence: a sequence of RGB values.
        """
        super().__init__(funcPointer, colorSequence)

        self.rowIndex: int = 0
        self.columnIndex: int = 0
        self.rowDirection: int = 1
        self.columnDirection: int = 1
        self.rowStep: int = 1
        self.columnStep: int = 1

    @staticmethod
    def functionMatrixColorFlux(
        flux: "LightMatrixFunction",
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
                LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 0] = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 0],
                    random.randint(-1, 0),
                    roll_index,
                )
                LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 1] = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 1],
                    random.randint(-1, 0),
                    roll_index,
                )
                LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 2] = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 2],
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
            raise LightFunctionException from ex

    @staticmethod
    def functionMatrixMarquee(
        marquee: "LightMatrixFunction",
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
                LightMatrixFunction.Controller.virtualLEDBuffer = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer,
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
            raise LightFunctionException from ex

    @staticmethod
    def functionMatrixEye(
        eye: "LightMatrixFunction",
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
                elif eye.rowIndex >= eye.Controller.realLEDRowCount - _max:
                    eye.rowIndex = eye.Controller.realLEDRowCount - _max - 1
                if eye.columnIndex < _min:
                    eye.columnIndex = _min
                elif eye.columnIndex >= eye.Controller.realLEDColumnCount - _max:
                    eye.columnIndex = eye.Controller.realLEDColumnCount - _max - 1
                eye.Controller.virtualLEDBuffer *= 0
                eye.Controller.virtualLEDBuffer[
                    eye.rowIndex, eye.columnIndex, :
                ] = PixelColors.RED.array
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
            raise LightFunctionException from ex

    @staticmethod
    def functionMatrixBounce(
        bounce: "LightMatrixFunction",
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
                elif bounce.rowIndex >= bounce.Controller.realLEDRowCount - _max:
                    bounce.rowIndex = bounce.Controller.realLEDRowCount - _max - 1
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
                elif bounce.columnIndex >= bounce.Controller.realLEDColumnCount - _max:
                    bounce.columnIndex = bounce.Controller.realLEDColumnCount - _max - 1
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                bounce.delayCounter = 0
            bounce.Controller.virtualLEDBuffer[
                bounce.rowIndex, bounce.columnIndex, :
            ] = bounce.color
            bounce.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionsMatrixFireworks(
        firework: "LightMatrixFunction",
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
                    firework.rowIndex = random.randint(
                        0, firework.Controller.realLEDRowCount - 1
                    )
                    firework.columnIndex = random.randint(
                        0, firework.Controller.realLEDColumnCount - 1
                    )
                    firework.delayCountMax = random.randint(1, 5)
                    if firework.colorCycle and random.randint(0, 10) >= 7:
                        firework.color = firework.colorSequenceNext
                firework.delayCounter = 0

            # _x = np.sin(np.linspace(0, np.pi, 1 + (4 * zoomy.size)) * (zoomy.size))
            x = (
                np.round(
                    np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * firework.size)))
                    * (firework.size)
                ).astype(dtype=np.int32)
                + firework.rowIndex
            )
            i1 = np.where((x >= firework.Controller.realLEDRowCount) | (x < 0))[0]
            y = (
                np.round(
                    np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * firework.size)))
                    * (firework.size)
                ).astype(dtype=np.int32)
                + firework.columnIndex
            )
            i2 = np.where((y >= firework.Controller.realLEDColumnCount) | (y < 0))[0]
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
            raise LightFunctionException from ex

    @staticmethod
    def functionsMatrixRadar(
        radar: "LightMatrixFunction",
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
            i1 = np.where((x >= radar.Controller.realLEDRowCount) | (x < 0))[0]
            i2 = np.where((y >= radar.Controller.realLEDColumnCount) | (y < 0))[0]
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

            radar.Controller.virtualLEDBuffer[xy] = PixelColors.GREEN3.array * 0.5

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
                radar.Controller.virtualLEDBuffer[enemy[1]] = PixelColors.RED.array
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
            raise LightFunctionException from ex