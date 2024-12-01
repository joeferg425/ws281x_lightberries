"""Test pixel/array functions."""
# ruff: noqa: S101, D103, SLF001, PGH003, PLR2004

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from unittest import mock

import lightberries.base.rpiws281x_patch
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.solid import SequenceSolid
from lightberries.array_transform.all import TransformAccelerate, TransformNone
from lightberries.array_transform.array_transform import (
    ArrayTransform,
)
from lightberries.base.pixel import LEDOrder, PixelColor
from lightberries.base.ws281x_strings import WS281xString, WS281xStringError
from lightberries.overlay.all import TransformFadeOff
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np
    from numpy.typing import NDArray


def pixel_strip_fakery(  # noqa: PLR0913
    self: WS281xString,
    led_count: int,
    pwm_gpio_pin: int,
    pwm_channel: int,
    pwm_frequency: int,
    dma_channel: int,
    led_gamma: float,
    led_strip_type: Any,  # noqa: ANN401
    led_brightness: Any,  # noqa: ANN401
    matrix_shape: tuple[int, int] | None = None,  # noqa: ARG001, ARG002, RUF100
    matrix_layout: NDArray[np.int32] | None = None,  # noqa: ARG001, ARG002, RUF100
    *,
    pwm_invert_signal: bool = False,
    testing: bool = False,  # noqa: ARG001, ARG002, RUF100
) -> None:
    try:
        # create ws281x pixel strip
        self._ws281x_pixel_strip = lightberries.base.rpiws281x_patch.FakePixelStrip(  # type: ignore
            pin=pwm_gpio_pin,
            dma=dma_channel,
            num=led_count,
            freq_hz=pwm_frequency,
            channel=pwm_channel,
            invert=pwm_invert_signal,
            gamma=led_gamma,
            strip_type=led_strip_type,
            brightness=int(255 * led_brightness),
        )
    except SystemExit:  # pragma: no cover
        raise
    except KeyboardInterrupt:  # pragma: no cover
        raise
    except Exception as ex:  # pragma: no cover
        raise WS281xStringError from ex


def wS281xString_mockery(  # noqa: N802, PLR0913
    self: ArrayController,
    led_count: int = 100,
    pwm_gpio_pin: int = 18,
    dma_channel: int = 10,
    pwm_frequency: int = 800000,
    led_brightness: float = 0.75,
    pwm_channel: int = 0,
    led_strip_type: Any = None,  # noqa: ANN401
    gamma: Any = None,  # noqa: ANN401
    refresh_callback: Callable[[], None] | None = None,  # noqa: ARG001
    led_order: LEDOrder = LEDOrder.GRB,  # noqa: ARG001
    *,
    pwm_invert_signal: bool = False,
    debug: bool = False,  # noqa: ARG001
    verbose: bool = False,  # noqa: ARG001
    simulate: bool = False,
    testing: bool = False,
    log_file: str | Path | None = None,  # noqa: ARG001
) -> None:
    with mock.patch.object(
        WS281xString,
        "_instantiate_pixel_strip",
        new=pixel_strip_fakery,
    ):
        self._ws281x_string = WS281xString(  # type: ignore
            led_count=led_count,
            pwm_gpio_pin=pwm_gpio_pin,
            dma_channel=dma_channel,
            pwm_frequency=pwm_frequency,
            pwm_invert_signal=pwm_invert_signal,
            led_brightness=led_brightness,
            pwm_channel=pwm_channel,
            led_strip_type=led_strip_type,
            led_gamma=gamma,
            simulate=simulate,
            testing=testing,
        )


def new_controller(led_count: int = 3) -> ArrayController:
    ArrayTransform.clear_active()
    with mock.patch.object(
        ArrayController,
        "_instantiate_ws281x_string",
        wS281xString_mockery,
    ):
        return ArrayController(
            led_count=led_count,
            simulate=True,
        )


def new_controller_bigger() -> ArrayController:
    with mock.patch.object(
        ArrayController,
        "_instantiate_WS281xString",
        wS281xString_mockery,
    ):
        return ArrayController(
            led_count=6,
            simulate=True,
        )


