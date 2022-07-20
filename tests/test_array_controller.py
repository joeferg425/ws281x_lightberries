from __future__ import annotations
from typing import Any
from lightberries.array_controller import ArrayController
import numpy as np
from lightberries.pixel import PixelColors
from lightberries.array_patterns import ConvertPixelArrayToNumpyArray
from lightberries.ws281x_strings import WS281xString
import mock
from lightberries.exceptions import WS281xStringException
import lightberries.rpiws281x_patch
from numpy.typing import NDArray


def new_instantiate_pixelstrip(
    self,
    pwmGPIOpin: int,
    channelDMA: int,
    ledCount: int,
    frequencyPWM: int,
    channelPWM: int,
    invertSignalPWM: bool,
    gamma: float,
    stripTypeLED: Any,
    ledBrightnessFloat: Any,
    testing: bool,
    matrixShape: tuple[int, int] = None,
    matrixLayout: NDArray[np.int32] | None = None,
) -> None:
    try:
        # create ws281x pixel strip
        self.ws281xPixelStrip = lightberries.rpiws281x_patch.PixelStrip(
            pin=pwmGPIOpin,
            dma=channelDMA,
            num=ledCount,
            freq_hz=frequencyPWM,
            channel=channelPWM,
            invert=invertSignalPWM,
            gamma=gamma,
            strip_type=stripTypeLED,
            brightness=int(255 * ledBrightnessFloat),
            matrixLayout=matrixLayout,
            matrixShape=matrixShape,
            testing=testing,
        )
    except SystemExit:  # pragma: no cover
        raise
    except KeyboardInterrupt:  # pragma: no cover
        raise
    except Exception as ex:  # pragma: no cover
        raise WS281xStringException from ex


def new_instantiate_WS281xString(
    self,
    ledCount: int,
    pwmGPIOpin: int,
    channelDMA: int,
    frequencyPWM: int,
    invertSignalPWM: bool,
    ledBrightnessFloat: float,
    channelPWM: int,
    stripTypeLED: Any,
    gamma: Any,
    simulate: bool,
    testing: bool = False,
    matrixShape: tuple[int, int] = None,
    matrixLayout: NDArray[np.int32] | None = None,
) -> None:
    with mock.patch.object(WS281xString, "_instantiate_pixelstrip", new=new_instantiate_pixelstrip):
        self.ws281xString = WS281xString(
            ledCount=ledCount,
            pwmGPIOpin=pwmGPIOpin,
            channelDMA=channelDMA,
            frequencyPWM=frequencyPWM,
            invertSignalPWM=invertSignalPWM,
            ledBrightnessFloat=ledBrightnessFloat,
            channelPWM=channelPWM,
            stripTypeLED=stripTypeLED,
            gamma=gamma,
            simulate=simulate,
            testing=testing,
            matrixLayout=matrixLayout,
            matrixShape=matrixShape,
        )


def newController() -> ArrayController:
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        return ArrayController(testing=True)


def test_create():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert ac is not None
        assert isinstance(ac.ws281xString, WS281xString)


def test_properties():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
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
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert isinstance(ac.ws281xString, WS281xString)
        ac.__del__()
        assert ac.ws281xString is None


def test_reset():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        ac.setvirtualLEDBuffer(ConvertPixelArrayToNumpyArray([PixelColors.OFF]))
        ac.reset()
        assert len(ac.virtualLEDBuffer) == ac.realLEDCount


def test_refresh_callback():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        ac.refreshCallback = print
        ac.refreshLEDs()


def test_getRandomIndices():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        for i in range(3):
            temp = ac.getRandomIndices(i)
            assert len(temp) == i
            for x in temp:
                assert isinstance(x, np.int32)


def test_getRandomBoolean():
    with mock.patch.object(ArrayController, "_instantiate_WS281xString", new_instantiate_WS281xString):
        ac = ArrayController(testing=True)
        assert isinstance(ac.getRandomBoolean(), bool)
