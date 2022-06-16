from __future__ import annotations
import random
from typing import Any, Callable

from numpy.typing import NDArray
import numpy as np
from lightberries.array_controller import ArrayController
import logging
from lightberries.array_functions import ArrayFunction
from lightberries.exceptions import LightBerryException, ControllerException
from lightberries.matrix_functions import MatrixFunction
from lightberries.matrix_patterns import (
    SolidColorMatrix,
    MatrixOrder,
    DEFAULT_MATRIX_ORDER,
    Spectrum2,
    TextMatrix,
)
from lightberries.array_patterns import ArrayPattern
from lightberries.pixel import PixelColors

LOGGER = logging.getLogger("lightBerries")


class MatrixController(ArrayController):
    def __init__(
        self,
        ledXaxisRange: int,
        ledYaxisRange: int,
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
        matrixShape: tuple[int, int] = None,
        matrixLayout: NDArray[np.int32] | None = None,
    ) -> None:
        if not ledXaxisRange:
            ledXaxisRange = 4
        else:
            ledXaxisRange = int(ledXaxisRange)
        if not ledYaxisRange:
            ledYaxisRange = 4
        else:
            ledYaxisRange = int(ledYaxisRange)
        super().__init__(
            (ledYaxisRange * ledXaxisRange),
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
        self.realLEDYaxisRange = ledXaxisRange
        self.realLEDXaxisRange = ledYaxisRange
        self.virtualLEDYaxisRange = ledXaxisRange
        self.virtualLEDXaxisRange = ledYaxisRange
        self.virtualLEDIndexBuffer: np.ndarray[(Any,), np.int32]
        if matrixLayout is not None:
            self.matrixLayout = matrixLayout
            self.matrixCount = matrixLayout.shape[0] * matrixLayout.shape[1]
            self.matrixShape = matrixShape
        else:
            self.matrixLayout = None
            self.matrixCount = None
            self.matrixShape = None
        self.setvirtualLEDBuffer(
            SolidColorMatrix(
                xRange=self.realLEDXaxisRange,
                yRange=self.realLEDYaxisRange,
                color=PixelColors.OFF,
            ),
        )

        # give LightFunction class a pointer to this class
        MatrixFunction.Controller = self

    def useColorMatrix(
        self,
        matrix: np.ndarray[(Any, Any, 3), np.int32] = None,
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

            # _backgroundColor: NDArray[(3,), np.int32] = DEFAULT_BACKGROUND_COLOR
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
                matrix = Spectrum2(xRange=self.realLEDXaxisRange, yRange=self.realLEDYaxisRange)

            self.virtualLEDXaxisRange = matrix.shape[0]
            self.virtualLEDYaxisRange = matrix.shape[1]

            self.virtualLEDBuffer = matrix
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

    def setvirtualLEDBuffer(self, ledMatrix: np.ndarray[(3, Any, Any), np.int32]) -> None:
        self.virtualLEDXaxisRange = ledMatrix.shape[0]
        self.virtualLEDYaxisRange = ledMatrix.shape[1]
        self.virtualLEDBuffer = ledMatrix
        self.privateVirtualLEDCount = int(ledMatrix.size / 3)
        if self.matrixLayout is None:
            self.virtualLEDBuffer = ledMatrix
            self.privateVirtualLEDCount = int(ledMatrix.size / 3)
            self.virtualLEDIndexBuffer = np.arange(self.virtualLEDCount)
            if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow.value:
                self.virtualLEDIndexBuffer = np.reshape(
                    self.virtualLEDIndexBuffer,
                    (self.virtualLEDXaxisRange, self.virtualLEDYaxisRange),
                )
                for i in range(1, self.virtualLEDXaxisRange, 2):
                    self.virtualLEDIndexBuffer[i, :] = np.flip(self.virtualLEDIndexBuffer[i, :])
            elif DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseRowThenColumn.value:
                self.virtualLEDIndexBuffer = np.reshape(
                    self.virtualLEDIndexBuffer,
                    (self.virtualLEDXaxisRange, self.virtualLEDYaxisRange),
                )
                for i in range(1, self.virtualLEDYaxisRange, 2):
                    self.virtualLEDIndexBuffer[i, :] = np.flip(self.virtualLEDIndexBuffer[i, :])
        else:
            matrix_led_count = self.matrixShape[0] * self.matrixShape[1]
            led_count = ledMatrix.shape[0] * ledMatrix.shape[1]
            if led_count % self.realLEDCount:
                led_count -= led_count % matrix_led_count
                led_count += self.realLEDCount
            self.virtualLEDIndexBuffer = np.zeros((self.realLEDYaxisRange, self.realLEDXaxisRange), dtype=np.int32)
            # self.virtualLEDIndexBuffer = np.zeros((self.realLEDXaxisRange, self.realLEDYaxisRange), dtype=np.int32)
            for matrix_row in range(self.matrixLayout.shape[0]):
                for matrix_column in range(self.matrixLayout.shape[1]):
                    matrix_index = self.matrixLayout[matrix_row, matrix_column]
                    temp = np.arange(matrix_led_count, dtype=np.int32)
                    if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow.value:
                        temp = np.reshape(
                            temp,
                            (self.matrixShape[0], self.matrixShape[1]),
                        )
                        for i in range(1, self.matrixShape[1], 2):
                            temp[i, :] = np.flip(temp[i, :])
                    elif DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseRowThenColumn.value:
                        temp = np.reshape(
                            temp,
                            (self.matrixShape[1], self.matrixShape[0]),
                        )
                        for i in range(1, self.matrixShape[0], 2):
                            temp[:, i] = np.flip(temp[:, i])
                    temp += matrix_led_count * matrix_index
                    r = matrix_row * self.matrixShape[1]
                    c = matrix_column * self.matrixShape[0]
                    self.virtualLEDIndexBuffer[c : c + self.matrixShape[1], r : r + self.matrixShape[0]] = temp

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
                self.setvirtualLEDBuffer(self.virtualLEDBuffer[: self.realLEDXaxisRange, : self.realLEDYaxisRange])
            elif self.virtualLEDCount < self.realLEDCount:
                array = SolidColorMatrix(
                    xRange=self.realLEDXaxisRange,
                    yRange=self.realLEDYaxisRange,
                    color=PixelColors.OFF,
                )
                try:
                    array[: self.virtualLEDXaxisRange, : self.virtualLEDYaxisRange] = self.virtualLEDBuffer
                except:  # noqa
                    pass
                self.setvirtualLEDBuffer(array)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

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

            def SetPixel(i_rgb):
                i = i_rgb[0]
                rgb = i_rgb[1]
                if i < self.realLEDCount:
                    self.ws281xString[i] = rgb

            # fast method of calling the callback method on each index of LED array
            if len(self.virtualLEDBuffer.shape) > 2:
                if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow.value:
                    list(
                        map(
                            SetPixel,
                            zip(
                                self.virtualLEDIndexBuffer[np.where(self.virtualLEDIndexBuffer < self.realLEDCount)],
                                self.virtualLEDBuffer[np.where(self.virtualLEDIndexBuffer < self.realLEDCount)],
                            ),
                        )
                    )
                else:
                    list(
                        map(
                            SetPixel,
                            enumerate(
                                self.virtualLEDBuffer.reshape(
                                    (
                                        self.virtualLEDXaxisRange * self.virtualLEDYaxisRange,
                                        3,
                                    )
                                )[self.virtualLEDIndexBuffer][np.where(self.virtualLEDIndexBuffer < self.realLEDCount)]
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
            raise ControllerException from ex

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
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixColorFlux.__name__)
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            flux: MatrixFunction = MatrixFunction(self, MatrixFunction.functionMatrixColorFlux, self.colorSequence)
            # set refresh counter
            flux.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            flux.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(flux)
            # clear LEDs, assign first color in sequence to all LEDs
            # self.virtualLEDBuffer *= 0
            # self.virtualLEDBuffer += self.colorSequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

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
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixMarquee.__name__)
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            marquee: MatrixFunction = MatrixFunction(self, MatrixFunction.functionMatrixMarquee, self.colorSequence)
            # set refresh counter
            marquee.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            marquee.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(marquee)
            self.virtualLEDBuffer[0, 0, :] += self.colorSequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

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
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixMarquee.__name__)
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            options = ["hello world", "hi guys", "lol             "]
            if text is None:
                _text = options[random.randint(0, len(options) - 1)]
            else:
                _text = str(text)
            # create the tracking object
            marquee: MatrixFunction = MatrixFunction(self, MatrixFunction.functionMatrixMarquee, self.colorSequence)
            # set refresh counter
            marquee.delayCounter = _delayCount
            # set refresh limit (after which this function will execute)
            marquee.delayCountMax = _delayCount
            # add this function to our function list
            self.privateLightFunctions.append(marquee)
            self.setvirtualLEDBuffer(
                TextMatrix(
                    yRange=self.realLEDYaxisRange,
                    text=_text,
                    color=self.colorSequence[0],
                )
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

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
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixEye.__name__)
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            eye: MatrixFunction = MatrixFunction(self, MatrixFunction.functionMatrixEye, self.colorSequence)
            eye.rowIndex = int(self.realLEDXaxisRange / 2)
            eye.columnIndex = int(self.realLEDYaxisRange / 2)
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
            raise ControllerException from ex

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
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixBounce.__name__)
        try:
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
                off: ArrayFunction = ArrayFunction(self, MatrixFunction.functionOff, self.colorSequence)
                self.privateLightFunctions.append(off)
            else:
                # fade the whole LED strand
                fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
                # by this amount
                fade.fadeAmount = _fadeAmount
                # add function to list
                self.privateLightFunctions.append(fade)
            # create the tracking object
            for _ in range(_ballCount):
                bounce: MatrixFunction = MatrixFunction(self, MatrixFunction.functionMatrixBounce, self.colorSequence)
                bounce.rowIndex = random.randint(0, self.realLEDXaxisRange - 1)
                bounce.columnIndex = random.randint(0, self.realLEDYaxisRange - 1)
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
            raise ControllerException from ex

    def useFunctionMatrixFireworks(
        self,
        delayCount: int = None,
        fireworkCount: int = None,
        fadeAmount=None,
        colorChange=True,
    ) -> None:
        """

        Args:
            delayCount: number of led updates between color updates
            fireworkCount: number of fireworks
            fadeAmount:fade amount
            colorChange: change colors

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixFireworks.__name__)
        try:
            if fadeAmount is None:
                fadeAmount: float = random.randint(10, 50) / 100.0
            # _fadeAmount: float = 0.0
            _delayCount: int = random.randint(0, 3)
            # _delayCount: int = 1
            _zoomyCount: int = random.randint(1, 6)
            # _zoomyCount: int = 1
            if fadeAmount is not None:
                _fadeAmount = int(fadeAmount)
            # make sure fade is valid
            if fadeAmount >= 0.0 or fadeAmount <= 1.0:
                # do nothing
                _fadeAmount = float(fadeAmount)
            elif fadeAmount > 1 and fadeAmount < 256:
                _fadeAmount = float(fadeAmount) / 255
            if _fadeAmount < 0 or _fadeAmount > 1:
                _fadeAmount = 0.1
            if delayCount is not None:
                _delayCount = int(delayCount)
            if fireworkCount is not None:
                _zoomyCount = int(fireworkCount)
            if _fadeAmount == 1.0:
                off: ArrayFunction = ArrayFunction(self, MatrixFunction.functionOff, self.colorSequence)
                self.privateLightFunctions.append(off)
            else:
                # fade the whole LED strand
                fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
                # by this amount
                fade.fadeAmount = _fadeAmount
                # add function to list
                self.privateLightFunctions.append(fade)
            # create the tracking object
            for _ in range(_zoomyCount):
                firework: MatrixFunction = MatrixFunction(
                    self, MatrixFunction.functionMatrixFireworks, self.colorSequence
                )
                firework.rowIndex = random.randint(0, self.realLEDXaxisRange - 1)
                firework.columnIndex = random.randint(0, self.realLEDYaxisRange - 1)
                firework.size = 1
                firework.step = 1
                firework.sizeMax = min(self.realLEDXaxisRange, self.realLEDYaxisRange)
                firework.delayCounter = 0
                # set refresh limit (after which this function will execute)
                firework.delayCountMax = _delayCount
                # add this function to our function list
                firework.color = self.colorSequenceNext
                firework.colorCycle = bool(colorChange)
                self.privateLightFunctions.append(firework)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

    def useFunctionMatrixRadar(
        self,
        delayCount: int = None,
        fadeAmount: float = None,
    ) -> None:
        """

        Args:
            delayCount: number of led updates between color updates
            fireworkCount: number of fireworks
            fadeAmount:fade amount
            colorChange: change colors

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixRadar.__name__)
        try:
            _fadeAmount: float = random.randint(5, 10) / 100.0
            _delayCount: int = random.randint(1, 3)
            if fadeAmount is not None:
                _fadeAmount = float(fadeAmount)
            # make sure fade is valid
            if _fadeAmount > 0.0 or _fadeAmount < 1.0:
                # do nothing
                _fadeAmount = float(_fadeAmount)
            elif _fadeAmount > 1 and _fadeAmount < 256:
                _fadeAmount = float(fadeAmount) / 255
            if _fadeAmount <= 0 or _fadeAmount >= 1:
                _fadeAmount = 0.1
            if delayCount is not None:
                _delayCount = int(delayCount)
            if self.colorSequence is None or len(self.colorSequence) == 0:
                self.colorSequence = ArrayPattern.DefaultColorSequenceByMonth()
            # fade the whole LED strand
            fade: ArrayFunction = ArrayFunction(self, ArrayFunction.functionFadeOff, self.colorSequence)
            # by this amount
            fade.fadeAmount = _fadeAmount
            # add function to list
            self.privateLightFunctions.append(fade)
            # create the tracking object
            radar: MatrixFunction = MatrixFunction(self, MatrixFunction.functionsMatrixRadar, self.colorSequence)
            max_radius = max(int(self.realLEDXaxisRange / 2), int(self.realLEDYaxisRange / 2))
            radar.rowIndex = random.randint(0, self.realLEDXaxisRange - 1)
            radar.columnIndex = random.randint(0, self.realLEDYaxisRange - 1)
            radar.delayCounter = 0
            radar.radius = max_radius
            radar.stepCountMax = 200
            radar.t = np.linspace(-np.pi, np.pi, radar.stepCountMax)
            radar.x = np.linspace(-max_radius, max_radius - 1, radar.stepCountMax)
            # radar.sinx = np.sin(radar.t)
            # radar.cosx = np.cos(radar.t)
            # radar.thetas = np.arctan2(radar.sinx, radar.cosx)
            radar.thetas = np.tan(radar.t)
            radar.x = radar.x.astype(np.int32)
            # set refresh limit (after which this function will execute)
            radar.delayCountMax = _delayCount
            # add this function to our function list
            radar.color = self.colorSequenceNext
            radar.activeChance = 0.01
            radar.enemy = []
            self.privateLightFunctions.append(radar)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

    def useFunctionMatrixSnake(
        self,
        delayCount: int = None,
        snakeLength: int = None,
        snakeCount: int = None,
        collision: bool = True,
    ) -> None:
        """

        Args:
            delayCount: number of led updates between color updates
            snakeLength: length of snake
            colorChange: change colors

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        LOGGER.debug("%s.%s:", self.__class__.__name__, self.useFunctionMatrixSnake.__name__)
        try:
            _delayCount: int = random.randint(1, 3)
            _snakeLength: int = random.randint(3, 30)
            _snakeCount: int = random.randint(1, 4)
            if delayCount is not None:
                _delayCount = int(delayCount)
            if snakeLength is not None:
                _snakeLength = int(snakeLength)
            if snakeCount is not None:
                _snakeCount = int(snakeCount)
            if self.colorSequence is None or len(self.colorSequence) == 0:
                self.colorSequence = ArrayPattern.DefaultColorSequenceByMonth()
            # turn off the whole LED strand each time
            off: ArrayFunction = ArrayFunction(self, ArrayFunction.functionOff, self.colorSequence)
            # add function to list
            self.privateLightFunctions.append(off)
            # create the tracking objects
            for _ in range(_snakeCount):
                snake = MatrixFunction(self, MatrixFunction.functionsMatrixSnake, self.colorSequence)
                snake.sizeMax = _snakeLength
                snake.size = random.randint(int(snake.sizeMax / 2), snake.sizeMax)
                snake.rowIndex = np.ones((snake.size), dtype=np.int32) * random.randint(0, self.realLEDXaxisRange - 1)
                snake.columnIndex = np.ones((snake.size), dtype=np.int32) * random.randint(
                    0, self.realLEDYaxisRange - 1
                )
                snake.stepCountMax = snake.size
                snake.delayCounter = 0
                snake.rowDirection = [-1, 0, 1][random.randint(0, 2)]
                if snake.rowDirection == 0:
                    snake.columnDirection = [-1, 1][random.randint(0, 1)]
                else:
                    snake.columnDirection = 0
                # set refresh limit (after which this function will execute)
                snake.delayCountMax = _delayCount
                # add this function to our function list
                snake.color = self.colorSequenceNext
                snake.collision = collision
                self.privateLightFunctions.append(snake)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise ControllerException from ex

    def getFunctionMatrixMethodsList(self) -> list[str]:
        """Get the list of methods in this class (by name) that set the color functions.

        Returns:
            a list of method name strings
        """
        attrs = list(dir(self))
        functions = [f for f in attrs if f[:17] == "useFunctionMatrix"]
        functions.sort()
        return functions

    def demo(
        self,
        secondsPerMode: float = 0.5,
        functionNames: list[str] = None,
        colorNames: list[str] = None,
        skipFunctions: list[str] = None,
        skipColors: list[str] = None,
        justMatrixFunctions: bool = False,
    ):
        """Run colors and functions semi-randomly.

        Args:
            secondsPerMode: seconds to run current function
            functionNames: function names to run
            colorNames: color pattern names to run
            skipFunctions: function strings to omit (run if "skipFunction not in name")
            skipColors: color pattern strings to omit (run if "skipColor not in name")
            justMatrixFunctions: set true to only use matrix functions

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens
        """
        try:
            _secondsPerMode: int = 60
            if secondsPerMode is not None:
                _secondsPerMode = int(secondsPerMode)
            self.secondsPerMode = _secondsPerMode

            if functionNames is None:
                functionNames = []
            elif not isinstance(functionNames, list):
                functionNames = [functionNames]
            if colorNames is None:
                colorNames = []
            elif not isinstance(colorNames, list):
                colorNames = [colorNames]
            if skipFunctions is None:
                skipFunctions = []
            elif not isinstance(skipFunctions, list):
                skipFunctions = [skipFunctions]
            if skipColors is None:
                skipColors = []
            elif not isinstance(skipColors, list):
                skipColors = [skipColors]

            if justMatrixFunctions:
                functions = self.getFunctionMatrixMethodsList()
            else:
                functions = self.getFunctionMethodsList()
            colors = self.getColorMethodsList()
            # get methods that match user's string
            if len(functionNames) > 0:
                matches = []
                for name in functionNames:
                    matches.extend([f for f in functions if name.lower() in f.lower()])
                functions = matches
            # get methods that match user's string
            if len(colorNames) > 0:
                matches = []
                for name in colorNames:
                    matches.extend([f for f in colors if name.lower() in f.lower()])
                colors = matches
            # remove methods that user requested
            if len(skipFunctions) > 0:
                matches = []
                for name in skipFunctions:
                    for function in functions:
                        if name.lower() in function.lower():
                            functions.remove(function)
            # remove methods that user requested
            if len(skipColors) > 0:
                matches = []
                for name in skipColors:
                    for color in colors:
                        if name.lower() in color.lower():
                            colors.remove(color)

            if len(functions) == 0:
                raise ControllerException("No functions selected in demo")
            elif len(colors) == 0:
                raise ControllerException("No colors selected in demo")
            else:
                while True:
                    try:
                        # make a temporary copy (so we can go through each one)
                        functionsCopy = functions.copy()
                        colorsCopy = colors.copy()
                        # loop while we still have a color and a function
                        while (len(functionsCopy) * len(colorsCopy)) > 0:
                            # get a new function if there is one
                            if len(functionsCopy) > 0:
                                function = functionsCopy[random.randint(0, len(functionsCopy) - 1)]
                                functionsCopy.remove(function)
                            # get a new color pattern if there is one
                            if len(colorsCopy) > 0:
                                color = colorsCopy[random.randint(0, len(colorsCopy) - 1)]
                                colorsCopy.remove(color)
                            # reset
                            self.reset()
                            # apply color
                            getattr(self, color)()
                            # configure function
                            getattr(self, function)()
                            # run the combination
                            self.run()
                    except SystemExit:  # pragma: no cover
                        raise
                    except KeyboardInterrupt:  # pragma: no cover
                        raise
                    except Exception as ex:  # pragma: no cover
                        LOGGER.exception(
                            "%s.%s Exception: %s",
                            self.__class__.__name__,
                            self.demo.__name__,
                            ex,
                        )
        except SystemExit:  # pragma: no cover
            raise
        except KeyboardInterrupt:  # pragma: no cover
            raise
        except Exception as ex:  # pragma: no cover
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.demo.__name__,
                ex,
            )
            raise ControllerException from ex
