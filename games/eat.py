#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
from lightberries.matrix_functions import MatrixFunction
from _game_objects import game_object, sprite, check_for_collisions
import os
import pygame
import numpy as np

pause = True


class snake(sprite):
    snakes: dict[int, snake] = {}

    def __init__(
        self,
        x: int,
        y: int,
        tail_length: int = 2,
        speed: float = 0.1,
        max_speed: float = 1.5,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name="snake",
            color=PixelColors.GREEN.array,
            has_gravity=False,
            destructible=True,
            bounded=True,
            dx=0.0,
            dy=0.0,
            phased=True,
        )
        snake.snakes[game_object.object_counter] = self
        self.speed_increment = 0.1
        self.speed_max = max_speed
        self.speed = speed
        self.tail = [(x, y)]
        self.tail_length = tail_length
        if random.randint(0, 1):
            self.dx = self.speed * [-1, 1][random.randint(0, 1)]
        else:
            self.dy = self.speed * [-1, 1][random.randint(0, 1)]

    @property
    def xs(self) -> list[int]:
        return [x for x, y in self.tail]

    @property
    def ys(self) -> list[int]:
        return [y for x, y in self.tail]

    def go(self):
        if self.collided:
            if self.collided[0].name == "apple":
                self.tail_length += 2
                self.collided.clear()
        last_x = self.x
        last_y = self.y
        if not self.dead and not game_object.pause:
            self.x = self._x + self.dx
            self.y = self._y + self.dy
        if self.x != last_x or self.y != last_y:
            if not (self.x, self.y) in self.tail:
                xs = [x for x, y in self.tail]
                ys = [y for x, y in self.tail]
                if len(self.tail) < self.tail_length:
                    xs += [self.x]
                    ys += [self.y]
                else:
                    xs = xs[1:] + [self.x]
                    ys = ys[1:] + [self.y]
                self.tail = list(zip(xs, ys))
            else:
                self._dead = True


class apple(sprite):
    apples: dict[int, apple] = {}

    def __init__(
        self,
        x: int,
        y: int,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=1,
            name="apple",
            color=color,
            has_gravity=False,
            destructible=True,
            damage=0,
        )
        self.animate = False
        self._dead = False
        self._dx = 0
        self._dy = 0
        self.airborn = False
        self.bounded = True
        apple.apples[game_object.object_counter] = self

    @property
    def dead(self) -> bool:
        if self.collided:
            return True


# the number of pixels in the light string
PIXEL_ROW_COUNT = 32
PIXEL_COLUMN_COUNT = 32
game_object.frame_size_x = PIXEL_COLUMN_COUNT
game_object.frame_size_y = PIXEL_ROW_COUNT
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
    matrixShape=MATRIX_SHAPE,
    matrixLayout=MATRIX_LAYOUT,
)


