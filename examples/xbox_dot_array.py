#!/usr/bin/python3
from __future__ import annotations
from lightberries.array_patterns import ArrayPattern
from lightberries.array_controller import ArrayController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
import os
import pygame
import numpy as np

COUNT = 1024
# COUNT = 512
# COUNT=1024
# the number of pixels in the light string
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

# create the lightberries Controller object
lightControl = ArrayController(
    ledCount=COUNT,
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


class sprite:
    def __init__(
        self,
        name: str,
        x: int = 0,
        dx: float = 0.0,
        bounded: bool = False,
        stop=False,
        size: int = 1,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        self.name = name
        self._x = x
        self.dx = dx
        self.stop = stop
        self.bounded = bounded
        self.size = size
        self.color = color

    @property
    def x(self) -> int:
        self._x = self._x % lightControl.realLEDCount
        return round(self._x)

    @property
    def xs(self) -> list[int]:
        xs = [round(self._x + i) % (lightControl.realLEDCount) for i in range(-self.size, self.size + 1)]
        xs.extend([round(self._x) % (lightControl.realLEDCount) for i in range(-self.size, self.size + 1)])
        return xs

    @x.setter
    def x(self, value) -> None:
        self._x = value

    def go(self):
        self._x = self._x + self.dx
        if self._x >= (lightControl.realLEDCount - 1) or self._x <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._x >= (lightControl.realLEDCount - 1):
                    self._x = lightControl.realLEDCount - 1
                elif self._x <= 0:
                    self._x = 0

    def __str__(self) -> str:
        return f"{self.name} [{self.x}]"

    def __repr__(self) -> str:
        return str(self.__class__.__name__) + " " + str(self)

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, (sprite, tuple)):
            return False
        elif isinstance(obj, tuple):
            return self.x == obj[0]
        else:
            return self.x == obj.x


os.environ["SDL_VIDEODRIVER"] = "dummy"
PAUSE_DELAY = 0.3
pygame.init()
keepPlaying = True
THRESHOLD = 0.05
fade = ArrayFunction(lightControl, ArrayFunction.functionFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
fade.fadeAmount = 0.3
fade.colorFade = int(0.3 * 256)
fade.color = PixelColors.OFF.array
player = sprite(
    "player",
    stop=True,
    color=PixelColors.GREEN.array,
)
joystick_count = 0
joystick = None
while True:
    events = list(pygame.event.get())
    if joystick_count != pygame.joystick.get_count():
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
        else:
            joystick.quit()
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            pause = True
        else:
            pause = False
    fade.run()
    for event in events:
        if "joy" in event.dict and "axis" in event.dict:
            if event.dict["axis"] == 0:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    player.dx = event.dict["value"]
                else:
                    player.dx = 0
    player.go()
    lightControl.virtualLEDBuffer[player.x] = Pixel(player.color).array
    lightControl.copyVirtualLedsToWS281X()
    lightControl.refreshLEDs()