def test_pixel_transform_init() -> None:
    f_type = PixelTransform
    name = f_type.__name__
    controller = new_controller()
    function = PixelTransform(
        controller=controller,
    )
    assert function is not None, "function is none"
    assert function.name == name, f"function name != {name} ({function.name})"
    assert isinstance(
        function,
        f_type,
    ), f"function is not an instance of the expected class: {type(function)} != {f_type}"


def test_pixel_transform_init_name() -> None:
    f_type = PixelTransform
    name = "test"
    controller = new_controller()
    function = PixelTransform(
        controller=controller,
        name=name,
    )
    assert function is not None, "function is none"
    assert function.name == name, f"function name != {name} ({function.name})"
    assert isinstance(
        function,
        f_type,
    ), f"function is not an instance of the expected class: {type(function)} != {f_type}"


def test_pixel_transform_str() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    assert str(function) == '[0]: "PixelTransform" PX#000000:GRB'


def test_pixel_transform_repr() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    assert repr(function) == '<PixelTransform> [0]: "PixelTransform" PX#000000:GRB'


def test_pixel_transform_create() -> None:
    f_type = PixelTransform
    controller = new_controller()
    function_list = PixelTransform.create(controller=controller)
    assert function_list is not None, "function is none"
    assert all(
        isinstance(
            f,
            list,
        )
        for f in function_list
    ), f"not all functions are not an instance of the expected class: {f_type}"
    assert len(function_list) == 0


def test_pixel_transform_copy() -> None:
    controller = new_controller()
    function1 = PixelTransform(controller=controller)
    function2 = function1.copy()
    assert function1.name == function2.name
    assert function1 != function2


def test_pixel_transform_eq() -> None:
    controller = new_controller()
    function1 = PixelTransform(controller=controller)
    function2 = function1.copy()
    assert function1.name == function2.name
    assert function1 == function1  # noqa: PLR0124
    assert function1 != function2
    assert function2 != "tacocat"


def test_pixel_transform_random_direction() -> None:
    directions = [PixelTransform.get_random_direction() for _ in range(20)]
    assert not all(d == directions[0] for d in directions)


def test_pixel_transform_random_bool() -> None:
    bools = [PixelTransform.get_random_boolean() for _ in range(20)]
    assert not all(b == bools[0] for b in bools)


def test_pixel_transform_state() -> None:
    controller = new_controller()
    function1 = PixelTransform(controller=controller)
    assert function1.state is not None
    assert function1.state.pixel_sequence == PixelSequence.get_monthly_color_sequence()


def test_pixel_transform_random_index() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    idxs = [function.get_random_index() for _ in range(20)]
    assert not all(i == idxs[0] for i in idxs)


def test_pixel_transform_random_indices() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    idxs = function.get_random_indices(20)
    assert not all(i == idxs[0] for i in idxs)


def test_pixel_transform_update_array_index() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    assert function.state.step_size == 1
    assert function.state.index == 0
    assert function.state.index_previous == 2
    assert function.state.index_next == 1
    function.update_array_index()
    assert function.state.index == 1
    assert function.state.index_previous == 0
    assert function.state.index_next == 2


def test_pixel_transform_calc_range() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    assert function.state.step_size == 1
    rng = function.calc_range()
    assert len(rng) == 1
    assert rng[0] == 1
    function.update_array_index()
    rng = function.calc_range()
    assert len(rng) == 1
    assert rng[0] == 2
    function.update_array_index()
    rng = function.calc_range()
    assert len(rng) == 1
    assert rng[0] == 0
    function.update_array_index()
    rng = function.calc_range()
    assert len(rng) == 1
    assert rng[0] == 1


def test_pixel_transform_calc_range_2() -> None:
    controller = new_controller()
    function = PixelTransform(controller=controller)
    function.state.step_size = 2
    assert function.state.step_size == 2
    rng = function.calc_range()
    assert len(rng) == 2
    assert rng[0] == 1
    assert rng[1] == 2
    function.update_array_index()
    rng = function.calc_range()
    assert len(rng) == 2
    assert rng[0] == 0
    assert rng[1] == 1


