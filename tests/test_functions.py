from __future__ import annotations

from typing import Any
from unittest import mock

import numpy as np
from numpy.testing import assert_array_equal
from numpy.typing import NDArray

import lightberries.rpiws281x_patch
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.base import ArraySequence, pixel_array_to_numpy_array
from lightberries.array_transform.base import (
    ArrayTransform,
    LEDFadeType,
    RaindropStates,
    SpriteState,
    ThingColors,
    ThingMoves,
    ThingSizes,
)
from lightberries.pixel import PixelColor
from lightberries.ws281x_strings import WS281xString, WS281xStringError


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
        WS281xString,
        "_instantiate_pixelstrip",
        new=new_instantiate_pixelstrip,
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
        ArrayController,
        "_instantiate_WS281xString",
        new_instantiate_WS281xString,
    ):
        return ArrayController(
            led_count=3,
            simulate=True,
        )


def newControllerBigger() -> ArrayController:
    with mock.patch.object(
        ArrayController,
        "_instantiate_WS281xString",
        new_instantiate_WS281xString,
    ):
        return ArrayController(
            led_count=6,
            simulate=True,
        )


def assert_func(func: ArrayTransform):
    assert func is not None
    assert isinstance(func, ArrayTransform)


def test_creation_simple():
    control = newController()
    function = ArrayTransform(control, assert_func)
    control.function_list.append(function)
    assert function is not None
    assert isinstance(function, ArrayTransform)


def test_creation_with_colors():
    control = newController()
    pattern = ArraySequence.default_color_sequence_by_month()
    function = ArrayTransform(control, assert_func, pattern)
    control.function_list.append(function)
    assert function is not None
    assert isinstance(function, ArrayTransform)


def test_str():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(control, assert_func, pattern)
    control.function_list.append(function)
    assert str(function) == '[0]: "assert_func" PX #FF0000'


def test_repr():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(control, assert_func, pattern)
    control.function_list.append(function)
    assert repr(function) == '<ArrayFunction> [0]: "assert_func" PX #FF0000'


def test_run():
    control = newController()
    function = ArrayTransform(control, assert_func)
    control.function_list.append(function)
    control._run_functions()
    function._transform()


def test_colorSequenceCount():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(newController(), assert_func, pattern)
    control.function_list.append(function)
    assert function.color_sequence_count == len(pattern)


def test_colorSequenceIndex():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(control, assert_func, pattern)
    control.function_list.append(function)
    assert function.color_sequence_index == 0


def test_colorSequenceNext():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(control, assert_func, pattern)
    control.function_list.append(function)
    left = function._color
    right = PixelColor.RED.array
    assert_array_equal(left, right)
    left = function.color_sequence_next
    right = PixelColor.GREEN.array
    assert_array_equal(left, right)
    left = function.color_sequence_next
    right = PixelColor.BLUE.array
    assert_array_equal(left, right)
    left = function.color_sequence_next
    right = PixelColor.RED.array
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
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function = ArrayTransform(control, ArrayTransform.do_fade, pattern)
    control.function_list.append(function)
    delay_count = 2
    function._delay_count_max = delay_count
    function._fade_amount = 1.0
    assert_array_equal(function._color, PixelColor.RED.array)
    assert function._delay_counter == 0
    control._run_functions()
    assert function._delay_counter == 1
    control._run_functions()
    assert function._delay_counter == 0
    assert_array_equal(function._color, PixelColor.OFF.array)
    function._color_next = PixelColor.PINK.array
    control._run_functions()
    assert function._delay_counter == 1
    control._run_functions()
    assert function._delay_counter == 0
    assert_array_equal(function._color, PixelColor.PINK.array)
    function._color_next = PixelColor.GREEN.array
    control._run_functions()
    assert function._delay_counter == 1
    control._run_functions()
    assert function._delay_counter == 0
    assert_array_equal(function._color, PixelColor.GREEN.array)
    function._delay_count_max = 0
    function._fade_amount = -1.0
    control._run_functions()
    function._fade_amount = 2567.0
    control._run_functions()


