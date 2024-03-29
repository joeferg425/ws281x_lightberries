#!/usr/bin/python3
from __future__ import annotations
import random
import time
from typing import Optional
from light_game import LightEvent, LightEventId, LightGame
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import GameObject, Player, Projectile, Enemy
import numpy as np
import logging

LOGGER = logging.getLogger(__name__)


class SpaceShip(Player):
    def __init__(
        self,
        x: int,
        y: int,
        color: np.ndarray[(3), np.int32] | None = None,
    ) -> None:
        if color is None:
            color = PixelColors.PSEUDO_RANDOM.array
        super().__init__(
            x=x,
            y=y,
            name=SpaceShip.__name__,
            color=color,
            has_gravity=False,
        )
        self.bullet_time = time.time()
        self.deathray_time = self.bullet_time
        self.color_time = self.bullet_time
        self.shield: Optional[Shield] = None


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
                if self.owner.shield is not None and self.owner.shield.dead:
                    self.owner.shield = Shield(self.owner)
            obj.point_value = 0
            if self.dead and self.id not in GameObject.dead_objects:
                self.shield._dead = True
                GameObject.dead_objects.append(self.shield.id)
                GameObject.dead_objects.append(self.id)


class SpaceEnemy(Enemy):
    def __init__(
        self,
        x: int,
        y: int,
        dx: float = 0,
        dy: float = 0,
        color: np.ndarray[3, np.int32] = PixelColors.RED.array,
        name: str = "space_enemy",
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=1,
            name=name,
            color=color,
            destructible=True,
            has_gravity=False,
            wrap=True,
            dx=dx,
            dy=dy,
        )


class ShieldEnemy(SpaceEnemy):
    def __init__(
        self,
        x: int,
        y: int,
        dx: float = 0,
        dy: float = 0,
        color: np.ndarray[3, np.int32] = PixelColors.ORANGE.array,
    ) -> None:
        super().__init__(x, y, dx, dy, color, name="ShieldEnemy")


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


