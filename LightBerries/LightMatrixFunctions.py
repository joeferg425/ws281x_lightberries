import random
from typing import Any, Callable, ClassVar
from nptyping import NDArray
import numpy as np
import logging
import LightBerries.LightMatrixControls
from LightBerries.LightMatrixPatterns import DEFAULT_MATRIX_ORDER, MatrixOrder

from LightBerries.LightBerryExceptions import LightFunctionException

LOGGER = logging.getLogger("LightBerries")


class LightMatrixFunction:
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
        self.privateColorSequence: NDArray[(3, Any), np.int32] = colorSequence
        self.privateColorSequenceCount: int = 0
        self.privateColorSequenceIndex: int = 0

        self.funcName: str = funcPointer.__name__
        self.runFunction: Callable = funcPointer

    @staticmethod
    def functionColorFlux(
        flux: "LightMatrixFunction",
    ) -> None:
        """Move the LEDs in the color sequence from one end of the LED string to the other continuously.

        Args:
            flux: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # wait for several LED cycles to change LEDs
            # if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow:
            # roll_index = 0
            # elif DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseRowThenColumn:
            # roll_index = 1
            roll_index = 1
            if flux.delayCounter >= flux.delayCountMax:
                LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 0] = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 0],
                    random.randint(0, 1),
                    # 1,
                    roll_index,
                )
                LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 1] = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 1],
                    random.randint(0, 1),
                    # 1,
                    roll_index,
                )
                LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 2] = np.roll(
                    LightMatrixFunction.Controller.virtualLEDBuffer[:, :, 2],
                    random.randint(0, 1),
                    # 1,
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
                flux.functionColorFlux.__name__,
                ex,
            )
            raise LightFunctionException from ex
