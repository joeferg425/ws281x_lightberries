"""Defines callable behaviors for this module."""

# ruff: noqa: F401, PGH003, I001, F403
from __future__ import annotations
from strenum import StrEnum
from typing import Annotated, Optional, cast

import typer
import logging
import sys

import lightberries
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.all_sequences import *
from lightberries.array_transform.all_functions import *
from lightberries.exceptions import LightBerryError, PermissionsError
from lightberries.pixel_sequence import PixelSequence
from lightberries.array_sequence.named import SequenceName
from lightberries.pixel_transform import PixelTransform

LOGGER = logging.getLogger("lightBerries")

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
def main(
    led_count: Annotated[
        int,
        typer.Option(
            "--led-count",
            "-l",
            min=1,
            max=512,
            help="the number of LEDs in your LED string",
        ),
    ] = DEFAULT_LED_COUNT,
    gpio_pwm_pin: Annotated[
        int,
        typer.Option(
            "--gpio-pwm-pin",
            # "--pwm-pin",
            # "--pin",
            "-p",
            help="GPIO pin to use for PWM signal",
        ),
    ] = DEFAULT_GPIO_PWM_PIN,
    dma_channel: Annotated[
        int,
        typer.Option(
            "--dma-channel",
            # "--dma",
            "-d",
            help="DMA channel",
        ),
    ] = DEFAULT_DMA_CHANNEL,
    pwm_frequency: Annotated[
        int,
        typer.Option(
            "--pwm-frequency",
            # "--frequency",
            help="frequency to run the PWM signal at",
        ),
    ] = DEFAULT_PWM_FREQUENCY,
    function: Annotated[  # type: ignore
        Optional[FunctionEnum],  # noqa: UP007 # type: ignore
        typer.Option(
            "--function",
            "-f",
            help="the name of the function to run",
        ),  # type: ignore
    ] = None,
    color: Annotated[
        Optional[ColorEnum],  # noqa: UP007
        typer.Option(
            "--sequence",
            "-s",
            help="the name of the color pattern to use",
        ),  # type: ignore
    ] = None,
    brightness: Annotated[
        float,
        typer.Option(
            "--brightness",
            "-b",
            min=0.01,
            max=0.99,
            help="the name of the color pattern to demo using randomized parameters",
        ),
    ] = DEFAULT_BRIGHTNESS,
    duration: Annotated[
        float,
        typer.Option(
            "--duration",
            "-d",
            help="the duration of each random demo function in seconds",
        ),
    ] = 0,
    *,
    debug: Annotated[
        bool,
        typer.Option(
            is_flag=True,
        ),
    ] = False,
) -> None:
    # to understand the rest of these arguments read their
    # documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    gamma = None
    led_strip_type = None
    invert = False
    pwm_channel = 0
    # create the light-function object
    try:
        light_control = ArrayController(
            led_count=led_count,
            pwm_gpio_pin=gpio_pwm_pin,
            dma_channel=dma_channel,
            pwm_frequency=pwm_frequency,
            pwm_channel=pwm_channel,
            pwm_invert_signal=invert,
            gamma=gamma,
            led_strip_type=led_strip_type,
            debug=debug,
            led_brightness=brightness,
        )
    except PermissionsError:
        LOGGER.exception("LightBerries failed")
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
        light_control.demo(
            seconds_per_mode=duration,
            function_names=function_names,
            color_names=color_names,
            kwargs={},
        )
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception:
        LOGGER.exception("LightBerries Demo failed")
        light_control.__del__()
