from typing import Callable, Any, Optional
import numpy as np
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray
from nptyping import NDArray
import logging

LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    streamHandler = logging.StreamHandler()
    LOGGER.addHandler(streamHandler)
LOGGER.setLevel(logging.INFO)


class LightData:
    def __init__(self, funcName: str, funcPointer: Callable):
        self.__colorSequence: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([])
        self.__colorSequenceCount: int = 0
        self.__colorSequenceIndex: int = 0

        self.funcName: str = funcName
        self.runFunction: Callable = funcPointer

        self.index: int = 0
        self.indexPrevious: int = 0
        self.indexUpdated: bool = False

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
        # self.colors: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([PixelColors.OFF])
        self.colorBegin: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorNext: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorGoal: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorSequenceIndex: int = 0
        # self.colorIndex: int = 0
        self.colorScaler: float = 0
        self.colorFade: int = 1
        self.colorCycle: bool = False
        self.explode: bool = False

        self.state: int = 0
        self.stateMax: int = 0

        self.bounce: bool = False
        self.collideWith: Optional[LightData] = None
        self.collideIntersect: int = 0
        self.indexRange: Optional[NDArray[(3, Any), np, np.int32]] = None
        self.dying: bool = False
        self.waking: bool = False
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

    @property
    def colorSequence(self) -> NDArray[(3, Any), np.int32]:
        return self.__colorSequence

    @colorSequence.setter
    def colorSequence(self, colorSequence: NDArray[(3, Any), np.int32]):
        self.__colorSequence = np.copy(ConvertPixelArrayToNumpyArray(colorSequence))
        self.colorSequenceCount = len(self.__colorSequence)
        self.colorSequenceIndex = 0

    @property
    def colorSequenceCount(self) -> int:
        return self.__colorSequenceCount

    @colorSequenceCount.setter
    def colorSequenceCount(self, colorSequenceCount: int):
        self.__colorSequenceCount = colorSequenceCount

    @property
    def colorSequenceIndex(self) -> int:
        return self.__colorSequenceIndex

    @colorSequenceIndex.setter
    def colorSequenceIndex(self, colorSequenceIndex: int):
        self.__colorSequenceIndex = colorSequenceIndex

    @property
    def colorSequenceNext(self) -> NDArray[(3,), np.int32]:
        if not callable(self.colorSequence):
            temp = self.colorSequence[self.colorSequenceIndex]
            self.colorSequenceIndex += 1
            if self.colorSequenceIndex >= self.colorSequenceCount:
                self.colorSequenceIndex = 0
        else:
            temp = self.colorSequence()
        if isinstance(temp, Pixel):
            return temp.array
        else:
            return temp

    def doFade(self) -> None:
        """
        fade pixel colors
        """
        try:
            if self.delayCounter >= self.delayCountMax:
                self.delayCounter = 0
                for rgbIndex in range(len(self.color)):
                    if self.color[rgbIndex] != self.colorNext[rgbIndex]:
                        if self.color[rgbIndex] - self.colorFade > self.colorNext[rgbIndex]:
                            self.color[rgbIndex] -= self.colorFade
                        elif self.color[rgbIndex] + self.colorFade < self.colorNext[rgbIndex]:
                            self.color[rgbIndex] += self.colorFade
                        else:
                            self.color[rgbIndex] = self.colorNext[rgbIndex]
            self.delayCounter += 1
            # self._VirtualLEDArray[self.index] = np.copy(self.color)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                self.__class__.__name__,
                self.doFade.__name__,
                ex,
            )
            raise

    def doMove(self, ledCount: int):
        self.indexPrevious = self.index
        newIndex_nomodulo = self.index + (self.step * self.direction)
        self.index = (self.index + (self.step * self.direction)) % (ledCount - 1)
        self.indexRange = np.array(
            list(
                range(
                    self.indexPrevious,
                    newIndex_nomodulo,
                    self.direction,
                )
            )
        )
        modulo = np.where(self.indexRange >= (ledCount - 1))
        self.indexRange[modulo] -= ledCount
        modulo = np.where(self.indexRange < 0)
        self.indexRange[modulo] += ledCount
        self.index = self.indexRange[-1]
        self.indexUpdated = True

    def calcRange(self, indexFrom: int, indexTo: int, ledCount: int) -> NDArray[(Any,), np.int32]:
        if indexTo >= indexFrom:
            direction = 1
        else:
            direction = -1
        rng = np.arange(
            start=indexFrom,
            stop=indexTo,
            step=direction,
            dtype=np.int32
            # )
            # )
        )
        modulo = np.where(rng >= (ledCount - 1))
        rng[modulo] -= ledCount
        modulo = np.where(rng < 0)
        rng[modulo] += ledCount
        return rng
