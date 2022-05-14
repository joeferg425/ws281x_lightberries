from lightberries.array_controller import ArrayController
import numpy as np
from typing import Any, Callable
from lightberries.pixel import PixelColors
from lightberries.array_patterns import ConvertPixelArrayToNumpyArray
from lightberries.ws281x_strings import WS281xString


def test_create():
    ac = ArrayController(debug=True, verbose=True)
    assert ac is not None
    assert isinstance(ac.ws281xString, WS281xString)


def test_properties():
    ac = ArrayController(debug=True, verbose=True)
    assert isinstance(ac.refreshDelay, float)
    ac.refreshDelay = 0.1
    assert isinstance(ac.backgroundColor, np.ndarray)
    ac.backgroundColor = PixelColors.OFF.array
    assert isinstance(ac.secondsPerMode, float)
    ac.secondsPerMode = 1.0
    assert isinstance(ac.colorSequence, np.ndarray)
    ac.colorSequence = ConvertPixelArrayToNumpyArray([PixelColors.OFF])
    assert isinstance(ac.colorSequenceCount, int)
    ac.colorSequenceCount = 1
    assert isinstance(ac.colorSequenceIndex, int)
    ac.colorSequenceIndex = 1
    assert isinstance(ac.colorSequenceNext, np.ndarray)
    assert isinstance(ac.getFunctionMethodsList(), list)
    for f in ac.getFunctionMethodsList():
        assert isinstance(f, str)
    assert isinstance(ac.getColorMethodsList(), list)
    for f in ac.getColorMethodsList():
        assert isinstance(f, str)


def test_delete():
    ac = ArrayController(debug=True, verbose=True)
    assert isinstance(ac.ws281xString, WS281xString)
    ac.__del__()
    assert ac.ws281xString is None


def test_reset():
    ac = ArrayController(debug=True, verbose=True)
    ac.setvirtualLEDBuffer(ConvertPixelArrayToNumpyArray([PixelColors.OFF]))
    ac.reset()
    assert len(ac.virtualLEDBuffer) == ac.realLEDCount


def test_refresh_callback():
    ac = ArrayController(debug=True, verbose=True)
    ac.refreshCallback = print
    ac.refreshLEDs()


def test_getRandomIndices():
    ac = ArrayController(debug=True, verbose=True)
    for i in range(3):
        temp = ac.getRandomIndices(i)
        assert len(temp) == i
        for x in temp:
            assert isinstance(x, np.int32)


def test_getRandomBoolean():
    ac = ArrayController(debug=True, verbose=True)
    assert isinstance(ac.getRandomBoolean(), bool)
