from __future__ import annotations
from lightberries.array_functions import (
    ArrayFunction,
    LEDFadeType,
    RaindropStates,
    SpriteState,
    ThingColors,
    ThingMoves,
    ThingSizes,
)
from numpy.typing import NDArray
from lightberries.array_patterns import ArrayPattern, ConvertPixelArrayToNumpyArray
from lightberries.pixel import PixelColors
from numpy.testing import assert_array_equal
from lightberries.array_controller import ArrayController
from lightberries.ws281x_strings import WS281xString, WS281xStringError
import numpy as np
from typing import Any
import mock
import lightberries.rpiws281x_patch


def new_instantiate_pixelstrip(
    self,
    pwmGPIOpin: int,
    channelDMA: int,
    ledCount: int,
    frequencyPWM: int,
    channelPWM: int,
    invertSignalPWM: bool,
    gamma: float,
    stripTypeLED: Any,
    ledBrightnessFloat: Any,
    testing: bool,
    matrixShape: tuple[int, int] = None,
    matrixLayout: NDArray[np.int32] | None = None,
) -> None:
    try:
        # create ws281x pixel strip
        self.ws281xPixelStrip = lightberries.rpiws281x_patch.PixelStrip(
            pin=pwmGPIOpin,
            dma=channelDMA,
            num=ledCount,
            freq_hz=frequencyPWM,
            channel=channelPWM,
            invert=invertSignalPWM,
            gamma=gamma,
            strip_type=stripTypeLED,
            brightness=int(255 * ledBrightnessFloat),
        )
    except SystemExit:  # pragma: no cover
        raise
    except KeyboardInterrupt:  # pragma: no cover
        raise
    except Exception as ex:  # pragma: no cover
        raise WS281xStringError from ex


def new_instantiate_WS281xString(
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
    testing: bool,
    matrixShape: tuple[int, int] = None,
    matrixLayout: NDArray[np.int32] | None = None,
) -> None:
    with mock.patch.object(
        WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip
    ):
        self.ws281xString = WS281xString(
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
            testing=testing,
            matrix_shape=matrixShape,
            matrix_layout=matrixLayout,
        )


def newController() -> ArrayController:
    with mock.patch.object(
        ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString
    ):
        return ArrayController(
            ledCount=3,
            simulate=True,
        )


def newControllerBigger() -> ArrayController:
    with mock.patch.object(
        ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString
    ):
        return ArrayController(
            ledCount=6,
            simulate=True,
        )


def assert_func(func: ArrayFunction):
    assert func is not None
    assert isinstance(func, ArrayFunction)


def test_creation_simple():
    control = newController()
    function = ArrayFunction(control, assert_func)
    control.functionList.append(function)
    assert function is not None
    assert isinstance(function, ArrayFunction)


def test_creation_with_colors():
    control = newController()
    pattern = ArrayPattern.DefaultColorSequenceByMonth()
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert function is not None
    assert isinstance(function, ArrayFunction)


def test_str():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert str(function) == '[0]: "assert_func" PX #FF0000'


def test_repr():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert repr(function) == '<ArrayFunction> [0]: "assert_func" PX #FF0000'


def test_run():
    control = newController()
    function = ArrayFunction(control, assert_func)
    control.functionList.append(function)
    control._runFunctions()
    function.run()


def test_colorSequenceCount():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(newController(), assert_func, pattern)
    control.functionList.append(function)
    assert function.color_sequence_count == len(pattern)


def test_colorSequenceIndex():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert function.color_sequence_index == 0


def test_colorSequenceNext():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    left = function._color
    right = PixelColors.RED.array
    assert_array_equal(left, right)
    left = function.color_sequence_next
    right = PixelColors.GREEN.array
    assert_array_equal(left, right)
    left = function.color_sequence_next
    right = PixelColors.BLUE.array
    assert_array_equal(left, right)
    left = function.color_sequence_next
    right = PixelColors.RED.array
    assert_array_equal(left, right)


# def test_colorSequenceNext_rollover():
#     control = newController()
#     pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
#     function = ArrayFunction(control, assert_func, pattern)
#     control.functionList.append(function)
#     function.colorSequenceNext
#     function.colorSequenceNext
#     function.colorSequenceNext
#     left = function.colorSequenceNext
#     right = PixelColors.RED.array
#     assert_array_equal(left, right)


