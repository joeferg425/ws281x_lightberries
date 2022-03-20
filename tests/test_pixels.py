"""Test Pixel."""
from __future__ import annotations
import numpy as np
import pytest
from typing import Tuple
import LightBerries.LightPixels
from LightBerries.LightPixels import EnumLEDOrder, Pixel
from nptyping import NDArray


def test_pixel_creation_default():
    """Test default pixel creation and attributes."""
    LightBerries.LightPixels.DEFAULT_PIXEL_ORDER = EnumLEDOrder.GRB
    p = Pixel()
    assert p is not None
    assert len(p.array) == 3
    assert isinstance(p.hexstr, str)
    assert p.hexstr == "000000"
    assert str(p) == "PX #000000"
    assert isinstance(p.pixel, Pixel)
    assert p.pixel == Pixel(0)
    assert isinstance(p.tuple, Tuple)
    assert p.tuple == (0, 0, 0)


@pytest.mark.parametrize(
    "arg",
    [0x010000, np.array((1, 0, 0), dtype=np.int32), Pixel(0x010000)],
)
def test_pixel_creation_value_args(arg: int | NDArray[(3), np.float32] | "Pixel"):
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    LightBerries.LightPixels.DEFAULT_PIXEL_ORDER = EnumLEDOrder.GRB
    p = Pixel(arg)
    assert p is not None, f"Pixel: {p} is None"
    exp = 0x000100
    assert p._value == exp, f"Pixel._value: {p._value} != expected value: {exp}"
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


@pytest.mark.parametrize(
    "arg",
    [0x010000, np.array((1, 0, 0), dtype=np.int32), Pixel(0x010000)],
)
def test_pixel_creation_pixel_order(arg: int | NDArray[(3), np.float32] | "Pixel"):
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    LightBerries.LightPixels.DEFAULT_PIXEL_ORDER = EnumLEDOrder.RGB
    p = Pixel(arg)
    assert p is not None, f"Pixel: {p} is None"
    exp = 0x000100
    assert p._value == exp, f"Pixel._value: {p._value} != expected value: {exp}"
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
