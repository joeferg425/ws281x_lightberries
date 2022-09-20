#!/usr/bin/python3
from __future__ import annotations
import random
import time
import logging
from typing import Optional
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import (
    GameObject,
    Floor,
    Player,
    Projectile,
    SpriteShape,
)
import pygame
import numpy as np
from light_game import LightEvent, LightEventId, LightGame

LOGGER = logging.getLogger(__name__)


# class PygameSprite(pygame.sprite.Sprite):
#     def __init__(self, top: int, left: int, width: int, height: int) -> None:
#         super().__init__()
#         self.surf = pygame.Surface((LightGame.SIMULATED_SIZE * width, LightGame.SIMULATED_SIZE * height))
#         self.surf.fill((128, 255, 40))
#         self.rect = self.surf.get_rect(topleft=((left * LightGame.SIMULATED_SIZE), top * LightGame.SIMULATED_SIZE))
#         self.rect.left = left * LightGame.SIMULATED_SIZE
#         self.rect.height = height * LightGame.SIMULATED_SIZE
#         self.rect.top = top * LightGame.SIMULATED_SIZE
#         self.rect.width = width * LightGame.SIMULATED_SIZE

#     def go(self, o: GameObject):
#         width = o.width + abs(o.left - o.left_last)
#         height = o.height + abs(o.top - o.top_last)
#         left = min(o.left, o.left_last)
#         top = min(o.top, o.top_last)
#         self.rect.width = width * LightGame.SIMULATED_SIZE
#         self.rect.left = left * LightGame.SIMULATED_SIZE
#         self.rect.height = height * LightGame.SIMULATED_SIZE
#         self.rect.top = top * LightGame.SIMULATED_SIZE


class Jumper(Player):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 3,
        name: str = "player",
        color: np.ndarray[3, np.int32] = PixelColors.ORANGE2.array,
        has_gravity: bool = True,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=size,
            name=name,
            color=color,
            has_gravity=has_gravity,
        )
        # self.p_sprite = PygameSprite(x, y, height=size, width=1)
        self.timestamp_color = time.time()
        self.timestamp_jump = time.time()
        self.timestamp_bullet = time.time()
        self.timestamp_color = time.time()
        self.falling = True
        self.shape = SpriteShape.SQUARE
        self.height = size
        self.width = 1
        self.color = color
        self.real_color = self.color

    def go(self):
        super().go()
        self.falling = True
        # self.p_sprite.go(self)

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        if not obj.owner == self:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
        if self.animate and not obj.owner == self:
            if not self.phased:
                if self.dy > 0:
                    if self.box.bottom > obj.box.top and self.box.top < obj.box.top:
                        self._y = int(obj.y - obj.height)
                        self.dy = 0
                elif self.dy < 0:
                    if self.box.top < obj.box.bottom and self.box.bottom > obj.box.bottom:
                        self._y = int(obj.y + self.height)
                        self.dy = 0

        self.falling = False
        self.jump_count = 0

    @property
    def dead(self) -> bool:
        was_dead = self._dead
        if self._dead:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.timestamp_death = time.time()
                self._dead = True
        elif self.health <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.timestamp_death = time.time()
                self._dead = True
        elif self.bounded:
            if self.x > (GameObject.frame_size_x - 1) or self.x < 0:
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.timestamp_death = time.time()
                    self._dead = True
            elif self.y > (GameObject.frame_size_y - 1):
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.timestamp_death = time.time()
                    self._dead = True
        if self._dead and not was_dead:
            self.color = PixelColors.YELLOW.array
        return self._dead

    @property
    def xs(self) -> list[int]:
        xs = np.array(super().xs)
        ys = np.array(super().ys)
        keep = np.where(ys >= 0)
        xs = xs[keep]
        keep = np.where(ys < GameObject.frame_size_y)
        xs = xs[keep]
        return [int(y) for y in xs]

    @property
    def ys(self) -> list[int]:
        ys = np.array(super().ys)
        keep = np.where(ys >= 0)
        ys = ys[keep]
        keep = np.where(ys < GameObject.frame_size_y)
        ys = ys[keep]
        return [int(y) for y in ys]