def test_pixel_transform_calc_range_3() -> None:
    controller = new_controller(led_count=4)
    function = PixelTransform(controller=controller)
    function.state.step_size = 3
    function.state.direction = -1
    assert function.state.step_size == 3
    rng = function.calc_range()
    assert len(rng) == 3
    assert rng[0] == 3
    assert rng[1] == 2
    assert rng[2] == 1
    function.update_array_index()
    rng = function.calc_range()
    assert len(rng) == 3
    assert rng[0] == 0
    assert rng[1] == 3
    assert rng[2] == 2
    function.update_array_index()
    rng = function.calc_range()
    assert len(rng) == 3
    assert rng[0] == 1
    assert rng[1] == 0
    assert rng[2] == 3


def test_pixel_transform_clear_active() -> None:
    controller = new_controller(led_count=4)
    TransformNone.create(controller=controller)
    assert len(ArrayTransform.ACTIVE_TRANSFORMS) == 1
    ArrayTransform.clear_active()
    assert len(ArrayTransform.ACTIVE_TRANSFORMS) == 0


def test_pixel_transform_advance_delay_counter() -> None:
    controller = new_controller(led_count=4)
    transform = TransformNone(controller=controller)
    transform.state.delay_count_max = 2
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 0
    assert transform.state.delay_count_reset is False
    transform.advance_delay_counter()
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 1
    assert transform.state.delay_count_reset is False
    transform.advance_delay_counter()
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 0
    assert transform.state.delay_count_reset is True


def test_pixel_transform_advance_step_counter() -> None:
    controller = new_controller(led_count=4)
    transform = TransformNone(controller=controller)
    transform.state.step_count_max = 2
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 0
    assert transform.state.step_count_reset is False
    transform.advance_step_counter()
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 1
    assert transform.state.step_count_reset is False
    transform.advance_step_counter()
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 0
    assert transform.state.step_count_reset is True


def test_pixel_transform_transform() -> None:
    controller = new_controller(led_count=4)
    transform = TransformNone(controller=controller)
    transform.state.delay_count_max = 2
    transform.state.step_count_max = 2
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 0
    assert transform.state.delay_count_reset is False
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 0
    assert transform.state.step_count_reset is False
    transform.transform()
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 1
    assert transform.state.delay_count_reset is False
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 0
    assert transform.state.step_count_reset is False
    transform.transform()
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 0
    assert transform.state.delay_count_reset is True
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 1
    assert transform.state.step_count_reset is False
    transform.transform()
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 1
    assert transform.state.delay_count_reset is False
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 1
    assert transform.state.step_count_reset is False
    transform.transform()
    assert transform.state.delay_count_max == 2
    assert transform.state.delay_count_max_setting == 0
    assert transform.state.delay_counter == 0
    assert transform.state.delay_count_reset is True
    assert transform.state.step_count_max == 2
    assert transform.state.step_size_max_setting == 1
    assert transform.state.step_counter == 0
    assert transform.state.step_count_reset is True


def test_array_transform_init() -> None:
    name = "ArrayTransform"
    controller = new_controller()
    function = ArrayTransform(controller=controller)
    assert function is not None
    assert function.name == name
    assert isinstance(function, ArrayTransform)


def test_array_transform_create() -> None:
    controller = new_controller()
    function_list = ArrayTransform.create(controller=controller)
    assert function_list is not None
    assert isinstance(function_list, list)
    assert len(function_list) == 0


def test_accelerate_init() -> None:
    controller = new_controller()
    function = TransformAccelerate(controller=controller)
    assert function is not None
    assert isinstance(function, TransformAccelerate)


def test_accelerate_create() -> None:
    controller = new_controller()
    function_list = TransformAccelerate.create(controller=controller)
    assert function_list is not None
    assert isinstance(function_list, list)
    assert len(function_list) > 0
    assert all(isinstance(f, (TransformAccelerate, TransformFadeOff)) for f in function_list)


