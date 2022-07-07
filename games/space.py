#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
from lightberries.matrix_functions import MatrixFunction
from _game_objects import XboxButton, XboxJoystick
import os
import pygame
import numpy as np


class sprite:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        dx: float,
        dy: float,
        lights: MatrixController,
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
        self.lights = lights

    @property
    def x(self) -> int:
        self._x = self._x % self.lights.realLEDYaxisRange
        return round(self._x)

    @property
    def xs(self) -> list[int]:
        xs = [round(self._x + i) % (self.lights.realLEDYaxisRange) for i in range(-self.size, self.size + 1)]
        xs.extend([round(self._x) % (self.lights.realLEDYaxisRange) for i in range(-self.size, self.size + 1)])
        return xs

    @x.setter
    def x(self, value) -> None:
        self._x = value

    @property
    def y(self) -> int:
        self._y = self._y % self.lights.realLEDXaxisRange
        return round(self._y)

    @property
    def ys(self) -> list[int]:
        ys = [round(self._y) % (self.lights.realLEDXaxisRange) for i in range(-self.size, self.size + 1)]
        ys.extend([round(self._y + i) % (self.lights.realLEDXaxisRange) for i in range(-self.size, self.size + 1)])
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
            (self.lights.realLEDYaxisRange - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (self.lights.realLEDXaxisRange - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) % (self.lights.realLEDYaxisRange) for i in range(-1, 2)])
                xs.extend([round(rx) % (self.lights.realLEDYaxisRange) for i in range(-1, 2)])
                ys.extend([round(ry) % (self.lights.realLEDXaxisRange) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) % (self.lights.realLEDXaxisRange) for i in range(-1, 2)])
        return xs, ys

    def go(self):
        self._x = self._x + self.dx
        self._y = self._y + self.dy
        if self._x >= (self.lights.realLEDYaxisRange - 1) or self._x <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._x >= (self.lights.realLEDYaxisRange - 1):
                    self._x = self.lights.realLEDYaxisRange - 1
                elif self._x <= 0:
                    self._x = 0
        if self._y >= (self.lights.realLEDXaxisRange - 1) or self._y <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._y >= (self.lights.realLEDXaxisRange - 1):
                    self._y = self.lights.realLEDXaxisRange - 1
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


