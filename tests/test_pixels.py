"""Test Pixel."""
from __future__ import annotations
import numpy as np
import pytest
from typing import Callable
from numpy.testing import assert_array_equal

# import lightberries.pixel
from lightberries.pixel import LEDOrder, Pixel, PixelColors
from lightberries.exceptions import PixelException


def test_pixel_creation_default():
    """Test default pixel creation and attributes."""
    Pixel.DEFAULT_PIXEL_ORDER = LEDOrder.GRB.value
    p = Pixel()
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000000
    assert p.int_value == exp, f"Pixel.int: {p.int_value} != expected value: {exp}"
    exp = 3
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000000"
    assert p.hexstr == exp, f"Pixel.hexstr: {p.hexstr} != expected value: {exp}"
    exp = "PX #000000"
    assert str(p) == exp, f"str(Pixel): {str(p)} != expected value: {exp}"
    exp = Pixel(0x000000)
    assert p.pixel == exp, f"Pixel.pixel: {p.pixel} != expected value: {exp}"
    exp = (0, 0, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_creation_None():
    """Test default pixel creation and attributes."""
    Pixel.DEFAULT_PIXEL_ORDER = LEDOrder.GRB.value
    p = Pixel(None)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000000
    assert p.int_value == exp, f"Pixel.int: {p.int_value} != expected value: {exp}"
    exp = 3
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000000"
    assert p.hexstr == exp, f"Pixel.hexstr: {p.hexstr} != expected value: {exp}"
    exp = "PX #000000"
    assert str(p) == exp, f"str(Pixel): {str(p)} != expected value: {exp}"
    exp = Pixel(0x000000)
    assert p.pixel == exp, f"Pixel.pixel: {p.pixel} != expected value: {exp}"
    exp = (0, 0, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_creation_invalid_rgb_value():
    """Test default pixel creation and attributes."""
    with pytest.raises(PixelException):
        Pixel((0, 255, 9001))


def test_pixel_creation_invalid_rgb_type():
    """Test default pixel creation and attributes."""
    with pytest.raises(PixelException):
        Pixel({"a": 0, "b": 255, "c": 9001.5})


def test_pixel_int_value():
    """Test default pixel creation and attributes."""
    p = Pixel(0x100, order=LEDOrder.RGB)
    assert p.int_value == 0x100
    exp = (0, 1, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 1, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_int_cast_value():
    """Test default pixel creation and attributes."""
    p = Pixel(0x100, order=LEDOrder.RGB)
    assert int(p) == 0x100


def test_pixel_len():
    """Test default pixel creation and attributes."""
    p = Pixel(0x100, order=LEDOrder.RGB)
    assert len(p) == 3


def test_pixel_representation():
    """Test default pixel creation and attributes."""
    p = Pixel(0x100, order=LEDOrder.RGB)
    assert repr(p) == "<Pixel> PX #000100 (256/RGB)"


def test_pixel_equality():
    """Test default pixel creation and attributes."""
    p1 = Pixel(0x100, order=LEDOrder.RGB)
    p2 = Pixel((0, 1, 0), order=LEDOrder.RGB)
    assert p1 == p2


def test_pixel_equality_not_equal():
    """Test default pixel creation and attributes."""
    p1 = Pixel(0x100, order=LEDOrder.RGB)
    p2 = {"not": "valid"}
    assert p1 != p2


@pytest.mark.parametrize(
    "arg",
    [0x010000, np.array((1, 0, 0), dtype=np.int32), Pixel(0x010000, LEDOrder.RGB), Pixel(0x000100, LEDOrder.GRB)],
)
def test_pixel_creationint_args(arg: int | np.ndarray[(3), np.float32] | "Pixel"):
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    Pixel.DEFAULT_PIXEL_ORDER = LEDOrder.RGB.value
    p = Pixel(arg)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x010000
    assert p.int_value == exp, f"Pixel.int: {p.int_value} != expected value: {exp}"
    exp = 3
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "010000"
    assert p.hexstr == exp, f"Pixel.hexstr: {p.hexstr} != expected value: {exp}"
    exp = "PX #010000"
    assert str(p) == exp, f"str(Pixel): {str(p)} != expected value: {exp}"
    exp = Pixel(0x010000)
    assert p.pixel == exp, f"Pixel.pixel: {p.pixel} != expected value: {exp}"
    exp = (1, 0, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([1, 0, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (1, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([1, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


@pytest.mark.parametrize(
    "arg",
    [0x010000, np.array((1, 0, 0), dtype=np.int32), Pixel(0x010000, LEDOrder.GRB), Pixel(0x000100, LEDOrder.RGB)],
)
def test_pixel_creation_pixel_order(arg: int | np.ndarray[(3), np.float32] | "Pixel"):
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    Pixel.DEFAULT_PIXEL_ORDER = LEDOrder.GRB.value
    p = Pixel(arg)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000100
    assert p.int_value == exp, f"Pixel.int: {p.int_value} != expected value: {exp}"
    exp = 3
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000100"
    assert p.hexstr == exp, f"Pixel.hexstr: {p.hexstr} != expected value: {exp}"
    exp = "PX #000100"
    assert str(p) == exp, f"str(Pixel): {str(p)} != expected value: {exp}"
    exp = Pixel(0x000100)
    assert p.pixel == exp, f"Pixel.pixel: {p.pixel} != expected value: {exp}"
    exp = (0, 1, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (1, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([1, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_creation_pixel_order_invalid():
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    with pytest.raises(PixelException):
        Pixel(rgb=1, order=(1, 12, 34))


def test_pixelcolors():
    """Test whether the pixel colors helper class is returning valid and consistent colors."""
    # loop through each class member
    for var in dir(PixelColors):
        # skip private members
        if "__" not in var:
            # get member by name
            p = getattr(PixelColors, var)
            # if member is function, call it
            if isinstance(p, Callable):
                p = p()
            # check type and length of pixel's ndarray
            assert isinstance(p, Pixel), f"Pixel: {p} is not {Pixel}"
