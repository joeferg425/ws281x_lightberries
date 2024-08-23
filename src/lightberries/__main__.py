"""Defines callable behaviors for this module."""

# ruff: noqa: F401, PGH003, I001, F403
from __future__ import annotations

import argparse
import contextlib
import logging
import sys

import lightberries
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.all_sequences import *
from lightberries.array_transform.all_functions import *
from lightberries.exceptions import LightBerryError, PermissionsError
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

LOGGER = logging.getLogger("lightBerries")

if __name__ == "__main__":  # pylint: disable=invalid-name
    # the number of pixels in the light string
    led_count = 100
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
    brightness = 0.75
    duration = 20.0
    functions: list[str] = []
    colors: list[str] = []

    # command-line args
    parser = argparse.ArgumentParser(
        description=lightberries.__doc__,
        usage="sudo python3 -m lightberries (Needs root for GPIO access)",
    )
    parser.add_argument(
        "-l",
        "--LED_count",
        type=int,
        help="the number of LEDs in your LED string",
    )
    parser.add_argument(
        "-d",
        "--function_duration",
        type=float,
        help="the duration of each random demo function in seconds",
    )
    parser.add_argument(
        "-f",
        "--function",
        choices=[name.lower() for name in PixelTransform.ALL_TRANSFORMS],
        help="the name of the function to demo using randomized parameters",
    )
    parser.add_argument(
        "-c",
        "--color",
        choices=[name.lower() for name in PixelSequence.ALL_SEQUENCES],
        help="the name of the color pattern to demo using randomized parameters",
    )
    parser.add_argument(
        "-b",
        "--brightness",
        metavar="[0-1]",
        type=float,
        default=brightness,
        help="the name of the color pattern to demo using randomized parameters",
    )
    parser.add_argument("--debug", action="store_true")
    args, remaining_args = parser.parse_known_args()
    kwargs: dict[str, str] = {}
    if remaining_args and len(remaining_args) % 2 == 0:
        with contextlib.suppress(Exception):
            kwargs = dict(zip(remaining_args[0::2], remaining_args[1::2]))

    if args.LED_count is not None:
        led_count = args.LED_count

    if args.function_duration is not None:
        duration = args.function_duration

    if args.function is not None:
        functions = [args.function]

    if args.color is not None:
        colors = [args.color]

    if args.brightness >= 0 and args.brightness <= 1:
        brightness = float(args.brightness)

    # create the light-function object
    try:
        light_control = ArrayController(
            led_count=led_count,
            pwm_gpio_pin=GPIO_PWM_PIN,
            dma_channel=DMA_CHANNEL,
            pwm_frequency=PWM_FREQUENCY,
            pwm_channel=PWM_CHANNEL,
            pwm_invert_signal=INVERT,
            gamma=GAMMA,
            led_strip_type=LED_STRIP_TYPE,
            debug=args.debug,
            led_brightness=brightness,
        )
    except PermissionsError:
        LOGGER.exception("LightBerries failed")
        sys.exit(1)
    except LightBerryError:
        LOGGER.exception("Failed to launch LightBerries Controller")
        sys.exit(1)
    # run the demo!
    try:
        light_control.demo(
            duration,
            function_names=functions,
            color_names=colors,
            kwargs=kwargs,
        )
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception:
        LOGGER.exception("LightBerries Demo failed")
        light_control.__del__()
