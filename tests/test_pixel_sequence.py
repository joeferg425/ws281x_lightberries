"""Test array patterns."""

# ruff: noqa: S101, D103, SLF001, PGH003, PLR2004

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


RANGE_100: list[int | None] = [None, *list(range(0, 101, 3))]
RANGE_5 = list(range(0, 5, 1))


def test_sequence_no_name_in_base() -> None:
    sequence = ArraySequence()
    assert sequence._name == ArraySequence.__name__  # type: ignore


def test_sequence_default() -> None:
    now = datetime.datetime.now()  # noqa: DTZ005
    last = np.zeros((2, 3), dtype=np.int32)
    last_month = now.month - 1
    for i in range(52):
        date = now + datetime.timedelta(weeks=i)
        month = date.month
        if month != last_month:
            sequence = PixelSequence.get_monthly_color_sequence(date)
            assert not np.array_equal(sequence.array, last)
            assert len(sequence.array.shape) > 1
            assert sequence._name == PixelSequence.__name__  # type: ignore
            last = sequence.array
        last_month = month


def test_sequence_get_item() -> None:
    pixel_list = [Pixel(PixelColor.RED), Pixel(PixelColor.GREEN), Pixel(PixelColor.BLUE)]
    sequence = PixelSequence(pixel_sequence=pixel_list)
    for i in range(sequence.led_count):
        assert_array_equal(pixel_list[i].array, sequence[i].array)
    idxs = np.array(range(sequence.led_count), dtype=np.int32)
    for i in idxs:
        assert_array_equal(pixel_list[i].array, sequence[i].array)  # type: ignore
    idxs = list(range(sequence.led_count))
    a1 = np.array([p.array for p in pixel_list])
    a2 = np.array([p.array for p in sequence[idxs]])
    assert_array_equal(a1, a2)  # type: ignore


def test_sequence_set_item() -> None:
    pixel_list = [Pixel(PixelColor.RED), Pixel(PixelColor.GREEN), Pixel(PixelColor.BLUE)]
    sequence = PixelSequence(pixel_sequence=pixel_list)
    new_color = Pixel(PixelColor.CYAN)
    pixel_list2 = [new_color, new_color, new_color]
    for i in range(sequence.led_count):
        sequence[i] = new_color
    for i in range(sequence.led_count):
        assert_array_equal(pixel_list2[i].array, sequence[i].array)
    pixel_list = [Pixel(PixelColor.RED), Pixel(PixelColor.GREEN), Pixel(PixelColor.BLUE)]
    idxs = np.array(range(sequence.led_count), dtype=np.int32)
    for i in idxs:
        sequence[i] = new_color
    for i in idxs:
        assert_array_equal(pixel_list2[i].array, sequence[i].array)  # type: ignore
    pixel_list = [Pixel(PixelColor.RED), Pixel(PixelColor.GREEN), Pixel(PixelColor.BLUE)]
    idxs = list(range(sequence.led_count))
    sequence[idxs] = pixel_list2[:]
    a1 = np.array([p.array for p in pixel_list2])
    a2 = np.array([p.array for p in sequence[idxs]])
    assert_array_equal(a1, a2)  # type: ignore


def test_sequence_led_index_zero() -> None:
    sequence = PixelSequence()
    assert sequence.led_index == 0
    sequence.advance_index()
    assert sequence.led_index == 0


def test_sequence_led_index() -> None:
    sequence = PixelSequence(led_count=2)
    assert sequence.led_index == 0
    sequence.advance_index()
    assert sequence.led_index == 1


def test_sequence_set_item_error() -> None:
    sequence = PixelSequence()
    with pytest.raises(TypeError):
        sequence[1] = PixelColor.CYAN  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_off(led_count: int | None) -> None:
    sequence = SequenceOff(led_count=led_count)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceOff.__name__  # type: ignore


def test_sequence_off_list() -> None:
    led_count = None
    pixel_sequence = PixelSequence.get_monthly_color_sequence().list
    sequence = SequenceOff(led_count=led_count, pixel_sequence=pixel_sequence)
    if led_count is None:
        led_count = len(pixel_sequence)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceOff.__name__  # type: ignore


