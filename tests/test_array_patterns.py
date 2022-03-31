from __future__ import annotations
from lightberries.array_patterns import (
    DefaultColorSequenceByMonth,
    PixelArrayOff,
    ConvertPixelArrayToNumpyArray,
    PseudoRandomArray,
    RandomArray,
    RepeatingColorSequenceArray,
    RepeatingRainbowArray,
    SolidColorArray,
    ColorTransitionArray,
    RainbowArray,
    ReflectArray,
    ColorStretchArray,
)
import datetime

import numpy as np
from lightberries.pixel import Pixel, PixelColors


def test_default_color_sequence():
    now = datetime.datetime.now()
    last = np.zeros((2, 3))
    last_month = now.month
    for i in range(52):
        date = now + datetime.timedelta(weeks=i)
        month = date.month
        if month != last_month:
            default_colors = DefaultColorSequenceByMonth(date)
            assert not np.array_equal(default_colors, last)
            assert len(default_colors.shape) > 1
            last = default_colors
        last_month = month


def test_pixel_array_off():
    for i in range(0, 101, 20):
        ary = PixelArrayOff(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_convert_pixel_array_to_numpy_array():
    for i in range(0, 5):
        ary1 = [Pixel(PixelColors.random()) for _ in range(i)]
        ary2 = ConvertPixelArrayToNumpyArray(ary1)
        assert ary1 is not None
        assert ary2 is not None
        assert len(ary2) == i
        assert len(ary2.shape) == 2
        assert ary2.shape[0] == i
        assert ary2.shape[1] == 3
        for j in range(i):
            assert np.array_equal(ary1[j].array, ary2[j])


def test_solid_color_array():
    for i in range(0, 101, 20):
        color = PixelColors.random()
        ary = SolidColorArray(i, color)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(i):
            assert np.array_equal(ary[j], color)


def test_color_transition_array():
    for i in range(0, 101, 20):
        colors = np.array([PixelColors.random() for _ in range(int(i / 10))])
        ary1 = ColorTransitionArray(i, colors)
        assert ary1 is not None
        assert len(ary1.shape) == 2
        assert ary1.shape[0] == i
        assert ary1.shape[1] == 3
        ary2 = ColorTransitionArray(i, colors, wrap=False)
        assert ary2 is not None
        assert len(ary2.shape) == 2
        assert ary2.shape[0] == i
        assert ary2.shape[1] == 3


def test_rainbow_array():
    for i in range(0, 101, 20):
        ary = RainbowArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_repeating_color_sequence_array():
    for i in range(0, 101, 20):
        colors = np.array([PixelColors.random() for _ in range(int(i / 10))])
        ary = RepeatingColorSequenceArray(i, colors)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_repeating_rainbow_array():
    for i in range(0, 101, 20):
        ary = RepeatingRainbowArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(1, 5):
            ary = RepeatingRainbowArray(i, j)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3


def test_reflect_array():
    for i in range(0, 101, 20):
        for j in range(1, 5):
            for k in range(1, 5):
                colors = np.array([PixelColors.random() for _ in range(int(i * j))])
                ary = ReflectArray(i, colors, k)
                assert ary is not None
                assert len(ary.shape) == 2
                assert ary.shape[0] == i
                assert ary.shape[1] == 3
                assert ary is not None
                assert len(ary.shape) == 2
                assert ary.shape[0] == i
                assert ary.shape[1] == 3


def test_random_array():
    for i in range(0, 101, 20):
        ary = RandomArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_pseudorandom_array():
    for i in range(0, 101, 20):
        ary = PseudoRandomArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(0, int(i / 10)):
            if j == 0:
                colors = np.zeros((0, 3))
            else:
                colors = np.array([PixelColors.random() for _ in range(int(j))])
            ary = PseudoRandomArray(i, colors)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3


def test_colorstretch_array():
    for i in range(0, 101, 20):
        for j in range(1, i + 1):
            colors = np.array([PixelColors.random() for _ in range(int(i / j))])
            ary = ColorStretchArray(i, colors)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3
