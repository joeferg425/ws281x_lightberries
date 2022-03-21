"""Test Light strings."""
from __future__ import annotations
from LightBerries.LightStrings import LightString


def test_creation():
    """Test creation of light string with simple args."""
    led_count = 10
    s = LightString(ledCount=led_count, simulate=True)
    assert s is not None
    assert len(s) == led_count
