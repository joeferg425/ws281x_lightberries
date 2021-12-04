from typing import Callable, Any
import numpy as np
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray
from nptyping import NDArray


class LightData:
    def __init__(self, funcName: str, funcPointer: Callable, colors: NDArray[(3, Any), np.int32]):
        self.funcName: str = funcName
        self.runFunction: Callable = funcPointer
        self.index: int = 0
        self.lastindex: int = 0
        self.step: int = 0
        self.oldStep: int = 0
        self.stepCounter: int = 0
        self.stepCountMax: int = 0
        self.previousIndex: int = 0
        self.moveRange: int = 0
        self.bounce: bool = False
        self.delayCounter: int = 0
        self.delayCountMax: int = 0
        self.active: bool = True
        self.dying: bool = False
        self.activeChance: float = 100.0
        self.duration: int = 0
        self.direction: int = 0
        self.colorSequenceIndex: int = 0
        self.size: int = 0
        self.sizeMin: int = 0
        self.sizeMax: int = 0
        self.fadeAmount: float = 0
        self.colorIndex: int = 0
        self.colorScaler: float = 0
        self.color: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorNext: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorFade: int = 1
        self.random: float = 0.5
        self.flipLength: int = 0
        self.state: int = 0
        self.stateMax: int = 0
        self.colors: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([PixelColors.OFF])
        if hasattr(colors, "__len__") and hasattr(colors, "shape") and len(colors.shape) > 1:
            self.color = None
            self.colors = ConvertPixelArrayToNumpyArray(colors)
        else:
            self.color = Pixel(colors).array
            self.colors = np.array([Pixel(colors).tuple])

    def __str__(self) -> str:
        return '[{}]: "{}" {}'.format(self.index, self.funcName, Pixel(self.color))

    def __repr__(self) -> str:
        return "<{}> {}".format(self.__class__.__name__, str(self))
