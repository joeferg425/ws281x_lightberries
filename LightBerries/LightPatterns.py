"""Defines a bunch of color patterns and color sequence methods."""
import random
import logging
import datetime
from typing import Any, List, Sequence, Union
from nptyping import NDArray
import numpy as np
from LightBerries.LightBerryExceptions import LightPatternException
from LightBerries.LightPixels import Pixel, PixelColors
from LightBerries.LightStrings import LightString

LOGGER = logging.getLogger("LightBerries")

# set some constants
DEFAULT_TWINKLE_COLOR = PixelColors.GRAY
DEFAULT_BACKGROUND_COLOR = PixelColors.OFF
DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]


def DefaultColorSequence() -> NDArray[(3, Any), np.int32]:
    """Get the default sequence of colors defined for this month.

    Returns:
        the default sequence of colors as determined by the current month

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    global DEFAULT_COLOR_SEQUENCE  # pylint: disable = global-statement
    try:
        date = datetime.datetime.now()
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
                PixelColors.CYAN,
                PixelColors.YELLOW,
                PixelColors.GREEN,
                PixelColors.WHITE,
            ]
        elif month == 6:
            DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.WHITE, PixelColors.BLUE]
        elif month == 7:
            DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.WHITE, PixelColors.BLUE]
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
            DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.WHITE, PixelColors.GREEN]
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __file__, DefaultColorSequence.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)
    return ConvertPixelArrayToNumpyArray(DEFAULT_COLOR_SEQUENCE)


def PixelArray(
    arrayLength: int,
) -> NDArray[(3, Any), np.int32]:
    """Creates array of RGB tuples that are all off.

    Args:
        arrayLength: the number of pixels desired in the returned pixel array

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        return np.array([PixelColors.OFF.array for i in range(int(arrayLength))])
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __file__, PixelArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def ConvertPixelArrayToNumpyArray(
    colorSequence: Sequence[Pixel],
) -> NDArray[(3, Any), np.int32]:
    """Convert an array of Pixels into a numpy array of rgb arrays.

    Args:
        colorSequence: a list of Pixel objects

    Returns:
        a numpy array of int arrays representing a string of rgb values

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        return np.array([Pixel(p).tuple for p in colorSequence])
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, ConvertPixelArrayToNumpyArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def SolidColorArray(
    arrayLength: int,
    color: Union[Pixel, NDArray[(3,), np.int32]] = DEFAULT_COLOR_SEQUENCE[0],
) -> NDArray[(3, Any), np.int32]:
    """Creates array of RGB tuples that are all one color.

    Args:
        arrayLength: the total desired length of the return array
        color: a pixel object defining the rgb values you want in the pattern

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        if isinstance(color, np.ndarray):
            _color = Pixel(color)
        else:
            _color = color
        return np.array([_color.array for i in range(int(arrayLength))])
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, SolidColorArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def ColorTransitionArray(
    arrayLength: int,
    wrap: bool = True,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = None,
) -> NDArray[(3, Any), np.int32]:
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
        LightPatternException: if something bad happens
    """
    try:
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        # get length of sequence
        sequenceLength = len(inputSequence)
        # derive=False
        count: int = 0
        stepCount = None
        prevStepCount: int = 0
        wrapOffset: int = 0
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
        arry = PixelArray(arrayLength)
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
                arry[i : (i + stepCount), rgbIndex] = np.linspace(
                    thisColor[rgbIndex], nextColor[rgbIndex], stepCount
                )
            count += stepCount
        return arry.astype(int)
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, ColorTransitionArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def RainbowArray(
    arrayLength: int,
    wrap: bool = False,
) -> NDArray[(3, Any), np.int32]:
    """Create a color gradient array.

    Args:
        arrayLength: The length of the gradient array to create. (the number of LEDs in the rainbow)
        wrap: set true to wrap the transition from the last color back to the first

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        return ColorTransitionArray(
            arrayLength=arrayLength,
            colorSequence=[
                PixelColors.RED,
                PixelColors.GREEN,
                PixelColors.BLUE,
                PixelColors.VIOLET,
            ],
            wrap=wrap,
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, RainbowArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def RepeatingColorSequenceArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = None,
) -> NDArray[(3, Any), np.int32]:
    """Creates a repeating LightPattern from a given sequence.

    Args:
        arrayLength: The length of the gradient array to create. (the number of LEDs in the rainbow)
        colorSequence: sequence of RGB tuples

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        arrayLength = int(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        sequenceLength = len(inputSequence)
        arry = PixelArray(arrayLength=arrayLength)
        arry[0:sequenceLength] = inputSequence
        for i in range(0, arrayLength, sequenceLength):
            if i + sequenceLength <= arrayLength:
                arry[i : i + sequenceLength] = arry[0:sequenceLength]
            else:
                extra = (i + sequenceLength) % arrayLength
                end = (i + sequenceLength) - extra
                arry[i:end] = arry[0 : (sequenceLength - extra)]
        return arry
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, RepeatingColorSequenceArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def RepeatingRainbowArray(
    arrayLength: int,
    segmentLength: int = None,
) -> NDArray[(3, Any), np.int32]:
    """Creates a repeating gradient for you.

    Args:
        arrayLength: the number of LEDs to involve in the rainbow
        segmentLength: the length of each mini rainbow in the repeating sequence

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
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
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, RepeatingRainbowArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def ReflectArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = None,
    foldLength=None,
) -> NDArray[(3, Any), np.int32]:
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
            temp = PixelArray(foldLength)
            temp[foldLength - colorSequenceLen :] = inputSequence
            inputSequence = temp
            colorSequenceLen = len(inputSequence)
        flip = False
        arry = PixelArray(arrayLength)
        for segBegin in range(0, arrayLength, foldLength):
            overflow = 0
            segEnd = 0
            if segBegin + foldLength <= arrayLength and segBegin + foldLength <= colorSequenceLen:
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
                arry[segBegin:segEnd] = inputSequence[foldLength - overflow - 1 :: -1]
            else:
                arry[segBegin:segEnd] = inputSequence[0 : foldLength - overflow]
            flip = not flip
        return arry
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, ReflectArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def RandomArray(
    arrayLength: int,
) -> NDArray[(3, Any), np.int32]:
    """Creates an array of random colors.

    Args:
        arrayLength: the number of random colors to generate for the array

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        arry = PixelArray(arrayLength)
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
            arry[i] = [redLED, greenLED, blueLED]
        return arry
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, RandomArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def PseudoRandomArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = None,
) -> NDArray[(3, Any), np.int32]:
    """Creates an array of random colors.

    Args:
        arrayLength: the number of random colors to generate for the array
        colorSequence: optional parameter from which to draw the pseudo random colors from

    Returns:
        a list of Pixel objects in the pattern you requested

    Raises:
        SystemExit: if exiting
        KeyboardInterrupt: if user quits
        LightPatternException: if something bad happens
    """
    try:
        inputSequence = None
        arry = PixelArray(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            inputSequence = DEFAULT_COLOR_SEQUENCE
        for i in range(arrayLength):
            if inputSequence is None:
                arry[i] = PixelColors.pseudoRandom()
            else:
                arry[i] = inputSequence[random.randint(0, len(inputSequence) - 1)]
        return arry
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, PseudoRandomArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


def ColorStretchArray(
    repeats=5,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = None,
) -> NDArray[(3, Any), np.int32]:
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
        arry = PixelArray(colorSequenceLength * repeats)
        for i in range(colorSequenceLength):
            arry[i * repeats : (i + 1) * repeats] = inputSequence[i]
        return arry
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in %s.%s: %s", __name__, ColorStretchArray.__name__, str(ex))
        raise LightPatternException(str(ex)).with_traceback(ex.__traceback__)


if __name__ == "__main__":
    import time

    lights = LightString(ledCount=100)
    LIGHT_LENGTH = len(lights)
    DELAY = 2

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = SolidColorArray(LIGHT_LENGTH, PixelColors.WHITE)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = ColorTransitionArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = RainbowArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = RepeatingColorSequenceArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = RepeatingRainbowArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = ReflectArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = PseudoRandomArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)

    p = PixelArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    p = ColorStretchArray(LIGHT_LENGTH)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(DELAY)