def test_sequence_off_list_short() -> None:
    led_count = None
    pixel_sequence = PixelSequence.get_monthly_color_sequence().list
    sequence = SequenceOff(led_count=led_count, pixel_sequence=pixel_sequence)
    if led_count is None:
        led_count = len(pixel_sequence)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceOff.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_5,
    ids=[f"led_count: {i}" for i in RANGE_5],
)
def test_array_to_numpy_array(led_count: int | None) -> None:
    sequence = SequenceRandom(led_count=led_count)
    array = SequenceRandom.pixel_array_to_numpy_array(sequence)
    assert sequence is not None
    assert array is not None
    assert len(array) == led_count
    assert len(array.shape) == TWO
    assert array.shape[0] == led_count
    assert array.shape[1] == THREE
    assert sequence._name == SequenceRandom.__name__  # type: ignore
    for j in range(led_count if led_count is not None else 0):
        a1 = sequence[j].rgb_array
        a2 = array[j]
        assert_array_equal(a1, a2)


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_solid(led_count: int | None) -> None:
    color = Pixel(PixelColor.get_RANDOM())
    sequence = SequenceSolid(led_count=led_count, color=color)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceSolid.__name__  # type: ignore
    for j in range(led_count):
        a1 = sequence[j].array
        a2 = color.array
        assert np.array_equal(a1, a2)


def test_sequence_solid_none() -> None:
    led_count = None
    color = None
    sequence = SequenceSolid(led_count=led_count, color=color)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
        color = PixelSequence.get_monthly_color_sequence()[0]
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceSolid.__name__  # type: ignore
    for j in range(led_count):
        a1 = sequence[j].array
        a2 = color.array  # type: ignore
        assert np.array_equal(a1, a2)


def test_sequence_solid_pixel_color() -> None:
    led_count = None
    color = PixelColor.OFF
    sequence = SequenceSolid(led_count=led_count, color=color)
    led_count = PixelSequence.get_monthly_color_sequence().led_count
    color = Pixel(color)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceSolid.__name__  # type: ignore
    for j in range(led_count):
        a1 = sequence[j].array
        a2 = color.array  # type: ignore
        assert np.array_equal(a1, a2)


def test_sequence_solid_pixel_list() -> None:
    color = Pixel(PixelColor.BLUE)
    pixel_sequence = [color for _ in range(5)]
    led_count = len(pixel_sequence) + 2
    sequence = SequenceSolid(led_count=led_count, color=color, pixel_sequence=pixel_sequence)
    color = Pixel(color)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceSolid.__name__  # type: ignore
    for j in range(led_count):
        a1 = sequence[j].array
        a2 = color.array  # type: ignore
        assert np.array_equal(a1, a2)


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_transition_with_wrap(led_count: int | None) -> None:
    colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count if led_count is not None else 0 / 10))]
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=colors, wrap=True)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == max(led_count if led_count is not None else 0, len(colors))
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceTransition.__name__  # type: ignore


def test_sequence_transition_no_sequence() -> None:
    led_count = 3
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=None, wrap=True)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE


def test_sequence_transition_no_sequence_short_count() -> None:
    led_count = 2
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=None, wrap=True)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceTransition.__name__  # type: ignore


def test_sequence_transition_none_none() -> None:
    led_count = 3
    sequence = SequenceTransition(led_count=None, pixel_sequence=None, wrap=True)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceTransition.__name__  # type: ignore


def test_sequence_transition_none_none_none() -> None:
    led_count = 3
    sequence = SequenceTransition(led_count=None, pixel_sequence=None, wrap=None)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceTransition.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_transition_no_wrap(led_count: int | None) -> None:
    colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count if led_count is not None else 0 / 10))]
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=colors, wrap=False)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceTransition.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_rainbow(led_count: int | None) -> None:
    sequence = SequenceRainbow(led_count=led_count)
    if led_count is None:
        led_count = 4
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRainbow.__name__  # type: ignore


def test_sequence_rainbow_list() -> None:
    pixel_sequence = PixelSequence.get_monthly_color_sequence().list
    led_count = len(pixel_sequence)
    sequence = SequenceRainbow(led_count=led_count, pixel_sequence=PixelSequence.get_monthly_color_sequence().list)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRainbow.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_repeat(led_count: int | None) -> None:
    colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count if led_count is not None else 0 / 10))]
    sequence = SequenceRepeat(led_count=led_count, pixel_sequence=colors)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRepeat.__name__  # type: ignore


def test_sequence_repeat_none() -> None:
    led_count = None
    sequence = SequenceRepeat(led_count=led_count, pixel_sequence=None)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRepeat.__name__  # type: ignore


