"""Test Light strings."""

# ruff: noqa: S101

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest import mock

import numpy as np
import pytest
from numpy.testing import assert_array_equal

import lightberries.base.rpiws281x
import lightberries.base.rpiws281x_patch
from lightberries.base.exceptions import WS281xStringError
from lightberries.base.pixel import Pixel, PixelColor
from lightberries.base.ws281x_strings import WS281xString
from lightberries.pixel_sequence import PixelSequence

if TYPE_CHECKING:
    from numpy.typing import NDArray


def mock_instantiate_pixel_strip(  # noqa: PLR0913
    self: WS281xString,
    led_count: int,
    pwm_gpio_pin: int,
    pwm_channel: int,
    pwm_frequency: int,
    dma_channel: int,
    led_gamma: float,
    led_strip_type: Any,  # noqa: ANN401
    led_brightness: Any,  # noqa: ANN401
    matrix_shape: tuple[int, int] | None = None,
    matrix_layout: NDArray[np.int32] | None = None,
    *,
    pwm_invert_signal: bool = False,
    testing: bool = False,
) -> None:
    """Replace the instantiation function with a mockery I tell you."""
    try:
        # create ws281x pixel strip
        self._ws281x_pixel_strip = lightberries.base.rpiws281x_patch.FakePixelStrip(  # type: ignore  # noqa: PGH003
            pin=pwm_gpio_pin,
            dma=dma_channel,
            num=led_count,
            freq_hz=pwm_frequency,
            channel=pwm_channel,
            invert=pwm_invert_signal,
            gamma=led_gamma,
            strip_type=led_strip_type,
            brightness=int(255 * led_brightness),
            matrixLayout=matrix_layout,
            matrixShape=matrix_shape,
            testing=testing,
        )
    except SystemExit:  # pragma: no cover
        raise
    except KeyboardInterrupt:  # pragma: no cover
        raise
    except Exception as ex:  # pragma: no cover
        raise WS281xStringError from ex


def test_creation() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        s = WS281xString(led_count=led_count, simulate=True)
        assert s is not None
        assert len(s) == led_count


def test_deletion() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        s = WS281xString(led_count=led_count, simulate=True)
        s.__del__()
        assert True


def test_creation_led_count_none() -> None:
    """Test creation of light string with simple args."""
    led_count = None
    with (
        mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip),
        pytest.raises(WS281xStringError),
    ):
        WS281xString(led_count=led_count, simulate=True)  # type: ignore  # noqa: PGH003


def test_creation_led_count_invalid() -> None:
    """Test creation of light string with simple args."""
    led_count = "invalid"
    with (
        mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip),
        pytest.raises(WS281xStringError),
    ):
        WS281xString(led_count=led_count, simulate=True)  # type: ignore  # noqa: PGH003


def test_single_assignment() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)
        for i in range(len(ws281x)):
            random_color = Pixel(PixelColor.random()).array
            ws281x[i] = random_color
            assigned_color = ws281x[i]
            assert assigned_color is not None
            assert_array_equal(assigned_color, random_color)


def test_single_assignment_indexerror() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)
        random_color = Pixel(PixelColor.random()).array
        with pytest.raises(IndexError):
            ws281x[led_count + 1] = random_color


def test_single_assignment_indexerror_numpy() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    led_count_np = np.array(np.arange(11), dtype=np.int32)[-1]
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)
        random_color = Pixel(PixelColor.random()).array
        with pytest.raises(IndexError):
            ws281x[led_count_np] = random_color


def test_single_access_indexerror() -> None:
    """Test creation of light string with simple args."""
    led_count = 11
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)
        with pytest.raises(IndexError):
            ws281x[led_count + 1]


def test_single_access_indexerror_numpy() -> None:
    """Test creation of light string with simple args."""
    led_count = 11
    led_count_np = np.array(np.arange(12), dtype=np.int32)[-1]
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)
        with pytest.raises(IndexError):
            ws281x[led_count_np]