class Bullet(Projectile):
    def __init__(
        self,
        owner: GameObject,
        x: int,
        y: int,
        size: int = 1,
        name: str = "bullet",
        color: np.ndarray[3, np.int32] = PixelColors.BLUE.array,
        destructible: bool = True,
        bounded: bool = True,
        dx: float = 0,
        dy: float = 0,
    ) -> None:
        super().__init__(
            owner,
            x,
            y,
            size,
            name,
            color,
            destructible,
            bounded,
            dx,
            dy,
        )

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        self.dead = True
        print(obj)
        super().collide(obj, xys)


class Baddy(Player):
    SPEED = 0.5

    def __init__(
        self,
        x: int,
        y: int,
        jumpgame: JumpGame,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=4,
            name="baddy",
            color=PixelColors.RED.array,
            has_gravity=True,
        )
        self.height = self.size
        self.width = self.size
        self.shape = SpriteShape.SQUARE
        self.jumpgame = jumpgame

    def go(self):
        super().go()
        t = time.time()
        target = self.jumpgame.players[random.randint(0, len(self.jumpgame.players) - 1)]
        if self.collided:
            if not self.dx:
                if not target.dead:
                    self.timestamp_bullet = t
                    self.dx = Baddy.SPEED if target.x > self.x else -Baddy.SPEED
                else:
                    self._dead = True
        else:
            self.dx = 0.0

    @property
    def dead(self) -> bool:
        was_dead = self._dead
        if self._dead:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.timestamp_death = time.time()
                self._dead = True
        elif self.health <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.timestamp_death = time.time()
                self._dead = True
        elif self.bounded:
            if self.x > (GameObject.frame_size_x - 1) or self.x < 0:
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.timestamp_death = time.time()
                    self._dead = True
            elif self.y > (GameObject.frame_size_y - 1):
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.timestamp_death = time.time()
                    self._dead = True
        if self._dead and not was_dead:
            self.color = PixelColors.YELLOW.array
        return self._dead


class Platform(Floor):
    def __init__(
        self,
        x: int,
        y: int,
        dy: float,
        width: int,
        height: int = 1,
        name: str = "platform",
        color: np.ndarray[3, np.int32] = PixelColors.GREEN.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            height=height,
            width=width,
            name=name,
            color=color,
        )
        self.damage = 0
        # self.p_sprite = PygameSprite(x, y, width, height)
        self.dy = dy

    def go(self):
        self.x = self._x + self.dx
        self.y = self._y + self.dy
        # self.p_sprite.go(self)
        # self.p_sprite.rect.height = (self.height + self.dy) * LightGame.SIMULATED_SIZE
        # self.p_sprite.rect.top = self.y * LightGame.SIMULATED_SIZE
        if self.y > GameObject.frame_size_y:
            self.dead = True