def test_doFade():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function = ArrayFunction(control, ArrayFunction.do_fade, pattern)
    control.functionList.append(function)
    delay_count = 2
    function._delay_count_max = delay_count
    function._fade_amount = 1.0
    assert_array_equal(function._color, PixelColors.RED.array)
    assert function._delay_counter == 0
    control._runFunctions()
    assert function._delay_counter == 1
    control._runFunctions()
    assert function._delay_counter == 0
    assert_array_equal(function._color, PixelColors.OFF.array)
    function._color_next = PixelColors.PINK.array
    control._runFunctions()
    assert function._delay_counter == 1
    control._runFunctions()
    assert function._delay_counter == 0
    assert_array_equal(function._color, PixelColors.PINK.array)
    function._color_next = PixelColors.GREEN.array
    control._runFunctions()
    assert function._delay_counter == 1
    control._runFunctions()
    assert function._delay_counter == 0
    assert_array_equal(function._color, PixelColors.GREEN.array)
    function._delay_count_max = 0
    function._fade_amount = -1.0
    control._runFunctions()
    function._fade_amount = 2567.0
    control._runFunctions()


def test_updateArrayIndex_singlestep():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    control.functionList.append(function)
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        control._runFunctions()
        assert function._index == (i + 1) % ArrayFunction.Controller.realLEDCount
        assert function._step == 1
        assert function._direction == 1
        assert_array_equal(
            function._index_range,
            np.array([(i + 1) % ArrayFunction.Controller.realLEDCount]),
        )
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1


def test_updateArrayIndex_largestep():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    control.functionList.append(function)
    function._step = 2
    assert function._index == 0
    assert function._step == 2
    assert function._direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        control._runFunctions()
        begin_idx = function._index_previous + 1
        idx = begin_idx + (function._step - 1)
        assert function._index == idx % ArrayFunction.Controller.realLEDCount
        assert function._step == 2
        assert function._direction == 1
        assert_array_equal(
            function._index_range,
            np.array(
                [
                    j % ArrayFunction.Controller.realLEDCount
                    for j in range(begin_idx, idx + 1)
                ]
            ),
        )
    assert function._index == 0
    assert function._step == 2
    assert function._direction == 1


def test_functionCollisionDetection_only_one():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function = ArrayFunction(control, ArrayFunction.functionCollisionDetection, pattern)
    control.functionList.append(function)
    function._step = 1
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        control._runFunctions()
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1
    assert function._collision is False


def test_functionCollisionDetection_small_step():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function1 = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    function2 = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    function3 = ArrayFunction(
        control, ArrayFunction.functionCollisionDetection, pattern
    )
    control.functionList.append(function1)
    control.functionList.append(function2)
    control.functionList.append(function3)
    function2._index = control.realLEDCount - 1
    function2._direction = -1
    assert function1._index == 0
    assert function1._step == 1
    assert function1._direction == 1
    control._runFunctions()
    assert function1._index == 1
    assert function1._index_range == [1]
    assert function1._step == 1
    assert function1._direction == 1
    assert function1._collision is False


def test_functionCollisionDetection_large_step():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function1 = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    function2 = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    function3 = ArrayFunction(
        control, ArrayFunction.functionCollisionDetection, pattern
    )
    function3._explode = True
    control.functionList.append(function1)
    control.functionList.append(function2)
    control.functionList.append(function3)
    function1._step = 2
    function1._collision_enabled = True
    function2._step = 2
    function2._collision_enabled = True
    function2._index = control.realLEDCount - 1
    function2._direction = -1
    assert function1._index == 0
    assert function1._step == 2
    assert function1._direction == 1
    assert function2._index == 2
    assert function2._step == 2
    assert function2._direction == -1
    control._runFunctions()
    assert function1._index == 0
    assert 1 in function1._index_range and 2 in function1._index_range
    assert 1 in function1._collision_intersection
    assert function1._step == 2
    assert function1._direction == -1
    assert function1._collision is True
    assert function1._collision_with == function2
    assert function2._index == 2
    assert 1 in function2._index_range and 0 in function2._index_range
    assert 1 in function2._collision_intersection
    assert function2._step == 2
    assert function2._direction == 1
    assert function1._collision is True
    assert function2._collision_with == function1


