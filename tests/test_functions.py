from lightberries.array_functions import (
    ArrayFunction,
    LEDFadeType,
    RaindropStates,
    SpriteState,
    ThingColors,
    ThingMoves,
    ThingSizes,
)
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


def newControllerBigger() -> ArrayController:
    return ArrayController(
        ledCount=6,
        simulate=True,
    )


def assert_func(func: ArrayFunction):
    assert func is not None
    assert isinstance(func, ArrayFunction)


def test_creation_simple():
    control = newController()
    function = ArrayFunction(control, assert_func)
    control.functionList.append(function)
    assert function is not None
    assert isinstance(function, ArrayFunction)


def test_creation_with_colors():
    control = newController()
    pattern = ArrayPattern.DefaultColorSequenceByMonth()
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert function is not None
    assert isinstance(function, ArrayFunction)


def test_str():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert str(function) == '[0]: "assert_func" PX #FF0000'


def test_repr():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert repr(function) == '<ArrayFunction> [0]: "assert_func" PX #FF0000'


def test_run():
    control = newController()
    function = ArrayFunction(control, assert_func)
    control.functionList.append(function)
    control._runFunctions()
    function.run()


def test_colorSequenceCount():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    function = ArrayFunction(newController(), assert_func, pattern)
    control.functionList.append(function)
    assert function.colorSequenceCount == len(pattern)


def test_colorSequenceIndex():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    assert function.colorSequenceIndex == 0


def test_colorSequenceNext():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    function = ArrayFunction(control, assert_func, pattern)
    control.functionList.append(function)
    left = function.color
    right = PixelColors.RED.array
    assert_array_equal(left, right)
    left = function.colorSequenceNext
    right = PixelColors.GREEN.array
    assert_array_equal(left, right)
    left = function.colorSequenceNext
    right = PixelColors.BLUE.array
    assert_array_equal(left, right)
    left = function.colorSequenceNext
    right = PixelColors.RED.array
    assert_array_equal(left, right)


# def test_colorSequenceNext_rollover():
#     control = newController()
#     pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
#     function = ArrayFunction(control, assert_func, pattern)
#     control.functionList.append(function)
#     function.colorSequenceNext
#     function.colorSequenceNext
#     function.colorSequenceNext
#     left = function.colorSequenceNext
#     right = PixelColors.RED.array
#     assert_array_equal(left, right)


def test_doFade():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function = ArrayFunction(control, ArrayFunction.doFade, pattern)
    control.functionList.append(function)
    delay_count = 2
    function.delayCountMax = delay_count
    function.fadeAmount = 1.0
    assert_array_equal(function.color, PixelColors.RED.array)
    assert function.delayCounter == 0
    control._runFunctions()
    assert function.delayCounter == 1
    control._runFunctions()
    assert function.delayCounter == 0
    assert_array_equal(function.color, PixelColors.OFF.array)
    function.colorNext = PixelColors.PINK.array
    control._runFunctions()
    assert function.delayCounter == 1
    control._runFunctions()
    assert function.delayCounter == 0
    assert_array_equal(function.color, PixelColors.PINK.array)
    function.colorNext = PixelColors.GREEN.array
    control._runFunctions()
    assert function.delayCounter == 1
    control._runFunctions()
    assert function.delayCounter == 0
    assert_array_equal(function.color, PixelColors.GREEN.array)


def test_updateArrayIndex_singlestep():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    control.functionList.append(function)
    assert function.index == 0
    assert function.step == 1
    assert function.direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        control._runFunctions()
        assert function.index == (i + 1) % ArrayFunction.Controller.realLEDCount
        assert function.step == 1
        assert function.direction == 1
        assert_array_equal(function.indexRange, np.array([(i + 1) % ArrayFunction.Controller.realLEDCount]))
    assert function.index == 0
    assert function.step == 1
    assert function.direction == 1


def test_updateArrayIndex_largestep():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    control.functionList.append(function)
    function.step = 2
    assert function.index == 0
    assert function.step == 2
    assert function.direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        control._runFunctions()
        begin_idx = function.indexPrevious + 1
        idx = begin_idx + (function.step - 1)
        assert function.index == idx % ArrayFunction.Controller.realLEDCount
        assert function.step == 2
        assert function.direction == 1
        assert_array_equal(
            function.indexRange,
            np.array([j % ArrayFunction.Controller.realLEDCount for j in range(begin_idx, idx + 1)]),
        )
    assert function.index == 0
    assert function.step == 2
    assert function.direction == 1