def test_accelerate_create_state_is_not_none() -> None:
    controller = new_controller()
    setting = 10000
    accelerate = TransformAccelerate(controller=controller)
    accelerate.state.delay_count_max_setting = setting
    function_list = TransformAccelerate.create(
        controller=controller,
        state=accelerate.state,
    )
    assert function_list is not None
    assert isinstance(function_list, list)
    assert len(function_list) > 0
    assert all(isinstance(f, (TransformAccelerate, TransformFadeOff)) for f in function_list)
    assert function_list[0].state.delay_count_max_setting == setting


def test_accelerate_create_state_is_none() -> None:
    controller = new_controller()
    accelerate = TransformAccelerate(controller=controller)
    function_list = TransformAccelerate.create(
        controller=controller,
        state=accelerate.state,
    )
    assert function_list is not None
    assert isinstance(function_list, list)
    assert len(function_list) > 0
    assert all(isinstance(f, (TransformAccelerate, TransformFadeOff)) for f in function_list)


def test_accelerate_create_with_pixel_sequence() -> None:
    controller = new_controller()
    pixel_sequence = SequenceSolid(led_count=12, color=PixelColor.CYAN)
    function_list = TransformAccelerate.create(
        controller=controller,
        pixel_sequence=pixel_sequence,
    )
    assert function_list is not None
    assert isinstance(function_list, list)
    assert len(function_list) > 0
    for f in function_list:
        assert f.state.pixel_sequence == pixel_sequence


def test_accelerate_create_with_values() -> None:
    delay_count_max = 12345
    step_count_max = 123456
    color_cycle = False
    fade_amount = 2
    controller = new_controller()
    pixel_sequence = SequenceSolid(led_count=12, color=PixelColor.CYAN)
    function_list = TransformAccelerate.create(
        controller=controller,
        pixel_sequence=pixel_sequence,
        delay_count_max=delay_count_max,
        step_count_max=step_count_max,
        color_cycle=color_cycle,
        fade_amount=fade_amount,
    )
    assert function_list is not None
    assert isinstance(function_list, list)
    assert len(function_list) > 0
    for f in function_list:
        assert f.state.pixel_sequence == pixel_sequence
        assert f.state.delay_count_max == delay_count_max
        assert f.state.step_count_max == step_count_max
        assert f.state.color_cycle == color_cycle
        assert f.state.fade_amount == fade_amount


# def test_repr():
#     control = new_controller()
#     pattern = PixelSequence.pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     function = ArrayTransform(control, assert_func, pattern)
#     control.function_list.append(function)
#     assert repr(function) == '<ArrayFunction> [0]: "assert_func" PX #FF0000'


# def test_run():
#     control = newController()
#     function = ArrayTransform(control, assert_func)
#     control.function_list.append(function)
#     control._run_functions()
#     function._transform()


# def test_colorSequenceCount():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     function = ArrayTransform(newController(), assert_func, pattern)
#     control.function_list.append(function)
#     assert function.color_sequence_count == len(pattern)


# def test_colorSequenceIndex():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     function = ArrayTransform(control, assert_func, pattern)
#     control.function_list.append(function)
#     assert function.color_sequence_index == 0


# def test_colorSequenceNext():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     function = ArrayTransform(control, assert_func, pattern)
#     control.function_list.append(function)
#     left = function._color
#     right = PixelColor.RED.array
#     assert_array_equal(left, right)
#     left = function.color_sequence_next
#     right = PixelColor.GREEN.array
#     assert_array_equal(left, right)
#     left = function.color_sequence_next
#     right = PixelColor.BLUE.array
#     assert_array_equal(left, right)
#     left = function.color_sequence_next
#     right = PixelColor.RED.array
#     assert_array_equal(left, right)


# # def test_colorSequenceNext_rollover():
# #     control = newController()
# #     pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
# #     function = ArrayFunction(control, assert_func, pattern)
# #     control.functionList.append(function)
# #     function.colorSequenceNext
# #     function.colorSequenceNext
# #     function.colorSequenceNext
# #     left = function.colorSequenceNext
# #     right = PixelColors.RED.array
# #     assert_array_equal(left, right)


