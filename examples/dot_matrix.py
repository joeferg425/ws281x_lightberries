#!/usr/bin/python3
from __future__ import annotations
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.matrix_functions import MatrixFunction
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
import os
import pygame
import numpy as np

COUNT = 1
# COUNT = 2
# COUNT=4
# the number of pixels in the light string
if COUNT == 1:
    PIXEL_ROW_COUNT = 16
    PIXEL_COLUMN_COUNT = 16
elif COUNT == 2:
    PIXEL_ROW_COUNT = 32
    PIXEL_COLUMN_COUNT = 16
elif COUNT == 4:
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
if COUNT == 1:
    MATRIX_LAYOUT = np.array(
        [
            [0],
        ]
    )
elif COUNT == 2:
    MATRIX_LAYOUT = np.array(
        [
            [1],
            [0],
        ]
    )
elif COUNT == 4:
    MATRIX_LAYOUT = np.array(
        [
            [1, 2],
            [0, 3],
        ]
    )
MATRIX_SHAPE = (16, 16)

# create the lightberries Controller object
lightControl = MatrixController(
    ledRowCount=PIXEL_ROW_COUNT,
    ledColumnCount=PIXEL_COLUMN_COUNT,
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


class sprite:
    def __init__(
        self,
        name: str,
        x: int = 0,
        y: int = 0,
        dx: float = 0.0,
        dy: float = 0.0,
        bounded: bool = False,
        stop=False,
        size: int = 1,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        self.name = name
        self._x = x
        self._y = y
        self.dx = dx
        self.dy = dy
        self.dead = False
        self.stop = stop
        self.bounded = bounded
        self.size = size
        self.color = color

    @property
    def x(self) -> int:
        self._x = self._x % lightControl.realLEDColumnCount
        return round(self._x)

    @property
    def xs(self) -> list[int]:
        xs = [round(self._x + i) % (lightControl.realLEDColumnCount) for i in range(-self.size, self.size + 1)]
        xs.extend([round(self._x) % (lightControl.realLEDColumnCount) for i in range(-self.size, self.size + 1)])
        return xs

    @x.setter
    def x(self, value) -> None:
        self._x = value

    @property
    def y(self) -> int:
        self._y = self._y % lightControl.realLEDRowCount
        return round(self._y)

    @property
    def ys(self) -> list[int]:
        ys = [round(self._y) % (lightControl.realLEDRowCount) for i in range(-self.size, self.size + 1)]
        ys.extend([round(self._y + i) % (lightControl.realLEDRowCount) for i in range(-self.size, self.size + 1)])
        return ys

    @y.setter
    def y(self, value) -> None:
        self._y = value

    @property
    def xy_ray(self) -> tuple[list[int], list[int]]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (lightControl.realLEDColumnCount - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (lightControl.realLEDRowCount - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) % (lightControl.realLEDColumnCount) for i in range(-1, 2)])
                xs.extend([round(rx) % (lightControl.realLEDColumnCount) for i in range(-1, 2)])
                ys.extend([round(ry) % (lightControl.realLEDRowCount) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) % (lightControl.realLEDRowCount) for i in range(-1, 2)])
        return xs, ys

    def go(self):
        self._x = self._x + self.dx
        self._y = self._y + self.dy
        if self._x >= (lightControl.realLEDColumnCount - 1) or self._x <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._x >= (lightControl.realLEDColumnCount - 1):
                    self._x = lightControl.realLEDColumnCount - 1
                elif self._x <= 0:
                    self._x = 0
        if self._y >= (lightControl.realLEDRowCount - 1) or self._y <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._y >= (lightControl.realLEDRowCount - 1):
                    self._y = lightControl.realLEDRowCount - 1
                elif self._y <= 0:
                    self._y = 0

    def __str__(self) -> str:
        return f"{self.name} [{self.x},{self.y}]"

    def __repr__(self) -> str:
        return str(self.__class__.__name__) + " " + str(self)

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, (sprite, tuple)):
            return False
        elif isinstance(obj, tuple):
            return self.x == obj[0] and self.y == obj[1]
        else:
            return self.x == obj.x and self.y == obj.y


os.environ["SDL_VIDEODRIVER"] = "dummy"
PAUSE_DELAY = 0.3
pygame.init()
keepPlaying = True
THRESHOLD = 0.05
fade = ArrayFunction(lightControl, MatrixFunction.functionMatrixFade, ArrayPattern.DefaultColorSequenceByMonth())
fade.fadeAmount = 0.3
fade.colorFade = int(0.3 * 256)
fade.color = PixelColors.OFF.array
x_change = 0
y_change = 0
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
            # print(event.dict)
            if event.dict["axis"] == 0:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    player.dx = event.dict["value"]
                else:
                    player.dx = 0.0
            if event.dict["axis"] == 1:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    player.dy = event.dict["value"]
                else:
                    player.dy = 0.0
    player.go()
    lightControl.virtualLEDBuffer[player.x, player.y] = Pixel(player.color).array
    lightControl.copyVirtualLedsToWS281X()
    lightControl.refreshLEDs()
