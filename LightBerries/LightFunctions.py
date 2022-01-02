"""This file defines functions that modify the LED patterns in interesting ways."""
from typing import Callable, Any, ClassVar, Optional
import logging
import random
from enum import IntEnum
from nptyping import NDArray
import numpy as np
import LightBerries  # pylint:disable=unused-import
from LightBerries.LightBerryExceptions import LightFunctionException
from LightBerries.LightPixels import Pixel, PixelColors
from LightBerries.LightPatterns import ConvertPixelArrayToNumpyArray

# pylint: disable=no-member

LOGGER = logging.getLogger("LightBerries")


class LEDFadeType(IntEnum):
    """Enumeration of types of LED fade for use in functions."""

    FADE_OFF = 0
    INSTANT_OFF = 1
    DONT = 2


class SpriteState(IntEnum):
    """Sprite function enum."""

    OFF = 0
    FADING_ON = 1
    ON = 2
    FADING_OFF = 3


class RaindropStates(IntEnum):
    """Raindrop function states."""

    OFF = 0
    SPLASH = 1


class ThingMoves(IntEnum):
    """States for thing movement."""

    NOTHING = 0x0
    METEOR = 0x1
    LIGHTSPEED = 0x2
    TURTLE = 0x4


class ThingSizes(IntEnum):
    """States for thing sizes."""

    NOTHING = 0x0
    GROW = 0x10
    SHRINK = 0x20


class ThingColors(IntEnum):
    """States for thing colors."""

    NOTHING = 0x0
    CYCLE = 0x100


