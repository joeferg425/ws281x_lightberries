from __future__ import annotations

import datetime

import numpy as np
from lightberries.light_sequences.base import ArraySequence, pixel_array_to_numpy_array
from lightberries.pixel import Pixel, PixelColors
from numpy.testing import assert_array_equal


def test_default_color_sequence():
    now = datetime.datetime.now()
    last = np.zeros((2, 3))
    last_month = now.month - 1
    for i in range(52):
        date = now + datetime.timedelta(weeks=i)
        month = date.month
        if month != last_month:
            default_colors = ArraySequence.default_color_sequence_by_month(date)
            assert not np.array_equal(default_colors, last)
            assert len(default_colors.shape) > 1
            last = default_colors
        last_month = month


def test_pixel_array_off():
    for i in range(0, 101, 20):
        ary = ArraySequence.PixelArrayOff(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_pixel_array_to_numpy_array():
    for i in range(5):
        ary1 = [Pixel(PixelColors.random) for _ in range(i)]
        ary2 = pixel_array_to_numpy_array(ary1)
        assert ary1 is not None
        assert ary2 is not None
        assert len(ary2) == i
        assert len(ary2.shape) == 2
        assert ary2.shape[0] == i
        assert ary2.shape[1] == 3
        for j in range(i):
            assert_array_equal(ary1[j].array, ary2[j])


def test_solid_color_array():
    for i in range(0, 101, 20):
        color = PixelColors.random.array
        ary = ArraySequence.SolidSequence(i, color)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(i):
            assert np.array_equal(ary[j], color)
    color = ArraySequence.default_color_sequence_by_month()[0]
    ary = ArraySequence.SolidSequence(i)
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    for j in range(i):
        assert np.array_equal(ary[j], color)


def test_color_transition_array():
    colors = ArraySequence.default_color_sequence_by_month()
    i = 10
    ary1 = ArraySequence.ColorTransitionArray(i)
    assert ary1 is not None
    assert len(ary1.shape) == 2
    assert ary1.shape[0] == i
    assert ary1.shape[1] == 3
    for i in range(0, 101, 20):
        colors = np.array([PixelColors.random.array for _ in range(int(i / 10))])
        ary1 = ArraySequence.ColorTransitionArray(i, colors)
        assert ary1 is not None
        assert len(ary1.shape) == 2
        assert ary1.shape[0] == i
        assert ary1.shape[1] == 3
        ary2 = ArraySequence.ColorTransitionArray(i, colors, wrap=False)
        assert ary2 is not None
        assert len(ary2.shape) == 2
        assert ary2.shape[0] == i
        assert ary2.shape[1] == 3


def test_rainbow_array():
    for i in range(0, 101, 20):
        ary = ArraySequence.RainbowArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_repeating_color_sequence_array():
    i = 10
    colors = ArraySequence.default_color_sequence_by_month()
    ary = ArraySequence.RepeatingColorSequenceArray(i)
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    for i in range(0, 101, 20):
        colors = np.array([PixelColors.random.array for _ in range(int(i / 10))])
        ary = ArraySequence.RepeatingColorSequenceArray(i, colors)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_repeating_rainbow_array():
    for i in range(0, 101, 20):
        ary = ArraySequence.RepeatingRainbowArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(1, 5):
            ary = ArraySequence.RepeatingRainbowArray(i, j)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3


def test_reflect_array():
    i = 20
    colors = ArraySequence.default_color_sequence_by_month()
    ary = ArraySequence.ReflectArray(i)
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
                colors = np.array([PixelColors.random.array for _ in range(int(i * j))])
                ary = ArraySequence.ReflectArray(i, colors, k)
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
        ary = ArraySequence.RandomArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3


def test_pseudorandom_array():
    for i in range(0, 101, 20):
        ary = ArraySequence.PseudoRandomArray(i)
        assert ary is not None
        assert len(ary.shape) == 2
        assert ary.shape[0] == i
        assert ary.shape[1] == 3
        for j in range(int(i / 10)):
            if j == 0:
                colors = np.zeros((0, 3))
            else:
                colors = np.array([PixelColors.random.array for _ in range(int(j))])
            ary = ArraySequence.PseudoRandomArray(i, colors)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3


def test_colorstretch_array():
    i = 10
    colors = ArraySequence.default_color_sequence_by_month()
    ary = ArraySequence.ColorStretchArray(i)
    assert ary is not None
    assert len(ary.shape) == 2
    assert ary.shape[0] == i
    assert ary.shape[1] == 3
    for i in range(0, 101, 20):
        for j in range(1, i + 1):
            colors = np.array([PixelColors.random for _ in range(int(i / j))])
            ary = ArraySequence.ColorStretchArray(i, colors)
            assert ary is not None
            assert len(ary.shape) == 2
            assert ary.shape[0] == i
            assert ary.shape[1] == 3
