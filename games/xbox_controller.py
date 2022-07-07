#!/usr/bin/python3
import random
import numpy as np
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from lightberries.array_functions import ArrayFunction
import os
import pygame
from _game_objects import XboxButton, XboxJoystick


def run_xbox_controller_test(lights: MatrixController):
    os.environ["SDL_VIDEODRIVER"] = "dummy"

    SPEED = 1.5
    pygame.init()
    joysticks = []
    THRESHOLD = 0.05
    fade = ArrayFunction(lights, ArrayFunction.functionFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
    fade.fadeAmount = 0.3
    for i in range(0, pygame.joystick.get_count()):
        joysticks.append(pygame.joystick.Joystick(i))
        joysticks[-1].init()
    x1 = random.randint(0, lights.realLEDXaxisRange)
    x2 = random.randint(0, lights.realLEDXaxisRange)
    y1 = random.randint(0, lights.realLEDYaxisRange)
    y2 = random.randint(0, lights.realLEDYaxisRange)
    x1_change = 0
    x2_change = 0
    y1_change = 0
    y2_change = 0
    color1 = PixelColors.pseudoRandom().array
    color2 = PixelColors.pseudoRandom().array
    lights.virtualLEDBuffer[x1, y1] = color1
    lights.virtualLEDBuffer[x2, y2] = color2
    exiting = False
    while not exiting:
        fade.run()
        events = list(pygame.event.get())
        for event in events:
            if "joy" in event.dict and "axis" in event.dict:
                if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                    if np.abs(event.dict["value"]) > THRESHOLD:
                        x1_change = event.dict["value"] * SPEED
                    else:
                        x1_change = 0
                elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
                    if np.abs(event.dict["value"]) > THRESHOLD:
                        y1_change = event.dict["value"] * SPEED
                    else:
                        y1_change = 0
                elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_X:
                    if np.abs(event.dict["value"]) > THRESHOLD:
                        x2_change = event.dict["value"] * SPEED
                    else:
                        x2_change = 0
                elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_Y:
                    if np.abs(event.dict["value"]) > THRESHOLD:
                        y2_change = event.dict["value"] * SPEED
                    else:
                        y2_change = 0
            elif "joy" in event.dict and "button" in event.dict:
                if event.dict["button"] == XboxButton.A:
                    color1 = PixelColors.random().array
                elif event.dict["button"] == XboxButton.X:
                    color2 = PixelColors.random().array
                elif event.dict["button"] == XboxButton.B:
                    lights.virtualLEDBuffer *= 0
                elif event.dict["button"] == XboxButton.Y:
                    lights.virtualLEDBuffer *= 0
                    lights.virtualLEDBuffer[:, :] += PixelColors.random().array
                elif event.dict["button"] == XboxButton.XBOX:
                    exiting = True
                    break
                elif event.dict["button"] == XboxButton.BUMPER_RIGHT:
                    fade.fadeAmount -= 0.05
                    if fade.fadeAmount < 0.0:
                        fade.fadeAmount = 0.0
                elif event.dict["button"] == XboxButton.BUMPER_LEFT:
                    fade.fadeAmount += 0.05
                    if fade.fadeAmount > 1.0:
                        fade.fadeAmount = 1.0
        x1 += x1_change
        y1 += y1_change
        x2 += x2_change
        y2 += y2_change
        lights.virtualLEDBuffer[round(x1) % lights.realLEDXaxisRange, round(y1) % lights.realLEDYaxisRange] = color1
        lights.virtualLEDBuffer[round(x2) % lights.realLEDXaxisRange, round(y2) % lights.realLEDYaxisRange] = color2
        lights.copyVirtualLedsToWS281X()
        lights.refreshLEDs()


if __name__ == "__main__":
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
    BRIGHTNESS = 0.25
    # to understand the rest of these arguments read
    # their documentation: https://github.com/rpi-ws281x/rpi-ws281x-python
    GAMMA = None
    LED_STRIP_TYPE = None
    INVERT = False
    PWM_CHANNEL = 0
    MATRIX_LAYOUT = np.array(
        [
            [1, 2],
            [0, 3],
        ]
    )
    MATRIX_SHAPE = (16, 16)

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
        matrixLayout=MATRIX_LAYOUT,
        matrixShape=MATRIX_SHAPE,
    )
    while True:
        run_xbox_controller_test(lights)
