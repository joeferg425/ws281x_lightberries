import pytest
from lightberries.array_functions import ArrayFunction
from lightberries.array_patterns import ArrayPattern, ConvertPixelArrayToNumpyArray
from lightberries.pixel import PixelColors
from numpy.testing import assert_array_equal
from lightberries.array_controller import ArrayController

import numpy as np


def newController() -> ArrayController:
    return ArrayController(
        ledCount=3,
        simulate=True,
    )


def assert_func(func: ArrayFunction):
    assert func is not None
    assert isinstance(func, ArrayFunction)


def test_creation_simple():
    a = ArrayFunction(newController(), assert_func)
    assert a is not None
    assert isinstance(a, ArrayFunction)


def test_creation_with_colors():
    p = ArrayPattern.DefaultColorSequenceByMonth()
    a = ArrayFunction(newController(), assert_func, p)
    assert a is not None
    assert isinstance(a, ArrayFunction)


def test_str():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    a = ArrayFunction(newController(), assert_func, p)
    assert str(a) == '[0]: "assert_func" PX #FF0000'


def test_repr():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    a = ArrayFunction(newController(), assert_func, p)
    assert repr(a) == '<ArrayFunction> [0]: "assert_func" PX #FF0000'


def test_run():
    a = ArrayFunction(newController(), assert_func)
    a.run()


def test_colorSequenceCount():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    a = ArrayFunction(newController(), assert_func, p)
    assert a.colorSequenceCount == len(p)


def test_colorSequenceIndex():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    a = ArrayFunction(newController(), assert_func, p)
    assert a.colorSequenceIndex == 0


def test_colorSequenceNext():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    a = ArrayFunction(newController(), assert_func, p)
    left = a.colorSequenceNext
    right = PixelColors.RED
    assert_array_equal(left, right)


def test_colorSequenceNext_rollover():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    a = ArrayFunction(newController(), assert_func, p)
    a.colorSequenceNext
    a.colorSequenceNext
    a.colorSequenceNext
    left = a.colorSequenceNext
    right = PixelColors.RED
    assert_array_equal(left, right)


def test_doFade():
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    a = ArrayFunction(newController(), ArrayFunction.doFade, p)
    delay_count = 2
    a.delayCountMax = delay_count
    a.colorFade = 255
    assert_array_equal(a.color, PixelColors.RED)
    assert a.delayCounter == 0
    a.run()
    assert a.delayCounter == 1
    a.run()
    assert a.delayCounter == 0
    assert_array_equal(a.color, PixelColors.OFF)
    a.colorNext = PixelColors.PINK
    a.run()
    assert a.delayCounter == 1
    a.run()
    assert a.delayCounter == 0
    assert_array_equal(a.color, PixelColors.PINK)
    a.colorNext = PixelColors.GREEN
    a.run()
    assert a.delayCounter == 1
    a.run()
    assert a.delayCounter == 0
    assert_array_equal(a.color, PixelColors.GREEN)


def test_updateArrayIndex_singlestep():
    controller = newController()
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    a = ArrayFunction(controller, ArrayFunction.updateArrayIndex, p)
    assert a.index == 0
    assert a.step == 1
    assert a.direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        a.run()
        assert a.index == (i + 1) % ArrayFunction.Controller.realLEDCount
        assert a.step == 1
        assert a.direction == 1
        assert_array_equal(a.indexRange, np.array([(i + 1) % ArrayFunction.Controller.realLEDCount]))
    assert a.index == 0
    assert a.step == 1
    assert a.direction == 1


def test_updateArrayIndex_largestep():
    controller = newController()
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    a = ArrayFunction(controller, ArrayFunction.updateArrayIndex, p)
    a.step = 2
    assert a.index == 0
    assert a.step == 2
    assert a.direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        a.run()
        begin_idx = a.indexPrevious + 1
        idx = begin_idx + (a.step - 1)
        assert a.index == idx % ArrayFunction.Controller.realLEDCount
        assert a.step == 2
        assert a.direction == 1
        assert_array_equal(
            a.indexRange, np.array([j % ArrayFunction.Controller.realLEDCount for j in range(begin_idx, idx + 1)])
        )
    assert a.index == 0
    assert a.step == 2
    assert a.direction == 1


def test_functionCollisionDetection_only_one():
    controller = newController()
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    a = ArrayFunction(controller, ArrayFunction.functionCollisionDetection, p)
    a.step = 1
    assert a.index == 0
    assert a.step == 1
    assert a.direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        a.run()
    assert a.index == 0
    assert a.step == 1
    assert a.direction == 1
    assert a.collision is False


def test_functionCollisionDetection_small_step():
    controller = newController()
    p = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    a1 = ArrayFunction(controller, ArrayFunction.updateArrayIndex, p)
    a2 = ArrayFunction(controller, ArrayFunction.updateArrayIndex, p)
    a3 = ArrayFunction(controller, ArrayFunction.functionCollisionDetection, p)
    a2.index = controller.realLEDCount - 1
    a2.direction = -1
    assert a1.index == 0
    assert a1.step == 1
    assert a1.direction == 1
    a1.run()
    a2.run()
    a3.run()
    assert a1.index == 0
    assert a1.step == 1
    assert a1.direction == 1
    assert a1.collision is False
