from __future__ import annotations

import logging
import random
from typing import Any, Callable, Optional

import numpy as np
from numpy.typing import NDArray

from lightberries.array_controller import ArrayController
from lightberries.array_transforms.base import ArrayTransform
from lightberries.exceptions import ControllerError, LightBerryError
from lightberries.light_sequences.base import ArraySequence
from lightberries.matrix_functions import MatrixFunction
from lightberries.matrix_patterns import DEFAULT_MATRIX_ORDER, MatrixOrder, SolidColorMatrix, Spectrum2, TextMatrix
from lightberries.pixel import PixelColors
from lightberries.ws281x_strings import WS281xString

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
        testing: bool = False,
    ) -> None:
        self.testing = testing
        if not ledXaxisRange:
            ledXaxisRange = 4
        else:
            ledXaxisRange = int(ledXaxisRange)
        if not ledYaxisRange:
            ledYaxisRange = 4
        else:
            ledYaxisRange = int(ledYaxisRange)
        if matrixLayout is not None:
            self.matrixLayout = matrixLayout
            self.matrixCount = matrixLayout.shape[0] * matrixLayout.shape[1]
            self.matrixShape = matrixShape
        else:
            self.matrixLayout = None
            self.matrixCount = None
            self.matrixShape = None
        super().__init__(
            led_count=(ledYaxisRange * ledXaxisRange),
            pwm_gpio_pin=pwmGPIOpin,
            dma_channel=channelDMA,
            pwm_frequency=frequencyPWM,
            pwm_invert_signal=invertSignalPWM,
            led_brightness=ledBrightnessFloat,
            pwm_channel=channelPWM,
            led_strip_type=stripTypeLED,
            gamma=gamma,
            debug=debug,
            verbose=verbose,
            refresh_callback=refreshCallback,
            simulate=simulate,
            testing=testing,
        )
        self.realLEDYaxisRange = ledXaxisRange
        self.realLEDXaxisRange = ledYaxisRange
        self.virtualLEDYaxisRange = ledXaxisRange
        self.virtualLEDXaxisRange = ledYaxisRange
        self.virtualLEDIndexBuffer: np.ndarray[(Any,), np.int32]
        self.set_virtual_led_buffer(
            SolidColorMatrix(
                xRange=self.realLEDXaxisRange,
                yRange=self.realLEDYaxisRange,
                color=PixelColors.OFF,
            ),
        )

        # give LightFunction class a pointer to this class
        MatrixFunction.Controller = self

    def _instantiate_WS281xString(
        self,
        ledCount: int,
        pwmGPIOpin: int,
        channelDMA: int,
        frequencyPWM: int,
        invertSignalPWM: bool,
        ledBrightnessFloat: float,
        channelPWM: int,
        stripTypeLED: Any,
        gamma: Any,
        simulate: bool,
        testing: bool = False,
    ) -> None:
        self.ws281xString: Optional[WS281xString] = WS281xString(
            led_count=ledCount,
            pwm_gpio_pin=pwmGPIOpin,
            dma_channel=channelDMA,
            pwm_frequency=frequencyPWM,
            pwm_invert_signal=invertSignalPWM,
            led_brightness=ledBrightnessFloat,
            pwm_channel=channelPWM,
            led_strip_type=stripTypeLED,
            led_gamma=gamma,
            simulate=simulate,
            matrix_shape=self.matrixShape,
            matrix_layout=self.matrixLayout,
        )

    def useColorMatrix(
        self,
        matrix: np.ndarray[(Any, Any, 3), np.int32] = None,
    ) -> None:
        """Sets the the color sequence used by light functions to one of your choice.

        Args:
        ----

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        try:
            LOGGER.debug(
                "\n%s.%s:",
                self.__class__.__name__,
                self.useColorMatrix.__name__,
            )

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
                matrix = Spectrum2(
                    xRange=self.realLEDXaxisRange,
                    yRange=self.realLEDYaxisRange,
                )

            self.virtualLEDXaxisRange = matrix.shape[0]
            self.virtualLEDYaxisRange = matrix.shape[1]

            self.virtual_led_buffer = matrix
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def set_virtual_led_buffer(
        self,
        ledMatrix: np.ndarray[(3, Any, Any), np.int32],
    ) -> None:
        self.virtualLEDXaxisRange = ledMatrix.shape[0]
        self.virtualLEDYaxisRange = ledMatrix.shape[1]
        self.virtual_led_buffer = ledMatrix
        self._virtual_led_count = int(ledMatrix.size / 3)
        if self.matrixLayout is None:
            self.virtual_led_buffer = ledMatrix
            self._virtual_led_count = int(ledMatrix.size / 3)
            self.virtualLEDIndexBuffer = np.arange(self.virtual_led_count)
            if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow.value:
                self.virtualLEDIndexBuffer = np.reshape(
                    self.virtualLEDIndexBuffer,
                    (self.virtualLEDXaxisRange, self.virtualLEDYaxisRange),
                )
                for i in range(1, self.virtualLEDXaxisRange, 2):
                    self.virtualLEDIndexBuffer[i, :] = np.flip(
                        self.virtualLEDIndexBuffer[i, :],
                    )
            elif DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseRowThenColumn.value:
                self.virtualLEDIndexBuffer = np.reshape(
                    self.virtualLEDIndexBuffer,
                    (self.virtualLEDXaxisRange, self.virtualLEDYaxisRange),
                )
                for i in range(1, self.virtualLEDYaxisRange, 2):
                    self.virtualLEDIndexBuffer[i, :] = np.flip(
                        self.virtualLEDIndexBuffer[i, :],
                    )
        else:
            matrix_led_count = self.matrixShape[0] * self.matrixShape[1]
            led_count = ledMatrix.shape[0] * ledMatrix.shape[1]
            if led_count % self.real_led_count:
                led_count -= led_count % matrix_led_count
                led_count += self.real_led_count
            self.virtualLEDIndexBuffer = np.zeros(
                (self.realLEDYaxisRange, self.realLEDXaxisRange),
                dtype=np.int32,
            )
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
                    self.virtualLEDIndexBuffer[
                        c : c + self.matrixShape[1],
                        r : r + self.matrixShape[0],
                    ] = temp

    def reset(
        self,
    ) -> None:
        """Reset class variables to default state.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        try:
            self._transforms = []
            if self.virtual_led_count > self.real_led_count:
                self.set_virtual_led_buffer(
                    self.virtual_led_buffer[
                        : self.realLEDXaxisRange,
                        : self.realLEDYaxisRange,
                    ],
                )
            elif self.virtual_led_count < self.real_led_count:
                array = SolidColorMatrix(
                    xRange=self.realLEDXaxisRange,
                    yRange=self.realLEDYaxisRange,
                    color=PixelColors.OFF,
                )
                try:
                    array[: self.virtualLEDXaxisRange, : self.virtualLEDYaxisRange] = self.virtual_led_buffer
                except:  # noqa
                    pass
                self.set_virtual_led_buffer(array)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def copy_virtual_leds_to_ws281x(
        self,
    ) -> None:
        """Sets each Pixel in the rpi_ws281x object to the buffered array value.

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        try:
            # callback function to do work

            def SetPixel(i_rgb):
                i = i_rgb[0]
                rgb = i_rgb[1]
                if i < self.real_led_count:
                    self.ws281xString[i] = rgb

            # fast method of calling the callback method on each index of LED array
            if len(self.virtual_led_buffer.shape) > 2:
                if DEFAULT_MATRIX_ORDER is MatrixOrder.TraverseColumnThenRow.value:
                    list(
                        map(
                            SetPixel,
                            zip(
                                self.virtualLEDIndexBuffer[
                                    np.where(
                                        self.virtualLEDIndexBuffer < self.real_led_count,
                                    )
                                ],
                                self.virtual_led_buffer[
                                    np.where(
                                        self.virtualLEDIndexBuffer < self.real_led_count,
                                    )
                                ],
                            ),
                        ),
                    )
                else:
                    list(
                        map(
                            SetPixel,
                            enumerate(
                                self.virtual_led_buffer.reshape(
                                    (
                                        self.virtualLEDXaxisRange * self.virtualLEDYaxisRange,
                                        3,
                                    ),
                                )[self.virtualLEDIndexBuffer][
                                    np.where(
                                        self.virtualLEDIndexBuffer < self.real_led_count,
                                    )
                                ],
                            ),
                        ),
                    )
            else:
                list(
                    map(
                        SetPixel,
                        enumerate(
                            self.virtual_led_buffer[self.virtualLEDIndexBuffer][
                                np.where(self.virtualLEDIndexBuffer < self.real_led_count)
                            ],
                        ),
                    ),
                )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixColorFlux(
        self,
        delayCount: int = None,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixColorFlux.__name__,
        )
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            flux: MatrixFunction = MatrixFunction(
                self,
                MatrixFunction.functionMatrixColorFlux,
                self.color_sequence,
            )
            # set refresh counter
            flux._delay_counter = _delayCount
            # set refresh limit (after which this function will execute)
            flux._delay_count_max = _delayCount
            # add this function to our function list
            self._transforms.append(flux)
            # clear LEDs, assign first color in sequence to all LEDs
            # self.virtualLEDBuffer *= 0
            # self.virtualLEDBuffer += self.colorSequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixMarquee(
        self,
        delayCount: int = None,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixMarquee.__name__,
        )
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            marquee: MatrixFunction = MatrixFunction(
                self,
                MatrixFunction.functionMatrixMarquee,
                self.color_sequence,
            )
            # set refresh counter
            marquee._delay_counter = _delayCount
            # set refresh limit (after which this function will execute)
            marquee._delay_count_max = _delayCount
            # add this function to our function list
            self._transforms.append(marquee)
            self.virtual_led_buffer[0, 0, :] += self.color_sequence[0, :]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixMarqueeText(
        self,
        delayCount: int = None,
        text: str = None,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixMarquee.__name__,
        )
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
            marquee: MatrixFunction = MatrixFunction(
                self,
                MatrixFunction.functionMatrixMarquee,
                self.color_sequence,
            )
            # set refresh counter
            marquee._delay_counter = _delayCount
            # set refresh limit (after which this function will execute)
            marquee._delay_count_max = _delayCount
            # add this function to our function list
            self._transforms.append(marquee)
            self.set_virtual_led_buffer(
                TextMatrix(
                    yRange=self.realLEDYaxisRange,
                    text=_text,
                    color=self.color_sequence[0],
                ),
            )
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixEye(
        self,
        delayCount: int = None,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixEye.__name__,
        )
        try:
            _delayCount: int = random.randint(0, 5)
            if delayCount is not None:
                _delayCount = int(delayCount)
            # create the tracking object
            eye: MatrixFunction = MatrixFunction(
                self,
                MatrixFunction.functionMatrixEye,
                self.color_sequence,
            )
            eye.rowIndex = int(self.realLEDXaxisRange / 2)
            eye.columnIndex = int(self.realLEDYaxisRange / 2)
            # set refresh counter
            eye._delay_counter = _delayCount
            # set refresh limit (after which this function will execute)
            eye._delay_count_max = _delayCount
            # add this function to our function list
            self._transforms.append(eye)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixBounce(
        self,
        delayCount: int = None,
        ballCount: int = None,
        fadeAmount=None,
        colorChange=False,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates
            ballCount: number of bouncy balls
            fadeAmount:fade amount
            colorChange: change colors

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixBounce.__name__,
        )
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
                off: ArrayTransform = ArrayTransform(
                    self,
                    MatrixFunction.functionOff,
                    self.color_sequence,
                )
                self._transforms.append(off)
            else:
                # fade the whole LED strand
                fade: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionFadeOff,
                    self.color_sequence,
                )
                # by this amount
                fade._fade_amount = _fadeAmount
                # add function to list
                self._transforms.append(fade)
            # create the tracking object
            for _ in range(_ballCount):
                bounce: MatrixFunction = MatrixFunction(
                    self,
                    MatrixFunction.functionMatrixBounce,
                    self.color_sequence,
                )
                bounce.rowIndex = random.randint(0, self.realLEDXaxisRange - 1)
                bounce.columnIndex = random.randint(0, self.realLEDYaxisRange - 1)
                bounce.rowDirection = [-1, 1][random.randint(0, 1)]
                bounce.columnDirection = [-1, 1][random.randint(0, 1)]
                bounce.rowStep = random.randint(1, 2)
                bounce.columnStep = random.randint(1, 2)
                # set refresh counter
                bounce._delay_counter = _delayCount
                # set refresh limit (after which this function will execute)
                bounce._delay_count_max = _delayCount
                # add this function to our function list
                bounce._color = self.color_sequence_next
                bounce._color_cycle = bool(colorChange)
                self._transforms.append(bounce)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixFireworks(
        self,
        delayCount: int = None,
        fireworkCount: int = None,
        fadeAmount=None,
        colorChange=True,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates
            fireworkCount: number of fireworks
            fadeAmount:fade amount
            colorChange: change colors

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixFireworks.__name__,
        )
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
                off: ArrayTransform = ArrayTransform(
                    self,
                    MatrixFunction.functionOff,
                    self.color_sequence,
                )
                self._transforms.append(off)
            else:
                # fade the whole LED strand
                fade: ArrayTransform = ArrayTransform(
                    self,
                    ArrayTransform.functionFadeOff,
                    self.color_sequence,
                )
                # by this amount
                fade._fade_amount = _fadeAmount
                # add function to list
                self._transforms.append(fade)
            # create the tracking object
            for _ in range(_zoomyCount):
                firework: MatrixFunction = MatrixFunction(
                    self,
                    MatrixFunction.functionMatrixFireworks,
                    self.color_sequence,
                )
                firework.rowIndex = random.randint(0, self.realLEDXaxisRange - 1)
                firework.columnIndex = random.randint(0, self.realLEDYaxisRange - 1)
                firework._size = 1
                firework._step = 1
                firework._size_max = min(self.realLEDXaxisRange, self.realLEDYaxisRange)
                firework._delay_counter = 0
                # set refresh limit (after which this function will execute)
                firework._delay_count_max = _delayCount
                # add this function to our function list
                firework._color = self.color_sequence_next
                firework._color_cycle = bool(colorChange)
                self._transforms.append(firework)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixRadar(
        self,
        delayCount: int = None,
        fadeAmount: float = None,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates
            fireworkCount: number of fireworks
            fadeAmount:fade amount
            colorChange: change colors

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixRadar.__name__,
        )
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
            if self.color_sequence is None or len(self.color_sequence) == 0:
                self.color_sequence = ArraySequence.default_color_sequence_by_month()
            # fade the whole LED strand
            fade: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionFadeOff,
                self.color_sequence,
            )
            # by this amount
            fade._fade_amount = _fadeAmount
            # add function to list
            self._transforms.append(fade)
            # create the tracking object
            radar: MatrixFunction = MatrixFunction(
                self,
                MatrixFunction.functionsMatrixRadar,
                self.color_sequence,
            )
            max_radius = max(
                int(self.realLEDXaxisRange / 2),
                int(self.realLEDYaxisRange / 2),
            )
            radar.rowIndex = random.randint(0, self.realLEDXaxisRange - 1)
            radar.columnIndex = random.randint(0, self.realLEDYaxisRange - 1)
            radar._delay_counter = 0
            radar.radius = max_radius
            radar._step_count_max = 200
            radar.t = np.linspace(-np.pi, np.pi, radar._step_count_max)
            radar.x = np.linspace(-max_radius, max_radius - 1, radar._step_count_max)
            # radar.sinx = np.sin(radar.t)
            # radar.cosx = np.cos(radar.t)
            # radar.thetas = np.arctan2(radar.sinx, radar.cosx)
            radar.thetas = np.tan(radar.t)
            radar.x = radar.x.astype(np.int32)
            # set refresh limit (after which this function will execute)
            radar._delay_count_max = _delayCount
            # add this function to our function list
            radar._color = self.color_sequence_next
            radar._active_chance = 0.01
            radar.enemy = []
            self._transforms.append(radar)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def useFunctionMatrixSnake(
        self,
        delayCount: int = None,
        snakeLength: int = None,
        snakeCount: int = None,
        collision: bool = True,
    ) -> None:
        """Args:
        ----
            delayCount: number of led updates between color updates
            snakeLength: length of snake
            colorChange: change colors

        Raises
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        LOGGER.debug(
            "%s.%s:",
            self.__class__.__name__,
            self.useFunctionMatrixSnake.__name__,
        )
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
            if self.color_sequence is None or len(self.color_sequence) == 0:
                self.color_sequence = ArraySequence.default_color_sequence_by_month()
            # turn off the whole LED strand each time
            off: ArrayTransform = ArrayTransform(
                self,
                ArrayTransform.functionOff,
                self.color_sequence,
            )
            # add function to list
            self._transforms.append(off)
            # create the tracking objects
            for _ in range(_snakeCount):
                snake = MatrixFunction(
                    self,
                    MatrixFunction.functionsMatrixSnake,
                    self.color_sequence,
                )
                snake._size_max = _snakeLength
                snake._size = random.randint(int(snake._size_max / 2), snake._size_max)
                snake.rowIndex = np.ones(
                    (snake._size),
                    dtype=np.int32,
                ) * random.randint(0, self.realLEDXaxisRange - 1)
                snake.columnIndex = np.ones(
                    (snake._size),
                    dtype=np.int32,
                ) * random.randint(0, self.realLEDYaxisRange - 1)
                snake._step_count_max = snake._size
                snake._delay_counter = 0
                snake.rowDirection = [-1, 0, 1][random.randint(0, 2)]
                if snake.rowDirection == 0:
                    snake.columnDirection = [-1, 1][random.randint(0, 1)]
                else:
                    snake.columnDirection = 0
                # set refresh limit (after which this function will execute)
                snake._delay_count_max = _delayCount
                # add this function to our function list
                snake._color = self.color_sequence_next
                snake._collision = collision
                self._transforms.append(snake)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryError:
            raise
        except Exception as ex:
            raise ControllerError from ex

    def getFunctionMatrixMethodsList(self) -> list[str]:
        """Get the list of methods in this class (by name) that set the color functions.

        Returns
        -------
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
        ----
            secondsPerMode: seconds to run current function
            functionNames: function names to run
            colorNames: color pattern names to run
            skipFunctions: function strings to omit (run if "skipFunction not in name")
            skipColors: color pattern strings to omit (run if "skipColor not in name")
            justMatrixFunctions: set true to only use matrix functions

        Raises:
        ------
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightControlException: if something bad happens

        """
        try:
            _secondsPerMode: int = 60
            if secondsPerMode is not None:
                _secondsPerMode = int(secondsPerMode)
            self.seconds_per_mode = _secondsPerMode

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
                functions = self.get_function_methods_list()
            colors = self.get_color_methods_list()
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
                raise ControllerError("No functions selected in demo")
            elif len(colors) == 0:
                raise ControllerError("No colors selected in demo")
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
            raise ControllerError from ex