# def test_doFade():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function = ArrayTransform(control, ArrayTransform.do_fade, pattern)
#     control.function_list.append(function)
#     delay_count = 2
#     function._delay_count_max = delay_count
#     function._fade_amount = 1.0
#     assert_array_equal(function._color, PixelColor.RED.array)
#     assert function._delay_counter == 0
#     control._run_functions()
#     assert function._delay_counter == 1
#     control._run_functions()
#     assert function._delay_counter == 0
#     assert_array_equal(function._color, PixelColor.OFF.array)
#     function._color_next = PixelColor.PINK.array
#     control._run_functions()
#     assert function._delay_counter == 1
#     control._run_functions()
#     assert function._delay_counter == 0
#     assert_array_equal(function._color, PixelColor.PINK.array)
#     function._color_next = PixelColor.GREEN.array
#     control._run_functions()
#     assert function._delay_counter == 1
#     control._run_functions()
#     assert function._delay_counter == 0
#     assert_array_equal(function._color, PixelColor.GREEN.array)
#     function._delay_count_max = 0
#     function._fade_amount = -1.0
#     control._run_functions()
#     function._fade_amount = 2567.0
#     control._run_functions()


# def test_updateArrayIndex_singlestep():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     control.function_list.append(function)
#     assert function._index == 0
#     assert function._step == 1
#     assert function._direction == 1
#     for i in range(ArrayTransform.Controller.realLEDCount):
#         control._run_functions()
#         assert function._index == (i + 1) % ArrayTransform.Controller.realLEDCount
#         assert function._step == 1
#         assert function._direction == 1
#         assert_array_equal(
#             function._index_range,
#             np.array([(i + 1) % ArrayTransform.Controller.realLEDCount]),
#         )
#     assert function._index == 0
#     assert function._step == 1
#     assert function._direction == 1


# def test_updateArrayIndex_largestep():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     control.function_list.append(function)
#     function._step = 2
#     assert function._index == 0
#     assert function._step == 2
#     assert function._direction == 1
#     for i in range(ArrayTransform.Controller.realLEDCount):
#         control._run_functions()
#         begin_idx = function._index_previous + 1
#         idx = begin_idx + (function._step - 1)
#         assert function._index == idx % ArrayTransform.Controller.realLEDCount
#         assert function._step == 2
#         assert function._direction == 1
#         assert_array_equal(
#             function._index_range,
#             np.array(
#                 [j % ArrayTransform.Controller.realLEDCount for j in range(begin_idx, idx + 1)],
#             ),
#         )
#     assert function._index == 0
#     assert function._step == 2
#     assert function._direction == 1


# def test_functionCollisionDetection_only_one():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function = ArrayTransform(control, ArrayTransform.functionCollisionDetection, pattern)
#     control.function_list.append(function)
#     function._step = 1
#     assert function._index == 0
#     assert function._step == 1
#     assert function._direction == 1
#     for i in range(ArrayTransform.Controller.realLEDCount):
#         control._run_functions()
#     assert function._index == 0
#     assert function._step == 1
#     assert function._direction == 1
#     assert function._collision is False


# def test_functionCollisionDetection_small_step():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function1 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     function2 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     function3 = ArrayTransform(
#         control,
#         ArrayTransform.functionCollisionDetection,
#         pattern,
#     )
#     control.function_list.append(function1)
#     control.function_list.append(function2)
#     control.function_list.append(function3)
#     function2._index = control.real_led_count - 1
#     function2._direction = -1
#     assert function1._index == 0
#     assert function1._step == 1
#     assert function1._direction == 1
#     control._run_functions()
#     assert function1._index == 1
#     assert function1._index_range == [1]
#     assert function1._step == 1
#     assert function1._direction == 1
#     assert function1._collision is False