class JumpGame(LightGame):
    THRESHOLD = 0.05
    WIN_DURATION = 10
    RESPAWN_DELAY = 1
    BULLET_DELAY = 0.2
    BADDY_DELAY = 5

    def __init__(self, lights: MatrixController) -> None:
        super().__init__(lights)
        self.players: dict[int, Jumper] = {}
        self.all_sprites = pygame.sprite.Group()
        self.platforms = []
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_player)
        self.splash_screen("jump", 20)
        self.timestamp_baddy = time.time()

    def get_new_player(self, old_player: Optional[Jumper] = None) -> GameObject:
        color = PixelColors.ORANGE2.array
        if old_player is not None:
            color = old_player.real_color
            if time.time() - old_player.timestamp_death > JumpGame.RESPAWN_DELAY:
                j = Jumper(
                    x=random.randint(3, int(GameObject.frame_size_x - 3)),
                    y=1,
                    color=color,
                )
            else:
                j = old_player
        else:
            j = Jumper(
                x=random.randint(3, int(GameObject.frame_size_x - 3)),
                y=1,
                color=color,
            )
        return j

    def spawn_platform(self):
        locations = {platform.y for platform in self.platforms}
        dead_ones = []
        for i in range(len(self.platforms)):
            if self.platforms[i].dead:
                dead_ones.append(i)
        for i in dead_ones:
            self.platforms.pop(i)
        if not locations or not {0, 1, 2, 3, 4, 5, 6} & locations:
            width = random.randint(3, int(GameObject.frame_size_x / 2))
            location = random.randint(0, GameObject.frame_size_x - width - 3)
            speed = [0.05, 0.1, 0.15, 0.2][random.randint(0, 3)]
            p = Platform(x=location, y=0, width=width, height=2, dy=speed)
            self.platforms.append(p)

    def spawn_baddy(self):
        t = time.time()
        if t - self.timestamp_baddy > JumpGame.BADDY_DELAY:
            self.timestamp_baddy = t
            location = random.randint(0, GameObject.frame_size_x - 3)
            Baddy(
                x=location,
                y=0,
                jumpgame=self,
            )

    def add_player(self, event: LightEvent):
        if event.controller_instance_id not in self.players:
            self.players[event.controller_instance_id] = self.get_new_player()

    def create_level(self):
        p = Platform(x=0, y=9, width=18, height=2, dy=0.1)
        self.platforms.append(p)

    def run(self):
        self.create_level()
        while not self.exiting:
            self.get_controllers()
            self.check_for_winner()
            self.respawn_dead_players()
            self.spawn_baddy()
            self.show_scores()
            for event in self.get_events():
                t = time.time()
                if event.controller_instance_id not in self.players:
                    self.add_player(event=event)
                player = self.players[event.controller_instance_id]
                controller = event.controller
                if not player.dead:
                    vector = controller.LS
                    if np.abs(vector.x) > JumpGame.THRESHOLD:
                        player.dx = vector.x
                    else:
                        player.dx = 0
                    player.x_aim = controller.RS.x
                    player.y_aim = controller.RS.y
                    if controller.RT > JumpGame.THRESHOLD:
                        if (t - player.timestamp_bullet >= JumpGame.BULLET_DELAY) and not (self.pause):
                            player.timestamp_bullet = t
                            Bullet(
                                x=player.x + player.x_aim_direction,
                                y=player.y + -1,
                                dx=player.x_aim * 2,
                                dy=player.y_aim * 2,
                                owner=player,
                            )
                    elif event.event_id == LightEventId.ButtonStart:
                        if t - self.pause_time > JumpGame.PAUSE_DELAY:
                            self.pause_time = t
                            self.pause = not self.pause
                    elif event.event_id == LightEventId.ButtonPower:
                        if t - self.timestamp_ready > 1:
                            self.exiting = True
                            break
                    elif event.event_id == LightEventId.ButtonTop:
                        if t - player.timestamp_color > 0.15:
                            player.timestamp_color = t
                            player.color = PixelColors.pseudoRandom().array
                            player.real_color = player.color
                    elif event.event_id == LightEventId.ButtonBottom:
                        if t - player.timestamp_jump > 0.25:
                            if player.dy > -8:
                                if player.jump_count < 2:
                                    player.jump_count += 1
                                    player.timestamp_jump = t
                                    if player.dy > 0:
                                        player.dy = -3.2
                                    else:
                                        player.dy -= 3.2
            self.spawn_platform()
            self.check_end_game()
            self.update_game()


def run_jump_game(lights: MatrixController):
    g = JumpGame(lights=lights)
    try:
        g.run()
    except:  # noqa
        LOGGER.exception("whoops")
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
    MATRIX_SHAPE = (16, 16)
    MATRIX_LAYOUT = np.array(
        [
            [1, 2],
            [0, 3],
        ],
    )

    SIMULATE = False
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
        simulate=SIMULATE,
        matrixShape=MATRIX_SHAPE,
        matrixLayout=MATRIX_LAYOUT,
    )
    while True:
        run_jump_game(lights)
