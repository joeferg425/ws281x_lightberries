#!/usr/bin/python3
from __future__ import annotations
import random
import numpy as np
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from lightberries.array_functions import ArrayFunction
import os
import pygame

# the number of pixels in the light string
PIXEL_ROW_COUNT = 32
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
    matrixCount=2,
    matrixShape=(16, 16),
)
x = int(lightControl.realLEDRowCount // 2)
y = int(lightControl.realLEDColumnCount // 2)

lightControl.virtualLEDBuffer[x, y, 1] = 255


class sprite:
    def __init__(self, x: int, y: int, dx: float, dy: float, bounded: bool = False) -> None:
        self._x = x
        self._y = y
        self.dx = dx
        self.dy = dy
        self.dead = False
        self.bounded = bounded

    @property
    def x(self) -> int:
        return round(self._x) % lightControl.realLEDRowCount

    @x.setter
    def x(self, value) -> None:
        self._x = value

    @property
    def y(self) -> int:
        return round(self._y) % lightControl.realLEDColumnCount

    @y.setter
    def y(self, value) -> None:
        self._y = value

    def go(self):
        self._x = self._x + self.dx
        self._y = self._y + self.dy
        if self.bounded and self._x > lightControl.realLEDRowCount - 1 or self._x < 0:
            self.dead = True
        if self.bounded and self._y > lightControl.realLEDColumnCount - 1 or self._y < 0:
            self.dead = True

    def __str__(self) -> str:
        return f"[{self.x},{self.y}]"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, sprite):
            return False
        else:
            return self.x == obj.x and self.y == obj.y


os.environ["SDL_VIDEODRIVER"] = "dummy"
ENEMY_SPEED_THRESHOLD = 0.2
color = PixelColors.GREEN
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
x_reticle = 0
y_reticle = 0
bullets: list[sprite] = []
enemies: list[sprite] = []
while True:
    # clock.tick(50)
    fade.run()
    events = list(pygame.event.get())
    for event in events:
        if "joy" in event.dict and "axis" in event.dict:
            # print(event.dict)
            if event.dict["axis"] == 0:
                y_change = -event.dict["value"]
            elif event.dict["axis"] == 1:
                x_change = event.dict["value"]
            elif event.dict["axis"] == 2:
                # if np.abs(event.dict["value"] > 0.25):
                y_reticle = -event.dict["value"]
            elif event.dict["axis"] == 3:
                # if np.abs(event.dict["value"] > 0.25):
                x_reticle = event.dict["value"]
            elif event.dict["axis"] == 5 and event.dict["value"] > 0.5:
                # if np.abs(x_reticle) > 0.25 and np.abs(y_reticle) > 0.25:
                bullets.append(
                    sprite(
                        round(x) % lightControl.realLEDRowCount,
                        round(y) % lightControl.realLEDColumnCount,
                        x_reticle,
                        y_reticle,
                        True,
                    )
                )
        # elif "joy" in event.dict and "button" in event.dict:
        #     if event.dict["button"] == 0:
        #         jjj = 0
        #         # bullets.append(
        #         #     (
        #         #         (round(x) % lightControl.realLEDRowCount, round(y) % lightControl.realLEDRowCount),
        #         #         (ceil(x_reticle), ceil(y_reticle)),
        #         #     )
        #         # )
        #     elif event.dict["button"] == 1:
        #         lightControl.virtualLEDBuffer *= 0
        #     elif event.dict["button"] == 2:
        #         lightControl.virtualLEDBuffer *= 0
        #         lightControl.virtualLEDBuffer[:, :] += PixelColors.random()
        #     elif event.dict["button"] == 9:
        #         fade.fadeAmount -= 0.05
        #         if fade.fadeAmount < 0.0:
        #             fade.fadeAmount = 0.0
        #     elif event.dict["button"] == 10:
        #         fade.fadeAmount += 0.05
        #         if fade.fadeAmount > 1.0:
        #             fade.fadeAmount = 1.0
    if np.abs(x_change) > THRESHOLD:
        x += x_change
    if np.abs(y_change) > THRESHOLD:
        y += y_change
    lightControl.virtualLEDBuffer[
        round(x) % lightControl.realLEDRowCount, round(y) % lightControl.realLEDColumnCount
    ] = color
    fizzled = []
    for bullet in bullets:
        bullet.go()
        if bullet.dead:
            fizzled.append(bullet)
        else:
            lightControl.virtualLEDBuffer[
                round(bullet.x) % lightControl.realLEDRowCount, round(bullet.y) % lightControl.realLEDColumnCount
            ] = PixelColors.BLUE
    for fizzle in fizzled:
        bullets.remove(fizzle)
    if len(enemies) == 0:
        enemy = sprite(
            random.randint(0, lightControl.realLEDRowCount - 1),
            random.randint(0, lightControl.realLEDColumnCount - 1),
            random.random(),
            random.random(),
        )
        if enemy.dx < 0.1:
            enemy.dx = 0.1
        elif enemy.dx > ENEMY_SPEED_THRESHOLD:
            enemy.dx = ENEMY_SPEED_THRESHOLD
        if enemy.dy < 0.1:
            enemy.dy = 0.1
        elif enemy.dy > ENEMY_SPEED_THRESHOLD:
            enemy.dy = ENEMY_SPEED_THRESHOLD
        enemies.append(enemy)
    dead_ones = []
    for enemy in enemies:
        enemy.go()
        if bullets:
            if enemy in bullets:
                enemy.dead = True
        if enemy.dead:
            dead_ones.append(enemy)
        else:
            lightControl.virtualLEDBuffer[
                round(enemy.x) % lightControl.realLEDRowCount, round(enemy.y) % lightControl.realLEDColumnCount
            ] = PixelColors.RED
    for dead in dead_ones:
        for i in range(-1, 2):
            for j in range(-1, 2):
                if (dead.x + i >= 0 and dead.x + i <= lightControl.realLEDRowCount - 1) and (
                    dead.y + j >= 0 and dead.y + j <= lightControl.realLEDColumnCount - 1
                ):
                    lightControl.virtualLEDBuffer[
                        dead.x + i,
                        dead.y + j,
                    ] = PixelColors.YELLOW

        enemies.remove(dead)

    lightControl.copyVirtualLedsToWS281X()
    lightControl.refreshLEDs()
