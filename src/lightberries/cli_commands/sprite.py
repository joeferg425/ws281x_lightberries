"""Sprite function CLI."""

# ruff: noqa: F401, PGH003, I001, F403
from __future__ import annotations

import random
import sys
from typing import Optional, TYPE_CHECKING

from typer import Option

from lightberries.array_controller import ArrayController
from lightberries.array_sequence.all import *
from lightberries.array_sequence.named import get_named_sequence
from lightberries.array_transform.sprite import TransformSprite
from lightberries.base.exceptions import LightBerryError, PermissionsError
from lightberries.base.logger import LOGGER
from lightberries.cli import BRIGHTNESS, CLI, COLOR, DMA_CHANNEL, LED_COUNT, PWM_FREQUENCY, PWM_PIN, VERBOSE


if TYPE_CHECKING:
    from lightberries.array_sequence.all import ColorEnum

DEFAULT_LED_COUNT = 100
DEFAULT_GPIO_PWM_PIN = 18
DEFAULT_DMA_CHANNEL = 5
DEFAULT_PWM_FREQUENCY = 800000
DEFAULT_BRIGHTNESS = 0.7


@CLI.command(
    name="sprite",
)
def sprite(  # noqa:  D103,  PLR0913
    led_count: int = LED_COUNT,
    gpio_pwm_pin: int = PWM_PIN,
    dma_channel: int = DMA_CHANNEL,
    pwm_frequency: int = PWM_FREQUENCY,
    color: Optional[ColorEnum] = COLOR,  # noqa: UP007
    brightness: float = BRIGHTNESS,
    verbose: int = VERBOSE,
    count: Optional[int] = Option(  # noqa: UP007
        None,
        "-c",
        "--count",
        help="Number of sprites",
    ),
    fade_steps: Optional[int] = Option(
        None,
        "-f",
        "--fade_steps",
        help="number of steps over which to fade to background",
    ),
) -> None:
    LOGGER.critical("Running %s function", sprite.__name__)
    gamma = None
    led_strip_type = None
    invert = False
    pwm_channel = 0
    if count is None:
        count = random.randint(1, 5)
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

    clr = None
    if color in PixelSequence.ALL_SEQUENCES:
        clr = PixelSequence.ALL_SEQUENCES[color](
            led_count=random.randint(
                1,
                array_controller.real_led_count,
            ),
        )
    elif color in SequenceName._member_map_:
        color_enum = SequenceName(color)
        clr = get_named_sequence(
            name=color_enum,
            led_count=random.randint(
                1,
                array_controller.real_led_count,
            ),
        )
    else:
        LOGGER.info("Color: %s", "default monthly sequence")
        clr = PixelSequence.get_monthly_color_sequence()
    try:
        TransformSprite.create(
            controller=array_controller,
            pixel_sequence=clr,
            instance_count=count,
            fade_steps=fade_steps,
        )
        array_controller.run(seconds_per_mode=None)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    except Exception:
        LOGGER.exception("LightBerries Demo failed")
    array_controller.__del__()
