"""This file defines functions that modify the LED patterns in interesting ways."""
from __future__ import annotations
from typing import Callable, Any, ClassVar, Optional
import logging
import random
from enum import IntEnum
import numpy as np
import lightberries  # noqa : used in typing
from lightberries.exceptions import LightFunctionException, LightBerryException
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_patterns import (
    ConvertPixelArrayToNumpyArray,
    DefaultColorSequenceByMonth,
)

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


class ArrayFunction:
    """This class defines everything necessary to modify LED patterns in interesting ways."""

    Controller: ClassVar["lightberries.pixel_array_controls.LightController"]

    def __init__(
        self,
        funcPointer: Callable,
        colorSequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Initialize the Light Function tracking object.

        Args:
            funcPointer: a function pointer that updates LEDs in the LightArrayController object.
            colorSequence: a sequence of RGB values.
        """
        self.privateColorSequence: np.ndarray[
            (3, Any), np.int32
        ] = ConvertPixelArrayToNumpyArray([])
        self.privateColorSequenceCount: int = 0
        self.privateColorSequenceIndex: int = 0

        self.colorSequence = colorSequence
        if self.colorSequence is None or len(self.colorSequence) == 0:
            self.colorSequence = DefaultColorSequenceByMonth()
        self.color: np.ndarray[(3,), np.int32] = self.colorSequence[0]
        self.colorBegin: np.ndarray[(3,), np.int32] = PixelColors.OFF
        self.colorNext: np.ndarray[(3,), np.int32] = PixelColors.OFF
        self.colorGoal: np.ndarray[(3,), np.int32] = PixelColors.OFF
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
        self.collision: bool = False
        self.collideWith: Optional[ArrayFunction] = None
        self.collideIntersect: int = 0
        self.indexRange: Optional[np.ndarray[(3, Any), np.int32]] = []
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

    def run(self):
        self.runFunction(self)

    @property
    def colorSequence(
        self,
    ) -> np.ndarray[(3, Any), np.int32]:
        """Return the color sequence.

        Returns:
            the color sequence
        """
        return self.privateColorSequence

    @colorSequence.setter
    def colorSequence(
        self,
        colorSequence: np.ndarray[(3, Any), np.int32],
    ) -> None:
        """Sets the color sequence.

        Args:
            colorSequence: desired color sequence
        """
        self.privateColorSequence = np.copy(
            ConvertPixelArrayToNumpyArray(colorSequence)
        )
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
    ) -> np.ndarray[(3,), np.int32]:
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
                        if (
                            self.color[rgbIndex] - self.colorFade
                            > self.colorNext[rgbIndex]
                        ):
                            self.color[rgbIndex] -= self.colorFade
                        elif (
                            self.color[rgbIndex] + self.colorFade
                            < self.colorNext[rgbIndex]
                        ):
                            self.color[rgbIndex] += self.colorFade
                        else:
                            self.color[rgbIndex] = self.colorNext[rgbIndex]
            self.delayCounter += 1
            # self._virtualLEDBuffer[self.index] = np.copy(self.color)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    def doMove(
        self,
    ) -> None:
        """Update the object index."""
        self.indexPrevious = self.index
        newIndexNoModulo = self.index + (self.step * self.direction)
        self.index = (self.index + (self.step * self.direction)) % (
            ArrayFunction.Controller.virtualLEDCount - 1
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
        modulo = np.where(
            self.indexRange >= (ArrayFunction.Controller.virtualLEDCount - 1)
        )
        self.indexRange[modulo] -= ArrayFunction.Controller.virtualLEDCount
        modulo = np.where(self.indexRange < 0)
        self.indexRange[modulo] += ArrayFunction.Controller.virtualLEDCount
        self.index = self.indexRange[-1]
        self.indexUpdated = True

    def calcRange(
        self,
        indexFrom: int,
        indexTo: int,
    ) -> np.ndarray[(Any,), np.int32]:
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
        modulo = np.where(rng >= (ArrayFunction.Controller.virtualLEDCount - 1))
        rng[modulo] -= ArrayFunction.Controller.virtualLEDCount
        modulo = np.where(rng < 0)
        rng[modulo] += ArrayFunction.Controller.virtualLEDCount
        return rng

    @staticmethod
    def functionCollisionDetection(
        collision: "ArrayFunction",
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
            lightFunctions = ArrayFunction.Controller.functionList
            if len(lightFunctions) > 1:
                for index1, meteor1 in enumerate(lightFunctions):
                    if "function" in meteor1.runFunction.__name__:
                        if index1 + 1 < len(lightFunctions):
                            for meteor2 in lightFunctions[index1 + 1 :]:
                                if "function" in meteor2.runFunction.__name__:
                                    if isinstance(
                                        meteor1.indexRange, np.ndarray
                                    ) and isinstance(meteor2.indexRange, np.ndarray):
                                        # this detects the intersection of two self._LightDataObjects'
                                        # movements across LEDs
                                        intersection = np.intersect1d(
                                            meteor1.indexRange, meteor2.indexRange
                                        )
                                        if (
                                            len(intersection) > 0
                                            and random.randint(0, 4) != 0
                                        ):
                                            meteor1.bounce = True
                                            meteor1.collideWith = meteor2
                                            meteor1.stepLast = meteor1.step
                                            meteor1.collideIntersect = int(
                                                intersection[0]
                                            )
                                            meteor2.bounce = True
                                            meteor2.collideWith = meteor1
                                            meteor2.stepLast = meteor2.step
                                            meteor2.collideIntersect = int(
                                                intersection[0]
                                            )
                                            foundBounce = True
            explosionIndices = []
            explosionColors = []
            if foundBounce is True:
                for meteor in lightFunctions:
                    if "function" in meteor.runFunction.__name__:
                        if meteor.bounce is True:
                            if isinstance(meteor.collideWith, ArrayFunction):
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
                                    meteor.collideIntersect
                                    + (meteor.step * meteor.direction)
                                ) % ArrayFunction.Controller.virtualLEDCount
                                othermeteor.index = (
                                    meteor.index + othermeteor.direction
                                ) % ArrayFunction.Controller.virtualLEDCount
                                meteor.indexPrevious = meteor.collideIntersect
                                othermeteor.indexPrevious = othermeteor.collideIntersect
                                meteor.bounce = False
                                othermeteor.collision = False
                                meteor.collideWith = None
                                othermeteor.collideWith = None
                                if collision.explode:
                                    if isinstance(meteor.indexRange, np.ndarray):
                                        middle = meteor.indexRange[
                                            len(meteor.indexRange) // 2
                                        ]
                                    radius = ArrayFunction.Controller.realLEDCount // 20
                                    for i in range(radius):
                                        explosionIndices.append(
                                            (middle - i)
                                            % ArrayFunction.Controller.virtualLEDCount,
                                        )
                                        explosionColors.append(
                                            Pixel(PixelColors.YELLOW)
                                            * (radius - i)
                                            / radius,
                                        )

                                        explosionIndices.append(
                                            (middle + i)
                                            % ArrayFunction.Controller.virtualLEDCount,
                                        )
                                        explosionColors.append(
                                            Pixel(PixelColors.YELLOW)
                                            * (radius - i)
                                            / radius,
                                        )
                                    ArrayFunction.Controller.virtualLEDBuffer[
                                        explosionIndices
                                    ] = np.array(explosionColors)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionOff(
        off: "ArrayFunction",
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
            ArrayFunction.Controller.virtualLEDBuffer[:] *= 0
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionFadeOff(
        fade: "ArrayFunction",
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
            ArrayFunction.Controller.virtualLEDBuffer[
                :
            ] = ArrayFunction.Controller.virtualLEDBuffer * (1 - fade.fadeAmount)
        except KeyboardInterrupt:
            raise
        except SystemExit:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionNone(
        nothing: "ArrayFunction",
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
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionSolidColorCycle(
        cycle: "ArrayFunction",
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
                ArrayFunction.Controller.virtualLEDBuffer *= 0
                # add new color
                ArrayFunction.Controller.virtualLEDBuffer += cycle.colorSequenceNext
            # increment delay counter
            cycle.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionMarquee(
        marquee: "ArrayFunction",
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
                if marquee.indexMax >= ArrayFunction.Controller.virtualLEDCount:
                    # switch direction
                    marquee.direction *= -1
                    # set index to either the next step or the max possible
                    # (accounts for step sizes > 1)
                    marquee.index = max(
                        marquee.index + (marquee.step * marquee.direction),
                        ArrayFunction.Controller.virtualLEDCount - marquee.size,
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
            ArrayFunction.Controller.virtualLEDBuffer[
                np.sort(marquee.indexRange)
            ] = marquee.colorSequence
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionCylon(
        cylon: "ArrayFunction",
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
                    cylon.indexRange = np.arange(
                        cylon.indexMin, cylon.indexMax, cylon.direction
                    )
                else:
                    # calculate index array going from max to min
                    cylon.indexNext = cylon.index + (cylon.direction * cylon.step)
                    cylon.indexMin = cylon.indexNext + (cylon.size * cylon.direction)
                    cylon.indexMax = cylon.indexNext
                    cylon.indexRange = np.arange(
                        cylon.indexMax, cylon.indexMin, cylon.direction
                    )
                # check if color sequence would go off of far end of light string
                if cylon.indexMax > ArrayFunction.Controller.virtualLEDCount:
                    # if the last LED is headed off the end
                    if cylon.indexNext >= ArrayFunction.Controller.virtualLEDCount:
                        # reverse direction
                        cylon.direction = -1
                        # fix next index
                        cylon.indexNext = ArrayFunction.Controller.virtualLEDCount - 2
                    # find where LEDs go off the end
                    over = np.where(
                        cylon.indexRange >= (ArrayFunction.Controller.virtualLEDCount)
                    )[0]
                    # reverse their direction
                    cylon.indexRange[over] = (
                        np.arange(-1, (len(over) + 1) * -1, -1)
                        + ArrayFunction.Controller.virtualLEDCount
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
            ArrayFunction.Controller.virtualLEDBuffer[
                cylon.indexRange
            ] = cylon.colorSequence[: ArrayFunction.Controller.virtualLEDCount]
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionMerge(
        merge: "ArrayFunction",
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
                segmentCount = int(
                    ArrayFunction.Controller.virtualLEDCount // merge.size
                )
                # this takes the 1-dimensional array
                # [0,1,2,3,4,5]
                # and creates a 2-dimensional matrix like
                # [[0,1,2],
                #  [3,4,5]]
                temp = np.reshape(
                    ArrayFunction.Controller.virtualLEDIndexArray,
                    (segmentCount, merge.size),
                )
                # now roll each row in a different direction and then undo
                # the matrixification of the array
                if temp[0][0] != temp[1][-1]:
                    temp[1] = np.flip(temp[0])
                    ArrayFunction.Controller.virtualLEDBuffer[
                        range(merge.size)
                    ] = merge.colorSequence[range(merge.size)]
                temp[0] = np.roll(temp[0], merge.step, 0)
                temp[1] = np.roll(temp[1], -merge.step, 0)
                for i in range(ArrayFunction.Controller.virtualLEDCount // merge.size):
                    if i % 2 == 0:
                        temp[i] = temp[0]
                    else:
                        temp[i] = temp[1]
                # turn the matrix back into an array
                ArrayFunction.Controller.virtualLEDIndexArray = np.reshape(
                    temp, (ArrayFunction.Controller.virtualLEDCount)
                )
            merge.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionAccelerate(
        accelerate: "ArrayFunction",
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
            # check delay counter, update index when it hits max
            if accelerate.delayCounter >= accelerate.delayCountMax:
                # reset delay counter
                accelerate.delayCounter = 0
                # update step counter
                accelerate.stepCounter += 1
                # calculate next index
                accelerate.index = int(
                    (accelerate.index + (accelerate.direction * accelerate.step))
                    % ArrayFunction.Controller.virtualLEDCount
                )
                accelerate.indexRange = np.arange(
                    accelerate.indexPrevious,
                    accelerate.index + accelerate.direction,
                    accelerate.direction,
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
                    int(ArrayFunction.Controller.realLEDCount / 20),
                    int(ArrayFunction.Controller.realLEDCount / 4),
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
                            accelerate.index
                            + (accelerate.step * accelerate.direction * 4),
                            accelerate.direction,
                        )
                    ),
                    dtype=np.int32,
                )
                # make sure that the splash doesn't go off the edge of the virtual led array
                modulo = np.where(
                    splashRange >= (ArrayFunction.Controller.realLEDCount - 1)
                )
                splashRange[modulo] -= ArrayFunction.Controller.realLEDCount
                modulo = np.where(splashRange < 0)
                splashRange[modulo] += ArrayFunction.Controller.realLEDCount
                # reset delay
                accelerate.delayCounter = 0
                # set new delay max
                accelerate.delayCountMax = random.randint(5, 10)
                # reset state max
                accelerate.stateMax = accelerate.delayCountMax
                # randomize direction
                accelerate.direction = ArrayFunction.Controller.getRandomDirection()
                # reset state
                accelerate.state = 0
                # reset step
                accelerate.step = 1
                # reset step counter
                accelerate.stepCounter = 0
                # randomize starting index
                accelerate.index = ArrayFunction.Controller.getRandomIndex()
                accelerate.indexPrevious = accelerate.index
                accelerate.indexRange = np.arange(
                    accelerate.indexPrevious, accelerate.index + 1
                )
            # increment delay counter
            accelerate.delayCounter += 1
            ArrayFunction.Controller.virtualLEDBuffer[
                accelerate.indexRange
            ] = accelerate.color
            if splash is True:
                ArrayFunction.Controller.virtualLEDBuffer[
                    splashRange, :
                ] = ArrayFunction.Controller.fadeColor(
                    accelerate.color, ArrayFunction.Controller.backgroundColor, 50
                )

        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionRandomChange(
        change: "ArrayFunction",
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
                            change.colorNext = ArrayFunction.Controller.backgroundColor
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
                        change.index = ArrayFunction.Controller.getRandomIndex()
                        # get color of current LED index
                        change.color = np.copy(
                            ArrayFunction.Controller.virtualLEDBuffer[change.index]
                        )
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
                change.color = ArrayFunction.Controller.fadeColor(
                    change.color, change.colorNext, change.colorFade
                )
            # if instant on/off
            else:
                # set the color
                change.color = change.colorNext
            # assign LED color to LED string
            ArrayFunction.Controller.virtualLEDBuffer[change.index] = change.color
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionMeteors(
        meteor: "ArrayFunction",
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
                meteor.indexNext = (
                    meteor.indexMax % ArrayFunction.Controller.virtualLEDCount
                )
                # save previous index
                meteor.indexPrevious = meteor.index
                # assign new index
                meteor.index = meteor.indexNext
                # calculate range of indices being updated
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
                    np.where(
                        meteor.indexRange >= ArrayFunction.Controller.virtualLEDCount
                    )
                ] -= ArrayFunction.Controller.virtualLEDCount
                meteor.indexRange[
                    np.where(meteor.indexRange < 0)
                ] += ArrayFunction.Controller.virtualLEDCount
                # if we are cycling through colors
                if meteor.colorCycle:
                    # assign the next color
                    meteor.color = meteor.colorSequenceNext
                # assign LEDs to LED string
                ArrayFunction.Controller.virtualLEDBuffer[
                    meteor.indexRange
                ] = meteor.color
            # update delay counter
            meteor.delayCounter += 1
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionSprites(
        sprite: "ArrayFunction",
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
                if (
                    random.randint(6, ArrayFunction.Controller.virtualLEDCount // 2)
                    < sprite.stepCounter
                ):
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
                    sprite.color = ArrayFunction.Controller.fadeColor(
                        sprite.color, sprite.colorNext, 25
                    )
                    # if we are done fading, then change state
                    if np.array_equal(sprite.color, sprite.colorNext):
                        sprite.state = SpriteState.OFF.value
                # if we are fading on
                if sprite.state == SpriteState.FADING_ON.value:
                    # fade the color
                    sprite.color = ArrayFunction.Controller.fadeColor(
                        sprite.color, sprite.colorGoal, 25
                    )
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
                    sprite.direction = ArrayFunction.Controller.getRandomDirection()
                    # randomize start index
                    sprite.index = ArrayFunction.Controller.getRandomIndex()
                    # set previous (prevent artifacts)
                    sprite.indexPrevious = sprite.index
                    # set target color
                    sprite.colorGoal = sprite.colorSequenceNext
                    # set current color
                    sprite.color = PixelColors.OFF
                    # set next color
                    sprite.colorNext = PixelColors.OFF
            # if we changed the index
            if sprite.indexUpdated is True and isinstance(
                sprite.indexRange, np.ndarray
            ):
                # reset flag
                sprite.indexUpdated = False
                # assign LEDs to LED string
                ArrayFunction.Controller.virtualLEDBuffer[sprite.indexRange] = [
                    sprite.color
                ] * len(sprite.indexRange)
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except LightBerryException:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def functionRaindrops(
        raindrop: "ArrayFunction",
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
                    indexLowerMin = max(
                        raindrop.index - raindrop.stepCounter - raindrop.step, 0
                    )
                    indexLowerMax = max(raindrop.index - raindrop.stepCounter, 0)
                    # higher valued side of "splash"
                    indexHigherMin = min(
                        raindrop.index + raindrop.stepCounter,
                        ArrayFunction.Controller.virtualLEDCount,
                    )
                    indexHigherMax = min(
                        raindrop.index + raindrop.stepCounter + raindrop.step,
                        ArrayFunction.Controller.virtualLEDCount,
                    )
                    if (indexLowerMax - indexLowerMin) > 0:
                        ArrayFunction.Controller.virtualLEDBuffer[
                            indexLowerMin:indexLowerMax
                        ] = [raindrop.color] * (indexLowerMax - indexLowerMin)
                    if (indexHigherMax - indexHigherMin) > 0:
                        ArrayFunction.Controller.virtualLEDBuffer[
                            indexHigherMin:indexHigherMax
                        ] = [raindrop.color] * (indexHigherMax - indexHigherMin)
                    # scaled fading as splash grows
                    raindrop.color[:] = raindrop.color * raindrop.colorScaler
                    # increment splash growth counter
                    raindrop.stepCounter += raindrop.step
                # splash is done growing
                else:
                    # randomize next splash start index
                    raindrop.index = random.randint(
                        0, ArrayFunction.Controller.virtualLEDCount - 1
                    )
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
            raise LightFunctionException from ex

    @staticmethod
    def functionAlive(
        thing: "ArrayFunction",
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
                        ) % ArrayFunction.Controller.virtualLEDCount
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
                        ) % ArrayFunction.Controller.virtualLEDCount
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
                        ) % ArrayFunction.Controller.virtualLEDCount
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
                        # make sure we aren't overgrown
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
                        # make sure we aren't overgrown
                        if thing.size >= thing.sizeMax:
                            thing.size = thing.sizeMax
                        # also make sure we still exist
                        elif thing.size < 1:
                            thing.size = 1
                    # if we are cycling through colors
                    if thing.state & ThingColors.CYCLE.value:
                        # artificially limit duration
                        if thing.stepCountMax >= shortPeriod:
                            thing.stepCountMax = shortPeriod
                        # randomly cycle through assign colors
                        if random.randint(0, 99) > 90:
                            for _ in range(0, random.randint(1, 3)):
                                thing.color = thing.colorSequenceNext
                    # calculate range of affected indices
                    index1 = thing.indexPrevious - (thing.size * thing.direction)
                    index2 = thing.indexPrevious + (
                        (thing.step + thing.size) * thing.direction
                    )
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
                            list(ThingMoves)[
                                random.randint(0, len(ThingMoves) - 1)
                            ].value
                            + list(ThingSizes)[
                                random.randint(0, len(ThingSizes) - 1)
                            ].value
                            + list(ThingColors)[
                                random.randint(0, len(ThingColors) - 1)
                            ].value
                        )
                    # reset step counter
                    thing.stepCounter = 0
                    # set step count to random value
                    thing.stepCountMax = random.randint(
                        ArrayFunction.Controller.virtualLEDCount // 10,
                        ArrayFunction.Controller.virtualLEDCount,
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
                    index2 = thing.indexPrevious + (
                        (thing.step + thing.size) * thing.direction
                    )
                    indexLower = min(index1, index2)
                    indexHigher = max(index1, index2)
                    # rng = np.array(range(_x1, _x2 + 1))
                    thing.indexRange = thing.calcRange(indexLower, indexHigher)
            # increment delay
            thing.delayCounter += 1
            # assign colors to indices
            ArrayFunction.Controller.virtualLEDBuffer[thing.indexRange] = thing.color
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def overlayTwinkle(
        twinkle: "ArrayFunction",
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
            for index in range(ArrayFunction.Controller.realLEDCount):
                if random.random() > twinkle.random:
                    ArrayFunction.Controller.overlayDictionary[
                        index
                    ] = twinkle.colorSequenceNext
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            raise LightFunctionException from ex

    @staticmethod
    def overlayBlink(
        blink: "ArrayFunction",
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
                for index in range(ArrayFunction.Controller.realLEDCount):
                    ArrayFunction.Controller.overlayDictionary[index] = color
        except SystemExit:
            raise
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            raise LightFunctionException from ex
