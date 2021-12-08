from typing import Callable, Any, Optional
import numpy as np
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray
import LightBerries
from nptyping import NDArray
import logging
import random
from enum import IntEnum

LOGGER = logging.getLogger("LightBerries")


class LightFunction:
    Controller: "LightBerries.LightControl.LightController"

    def __init__(self, funcPointer: Callable, colorSequence: NDArray[(3, Any), np.int32]):
        self.__colorSequence: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([])
        self.__colorSequenceCount: int = 0
        self.__colorSequenceIndex: int = 0

        self.colorSequence = colorSequence

        self.funcName: str = funcPointer.__name__
        self.runFunction: Callable = funcPointer

        self.index: int = 0
        self.indexPrevious: int = 0
        self.indexUpdated: bool = False

        self.step: int = 1
        self.stepLast: int = 0
        self.stepCounter: int = 0
        self.stepCountMax: int = 0
        self.stepSizeMax: int = 1

        self.size: int = 1
        self.sizeMin: int = 1
        self.sizeMax: int = 1

        self.delayCounter: int = 0
        self.delayCountMax: int = 0

        self.active: bool = True
        self.activeChance: float = 100.0

        self.color: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorBegin: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorNext: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorGoal: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorScaler: float = 0
        self.colorFade: int = 1
        self.colorCycle: bool = False

        self.state: int = 0
        self.stateMax: int = 0

        self.explode: bool = False
        self.fade: bool = False
        self.bounce: bool = False
        self.collideWith: Optional[LightFunction] = None
        self.collideIntersect: int = 0
        self.indexRange: Optional[NDArray[(3, Any), np, np.int32]] = None
        self.dying: bool = False
        self.waking: bool = False
        self.duration: int = 0
        self.direction: int = 1
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
        temp = self.colorSequence[self.colorSequenceIndex]
        self.colorSequenceIndex += 1
        if self.colorSequenceIndex >= self.colorSequenceCount:
            self.colorSequenceIndex = 0
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

    @staticmethod
    def functionCollisionDetection(
        collision: "LightFunction",
    ) -> None:
        try:
            foundBounce = False
            lightFunctions = LightFunction.Controller.lightFunctionList
            if len(lightFunctions) > 1:
                for index1, meteor1 in enumerate(lightFunctions):
                    if "function" in meteor1.runFunction.__name__:
                        if index1 + 1 < len(lightFunctions):
                            for index2, meteor2 in enumerate(lightFunctions[index1 + 1 :]):
                                if "function" in meteor2.runFunction.__name__:
                                    if isinstance(meteor1.indexRange, np.ndarray) and isinstance(
                                        meteor2.indexRange, np.ndarray
                                    ):
                                        # this detects the intersection of two self._LightDataObjects' movements across LEDs
                                        intersection = np.intersect1d(meteor1.indexRange, meteor2.indexRange)
                                        if len(intersection) > 0 and random.randint(0, 4) != 0:
                                            meteor1.bounce = True
                                            meteor1.collideWith = meteor2
                                            meteor1.stepLast = meteor1.step
                                            meteor1.collideIntersect = int(intersection[0])
                                            meteor2.bounce = True
                                            meteor2.collideWith = meteor1
                                            meteor2.stepLast = meteor2.step
                                            meteor2.collideIntersect = int(intersection[0])
                                            foundBounce = True
            explosion_indices = []
            explosion_colors = []
            if foundBounce == True:
                for index, meteor in enumerate(lightFunctions):
                    if "function" in meteor.runFunction.__name__:
                        if meteor.bounce is True:
                            if isinstance(meteor.collideWith, LightFunction):
                                othermeteor = meteor.collideWith
                                previous = int(meteor.step)
                                if (meteor.direction * othermeteor.direction) < 0:
                                    meteor.direction *= -1
                                    othermeteor.direction *= -1
                                else:
                                    temp = othermeteor.step
                                    othermeteor.step = meteor.step
                                    meteor.step = temp
                                meteor.index = (
                                    meteor.collideIntersect + (meteor.step * meteor.direction)
                                ) % LightFunction.Controller.virtualLEDCount
                                othermeteor.index = meteor.index
                                meteor.indexPrevious = meteor.collideIntersect
                                othermeteor.indexPrevious = othermeteor.collideIntersect
                                meteor.bounce = False
                                othermeteor.bounce = False
                                meteor.collideWith = None
                                othermeteor.collideWith = None
                                if collision.explode:
                                    if isinstance(meteor.indexRange, np.ndarray):
                                        middle = meteor.indexRange[len(meteor.indexRange) // 2]
                                    r = LightFunction.Controller.LEDCount // 20
                                    for i in range(r):
                                        explosion_indices.append(
                                            (middle - i) % LightFunction.Controller.virtualLEDCount,
                                        )
                                        explosion_colors.append(
                                            Pixel(PixelColors.YELLOW).array * (r - i) / r,
                                        )

                                        explosion_indices.append(
                                            (middle + i) % LightFunction.Controller.virtualLEDCount,
                                        )
                                        explosion_colors.append(
                                            Pixel(PixelColors.YELLOW).array * (r - i) / r,
                                        )
                                    LightFunction.Controller._VirtualLEDArray[explosion_indices] = np.array(
                                        explosion_colors
                                    )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                collision.__class__.__name__,
                collision.functionCollisionDetection.__name__,
                ex,
            )
            raise

    def functionFadeOff(
        fade: "LightFunction",
    ) -> None:
        """
        Fade all Pixels toward OFF
        """
        try:
            LightFunction.Controller._VirtualLEDArray[:] = LightFunction.Controller._VirtualLEDArray * (
                1 - fade.fadeAmount
            )
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                fade.__class__.__name__,
                fade.functionFadeOff.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionNone(
        nothing: "LightFunction",
    ) -> None:
        """
        do nothing
        """
        try:
            pass
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                nothing.__class__.__name__,
                nothing.functionNone.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionSolidColorCycle(
        cycle: "LightFunction",
    ) -> None:
        """
        set all pixels to the next color
        """
        try:
            cycle.delayCounter += 1
            if cycle.delayCounter >= cycle.delayCountMax:
                LightFunction.Controller._VirtualLEDArray *= 0
                LightFunction.Controller._VirtualLEDArray += cycle.colorSequenceNext
                cycle.delayCounter = 0
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                cycle.__class__.__name__,
                cycle.functionSolidColorCycle.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionMarquee(
        marquee: "LightFunction",
    ) -> None:
        """ """
        try:
            if marquee.delayCounter >= marquee.delayCountMax:
                marquee.delayCounter = 0
                marquee.stepCounter += marquee.step * marquee.direction
                if (
                    marquee.stepCounter + marquee.colorSequenceCount
                    >= LightFunction.Controller.virtualLEDCount
                ) or (marquee.stepCounter < 0):
                    marquee.direction *= -1
                LightFunction.Controller._VirtualLEDArray = np.roll(
                    LightFunction.Controller._VirtualLEDArray,
                    (marquee.step * marquee.direction),
                    0,
                )
            marquee.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                marquee.__class__.__name__,
                marquee.functionMarquee.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionCylon(
        cylon: "LightFunction",
    ) -> None:
        """ """
        try:
            next_index = cylon.index + (cylon.direction * cylon.step)
            if next_index >= LightFunction.Controller.virtualLEDCount:
                next_index = LightFunction.Controller.virtualLEDCount - 1
                cylon.direction = -1
            elif next_index < 0:
                next_index = 1
                cylon.direction = 1
            cylon.index = next_index
            if cylon.direction == 1:
                indices = list(
                    range(
                        cylon.index,
                        min(
                            (cylon.index + cylon.colorSequenceCount), LightFunction.Controller.virtualLEDCount
                        ),
                    )
                )
                if (cylon.index + cylon.colorSequenceCount) > LightFunction.Controller.virtualLEDCount:
                    overlap = (cylon.index + cylon.colorSequenceCount) - (
                        LightFunction.Controller.virtualLEDCount
                    )
                    idxs = list(
                        range(
                            (LightFunction.Controller.virtualLEDCount - 1),
                            (LightFunction.Controller.virtualLEDCount - 1 - overlap),
                            -1,
                        )
                    )
                    indices.extend(idxs)
                LightFunction.Controller._VirtualLEDArray[indices, :] = cylon.colorSequence[
                    : cylon.colorSequenceCount
                ]
            else:
                indices = list(range(cylon.index, max((cylon.index - cylon.colorSequenceCount), 0), -1))
                if (cylon.index - cylon.colorSequenceCount) < 0:
                    overlap = 0 - (cylon.index - cylon.colorSequenceCount)
                    idxs = list(
                        range(
                            (1),
                            (1 + overlap),
                        )
                    )
                    indices.extend(idxs)

                LightFunction.Controller._VirtualLEDArray[indices, :] = cylon.colorSequence[
                    : cylon.colorSequenceCount
                ]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                cylon.__class__.__name__,
                cylon.functionCylon.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionMerge(
        merge: "LightFunction",
    ) -> None:
        """ """
        try:
            # this takes
            # [0,1,2,3,4,5]
            # and creates
            # [[0,1,2]
            #  [3,4,5]]
            # out of it
            if merge.delayCounter >= merge.delayCountMax:
                merge.delayCounter = 0
                segmentCount = int(LightFunction.Controller.virtualLEDCount // merge.size)
                temp = np.reshape(LightFunction.Controller._VirtualLEDIndexArray, (segmentCount, merge.size))
                # now i can roll each row in a different direction and then undo
                # the matrixification of the array
                if temp[0][0] != temp[1][-1]:
                    temp[1] = np.flip(temp[0])
                    LightFunction.Controller._VirtualLEDArray[range(merge.size)] = merge.colorSequence[
                        range(merge.size)
                    ]
                temp[0] = np.roll(temp[0], merge.step, 0)
                temp[1] = np.roll(temp[1], -merge.step, 0)
                for i in range(LightFunction.Controller.virtualLEDCount // merge.size):
                    if i % 2 == 0:
                        temp[i] = temp[0]
                    else:
                        temp[i] = temp[1]
                # turn the matrix back into an array
                LightFunction.Controller._VirtualLEDIndexArray = np.reshape(
                    temp, (LightFunction.Controller.virtualLEDCount)
                )
            merge.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                merge.__class__.__name__,
                merge.functionMerge.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionAccelerate(
        accelerate: "LightFunction",
    ) -> None:
        """ """
        try:
            last_index = accelerate.index
            smash = False
            if accelerate.delayCounter >= accelerate.delayCountMax:
                accelerate.delayCounter = 0
                accelerate.stepCounter += 1
                accelerate.index = int(
                    (accelerate.index + (accelerate.direction * accelerate.step))
                    % LightFunction.Controller.virtualLEDCount
                )
            if accelerate.stepCounter >= accelerate.stepCountMax:
                accelerate.stepCounter = 0
                accelerate.delayCountMax -= 1
                if (accelerate.state % 2) == 0:
                    accelerate.step += 1
                accelerate.stepCountMax = random.randint(
                    int(LightFunction.Controller.LEDCount / 20), int(LightFunction.Controller.LEDCount / 4)
                )
                accelerate.state += 1
            if accelerate.state >= accelerate.stateMax:
                smash = True
                smash_rng = np.array(
                    list(
                        range(
                            accelerate.index,
                            accelerate.index + (accelerate.step * accelerate.direction * 3),
                            accelerate.direction,
                        )
                    )
                )
                modulo = np.where(smash_rng >= (LightFunction.Controller.LEDCount - 1))
                smash_rng[modulo] -= LightFunction.Controller.LEDCount
                modulo = np.where(smash_rng < 0)
                smash_rng[modulo] += LightFunction.Controller.LEDCount
                accelerate.delayCountMax = random.randint(5, 10)
                accelerate.stateMax = accelerate.delayCountMax
                accelerate.direction = [-1, 1][random.randint(0, 1)]
                accelerate.state = 0
                accelerate.step = 1
            accelerate.delayCounter += 1

            color = accelerate.colorSequenceNext
            LightFunction.Controller._VirtualLEDArray[last_index : accelerate.index, :] = color
            if smash == True:
                LightFunction.Controller._VirtualLEDArray[smash_rng, :] = LightFunction.Controller._fadeColor(
                    color, LightFunction.Controller.backgroundColor, 50
                )

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                accelerate.__class__.__name__,
                accelerate.functionAccelerate.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionRandomChange(
        change: "LightFunction",
    ) -> None:
        """ """

        class ChangeStates(IntEnum):
            FADING_ON = 0
            ON = 1
            FADING_OFF = 2
            WAIT = 3

        try:
            if np.array_equal(change.color, change.colorNext):
                if change.state == ChangeStates.FADING_ON.value:
                    change.state = ChangeStates.ON.value

                elif change.state == ChangeStates.ON.value:
                    if change.delayCounter >= change.delayCountMax:
                        change.delayCounter = random.randint(0, change.delayCountMax)
                        if random.randint(0, 3) == 3:
                            change.colorNext = LightFunction.Controller.backgroundColor
                            change.state = ChangeStates.FADING_OFF.value
                        else:
                            change.state = ChangeStates.WAIT.value
                    change.delayCounter += 1

                elif change.state == ChangeStates.FADING_OFF:
                    if change.delayCounter >= change.delayCountMax:
                        change.state = ChangeStates.WAIT.value
                        change.delayCounter = random.randint(0, change.delayCountMax)
                    change.delayCounter += 1

                else:
                    if change.delayCounter >= change.delayCountMax:
                        change.index = LightFunction.Controller.getRandomIndex()
                        change.color = np.copy(LightFunction.Controller._VirtualLEDArray[change.index])
                        change.colorNext = change.colorSequenceNext
                        change.state = ChangeStates.FADING_ON.value
                        change.delayCounter = random.randint(0, change.delayCountMax)
                    change.delayCounter += 1

            if change.fade == True:
                change.color = LightFunction.Controller._fadeColor(
                    change.color, change.colorNext, change.colorFade
                )
            else:
                change.color = change.colorNext
            LightFunction.Controller._VirtualLEDArray[change.index] = change.color

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                change.__class__.__name__,
                change.functionRandomChange.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionMeteors(
        meteor: "LightFunction",
    ) -> None:
        """ """
        try:
            if meteor.delayCounter >= meteor.delayCountMax:
                meteor.delayCounter = 0
                oldIndex = meteor.index
                newIndex = meteor.index + (meteor.step * meteor.direction)
                newLocation = (
                    meteor.index + (meteor.step * meteor.direction)
                ) % LightFunction.Controller.virtualLEDCount
                # save previous index
                meteor.indexPrevious = meteor.index
                # assign new index
                meteor.index = newLocation
                # positive step
                meteor.indexRange = np.array(
                    list(
                        range(
                            meteor.indexPrevious,
                            newIndex,
                            meteor.direction,
                        )
                    )
                )
                modulo = np.where(meteor.indexRange >= LightFunction.Controller.virtualLEDCount)
                meteor.indexRange[modulo] -= LightFunction.Controller.virtualLEDCount
                modulo = np.where(meteor.indexRange < 0)
                meteor.indexRange[modulo] += LightFunction.Controller.virtualLEDCount

                if meteor.colorCycle:
                    meteor.color = meteor.colorSequenceNext

                LightFunction.Controller._VirtualLEDArray[meteor.indexRange] = meteor.color

            meteor.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                meteor.__class__.__name__,
                meteor.functionMeteors.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionPaint(
        paintBrush: "LightFunction",
    ) -> None:
        """ """
        try:
            paintBrush.delayCounter += 1
            if paintBrush.delayCounter >= paintBrush.delayCountMax:
                paintBrush.delayCounter = 0
                paintBrush.index = (
                    paintBrush.index + (paintBrush.step * paintBrush.direction)
                ) % LightFunction.Controller.virtualLEDCount
                paintBrush.stepCounter += 1
                if paintBrush.stepCounter >= paintBrush.stepCountMax:
                    paintBrush.stepCounter = 0
                    paintBrush.direction = [-1, 1][random.randint(0, 1)]
                    paintBrush.delayCountMax = random.randint(0, paintBrush.delayCountMax)
                    paintBrush.stepCountMax = random.randint(2, LightFunction.Controller.virtualLEDCount * 2)
                    for i in range(random.randint(1, 5)):
                        paintBrush.color = paintBrush.colorSequenceNext
            LightFunction.Controller._VirtualLEDArray[paintBrush.index] = paintBrush.color
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                paintBrush.__class__.__name__,
                paintBrush.functionPaint.__name__,
                ex,
            )
            raise

    @staticmethod
    def functionSprites(
        sprite: "LightFunction",
    ) -> None:
        """ """
        try:
            if sprite.active:
                if not sprite.dying and not sprite.waking:
                    sprite.dying = (
                        random.randint(6, LightFunction.Controller.virtualLEDCount // 2) < sprite.duration
                    )
                sprite.step = random.randint(1, 3)
                sprite.indexUpdated = False
                if sprite.delayCounter >= sprite.delayCountMax:
                    sprite.delayCounter = 0
                    sprite.doMove(LightFunction.Controller.virtualLEDCount)
                if sprite.dying == True:
                    sprite.color = LightFunction.Controller._fadeColor(sprite.color, sprite.colorNext, 25)
                    if np.array_equal(sprite.color, sprite.colorNext):
                        sprite.active = False
                if sprite.waking == True:
                    sprite.color = LightFunction.Controller._fadeColor(sprite.color, sprite.colorGoal, 25)
                    if np.array_equal(sprite.color, sprite.colorGoal):
                        sprite.waking = False
                sprite.duration += 1
            else:
                if random.randint(0, 999) > 800:
                    sprite.active = True
                    sprite.waking = True
                    sprite.dying = False
                    sprite.duration = 0
                    sprite.direction = [-1, 1][random.randint(0, 1)]
                    sprite.index = random.randint(0, LightFunction.Controller.virtualLEDCount - 1)
                    sprite.indexPrevious = sprite.index
                    sprite.colorGoal = sprite.colorSequenceNext
                    sprite.color = PixelColors.OFF.array
                    sprite.colorNext = PixelColors.OFF.array
            if sprite.indexUpdated == True and isinstance(sprite.indexRange, np.ndarray):
                sprite.indexUpdated = False
                LightFunction.Controller._VirtualLEDArray[sprite.indexRange] = [sprite.color] * len(
                    sprite.indexRange
                )

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                sprite.__class__.__name__,
                sprite.functionSprites.__name__,
                ex,
            )
            raise