def test_updateArrayIndex_singlestep():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    control.function_list.append(function)
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1
    for i in range(ArrayTransform.Controller.realLEDCount):
        control._run_functions()
        assert function._index == (i + 1) % ArrayTransform.Controller.realLEDCount
        assert function._step == 1
        assert function._direction == 1
        assert_array_equal(
            function._index_range,
            np.array([(i + 1) % ArrayTransform.Controller.realLEDCount]),
        )
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1


def test_updateArrayIndex_largestep():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    control.function_list.append(function)
    function._step = 2
    assert function._index == 0
    assert function._step == 2
    assert function._direction == 1
    for i in range(ArrayTransform.Controller.realLEDCount):
        control._run_functions()
        begin_idx = function._index_previous + 1
        idx = begin_idx + (function._step - 1)
        assert function._index == idx % ArrayTransform.Controller.realLEDCount
        assert function._step == 2
        assert function._direction == 1
        assert_array_equal(
            function._index_range,
            np.array(
                [j % ArrayTransform.Controller.realLEDCount for j in range(begin_idx, idx + 1)],
            ),
        )
    assert function._index == 0
    assert function._step == 2
    assert function._direction == 1


def test_functionCollisionDetection_only_one():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function = ArrayTransform(control, ArrayTransform.functionCollisionDetection, pattern)
    control.function_list.append(function)
    function._step = 1
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1
    for i in range(ArrayTransform.Controller.realLEDCount):
        control._run_functions()
    assert function._index == 0
    assert function._step == 1
    assert function._direction == 1
    assert function._collision is False


def test_functionCollisionDetection_small_step():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function1 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    function2 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    function3 = ArrayTransform(
        control,
        ArrayTransform.functionCollisionDetection,
        pattern,
    )
    control.function_list.append(function1)
    control.function_list.append(function2)
    control.function_list.append(function3)
    function2._index = control.real_led_count - 1
    function2._direction = -1
    assert function1._index == 0
    assert function1._step == 1
    assert function1._direction == 1
    control._run_functions()
    assert function1._index == 1
    assert function1._index_range == [1]
    assert function1._step == 1
    assert function1._direction == 1
    assert function1._collision is False


def test_functionCollisionDetection_large_step():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function1 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    function2 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    function3 = ArrayTransform(
        control,
        ArrayTransform.functionCollisionDetection,
        pattern,
    )
    function3._explode = True
    control.function_list.append(function1)
    control.function_list.append(function2)
    control.function_list.append(function3)
    function1._step = 2
    function1._collision_enabled = True
    function2._step = 2
    function2._collision_enabled = True
    function2._index = control.real_led_count - 1
    function2._direction = -1
    assert function1._index == 0
    assert function1._step == 2
    assert function1._direction == 1
    assert function2._index == 2
    assert function2._step == 2
    assert function2._direction == -1
    control._run_functions()
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
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    function1 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    function2 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
    function3 = ArrayTransform(
        control,
        ArrayTransform.functionCollisionDetection,
        pattern,
    )
    function3._explode = True
    control.function_list.append(function1)
    control.function_list.append(function2)
    control.function_list.append(function3)
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
    control._run_functions()
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
    control._run_functions()
    assert function1._collision is True
    assert function1._collision_with == function2
    assert function1._collision is True
    assert function2._collision_with == function1


def test_functionOff():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
    )
    off = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    control.set_virtual_led_buffer(pattern)
    function1 = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(function1)
    assert_array_equal(control.virtual_led_buffer, pattern)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, off)


def test_functionFadeOff():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    half = pixel_array_to_numpy_array(
        [PixelColor.RED2, PixelColor.GREEN2, PixelColor.BLUE2],
    )
    quarter = pixel_array_to_numpy_array(
        [PixelColor.RED3, PixelColor.GREEN3, PixelColor.BLUE3],
    )
    eighth = pixel_array_to_numpy_array(
        [PixelColor.RED4, PixelColor.GREEN4, PixelColor.BLUE4],
    )
    control.set_virtual_led_buffer(pattern)
    function1 = ArrayTransform(control, ArrayTransform.functionFadeOff, pattern)
    function1._fade_amount = 0.5
    control.function_list.append(function1)
    assert_array_equal(control.virtual_led_buffer, pattern)
    assert function1._fade_amount == 0.5
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, half)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, quarter)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, eighth)


