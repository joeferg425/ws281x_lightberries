import random
from typing import Any, Callable, ClassVar
from nptyping import NDArray
import numpy as np
import logging
from LightBerries.LightArrayFunctions import LightArrayFunction
import LightBerries.LightMatrixControls

from LightBerries.LightBerryExceptions import LightFunctionException
from LightBerries.LightPixels import PixelColors

LOGGER = logging.getLogger("LightBerries")


class LightMatrixFunction(LightArrayFunction):
    """This class defines everything neccesary to modify LED patterns in interesting ways."""

    Controller: ClassVar["LightBerries.LightMatrixControls.LightMatrixController"]

    def __init__(
        self,
        funcPointer: Callable,
        colorSequence: NDArray[(3, Any), np.int32],
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
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                flux.__class__.__name__,
                flux.functionMatrixColorFlux.__name__,
                ex,
            )
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
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                marquee.__class__.__name__,
                marquee.functionMatrixMarquee.__name__,
                ex,
            )
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
            mmin = 1
            mmax = 1
            if eye.delayCounter >= eye.delayCountMax:
                eye.rowIndex += random.randint(-5, 5)
                eye.columnIndex += random.randint(-5, 5)
                if eye.rowIndex < mmin:
                    eye.rowIndex = mmin
                elif eye.rowIndex >= eye.Controller.realLEDRowCount - mmax:
                    eye.rowIndex = eye.Controller.realLEDRowCount - mmax - 1
                if eye.columnIndex < mmin:
                    eye.columnIndex = mmin
                elif eye.columnIndex >= eye.Controller.realLEDColumnCount - mmax:
                    eye.columnIndex = eye.Controller.realLEDColumnCount - mmax - 1
                eye.Controller.virtualLEDBuffer *= 0
                eye.Controller.virtualLEDBuffer[eye.rowIndex, eye.columnIndex, :] = PixelColors.RED.array
                eye.delayCountMax = random.randint(10, 850)
                eye.delayCounter = 0
            eye.delayCounter += 1

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                eye.__class__.__name__,
                eye.functionMatrixMarquee.__name__,
                ex,
            )
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
            mmin = 1
            mmax = 1
            if bounce.delayCounter >= bounce.delayCountMax:
                bounce.rowIndex += bounce.rowDirection * bounce.rowStep
                bounce.columnIndex += bounce.columnDirection * bounce.columnStep
                if bounce.rowIndex < mmin:
                    bounce.rowIndex = mmin
                    bounce.rowDirection *= -1
                    bounce.rowStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                elif bounce.rowIndex >= bounce.Controller.realLEDRowCount - mmax:
                    bounce.rowIndex = bounce.Controller.realLEDRowCount - mmax - 1
                    bounce.rowDirection *= -1
                    bounce.rowStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                if bounce.columnIndex < mmin:
                    bounce.columnIndex = mmin
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                elif bounce.columnIndex >= bounce.Controller.realLEDColumnCount - mmax:
                    bounce.columnIndex = bounce.Controller.realLEDColumnCount - mmax - 1
                    bounce.columnDirection *= -1
                    bounce.columnStep = random.randint(1, 2)
                    bounce.delayCountMax = random.randint(1, 5)
                    if bounce.colorCycle and random.randint(0, 10) >= 7:
                        bounce.color = bounce.colorSequenceNext
                bounce.delayCounter = 0
            bounce.Controller.virtualLEDBuffer[bounce.rowIndex, bounce.columnIndex, :] = bounce.color
            bounce.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                bounce.__class__.__name__,
                bounce.functionMatrixBounce.__name__,
                ex,
            )
            raise LightFunctionException from ex