class SpaceGame(LightGame):
    MAX_ENEMY_SPEED = 0.5
    BULLET_DELAY = 0.2
    MIN_BULLET_SPEED = 0.05
    ENEMY_DELAY = 1.5
    SHIELD_ENEMY_CHANCE = 10
    DEATH_RAY_DELAY = 3

    def __init__(self, lights: MatrixController):
        super().__init__(lights=lights)
        self.exiting = False
        self.enemy_delay = SpaceGame.ENEMY_DELAY
        self.enemy_time = time.time()
        self.players: dict[int, SpaceShip] = {}
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_spaceship)
        self.splash_screen("space", 20)

    def get_new_player(self, old_player: Optional[SpaceShip] = None) -> GameObject:
        color = PixelColors.PSEUDO_RANDOM.array
        if old_player is not None:
            color = old_player.color
        return SpaceShip(
            x=random.randint(0, self.lights.realLEDXaxisRange - 1),
            y=random.randint(0, self.lights.realLEDYaxisRange - 1),
            color=color,
        )

    def add_spaceship(self, event: LightEvent):
        self.players[event.controller_instance_id] = self.get_new_player()

    def run(self):
        while not self.exiting:
            self.enemy_delay = SpaceGame.ENEMY_DELAY * len(self.get_controllers())
            self.check_for_winner()
            self.respawn_dead_players()
            self.show_scores()
            for event in self.get_events():
                t = time.time()
                if event.controller_instance_id not in self.players:
                    self.players[event.controller_instance_id] = SpaceShip(0, 0)
                    self.players[event.controller_instance_id].health = 0
                    self.players[event.controller_instance_id].timestamp_death -= 20
                else:
                    ship = self.players[event.controller_instance_id]
                    controller = event.controller
                    if not ship.dead:
                        vector = controller.LS
                        if np.abs(vector.x) > SpaceGame.THRESHOLD:
                            ship.dx = vector.x
                        else:
                            ship.dx = 0
                        if np.abs(vector.y) > SpaceGame.THRESHOLD:
                            ship.dy = vector.y
                        else:
                            ship.dy = 0
                        ship.x_aim = controller.RS.x
                        ship.y_aim = controller.RS.y
                        if controller.LT > 0.0:
                            if (
                                abs(ship.y_aim) >= SpaceGame.MIN_BULLET_SPEED
                                and abs(ship.x_aim) >= SpaceGame.MIN_BULLET_SPEED
                                and time.time() - ship.deathray_time > SpaceGame.DEATH_RAY_DELAY
                            ) and not (self.pause):
                                if t - ship.deathray_time > SpaceGame.DEATH_RAY_DELAY:
                                    ship.deathray_time = t
                                    ship.timestamp_ready = t
                                    DeathRay(
                                        owner=ship,
                                    )
                        elif controller.RT > 0.0:
                            if (
                                (t - ship.bullet_time >= SpaceGame.BULLET_DELAY)
                                and (
                                    abs(ship.y_aim) >= SpaceGame.MIN_BULLET_SPEED
                                    and abs(ship.x_aim) >= SpaceGame.MIN_BULLET_SPEED
                                )
                                and not (self.pause)
                            ):
                                ship.bullet_time = t
                                Bullet(
                                    x=ship.x + ship.x_aim,
                                    y=ship.y + ship.y_aim,
                                    dx=ship.x_aim * 2,
                                    dy=ship.y_aim * 2,
                                    owner=ship,
                                )
                        elif event.event_id == LightEventId.ButtonStart:
                            if t - self.pause_time > SpaceGame.PAUSE_DELAY:
                                self.pause_time = t
                                self.pause = not self.pause
                        elif event.event_id == LightEventId.ButtonPower:
                            self.exiting = True
                            break
                        elif event.event_id == LightEventId.ButtonTop:
                            if t - ship.color_time > 0.15:
                                ship.color_time = t
                                ship.color = PixelColors.PSEUDO_RANDOM.array
            if time.time() - self.enemy_time >= self.enemy_delay and (self.first_render is True or self.pause is False):
                self.enemy_time = time.time()
                if random.randint(0, SpaceGame.SHIELD_ENEMY_CHANCE - 1) == SpaceGame.SHIELD_ENEMY_CHANCE - 1:
                    e = ShieldEnemy(
                        x=random.randint(0, self.lights.realLEDYaxisRange - 1),
                        y=random.randint(0, self.lights.realLEDXaxisRange - 1),
                        dx=random.uniform(-SpaceGame.MAX_ENEMY_SPEED, SpaceGame.MAX_ENEMY_SPEED),
                        dy=random.uniform(-SpaceGame.MAX_ENEMY_SPEED, SpaceGame.MAX_ENEMY_SPEED),
                    )
                else:
                    e = SpaceEnemy(
                        x=random.randint(0, self.lights.realLEDYaxisRange - 1),
                        y=random.randint(0, self.lights.realLEDXaxisRange - 1),
                        dx=random.uniform(-SpaceGame.MAX_ENEMY_SPEED, SpaceGame.MAX_ENEMY_SPEED),
                        dy=random.uniform(-SpaceGame.MAX_ENEMY_SPEED, SpaceGame.MAX_ENEMY_SPEED),
                    )
                failing = True
                while failing:
                    failing = False
                    for ship in self.players.values():
                        if abs(e.x - ship.x) < 5 and abs(e.y - ship.y) < 5:
                            failing = True
                            e.x = random.randint(0, self.lights.realLEDYaxisRange - 1)
                            e.y = random.randint(0, self.lights.realLEDXaxisRange - 1)
            self.check_end_game()
            self.update_game()


def run_space_game(lights: MatrixController):
    g = SpaceGame(lights=lights)
    try:
        g.run()
    except Exception as ex:  # noqa
        LOGGER.exception("oops")
    g.__del__()


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
    )

    run_space_game(lights)
