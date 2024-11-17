"""Test array patterns."""

# ruff: noqa: S101, D103

from __future__ import annotations

import datetime

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from lightberries.array_sequence import (
    ArraySequence,
    SequenceOff,
    SequencePseudoRandom,
    SequenceRainbow,
    SequenceRainbowRepeating,
    SequenceRandom,
    SequenceReflect,
    SequenceRepeat,
    SequenceSolid,
    SequenceStretch,
    SequenceTransition,
)
from lightberries.base.pixel import Pixel, PixelColor
from lightberries.pixel_sequence import PixelSequence

TWO = 2
THREE = 3


def test_default_color_sequence() -> None:
    now = datetime.datetime.now()  # noqa: DTZ005
    last = np.zeros((2, 3), dtype=np.int32)
    last_month = now.month - 1
    for i in range(52):
        date = now + datetime.timedelta(weeks=i)
        month = date.month
        if month != last_month:
            default_colors = PixelSequence.pixel_array_to_numpy_array(PixelSequence.get_monthly_color_sequence(date))
            assert not np.array_equal(default_colors, last)
            assert len(default_colors.shape) > 1
            last = default_colors
        last_month = month


RANGE_0_101_20 = list(range(0, 101, 20))


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_pixel_array_off(led_count: int) -> None:
    sequence = SequenceOff(led_count=led_count)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE


RANGE_0_5_1 = list(range(0, 5, 1))


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_5_1,
    ids=[f"led_count: {i}" for i in RANGE_0_5_1],
)
def test_pixel_array_to_numpy_array(led_count: int) -> None:
    sequence = SequenceRandom(led_count=led_count)
    array = SequenceRandom.pixel_array_to_numpy_array(sequence)
    assert sequence is not None
    assert array is not None
    assert len(array) == led_count
    assert len(array.shape) == TWO
    assert array.shape[0] == led_count
    assert array.shape[1] == THREE
    for j in range(led_count):
        a1 = sequence[j].rgb_array
        a2 = array[j]
        assert_array_equal(a1, a2)


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_solid_color_array(led_count: int) -> None:
    color = Pixel(PixelColor.get_RANDOM())
    sequence = SequenceSolid(led_count=led_count, color=color)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    for j in range(led_count):
        a1 = sequence[j].array
        a2 = color.array
        assert np.array_equal(a1, a2)


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_color_transition_array(led_count: int) -> None:
    colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count / 10))]
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=colors)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == max(led_count, len(colors))
    assert sequence.array.shape[1] == THREE
    sequence2 = SequenceTransition(led_count, colors, wrap=False)
    assert sequence2 is not None
    assert len(sequence2.array.shape) == TWO
    assert sequence2.array.shape[0] == led_count
    assert sequence2.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_rainbow_array(led_count: int) -> None:
    sequence = SequenceRainbow(led_count=led_count)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_repeating_color_sequence_array(led_count: int) -> None:
    colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count / 10))]
    sequence = SequenceRepeat(led_count=led_count, pixel_sequence=colors)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_repeating_rainbow_array(led_count: int) -> None:
    sequence = SequenceRainbowRepeating(led_count=led_count)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    for j in range(1, 5):
        sequence = SequenceRainbowRepeating(led_count=led_count, segment_length=j)
        assert sequence is not None
        assert len(sequence.array.shape) == TWO
        assert sequence.array.shape[0] == led_count
        assert sequence.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_reflect_array(led_count: int) -> None:
    for j in range(1, 5):
        for fold_length in range(1, 5):
            colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count * j))]
            sequence = SequenceReflect(led_count=led_count, pixel_sequence=colors, fold_length=fold_length)
            assert sequence is not None
            assert len(sequence.array.shape) == TWO
            assert sequence.array.shape[0] == led_count
            assert sequence.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_random_array(led_count: int) -> None:
    sequence = SequenceRandom(led_count=led_count)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_pseudorandom_array(led_count: int) -> None:
    for j in range(int(led_count / 10)):
        if j == 0:
            colors = []
        else:
            colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(j))]
        sequence = SequencePseudoRandom(led_count=led_count, pixel_sequence=colors)
        assert sequence is not None
        assert len(sequence.array.shape) == TWO
        assert sequence.array.shape[0] == led_count
        assert sequence.array.shape[1] == THREE


@pytest.mark.parametrize(
    "led_count",
    RANGE_0_101_20,
    ids=[f"led_count: {i}" for i in RANGE_0_101_20],
)
def test_color_stre0tch_array(led_count: int) -> None:
    for j in range(1, led_count + 1):
        colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count / j))]
        sequence = SequenceStretch(led_count=led_count, pixel_sequence=colors)
        assert sequence is not None
        assert len(sequence.array.shape) == TWO
        assert sequence.array.shape[0] == led_count
        assert sequence.array.shape[1] == THREE