def test_single_assignment_numpy_int() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)
        for i in np.arange(len(ws281x)):
            random_color = Pixel(PixelColor.random()).array
            ws281x[i] = random_color
            assigned_color = ws281x[i]
            assert assigned_color is not None
            assert_array_equal(assigned_color, random_color)


def test_multiple_assignment() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)

        # one
        assign_count = 1
        random_colors = PixelSequence.pixel_array_to_numpy_array(
            [Pixel(PixelColor.random()) for _ in range(assign_count)],
        )
        ws281x[0] = random_colors[0]
        assigned_colors = ws281x[0]
        assert assigned_colors is not None
        assert_array_equal(assigned_colors, random_colors[0])

        # stop only
        assign_count = 2
        random_colors = PixelSequence.pixel_array_to_numpy_array(
            [Pixel(PixelColor.random()) for _ in range(assign_count)],
        )
        ws281x[:assign_count] = random_colors
        assigned_colors = ws281x[:assign_count]
        assert assigned_colors is not None
        assert_array_equal(assigned_colors, random_colors)

        # start only
        random_colors = PixelSequence.pixel_array_to_numpy_array(
            [Pixel(PixelColor.random()) for _ in range(assign_count)],
        )
        ws281x[-assign_count:] = random_colors
        assigned_colors = ws281x[-assign_count:]
        assert assigned_colors is not None
        assert_array_equal(assigned_colors, random_colors)

        # step only
        random_colors = PixelSequence.pixel_array_to_numpy_array(
            [Pixel(PixelColor.random()) for _ in range(assign_count)],
        )
        ws281x[:: int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert assigned_colors is not None
        assert_array_equal(assigned_colors, random_colors)

        # all
        random_colors = PixelSequence.pixel_array_to_numpy_array(
            [Pixel(PixelColor.random()) for _ in range(assign_count)],
        )
        ws281x[0 : led_count : int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert assigned_colors is not None
        assert_array_equal(assigned_colors, random_colors)

        # nones
        random_colors = PixelSequence.pixel_array_to_numpy_array(
            [Pixel(PixelColor.random()) for _ in range(led_count)],
        )
        ws281x[:] = random_colors
        assigned_colors = ws281x[:]
        assert assigned_colors is not None
        assert_array_equal(assigned_colors, random_colors)


def test_multiple_assignment_simulated() -> None:
    """Test creation of light string with simple args."""
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        ws281x = WS281xString(led_count=led_count, simulate=True)

        # one
        assign_count = 1
        random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(assign_count)])
        ws281x[0] = random_colors[0]
        assigned_colors = ws281x[0]
        assert_array_equal(assigned_colors, random_colors[0])

        # stop only
        assign_count = 2
        random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(assign_count)])
        ws281x[:assign_count] = random_colors
        assigned_colors = ws281x[:assign_count]
        assert_array_equal(assigned_colors, random_colors)

        # start only
        random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(assign_count)])
        ws281x[-assign_count:] = random_colors
        assigned_colors = ws281x[-assign_count:]
        assert_array_equal(assigned_colors, random_colors)

        # step only
        random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(assign_count)])
        ws281x[:: int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert_array_equal(assigned_colors, random_colors)

        # all
        random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(assign_count)])
        ws281x[0 : led_count : int(led_count // 2)] = random_colors
        assigned_colors = ws281x[:: int(led_count // 2)]
        assert_array_equal(assigned_colors, random_colors)

        # nones
        random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(led_count)])
        ws281x[:] = random_colors
        assigned_colors = ws281x[:]
        assert_array_equal(assigned_colors, random_colors)


def test_context_manager() -> None:
    led_count = 10
    with mock.patch.object(WS281xString, "_instantiate_pixel_strip", new=mock_instantiate_pixel_strip):
        with WS281xString(led_count=led_count, simulate=True) as ws281x:
            # all
            random_colors = pixel_array_to_numpy_array([PixelColor.random for i in range(led_count)])
            ws281x[:] = random_colors
            assigned_colors = ws281x[:]
            assert_array_equal(assigned_colors, random_colors)
            assert_array_equal(assigned_colors, random_colors)
