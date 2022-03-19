import random
from typing import Any, Callable

import numpy as np
from LightBerries.LightArrayControls import LightArrayController
from nptyping import NDArray
import logging
from LightBerries.LightArrayFunctions import LightArrayFunction
from LightBerries.LightBerryExceptions import LightBerryException, LightControlException
from LightBerries.LightMatrixFunctions import LightMatrixFunction
from LightBerries.LightMatrixPatterns import (
    SolidColorMatrix,
    MatrixOrder,
    DEFAULT_MATRIX_ORDER,
    Spectrum2,
    TextMatrix,
)
from LightBerries.LightPixels import PixelColors

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
        self.virtualLEDIndexBuffer: NDArray[(Any,), np.int32]
        self.setVirtualLEDBuffer(
            SolidColorMatrix(self.realLEDRowCount, self.realLEDColumnCount, color=PixelColors.OFF.array)
        )

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

            if matrix is None:
                matrix = Spectrum2(rowCount=self.realLEDRowCount, columnCount=self.realLEDColumnCount)

            self.virtualLEDRowCount = matrix.shape[0]
            self.virtualLEDColumnCount = matrix.shape[1]

            self.virtualLEDBuffer = matrix
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

    def setVirtualLEDBuffer(self, ledMatrix: NDArray[(3, Any, Any), np.int32]) -> None:
        self.virtualLEDRowCount = ledMatrix.shape[0]
        self.virtualLEDColumnCount = ledMatrix.shape[1]
        if len(self.virtualLEDBuffer.shape) == 3:
            ledArray = np.reshape(ledMatrix, (self.virtualLEDRowCount * self.virtualLEDColumnCount, 3))
        else:
            ledArray = ledMatrix.copy()
        super().setVirtualLEDBuffer(ledArray)
        self.virtualLEDBuffer = ledMatrix
        self.privateVirtualLEDCount = int(ledMatrix.size / 3)
        self.virtualLEDIndexBuffer = np.arange(self.virtualLEDCount)
        if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow:
            self.virtualLEDIndexBuffer = np.reshape(
                self.virtualLEDIndexBuffer, (self.virtualLEDRowCount, self.virtualLEDColumnCount)
            )
            for i in range(1, self.virtualLEDRowCount, 2):
                self.virtualLEDIndexBuffer[i, :] = np.flip(self.virtualLEDIndexBuffer[i, :])
        elif DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseRowThenColumn:
            self.virtualLEDIndexBuffer = np.reshape(
                self.virtualLEDIndexBuffer, (self.virtualLEDRowCount, self.virtualLEDColumnCount)
            )
            for i in range(1, self.virtualLEDColumnCount, 2):
                self.virtualLEDIndexBuffer[i, :] = np.flip(self.virtualLEDIndexBuffer[i, :])

    def reset(
        self,
    ) -> None:
        """Reset class variables to default state.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.reset.__name__)
            self.privateLightFunctions = []
            if self.virtualLEDCount > self.realLEDCount:
                self.setVirtualLEDBuffer(
                    self.virtualLEDBuffer[: self.realLEDRowCount, : self.realLEDColumnCount]
                )
            elif self.virtualLEDCount < self.realLEDCount:
                array = SolidColorMatrix(
                    rowCount=self.realLEDRowCount,
                    columnCount=self.realLEDColumnCount,
                    color=PixelColors.OFF.array,
                )
                array[: self.virtualLEDRowCount, : self.virtualLEDColumnCount] = self.virtualLEDBuffer
                self.setVirtualLEDBuffer(array)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

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
            if len(self.virtualLEDBuffer.shape) > 2:
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
            else:
                list(
                    map(
                        SetPixel,
                        enumerate(
                            self.virtualLEDBuffer[self.virtualLEDIndexBuffer][
                                np.where(self.virtualLEDIndexBuffer < self.realLEDCount)
                            ]
                        ),
                    )
                )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

    def useFunctionMatrixColorFlux(
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
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixColorFlux.__name__)

            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)

            # create the tracking object
            flux: LightMatrixFunction = LightMatrixFunction(
                LightMatrixFunction.functionMatrixColorFlux, self.colorSequence
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
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

    def useFunctionMatrixMarquee(
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
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixMarquee.__name__)

            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)

            # create the tracking object
            marquee: LightMatrixFunction = LightMatrixFunction(
                LightMatrixFunction.functionMatrixMarquee, self.colorSequence
            )
            # set refresh counter
            marquee.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            marquee.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(marquee)

            self.virtualLEDArray[0, 0, :] += self.colorSequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

    def useFunctionMatrixMarqueeText(
        self,
        delayCount: int = None,
        text: str = None,
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
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixMarquee.__name__)

            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)

            options = ["hello world", "hi guys", "lol             "]
            if text is None:
                _text = options[random.randint(0, len(options) - 1)]
            else:
                _text = str(text)

            # create the tracking object
            marquee: LightMatrixFunction = LightMatrixFunction(
                LightMatrixFunction.functionMatrixMarquee, self.colorSequence
            )
            # set refresh counter
            marquee.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            marquee.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(marquee)

            self.setVirtualLEDBuffer(TextMatrix(_text, self.colorSequence[0]))
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

    def useFunctionMatrixEye(
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
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixEye.__name__)

            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)

            # create the tracking object
            eye: LightMatrixFunction = LightMatrixFunction(
                LightMatrixFunction.functionMatrixEye, self.colorSequence
            )
            eye.rowIndex = int(self.realLEDRowCount / 2)
            eye.columnIndex = int(self.realLEDColumnCount / 2)
            # set refresh counter
            eye.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            eye.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(eye)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex

    def useFunctionMatrixBounce(
        self,
        delayCount: int = None,
        ballCount: int = None,
        fadeAmount=None,
        colorChange=False,
    ) -> None:
        """

        Args:
            delayCount: number of led updates between color updates
            ballCount: number of bouncy balls
            fadeAmount:fade amount
            colorChange: change colors

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixBounce.__name__)

            _fadeAmount: float = random.randint(50, 100) / 255.0
            _delayCount: int = random.randint(1, 6)
            _ballCount: int = random.randint(1, 6)
            if fadeAmount is not None:
                _fadeAmount = int(fadeAmount)

            # make sure fade is valid
            if _fadeAmount > 0 and _fadeAmount < 1:
                # do nothing
                pass
            elif _fadeAmount > 0 and _fadeAmount < 256:
                _fadeAmount /= 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1

            if delayCount is not None:
                _delayCount = int(delayCount)

            if ballCount is not None:
                _ballCount = int(ballCount)

            if _fadeAmount == 0.0:
                off: LightArrayFunction = LightArrayFunction(
                    LightMatrixFunction.functionOff, self.colorSequence
                )
                self.privateLightFunctions.append(off)
            else:
                # fade the whole LED strand
                fade: LightArrayFunction = LightArrayFunction(
                    LightArrayFunction.functionFadeOff, self.colorSequence
                )
                # by this amount
                fade.fadeAmount = _fadeAmount
                # add function to list
                self.privateLightFunctions.append(fade)

            # create the tracking object
            for _ in range(_ballCount):
                bounce: LightMatrixFunction = LightMatrixFunction(
                    LightMatrixFunction.functionMatrixBounce, self.colorSequence
                )
                bounce.rowIndex = random.randint(0, self.realLEDRowCount - 1)
                bounce.columnIndex = random.randint(0, self.realLEDColumnCount - 1)
                bounce.rowDirection = [-1, 1][random.randint(0, 1)]
                bounce.columnDirection = [-1, 1][random.randint(0, 1)]
                bounce.rowStep = random.randint(1, 2)
                bounce.columnStep = random.randint(1, 2)
                # set refresh counter
                bounce.delayCounter = _delayCount
                # set refresh limit (after which this function will execute)
                bounce.delayCountMax = _delayCount
                # add this function to our function list
                bounce.color = self.colorSequenceNext
                bounce.colorCycle = bool(colorChange)
                self.privateLightFunctions.append(bounce)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightControlException from ex