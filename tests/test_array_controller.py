from __future__ import annotations

from typing import Any
from unittest import mock

import lightberries.rpiws281x_patch
import numpy as np
from lightberries.array_controller import ArrayController
from lightberries.exceptions import WS281xStringError
from lightberries.light_sequences.base import pixel_array_to_numpy_array
from lightberries.pixel import PixelColors
from lightberries.ws281x_strings import WS281xString
from numpy.typing import NDArray


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
            matrixLayout=matrixLayout,
            matrixShape=matrixShape,
            testing=testing,
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
    testing: bool = False,
    matrixShape: tuple[int, int] = None,
    matrixLayout: NDArray[np.int32] | None = None,
) -> None:
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
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
            matrix_layout=matrixLayout,
            matrix_shape=matrixShape,
        )


def newController() -> ArrayController:
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        return ArrayController(testing=True)


def test_create():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert ac is not None
        assert isinstance(ac.ws281xString, WS281xString)


def test_properties():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert isinstance(ac.refresh_delay, float)
        ac.refresh_delay = 0.1
        assert isinstance(ac.background_color, np.ndarray)
        ac.background_color = PixelColors.OFF.array
        assert isinstance(ac.seconds_per_mode, float)
        ac.seconds_per_mode = 1.0
        assert isinstance(ac.color_sequence, np.ndarray)
        ac.color_sequence = pixel_array_to_numpy_array([PixelColors.OFF])
        assert isinstance(ac.color_sequence_count, int)
        ac.color_sequence_count = 1
        assert isinstance(ac.color_sequence_index, int)
        ac.color_sequence_index = 1
        assert isinstance(ac.color_sequence_next, np.ndarray)
        assert isinstance(ac.get_function_methods_list(), list)
        for f in ac.get_function_methods_list():
            assert isinstance(f, str)
        assert isinstance(ac.get_color_methods_list(), list)
        for f in ac.get_color_methods_list():
            assert isinstance(f, str)


def test_delete():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert isinstance(ac.ws281xString, WS281xString)
        ac.__del__()
        assert ac.ws281xString is None


def test_reset():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        ac.set_virtual_led_buffer(pixel_array_to_numpy_array([PixelColors.OFF]))
        ac.reset()
        assert len(ac.virtual_led_buffer) == ac.real_led_count


def test_refresh_callback():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        ac.refreshCallback = print
        ac.refresh_leds()


def test_getRandomIndices():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        for i in range(3):
            temp = ac.get_random_indices(i)
            assert len(temp) == i
            for x in temp:
                assert isinstance(x, np.int32)


def test_getRandomBoolean():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert isinstance(ac.get_random_boolean(), bool)