def run_space_game(lights: MatrixController):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    MAX_ENEMY_SPEED = 0.3
    PAUSE_DELAY = 0.3
    pygame.init()
    THRESHOLD = 0.05
    fade = ArrayFunction(lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
    fade.fadeAmount = 0.3
    fade.color = PixelColors.OFF.array
    x_change = 0
    y_change = 0
    x_reticle = 0
    y_reticle = 0
    bullets: list[sprite] = []
    enemies: list[sprite] = []
    fizzled = []
    dead_ones = []
    BULLET_DELAY = 0.2
    MIN_BULLET_SPEED = 0.05
    MIN_ENEMY_SPEED = 0.01
    ENEMY_DELAY = 2.0
    bullet_time = time.time()
    enemy_time = time.time()
    player_dead_time = time.time()
    score = 1
    player = sprite(
        "player",
        int(lights.realLEDYaxisRange // 2),
        int(lights.realLEDXaxisRange // 2),
        0,
        0,
        stop=True,
        color=PixelColors.GREEN.array,
        lights=lights,
    )
    fireworks = []
    for i in range(10):
        firework = MatrixFunction(lights, MatrixFunction.functionMatrixFireworks, ArrayPattern.RainbowArray(10))
        firework.rowIndex = random.randint(0, lights.realLEDXaxisRange - 1)
        firework.columnIndex = random.randint(0, lights.realLEDYaxisRange - 1)
        firework.size = 1
        firework.step = 1
        firework.sizeMax = min(int(lights.realLEDXaxisRange / 2), int(lights.realLEDYaxisRange / 2))
        firework.colorCycle = True
        for _ in range(i):
            firework.color = firework.colorSequenceNext
        fireworks.append(firework)
    win = False
    win_time = time.time()
    WIN_SCORE = lights.realLEDYaxisRange
    WIN_DURATION = 10
    pause = True
    pause_time = time.time()
    fake_pause_time = time.time() - 5
    fake_pause = False
    left_bumper_time = time.time()
    right_bumper_time = time.time() - 1
    death_rays = []
    death_ray_time = time.time() - 10
    DEATH_RAY_DELAY = 3
    FAKE_PAUSE_DELAY = 3
    READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.CYAN.array).array])
    NOT_READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.ORANGE.array).array])
    joystick_count = 0
    joystick = None
    DEATH_RAY_DURATION = 0.4
    exiting = False
    while not exiting:
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
            lights.copyVirtualLedsToWS281X()
            lights.refreshLEDs()
            if time.time() - win_time > WIN_DURATION:
                win = False
                score = 1
                player.dead = True
            continue
        if player.dead:
            delta = time.time() - player_dead_time
            if delta > 1:
                player.dead = False
                player.x = random.randint(0, lights.realLEDYaxisRange - 1)
                player.y = random.randint(0, lights.realLEDXaxisRange - 1)
                enemies.clear()
                bullets.clear()
                fizzled.clear()
                dead_ones.clear()
                score = 1
                fade.color = PixelColors.OFF.array

        fade.run()
        if time.time() - death_ray_time >= DEATH_RAY_DELAY:
            lights.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, READY)
        else:
            lights.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, NOT_READY)
        for event in events:
            if "joy" in event.dict and "axis" in event.dict:
                if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                    x_change = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
                    y_change = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_X:
                    x_reticle = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_Y:
                    y_reticle = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.TRIGGER_LEFT and event.dict["value"] > 0.5:
                    if (
                        abs(y_reticle) >= MIN_BULLET_SPEED
                        and abs(x_reticle) >= MIN_BULLET_SPEED
                        and time.time() - death_ray_time > DEATH_RAY_DELAY
                    ) and not (pause or fake_pause):
                        death_rays.append(
                            sprite(
                                "death ray",
                                player.x,
                                player.y,
                                x_reticle,
                                y_reticle,
                                bounded=True,
                                color=PixelColors.CYAN.array,
                                lights=lights,
                            )
                        )
                        death_ray_time = time.time()
                elif event.dict["axis"] == XboxJoystick.TRIGGER_RIGHT and event.dict["value"] > 0.5:
                    if (
                        (time.time() - bullet_time >= BULLET_DELAY)
                        and (abs(y_reticle) >= MIN_BULLET_SPEED and abs(x_reticle) >= MIN_BULLET_SPEED)
                        and not (pause or fake_pause)
                    ):
                        bullet_time = time.time()
                        bullets.append(
                            sprite(
                                "bullet",
                                player.x,
                                player.y,
                                x_reticle * 1.5,
                                y_reticle * 1.5,
                                bounded=True,
                                color=PixelColors.BLUE.array,
                                lights=lights,
                            )
                        )
            if "joy" in event.dict and "button" in event.dict:
                if event.dict["button"] == XboxButton.START:
                    if time.time() - pause_time > PAUSE_DELAY:
                        pause_time = time.time()
                        pause = not pause
                elif event.dict["button"] == XboxButton.XBOX:
                    exiting = True
                    break
                elif event.dict["button"] == XboxButton.BUMPER_LEFT:
                    left_bumper_time = time.time()
                elif event.dict["button"] == XboxButton.BUMPER_RIGHT:
                    right_bumper_time = time.time()
            if time.time() - left_bumper_time < 0.1 and time.time() - right_bumper_time < 0.1:
                fake_pause = True
                fake_pause_time = time.time()
        if np.abs(x_change) > THRESHOLD:
            player.dx = x_change
        else:
            player.dx = 0
        x_change * 0.5
        if np.abs(y_change) > THRESHOLD:
            player.dy = y_change
        else:
            player.dy = 0
        x_change * 0.5
        if not player.dead and not pause:
            player.go()
        lights.virtualLEDBuffer[player.x, player.y] = Pixel(player.color).array
        for bullet in bullets:
            if not player.dead and not (pause or fake_pause):
                bullet.go()
            if bullet.dead:
                fizzled.append(bullet)
            else:
                if not player.dead:
                    lights.virtualLEDBuffer[bullet.x, bullet.y] = Pixel(bullet.color).array
        for fizzle in fizzled:
            if fizzle in bullets:
                bullets.remove(fizzle)
        fizzled.clear()
        if time.time() - enemy_time >= ENEMY_DELAY and not player.dead and not pause and not fake_pause:
            enemy_time = time.time()
            enemy = sprite(
                "enemy",
                random.randint(0, lights.realLEDYaxisRange - 1),
                random.randint(0, lights.realLEDXaxisRange - 1),
                random.random() * random.uniform(-1.0, 1.0),
                random.random() * random.uniform(-1.0, 1.0),
                color=PixelColors.RED.array,
                lights=lights,
            )
            if abs(enemy.dx) < MIN_ENEMY_SPEED:
                if enemy.dx < 0:
                    enemy.dx = -MIN_ENEMY_SPEED
                else:
                    enemy.dx = MIN_ENEMY_SPEED
            elif abs(enemy.dx) > MAX_ENEMY_SPEED:
                if enemy.dx < 0:
                    enemy.dx = -MAX_ENEMY_SPEED
                else:
                    enemy.dx = MAX_ENEMY_SPEED
            if abs(enemy.dy) < MIN_ENEMY_SPEED:
                if enemy.dy < 0:
                    enemy.dy = -MIN_ENEMY_SPEED
                else:
                    enemy.dy = MIN_ENEMY_SPEED
            elif abs(enemy.dy) > MAX_ENEMY_SPEED:
                if enemy.dy < 0:
                    enemy.dy = -MAX_ENEMY_SPEED
                else:
                    enemy.dy = MAX_ENEMY_SPEED
            while abs(enemy.x - player.x) < 5 and abs(enemy.y - player.y) < 5:
                enemy.x = random.randint(0, lights.realLEDYaxisRange - 1)
                enemy.y = random.randint(0, lights.realLEDXaxisRange - 1)
            enemies.append(enemy)
        for death_ray in death_rays:
            # duration = int((time.time() - death_ray_time) / DEATH_RAY_FLICKER)
            death_ray.x = player.x
            death_ray.y = player.y
            if x_reticle > 0.0:
                death_ray.dx = x_reticle
            if y_reticle > 0.0:
                death_ray.dy = y_reticle
            rxs, rys = death_ray.xy_ray
            if np.array_equal(death_ray.color, PixelColors.MAGENTA.array):
                death_ray.color = PixelColors.CYAN.array
            else:
                death_ray.color = PixelColors.MAGENTA.array
            lights.virtualLEDBuffer[rxs, rys] = Pixel(death_ray.color).array
        for enemy in enemies:
            if not player.dead and not (pause or fake_pause):
                enemy.go()
                for xy in zip(enemy.xs, enemy.ys):
                    if xy == player:
                        player.dead = True
                        fade.color = Pixel(PixelColors.RED.array).array
                        player_dead_time = time.time()
                    if bullets:
                        for bullet in bullets:
                            if xy == bullet:
                                enemy.dead = True
                                score += 1
                                dead_ones.append(enemy)
                                fizzled.append(bullet)
                                break
                    if enemy.dead:
                        break
                    if death_rays:
                        for death_ray in death_rays:
                            rxs, rys = death_ray.xy_ray
                            rxy = list(zip(rxs, rys))
                            if xy in rxy:
                                enemy.dead = True
                                score += 1
                                dead_ones.append(enemy)
                    if enemy.dead:
                        break

            if not enemy.dead and not player.dead:
                lights.virtualLEDBuffer[enemy.xs, enemy.ys] = Pixel(enemy.color).array
        if time.time() - death_ray_time >= DEATH_RAY_DURATION:
            death_rays.clear()
        for dead in dead_ones:
            lights.virtualLEDBuffer[
                dead.xs,
                dead.ys,
            ] = Pixel(PixelColors.YELLOW.array).array
            if dead in enemies:
                try:
                    enemies.remove(dead)
                except:  # noqa
                    pass
        dead_ones.clear()
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
    BRIGHTNESS = 0.1
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
        run_space_game(lights=lights)
