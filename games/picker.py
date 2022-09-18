#!/usr/bin/python3
from __future__ import annotations
from lightberries.matrix_controller import MatrixController
import numpy as np
from eat import run_eat_game
from jump import run_jump_game
from space import run_space_game
from dots import run_dots_game
import logging

games = [
    run_eat_game,
    run_jump_game,
    run_space_game,
    run_dots_game,
]

LOGGER = logging.getLogger(__name__)


def run_picker():

    # the number of pixels in the light string
    PIXEL_ROW_COUNT = 32
    PIXEL_COLUMN_COUNT = 32
    # GPIO pin to use for PWM signal
    GPIO_PWM_PIN = 18
    # DMA channel
    DMA_CHANNEL = 10
    # frequency to run the PWM signal at
    PWM_FREQUENCY = 800000
    # brightness of LEDs in range [0.0, 1.0]
    BRIGHTNESS = 0.1
    # to understand the rest of these arguments read
    # their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    GAMMA = None
    LED_STRIP_TYPE = None
    INVERT = False
    PWM_CHANNEL = 0
    MATRIX_SHAPE = (16, 16)
    MATRIX_LAYOUT = np.array(
        [
            [1, 2],
            [0, 3],
        ],
    )

    # create the lightberries Controller object
    lights = MatrixController(
        ledXaxisRange=PIXEL_ROW_COUNT,
        ledYaxisRange=PIXEL_COLUMN_COUNT,
        pwmGPIOpin=GPIO_PWM_PIN,
        channelDMA=DMA_CHANNEL,
        frequencyPWM=PWM_FREQUENCY,
        channelPWM=PWM_CHANNEL,
        invertSignalPWM=INVERT,
        gamma=GAMMA,
        stripTypeLED=LED_STRIP_TYPE,
        ledBrightnessFloat=BRIGHTNESS,
        debug=True,
        matrixShape=MATRIX_SHAPE,
        matrixLayout=MATRIX_LAYOUT,
    )

    while True:
        for game in games:
            try:
                print(game)
                game(lights)
            except KeyboardInterrupt:
                raise
            except SystemExit:
                raise
            except Exception as ex:  # noqa
                LOGGER.exception(
                    "picker",
                )


if __name__ == "__main__":
    run_picker()