def test_functionCollisionDetection_only_one():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function = ArrayFunction(control, ArrayFunction.functionCollisionDetection, pattern)
    control.functionList.append(function)
    function.step = 1
    assert function.index == 0
    assert function.step == 1
    assert function.direction == 1
    for i in range(ArrayFunction.Controller.realLEDCount):
        control._runFunctions()
    assert function.index == 0
    assert function.step == 1
    assert function.direction == 1
    assert function.collision is False


def test_functionCollisionDetection_small_step():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function1 = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    function2 = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    function3 = ArrayFunction(control, ArrayFunction.functionCollisionDetection, pattern)
    control.functionList.append(function1)
    control.functionList.append(function2)
    control.functionList.append(function3)
    function2.index = control.realLEDCount - 1
    function2.direction = -1
    assert function1.index == 0
    assert function1.step == 1
    assert function1.direction == 1
    control._runFunctions()
    assert function1.index == 1
    assert function1.indexRange == [1]
    assert function1.step == 1
    assert function1.direction == 1
    assert function1.collision is False


def test_functionCollisionDetection_large_step():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function1 = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    function2 = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    function3 = ArrayFunction(control, ArrayFunction.functionCollisionDetection, pattern)
    function3.explode = True
    control.functionList.append(function1)
    control.functionList.append(function2)
    control.functionList.append(function3)
    function1.step = 2
    function1.collisionEnabled = True
    function2.step = 2
    function2.collisionEnabled = True
    function2.index = control.realLEDCount - 1
    function2.direction = -1
    assert function1.index == 0
    assert function1.step == 2
    assert function1.direction == 1
    assert function2.index == 2
    assert function2.step == 2
    assert function2.direction == -1
    control._runFunctions()
    assert function1.index == 0
    assert 1 in function1.indexRange and 2 in function1.indexRange
    assert 1 in function1.collisionIntersection
    assert function1.step == 2
    assert function1.direction == -1
    assert function1.collision is True
    assert function1.collisionWith == function2
    assert function2.index == 2
    assert 1 in function2.indexRange and 0 in function2.indexRange
    assert 1 in function2.collisionIntersection
    assert function2.step == 2
    assert function2.direction == 1
    assert function1.collision is True
    assert function2.collisionWith == function1


def test_functionCollisionDetection_slow_fast():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    function1 = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    function2 = ArrayFunction(control, ArrayFunction.updateArrayIndex, pattern)
    function3 = ArrayFunction(control, ArrayFunction.functionCollisionDetection, pattern)
    function3.explode = True
    control.functionList.append(function1)
    control.functionList.append(function2)
    control.functionList.append(function3)
    function1.step = 3
    function1.collisionEnabled = True
    function2.collisionEnabled = True
    function2.index = 1
    assert function1.index == 0
    assert function1.step == 3
    assert function1.direction == 1
    assert function2.index == 1
    assert function2.step == 1
    assert function2.direction == 1
    control._runFunctions()
    assert function1.index == 2
    assert 2 in function1.indexRange
    assert 2 in function1.collisionIntersection
    assert function1.step == 1
    assert function1.direction == 1
    assert function1.collision is True
    assert function1.collisionWith == function2
    assert function2.index == 1
    assert 2 in function2.indexRange
    assert 2 in function2.collisionIntersection
    assert function2.step == 3
    assert function2.direction == 1
    assert function1.collision is True
    assert function2.collisionWith == function1
    control._runFunctions()
    assert function1.collision is True
    assert function1.collisionWith == function2
    assert function1.collision is True
    assert function2.collisionWith == function1


def test_functionOff():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.PINK])
    off = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    control.setvirtualLEDBuffer(pattern)
    function1 = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, pattern)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, off)


def test_functionFadeOff():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    half = ConvertPixelArrayToNumpyArray([PixelColors.RED2, PixelColors.GREEN2, PixelColors.BLUE2])
    quarter = ConvertPixelArrayToNumpyArray([PixelColors.RED3, PixelColors.GREEN3, PixelColors.BLUE3])
    eighth = ConvertPixelArrayToNumpyArray([PixelColors.RED4, PixelColors.GREEN4, PixelColors.BLUE4])
    control.setvirtualLEDBuffer(pattern)
    function1 = ArrayFunction(control, ArrayFunction.functionFadeOff, pattern)
    function1.fadeAmount = 0.5
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert function1.fadeAmount == 0.5
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, half)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, quarter)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, eighth)


def test_functionSolidColorCycle():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    one = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.RED, PixelColors.RED])
    three = ConvertPixelArrayToNumpyArray([PixelColors.GREEN, PixelColors.GREEN, PixelColors.GREEN])
    four = ConvertPixelArrayToNumpyArray([PixelColors.BLUE, PixelColors.BLUE, PixelColors.BLUE])
    function1 = ArrayFunction(control, ArrayFunction.functionSolidColorCycle, pattern)
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, four)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionFade():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    one = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.RED2, PixelColors.RED2, PixelColors.RED2]) + [1, 0, 0]
    three = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.RED, PixelColors.RED]) + [1, 0, 0]
    three -= [1, 0, 0]
    function1 = ArrayFunction(control, ArrayFunction.functionFade, pattern)
    function1.fadeAmount = 0.5
    control.functionList.append(function1)
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    function1.color = PixelColors.OFF.array
    control.virtualLEDBuffer += [1, 0, 0]
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)


