"""Test Light strings."""
from __future__ import annotations
from lightberries.ws281x_strings import WS281xString
from lightberries.pixel import PixelColors
from numpy.testing import assert_array_equal
from lightberries.array_patterns import ConvertPixelArrayToNumpyArray
import pytest
from lightberries.exceptions import WS281xStringException
import numpy as np
import lightberries.rpiws281x
import lightberries.rpiws281x_patch
import mock
from numpy.typing import NDArray
from typing import Any


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
        raise WS281xStringException from ex


def test_creation():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        s = WS281xString(ledCount=led_count, simulate=True)
        assert s is not None
        assert len(s) == led_count


def test_deletion():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        s = WS281xString(ledCount=led_count, simulate=True)
        s.__del__()
        assert True


def test_creation_led_count_none():
    """Test creation of light string with simple args."""
    led_count = None
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        with pytest.raises(WS281xStringException):
            WS281xString(ledCount=led_count, simulate=True)


def test_creation_led_count_invalid():
    """Test creation of light string with simple args."""
    led_count = "invalid"
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        with pytest.raises(WS281xStringException):
            WS281xString(ledCount=led_count, simulate=True)


def test_single_assignment():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)
        for i in range(len(ws281x)):
            random_color = PixelColors.random().array
            ws281x[i] = random_color
            assigned_color = ws281x[i]
            assert_array_equal(assigned_color, random_color)


def test_single_assignment_indexerror():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)
        with pytest.raises(IndexError):
            random_color = PixelColors.random().array
            ws281x[led_count + 1] = random_color


def test_single_assignment_indexerror_numpy():
    """Test creation of light string with simple args."""
    led_count = 10
    led_count_np = np.array(np.arange(11), dtype=np.int32)[-1]
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)
        with pytest.raises(IndexError):
            random_color = PixelColors.random().array
            ws281x[led_count_np] = random_color


def test_single_access_indexerror():
    """Test creation of light string with simple args."""
    led_count = 11
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)
        with pytest.raises(IndexError):
            ws281x[led_count + 1]


def test_single_access_indexerror_numpy():
    """Test creation of light string with simple args."""
    led_count = 11
    led_count_np = np.array(np.arange(12), dtype=np.int32)[-1]
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)
        with pytest.raises(IndexError):
            ws281x[led_count_np]


def test_single_assignment_numpy_int():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)
        for i in np.arange(len(ws281x)):
            random_color = PixelColors.random().array
            ws281x[i] = random_color
            assigned_color = ws281x[i]
            assert_array_equal(assigned_color, random_color)


def test_multiple_assignment():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)

        # one
        assign_count = 1
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[0] = random_colors[0]
        assigned_colors = ws281x[0]
        assert_array_equal(assigned_colors, random_colors[0])

        # stop only
        assign_count = 2
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[:assign_count] = random_colors
        assigned_colors = ws281x[:assign_count]
        assert_array_equal(assigned_colors, random_colors)

        # start only
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[-assign_count:] = random_colors
        assigned_colors = ws281x[-assign_count:]
        assert_array_equal(assigned_colors, random_colors)

        # step only
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[:: int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert_array_equal(assigned_colors, random_colors)

        # all
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[0 : led_count : int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert_array_equal(assigned_colors, random_colors)

        # nones
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(led_count)])
        ws281x[:] = random_colors
        assigned_colors = ws281x[:]
        assert_array_equal(assigned_colors, random_colors)


def test_multiple_assignment_simulated():
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        ws281x = WS281xString(ledCount=led_count, simulate=True)

        # one
        assign_count = 1
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[0] = random_colors[0]
        assigned_colors = ws281x[0]
        assert_array_equal(assigned_colors, random_colors[0])

        # stop only
        assign_count = 2
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[:assign_count] = random_colors
        assigned_colors = ws281x[:assign_count]
        assert_array_equal(assigned_colors, random_colors)

        # start only
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[-assign_count:] = random_colors
        assigned_colors = ws281x[-assign_count:]
        assert_array_equal(assigned_colors, random_colors)

        # step only
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[:: int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert_array_equal(assigned_colors, random_colors)

        # all
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(assign_count)])
        ws281x[0 : led_count : int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert_array_equal(assigned_colors, random_colors)

        # nones
        random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(led_count)])
        ws281x[:] = random_colors
        assigned_colors = ws281x[:]
        assert_array_equal(assigned_colors, random_colors)


def test_context_manager():
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        with WS281xString(ledCount=led_count, simulate=True) as ws281x:
            # all
            random_colors = ConvertPixelArrayToNumpyArray([PixelColors.random() for i in range(led_count)])
            ws281x[:] = random_colors
            assigned_colors = ws281x[:]
            assert_array_equal(assigned_colors, random_colors)
