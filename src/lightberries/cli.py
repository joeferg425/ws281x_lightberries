"""Defines callable behaviors for this module."""

# ruff: noqa: F401, PGH003, I001, F403
from __future__ import annotations

import logging
import sys
from typing import Optional, cast, TYPE_CHECKING

import typer

import lightberries
from lightberries.array_controller import ArrayController
from lightberries.array_sequence.all import *
from lightberries.array_transform.all import *
from lightberries.base.exceptions import LightBerryError, PermissionsError
from lightberries.base.logger import LOGGER


from lightberries.array_sequence.all import ColorEnum

CLI = typer.Typer(
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

DEFAULT_LED_COUNT = 100
DEFAULT_GPIO_PWM_PIN = 18
DEFAULT_DMA_CHANNEL = 5
DEFAULT_PWM_FREQUENCY = 800000
DEFAULT_BRIGHTNESS = 0.7


def set_verbosity(verbosity: int) -> int:
    """Handle verbosity argument in one place."""
    if verbosity > 2:  # noqa: PLR2004
        LOGGER.setLevel(5)
        LOGGER.log(5, "logging debug information verbosely.")
    elif verbosity > 1:
        LOGGER.setLevel(logging.DEBUG)
        LOGGER.debug("logging all debug information.")
    elif verbosity > 0:
        LOGGER.setLevel(logging.INFO)
        LOGGER.info("logging some debug information.")
    else:
        LOGGER.setLevel(logging.ERROR)
    return verbosity


LED_COUNT = typer.Option(
    DEFAULT_LED_COUNT,
    "--led-count",
    "-l",
    min=1,
    max=512,
    help="the number of LEDs in your LED string",
)
PWM_PIN = typer.Option(
    DEFAULT_GPIO_PWM_PIN,
    "--gpio-pwm-pin",
    "-p",
    help="GPIO pin to use for PWM signal",
)
DMA_CHANNEL = typer.Option(
    DEFAULT_DMA_CHANNEL,
    "--dma-channel",
    "-d",
    help="DMA channel",
)
PWM_FREQUENCY = typer.Option(
    DEFAULT_PWM_FREQUENCY,
    "--pwm-frequency",
    "-w",
    help="frequency to run the PWM signal at",
)
COLOR = typer.Option(
    None,
    "--sequence",
    "-s",
    help="the name of the color pattern to use",
)
BRIGHTNESS = typer.Option(
    DEFAULT_BRIGHTNESS,
    "--brightness",
    "-b",
    min=0.01,
    max=0.99,
    help="the name of the color pattern to demo using randomized parameters",
)
DURATION = typer.Option(
    0,
    "--duration",
    "-d",
    help="the duration of each random demo function in seconds",
)
VERBOSE = typer.Option(
    0,
    "--verbose",
    "-v",
    count=True,
    callback=set_verbosity,
)


@CLI.command(
    help=lightberries.__doc__,
    no_args_is_help=True,
    short_help="sudo python3 -m lightberries (Needs root for GPIO access)",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def main(  # noqa:  D103,  PLR0913
    led_count: int = LED_COUNT,
    gpio_pwm_pin: int = PWM_PIN,
    dma_channel: int = DMA_CHANNEL,
    pwm_frequency: int = PWM_FREQUENCY,
    color: Optional[ColorEnum] = COLOR,  # noqa: UP007
    brightness: float = BRIGHTNESS,
    duration: float = DURATION,
    verbose: int = VERBOSE,
) -> None:
    # to understand the rest of these arguments read their
    # documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    gamma = None
    led_strip_type = None
    invert = False
    pwm_channel = 0

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
    if color is None:
        color_names = color
    else:
        color_names = [cast("str", color)]
    try:
        array_controller.demo(
            seconds_per_mode=duration,
            function_names=None,
            color_names=color_names,
        )
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception:  # noqa: BLE001
        LOGGER.exception("LightBerries Demo failed")
    array_controller.__del__()


# for function_name in PixelTransform.ALL_TRANSFORMS:
#     if function_name not in ("Sprite", "sprite"):

#         @CLI.command(
#             name=function_name.lower(),
#             context_settings={"help_option_names": ["-h", "--help"]},
#         )
#         def function(  # noqa:  D103,  PLR0913
#             led_count: int = LED_COUNT,
#             gpio_pwm_pin: int = PWM_PIN,
#             dma_channel: int = DMA_CHANNEL,
#             pwm_frequency: int = PWM_FREQUENCY,
#             color: Optional[ColorEnum] = COLOR,  # noqa: UP007
#             brightness: float = BRIGHTNESS,
#             verbose: int = VERBOSE,
#             function_name: str = typer.Option(function_name, hidden=True),
#             # delay_count: Optional[int] = typer.Option(  # noqa: UP007
#             #     None,
#             #     "--delay-count",
#             #     "-d",
#             #     min=0,
#             #     max=50,
#             # ),
#             # fade_amount: Optional[int] = typer.Option(  # noqa: UP007
#             #     None,
#             #     "--fade-amount",
#             #     "-f",
#             #     min=0,
#             #     max=255,
#             # ),
#         ) -> None:
#             LOGGER.critical("Running %s function", function_name)
#             gamma = None
#             led_strip_type = None
#             invert = False
#             pwm_channel = 0
#             # create the light-function object
#             try:
#                 array_controller = ArrayController(
#                     led_count=led_count,
#                     pwm_gpio_pin=gpio_pwm_pin,
#                     dma_channel=dma_channel,
#                     pwm_frequency=pwm_frequency,
#                     pwm_channel=pwm_channel,
#                     pwm_invert_signal=invert,
#                     gamma=gamma,
#                     led_strip_type=led_strip_type,
#                     debug=verbose > 2,  # noqa: PLR2004
#                     led_brightness=brightness,
#                 )
#             except PermissionsError as ex:
#                 LOGGER.error(str(ex))
#                 sys.exit(1)
#             except LightBerryError:
#                 LOGGER.exception("Failed to launch LightBerries Controller")
#                 sys.exit(1)

#             clr = None
#             if color in PixelSequence.ALL_SEQUENCES:
#                 clr = PixelSequence.ALL_SEQUENCES[color](
#                     led_count=random.randint(
#                         1,
#                         array_controller.real_led_count,
#                     ),
#                 )
#             elif color in SequenceName._member_map_:
#                 color_enum = SequenceName(color)
#                 clr = get_named_sequence(
#                     name=color_enum,
#                     led_count=random.randint(
#                         1,
#                         array_controller.real_led_count,
#                     ),
#                 )
#             else:
#                 LOGGER.info("Color: %s", "default monthly sequence")
#                 clr = PixelSequence.get_monthly_color_sequence()
#             try:
#                 PixelTransform.ALL_TRANSFORMS[function_name].create(
#                     controller=array_controller,
#                     pixel_sequence=clr,
#                     # delay_count=delay_count,
#                     # fade_amount=fade_amount,
#                 )
#                 array_controller.run(seconds_per_mode=None)
#             except SystemExit:
#                 pass
#             except KeyboardInterrupt:
#                 pass
#             except Exception:
#                 LOGGER.exception("LightBerries Demo failed")
#             array_controller.__del__()