# def test_functionCollisionDetection_large_step():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function1 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     function2 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     function3 = ArrayTransform(
#         control,
#         ArrayTransform.functionCollisionDetection,
#         pattern,
#     )
#     function3._explode = True
#     control.function_list.append(function1)
#     control.function_list.append(function2)
#     control.function_list.append(function3)
#     function1._step = 2
#     function1._collision_enabled = True
#     function2._step = 2
#     function2._collision_enabled = True
#     function2._index = control.real_led_count - 1
#     function2._direction = -1
#     assert function1._index == 0
#     assert function1._step == 2
#     assert function1._direction == 1
#     assert function2._index == 2
#     assert function2._step == 2
#     assert function2._direction == -1
#     control._run_functions()
#     assert function1._index == 0
#     assert 1 in function1._index_range and 2 in function1._index_range
#     assert 1 in function1._collision_intersection
#     assert function1._step == 2
#     assert function1._direction == -1
#     assert function1._collision is True
#     assert function1._collision_with == function2
#     assert function2._index == 2
#     assert 1 in function2._index_range and 0 in function2._index_range
#     assert 1 in function2._collision_intersection
#     assert function2._step == 2
#     assert function2._direction == 1
#     assert function1._collision is True
#     assert function2._collision_with == function1


# def test_functionCollisionDetection_slow_fast():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     function1 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     function2 = ArrayTransform(control, ArrayTransform.update_array_index, pattern)
#     function3 = ArrayTransform(
#         control,
#         ArrayTransform.functionCollisionDetection,
#         pattern,
#     )
#     function3._explode = True
#     control.function_list.append(function1)
#     control.function_list.append(function2)
#     control.function_list.append(function3)
#     function1._step = 3
#     function1._collision_enabled = True
#     function2._collision_enabled = True
#     function2._index = 1
#     assert function1._index == 0
#     assert function1._step == 3
#     assert function1._direction == 1
#     assert function2._index == 1
#     assert function2._step == 1
#     assert function2._direction == 1
#     control._run_functions()
#     assert function1._index == 2
#     assert 2 in function1._index_range
#     assert 2 in function1._collision_intersection
#     assert function1._step == 1
#     assert function1._direction == 1
#     assert function1._collision is True
#     assert function1._collision_with == function2
#     assert function2._index == 1
#     assert 2 in function2._index_range
#     assert 2 in function2._collision_intersection
#     assert function2._step == 3
#     assert function2._direction == 1
#     assert function1._collision is True
#     assert function2._collision_with == function1
#     control._run_functions()
#     assert function1._collision is True
#     assert function1._collision_with == function2
#     assert function1._collision is True
#     assert function2._collision_with == function1


# def test_functionOff():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.PINK],
#     )
#     off = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     control.set_virtual_led_buffer(pattern)
#     function1 = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(function1)
#     assert_array_equal(control.virtual_led_buffer, pattern)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, off)


# def test_functionFadeOff():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     half = pixel_array_to_numpy_array(
#         [PixelColor.RED2, PixelColor.GREEN2, PixelColor.BLUE2],
#     )
#     quarter = pixel_array_to_numpy_array(
#         [PixelColor.RED3, PixelColor.GREEN3, PixelColor.BLUE3],
#     )
#     eighth = pixel_array_to_numpy_array(
#         [PixelColor.RED4, PixelColor.GREEN4, PixelColor.BLUE4],
#     )
#     control.set_virtual_led_buffer(pattern)
#     function1 = ArrayTransform(control, ArrayTransform.functionFadeOff, pattern)
#     function1._fade_amount = 0.5
#     control.function_list.append(function1)
#     assert_array_equal(control.virtual_led_buffer, pattern)
#     assert function1._fade_amount == 0.5
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, half)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, quarter)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, eighth)


# def test_functionSolidColorCycle():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     one = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.RED, PixelColor.RED],
#     )
#     three = pixel_array_to_numpy_array(
#         [PixelColor.GREEN, PixelColor.GREEN, PixelColor.GREEN],
#     )
#     four = pixel_array_to_numpy_array(
#         [PixelColor.BLUE, PixelColor.BLUE, PixelColor.BLUE],
#     )
#     function1 = ArrayTransform(control, ArrayTransform.functionSolidColorCycle, pattern)
#     control.function_list.append(function1)
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, three)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, four)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)


