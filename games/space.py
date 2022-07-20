#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
from lightberries.matrix_functions import MatrixFunction
from _game_objects import XboxButton, XboxJoystick, GameObject, Player, Projectile, check_for_collisions, Enemy
import os
import pygame
import numpy as np


class SpaceShip(Player):
    def __init__(
        self,
        x: int,
        y: int,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            name=SpaceShip.__name__,
            color=PixelColors.pseudoRandom().array,
            has_gravity=False,
        )
        self.bullet_time = time.time()
        self.deathray_time = self.bullet_time
        self.color_time = self.bullet_time
        self.shield = Shield(self)
        self.shield._dead = True
        GameObject.dead_objects.append(self.shield.id)


class Bullet(Projectile):
    def __init__(
        self,
        owner: GameObject,
        x: int,
        y: int,
        dx: float = 0,
        dy: float = 0,
        size: int = 1,
    ) -> None:
        super().__init__(
            owner=owner,
            x=x,
            y=y,
            size=size,
            name="Bullet",
            color=PixelColors.BLUE.array,
            destructible=True,
            bounded=True,
            dx=dx,
            dy=dy,
        )

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        if obj.id != self.owner.id and (not obj.owner or self.owner.id != obj.owner.id):
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            self.owner.score += obj.point_value
            if isinstance(obj, ShieldEnemy) and isinstance(self.owner, SpaceShip):
                if self.owner.shield.dead:
                    self.owner.shield = Shield(self.owner)
            obj.point_value = 0
            if self.dead and self.id not in GameObject.dead_objects:
                self.shield._dead = True
                GameObject.dead_objects.append(self.shield.id)
                GameObject.dead_objects.append(self.id)


class SpaceEnemy(Enemy):
    SpaceEnemies: dict[int, SpaceEnemy] = {}

    def __init__(
        self,
        x: int,
        y: int,
        dx: float = 0,
        dy: float = 0,
        color: np.ndarray[3, np.int32] = PixelColors.RED.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=1,
            name="space_enemy",
            color=color,
            destructible=True,
            has_gravity=False,
            wrap=True,
            dx=dx,
            dy=dy,
        )
        SpaceEnemy.SpaceEnemies[GameObject.object_counter] = self

    @property
    def dead(self) -> bool:
        dead = super().dead
        if dead:
            self.color = PixelColors.YELLOW.array
        return dead


class ShieldEnemy(SpaceEnemy):
    def __init__(
        self,
        x: int,
        y: int,
        dx: float = 0,
        dy: float = 0,
        color: np.ndarray[3, np.int32] = PixelColors.ORANGE.array,
    ) -> None:
        super().__init__(
            x,
            y,
            dx,
            dy,
            color,
        )
        self.name = "ShieldEnemy"


class Shield(Projectile):
    def __init__(
        self,
        owner: GameObject,
    ) -> None:
        super().__init__(
            owner,
            x=0,
            y=0,
            size=3,
            name="Shield",
            color=PixelColors.CYAN3.array,
            destructible=True,
            bounded=False,
            dx=0.0,
            dy=0.0,
        )
        self.max_health = 3
        self.health = 3
        self.damage = 3

    @property
    def x(self) -> int:
        return self.owner.x

    @property
    def y(self) -> int:
        return self.owner.y

    @property
    def xs(self) -> list[int]:
        xs = (
            np.round(np.sin(np.linspace(0, 2 * np.pi, 1 + (4 * self.size))) * (self.size)).astype(dtype=np.int32)
            + self.x
        )
        xs = np.array(xs)
        fix = np.where(xs < 0)
        if fix:
            xs[fix] *= 0
        fix = np.where(xs >= GameObject.frame_size_x)
        if fix:
            xs[fix] *= 0
            xs[fix] += GameObject.frame_size_x
        return [int(x) for x in xs]

    @property
    def move_xs(self) -> list[int]:
        return self.xs

    @property
    def ys(self) -> list[int]:
        ys = (
            np.round(np.cos(np.linspace(0, 2 * np.pi, 1 + (4 * self.size))) * (self.size)).astype(dtype=np.int32)
            + self.y
        )
        ys = np.array(ys)
        fix = np.where(ys < 0)
        if fix:
            ys[fix] *= 0
        fix = np.where(ys >= GameObject.frame_size_y)
        if fix:
            ys[fix] *= 0
            ys[fix] += GameObject.frame_size_y
        return [int(y) for y in ys]

    @property
    def move_ys(self) -> list[int]:
        return self.ys

    def go(self):
        pass

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        if obj.id != self.owner.id and (not obj.owner or obj.owner.id != self.owner.id):
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            # self.owner.score += obj.point_value
            obj.point_value = 0
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)