def test_functionCollisionDetection_slow_fast():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    function1 = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    function2 = ArrayFunction(control, ArrayFunction.update_array_index, pattern)
    function3 = ArrayFunction(
        control, ArrayFunction.functionCollisionDetection, pattern
    )
    function3._explode = True
    control.functionList.append(function1)
    control.functionList.append(function2)
    control.functionList.append(function3)
    function1._step = 3
    function1._collision_enabled = True
    function2._collision_enabled = True
    function2._index = 1
    assert function1._index == 0
    assert function1._step == 3
    assert function1._direction == 1
    assert function2._index == 1
    assert function2._step == 1
    assert function2._direction == 1
    control._runFunctions()
    assert function1._index == 2
    assert 2 in function1._index_range
    assert 2 in function1._collision_intersection
    assert function1._step == 1
    assert function1._direction == 1
    assert function1._collision is True
    assert function1._collision_with == function2
    assert function2._index == 1
    assert 2 in function2._index_range
    assert 2 in function2._collision_intersection
    assert function2._step == 3
    assert function2._direction == 1
    assert function1._collision is True
    assert function2._collision_with == function1
    control._runFunctions()
    assert function1._collision is True
    assert function1._collision_with == function2
    assert function1._collision is True
    assert function2._collision_with == function1


def test_functionOff():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.PINK]
    )
    off = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    control.setvirtualLEDBuffer(pattern)
    function1 = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, pattern)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, off)


def test_functionFadeOff():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    half = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED2, PixelColors.GREEN2, PixelColors.BLUE2]
    )
    quarter = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED3, PixelColors.GREEN3, PixelColors.BLUE3]
    )
    eighth = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED4, PixelColors.GREEN4, PixelColors.BLUE4]
    )
    control.setvirtualLEDBuffer(pattern)
    function1 = ArrayFunction(control, ArrayFunction.functionFadeOff, pattern)
    function1._fade_amount = 0.5
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert function1._fade_amount == 0.5
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, half)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, quarter)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, eighth)


def test_functionSolidColorCycle():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.RED, PixelColors.RED]
    )
    three = ConvertPixelArrayToNumpyArray(
        [PixelColors.GREEN, PixelColors.GREEN, PixelColors.GREEN]
    )
    four = ConvertPixelArrayToNumpyArray(
        [PixelColors.BLUE, PixelColors.BLUE, PixelColors.BLUE]
    )
    function1 = ArrayFunction(control, ArrayFunction.functionSolidColorCycle, pattern)
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, four)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionFade():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED2, PixelColors.RED2, PixelColors.RED2]
    ) + [1, 0, 0]
    three = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.RED, PixelColors.RED]
    ) + [1, 0, 0]
    three -= [1, 0, 0]
    function1 = ArrayFunction(control, ArrayFunction.functionFade, pattern)
    function1._fade_amount = 0.5
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    function1._color = PixelColors.OFF.array
    control.virtualLEDBuffer += [1, 0, 0]
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    function1._delay_count_max = 0
    function1._fade_amount = -1.0
    control._runFunctions()
    function1._fade_amount = 2567.0
    control._runFunctions()


def test_functionMarquee():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED])
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.RED, PixelColors.OFF]
    )
    three = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.RED]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionMarquee, pattern)
    control.functionList.append(function)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionCylon():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED])
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.RED, PixelColors.OFF]
    )
    three = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.RED]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionCylon, pattern)
    control.functionList.append(function)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionMerge():
    control = newControllerBigger()
    pattern = ConvertPixelArrayToNumpyArray(
        [
            PixelColors.RED,
            PixelColors.OFF,
            PixelColors.OFF,
            PixelColors.OFF,
            PixelColors.OFF,
            PixelColors.RED,
        ]
    )
    one = np.array([0, 1, 2, 3, 4, 5])
    two = np.array([2, 0, 1, 1, 0, 2])
    three = np.array([1, 2, 0, 0, 2, 1])
    four = np.array([0, 1, 2, 2, 1, 0])
    function = ArrayFunction(control, ArrayFunction.functionMerge, pattern)
    function._size = 3
    control.functionList.append(function)
    control.setvirtualLEDBuffer(pattern)
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, four)