# def test_functionFade():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     one = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.RED2, PixelColor.RED2, PixelColor.RED2],
#     ) + [1, 0, 0]
#     three = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.RED, PixelColor.RED],
#     ) + [1, 0, 0]
#     three -= [1, 0, 0]
#     function1 = ArrayTransform(control, ArrayTransform.functionFade, pattern)
#     function1._fade_amount = 0.5
#     control.function_list.append(function1)
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, three)
#     function1._color = PixelColor.OFF.array
#     control.virtual_led_buffer += [1, 0, 0]
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, one)
#     function1._delay_count_max = 0
#     function1._fade_amount = -1.0
#     control._run_functions()
#     function1._fade_amount = 2567.0
#     control._run_functions()


# def test_functionMarquee():
#     control = newController()
#     pattern = pixel_array_to_numpy_array([PixelColor.RED])
#     one = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
#     )
#     three = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.RED],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionMarquee, pattern)
#     control.function_list.append(function)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, three)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)


# def test_functionCylon():
#     control = newController()
#     pattern = pixel_array_to_numpy_array([PixelColor.RED])
#     one = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
#     )
#     three = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.RED],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionCylon, pattern)
#     control.function_list.append(function)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, three)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)


# def test_functionMerge():
#     control = newControllerBigger()
#     pattern = pixel_array_to_numpy_array(
#         [
#             PixelColor.RED,
#             PixelColor.OFF,
#             PixelColor.OFF,
#             PixelColor.OFF,
#             PixelColor.OFF,
#             PixelColor.RED,
#         ],
#     )
#     one = np.array([0, 1, 2, 3, 4, 5])
#     two = np.array([2, 0, 1, 1, 0, 2])
#     three = np.array([1, 2, 0, 0, 2, 1])
#     four = np.array([0, 1, 2, 2, 1, 0])
#     function = ArrayTransform(control, ArrayTransform.functionMerge, pattern)
#     function._size = 3
#     control.function_list.append(function)
#     control.set_virtual_led_buffer(pattern)
#     assert_array_equal(control.virtual_led_buffer, pattern)
#     assert_array_equal(control.virtual_led_index_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, pattern)
#     assert_array_equal(control.virtual_led_index_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, pattern)
#     assert_array_equal(control.virtual_led_index_buffer, three)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, pattern)
#     assert_array_equal(control.virtual_led_index_buffer, four)


# def test_functionAccelerate():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     one = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.RED],
#     )
#     three = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.RED, PixelColor.RED],
#     )
#     four = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.RED, PixelColor.RED],
#     )
#     five = pixel_array_to_numpy_array(
#         [PixelColor.GREEN, PixelColor.GREEN, PixelColor.GREEN],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionAccelerate, pattern)
#     function._state_max = 5
#     control.function_list.append(function)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, three)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, four)
#     function._color_cycle = True
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, five)
#     control._run_functions()


# def test_functionRandomChange():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     off = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     function = ArrayTransform(control, ArrayTransform.functionRandomChange, pattern)
#     function._color_next = function._color
#     function._fade_amount = 1
#     control.function_list.append(function)
#     assert_array_equal(control.virtual_led_buffer, off)
#     control._run_functions()
#     control._run_functions()
#     control._run_functions()
#     control._run_functions()
#     while not np.array_equal(function._color_next, control.background_color):
#         control._run_functions()
#     control._run_functions()
#     function._fade_type = LEDFadeType.INSTANT_OFF
#     control._run_functions()


# def test_functionMeteors():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     initial = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     one = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.RED],
#     )
#     three = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.OFF],
#     )
#     four = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.GREEN, PixelColor.OFF],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionMeteors, pattern)
#     function._fade_amount = 1
#     control.function_list.append(function)
#     assert_array_equal(control.virtual_led_buffer, initial)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, three)
#     function._color_cycle = True
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, four)


