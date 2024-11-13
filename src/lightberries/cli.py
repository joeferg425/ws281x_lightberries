"""Defines callable behaviors for this module."""

# ruff: noqa: F401, PGH003, I001, F403
from __future__ import annotations

import logging
import sys
from typing import Optional, cast

import typer
from strenum import StrEnum

import lightberries
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.all_sequences import *
from lightberries.array_sequence.named import SequenceName
from lightberries.array_transform.all_functions import *
from lightberries.base.exceptions import LightBerryError, PermissionsError
from lightberries.base.logger import LOGGER
from lightberries.pixel_sequence import PixelSequence
from lightberries.pixel_transform import PixelTransform

CLI = typer.Typer()

DEFAULT_LED_COUNT = 100
DEFAULT_GPIO_PWM_PIN = 18
DEFAULT_DMA_CHANNEL = 5
DEFAULT_PWM_FREQUENCY = 800000
DEFAULT_BRIGHTNESS = 0.7
FUNCTION_NAMES = [name.lower() for name in PixelTransform.ALL_TRANSFORMS]
FunctionEnum = StrEnum("FunctionEnum", FUNCTION_NAMES)
COLOR_SEQUENCE_NAMES = [name.lower() for name in PixelSequence.ALL_SEQUENCES] + [
    name.lower() for name in SequenceName._member_names_
]
ColorEnum = StrEnum("ColorEnum", COLOR_SEQUENCE_NAMES)


@CLI.command(
    help=lightberries.__doc__,
    no_args_is_help=True,
    short_help="sudo python3 -m lightberries (Needs root for GPIO access)",
)
def main(  # noqa: C901, PLR0912, PLR0913
    led_count: int = typer.Option(
        DEFAULT_LED_COUNT,
        "--led-count",
        "--leds",
        "-l",
        min=1,
        max=512,
        help="the number of LEDs in your LED string",
    ),
    gpio_pwm_pin: int = typer.Option(
        DEFAULT_GPIO_PWM_PIN,
        "--gpio-pwm-pin",
        "--pwm-pin",
        "--pin",
        "-p",
        help="GPIO pin to use for PWM signal",
    ),
    dma_channel: int = typer.Option(
        DEFAULT_DMA_CHANNEL,
        "--dma-channel",
        "--dma",
        "-d",
        help="DMA channel",
    ),
    pwm_frequency: int = typer.Option(
        DEFAULT_PWM_FREQUENCY,
        "--pwm-frequency",
        "--frequency",
        "--freq",
        help="frequency to run the PWM signal at",
    ),
    function: Optional[FunctionEnum] = typer.Option(  # noqa: B008, UP007
        None,
        "--function",
        "-f",
        help="the name of the function to run",
    ),  # type: ignore
    color: Optional[ColorEnum] = typer.Option(  # noqa: B008, UP007
        None,
        "--sequence",
        "-s",
        help="the name of the color pattern to use",
    ),  # type: ignore
    brightness: float = typer.Option(
        DEFAULT_BRIGHTNESS,
        "--brightness",
        "-b",
        min=0.01,
        max=0.99,
        help="the name of the color pattern to demo using randomized parameters",
    ),
    duration: float = typer.Option(
        0,
        "--duration",
        "-d",
        help="the duration of each random demo function in seconds",
    ),
    *,
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
    ),
) -> None:
    # to understand the rest of these arguments read their
    # documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    gamma = None
    led_strip_type = None
    invert = False
    pwm_channel = 0
    if verbose > 2:  # noqa: PLR2004
        LOGGER.setLevel(5)
        LOGGER.log(5,"logging debug information verbosely.")
    elif verbose > 1:
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug("logging all debug information.")
    elif verbose > 0:
        LOGGER.setLevel(logging.INFO)
        LOGGER.info("logging some debug information.")
    else:
        LOGGER.setLevel(logging.ERROR)

    # create the light-function object
    try:
        array_controller = ArrayController(
            led_count=led_count,
            pwm_gpio_pin=gpio_pwm_pin,
            dma_channel=dma_channel,
            pwm_frequency=pwm_frequency,
            pwm_channel=pwm_channel,
            pwm_invert_signal=invert,
            gamma=gamma,
            led_strip_type=led_strip_type,
            debug=verbose > 2,  # noqa: PLR2004
            led_brightness=brightness,
        )
    except PermissionsError as ex:
        LOGGER.error(str(ex))
        sys.exit(1)
    except LightBerryError:
        LOGGER.exception("Failed to launch LightBerries Controller")
        sys.exit(1)
    # run the demo!
    if function is None:
        function_names = function
    else:
        function_names = [cast("str", function)]
    if color is None:
        color_names = color
    else:
        color_names = [cast("str", color)]
    try:
        array_controller.demo(
            seconds_per_mode=duration,
            function_names=function_names,
            color_names=color_names,
        )
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception:
        LOGGER.exception("LightBerries Demo failed")
        array_controller.__del__()
