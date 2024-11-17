"""Test Pixel."""

# ruff: noqa: S101

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from lightberries.base.exceptions import PixelError
from lightberries.base.pixel import (
    LEDOrder,
    Pixel,
    PixelColor,
    _Pixel,  # type: ignore  # noqa: PGH003
    pixel_from_color,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

THREE = 3
HEX_ONE_HUNDRED = 0x100
HEX_TEN_THOUSAND = 0x10000
Pixel.default_pixel_order = LEDOrder.RGB
PIXEL1_RGB = Pixel(HEX_ONE_HUNDRED)
PIXEL2_RGB = Pixel(HEX_TEN_THOUSAND)
Pixel.default_pixel_order = LEDOrder.GRB
PIXEL1_GRB = Pixel(HEX_ONE_HUNDRED)
PIXEL2_GRB = Pixel(HEX_TEN_THOUSAND)


@pytest.fixture(autouse=True)
def run_around_tests() -> None:
    """Fixture."""
    # Code that will run before your test, for example:
    Pixel.default_pixel_order = LEDOrder.GRB


def test_pixel_creation_default() -> None:
    """Test default pixel creation and attributes."""
    p = Pixel()
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000000
    assert p.int32 == exp, f"Pixel.int32: {p.int32} != expected value: {exp}"
    exp = THREE
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000000"
    assert p.hex_str == exp, f"Pixel.hex_str: {p.hex_str} != expected value: {exp}"
    exp = "PX#000000:GRB"
    assert str(p) == exp, f"str(Pixel): {p!s} != expected value: {exp}"
    exp = Pixel(0x000000)
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = (0, 0, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_creation_none() -> None:
    """Test default pixel creation and attributes."""
    p = Pixel(None)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = 0x000000
    assert p.int32 == exp, f"Pixel.int32: {p.int32} != expected value: {exp}"
    exp = THREE
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000000"
    assert p.hex_str == exp, f"Pixel.hex_str: {p.hex_str} != expected value: {exp}"
    exp = "PX#000000:GRB"
    assert str(p) == exp, f"str(Pixel): {p!s} != expected value: {exp}"
    exp = Pixel(0x000000)
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = (0, 0, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_creation_invalid_rgb_value() -> None:
    """Test default pixel creation and attributes."""
    with pytest.raises(PixelError):
        Pixel((0, 255, 9001))


def test_pixel_creation_invalid_rgb_type() -> None:
    """Test default pixel creation and attributes."""
    with pytest.raises(PixelError):
        Pixel({"a": 0, "b": 255, "c": 9001.5})  # type: ignore  # noqa: PGH003


def test_pixel_int_value() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = Pixel(HEX_ONE_HUNDRED)
    assert p.int32 == HEX_ONE_HUNDRED
    exp = (0, 1, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 1, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_int_cast_value() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = Pixel(HEX_ONE_HUNDRED)
    assert int(p) == HEX_ONE_HUNDRED


def test_pixel_len() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = Pixel(HEX_ONE_HUNDRED)
    assert len(p) == THREE


def test_pixel_representation() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = Pixel(HEX_ONE_HUNDRED)
    assert repr(p) == "PX#000100:RGB"


def test_pixel_invert() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = Pixel((0, 255, 0))
    p2 = p1.invert()
    exp = np.array((255, 0, 255), dtype=np.int32)
    assert_array_equal(p2.array, exp, err_msg=f"Pixel.array: {p2.array} != expected value: {exp}")


def test_pixel_copy() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = Pixel((1, 127, 255))
    p2 = p1.copy()
    exp = np.array((1, 127, 255), dtype=np.int32)
    assert_array_equal(p2.array, exp, err_msg=f"Pixel.array: {p2.array} != expected value: {exp}")


def test_pixel_from_color() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = pixel_from_color(PixelColor.SKY)
    exp = np.array((0, 127, 255), dtype=np.int32)
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")


def test_pixel_equality() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = Pixel(HEX_ONE_HUNDRED)
    p2 = Pixel((0, 1, 0))
    assert p1 == p2


def test_pixel_equality_not_equal() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = Pixel(HEX_ONE_HUNDRED)
    p2 = {"not": "valid"}
    assert p1 != p2


def test_pixel_color_random() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = Pixel(PixelColor.get_RANDOM())
    p2 = Pixel(PixelColor.get_RANDOM())
    assert p1 != p2


def test_pixel_fade() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = pixel_from_color(PixelColor.WHITE)
    assert p1[0] == PixelColor.WHITE.red, f"red value does not match: {p1[0]} != {PixelColor.WHITE.red}"
    assert p1[1] == PixelColor.WHITE.green, f"green value does not match: {p1[1]} != {PixelColor.WHITE.green}"
    assert p1[2] == PixelColor.WHITE.blue, f"blue value does not match: {p1[2]} != {PixelColor.WHITE.blue}"
    p2 = p1.copy()
    p2.fade()
    assert p2[0] == PixelColor.WHITE.red - 25, f"red value does not match: {p2[0]} != {PixelColor.WHITE.red-25}"
    assert p2[1] == PixelColor.WHITE.green - 25, f"green value does not match: {p2[1]} != {PixelColor.WHITE.green-25}"
    assert p2[2] == PixelColor.WHITE.blue - 25, f"blue value does not match: {p2[2]} != {PixelColor.WHITE.blue-25}"
    p3 = p1.copy()
    p3.fade(Pixel(PixelColor.OFF))
    assert p3[0] == PixelColor.WHITE.red - 25, f"red value does not match: {p3[0]} != {PixelColor.WHITE.red-25}"
    assert p3[1] == PixelColor.WHITE.green - 25, f"green value does not match: {p3[1]} != {PixelColor.WHITE.green-25}"
    assert p3[2] == PixelColor.WHITE.blue - 25, f"blue value does not match: {p3[2]} != {PixelColor.WHITE.blue-25}"
    p4 = p1.copy()
    p4.fade(color_next=Pixel(PixelColor.OFF), fade_amount=25)
    assert p4[0] == PixelColor.WHITE.red - 25, f"red value does not match: {p4[0]} != {PixelColor.WHITE.red-25}"
    assert p4[1] == PixelColor.WHITE.green - 25, f"green value does not match: {p4[1]} != {PixelColor.WHITE.green-25}"
    assert p4[2] == PixelColor.WHITE.blue - 25, f"blue value does not match: {p4[2]} != {PixelColor.WHITE.blue-25}"
    p5 = Pixel()
    p6 = p5.copy()
    p6.fade(color_next=Pixel(PixelColor.CYAN), fade_amount=25)
    assert p6[0] == PixelColor.OFF.red, f"red value does not match: {p6[0]} != {PixelColor.OFF.red}"
    assert p6[1] == PixelColor.OFF.green + 25, f"green value does not match: {p6[1]} != {PixelColor.OFF.green+25}"
    assert p6[2] == PixelColor.OFF.blue + 25, f"blue value does not match: {p6[2]} != {PixelColor.OFF.blue+25}"
    p7 = p5.copy()
    p7.fade(color_next=Pixel(PixelColor.WHITE), fade_amount=255)
    assert p7[0] == PixelColor.WHITE.red, f"red value does not match: {p6[0]} != {PixelColor.WHITE.red}"
    assert p7[1] == PixelColor.WHITE.green, f"green value does not match: {p6[1]} != {PixelColor.WHITE.green}"
    assert p7[2] == PixelColor.WHITE.blue, f"blue value does not match: {p6[2]} != {PixelColor.WHITE.blue}"


def test_pixel_get_item() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = pixel_from_color(PixelColor.CYAN)
    assert p[0] == PixelColor.CYAN.red, f"red value does not match: {p[0]} != {PixelColor.CYAN.red}"
    assert p[1] == PixelColor.CYAN.green, f"green value does not match: {p[1]} != {PixelColor.CYAN.green}"
    assert p[2] == PixelColor.CYAN.blue, f"blue value does not match: {p[2]} != {PixelColor.CYAN.blue}"
    a = np.array([0, 1, 2], dtype=np.int32)
    assert p[a[0]] == PixelColor.CYAN.red, f"red value does not match: {p[a[0]]} != {PixelColor.CYAN.red}"
    assert p[a[1]] == PixelColor.CYAN.green, f"green value does not match: {p[a[1]]} != {PixelColor.CYAN.green}"
    assert p[a[2]] == PixelColor.CYAN.blue, f"blue value does not match: {p[a[2]]} != {PixelColor.CYAN.blue}"
    assert p[:1] == [PixelColor.CYAN.red], f"red value does not match: {p[:1]} != {[PixelColor.CYAN.red]}"
    assert p[1:2] == [PixelColor.CYAN.green], f"green value does not match: {p[1:2]} != {[PixelColor.CYAN.green]}"
    assert p[2:] == [PixelColor.CYAN.blue], f"blue value does not match: {p[2:]} != {[PixelColor.CYAN.blue]}"


def test_pixel_set_item() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p = Pixel()
    assert p[0] != PixelColor.GRAY.red, f"red value already matched: {p[0]} == {PixelColor.GRAY.red}"
    assert p[1] != PixelColor.GRAY.green, f"green value already matched: {p[1]} == {PixelColor.GRAY.green}"
    assert p[2] != PixelColor.GRAY.blue, f"blue value already matched: {p[2]} == {PixelColor.GRAY.blue}"
    p[0] = PixelColor.GRAY.red
    p[1] = PixelColor.GRAY.green
    p[2] = PixelColor.GRAY.blue
    assert p[0] == PixelColor.GRAY.red, f"red value does not match: {p[0]} != {PixelColor.GRAY.red}"
    assert p[1] == PixelColor.GRAY.green, f"green value does not match: {p[1]} != {PixelColor.GRAY.green}"
    assert p[2] == PixelColor.GRAY.blue, f"blue value does not match: {p[2]} != {PixelColor.GRAY.blue}"
    p = Pixel()
    assert p[0] != PixelColor.GRAY.red, f"red value already matched: {p[0]} == {PixelColor.GRAY.red}"
    assert p[1] != PixelColor.GRAY.green, f"green value already matched: {p[1]} == {PixelColor.GRAY.green}"
    assert p[2] != PixelColor.GRAY.blue, f"blue value already matched: {p[2]} == {PixelColor.GRAY.blue}"
    a = np.array([0, 1, 2], dtype=np.int32)
    p[a[0]] = PixelColor.GRAY.red
    p[a[1]] = PixelColor.GRAY.green
    p[a[2]] = PixelColor.GRAY.blue
    assert p[a[0]] == PixelColor.GRAY.red, f"red value does not match: {p[a[0]]} != {PixelColor.GRAY.red}"
    assert p[a[1]] == PixelColor.GRAY.green, f"green value does not match: {p[a[1]]} != {PixelColor.GRAY.green}"
    assert p[a[2]] == PixelColor.GRAY.blue, f"blue value does not match: {p[a[2]]} != {PixelColor.GRAY.blue}"
    p = Pixel()
    assert p[0] != PixelColor.GRAY.red, f"red value already matched: {p[0]} == {PixelColor.GRAY.red}"
    assert p[1] != PixelColor.GRAY.green, f"green value already matched: {p[1]} == {PixelColor.GRAY.green}"
    assert p[2] != PixelColor.GRAY.blue, f"blue value already matched: {p[2]} == {PixelColor.GRAY.blue}"
    p[:1] = [PixelColor.GRAY.red]
    p[1:2] = [PixelColor.GRAY.green]
    p[2:] = [PixelColor.GRAY.blue]
    assert p[:1] == [PixelColor.GRAY.red], f"red value does not match: {p[:1]} != {[PixelColor.GRAY.red]}"
    assert p[1:2] == [PixelColor.GRAY.green], f"green value does not match: {p[1:2]} != {[PixelColor.GRAY.green]}"
    assert p[2:] == [PixelColor.GRAY.blue], f"blue value does not match: {p[2:]} != {[PixelColor.GRAY.blue]}"


def test_pixel_color_pseudo_random() -> None:
    """Test default pixel creation and attributes."""
    Pixel.default_pixel_order = LEDOrder.RGB
    p1 = Pixel(PixelColor.get_PSEUDO_RANDOM())
    pixels = [Pixel(PixelColor.get_PSEUDO_RANDOM()) for _ in range(5)]
    assert not all(p1 == p for p in pixels)


PARAMS2: dict[str, Any] = {
    f"0x{v:X}" if isinstance(v, int) else str(v): v  # type: ignore  # noqa: PGH003
    for v in [  # type: ignore  # noqa: PGH003
        HEX_ONE_HUNDRED,
        np.array((0, 1, 0), dtype=np.int32),
        PIXEL1_RGB,
        PIXEL1_GRB,
    ]
}


@pytest.mark.parametrize(
    "arg",
    PARAMS2.values(),
    ids=PARAMS2.keys(),
)
def test_pixel_creation_rgb(arg: int | NDArray[np.float32] | Pixel) -> None:
    """Test the valid creation methods.

    Args:
    ----
        arg: initial pixel value

    """
    Pixel.default_pixel_order = LEDOrder.RGB
    p = Pixel(arg)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = HEX_ONE_HUNDRED
    assert p.int32 == exp, f"Pixel.int32: {p.int32} != expected value: {exp}"
    exp = THREE
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000100"
    assert p.hex_str == exp, f"Pixel.hex_str: {p.hex_str} != expected value: {exp}"
    exp = "PX#000100:RGB"
    assert str(p) == exp, f"str(Pixel): {p!s} != expected value: {exp}"
    exp = Pixel(HEX_ONE_HUNDRED)
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = HEX_ONE_HUNDRED
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = (0, 1, 0)
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = (0, 1, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (0, 1, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


PARAMS1: dict[str, Any] = {
    f"0x{v:X}" if isinstance(v, int) else str(v): v  # type: ignore  # noqa: PGH003
    for v in [  # type: ignore  # noqa: PGH003
        HEX_ONE_HUNDRED,
        np.array((0, 1, 0), dtype=np.int32),
        PIXEL2_RGB,
        PIXEL2_GRB,
    ]
}


@pytest.mark.parametrize(
    "arg",
    PARAMS1.values(),
    ids=PARAMS1.keys(),
)
def test_pixel_creation_grb(arg: int | NDArray[np.float32] | Pixel) -> None:
    """Test the valid creation methods.

    Args:
    ----
        arg: initial pixel value

    """
    Pixel.default_pixel_order = LEDOrder.GRB
    p = Pixel(arg)
    assert isinstance(p, Pixel), f"Pixel: {p} is not {type(Pixel)}"
    exp = HEX_ONE_HUNDRED
    assert p.int32 == exp, f"Pixel.int32: {p.int32} != expected value: {exp}"
    exp = THREE
    assert len(p.array) == exp, f"Pixel.array: {p.array} != expected value: {exp}"
    exp = "000100"
    assert p.hex_str == exp, f"Pixel.hex_str: {p.hex_str} != expected value: {exp}"
    exp = "PX#000100:GRB"
    assert str(p) == exp, f"str(Pixel): {p!s} != expected value: {exp}"
    exp = Pixel(HEX_ONE_HUNDRED)
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = HEX_ONE_HUNDRED
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = (0, 1, 0)
    assert p == exp, f"Pixel: {p} != expected value: {exp}"
    exp = (0, 1, 0)
    assert p.tuple == exp, f"Pixel.tuple: {p.tuple} != expected value: {exp}"
    exp = np.array([0, 1, 0])
    assert_array_equal(p.array, exp, err_msg=f"Pixel.array: {p.array} != expected value: {exp}")
    exp = (1, 0, 0)
    assert p.rgb_tuple == exp, f"Pixel.rgb_tuple: {p.rgb_tuple} != expected value: {exp}"
    exp = np.array([1, 0, 0])
    assert_array_equal(p.rgb_array, exp, err_msg=f"Pixel.rgb_array: {p.rgb_array} != expected value: {exp}")


def test_pixel_creation_pixel_order_invalid() -> None:
    """Test the valid creation methods.

    Args:
    ----
        arg: initial pixel value

    """
    Pixel.default_pixel_order = (1, 12, 34)  # type: ignore  # noqa: PGH003
    with pytest.raises(PixelError):
        Pixel(color=(1, 1, 1))


def test_pixel_colors() -> None:
    """Test whether the pixel colors helper class is returning valid and consistent colors."""
    # loop through each class member
    for var in dir(PixelColor):
        # skip private members
        if "__" not in var:
            # get member by name
            pixel_function = getattr(PixelColor, var)
            # if member is function, call it
            if isinstance(pixel_function, PixelColor):
                pixel = cast("_Pixel", pixel_function.value)
                # check type and length of pixel's ndarray
                assert isinstance(pixel, _Pixel), f"Pixel: {pixel} is not {_Pixel}"  # type: ignore  # noqa: PGH003
