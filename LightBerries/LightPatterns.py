from nptyping import NDArray
import numpy as np
import random
import logging
import datetime
from typing import Any, List, Optional, Sequence, Union
from numpy.lib.arraysetops import isin
from LightBerries.Pixels import Pixel, PixelColors
from LightBerries.LightStrings import LightString

LOGGER = logging.getLogger("LightBerries")

# set some constants
DEFAULT_TWINKLE_COLOR = PixelColors.GRAY
DEFAULT_BACKGROUND_COLOR = PixelColors.OFF
DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.GREEN, PixelColors.BLUE]


def get_DEFAULT_COLOR_SEQUENCE() -> NDArray[(3, Any), np.int32]:
    global DEFAULT_COLOR_SEQUENCE
    d = datetime.datetime.now()
    m = d.month
    if m == 1:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.CYAN2,
            PixelColors.WHITE,
            PixelColors.CYAN,
            PixelColors.BLUE2,
            PixelColors.BLUE,
        ]
    elif m == 2:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.PINK,
            PixelColors.WHITE,
            PixelColors.RED,
            PixelColors.WHITE,
        ]
    elif m == 3:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.GREEN,
            PixelColors.WHITE,
            PixelColors.ORANGE,
            PixelColors.WHITE,
            PixelColors.YELLOW,
        ]
    elif m == 4:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.PINK,
            PixelColors.CYAN,
            PixelColors.YELLOW,
            PixelColors.GREEN,
            PixelColors.WHITE,
        ]
    elif m == 5:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.PINK,
            PixelColors.CYAN,
            PixelColors.YELLOW,
            PixelColors.GREEN,
            PixelColors.WHITE,
        ]
    elif m == 6:
        DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.WHITE, PixelColors.BLUE]
    elif m == 7:
        DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.WHITE, PixelColors.BLUE]
    elif m == 8:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.ORANGE,
            PixelColors.WHITE,
            PixelColors.YELLOW,
            PixelColors.ORANGE2,
        ]
    elif m == 9:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.ORANGE,
            PixelColors.WHITE,
            PixelColors.YELLOW,
            PixelColors.ORANGE2,
            PixelColors.RED,
            PixelColors.RED2,
        ]
    elif m == 10:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.MIDNIGHT,
            PixelColors.RED,
            PixelColors.ORANGE,
            PixelColors.OFF,
        ]
    elif m == 11:
        DEFAULT_COLOR_SEQUENCE = [
            PixelColors.RED,
            PixelColors.MIDNIGHT,
            PixelColors.GRAY,
        ]
    elif m == 12:
        DEFAULT_COLOR_SEQUENCE = [PixelColors.RED, PixelColors.WHITE, PixelColors.GREEN]
    return ConvertPixelArrayToNumpyArray(DEFAULT_COLOR_SEQUENCE)


def PixelArray(arrayLength: int) -> NDArray[(3, Any), np.int32]:
    """Creates array of RGB tuples that are all off

    arrayLength: the number of pixels desired in the returned pixel array

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        return np.array([PixelColors.OFF.array for i in range(int(arrayLength))])
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in {}.PixelArray: {}".format("LightPatterns", ex))
        raise


def ConvertPixelArrayToNumpyArray(colorSequence: Sequence[Pixel]) -> NDArray[(3, Any), np.int32]:
    """Convert an array of Pixels into a numpy array of rgb arrays

    colorSequence: a list of Pixel objects

    returns: a numpy array of int arrays representing a string of rgb values
    """
    try:
        return np.array([Pixel(p).tuple for p in colorSequence])
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in {}.ConvertPixelArrayToNumpyArray: {}".format("LightPatterns", ex))
        raise


def SolidColorArray(
    arrayLength: int,
    color: Union[Pixel, NDArray[(3,), np.int32]] = DEFAULT_COLOR_SEQUENCE[0],
) -> NDArray[(3, Any), np.int32]:
    """Creates array of RGB tuples that are all one color

    arrayLength: the total desired length of the return array

    color: a pixel object defining the rgb values you want in the pattern

    returns: a list of Pixel objects in the pattern you requested
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
        LOGGER.exception("Error in {}.SolidColorArray: {}".format("LightPatterns", ex))
        raise


def WesArray() -> NDArray[(3, Any), np.int32]:
    """creates a color array that Wes wanted

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        return ConvertPixelArrayToNumpyArray(
            [
                PixelColors.WHITE,
                PixelColors.ORANGE,
                PixelColors.YELLOW,
                PixelColors.RED,
                PixelColors.BLUE,
                PixelColors.GREEN,
            ]
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in {}.WesArray: {}".format("LightPatterns", ex))
        raise


def ColorTransitionArray(
    arrayLength: int,
    wrap: bool = True,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = DEFAULT_COLOR_SEQUENCE,
) -> NDArray[(3, Any), np.int32]:
    """
    This is a slightly more versatile version of CreateRainbow.
    The user specifies a color sequence and the number of steps (LEDs)
    in the transition from one color to the next.

    arrayLength: int
            The total totalArrayLength of the final sequence in LEDs
            This parameter is optional and defaults to LED_INDEX_COUNT

    wrap: bool
            set true to wrap the transition from the last color back to the first

    colorSequence: array(tuple(int,int,int))
            a sequence of colors to merge between

    stepCount: int
            The number of LEDs it takes to transition between one color and the next.
            This parameter is optional and defaults to 'totalArrayLength / len(sequence)'.

    returns: List[Pixel]
            a list of Pixel objects in the pattern you requested
    """
    try:
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            # TODO make this exception useful
            raise Exception("")
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
        LOGGER.exception("Error in {}.ColorTransitionArray: {}".format("LightPatterns", ex))
        raise


def RainbowArray(arrayLength: int, wrap: bool = False) -> NDArray[(3, Any), np.int32]:
    """create a color gradient array

    arrayLength: The length of the gradient array to create.
            (the number of LEDs in the rainbow)

    returns: a list of Pixel objects in the pattern you requested
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
        LOGGER.exception("Error in {}.RainbowArray: {}".format("LightPatterns", ex))
        raise


def RepeatingColorSequenceArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = DEFAULT_COLOR_SEQUENCE,
) -> NDArray[(3, Any), np.int32]:
    """
    Creates a repeating LightPattern from a given sequence

    arrayLength: The length of the gradient array to create.
            (the number of LEDs in the rainbow)

    colorSequence: sequence of RGB tuples

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        arrayLength = int(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            # TODO: make this useful
            raise Exception("")
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
        LOGGER.exception("Error in {}.RepeatingColorSequenceArray: {}".format("LightPatterns", ex))
        raise


def RepeatingRainbowArray(arrayLength: int, segmentLength: int = None) -> NDArray[(3, Any), np.int32]:
    """
    Creates a repeating gradient for you

    arrayLength: the number of LEDs to involve in the rainbow

    segmentLength: the length of each mini rainbow in the repeating sequence

    returns: a list of Pixel objects in the pattern you requested
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
        LOGGER.exception("Error in {}.RepeatingRainbowArray: {}".format("LightPatterns", ex))
        raise


def ReflectArray(
    arrayLength: int,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = DEFAULT_COLOR_SEQUENCE,
    foldLength=None,
) -> NDArray[(3, Any), np.int32]:
    """
    generates an array where each repetition of the input
    sequence is reversed from the previous

    arrayLength: the number of LEDs to involve in the rainbow

    colorSequence: an array of RGB tuples

    returns: a list of Pixel objects in the pattern you requested
    """
    # if user didn't specify otherwise, fold in middle
    try:
        arrayLength = int(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            # TODO: make this useful
            raise Exception("")
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
        LOGGER.exception("Error in {}.ReflectArray: {}".format("LightPatterns", ex))
        raise


def RandomArray(arrayLength: int) -> NDArray[(3, Any), np.int32]:
    """
    Creates an array of random colors

    arrayLength: the number of random colors to generate for the array

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        arry = PixelArray(arrayLength)
        for i in range(arrayLength):
            # prevent 255, 255, 255
            x = random.randint(0, 2)
            if x != 0:
                redLED = random.randint(0, 255)
            else:
                redLED = 0
            if x != 1:
                greenLED = random.randint(0, 255)
            else:
                greenLED = 0
            if x != 2:
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
        LOGGER.exception("Error in {}.PseudoRandomArray: {}".format("LightPatterns", ex))
        raise


def PseudoRandomArray(
    arrayLength: int, colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = None
) -> NDArray[(3, Any), np.int32]:
    """
    Creates an array of random colors

    arrayLength: the number of random colors to generate for the array

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        inputSequence = None
        arry = PixelArray(arrayLength)
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            # TODO: make this usefule
            raise Exception("")
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
        LOGGER.exception("Error in {}.PseudoRandomArray: {}".format("LightPatterns", ex))
        raise


def ColorStretchArray(
    repeats=5,
    colorSequence: Union[List[Pixel], NDArray[(3, Any), np.int32]] = DEFAULT_COLOR_SEQUENCE,
) -> NDArray[(3, Any), np.int32]:
    """takes a sequence of input colors and repeats each element the requested number of times

    repeats: the number of times to repeat each element oc colorSequence

    colorSequence: a list of pixels defining the desired colors in the output array

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        if isinstance(colorSequence, list):
            inputSequence = ConvertPixelArrayToNumpyArray(colorSequence)
        elif isinstance(colorSequence, np.ndarray):
            inputSequence = np.array(colorSequence)
        else:
            # TODO: make this useful
            raise Exception("")
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
        LOGGER.exception("Error in {}.PseudoRandomArray: {}".format("LightPatterns", ex))
        raise


def Emily1() -> NDArray[(3, Any), np.int32]:
    """
    defines a color pattern that emily requested

    returns: a list of Pixel objects in the pattern you requested
    """
    try:
        return ConvertPixelArrayToNumpyArray(
            [
                PixelColors.RED,
                PixelColors.ORANGE,
                PixelColors.YELLOW,
                PixelColors.GREEN,
                PixelColors.ORANGE,
                PixelColors.YELLOW,
                PixelColors.GREEN,
                PixelColors.PURPLE,
                PixelColors.YELLOW,
                PixelColors.GREEN,
                PixelColors.PURPLE,
                PixelColors.BLUE,
            ]
        )
    except SystemExit:
        raise
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        LOGGER.exception("Error in {}.PseudoRandomArray: {}".format("LightPatterns", ex))
        raise


if __name__ == "__main__":
    import time

    lights = LightString(ledCount=100)
    lightLength = len(lights)
    delay = 2

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = SolidColorArray(lightLength, PixelColors.WHITE)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = WesArray()
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = ColorTransitionArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = RainbowArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = RepeatingColorSequenceArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = RepeatingRainbowArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = ReflectArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = PseudoRandomArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)

    p = PixelArray(lightLength)
    lights[: len(p)] = p
    p = ColorStretchArray(lightLength)
    lights[: len(p)] = p
    lights.refresh()
    time.sleep(delay)