def test_functionAccelerate():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.RED, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.RED]
    )
    three = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.RED, PixelColors.RED]
    )
    four = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.RED, PixelColors.RED]
    )
    five = ConvertPixelArrayToNumpyArray(
        [PixelColors.GREEN, PixelColors.GREEN, PixelColors.GREEN]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionAccelerate, pattern)
    function._state_max = 5
    control.functionList.append(function)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, four)
    function._color_cycle = True
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, five)
    control._runFunctions()


def test_functionRandomChange():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    off = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    function = ArrayFunction(control, ArrayFunction.functionRandomChange, pattern)
    function._color_next = function._color
    function._fade_amount = 1
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, off)
    control._runFunctions()
    control._runFunctions()
    control._runFunctions()
    control._runFunctions()
    while not np.array_equal(function._color_next, control.backgroundColor):
        control._runFunctions()
    control._runFunctions()
    function._fade_type = LEDFadeType.INSTANT_OFF
    control._runFunctions()


def test_functionMeteors():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    initial = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.RED, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.RED]
    )
    three = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.OFF]
    )
    four = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.GREEN, PixelColors.OFF]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionMeteors, pattern)
    function._fade_amount = 1
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    function._color_cycle = True
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, four)


def test_functionSprites():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    initial = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionSprites, pattern)
    function._fade_amount = 1.0
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    while function._state == SpriteState.OFF.value:
        control._runFunctions()
    function._step_counter = 0
    while function._state != SpriteState.OFF.value:
        control._runFunctions()


def test_functionRaindrops():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    initial = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    one = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.RED, PixelColors.OFF]
    )
    two = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.RED]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionRaindrops, pattern)
    function._fade_amount = 1.0
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    control._runFunctions()
    while function._index != 1:
        control._runFunctions()
    # assert_array_equal(control.virtualLEDBuffer, one)
    while function._state == RaindropStates.OFF.value:
        control._runFunctions()
    function._step_count_max = 2
    function._color = PixelColors.RED.array
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionAlive():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    initial = ConvertPixelArrayToNumpyArray(
        [PixelColors.OFF, PixelColors.OFF, PixelColors.OFF]
    )
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionAlive, pattern)
    function._fade_amount = 1.0
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    control._runFunctions()
    while not function._state & ThingMoves.METEOR.value:
        control._runFunctions()
    while not function._state & ThingMoves.LIGHTSPEED.value:
        control._runFunctions()
    while not function._state & ThingMoves.TURTLE.value:
        control._runFunctions()
    while not function._state & ThingSizes.GROW.value:
        control._runFunctions()
    while not function._state & ThingSizes.SHRINK.value:
        control._runFunctions()
    while not function._state & ThingColors.CYCLE.value:
        control._runFunctions()
    control._runFunctions()
    while not function._state & ThingSizes.GROW.value:
        control._runFunctions()
    function._size_max = 5
    function._size = 2
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()
    while not function._state & ThingSizes.GROW.value:
        control._runFunctions()
    function._size_max = 5
    function._size = 3
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()
    while not function._state & ThingSizes.GROW.value:
        control._runFunctions()
    function._size_max = 5
    function._size = 0
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()
    while not function._state & ThingSizes.GROW.value:
        control._runFunctions()
    function._size_max = 5
    function._size = 6
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()
    while not function._state & ThingMoves.LIGHTSPEED.value:
        control._runFunctions()
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()
    while not function._state & ThingSizes.GROW.value:
        control._runFunctions()
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()
    while not function._state & ThingSizes.SHRINK.value:
        control._runFunctions()
    function._delay_count_max = 0
    function._step_count_max = 114
    control._runFunctions()


def test_overlayTwinkle():
    control = newControllerBigger()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(control, ArrayFunction.overlayTwinkle, pattern)
    function._random = 0.0
    control.functionList.append(function)
    control._runFunctions()
    control._copyOverlays()
    assert np.sum(np.array(control.ws281xString)) != 0


def test_overlayBlink():
    control = newControllerBigger()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]
    )
    function = ArrayFunction(control, ArrayFunction.overlayBlink, pattern)
    function._random = 0.0
    control.functionList.append(function)
    control._runFunctions()
    control._copyOverlays()
    assert np.sum(np.array(control.ws281xString)) != 0