# def test_functionSprites():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     initial = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionSprites, pattern)
#     function._fade_amount = 1.0
#     control.function_list.append(function)
#     assert_array_equal(control.virtual_led_buffer, initial)
#     while function.state == SpriteState.OFF.value:
#         control._run_functions()
#     function._step_counter = 0
#     while function.state != SpriteState.OFF.value:
#         control._run_functions()


# def test_functionRaindrops():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     initial = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     one = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.RED, PixelColor.OFF],
#     )
#     two = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.OFF, PixelColor.RED],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionRaindrops, pattern)
#     function._fade_amount = 1.0
#     control.function_list.append(function)
#     assert_array_equal(control.virtual_led_buffer, initial)
#     control._run_functions()
#     while function._index != 1:
#         control._run_functions()
#     # assert_array_equal(control.virtualLEDBuffer, one)
#     while function.state == RaindropStates.OFF.value:
#         control._run_functions()
#     function._step_count_max = 2
#     function._color = PixelColor.RED.array
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, one)
#     control._run_functions()
#     assert_array_equal(control.virtual_led_buffer, two)


# def test_functionAlive():
#     control = newController()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     initial = pixel_array_to_numpy_array(
#         [PixelColor.OFF, PixelColor.OFF, PixelColor.OFF],
#     )
#     off = ArrayTransform(control, ArrayTransform.functionOff, pattern)
#     control.function_list.append(off)
#     function = ArrayTransform(control, ArrayTransform.functionAlive, pattern)
#     function._fade_amount = 1.0
#     control.function_list.append(function)
#     assert_array_equal(control.virtual_led_buffer, initial)
#     control._run_functions()
#     while not function.state & ThingMoves.METEOR.value:
#         control._run_functions()
#     while not function.state & ThingMoves.LIGHT_SPEED.value:
#         control._run_functions()
#     while not function.state & ThingMoves.TURTLE.value:
#         control._run_functions()
#     while not function.state & ThingSizes.GROW.value:
#         control._run_functions()
#     while not function.state & ThingSizes.SHRINK.value:
#         control._run_functions()
#     while not function.state & ThingColors.CYCLE.value:
#         control._run_functions()
#     control._run_functions()
#     while not function.state & ThingSizes.GROW.value:
#         control._run_functions()
#     function._size_max = 5
#     function._size = 2
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()
#     while not function.state & ThingSizes.GROW.value:
#         control._run_functions()
#     function._size_max = 5
#     function._size = 3
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()
#     while not function.state & ThingSizes.GROW.value:
#         control._run_functions()
#     function._size_max = 5
#     function._size = 0
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()
#     while not function.state & ThingSizes.GROW.value:
#         control._run_functions()
#     function._size_max = 5
#     function._size = 6
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()
#     while not function.state & ThingMoves.LIGHT_SPEED.value:
#         control._run_functions()
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()
#     while not function.state & ThingSizes.GROW.value:
#         control._run_functions()
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()
#     while not function.state & ThingSizes.SHRINK.value:
#         control._run_functions()
#     function._delay_count_max = 0
#     function._step_count_max = 114
#     control._run_functions()


# def test_overlayTwinkle():
#     control = newControllerBigger()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     function = ArrayTransform(control, ArrayTransform.overlayTwinkle, pattern)
#     function._random = 0.0
#     control.function_list.append(function)
#     control._run_functions()
#     control._copy_overlays()
#     assert np.sum(np.array(control.ws281xString)) != 0


# def test_overlayBlink():
#     control = newControllerBigger()
#     pattern = pixel_array_to_numpy_array(
#         [PixelColor.RED, PixelColor.GREEN, PixelColor.BLUE],
#     )
#     function = ArrayTransform(control, ArrayTransform.overlayBlink, pattern)
#     function._random = 0.0
#     control.function_list.append(function)
#     control._run_functions()
#     control._copy_overlays()
#     assert np.sum(np.array(control.ws281xString)) != 0
#     assert np.sum(np.array(control.ws281xString)) != 0
