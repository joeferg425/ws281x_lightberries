"""Test Pixel."""
from __future__ import annotations
import numpy as np
import pytest
from typing import Callable
import lightberries.pixel
from lightberries.pixel import EnumLEDOrder, Pixel, PixelColors


def test_pixel_creation_default():
    """Test default pixel creation and attributes."""
    lightberries.pixel.DEFAULT_PIXEL_ORDER = EnumLEDOrder.GRB
    p = Pixel()
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000000
    assert p.int == exp, f"Pixel.int: {p.int} != expected value: {exp}"
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


def test_pixel_creation_None():
    """Test default pixel creation and attributes."""
    lightberries.pixel.DEFAULT_PIXEL_ORDER = EnumLEDOrder.GRB
    p = Pixel(None)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000000
    assert p.int == exp, f"Pixel.int: {p.int} != expected value: {exp}"
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


@pytest.mark.parametrize(
    "arg",
    [0x010000, np.array((1, 0, 0), dtype=np.int32), Pixel(0x010000)],
)
def test_pixel_creationint_args(arg: int | np.ndarray[(3), np.float32] | "Pixel"):
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    lightberries.pixel.DEFAULT_PIXEL_ORDER = EnumLEDOrder.GRB
    p = Pixel(arg)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000100
    assert p.int == exp, f"Pixel.int: {p.int} != expected value: {exp}"
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
def test_pixel_creation_pixel_order(arg: int | np.ndarray[(3), np.float32] | "Pixel"):
    """Test the valid creation methods.

    Args:
        arg: initial pixel value
    """
    lightberries.pixel.DEFAULT_PIXEL_ORDER = EnumLEDOrder.RGB
    p = Pixel(arg)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000100
    assert p.int == exp, f"Pixel.int: {p.int} != expected value: {exp}"
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
            assert isinstance(p, np.ndarray), f"Pixel: {p} is not {np.ndarray}"
            exp = 3
            assert len(p) == exp, f"Pixel length: {len(p)} is not {exp}"