def test_sequence_repeat_empty() -> None:
    led_count = None
    sequence = SequenceRepeat(led_count=led_count, pixel_sequence=[])
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRepeat.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_rainbow_repeat(led_count: int | None) -> None:
    sequence = SequenceRainbowRepeating(led_count=led_count)
    test_led_count = led_count
    if led_count is None:
        test_led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == test_led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRainbowRepeating.__name__  # type: ignore
    for j in range(1, 5):
        sequence = SequenceRainbowRepeating(led_count=led_count, segment_length=j)
        assert sequence is not None
        assert len(sequence.array.shape) == TWO
        assert sequence.array.shape[0] == test_led_count
        assert sequence.array.shape[1] == THREE
        assert sequence._name == SequenceRainbowRepeating.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_reflect(led_count: int | None) -> None:
    for j in range(1, 5):
        for fold_length in range(1, 5):
            if led_count is not None:
                color_count = led_count * j
            else:
                color_count = PixelSequence.get_monthly_color_sequence().led_count * j
            colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(color_count)]
            sequence = SequenceReflect(led_count=led_count, pixel_sequence=colors, fold_length=fold_length)
            if led_count is None:
                led_count = PixelSequence.get_monthly_color_sequence().led_count
            assert sequence is not None
            assert len(sequence.array.shape) == TWO
            assert sequence.array.shape[0] == led_count
            assert sequence.array.shape[1] == THREE
            assert sequence._name == SequenceReflect.__name__  # type: ignore


def test_sequence_reflect_none() -> None:
    led_count = None
    colors = None
    sequence = SequenceReflect(led_count=led_count, pixel_sequence=colors)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceReflect.__name__  # type: ignore


def test_sequence_reflect_fold_len() -> None:
    led_count = 6
    colors = PixelSequence.get_monthly_color_sequence()
    fold_length = colors.led_count
    sequence = SequenceReflect(led_count=led_count, pixel_sequence=colors, fold_length=fold_length)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceReflect.__name__  # type: ignore


def test_sequence_reflect_fold_len_none() -> None:
    led_count = 6
    colors = PixelSequence.get_monthly_color_sequence()
    fold_length = None
    sequence = SequenceReflect(led_count=led_count, pixel_sequence=colors, fold_length=fold_length)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceReflect.__name__  # type: ignore


def test_sequence_reflect_fold_len_none_none() -> None:
    led_count = None
    colors = PixelSequence.get_monthly_color_sequence()
    fold_length = None
    sequence = SequenceReflect(led_count=led_count, pixel_sequence=colors, fold_length=fold_length)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceReflect.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_random(led_count: int | None) -> None:
    sequence = SequenceRandom(led_count=led_count)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRandom.__name__  # type: ignore


def test_sequence_random_list() -> None:
    pixel_sequence = PixelSequence.get_monthly_color_sequence().list
    led_count = len(pixel_sequence)
    sequence = SequenceRandom(led_count=led_count, pixel_sequence=pixel_sequence)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceRandom.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_pseudorandom(led_count: int | None) -> None:
    sequence = SequencePseudoRandom(led_count=led_count)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequencePseudoRandom.__name__  # type: ignore


def test_sequence_pseudorandom_list() -> None:
    led_count = None
    pixel_sequence = PixelSequence.get_monthly_color_sequence().list
    sequence = SequencePseudoRandom(led_count=led_count, pixel_sequence=pixel_sequence)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequencePseudoRandom.__name__  # type: ignore


def test_sequence_pseudorandom_list_empty() -> None:
    led_count = None
    pixel_sequence: list[Pixel] = []
    sequence = SequencePseudoRandom(led_count=led_count, pixel_sequence=pixel_sequence)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequencePseudoRandom.__name__  # type: ignore


@pytest.mark.parametrize(
    "led_count",
    RANGE_100,
    ids=[f"led_count: {i}" for i in RANGE_100],
)
def test_sequence_stretch(led_count: int | None) -> None:
    for j in range(1, led_count if led_count is not None else 0 + 1):
        colors = [Pixel(PixelColor.get_RANDOM()) for _ in range(int(led_count if led_count is not None else 0 / j))]
        sequence = SequenceStretch(led_count=led_count, pixel_sequence=colors)
        assert sequence is not None
        assert len(sequence.array.shape) == TWO
        assert sequence.array.shape[0] == led_count
        assert sequence.array.shape[1] == THREE
        assert sequence._name == SequenceStretch.__name__  # type: ignore


def test_sequence_stretch_none() -> None:
    led_count = None
    sequence = SequenceStretch(led_count=led_count, pixel_sequence=None)
    if led_count is None:
        led_count = PixelSequence.get_monthly_color_sequence().led_count
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceStretch.__name__  # type: ignore


