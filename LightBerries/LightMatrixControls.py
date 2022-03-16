import random
from typing import Any, Callable

import numpy as np
from LightBerries.LightArrayControls import LightArrayController
from nptyping import NDArray
import logging
from LightBerries.LightBerryExceptions import LightControlException
from LightBerries.LightPixels import Pixel
from LightBerries.LightMatrixFunctions import LightMatrixFunction
from LightBerries.LightMatrixPatterns import MatrixOrder, DEFAULT_MATRIX_ORDER

LOGGER = logging.getLogger("LightBerries")


class LightMatrixController(LightArrayController):
    def __init__(
        self,
        ledRowCount: int,
        ledColumnCount: int,
        pwmGPIOpin: int = 18,
        channelDMA: int = 10,
        frequencyPWM: int = 800000,
        invertSignalPWM: bool = False,
        ledBrightnessFloat: float = 0.75,
        channelPWM: int = 0,
        stripTypeLED: Any = None,
        gamma: Any = None,
        debug: bool = False,
        verbose: bool = False,
        refreshCallback: Callable = None,
        simulate: bool = False,
    ) -> None:
        if not ledRowCount:
            ledRowCount = 4
        else:
            ledRowCount = int(ledRowCount)
        if not ledColumnCount:
            ledColumnCount = 4
        else:
            ledColumnCount = int(ledColumnCount)
        super().__init__(
            (ledRowCount * ledColumnCount),
            pwmGPIOpin,
            channelDMA,
            frequencyPWM,
            invertSignalPWM,
            ledBrightnessFloat,
            channelPWM,
            stripTypeLED,
            gamma,
            debug,
            verbose,
            refreshCallback,
            simulate,
        )
        self.realLEDRowCount = ledRowCount
        self.realLEDColumnCount = ledColumnCount
        self.virtualLEDRowCount = ledRowCount
        self.virtualLEDColumnCount = ledColumnCount
        self.virtualLEDIndexBuffer: NDArray[
            (Any,), np.int32
        ]  # = np.array(range(len(self.ws28xxLightString)))
        # self.virtualLEDIndexBuffer = np.reshape(
        # self.virtualLEDIndexBuffer, (self.virtualLEDRowCount, self.virtualLEDColumnCount)
        # )
        # for i in range(1, self.virtualLEDRowCount, 2):
        # self.virtualLEDIndexBuffer[i, :] = np.flip(self.virtualLEDIndexBuffer[i, :])
        # self.virtualLEDIndexBuffer = np.reshape(
        # self.virtualLEDIndexBuffer, (self.virtualLEDRowCount * self.virtualLEDColumnCount)
        # )

        # give LightFunction class a pointer to this class
        LightMatrixFunction.Controller = self

    def useColorMatrix(
        self,
        matrix: NDArray[(Any, Any, 3), np.int32] = None,
    ) -> None:
        """Sets the the color sequence used by light functions to one of your choice.

        Args:

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            LOGGER.debug("\n%s.%s:", self.__class__.__name__, self.useColorMatrix.__name__)

            # _backgroundColor: NDArray[(3,), np.int32] = DEFAULT_BACKGROUND_COLOR.array
            # _colorSequence: NDArray[(Any, 3), np.int32] = DefaultColorSequence()

            # set the color sequence to the default one for this month, or use the passed in argument
            # if matrix is not None:
            # _colorSequence = np.zeros((self._ledRowCount, self._ledColumnCount,3))

            # assign the background color its default value
            # if backgroundColor is not None:
            # _backgroundColor = Pixel(backgroundColor).array

            # self.backgroundColor = _backgroundColor
            # set the color sequence

            self.virtualLEDRowCount = matrix.shape[0]
            self.virtualLEDColumnCount = matrix.shape[1]

            self.virtualLEDBuffer = matrix
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useColorMatrix.__name__,
                ex,
            )
            raise LightControlException from ex

    def setVirtualLEDBuffer(self, ledMatrix: NDArray[(3, Any, Any), np.int32]) -> None:
        self.virtualLEDRowCount = ledMatrix.shape[0]
        self.virtualLEDColumnCount = ledMatrix.shape[1]
        ledArray = np.reshape(ledMatrix, (self.virtualLEDRowCount * self.virtualLEDColumnCount, 3))
        super().setVirtualLEDBuffer(ledArray)
        self.virtualLEDBuffer = ledMatrix
        self.virtualLEDIndexBuffer = np.reshape(
            self.virtualLEDIndexBuffer, (self.virtualLEDRowCount, self.virtualLEDColumnCount)
        )
        if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow:
            for i in range(1, self.virtualLEDRowCount, 2):
                self.virtualLEDIndexBuffer[i, :] = np.flip(self.virtualLEDIndexBuffer[i, :])
        elif DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseRowThenColumn:
            for i in range(1, self.virtualLEDColumnCount, 2):
                self.virtualLEDIndexBuffer[:, i] = np.flip(self.virtualLEDIndexBuffer[:, i])
        self.virtualLEDIndexBuffer = np.reshape(
            self.virtualLEDIndexBuffer, (self.virtualLEDRowCount * self.virtualLEDColumnCount)
        )

    def copyVirtualLedsToWS281X(
        self,
    ) -> None:
        """Sets each Pixel in the rpi_ws281x object to the buffered array value.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            # callback function to do work

            def SetPixel(irgb):
                i = irgb[0]
                rgb = irgb[1]
                if i < self.realLEDCount:
                    self.ws28xxLightString[i] = rgb

            # fast method of calling the callback method on each index of LED array
            list(
                map(
                    SetPixel,
                    enumerate(
                        self.virtualLEDBuffer.reshape(
                            (self.virtualLEDRowCount * self.virtualLEDColumnCount, 3)
                        )[self.virtualLEDIndexBuffer][
                            np.where(self.virtualLEDIndexBuffer < self.realLEDCount)
                        ]
                    ),
                )
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.copyVirtualLedsToWS281X.__name__,
                ex,
            )
            raise LightControlException from ex

    def useFunctionColorFlux(
        self,
        delayCount: int = None,
    ) -> None:
        """

        Args:
            delayCount: number of led updates between color updates

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionColorFlux.__name__)

            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)

            # create the tracking object
            flux: LightMatrixFunction = LightMatrixFunction(
                LightMatrixFunction.functionColorFlux, self.colorSequence
            )
            # set refresh counter
            flux.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            flux.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(flux)

            # clear LEDs, assign first color in sequence to all LEDs
            # self.virtualLEDArray *= 0
            # self.virtualLEDArray += self.colorSequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.useFunctionColorFlux.__name__,
                ex,
            )
            raise LightControlException from ex