os.environ["SDL_VIDEODRIVER"] = "dummy"
MAX_apple_SPEED = 1.0
PAUSE_DELAY = 0.3
pygame.init()
THRESHOLD = 0.05
fade = ArrayFunction(lightControl, MatrixFunction.functionOff, ArrayPattern.DefaultColorSequenceByMonth())
fade.fadeAmount = 0.3
fade.colorFade = int(0.3 * 256)
fade.color = PixelColors.OFF.array
x_change = 0
y_change = 0
x_reticle = 0
y_reticle = 0
fizzled = []
dead_ones = []
BULLET_DELAY = 0.2
MIN_BULLET_SPEED = 0.2
MIN_apple_SPEED = 0.01
APPLE_DELAY = 2.0
bullet_time = time.time()
apple_time = time.time() - APPLE_DELAY
player1_dead_time = time.time()
score = 1
START_SPEED = 0.4
player1 = snake(
    x=random.randint(0, lightControl.realLEDXaxisRange // 2),
    y=random.randint(0, lightControl.realLEDYaxisRange // 2),
    tail_length=10,
    speed=START_SPEED,
    max_speed=1.5,
)
fireworks = []
for i in range(10):
    firework = MatrixFunction(lightControl, MatrixFunction.functionMatrixFireworks, ArrayPattern.RainbowArray(10))
    firework.rowIndex = random.randint(0, lightControl.realLEDXaxisRange - 1)
    firework.columnIndex = random.randint(0, lightControl.realLEDYaxisRange - 1)
    firework.size = 1
    firework.step = 1
    firework.sizeMax = min(int(lightControl.realLEDXaxisRange / 2), int(lightControl.realLEDYaxisRange / 2))
    firework.colorCycle = True
    for _ in range(i):
        firework.color = firework.colorSequenceNext
    fireworks.append(firework)
win = False
win_time = time.time()
WIN_SCORE = lightControl.realLEDYaxisRange
WIN_DURATION = 10
pause_time = time.time()
fake_pause_time = time.time() - 5
fake_pause = False
b9_time = time.time()
b10_time = time.time() - 1
death_ray_time = time.time() - 10
DEATH_RAY_DELAY = 3
FAKE_PAUSE_DELAY = 3
JUMP_DELAY = 0.3
jump_time = time.time() - JUMP_DELAY
READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.CYAN.array).array])
NOT_READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.ORANGE.array).array])
joystick_count = 0
joystick = None
DEATH_RAY_DURATION = 0.4
DEATH_RAY_FLICKER = 0.1
enemies: list[sprite] = []
apples: list[sprite] = []

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
    if fake_pause and time.time() - fake_pause_time > FAKE_PAUSE_DELAY:
        pause = False
        fake_pause = False

    if score >= WIN_SCORE:
        if not win:
            win = True
            win_time = time.time()
        for firework in fireworks:
            firework.run()
        fade.run()
        lightControl.copyVirtualLedsToWS281X()
        lightControl.refreshLEDs()
        if time.time() - win_time > WIN_DURATION:
            win = False
            score = 1
            player1.dead = True
        continue
    if player1.dead:
        delta = time.time() - player1_dead_time
        if delta > 1:
            player1._dead = True
            player1 = snake(
                x=random.randint(0, lightControl.realLEDXaxisRange // 2),
                y=random.randint(0, lightControl.realLEDYaxisRange // 2),
                speed=START_SPEED,
                max_speed=1.5,
            )
            # enemies.clear()
            # bullets.clear()
            fizzled.clear()
            dead_ones.clear()
            score = 1
            fade.color = PixelColors.OFF.array

    fade.run()
    # if time.time() - death_ray_time >= DEATH_RAY_DELAY:
    #     lightControl.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, READY)
    # else:
    #     lightControl.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, NOT_READY)
    for event in events:
        if "joy" in event.dict and "axis" in event.dict:
            if event.dict["axis"] == 0:
                x_change = event.dict["value"]
            elif event.dict["axis"] == 1:
                y_change = event.dict["value"]
            # elif event.dict["axis"] == 2:
            #     if np.abs(event.dict["value"]) > MIN_BULLET_SPEED:
            #         player1.x_aim = event.dict["value"] * 2
            # elif event.dict["axis"] == 3:
            #     if np.abs(event.dict["value"]) > MIN_BULLET_SPEED:
            #         player1.y_aim = event.dict["value"] * 2
            # elif event.dict["axis"] == 5 and event.dict["value"] > 0.5:
            #     if (
            #         (time.time() - bullet_time >= BULLET_DELAY)
            #         and not (pause or fake_pause)
            #         and (player1.x_aim != 0.0 and player1.y_aim != 0.0)
            #     ):
            #         bullet_time = time.time()
            #         # bullets.append(
            #         projectile(
            #             x=player1.x + player1.x_aim_direction,
            #             y=player1.y + player1.y_aim_direction,
            #             size=0,
            #             dx=player1.x_aim,
            #             dy=player1.y_aim,
            #         )
            #         # )
        if "joy" in event.dict and "button" in event.dict:
            if event.dict["button"] == 3:
                player1.color = PixelColors.random().array
            elif event.dict["button"] == 6:
                if time.time() - pause_time > PAUSE_DELAY:
                    pause_time = time.time()
                    pause = not pause
            elif event.dict["button"] == 11 and player1.dy == 0:
                y_change = -player1.speed
                x_change = 0
            elif event.dict["button"] == 12 and player1.dy == 0:
                y_change = player1.speed
                x_change = 0
            elif event.dict["button"] == 13 and player1.dx == 0:
                x_change = -player1.speed
                y_change = 0
            elif event.dict["button"] == 14 and player1.dx == 0:
                x_change = player1.speed
                y_change = 0
            # elif event.dict["button"] == 0:
            #     if time.time() - jump_time > JUMP_DELAY and player1.dy >= 0 and player1.jump_count < 2:
            #         player1.jump_count += 1
            #         jump_time = time.time()
            #         player1.dy -= 4.5
            #         if player1.dy < -4.5:
            #             player1.dy = -4.5
            # elif event.dict["button"] == 9:
            # b9_time = time.time()
            # elif event.dict["button"] == 10:
            # b10_time = time.time()
    if time.time() - b9_time < 0.1 and time.time() - b10_time < 0.1:
        fake_pause = True
        fake_pause_time = time.time()
    if np.abs(x_change) > THRESHOLD or np.abs(y_change) > THRESHOLD:
        if np.abs(x_change) > np.abs(y_change):
            if x_change > 0:
                player1.dx = player1.speed
            else:
                player1.dx = -player1.speed
            player1.dy = 0
        else:
            if y_change > 0:
                player1.dy = player1.speed
            else:
                player1.dy = -player1.speed
            player1.dx = 0
    if time.time() - apple_time >= APPLE_DELAY and not player1.dead and not pause and not fake_pause:
        apple_time = time.time()
        new_apple = apple(
            random.randint(0, lightControl.realLEDYaxisRange - 1),
            random.randint(0, lightControl.realLEDXaxisRange - 1),
            color=PixelColors.RED.array,
        )
        while abs(new_apple.x - player1.x) < 5 and abs(new_apple.y - player1.y) < 5:
            new_apple.x = random.randint(0, lightControl.realLEDYaxisRange - 1)
            new_apple.y = random.randint(0, lightControl.realLEDXaxisRange - 1)
        apples.append(new_apple)
    if not pause:
        check_for_collisions()
        for obj in game_object.objects.values():
            try:
                lightControl.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
            except:  # noqa
                pass
        lightControl.copyVirtualLedsToWS281X()
        lightControl.refreshLEDs()
        dead_ones.clear()
