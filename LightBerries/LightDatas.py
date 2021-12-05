from typing import Callable, Any, Optional
import numpy as np
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray
from nptyping import NDArray


class LightData:
    def __init__(self, funcName: str, funcPointer: Callable):
        self.funcName: str = funcName
        self.runFunction: Callable = funcPointer

        self.index: int = 0
        self.indexPrevious: int = 0

        self.step: int = 0
        self.stepLast: int = 0
        self.stepCounter: int = 0
        self.stepCountMax: int = 0
        self.stepSizeMax: int = 0

        self.size: int = 0
        self.sizeMin: int = 0
        self.sizeMax: int = 0

        self.delayCounter: int = 0
        self.delayCountMax: int = 0

        self.active: bool = True
        self.activeChance: float = 100.0

        self.color: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colors: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([PixelColors.OFF])
        self.colorNext: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorSequenceIndex: int = 0
        self.colorIndex: int = 0
        self.colorScaler: float = 0
        self.colorFade: int = 1
        self.colorCycle: bool = False
        self.explode: bool = False

        self.state: int = 0
        self.stateMax: int = 0

        self.bounce: bool = False
        self.collideWith: Optional[LightData] = None
        self.collideIntersect: int = 0
        self.moveRange: Optional[int] = None
        self.dying: bool = False
        self.duration: int = 0
        self.direction: int = 0
        self.fadeAmount: float = 0
        self.fadeSteps: int = 0
        self.random: float = 0.5
        self.flipLength: int = 0

    def __str__(self) -> str:
        return '[{}]: "{}" {}'.format(self.index, self.funcName, Pixel(self.color))

    def __repr__(self) -> str:
        return "<{}> {}".format(self.__class__.__name__, str(self))
