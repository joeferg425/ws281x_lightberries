"""Test Light strings."""
from __future__ import annotations
from lightberries.ws281x_strings import WS281xString
from lightberries.pixel import PixelColors
from numpy.testing import assert_array_equal


def test_creation():
    """Test creation of light string with simple args."""
    led_count = 10
    s = WS281xString(ledCount=led_count, simulate=True)
    assert s is not None
    assert len(s) == led_count


def test_assignment():
    """Test creation of light string with simple args."""
    led_count = 10
    ws281x = WS281xString(ledCount=led_count, simulate=True)
    for i in range(len(ws281x)):
        random_color = PixelColors.random()
        ws281x[i] = random_color
        assigned_color = ws281x[i]
        assert_array_equal(assigned_color, random_color)