class DeathRay(Projectile):
    death_rays: dict[int, DeathRay] = {}

    def __init__(
        self,
        owner: GameObject,
    ) -> None:
        super().__init__(
            owner=owner,
            x=0,
            y=0,
            size=1,
            name="death_ray",
            color=PixelColors.CYAN.array,
            destructible=False,
            dx=0.0,
            dy=0.0,
        )
        self.life_time = 0.3
        self.alternate = True
        self.score = 0
        self.damage = 3
        DeathRay.death_rays[GameObject.object_counter] = self

    def go(self):
        if self.alternate:
            self.color = PixelColors.CYAN.array
        else:
            self.color = PixelColors.MAGENTA.array
        self.alternate = not self.alternate
        if time.time() - self.timestamp_spawn > self.life_time:
            self._dead = True
            GameObject.dead_objects.append(self.id)

    @property
    def x(self) -> int:
        return self.owner.x

    @property
    def y(self) -> int:
        return self.owner.y

    @property
    def dx(self) -> int:
        return self.owner.x_aim

    @property
    def dy(self) -> int:
        return self.owner.y_aim

    @property
    def move_xs(self) -> list[int]:
        return self.xs

    @property
    def xs(self) -> list[int]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (GameObject.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (GameObject.frame_size_y - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) % (GameObject.frame_size_x) for i in range(-1, 2)])
                xs.extend([round(rx) % (GameObject.frame_size_x) for i in range(-1, 2)])
                ys.extend([round(ry) % (GameObject.frame_size_y) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) % (GameObject.frame_size_y) for i in range(-1, 2)])
        return xs

    @property
    def move_ys(self) -> list[int]:
        return self.ys

    @property
    def ys(self) -> list[int]:
        xs = [self.x]
        ys = [self.y]
        rx = self.x
        ry = self.y
        while (
            (GameObject.frame_size_x - 1) not in xs
            and 0 not in xs
            and 0 not in ys
            and (GameObject.frame_size_y - 1) not in ys
        ):
            rx += self.dx
            ry += self.dy
            if round(rx) not in xs or round(ry) not in ys:
                xs.extend([(round(rx) + i) % (GameObject.frame_size_x) for i in range(-1, 2)])
                xs.extend([round(rx) % (GameObject.frame_size_x) for i in range(-1, 2)])
                ys.extend([round(ry) % (GameObject.frame_size_y) for i in range(-1, 2)])
                ys.extend([(round(ry) + i) % (GameObject.frame_size_y) for i in range(-1, 2)])
        return ys

    def collide(self, obj: GameObject, xys: list[tuple[int, int]]) -> None:
        if obj.id != self.owner.id:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            self.owner.score += obj.point_value
            obj.point_value = 0
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)

    @property
    def dead(self) -> bool:
        return self._dead

    @dead.setter
    def dead(self, value: bool) -> None:
        pass