def test_functionSolidColorCycle():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    one = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.RED, PixelColor.RED],
    )
    three = pixel_array_to_numpy_array(
        [PixelColor.GREEN, PixelColor.GREEN, PixelColor.GREEN],
    )
    four = pixel_array_to_numpy_array(
        [PixelColor.BLUE, PixelColor.BLUE, PixelColor.BLUE],
    )
    function1 = ArrayTransform(control, ArrayTransform.functionSolidColorCycle, pattern)
    control.function_list.append(function1)
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, three)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, four)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)


def test_functionFade():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    one = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.RED2, PixelColor.RED2, PixelColor.RED2],
    ) + [1, 0, 0]
    three = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.RED, PixelColor.RED],
    ) + [1, 0, 0]
    three -= [1, 0, 0]
    function1 = ArrayTransform(control, ArrayTransform.functionFade, pattern)
    function1._fade_amount = 0.5
    control.function_list.append(function1)
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, three)
    function1._color = PixelColor.OFF.array
    control.virtual_led_buffer += [1, 0, 0]
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, one)
    function1._delay_count_max = 0
    function1._fade_amount = -1.0
    control._run_functions()
    function1._fade_amount = 2567.0
    control._run_functions()


def test_functionMarquee():
    control = newController()
    pattern = pixel_array_to_numpy_array([PixelColor.RED])
    one = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
    )
    three = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.RED],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionMarquee, pattern)
    control.function_list.append(function)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, three)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)


def test_functionCylon():
    control = newController()
    pattern = pixel_array_to_numpy_array([PixelColor.RED])
    one = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
    )
    three = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.RED],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionCylon, pattern)
    control.function_list.append(function)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, three)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)


def test_functionMerge():
    control = newControllerBigger()
    pattern = pixel_array_to_numpy_array(
        [
            PixelColor.RED,
            PixelColor.OFF,
            PixelColor.OFF,
            PixelColor.OFF,
            PixelColor.OFF,
            PixelColor.RED,
        ],
    )
    one = np.array([0, 1, 2, 3, 4, 5])
    two = np.array([2, 0, 1, 1, 0, 2])
    three = np.array([1, 2, 0, 0, 2, 1])
    four = np.array([0, 1, 2, 2, 1, 0])
    function = ArrayTransform(control, ArrayTransform.functionMerge, pattern)
    function._size = 3
    control.function_list.append(function)
    control.set_virtual_led_buffer(pattern)
    assert_array_equal(control.virtual_led_buffer, pattern)
    assert_array_equal(control.virtual_led_index_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, pattern)
    assert_array_equal(control.virtual_led_index_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, pattern)
    assert_array_equal(control.virtual_led_index_buffer, three)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, pattern)
    assert_array_equal(control.virtual_led_index_buffer, four)


def test_functionAccelerate():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    one = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.RED],
    )
    three = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.RED, PixelColor.RED],
    )
    four = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.RED, PixelColor.RED],
    )
    five = pixel_array_to_numpy_array(
        [PixelColor.GREEN, PixelColor.GREEN, PixelColor.GREEN],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionAccelerate, pattern)
    function._state_max = 5
    control.function_list.append(function)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, three)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, four)
    function._color_cycle = True
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, five)
    control._run_functions()


def test_functionRandomChange():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    off = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    function = ArrayTransform(control, ArrayTransform.functionRandomChange, pattern)
    function._color_next = function._color
    function._fade_amount = 1
    control.function_list.append(function)
    assert_array_equal(control.virtual_led_buffer, off)
    control._run_functions()
    control._run_functions()
    control._run_functions()
    control._run_functions()
    while not np.array_equal(function._color_next, control.background_color):
        control._run_functions()
    control._run_functions()
    function._fade_type = LEDFadeType.INSTANT_OFF
    control._run_functions()


