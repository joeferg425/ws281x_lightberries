"""Defines a bunch of color patterns and color sequence methods."""
from __future__ import annotations
import random
import logging
import datetime
from typing import Any, List, Sequence, Union
import numpy as np
from lightberries.exceptions import (
    LightBerryException,
    LightPatternException,
)
from lightberries.pixel import Pixel, PixelColors

LOGGER = logging.getLogger("LightBerries")

# set some constants
DEFAULT_TWINKLE_COLOR = PixelColors.GRAY
DEFAULT_BACKGROUND_COLOR = PixelColors.OFF
DEFAULT_COLOR_SEQUENCE = np.array(
    [
        PixelColors.RED,
        PixelColors.GREEN,
        PixelColors.BLUE,
    ],
    dtype=np.int32,
)


def DefaultColorSequenceByMonth(
    date: datetime.datetime = datetime.datetime.now(),
) -> np.ndarray[(3, Any), np.int32]:
    """Get the default sequence of colors defined for this month.

    Returns:
        the default sequence of colors as determined by the current month

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    global DEFAULT_COLOR_SEQUENCE  # pylint: disable = global-statement
    try:
        month = date.month
        if month == 1:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.CYAN2,
                PixelColors.WHITE,
                PixelColors.CYAN,
                PixelColors.BLUE2,
                PixelColors.BLUE,
            ]
        elif month == 2:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.PINK,
                PixelColors.WHITE,
                PixelColors.RED,
                PixelColors.WHITE,
            ]
        elif month == 3:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.GREEN,
                PixelColors.WHITE,
                PixelColors.ORANGE,
                PixelColors.WHITE,
                PixelColors.YELLOW,
            ]
        elif month == 4:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.PINK,
                PixelColors.CYAN,
                PixelColors.YELLOW,
                PixelColors.GREEN,
                PixelColors.WHITE,
            ]
        elif month == 5:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.PINK,
                PixelColors.YELLOW,
                PixelColors.GREEN,
                PixelColors.WHITE,
            ]
        elif month == 6:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.RED,
                PixelColors.WHITE,
                PixelColors.BLUE,
                PixelColors.GREEN,
            ]
        elif month == 7:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.RED,
                PixelColors.WHITE,
                PixelColors.BLUE,
            ]
        elif month == 8:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.ORANGE,
                PixelColors.WHITE,
                PixelColors.YELLOW,
                PixelColors.ORANGE2,
            ]
        elif month == 9:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.ORANGE,
                PixelColors.WHITE,
                PixelColors.YELLOW,
                PixelColors.ORANGE2,
                PixelColors.RED,
                PixelColors.RED2,
            ]
        elif month == 10:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.MIDNIGHT,
                PixelColors.RED,
                PixelColors.ORANGE,
                PixelColors.OFF,
            ]
        elif month == 11:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.RED,
                PixelColors.MIDNIGHT,
                PixelColors.GRAY,
            ]
        elif month == 12:
            DEFAULT_COLOR_SEQUENCE = [
                PixelColors.RED,
                PixelColors.WHITE,
                PixelColors.GREEN,
            ]
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex
    return ConvertPixelArrayToNumpyArray(DEFAULT_COLOR_SEQUENCE)


def PixelArrayOff(
    arrayLength: int,
) -> np.ndarray[(3, Any), np.int32]:
    """Creates array of RGB tuples that are all off.

    Args:
        arrayLength: the number of pixels desired in the returned pixel array

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        if arrayLength > 0:
            return np.array([PixelColors.OFF for i in range(int(arrayLength))])
        else:
            return np.zeros((0, 3))
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def ConvertPixelArrayToNumpyArray(
    colorSequence: Sequence[Pixel],
) -> np.ndarray[(3, Any), np.int32]:
    """Convert an array of Pixels into a numpy array of rgb arrays.

    Args:
        colorSequence: a list of Pixel objects

    Returns:
        a numpy array of int arrays representing a string of rgb values

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        if len(colorSequence) > 0:
            return np.array([Pixel(p).tuple for p in colorSequence])
        else:
            return np.zeros((0, 3))
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def SolidColorArray(
    arrayLength: int,
    color: np.ndarray[(3,), np.int32] = DEFAULT_COLOR_SEQUENCE[0],
) -> np.ndarray[(3, Any), np.int32]:
    """Creates array of RGB tuples that are all one color.

    Args:
        arrayLength: the total desired length of the return array
        color: a pixel object defining the rgb values you want in the pattern

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        if arrayLength > 0:
            return np.array([color for i in range(int(arrayLength))])
        else:
            return np.zeros((0, 3))
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def ColorTransitionArray(
    arrayLength: int,
    colorSequence: np.ndarray[(3, Any), np.int32] = None,
    wrap: bool = True,
) -> np.ndarray[(3, Any), np.int32]:
    """This is a slightly more versatile version of CreateRainbow.

    The user specifies a color sequence and the number of steps (LEDs)
    in the transition from one color to the next.

    Args:
        arrayLength: The total totalArrayLength of the final sequence in LEDs. This
            parameter is optional and defaults to LED_INDEX_COUNT
        wrap: set true to wrap the transition from the last color back to the first
        colorSequence: a sequence of colors to merge between

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        if colorSequence is None:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        else:
            inputSequence = colorSequence
        # get length of sequence
        if len(inputSequence.shape):
            sequenceLength = inputSequence.shape[0]
        if sequenceLength == 0:
            return np.zeros((0, 3))
        count = 0
        stepCount = None
        prevStepCount = 0
        wrapOffset = 0
        if wrap is True:
            wrapOffset = 0
        else:
            wrapOffset = 1
        # figure out how many LEDs per color change
        if stepCount is None:
            # derive = True
            stepCount = arrayLength // (sequenceLength - wrapOffset)
            prevStepCount = stepCount
        # create temporary array
        temp_array = PixelArrayOff(arrayLength)
        # step through color sequence
        for colorIndex in range(sequenceLength - wrapOffset):
            if colorIndex == sequenceLength - 1:
                stepCount = arrayLength - count
            elif colorIndex == sequenceLength - 2:
                stepCount = arrayLength - count
            # figure out the current and next colors
            thisColor = inputSequence[colorIndex]
            nextColor = inputSequence[(colorIndex + 1) % sequenceLength]
            # handle red, green, and blue individually
            for rgbIndex in range(len(thisColor)):
                i = colorIndex * prevStepCount
                # linspace creates the array of values from arg1, to arg2, in exactly arg3 steps
                temp_array[i : (i + stepCount), rgbIndex] = np.linspace(
                    thisColor[rgbIndex], nextColor[rgbIndex], stepCount
                )
            count += stepCount
        return temp_array.astype(int)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def RainbowArray(
    arrayLength: int,
    wrap: bool = False,
) -> np.ndarray[(3, Any), np.int32]:
    """Create a color gradient array.

    Args:
        arrayLength: The length of the gradient array to create. (the number of LEDs in the rainbow)
        wrap: set true to wrap the transition from the last color back to the first

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        return ColorTransitionArray(
            arrayLength=arrayLength,
            colorSequence=np.array(
                [
                    PixelColors.RED,
                    PixelColors.GREEN,
                    PixelColors.BLUE,
                    PixelColors.VIOLET,
                ]
            ),
            wrap=wrap,
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def RepeatingColorSequenceArray(
    arrayLength: int,
    colorSequence: np.ndarray[(3, Any), np.int32] = None,
) -> np.ndarray[(3, Any), np.int32]:
    """Creates a repeating LightPattern from a given sequence.

    Args:
        arrayLength: The length of the gradient array to create. (the number of LEDs in the rainbow)
        colorSequence: sequence of RGB tuples

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        arrayLength = int(arrayLength)
        if colorSequence is None:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        else:
            inputSequence = colorSequence
        if len(inputSequence):
            sequenceLength = len(inputSequence)
        else:
            return np.zeros((0, 3))
        temp_array = PixelArrayOff(arrayLength=arrayLength)
        temp_array[0:sequenceLength] = inputSequence
        for i in range(0, arrayLength, sequenceLength):
            if i + sequenceLength <= arrayLength:
                temp_array[i : i + sequenceLength] = temp_array[0:sequenceLength]
            else:
                extra = (i + sequenceLength) % arrayLength
                end = (i + sequenceLength) - extra
                temp_array[i:end] = temp_array[0 : (sequenceLength - extra)]
        return temp_array
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def RepeatingRainbowArray(
    arrayLength: int,
    segmentLength: int = None,
) -> np.ndarray[(3, Any), np.int32]:
    """Creates a repeating gradient for you.

    Args:
        arrayLength: the number of LEDs to involve in the rainbow
        segmentLength: the length of each mini rainbow in the repeating sequence

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    if segmentLength is None:
        segmentLength = arrayLength // 4
    try:
        return RepeatingColorSequenceArray(
            arrayLength=arrayLength,
            colorSequence=RainbowArray(arrayLength=segmentLength, wrap=True),
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def ReflectArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], np.ndarray[(3, Any), np.int32]] = None,
    foldLength=None,
) -> np.ndarray[(3, Any), np.int32]:
    """Generates an array where each repetition of the input. Sequence is reversed from the previous one.

    Args:
        arrayLength: the number of LEDs to involve in the rainbow
        colorSequence: an array of RGB tuples
        foldLength: the length of each segment wto be copied and reflected

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    # if user didn't specify otherwise, fold in middle
    try:
        arrayLength = int(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        colorSequenceLen = len(inputSequence)
        if foldLength is None:
            foldLength = arrayLength // 2
        if foldLength > colorSequenceLen:
            temp = PixelArrayOff(foldLength)
            temp[foldLength - colorSequenceLen :] = inputSequence
            inputSequence = temp
            colorSequenceLen = len(inputSequence)
        flip = False
        temp_array = PixelArrayOff(arrayLength)
        for segBegin in range(0, arrayLength, foldLength):
            overflow = 0
            segEnd = 0
            if (
                segBegin + foldLength <= arrayLength
                and segBegin + foldLength <= colorSequenceLen
            ):
                segEnd = segBegin + foldLength
            elif segBegin + foldLength > arrayLength:
                segEnd = segBegin + foldLength
                overflow = (segBegin + foldLength) % arrayLength
                segEnd = (segBegin + foldLength) - overflow
            elif segBegin + foldLength > colorSequenceLen:
                segEnd = segBegin + colorSequenceLen
                overflow = (segBegin + colorSequenceLen) % colorSequenceLen
                segEnd = (segBegin + colorSequenceLen) - overflow

            if flip:
                temp_array[segBegin:segEnd] = inputSequence[
                    foldLength - overflow - 1 :: -1
                ]
            else:
                temp_array[segBegin:segEnd] = inputSequence[0 : foldLength - overflow]
            flip = not flip
        return temp_array
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def RandomArray(
    arrayLength: int,
) -> np.ndarray[(3, Any), np.int32]:
    """Creates an array of random colors.

    Args:
        arrayLength: the number of random colors to generate for the array

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        temp_array = PixelArrayOff(arrayLength)
        for i in range(arrayLength):
            # prevent 255, 255, 255
            exclusion = random.randint(0, 2)
            if exclusion != 0:
                redLED = random.randint(0, 255)
            else:
                redLED = 0
            if exclusion != 1:
                greenLED = random.randint(0, 255)
            else:
                greenLED = 0
            if exclusion != 2:
                blueLED = random.randint(0, 255)
            else:
                blueLED = 0
            temp_array[i] = [redLED, greenLED, blueLED]
        return temp_array
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def PseudoRandomArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], np.ndarray[(3, Any), np.int32]] = None,
) -> np.ndarray[(3, Any), np.int32]:
    """Creates an array of random colors.

    Args:
        arrayLength: the number of random colors to generate for the array
        colorSequence: optional parameter from which to draw the pseudo random colors from

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightBerryException: if propagating an exception
        LightPatternException: if something bad happens
    """
    try:
        inputSequence = None
        temp_array = PixelArrayOff(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        for i in range(arrayLength):
            if inputSequence is None:
                temp_array[i] = PixelColors.pseudoRandom()
            else:
                temp_array[i] = inputSequence[random.randint(0, len(inputSequence) - 1)]
        return temp_array
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex


def ColorStretchArray(
    repeats=5,
    colorSequence: Union[List[Pixel], np.ndarray[(3, Any), np.int32]] = None,
) -> np.ndarray[(3, Any), np.int32]:
    """Takes a sequence of input colors and repeats each element the requested number of times.

    Args:
        repeats: the number of times to repeat each element oc colorSequence
        colorSequence: a list of pixels defining the desired colors in the output array

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        colorSequenceLength = len(inputSequence)
        # repeats = arrayLength // colorSequenceLength
        temp_array = PixelArrayOff(colorSequenceLength * repeats)
        for i in range(colorSequenceLength):
            temp_array[i * repeats : (i + 1) * repeats] = inputSequence[i]
        return temp_array
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except LightBerryException:
        raise
    except Exception as ex:
        raise LightPatternException from ex