def run_space_game(lights: MatrixController):
    if not lights.testing:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    GameObject.frame_size_x = lights.realLEDXaxisRange
    GameObject.frame_size_y = lights.realLEDYaxisRange
    MAX_ENEMY_SPEED = 0.5
    PAUSE_DELAY = 0.3
    print("space")
    pygame.init()
    rs: list[pygame.Rect] = []
    if lights.testing:
        display = pygame.display.set_mode((lights.realLEDXaxisRange * 10, lights.realLEDYaxisRange * 10))
        display.fill((127, 127, 127))
        for i in range(32):
            for j in range(32):
                rs.append(
                    pygame.draw.rect(
                        display,
                        (0, 0, 0),
                        (((i * 10) + 1, (j * 10) + 1), (8, 8)),
                    )
                )
        pygame.display.flip()
    THRESHOLD = 0.05
    fade = ArrayFunction(lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
    fade.fadeAmount = 0.5
    fade.color = PixelColors.OFF.array
    BULLET_DELAY = 0.2
    MIN_BULLET_SPEED = 0.05
    ENEMY_DELAY = 1.5
    enemy_delay = ENEMY_DELAY
    SHIELD_ENEMY_CHANCE = 10
    enemy_time = time.time()
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
    WIN_SCORE = int(lights.realLEDYaxisRange // 2)
    WIN_DURATION = 10
    RESPAWN_DELAY = 1
    pause = True
    pause_time = time.time()
    DEATH_RAY_DELAY = 3
    exiting = False
    joysticks: dict[int, pygame.joystick.Joystick] = {}
    spaceships: dict[int, SpaceShip] = {}
    print(pygame.joystick.get_count())
    while not exiting:
        if len(joysticks) != pygame.joystick.get_count():
            if len(joysticks) < pygame.joystick.get_count() and pygame.joystick.get_count() <= 4:
                for i in range(0, pygame.joystick.get_count()):
                    if i not in joysticks:
                        joysticks[i] = pygame.joystick.Joystick(i)
                        joysticks[i].init()
                        spaceships[i] = SpaceShip(
                            x=random.randint(0, lights.realLEDXaxisRange),
                            y=random.randint(0, lights.realLEDYaxisRange),
                        )
            else:
                while len(spaceships) > pygame.joystick.get_count():
                    spaceships[len(spaceships) - 1]._dead = True
                    joysticks[len(spaceships) - 1].quit()
                    spaceships.pop(len(spaceships) - 1)
            if pygame.joystick.get_count() == 0:
                pause = True
            else:
                pause = False
        enemy_delay = ENEMY_DELAY * len(joysticks)
        if any([player.score >= WIN_SCORE for player in spaceships.values()]):
            if not win:
                for ship in spaceships.values():
                    if ship.score >= WIN_SCORE:
                        break
                win = True
                win_time = time.time()
                for firework in fireworks:
                    firework.color = Pixel(ship.color).array
            for firework in fireworks:
                firework.run()
            lights.copyVirtualLedsToWS281X()
            lights.refreshLEDs()
            if time.time() - win_time > WIN_DURATION:
                win = False
                for i in spaceships.keys():
                    spaceships[i].score = 0
                    spaceships[i]._dead = True
            fade.run()
            continue
        else:
            fade.run()
        for index, ship in spaceships.items():
            if ship.dead:
                if time.time() - ship.dead_time > RESPAWN_DELAY:
                    color = spaceships[index].color
                    spaceships[index] = SpaceShip(
                        x=random.randint(0, lights.realLEDYaxisRange - 1),
                        y=random.randint(0, lights.realLEDXaxisRange - 1),
                    )
                    spaceships[index].color = color
            ready = np.array([Pixel(PixelColors.GRAY.array).array, Pixel(ship.color).array])
            not_ready = np.array([Pixel(PixelColors.OFF.array).array, Pixel(ship.color).array])
            if index % 2 == 0:
                if index == 0:
                    x = 0
                else:
                    x = lights.realLEDYaxisRange - 1
                if time.time() - ship.deathray_time >= DEATH_RAY_DELAY:
                    lights.virtualLEDBuffer[: int(ship.score), x, :] = ArrayPattern.ColorTransitionArray(
                        int(ship.score), ready
                    )
                else:
                    lights.virtualLEDBuffer[: int(ship.score), x, :] = ArrayPattern.ColorTransitionArray(
                        int(ship.score), not_ready
                    )
            else:
                if index == 1:
                    x = 0
                else:
                    x = lights.realLEDYaxisRange - 1
                if ship.score > 0:
                    if time.time() - ship.deathray_time >= DEATH_RAY_DELAY:
                        lights.virtualLEDBuffer[-int(ship.score) :, x, :] = ArrayPattern.ColorTransitionArray(
                            int(ship.score), ready
                        )
                    else:
                        lights.virtualLEDBuffer[-int(ship.score) :, x, :] = ArrayPattern.ColorTransitionArray(
                            int(ship.score), not_ready
                        )
        # print(joysticks[0].get_axis(0))
        for event in pygame.event.get():
            if "joy" in event.dict:
                t = time.time()
                ship = spaceships[event.dict["joy"]]
                if not ship.dead:
                    if "axis" in event.dict:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            value = event.dict["value"]
                        else:
                            value = 0
                        if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                            ship.dx = value
                        elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
                            ship.dy = value
                        elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_X:
                            ship.x_aim = value
                        elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_Y:
                            ship.y_aim = value
                        elif event.dict["axis"] == XboxJoystick.TRIGGER_LEFT and event.dict["value"] > 0.5:
                            if (
                                abs(ship.y_aim) >= MIN_BULLET_SPEED
                                and abs(ship.x_aim) >= MIN_BULLET_SPEED
                                and time.time() - ship.deathray_time > DEATH_RAY_DELAY
                            ) and not (pause):
                                if t - ship.deathray_time > DEATH_RAY_DELAY:
                                    ship.deathray_time = t
                                    DeathRay(
                                        owner=ship,
                                    )
                        elif event.dict["axis"] == XboxJoystick.TRIGGER_RIGHT and value > 0.5:
                            if (
                                (t - ship.bullet_time >= BULLET_DELAY)
                                and (abs(ship.y_aim) >= MIN_BULLET_SPEED and abs(ship.x_aim) >= MIN_BULLET_SPEED)
                                and not (pause)
                            ):
                                ship.bullet_time = t
                                Bullet(
                                    x=ship.x + ship.x_aim,
                                    y=ship.y + ship.y_aim,
                                    dx=ship.x_aim * 2,
                                    dy=ship.y_aim * 2,
                                    owner=ship,
                                )
                    if "button" in event.dict:
                        if event.dict["button"] == XboxButton.START:
                            if t - pause_time > PAUSE_DELAY:
                                pause_time = t
                                pause = not pause
                        elif event.dict["button"] == XboxButton.XBOX:
                            exiting = True
                            break
                        elif event.dict["button"] == XboxButton.Y:
                            if t - ship.color_time > 0.15:
                                ship.color_time = t
                                ship.color = PixelColors.pseudoRandom().array
        if time.time() - enemy_time >= enemy_delay and not pause:  # and not fake_pause:
            enemy_time = time.time()
            if random.randint(0, SHIELD_ENEMY_CHANCE - 1) == SHIELD_ENEMY_CHANCE - 1:
                e = ShieldEnemy(
                    x=random.randint(0, lights.realLEDYaxisRange - 1),
                    y=random.randint(0, lights.realLEDXaxisRange - 1),
                    dx=random.uniform(-MAX_ENEMY_SPEED, MAX_ENEMY_SPEED),
                    dy=random.uniform(-MAX_ENEMY_SPEED, MAX_ENEMY_SPEED),
                )
            else:
                e = SpaceEnemy(
                    x=random.randint(0, lights.realLEDYaxisRange - 1),
                    y=random.randint(0, lights.realLEDXaxisRange - 1),
                    dx=random.uniform(-MAX_ENEMY_SPEED, MAX_ENEMY_SPEED),
                    dy=random.uniform(-MAX_ENEMY_SPEED, MAX_ENEMY_SPEED),
                )
            failing = True
            while failing:
                failing = False
                for ship in spaceships.values():
                    if abs(e.x - ship.x) < 5 and abs(e.y - ship.y) < 5:
                        failing = True
                        e.x = random.randint(0, lights.realLEDYaxisRange - 1)
                        e.y = random.randint(0, lights.realLEDXaxisRange - 1)
        if not pause:
            check_for_collisions()
            for obj in GameObject.objects.values():
                try:
                    lights.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
                except:  # noqa
                    pass
            if not lights.simulate:
                lights.copyVirtualLedsToWS281X()
                lights.refreshLEDs()
            else:
                counter = 0
                for row in lights.virtualLEDBuffer:
                    for column in row:
                        pygame.draw.rect(display, [int(x) for x in column], rs[counter])
                        counter += 1
                pygame.display.update()
                time.sleep(0.15)


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
    SIMULATE = True

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
        simulate=True,
        testing=True,
    )
    while True:
        run_space_game(lights=lights)