def test_functionMarquee():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED])
    one = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.RED, PixelColors.OFF])
    three = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.RED])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionMarquee, pattern)
    control.functionList.append(function)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionCylon():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED])
    one = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.RED, PixelColors.OFF])
    three = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.RED])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionCylon, pattern)
    control.functionList.append(function)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionMerge():
    control = newControllerBigger()
    pattern = ConvertPixelArrayToNumpyArray(
        [PixelColors.RED, PixelColors.OFF, PixelColors.OFF, PixelColors.OFF, PixelColors.OFF, PixelColors.RED]
    )
    one = np.array([0, 1, 2, 3, 4, 5])
    two = np.array([2, 0, 1, 1, 0, 2])
    three = np.array([1, 2, 0, 0, 2, 1])
    four = np.array([0, 1, 2, 2, 1, 0])
    function = ArrayFunction(control, ArrayFunction.functionMerge, pattern)
    function.size = 3
    control.functionList.append(function)
    control.setvirtualLEDBuffer(pattern)
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, pattern)
    assert_array_equal(control.virtualLEDIndexBuffer, four)


def test_functionAccelerate():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    one = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.RED, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.RED])
    three = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.RED, PixelColors.RED])
    four = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.RED, PixelColors.RED])
    five = ConvertPixelArrayToNumpyArray([PixelColors.GREEN, PixelColors.GREEN, PixelColors.GREEN])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionAccelerate, pattern)
    function.stateMax = 5
    control.functionList.append(function)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, four)
    function.colorCycle = True
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, five)
    control._runFunctions()


def test_functionRandomChange():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    off = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    function = ArrayFunction(control, ArrayFunction.functionRandomChange, pattern)
    function.colorNext = function.color
    function.fadeAmount = 1
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, off)
    control._runFunctions()
    control._runFunctions()
    control._runFunctions()
    control._runFunctions()
    while not np.array_equal(function.colorNext, control.backgroundColor):
        control._runFunctions()
    control._runFunctions()
    function.fadeType = LEDFadeType.INSTANT_OFF
    control._runFunctions()


def test_functionMeteors():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    initial = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    one = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.RED, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.RED])
    three = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.OFF])
    four = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.GREEN, PixelColors.OFF])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionMeteors, pattern)
    function.fadeAmount = 1
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, three)
    function.colorCycle = True
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, four)


def test_functionSprites():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    initial = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionSprites, pattern)
    function.fadeAmount = 1.0
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    while function.state == SpriteState.OFF.value:
        control._runFunctions()
    control._runFunctions()


def test_functionRaindrops():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    initial = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    one = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.RED, PixelColors.OFF])
    two = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.OFF, PixelColors.RED])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionRaindrops, pattern)
    function.fadeAmount = 1.0
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    control._runFunctions()
    while function.index != 1:
        control._runFunctions()
    # assert_array_equal(control.virtualLEDBuffer, one)
    while function.state == RaindropStates.OFF.value:
        control._runFunctions()
    function.stepCountMax = 2
    function.color = PixelColors.RED.array
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, one)
    control._runFunctions()
    assert_array_equal(control.virtualLEDBuffer, two)


def test_functionAlive():
    control = newController()
    pattern = ConvertPixelArrayToNumpyArray([PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE])
    initial = ConvertPixelArrayToNumpyArray([PixelColors.OFF, PixelColors.OFF, PixelColors.OFF])
    off = ArrayFunction(control, ArrayFunction.functionOff, pattern)
    control.functionList.append(off)
    function = ArrayFunction(control, ArrayFunction.functionAlive, pattern)
    function.fadeAmount = 1.0
    control.functionList.append(function)
    assert_array_equal(control.virtualLEDBuffer, initial)
    control._runFunctions()
    while not function.state & ThingMoves.METEOR.value:
        control._runFunctions()
    while not function.state & ThingMoves.LIGHTSPEED.value:
        control._runFunctions()
    while not function.state & ThingMoves.TURTLE.value:
        control._runFunctions()
    while not function.state & ThingSizes.GROW.value:
        control._runFunctions()
    while not function.state & ThingSizes.SHRINK.value:
        control._runFunctions()
    while not function.state & ThingColors.CYCLE.value:
        control._runFunctions()
    control._runFunctions()