def test_functionMeteors():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    initial = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    one = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.RED],
    )
    three = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.OFF],
    )
    four = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.GREEN, PixelColor.OFF],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionMeteors, pattern)
    function._fade_amount = 1
    control.function_list.append(function)
    assert_array_equal(control.virtual_led_buffer, initial)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, three)
    function._color_cycle = True
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, four)


def test_functionSprites():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    initial = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionSprites, pattern)
    function._fade_amount = 1.0
    control.function_list.append(function)
    assert_array_equal(control.virtual_led_buffer, initial)
    while function.state == SpriteState.OFF.value:
        control._run_functions()
    function._step_counter = 0
    while function.state != SpriteState.OFF.value:
        control._run_functions()


def test_functionRaindrops():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    initial = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    one = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
    )
    two = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.OFF, PixelColor.RED],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionRaindrops, pattern)
    function._fade_amount = 1.0
    control.function_list.append(function)
    assert_array_equal(control.virtual_led_buffer, initial)
    control._run_functions()
    while function._index != 1:
        control._run_functions()
    # assert_array_equal(control.virtualLEDBuffer, one)
    while function.state == RaindropStates.OFF.value:
        control._run_functions()
    function._step_count_max = 2
    function._color = PixelColor.RED.array
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, one)
    control._run_functions()
    assert_array_equal(control.virtual_led_buffer, two)


def test_functionAlive():
    control = newController()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    initial = pixel_array_to_numpy_array(
        [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
    )
    off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
    control.function_list.append(off)
    function = ArrayTransform(control, ArrayTransform.functionAlive, pattern)
    function._fade_amount = 1.0
    control.function_list.append(function)
    assert_array_equal(control.virtual_led_buffer, initial)
    control._run_functions()
    while not function.state & ThingMoves.METEOR.value:
        control._run_functions()
    while not function.state & ThingMoves.LIGHT_SPEED.value:
        control._run_functions()
    while not function.state & ThingMoves.TURTLE.value:
        control._run_functions()
    while not function.state & ThingSizes.GROW.value:
        control._run_functions()
    while not function.state & ThingSizes.SHRINK.value:
        control._run_functions()
    while not function.state & ThingColors.CYCLE.value:
        control._run_functions()
    control._run_functions()
    while not function.state & ThingSizes.GROW.value:
        control._run_functions()
    function._size_max = 5
    function._size = 2
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()
    while not function.state & ThingSizes.GROW.value:
        control._run_functions()
    function._size_max = 5
    function._size = 3
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()
    while not function.state & ThingSizes.GROW.value:
        control._run_functions()
    function._size_max = 5
    function._size = 0
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()
    while not function.state & ThingSizes.GROW.value:
        control._run_functions()
    function._size_max = 5
    function._size = 6
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()
    while not function.state & ThingMoves.LIGHT_SPEED.value:
        control._run_functions()
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()
    while not function.state & ThingSizes.GROW.value:
        control._run_functions()
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()
    while not function.state & ThingSizes.SHRINK.value:
        control._run_functions()
    function._delay_count_max = 0
    function._step_count_max = 114
    control._run_functions()


def test_overlayTwinkle():
    control = newControllerBigger()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(control, ArrayTransform.overlayTwinkle, pattern)
    function._random = 0.0
    control.function_list.append(function)
    control._run_functions()
    control._copy_overlays()
    assert np.sum(np.array(control.ws281xString)) != 0


def test_overlayBlink():
    control = newControllerBigger()
    pattern = pixel_array_to_numpy_array(
        [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
    )
    function = ArrayTransform(control, ArrayTransform.overlayBlink, pattern)
    function._random = 0.0
    control.function_list.append(function)
    control._run_functions()
    control._copy_overlays()
    assert np.sum(np.array(control.ws281xString)) != 0
