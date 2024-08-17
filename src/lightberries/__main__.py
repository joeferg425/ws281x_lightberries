"""Defines callable behaviors for this module."""

# ruff: noqa: F401
from __future__ import annotations

import argparse
import logging
import sys

import lightberries
from lightberries.array_controller import ArrayController
from lightberries.array_transforms.all_functions import (
    TransformAccelerate,
    TransformAlive,
    TransformBlink,
    TransformCollisionDetect,
    TransformCylon,
    TransformFade,
    TransformFadeOff,
    TransformMarquee,
    TransformMerge,
    TransformMeteor,
    TransformNone,
    TransformOff,
    TransformRaindrop,
    TransformRandomChange,
    TransformSolidColorCycle,
    TransformSprites,
    TransformTwinkle,
)
from lightberries.exceptions import LightBerryError, PermissionsError
from lightberries.light_sequences import (
    SequenceOff,
    SequencePseudoRandom,
    SequenceRainbow,
    SequenceRainbowRepeating,
    SequenceRandom,
    SequenceRepeatedReflected,
    SequenceRepeating,
    SequenceSolid,
    SequenceStretch,
    SequenceTransition,
)
from lightberries.sequence import Sequence
from lightberries.transform import Transform

LOGGER = logging.getLogger("lightBerries")

if __name__ == "__main__":  # pylint: disable=invalid-name
    # the number of pixels in the light string
    PIXEL_COUNT = 100
    # GPIO pin to use for PWM signal
    GPIO_PWM_PIN = 18
    # DMA channel
    DMA_CHANNEL = 5
    # frequency to run the PWM signal at
    PWM_FREQUENCY = 800000
    # to understand the rest of these arguments read their
    # documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    GAMMA = None
    LED_STRIP_TYPE = None
    INVERT = False
    PWM_CHANNEL = 0
    BRIGHTNESS = 0.75
    DURATION = 20.0
    FUNCTIONS = None
    COLORS = None

    # command-line args
    parser = argparse.ArgumentParser(
        description=lightberries.__doc__,
        usage="sudo python3 -m lightberries (Needs root for GPIO access)",
    )
    parser.add_argument("-l", "--LED_count", type=int, help="the number of LEDs in your LED string")
    parser.add_argument(
        "-d",
        "--function_duration",
        type=float,
        help="the duration of each random demo function in seconds",
    )
    parser.add_argument(
        "-f",
        "--function",
        choices=[name.lower() for name in Transform.ALL_TRANSFORMS],
        help="the name of the function to demo using randomized parameters",
    )
    parser.add_argument(
        "-c",
        "--color",
        choices=[name.lower() for name in Sequence.ALL_SEQUENCES],
        help="the name of the color pattern to demo using randomized parameters",
    )
    parser.add_argument(
        "-b",
        "--brightness",
        metavar="[0-1]",
        type=float,
        default=BRIGHTNESS,
        help="the name of the color pattern to demo using randomized parameters",
    )
    args = parser.parse_args()

    if args.LED_count is not None:
        PIXEL_COUNT = args.LED_count

    if args.function_duration is not None:
        DURATION = args.function_duration

    if args.function is not None:
        FUNCTIONS = [args.function]

    if args.color is not None:
        COLORS = [args.color]

    if args.brightness >= 0 and args.brightness <= 1:
        BRIGHTNESS = float(args.brightness)

    # create the light-function object
    try:
        lightControl = ArrayController(
            led_count=PIXEL_COUNT,
            pwm_gpio_pin=GPIO_PWM_PIN,
            dma_channel=DMA_CHANNEL,
            pwm_frequency=PWM_FREQUENCY,
            pwm_channel=PWM_CHANNEL,
            pwm_invert_signal=INVERT,
            gamma=GAMMA,
            led_strip_type=LED_STRIP_TYPE,
            debug=True,
            led_brightness=BRIGHTNESS,
        )
    except PermissionsError as ex:
        LOGGER.error("%s", ex)
        sys.exit(1)
    except LightBerryError:
        LOGGER.exception("Failed to launch LightBerries Controller")
        sys.exit(1)
    # run the demo!
    try:
        lightControl.demo(DURATION, functionNames=FUNCTIONS, colorNames=COLORS)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        LOGGER.exception(ex)
        lightControl.__del__()
        # sys.exit(1)
    # run the demo!
    try:
        lightControl.demo(DURATION, functionNames=FUNCTIONS, colorNames=COLORS)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        LOGGER.exception(ex)
    lightControl.__del__()