def test_sequence_stretch_odd() -> None:
    led_count = 7
    sequence = SequenceStretch(led_count=led_count, pixel_sequence=None)
    assert sequence is not None
    assert len(sequence.array.shape) == TWO
    assert sequence.array.shape[0] == led_count
    assert sequence.array.shape[1] == THREE
    assert sequence._name == SequenceStretch.__name__  # type: ignore


def test_sequence_set_led_index() -> None:
    led_count = 7
    sequence = SequenceStretch(led_count=led_count, pixel_sequence=None)
    assert sequence.led_index == 0
    sequence.led_index = 2
    assert sequence.led_index == 2


def test_sequence_set_pixel() -> None:
    led_count = 7
    color = Pixel(PixelColor.RED)
    sequence = SequenceSolid(led_count=led_count, color=color)
    assert sequence.pixel == color
    new_color = Pixel(PixelColor.BLUE)
    sequence.pixel = new_color
    assert sequence.pixel == new_color


def test_sequence_set_pixel_next() -> None:
    led_count = 7
    color = Pixel(PixelColor.RED)
    sequence = SequenceSolid(led_count=led_count, color=color)
    assert sequence.pixel_next == color
    new_color = Pixel(PixelColor.BLUE)
    sequence.pixel_next = new_color
    assert sequence.pixel_next == new_color


def test_sequence_count() -> None:
    led_count = 8
    color1 = Pixel(PixelColor.RED)
    color2 = Pixel(PixelColor.BLUE)
    sequence = SequenceSolid(led_count=led_count, color=color1)
    assert sequence.count(color1) == led_count
    sequence = SequenceStretch(led_count=led_count, pixel_sequence=[color1, color2])
    assert sequence.count(color1) == 4
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=[color1, color2], wrap=False)
    assert sequence.count(color1) == 1


def test_sequence_random_index() -> None:
    led_count = 8
    sequence = SequenceSolid(led_count=led_count)
    idxs = [sequence.random_index() for _ in range(5)]
    assert not all(idx == idxs[0] for idx in idxs)


def test_sequence_copy() -> None:
    led_count = 8
    color1 = Pixel(PixelColor.RED)
    color2 = Pixel(PixelColor.BLUE)
    sequence1 = SequenceTransition(led_count=led_count, pixel_sequence=[color1, color2])
    sequence2 = sequence1.copy()
    assert all(sequence1[i] == sequence2[i] for i in range(len(sequence1)))


def test_sequence_advance_index() -> None:
    led_count = 7
    color1 = Pixel(PixelColor.RED)
    color2 = Pixel(PixelColor.BLUE)
    sequence = SequenceTransition(led_count=led_count, pixel_sequence=[color1, color2])
    assert sequence.pixel == color1
    assert sequence[sequence.led_index] == color1
    assert sequence[sequence.index_next] != color1
    sequence.advance_index(keep_current=True)
    assert sequence.pixel == color1
    assert sequence[sequence.led_index] != color1
    assert sequence[sequence.index_next] != color1


def test_sequence_str() -> None:
    color1 = Pixel(PixelColor.RED)
    color2 = Pixel(PixelColor.GREEN)
    color3 = Pixel(PixelColor.BLUE)
    sequence = PixelSequence(pixel_sequence=[color1, color2, color3])
    str_val = "Pixel: SQX#3[PX#FF0000:GRB, PX#00FF00:GRB, PX#0000FF:GRB]"
    assert str(sequence) == str_val
    sequence = SequenceSolid(led_count=100, color=color1)
    str_val = "Solid: SQX#100[PX#FF0000:GRB, PX#FF0000:GRB, PX#FF0000:GRB, ...]"
    assert str(sequence) == str_val


def test_sequence_repr() -> None:
    color1 = Pixel(PixelColor.RED)
    color2 = Pixel(PixelColor.GREEN)
    color3 = Pixel(PixelColor.BLUE)
    sequence = PixelSequence(pixel_sequence=[color1, color2, color3])
    str_val = "Pixel: SQX#3[PX#FF0000:GRB, PX#00FF00:GRB, PX#0000FF:GRB]"
    assert repr(sequence) == str_val


def test_sequence_monthly() -> None:
    sequence = PixelSequence.get_monthly_color_sequence(12)
    assert sequence[0] == Pixel(PixelColor.RED)
    assert sequence[1] == Pixel(PixelColor.WHITE)
    assert sequence[2] == Pixel(PixelColor.GREEN)
