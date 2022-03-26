"""Test Light strings."""
from __future__ import annotations
from lightberries.ws281x_strings import WS281xString
from lightberries.pixel import PixelColors
from numpy.testing import assert_array_equal
from lightberries.array_patterns import ConvertPixelArrayToNumpyArray


def test_creation():
    """Test creation of light string with simple args."""
    led_count = 10
    s = WS281xString(ledCount=led_count, simulate=True)
    assert s is not None
    assert len(s) == led_count


def test_single_assignment():
    """Test creation of light string with simple args."""
    led_count = 10
    ws281x = WS281xString(ledCount=led_count, simulate=True)
    for i in range(len(ws281x)):
        random_color = PixelColors.random()
        ws281x[i] = random_color
        assigned_color = ws281x[i]
        assert_array_equal(assigned_color, random_color)


def test_multiple_assignment():
    """Test creation of light string with simple args."""
    led_count = 10
    ws281x = WS281xString(ledCount=led_count, simulate=True)

    # stop only
    assign_count = 2
    random_colors = ConvertPixelArrayToNumpyArray(
        [PixelColors.random() for i in range(assign_count)]
    )
    ws281x[:assign_count] = random_colors
    assigned_colors = ws281x[:assign_count]
    assert_array_equal(assigned_colors, random_colors)

    # start only
    random_colors = ConvertPixelArrayToNumpyArray(
        [PixelColors.random() for i in range(assign_count)]
    )
    ws281x[-assign_count:] = random_colors
    assigned_colors = ws281x[-assign_count:]
    assert_array_equal(assigned_colors, random_colors)

    # step only
    random_colors = ConvertPixelArrayToNumpyArray(
        [PixelColors.random() for i in range(assign_count)]
    )
    ws281x[:: int(led_count // 2)] = random_colors
    assigned_colors = ws281x[:: int(led_count // 2)]
    assert_array_equal(assigned_colors, random_colors)

    # all
    random_colors = ConvertPixelArrayToNumpyArray(
        [PixelColors.random() for i in range(assign_count)]
    )
    ws281x[0 : led_count : int(led_count // 2)] = random_colors
    assigned_colors = ws281x[:: int(led_count // 2)]
    assert_array_equal(assigned_colors, random_colors)

    # nones
    random_colors = ConvertPixelArrayToNumpyArray(
        [PixelColors.random() for i in range(assign_count)]
    )
    ws281x[:] = random_colors
    assigned_colors = ws281x[:]
    assert_array_equal(assigned_colors, random_colors)
