#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
from lightberries.matrix_functions import MatrixFunction
import os
import pygame
import numpy as np

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


class sprite:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        dx: float,
        dy: float,
        bounded: bool = False,
        stop=False,
        size: int = 1,
        color: np.ndarray[(3), np.int32] = None,
        parent=None,
    ) -> None:
        self.name = name
        self._x = x
        self._y = y
        self.dx = dx
        self.dy = dy
        self.x_aim = 0.0
        self.y_aim = 0.0
        self.dead = False
        self.stop = stop
        self.bounded = bounded
        self.size = size
        if color is None:
            self.color = PixelColors.pseudoRandom().array
        else:
            self.color = color
        self.parent: sprite = parent
        self.score = 1

    @property
    def x(self) -> int:
        self._x = self._x % lightControl.realLEDYaxisRange
        return round(self._x)

    @property
    def xs(self) -> list[int]:
        xs = [round(self._x + i) % (lightControl.realLEDYaxisRange) for i in range(-self.size, self.size + 1)]
        xs.extend([round(self._x) % (lightControl.realLEDYaxisRange) for i in range(-self.size, self.size + 1)])
        return xs

    @x.setter
    def x(self, value) -> None:
        self._x = value

    @property
    def y(self) -> int:
        self._y = self._y % lightControl.realLEDXaxisRange
        return round(self._y)

    @property
    def ys(self) -> list[int]:
        ys = [round(self._y) % (lightControl.realLEDXaxisRange) for i in range(-self.size, self.size + 1)]
        ys.extend([round(self._y + i) % (lightControl.realLEDXaxisRange) for i in range(-self.size, self.size + 1)])
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
            (lightControl.realLEDYaxisRange - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (lightControl.realLEDXaxisRange - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) % (lightControl.realLEDYaxisRange) for i in range(-1, 2)])
                xs.extend([round(rx) % (lightControl.realLEDYaxisRange) for i in range(-1, 2)])
                ys.extend([round(ry) % (lightControl.realLEDXaxisRange) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) % (lightControl.realLEDXaxisRange) for i in range(-1, 2)])
        return xs, ys

    @property
    def xys(self):
        return zip(self.xs, self.ys)

    def go(self):
        self._x = self._x + self.dx
        self._y = self._y + self.dy
        if self._x >= (lightControl.realLEDYaxisRange - 1) or self._x <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._x >= (lightControl.realLEDYaxisRange - 1):
                    self._x = lightControl.realLEDYaxisRange - 1
                elif self._x <= 0:
                    self._x = 0
        if self._y >= (lightControl.realLEDXaxisRange - 1) or self._y <= 0:
            if self.bounded:
                self.dead = True
            elif self.stop:
                if self._y >= (lightControl.realLEDXaxisRange - 1):
                    self._y = lightControl.realLEDXaxisRange - 1
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
MAX_ENEMY_SPEED = 0.3
PAUSE_DELAY = 0.3
pygame.init()
# joysticks = []
# clock = pygame.time.Clock()
keepPlaying = True
THRESHOLD = 0.05
# fade = ArrayFunction(lightControl, ArrayFunction.functionFade, ArrayPattern.DefaultColorSequenceByMonth())
fade = ArrayFunction(lightControl, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
fade.fadeAmount = 0.3
fade.color = PixelColors.OFF.array
# fade.colorFade = int(0.3 * 256)
# fade.color = PixelColors.OFF.array
# for i in range(0, pygame.joystick.get_count()):
#     joysticks.append(pygame.joystick.Joystick(i))
#     joysticks[-1].init()
# x_change = 0
# y_change = 0
# x_reticle = 0
# y_reticle = 0
bullets: list[sprite] = []
enemies: list[sprite] = []
fizzled: list[sprite] = []
dead_ones: list[sprite] = []
BULLET_DELAY = 0.2
MIN_BULLET_SPEED = 0.05
MIN_ENEMY_SPEED = 0.01
ENEMY_DELAY = 8.0
p1_bullet_time = time.time()
p2_bullet_time = time.time()
enemy_time = time.time()
p1_dead_time = time.time()
p2_dead_time = time.time()
p1 = sprite(
    "player1",
    random.randint(0, (lightControl.realLEDYaxisRange - 1)),
    random.randint(0, (lightControl.realLEDXaxisRange - 1)),
    0,
    0,
    stop=True,
    size=0,
)
enemies.append(p1)
p2 = sprite(
    "player2",
    random.randint(0, (lightControl.realLEDYaxisRange - 1)),
    random.randint(0, (lightControl.realLEDXaxisRange - 1)),
    0,
    0,
    stop=True,
    size=0,
)
enemies.append(p2)
fireworks = []
for i in range(10):
    firework = MatrixFunction(lightControl, MatrixFunction.functionMatrixFireworks, ArrayPattern.RainbowArray(10))
    firework.rowIndex = random.randint(0, lightControl.realLEDYaxisRange - 1)
    firework.columnIndex = random.randint(0, lightControl.realLEDXaxisRange - 1)
    firework.size = 1
    firework.step = 1
    firework.sizeMax = min(int(lightControl.realLEDXaxisRange / 2), int(lightControl.realLEDYaxisRange / 2))
    firework.colorCycle = True
    for _ in range(i):
        firework.color = firework.colorSequenceNext
    fireworks.append(firework)
win = False
win_time = time.time()
WIN_SCORE = int(lightControl.realLEDYaxisRange // 2)
WIN_DURATION = 10
pause = True
pause_time = time.time()
fake_pause_time = time.time() - 5
fake_pause = False
p1_b9_time = time.time()
p1_b10_time = time.time() - 1
p2_b9_time = time.time()
p2_b10_time = time.time() - 1
death_rays: list[sprite] = []
p1_death_ray_time = time.time() - 10
p2_death_ray_time = time.time() - 10
DEATH_RAY_DELAY = 3
FAKE_PAUSE_DELAY = 3
READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.CYAN.array).array])
NOT_READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.ORANGE.array).array])
joystick_count = 0
joystick1 = None
joystick2 = None
RESPAWN_TIME = 3
DEATH_RAY_DURATION = 0.4
DEATH_RAY_FLICKER = 0.1
COLOR_CHANGE_DELAY = 0.2
p1_color_change_time = time.time() - COLOR_CHANGE_DELAY
p2_color_change_time = time.time() - COLOR_CHANGE_DELAY
while True:
    events = list(pygame.event.get())
    if joystick_count != pygame.joystick.get_count():
        if pygame.joystick.get_count() > 0:
            if joystick1 is None:
                joystick1 = pygame.joystick.Joystick(0)
                joystick1.init()
        elif joystick1 is not None:
            joystick1.quit()
            joystick1 = None
        if pygame.joystick.get_count() > 1:
            if joystick2 is None:
                joystick2 = pygame.joystick.Joystick(1)
                joystick2.init()
        elif joystick2 is not None:
            joystick2.quit()
            joystick2 = None
        joystick_count = pygame.joystick.get_count()
        if joystick_count < 2:
            pause = True
        else:
            pause = False
    if fake_pause and time.time() - fake_pause_time > FAKE_PAUSE_DELAY:
        pause = False
        fake_pause = False

    if p1.score >= WIN_SCORE or p2.score >= WIN_SCORE:
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
            p1.score = 1
            p1.dead = True
            p2.score = 1
            p2.dead = True
        continue
    if p1.dead and p2.dead:
        if time.time() - p1_dead_time > 1:
            p1.dead = False
            p1.x = random.randint(0, lightControl.realLEDYaxisRange - 1)
            p1.y = random.randint(0, lightControl.realLEDXaxisRange - 1)
            for enemy in enemies:
                if enemy.name == "enemy":
                    enemies.remove(enemy)
            bullets.clear()
            fizzled.clear()
            dead_ones.clear()
            p1.score = 1
            p2.score = 1
            fade.color = PixelColors.OFF.array
    elif p1.dead:
        if time.time() - p1_dead_time > RESPAWN_TIME:
            p1.dead = False
            p1.x = random.randint(0, lightControl.realLEDYaxisRange - 1)
            p1.y = random.randint(0, lightControl.realLEDXaxisRange - 1)
            p1.score = 1
            fade.color = PixelColors.OFF.array
    if p2.dead:
        if time.time() - p2_dead_time > RESPAWN_TIME:
            p2.dead = False
            p2.x = random.randint(0, lightControl.realLEDYaxisRange - 1)
            p2.y = random.randint(0, lightControl.realLEDXaxisRange - 1)
            p2.score = 1
            fade.color = PixelColors.OFF.array

    fade.run()
    if time.time() - p1_death_ray_time >= DEATH_RAY_DELAY:
        lightControl.virtualLEDBuffer[: p1.score, 0, :] = ArrayPattern.ColorTransitionArray(p1.score, READY)
    else:
        lightControl.virtualLEDBuffer[: p1.score, 0, :] = ArrayPattern.ColorTransitionArray(p1.score, NOT_READY)
    if time.time() - p2_death_ray_time >= DEATH_RAY_DELAY:
        lightControl.virtualLEDBuffer[-p2.score :, 0, :] = ArrayPattern.ColorTransitionArray(p2.score, READY)
    else:
        lightControl.virtualLEDBuffer[-p2.score :, 0, :] = ArrayPattern.ColorTransitionArray(p2.score, NOT_READY)
    for event in events:
        if "joy" in event.dict and "axis" in event.dict:
            # print(event.dict)
            if event.dict["axis"] == 0:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    if event.dict["joy"] == 0:
                        p1.dx = event.dict["value"]
                    else:
                        p2.dx = event.dict["value"]
                else:
                    if event.dict["joy"] == 0:
                        p1.dx = 0
                    else:
                        p2.dx = 0
            elif event.dict["axis"] == 1:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    if event.dict["joy"] == 0:
                        p1.dy = event.dict["value"]
                    else:
                        p2.dy = event.dict["value"]
                else:
                    if event.dict["joy"] == 0:
                        p1.dy = 0
                    else:
                        p2.dy = 0
            elif event.dict["axis"] == 2:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    if event.dict["joy"] == 0:
                        p1.x_aim = event.dict["value"]
                    else:
                        p2.x_aim = event.dict["value"]
            elif event.dict["axis"] == 3:
                if np.abs(event.dict["value"]) > THRESHOLD:
                    if event.dict["joy"] == 0:
                        p1.y_aim = event.dict["value"]
                    else:
                        p2.y_aim = event.dict["value"]
            elif event.dict["axis"] == 4 and event.dict["value"] > 0.5:
                if event.dict["joy"] == 0:
                    if (
                        abs(p1.x_aim) >= MIN_BULLET_SPEED
                        and abs(p1.y_aim) >= MIN_BULLET_SPEED
                        and time.time() - p1_death_ray_time > DEATH_RAY_DELAY
                    ) and not (pause or fake_pause):
                        death_rays.append(
                            sprite(
                                "death ray",
                                p1.x,
                                p1.y,
                                p1.x_aim,
                                p1.y_aim,
                                bounded=True,
                                color=PixelColors.CYAN.array,
                                parent=p1,
                            )
                        )
                        p1_death_ray_time = time.time()
                else:
                    if (
                        abs(p2.x_aim) >= MIN_BULLET_SPEED
                        and abs(p2.y_aim) >= MIN_BULLET_SPEED
                        and time.time() - p2_death_ray_time > DEATH_RAY_DELAY
                    ) and not (pause or fake_pause):
                        death_rays.append(
                            sprite(
                                "death ray",
                                p2.x,
                                p2.y,
                                p2.x_aim,
                                p2.y_aim,
                                bounded=True,
                                color=PixelColors.CYAN.array,
                                parent=p2,
                            )
                        )
                        p2_death_ray_time = time.time()
            elif event.dict["axis"] == 5 and event.dict["value"] > 0.5:
                if event.dict["joy"] == 0:
                    if (
                        (time.time() - p1_bullet_time >= BULLET_DELAY)
                        and (abs(p1.x_aim) >= MIN_BULLET_SPEED and abs(p1.y_aim) >= MIN_BULLET_SPEED)
                        and not (pause or fake_pause)
                    ):
                        p1_bullet_time = time.time()
                        bullets.append(
                            sprite(
                                "bullet",
                                p1.x,
                                p1.y,
                                p1.x_aim,
                                p1.y_aim,
                                bounded=True,
                                color=PixelColors.BLUE.array,
                                parent=p1,
                                size=1,
                            )
                        )
                else:
                    if (
                        (time.time() - p2_bullet_time >= BULLET_DELAY)
                        and (abs(p2.x_aim) >= MIN_BULLET_SPEED and abs(p2.y_aim) >= MIN_BULLET_SPEED)
                        and not (pause or fake_pause)
                    ):
                        p2_bullet_time = time.time()
                        bullets.append(
                            sprite(
                                "bullet",
                                p2.x,
                                p2.y,
                                p2.x_aim,
                                p2.y_aim,
                                bounded=True,
                                color=PixelColors.BLUE.array,
                                parent=p2,
                                size=1,
                            )
                        )
        if "joy" in event.dict and "button" in event.dict:
            if event.dict["button"] == 6:
                if time.time() - pause_time > PAUSE_DELAY:
                    pause_time = time.time()
                    pause = not pause
            # elif event.dict["button"] == 9:
            #     p1_b9_time = time.time()
            # elif event.dict["button"] == 10:
            #     p2_b10_time = time.time()
            elif event.dict["button"] == 2:
                if event.dict["joy"] == 0:
                    if time.time() - p1_color_change_time > COLOR_CHANGE_DELAY:
                        p1.color = PixelColors.pseudoRandom().array
                        p1_color_change_time = time.time()
                else:
                    if time.time() - p2_color_change_time > COLOR_CHANGE_DELAY:
                        p2.color = PixelColors.pseudoRandom().array
                        p2_color_change_time = time.time()
        if time.time() - p1_b9_time < 0.1 and time.time() - p2_b10_time < 0.1:
            fake_pause = True
            fake_pause_time = time.time()
    if not p1.dead and not pause:
        p1.go()
        lightControl.virtualLEDBuffer[p1.xs, p1.ys] = Pixel(p1.color).array
    if not p2.dead and not pause:
        p2.go()
        lightControl.virtualLEDBuffer[p2.xs, p2.ys] = Pixel(p2.color).array
    for fizzle in fizzled:
        if fizzle in bullets:
            bullets.remove(fizzle)
    fizzled.clear()
    for bullet in bullets:
        if not (pause or fake_pause):
            bullet.go()
        if bullet.dead:
            fizzled.append(bullet)
        else:
            lightControl.virtualLEDBuffer[bullet.x, bullet.y] = Pixel(bullet.color).array
            # lightControl.virtualLEDBuffer[bullet.xs, bullet.ys] = Pixel(bullet.color).array
    if time.time() - enemy_time >= ENEMY_DELAY and not p1.dead and not pause and not fake_pause:
        enemy_time = time.time()
        enemy = sprite(
            "enemy",
            random.randint(0, lightControl.realLEDYaxisRange - 1),
            random.randint(0, lightControl.realLEDXaxisRange - 1),
            random.random() * [-1, 1][random.randint(0, 1)],
            random.random() * [-1, 1][random.randint(0, 1)],
            color=PixelColors.RED.array,
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
        while abs(enemy.x - p1.x) < 5 and abs(enemy.y - p1.y) < 5:
            enemy.x = random.randint(0, lightControl.realLEDYaxisRange - 1)
            enemy.y = random.randint(0, lightControl.realLEDXaxisRange - 1)
        enemies.append(enemy)
    for death_ray in death_rays:
        # duration = int((time.time() - p1_death_ray_time) / DEATH_RAY_FLICKER)
        death_ray.x = death_ray.parent.x
        death_ray.y = death_ray.parent.y
        if death_ray.parent.x_aim > 0.0:
            death_ray.dx = death_ray.parent.x_aim
        if death_ray.parent.y_aim > 0.0:
            death_ray.dy = death_ray.parent.y_aim
        rxs, rys = death_ray.xy_ray
        if np.array_equal(death_ray.color, PixelColors.MAGENTA.array):
            death_ray.color = PixelColors.CYAN.array
        else:
            death_ray.color = PixelColors.MAGENTA.array
        lightControl.virtualLEDBuffer[rxs, rys] = Pixel(death_ray.color).array
    for index, enemy in enumerate(enemies):
        if not (pause or fake_pause):
            enemy.go()
            for xy in zip(enemy.xs, enemy.ys):
                for other_enemy in enemies[index + 1 :]:
                    if xy in other_enemy.xys and not other_enemy.dead:
                        enemy.dead = True
                        other_enemy.dead = True
                        if enemy == p1:
                            p1_dead_time = time.time()
                        elif enemy == p2:
                            p2_dead_time = time.time()
                        else:
                            dead_ones.append(enemy)
                        if other_enemy == p1:
                            p1_dead_time = time.time()
                        elif other_enemy == p2:
                            p2_dead_time = time.time()
                        else:
                            dead_ones.append(other_enemy)
                        break
                if bullets:
                    for bullet in bullets:
                        if xy in bullet.xys:
                            if bullet.parent is not None and not bullet.dead and not enemy.dead:
                                if enemy != p1 and bullet.parent == p1:
                                    # bullet.parent.score += 1
                                    enemy.dead = True
                                    p1.score += 1
                                    p2_dead_time = time.time()
                                    bullet.dead = True
                                    fizzled.append(bullet)
                                elif enemy != p2 and bullet.parent == p2:
                                    # bullet.parent.score += 1
                                    enemy.dead = True
                                    p2.score += 1
                                    p1_dead_time = time.time()
                                    bullet.dead = True
                                    fizzled.append(bullet)
                                elif enemy.name == "enemy":
                                    bullet.parent.score += 1
                                    enemy.dead = True
                                    dead_ones.append(enemy)
                                    bullet.dead = True
                                    fizzled.append(bullet)
                            break
                if enemy.dead:
                    break
                if death_rays:
                    for death_ray in death_rays:
                        rxs, rys = death_ray.xy_ray
                        rxy = list(zip(rxs, rys))
                        if xy in rxy:
                            if enemy != p1 and death_ray.parent == p1:
                                # death_ray.parent.score += 1
                                enemy.dead = True
                                p1.score += 1
                                p2_dead_time = time.time()
                                death_ray.dead = True
                                dead_ones.append(enemy)
                            elif enemy != p2 and death_ray.parent == p2:
                                # death_ray.parent.score += 1
                                enemy.dead = True
                                p2.score += 1
                                p1_dead_time = time.time()
                                death_ray.dead = True
                                fizzled.append(death_ray)
                if enemy.dead:
                    break

        if not enemy.dead:
            lightControl.virtualLEDBuffer[enemy.xs, enemy.ys] = Pixel(enemy.color).array
    for death_ray in death_rays:
        if death_ray.parent == p1:
            if time.time() - p1_death_ray_time >= DEATH_RAY_DURATION:
                death_rays.remove(death_ray)
        elif death_ray.parent == p2:
            if time.time() - p2_death_ray_time >= DEATH_RAY_DURATION:
                death_rays.remove(death_ray)
    for dead in dead_ones:
        lightControl.virtualLEDBuffer[
            dead.xs,
            dead.ys,
        ] = Pixel(PixelColors.YELLOW.array).array
        if dead in enemies:
            try:
                enemies.remove(dead)
            except:  # noqa
                pass
    dead_ones.clear()
    lightControl.copyVirtualLedsToWS281X()
    lightControl.refreshLEDs()
