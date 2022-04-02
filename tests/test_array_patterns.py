from __future__ import annotations
from lightberries.array_patterns import ArrayPattern, ConvertPixelArrayToNumpyArray
import datetime

import numpy as np
from lightberries.pixel import Pixel, PixelColors


def test_default_color_sequence():
    now = datetime.datetime.now()
    last = np.zeros((2, 3))
    last_month = now.month - 1
    for i in range(52):
        date = now + datetime.timedelta(weeks=i)
        month = date.month
        if month != last_month:
            default_colors = ArrayPattern.DefaultColorSequenceByMonth(date)
            assert not np.array_equal(default_colors, last)
            assert len(default_colors.shape) > 1
            last = default_colors
        last_month = month


def test_pixel_array_off():
    for i in range(0, 101, 20):
        ary = ArrayPattern.PixelArrayOff(i)
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
        ary = ArrayPattern.SolidColorArray(i, color)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(i):
            assert np.array_equal(ary[j], color)


def test_color_transition_array():
    colors = ArrayPattern.DefaultColorSequenceByMonth()
    i = 10
    ary1 = ArrayPattern.ColorTransitionArray(i)
    assert ary1 is not None
    assert len(ary1.shape) == 2
    assert ary1.shape[0] == i
    assert ary1.shape[1] == 3
    for i in range(0, 101, 20):
        colors = np.array([PixelColors.random() for _ in range(int(i / 10))])
        ary1 = ArrayPattern.ColorTransitionArray(i, colors)
        assert ary1 is not None
        assert len(ary1.shape) == 2
        assert ary1.shape[0] == i
        assert ary1.shape[1] == 3
        ary2 = ArrayPattern.ColorTransitionArray(i, colors, wrap=False)
        assert ary2 is not None
        assert len(ary2.shape) == 2
        assert ary2.shape[0] == i
        assert ary2.shape[1] == 3


def test_rainbow_array():
    for i in range(0, 101, 20):
        ary = ArrayPattern.RainbowArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_repeating_color_sequence_array():
    i = 10
    colors = ArrayPattern.DefaultColorSequenceByMonth()
    ary = ArrayPattern.RepeatingColorSequenceArray(i)
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    for i in range(0, 101, 20):
        colors = np.array([PixelColors.random() for _ in range(int(i / 10))])
        ary = ArrayPattern.RepeatingColorSequenceArray(i, colors)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_repeating_rainbow_array():
    for i in range(0, 101, 20):
        ary = ArrayPattern.RepeatingRainbowArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(1, 5):
            ary = ArrayPattern.RepeatingRainbowArray(i, j)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3


def test_reflect_array():
    i = 20
    colors = ArrayPattern.DefaultColorSequenceByMonth()
    ary = ArrayPattern.ReflectArray(i)
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    for i in range(0, 101, 20):
        for j in range(1, 5):
            for k in range(1, 5):
                colors = np.array([PixelColors.random() for _ in range(int(i * j))])
                ary = ArrayPattern.ReflectArray(i, colors, k)
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
        ary = ArrayPattern.RandomArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_pseudorandom_array():
    for i in range(0, 101, 20):
        ary = ArrayPattern.PseudoRandomArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(0, int(i / 10)):
            if j == 0:
                colors = np.zeros((0, 3))
            else:
                colors = np.array([PixelColors.random() for _ in range(int(j))])
            ary = ArrayPattern.PseudoRandomArray(i, colors)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3


def test_colorstretch_array():
    i = 10
    colors = ArrayPattern.DefaultColorSequenceByMonth()
    ary = ArrayPattern.ColorStretchArray(i)
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    for i in range(0, 101, 20):
        for j in range(1, i + 1):
            colors = np.array([PixelColors.random() for _ in range(int(i / j))])
            ary = ArrayPattern.ColorStretchArray(i, colors)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3
