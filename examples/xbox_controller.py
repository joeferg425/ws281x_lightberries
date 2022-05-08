#!/usr/bin/python3
import numpy as np
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from lightberries.array_functions import ArrayFunction
import os
import pygame

# the number of pixels in the light string
PIXEL_ROW_COUNT = 16
PIXEL_COLUMN_COUNT = 16
# PIXEL_ROW_COUNT = 3
# PIXEL_COLUMN_COUNT = 5
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


# create the lightberries Controller object
lightControl = MatrixController(
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
)
x = int(lightControl.realLEDXaxisRange // 2)
y = int(lightControl.realLEDYaxisRange // 2)

lightControl.virtualLEDBuffer[x, y, 1] = 255

os.environ["SDL_VIDEODRIVER"] = "dummy"

color = PixelColors.RED
pygame.init()
joysticks = []
clock = pygame.time.Clock()
keepPlaying = True
THRESHOLD = 0.05
fade = ArrayFunction(ArrayFunction.functionFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
fade.fadeAmount = 0.3
for i in range(0, pygame.joystick.get_count()):
    joysticks.append(pygame.joystick.Joystick(i))
    joysticks[-1].init()
x_change = 0
y_change = 0
while True:
    # clock.tick(50)
    fade.run()
    events = list(pygame.event.get())
    for event in events:
        if "joy" in event.dict and "axis" in event.dict:
            if event.dict["axis"] == 0:
                y_change = -event.dict["value"]
            elif event.dict["axis"] == 1:
                x_change = event.dict["value"]
        elif "joy" in event.dict and "button" in event.dict:
            if event.dict["button"] == 0:
                color = PixelColors.random()
            elif event.dict["button"] == 1:
                lightControl.virtualLEDBuffer *= 0
            elif event.dict["button"] == 2:
                lightControl.virtualLEDBuffer *= 0
                lightControl.virtualLEDBuffer[:, :] += PixelColors.random()
            elif event.dict["button"] == 9:
                fade.fadeAmount -= 0.05
                if fade.fadeAmount < 0.0:
                    fade.fadeAmount = 0.0
            elif event.dict["button"] == 10:
                fade.fadeAmount += 0.05
                if fade.fadeAmount > 1.0:
                    fade.fadeAmount = 1.0
    if np.abs(x_change) > THRESHOLD:
        x += x_change
    if np.abs(y_change) > THRESHOLD:
        y += y_change
    lightControl.virtualLEDBuffer[
        round(x) % lightControl.realLEDXaxisRange, round(y) % lightControl.realLEDYaxisRange
    ] = color
    lightControl.copyVirtualLedsToWS281X()
    lightControl.refreshLEDs()