class LightFunction:
    """This class defines everything neccesary to modify LED patterns in interesting ways."""

    Controller: ClassVar["LightBerries.LightControl.LightController"]

    def __init__(
        self,
        funcPointer: Callable,
        colorSequence: NDArray[(3, Any), np.int32],
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
            funcPointer: a function pointer that updates LEDs in the LightController object.
            colorSequence: a sequence of RGB values.
        """
        self.privateColorSequence: NDArray[(3, Any), np.int32] = ConvertPixelArrayToNumpyArray([])
        self.privateColorSequenceCount: int = 0
        self.privateColorSequenceIndex: int = 0

        self.colorSequence = colorSequence
        self.color: NDArray[(3,), np.int32] = colorSequence[0]
        self.colorBegin: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorNext: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorGoal: NDArray[(3,), np.int32] = PixelColors.OFF.array
        self.colorScaler: float = 0
        self.colorFade: int = 1
        self.colorCycle: bool = False

        self.funcName: str = funcPointer.__name__
        self.runFunction: Callable = funcPointer

        self.index: int = 0
        self.indexNext: int = self.index
        self.indexPrevious: int = self.index
        self.indexMin: int = self.index
        self.indexMax: int = self.index
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

        self.state: int = 0
        self.stateMax: int = 0

        self.explode: bool = False
        self.fadeType: LEDFadeType = LEDFadeType.FADE_OFF
        self.bounce: bool = False
        self.collideWith: Optional[LightFunction] = None
        self.collideIntersect: int = 0
        self.indexRange: Optional[NDArray[(3, Any), np, np.int32]] = []
        self.dying: bool = False
        self.waking: bool = False
        self.duration: int = 0
        self.direction: int = 1
        self.fadeAmount: float = 0
        self.fadeSteps: int = 0
        self.random: float = 0.5
        self.flipLength: int = 0

    def __str__(
        self,
    ) -> str:
        """String representation of this object.

        Returns:
            String representation of this object
        """
        return f'[{self.index}]: "{self.funcName}" {Pixel(self.color)}'

    def __repr__(
        self,
    ) -> str:
        """Return a string representation of this class(not de-serializable).

        Returns:
            string representation of this class(not de-serializable)
        """
        return f"<{self.__class__.__name__}> {str(self)}"

    @property
    def colorSequence(
        self,
    ) -> NDArray[(3, Any), np.int32]:
        """Return the color sequence.

        Returns:
            the color sequence
        """
        return self.privateColorSequence

    @colorSequence.setter
    def colorSequence(
        self,
        colorSequence: NDArray[(3, Any), np.int32],
    ) -> None:
        """Sets the color sequence.

        Args:
            colorSequence: desired color sequence
        """
        self.privateColorSequence = np.copy(ConvertPixelArrayToNumpyArray(colorSequence))
        self.colorSequenceCount = len(self.privateColorSequence)
        self.colorSequenceIndex = 0

    @property
    def colorSequenceCount(
        self,
    ) -> int:
        """Get the color sequence count.

        Returns:
            the color sequence count
        """
        return self.privateColorSequenceCount

    @colorSequenceCount.setter
    def colorSequenceCount(
        self,
        colorSequenceCount: int,
    ) -> None:
        """Setter for color sequence count.

        Args:
            colorSequenceCount: the number of colors in the sequence
        """
        self.privateColorSequenceCount = colorSequenceCount

    @property
    def colorSequenceIndex(
        self,
    ) -> int:
        """Color sequence index.

        Returns:
            the current color sequence index
        """
        return self.privateColorSequenceIndex

    @colorSequenceIndex.setter
    def colorSequenceIndex(
        self,
        colorSequenceIndex: int,
    ) -> None:
        """Color sequence index.

        Args:
            colorSequenceIndex: the current index being used for the color sequence
        """
        self.privateColorSequenceIndex = colorSequenceIndex

    @property
    def colorSequenceNext(
        self,
    ) -> NDArray[(3,), np.int32]:
        """Get the next color in the sequence.

        Returns:
            the next color in the sequence
        """
        temp = self.colorSequence[self.colorSequenceIndex]
        self.colorSequenceIndex += 1
        if self.colorSequenceIndex >= self.colorSequenceCount:
            self.colorSequenceIndex = 0
        if isinstance(temp, Pixel):
            return temp.array
        else:
            return temp

    def doFade(
        self,
    ) -> None:
        """Fade pixel colors.

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    def doMove(
        self,
    ) -> None:
        """Update the object index."""
        self.indexPrevious = self.index
        newIndexNoModulo = self.index + (self.step * self.direction)
        self.index = (self.index + (self.step * self.direction)) % (
            LightFunction.Controller.virtualLEDCount - 1
        )
        self.indexRange = np.array(
            list(
                range(
                    self.indexPrevious,
                    newIndexNoModulo,
                    self.direction,
                )
            )
        )
        modulo = np.where(self.indexRange >= (LightFunction.Controller.virtualLEDCount - 1))
        self.indexRange[modulo] -= LightFunction.Controller.virtualLEDCount
        modulo = np.where(self.indexRange < 0)
        self.indexRange[modulo] += LightFunction.Controller.virtualLEDCount
        self.index = self.indexRange[-1]
        self.indexUpdated = True

    def calcRange(
        self,
        indexFrom: int,
        indexTo: int,
    ) -> NDArray[(Any,), np.int32]:
        """Calculate index range.

        Args:
            indexFrom: from index
            indexTo: to index

        Returns:
            array of indices
        """
        if indexTo >= indexFrom:
            direction = 1
        else:
            direction = -1
        rng = np.arange(start=indexFrom, stop=indexTo, step=direction, dtype=np.int32)
        modulo = np.where(rng >= (LightFunction.Controller.virtualLEDCount - 1))
        rng[modulo] -= LightFunction.Controller.virtualLEDCount
        modulo = np.where(rng < 0)
        rng[modulo] += LightFunction.Controller.virtualLEDCount
        return rng

    @staticmethod
    def functionCollisionDetection(
        collision: "LightFunction",
    ) -> None:
        """Perform collision detection on the list of light function objects.

        Args:
            collision: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            foundBounce = False
            lightFunctions = LightFunction.Controller.functionList
            if len(lightFunctions) > 1:
                for index1, meteor1 in enumerate(lightFunctions):
                    if "function" in meteor1.runFunction.__name__:
                        if index1 + 1 < len(lightFunctions):
                            for meteor2 in lightFunctions[index1 + 1 :]:
                                if "function" in meteor2.runFunction.__name__:
                                    if isinstance(meteor1.indexRange, np.ndarray) and isinstance(
                                        meteor2.indexRange, np.ndarray
                                    ):
                                        # this detects the intersection of two self._LightDataObjects'
                                        # movements across LEDs
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
            explosionIndices = []
            explosionColors = []
            if foundBounce is True:
                for meteor in lightFunctions:
                    if "function" in meteor.runFunction.__name__:
                        if meteor.bounce is True:
                            if isinstance(meteor.collideWith, LightFunction):
                                othermeteor = meteor.collideWith
                                # previous = int(meteor.step)
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
                                othermeteor.index = (
                                    meteor.index + othermeteor.direction
                                ) % LightFunction.Controller.virtualLEDCount
                                meteor.indexPrevious = meteor.collideIntersect
                                othermeteor.indexPrevious = othermeteor.collideIntersect
                                meteor.bounce = False
                                othermeteor.bounce = False
                                meteor.collideWith = None
                                othermeteor.collideWith = None
                                if collision.explode:
                                    if isinstance(meteor.indexRange, np.ndarray):
                                        middle = meteor.indexRange[len(meteor.indexRange) // 2]
                                    radius = LightFunction.Controller.realLEDCount // 20
                                    for i in range(radius):
                                        explosionIndices.append(
                                            (middle - i) % LightFunction.Controller.virtualLEDCount,
                                        )
                                        explosionColors.append(
                                            Pixel(PixelColors.YELLOW).array * (radius - i) / radius,
                                        )

                                        explosionIndices.append(
                                            (middle + i) % LightFunction.Controller.virtualLEDCount,
                                        )
                                        explosionColors.append(
                                            Pixel(PixelColors.YELLOW).array * (radius - i) / radius,
                                        )
                                    LightFunction.Controller.virtualLEDArray[explosionIndices] = np.array(
                                        explosionColors
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionOff(
        off: "LightFunction",
    ) -> None:
        """Turn all Pixels OFF.

        Args:
            off: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            LightFunction.Controller.virtualLEDArray[:] *= 0
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                off.__class__.__name__,
                off.functionOff.__name__,
                ex,
            )
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionFadeOff(
        fade: "LightFunction",
    ) -> None:
        """Fade all Pixels toward OFF.

        Args:
            fade: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            LightFunction.Controller.virtualLEDArray[:] = LightFunction.Controller.virtualLEDArray * (
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionNone(
        nothing: "LightFunction",
    ) -> None:
        """Do nothing.

        Args:
            nothing: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionSolidColorCycle(
        cycle: "LightFunction",
    ) -> None:
        """Set all pixels to the next color.

        Args:
            cycle: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # wait for delay count before changing LEDs
            if cycle.delayCounter >= cycle.delayCountMax:
                # reset delay counter
                cycle.delayCounter = 0
                # remove any current color
                LightFunction.Controller.virtualLEDArray *= 0
                # add new color
                LightFunction.Controller.virtualLEDArray += cycle.colorSequenceNext
            # increment delay counter
            cycle.delayCounter += 1
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionMarquee(
        marquee: "LightFunction",
    ) -> None:
        """Move the LEDs in the color sequence from one end of the LED string to the other continuously.

        Args:
            marquee: the object used for tracking marquee status

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # wait for several LED cycles to change LEDs
            if marquee.delayCounter >= marquee.delayCountMax:
                # reset delay counter
                marquee.delayCounter = 0
                # calculate possible next index
                marquee.indexNext = marquee.index + (marquee.step * marquee.direction)
                # calculate max index we will update
                marquee.indexMax = marquee.indexNext + marquee.size
                # if we are going to overshoot
                if marquee.indexMax >= LightFunction.Controller.virtualLEDCount:
                    # switch direction
                    marquee.direction *= -1
                    # set index to either the next step or the max possible
                    # (accounts for step sizes > 1)
                    marquee.index = max(
                        marquee.index + (marquee.step * marquee.direction),
                        LightFunction.Controller.virtualLEDCount - marquee.size,
                    )
                # if we will undershoot
                elif marquee.indexMax < marquee.size:
                    # switch direction
                    marquee.direction *= -1
                    # set index to either the next step or zero
                    # (accounts for step sizes > 1)
                    marquee.index = max(
                        marquee.index + (marquee.step * marquee.direction),
                        0,
                    )
                else:
                    # next index is valid, use it
                    marquee.index = marquee.indexNext
            # increment delay counter
            marquee.delayCounter += 1
            # calculate color sequence range
            marquee.indexRange = np.arange(
                marquee.index,
                marquee.index + marquee.size,
            )
            # update LEDs with new values
            LightFunction.Controller.virtualLEDArray[np.sort(marquee.indexRange)] = marquee.colorSequence
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionCylon(
        cylon: "LightFunction",
    ) -> None:
        """Do cylon eye things.

        Args:
            cylon: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # if cylon.size > LightFunction.Controller.virtualLEDCount:
            # cylon.size = LightFunction.Controller.virtualLEDCount - 1
            # wait for several LED cycles to change LEDs
            if cylon.delayCounter >= cylon.delayCountMax:
                # reset delay counter
                cylon.delayCounter = 0
                # check direction
                if cylon.direction > 0:
                    # calculate index array going from min to max
                    cylon.indexNext = cylon.index + (cylon.direction * cylon.step)
                    cylon.indexMin = cylon.indexNext
                    cylon.indexMax = cylon.indexNext + (cylon.size * cylon.direction)
                    cylon.indexRange = np.arange(cylon.indexMin, cylon.indexMax, cylon.direction)
                else:
                    # calculate index array going from max to min
                    cylon.indexNext = cylon.index + (cylon.direction * cylon.step)
                    cylon.indexMin = cylon.indexNext + (cylon.size * cylon.direction)
                    cylon.indexMax = cylon.indexNext
                    cylon.indexRange = np.arange(cylon.indexMax, cylon.indexMin, cylon.direction)
                # check if color sequence would go off of far end of light string
                if cylon.indexMax > LightFunction.Controller.virtualLEDCount:
                    # if the last LED is headed off the end
                    if cylon.indexNext >= LightFunction.Controller.virtualLEDCount:
                        # reverse direction
                        cylon.direction = -1
                        # fix next index
                        cylon.indexNext = LightFunction.Controller.virtualLEDCount - 2
                    # find where LEDs go off the end
                    over = np.where(cylon.indexRange >= (LightFunction.Controller.virtualLEDCount))[0]
                    # reverse their direction
                    cylon.indexRange[over] = (
                        np.arange(-1, (len(over) + 1) * -1, -1) + LightFunction.Controller.virtualLEDCount
                    )
                # if LEDs go off the other end
                elif cylon.indexMin < -1:
                    # if the last LED is headed off the end
                    if cylon.indexNext < 0:
                        # reverse direction
                        cylon.direction *= -1
                        # fix next index
                        cylon.indexNext = 1
                    # find where LEDs go off the end
                    over = np.where(cylon.indexRange < 0)[0]
                    # reverse their direction
                    cylon.indexRange[over] = np.arange(1, (len(over) + 1), 1)
            # update delay counter
            cylon.delayCounter += 1
            # update index
            cylon.index = cylon.indexNext
            # update LEDs with new values
            LightFunction.Controller.virtualLEDArray[cylon.indexRange] = cylon.colorSequence[
                : LightFunction.Controller.virtualLEDCount
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionMerge(
        merge: "LightFunction",
    ) -> None:
        """Do merge function things.

        Args:
            merge: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # check delay counter
            if merge.delayCounter >= merge.delayCountMax:
                # reset delay counter
                merge.delayCounter = 0
                # figure out how many segments there are
                segmentCount = int(LightFunction.Controller.virtualLEDCount // merge.size)
                # this takes the 1-dimensional array
                # [0,1,2,3,4,5]
                # and creates a 2-dimensional matrix like
                # [[0,1,2],
                #  [3,4,5]]
                temp = np.reshape(LightFunction.Controller.virtualLEDIndexArray, (segmentCount, merge.size))
                # now roll each row in a different direction and then undo
                # the matrixification of the array
                if temp[0][0] != temp[1][-1]:
                    temp[1] = np.flip(temp[0])
                    LightFunction.Controller.virtualLEDArray[range(merge.size)] = merge.colorSequence[
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
                LightFunction.Controller.virtualLEDIndexArray = np.reshape(
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionAccelerate(
        accelerate: "LightFunction",
    ) -> None:
        """Do accelerate function things.

        Args:
            accelerate: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            accelerate.indexPrevious = accelerate.index
            splash = False
            # check delay counter, updaate index when it hits max
            if accelerate.delayCounter >= accelerate.delayCountMax:
                # reset delay counter
                accelerate.delayCounter = 0
                # update step counter
                accelerate.stepCounter += 1
                # calculate next index
                accelerate.index = int(
                    (accelerate.index + (accelerate.direction * accelerate.step))
                    % LightFunction.Controller.virtualLEDCount
                )
                accelerate.indexRange = np.arange(
                    accelerate.indexPrevious, accelerate.index + accelerate.direction, accelerate.direction
                )
                if accelerate.colorCycle is True:
                    accelerate.color = accelerate.colorSequenceNext
            # check index step counter, update speed state when it hits step count max
            if accelerate.stepCounter >= accelerate.stepCountMax:
                # reset step counter
                accelerate.stepCounter = 0
                # reduce delay max
                accelerate.delayCountMax -= 1
                # increment step size every two delay reductions
                if (accelerate.state % 2) == 0:
                    accelerate.step += 1
                # set step counter to a random number of steps based on LED count
                accelerate.stepCountMax = random.randint(
                    int(LightFunction.Controller.realLEDCount / 20),
                    int(LightFunction.Controller.realLEDCount / 4),
                )
                # update state counter
                accelerate.state += 1
            # check state counter, reset speed state when it hits max speed
            if accelerate.state >= accelerate.stateMax:
                # "splash" color when we hit the end
                splash = True
                #  create the "splash" index array before updating direction etc.
                splashRange = np.array(
                    list(
                        range(
                            accelerate.indexPrevious,
                            accelerate.index + (accelerate.step * accelerate.direction * 4),
                            accelerate.direction,
                        )
                    ),
                    dtype=np.int32,
                )
                # make sure that the splash doesnt go off the edge of the virtual led array
                modulo = np.where(splashRange >= (LightFunction.Controller.realLEDCount - 1))
                splashRange[modulo] -= LightFunction.Controller.realLEDCount
                modulo = np.where(splashRange < 0)
                splashRange[modulo] += LightFunction.Controller.realLEDCount
                # reset delay
                accelerate.delayCounter = 0
                # set new delay max
                accelerate.delayCountMax = random.randint(5, 10)
                # reset state max
                accelerate.stateMax = accelerate.delayCountMax
                # randomize direction
                accelerate.direction = LightFunction.Controller.getRandomDirection()
                # reset state
                accelerate.state = 0
                # reset step
                accelerate.step = 1
                # reset step counter
                accelerate.stepCounter = 0
                # randomize starting index
                accelerate.index = LightFunction.Controller.getRandomIndex()
                accelerate.indexPrevious = accelerate.index
                accelerate.indexRange = np.arange(accelerate.indexPrevious, accelerate.index + 1)
            # increment delay counter
            accelerate.delayCounter += 1
            LightFunction.Controller.virtualLEDArray[accelerate.indexRange] = accelerate.color
            if splash is True:
                LightFunction.Controller.virtualLEDArray[splashRange, :] = LightFunction.Controller.fadeColor(
                    accelerate.color, LightFunction.Controller.backgroundColor, 50
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionRandomChange(
        change: "LightFunction",
    ) -> None:
        """Do random change function things.

        Args:
            change: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """

        class ChangeStates(IntEnum):
            """States for random change."""

            FADING_ON = 0
            ON = 1
            FADING_OFF = 2
            WAIT = 3

        try:
            # if the random change has completed
            if np.array_equal(change.color, change.colorNext):
                # if the state is "fading on"
                if change.state == ChangeStates.FADING_ON.value:
                    # just set next state to "on"
                    change.state = ChangeStates.ON.value
                # if the state is "on"
                elif change.state == ChangeStates.ON.value:
                    # if we are done delaying
                    if change.delayCounter >= change.delayCountMax:
                        # reset delay counter
                        change.delayCounter = random.randint(0, change.delayCountMax)
                        # if semi-randomly fading to background color
                        if random.randint(0, 3) == 3:
                            # set next color to background color
                            change.colorNext = LightFunction.Controller.backgroundColor
                            # set state to "fading off"
                            change.state = ChangeStates.FADING_OFF.value
                        # if not fading to background
                        else:
                            # go to wait state
                            change.state = ChangeStates.WAIT.value
                    # increment delay counter
                    change.delayCounter += 1
                # if state is "fading off"
                elif change.state == ChangeStates.FADING_OFF.value:
                    # if we are done delaying
                    if change.delayCounter >= change.delayCountMax:
                        # set state to "waiting"
                        change.state = ChangeStates.WAIT.value
                        # reset delay counter
                        change.delayCounter = random.randint(0, change.delayCountMax)
                    # increment delay counter
                    change.delayCounter += 1
                # if state is "waiting"
                elif change.state == ChangeStates.WAIT.value:
                    # if we are done waiting
                    if change.delayCounter >= change.delayCountMax:
                        # randomize next index
                        change.index = LightFunction.Controller.getRandomIndex()
                        # get color of current LED index
                        change.color = np.copy(LightFunction.Controller.virtualLEDArray[change.index])
                        # get next color
                        for _ in range(random.randint(1, 5)):
                            change.colorNext = change.colorSequenceNext
                        # set state to "fading on"
                        change.state = ChangeStates.FADING_ON.value
                        # randomize delay counter so they aren't synchronized
                        change.delayCounter = random.randint(0, change.delayCountMax)
                    # increment delay counter
                    change.delayCounter += 1
            # if fading LEDs
            if change.fadeType == LEDFadeType.FADE_OFF:
                # fade the color
                change.color = LightFunction.Controller.fadeColor(
                    change.color, change.colorNext, change.colorFade
                )
            # if instant on/off
            else:
                # set the color
                change.color = change.colorNext
            # assign LED color to LED string
            LightFunction.Controller.virtualLEDArray[change.index] = change.color
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionMeteors(
        meteor: "LightFunction",
    ) -> None:
        """Do meteor function things.

        Args:
            meteor: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # check if we are done delaying
            if meteor.delayCounter >= meteor.delayCountMax:
                # reset delay counter
                meteor.delayCounter = 0
                # calculate index + step
                meteor.indexMax = meteor.index + (meteor.step * meteor.direction)
                # modulo next index to make sure it is a valid index in our string
                meteor.indexNext = meteor.indexMax % LightFunction.Controller.virtualLEDCount
                # save previous index
                meteor.indexPrevious = meteor.index
                # assign new index
                meteor.index = meteor.indexNext
                # caclulate range of indices being updated
                meteor.indexRange = np.array(
                    list(
                        range(
                            meteor.indexPrevious,
                            meteor.indexMax,
                            meteor.direction,
                        )
                    )
                )
                # make sure indices are valid ones
                meteor.indexRange[
                    np.where(meteor.indexRange >= LightFunction.Controller.virtualLEDCount)
                ] -= LightFunction.Controller.virtualLEDCount
                meteor.indexRange[np.where(meteor.indexRange < 0)] += LightFunction.Controller.virtualLEDCount
                # if we are cycling through colors
                if meteor.colorCycle:
                    # assign the next color
                    meteor.color = meteor.colorSequenceNext
                # assign LEDs to LED string
                LightFunction.Controller.virtualLEDArray[meteor.indexRange] = meteor.color
            # update delay counter
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionSprites(
        sprite: "LightFunction",
    ) -> None:
        """Do sprite function things.

        Args:
            sprite: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # if not off
            if sprite.state != SpriteState.OFF.value:
                # semi-randomly die
                if random.randint(6, LightFunction.Controller.virtualLEDCount // 2) < sprite.stepCounter:
                    sprite.state = SpriteState.FADING_OFF.value
                # randomize step sizes
                sprite.step = random.randint(1, 3)
                # only update LED string when we change the index
                sprite.indexUpdated = False
                # if we are done delaying
                if sprite.delayCounter >= sprite.delayCountMax:
                    # reset delay counter
                    sprite.delayCounter = 0
                    # move index
                    sprite.doMove()
                # if we are fading off
                if sprite.state == SpriteState.FADING_OFF.value:
                    # fade the color
                    sprite.color = LightFunction.Controller.fadeColor(sprite.color, sprite.colorNext, 25)
                    # if we are done fading, then change state
                    if np.array_equal(sprite.color, sprite.colorNext):
                        sprite.state = SpriteState.OFF.value
                # if we are fading on
                if sprite.state == SpriteState.FADING_ON.value:
                    # fade the color
                    sprite.color = LightFunction.Controller.fadeColor(sprite.color, sprite.colorGoal, 25)
                    # if we are done fading
                    if np.array_equal(sprite.color, sprite.colorGoal):
                        # change state
                        sprite.state = SpriteState.ON.value
                # increment duration counter
                sprite.stepCounter += 1
            # when sprite is in "off" state
            else:
                # randomly start fading on
                if random.randint(0, 999) > 800:
                    # set state to fade on
                    sprite.state = SpriteState.FADING_ON.value
                    # reset step counter
                    sprite.stepCounter = 0
                    # randomize direction
                    sprite.direction = LightFunction.Controller.getRandomDirection()
                    # randomize start index
                    sprite.index = LightFunction.Controller.getRandomIndex()
                    # set previous (prevent artifacts)
                    sprite.indexPrevious = sprite.index
                    # set target color
                    sprite.colorGoal = sprite.colorSequenceNext
                    # set current color
                    sprite.color = PixelColors.OFF.array
                    # set next color
                    sprite.colorNext = PixelColors.OFF.array
            # if we changed the index
            if sprite.indexUpdated is True and isinstance(sprite.indexRange, np.ndarray):
                # reset flag
                sprite.indexUpdated = False
                # assign LEDs to LED string
                LightFunction.Controller.virtualLEDArray[sprite.indexRange] = [sprite.color] * len(
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
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionRaindrops(
        raindrop: "LightFunction",
    ) -> None:
        """Do raindrop function things.

        Args:
            raindrop: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            # if raindrop is off
            if raindrop.state == RaindropStates.OFF.value:
                # randomly turn on
                if random.randint(0, 1000) / 1000 < raindrop.activeChance:
                    # set state on
                    raindrop.state = RaindropStates.SPLASH.value
                    # set max width of this raindrop
                    raindrop.stepCountMax = random.randint(2, raindrop.sizeMax)
                    # set fade amount
                    raindrop.fadeAmount = ((255 / raindrop.stepCountMax) / 255) * 2
                    raindrop.colorScaler = (
                        raindrop.stepCountMax - raindrop.stepCounter
                    ) / raindrop.stepCountMax
            # if raindrop is splashing
            if raindrop.state == RaindropStates.SPLASH.value:
                # if splash is still growing
                if raindrop.stepCounter < raindrop.stepCountMax:
                    # lower valued side of "splash"
                    indexLowerMin = max(raindrop.index - raindrop.stepCounter - raindrop.step, 0)
                    indexLowerMax = max(raindrop.index - raindrop.stepCounter, 0)
                    # higher valued side of "splash"
                    indexHigherMin = min(
                        raindrop.index + raindrop.stepCounter, LightFunction.Controller.virtualLEDCount
                    )
                    indexHigherMax = min(
                        raindrop.index + raindrop.stepCounter + raindrop.step,
                        LightFunction.Controller.virtualLEDCount,
                    )
                    if (indexLowerMax - indexLowerMin) > 0:
                        LightFunction.Controller.virtualLEDArray[indexLowerMin:indexLowerMax] = [
                            raindrop.color
                        ] * (indexLowerMax - indexLowerMin)
                    if (indexHigherMax - indexHigherMin) > 0:
                        LightFunction.Controller.virtualLEDArray[indexHigherMin:indexHigherMax] = [
                            raindrop.color
                        ] * (indexHigherMax - indexHigherMin)
                    # scaled fading as splash grows
                    raindrop.color[:] = raindrop.color * raindrop.colorScaler
                    # increment splash growth counter
                    raindrop.stepCounter += raindrop.step
                # splash is done growing
                else:
                    # raindomize next splash start index
                    raindrop.index = random.randint(0, LightFunction.Controller.virtualLEDCount - 1)
                    # reset growth counter
                    raindrop.stepCounter = 0
                    # semi-randomize next color
                    for _ in range(1, random.randint(2, 4)):
                        raindrop.color = raindrop.colorSequenceNext
                    # set state to off
                    raindrop.state = RaindropStates.OFF.value
            # increment delay
            # raindrop.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                LightFunction.__class__.__name__,
                LightFunction.functionRaindrops.__name__,
                ex,
            )
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def functionAlive(
        thing: "LightFunction",
    ) -> None:
        """Do alive function things.

        Args:
            thing: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """

        shortPeriod = 10

        try:
            # track last index
            thing.indexPrevious = thing.index
            # if we have hit our step goal
            if thing.delayCounter >= thing.delayCountMax:
                thing.delayCounter = 0
                if thing.stepCounter < thing.stepCountMax:
                    # if in meteor mode
                    if thing.state & ThingMoves.METEOR.value:
                        thing.step = 1
                        # set next index
                        thing.index = (
                            thing.index + (thing.step * thing.direction)
                        ) % LightFunction.Controller.virtualLEDCount
                        # randomly change direction
                        if random.randint(0, 99) > 95:
                            thing.direction *= -1
                    # if in fast meteor mode
                    elif thing.state & ThingMoves.LIGHTSPEED.value:
                        # artificially limit duration of this mode
                        if thing.stepCountMax >= shortPeriod:
                            thing.stepCountMax = shortPeriod
                        # randomize step size
                        thing.step = random.randint(7, 12)
                        # set next index
                        thing.index = (
                            thing.index + (thing.step * thing.direction)
                        ) % LightFunction.Controller.virtualLEDCount
                        # randomly change direction
                        if random.randint(0, 99) > 95:
                            thing.direction *= -1
                    # if slow meteor
                    elif thing.state & ThingMoves.TURTLE.value:
                        # set step to 1
                        thing.step = 1
                        # randomly change direction
                        if random.randint(0, 99) > 80:
                            thing.direction *= -1
                        # set next index
                        thing.index = (
                            thing.index + (thing.step * thing.direction)
                        ) % LightFunction.Controller.virtualLEDCount
                    # if we are growing
                    if thing.state & ThingSizes.GROW.value:
                        # artificially limit duration
                        if thing.stepCountMax > shortPeriod:
                            thing.stepCountMax = shortPeriod
                        # if we can still grow
                        if thing.size < thing.sizeMax:
                            # randomly grow
                            if random.randint(0, 99) > 80:
                                thing.size += random.randint(1, 5)
                            # also randomly shrink a bit
                            elif thing.size > 2:
                                if random.randint(0, 99) > 90:
                                    thing.size -= 1
                        # make sure we arent overgrown
                        if thing.size > thing.sizeMax:
                            thing.size = thing.sizeMax
                        # make sure we still exist
                        elif thing.size < 1:
                            thing.size = 1
                    # if we are shrinking
                    elif thing.state & ThingSizes.SHRINK.value:
                        # artificially limit duration
                        if thing.stepCountMax > shortPeriod:
                            thing.stepCountMax = shortPeriod
                        # if we can shrink
                        if thing.size > 0:
                            # randomly shrink
                            if random.randint(0, 99) > 80:
                                thing.size -= random.randint(1, 5)
                            # also randomly grow a bit
                            elif thing.size < thing.sizeMax:
                                if random.randint(0, 99) > 90:
                                    thing.size += 1
                        # make sure we arent overgrown
                        if thing.size >= thing.sizeMax:
                            thing.size = thing.sizeMax
                        # also make sure we still exist
                        elif thing.size < 1:
                            thing.size = 1
                    # if we are cycling through colors
                    if thing.state & ThingColors.CYCLE.value:
                        # artifically limit duration
                        if thing.stepCountMax >= shortPeriod:
                            thing.stepCountMax = shortPeriod
                        # randomly cycle through assign colors
                        if random.randint(0, 99) > 90:
                            for _ in range(0, random.randint(1, 3)):
                                thing.color = thing.colorSequenceNext
                    # calculate range of affected indices
                    index1 = thing.indexPrevious - (thing.size * thing.direction)
                    index2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
                    indexLower = min(index1, index2)
                    indexHigher = max(index1, index2)
                    # calculate affected range
                    thing.indexRange = thing.calcRange(indexLower, indexHigher)
                    # increment step counter
                    thing.stepCounter += 1
                # we hit our step goal, randomize next state
                else:
                    # states are mutually exclusive bits, can just add one of each
                    for _ in range(random.randint(1, 3)):
                        thing.state = (
                            list(ThingMoves)[random.randint(0, len(ThingMoves) - 1)].value
                            + list(ThingSizes)[random.randint(0, len(ThingSizes) - 1)].value
                            + list(ThingColors)[random.randint(0, len(ThingColors) - 1)].value
                        )
                    # reset step counter
                    thing.stepCounter = 0
                    # set step count to random value
                    thing.stepCountMax = random.randint(
                        LightFunction.Controller.virtualLEDCount // 10,
                        LightFunction.Controller.virtualLEDCount,
                    )
                    # set delay count randomly
                    thing.delayCountMax = random.randint(6, 15)
                    # randomize step size
                    thing.step = random.randint(1, 3)
                    # randomize fade amount
                    thing.fadeAmount = random.randint(80, 192)
                    # randomize delays
                    if thing.state & ThingMoves.METEOR.value:
                        thing.delayCountMax = random.randint(1, 3)
                    elif thing.state & ThingMoves.TURTLE.value:
                        thing.delayCountMax = random.randint(10, 15)
                    elif thing.state & ThingMoves.LIGHTSPEED.value:
                        thing.delayCountMax = random.randint(0, 3)
                    else:
                        thing.delayCountMax = random.randint(1, 7)
                    # calculate affected range
                    index1 = thing.indexPrevious - (thing.size * thing.direction)
                    index2 = thing.indexPrevious + ((thing.step + thing.size) * thing.direction)
                    indexLower = min(index1, index2)
                    indexHigher = max(index1, index2)
                    # rng = np.array(range(_x1, _x2 + 1))
                    thing.indexRange = thing.calcRange(indexLower, indexHigher)
            # increment delay
            thing.delayCounter += 1
            # assign colors to indices
            LightFunction.Controller.virtualLEDArray[thing.indexRange] = thing.color
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                thing.__class__.__name__,
                thing.functionAlive.__name__,
                ex,
            )
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def overlayTwinkle(
        twinkle: "LightFunction",
    ) -> None:
        """Do temporary twinkle modifications.

        Args:
            twinkle: tracking object

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            for index in range(LightFunction.Controller.realLEDCount):
                if random.random() > twinkle.random:
                    LightFunction.Controller.overlayDictionary[index] = twinkle.colorSequenceNext
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                twinkle.__class__.__name__,
                twinkle.overlayTwinkle.__name__,
                ex,
            )
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)

    @staticmethod
    def overlayBlink(
        blink: "LightFunction",
    ) -> None:
        """Randomly sets some lights to 'twinkleColor' without changing the virtual LED buffer.

        Args:
            blink: object for tracking blinking

        Raises:
            SystemExit: if exiting
            KeyboardInterrupt: if user quits
            LightFunctionException: if something bad happens
        """
        try:
            color = blink.colorSequenceNext
            if random.random() > blink.random:
                for index in range(LightFunction.Controller.realLEDCount):
                    LightFunction.Controller.overlayDictionary[index] = color
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            LOGGER.exception(
                "%s.%s Exception: %s",
                blink.__class__.__name__,
                blink.overlayBlink.__name__,
                ex,
            )
            raise LightFunctionException(str(ex)).with_traceback(ex.__traceback__)
