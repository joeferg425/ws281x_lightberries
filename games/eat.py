#!/usr/bin/python3
from __future__ import annotations
import random
import time
from typing import Optional, cast
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import GameObject, Sprite, Projectile, Player
import numpy as np
from light_game import LightEvent, LightEventId, LightGame, XboxController
import logging

LOGGER = logging.getLogger(__name__)


class Snake(Player):
    BASE_SPEED = 0.15
    BASE_GROWTH = 2

    def __init__(
        self,
        x: int,
        y: int,
        tail_length: int = 2,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name="snake",
            color=color,
            has_gravity=False,
        )
        self._speed = 0.1
        self.tail = [(x, y)]
        self.tail_length = tail_length
        self.color_change_time = time.time()
        self.bad_apple_time = time.time()
        self.bullet_time = time.time()
        self.powerup: Optional[Apple] = None
        self.score = 1
        self.x_change = 0.0
        self.y_change = 0.0
        if random.randint(0, 1):
            self.dx = self.speed * [-1, 1][random.randint(0, 1)]
        else:
            self.dy = self.speed * [-1, 1][random.randint(0, 1)]

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        if isinstance(obj, Apple):
            if (self.x, self.y) in xys:
                if isinstance(obj, BadApple):
                    self.powerup = None
                    if obj.owner.id != self.id:
                        self.collided.append(obj)
                        self.collision_xys.append(xys)
                        self.health -= obj.damage
                        if self.dead and self.id not in GameObject.dead_objects:
                            GameObject.dead_objects.append(self.id)
                else:
                    if self.powerup is None or not obj.name == "apple":
                        self.powerup = obj
                        self.timestamp_powerup = time.time()
                    self.tail_length += self.tail_growth
                    self.score += obj.point_value
            else:
                obj._dead = False
        elif obj.name == "snake":
            if (self.x, self.y) in xys:
                self.collided.append(obj)
                self.collision_xys.append(xys)
                self.health -= obj.damage
                if self.dead and self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
        elif obj.name == "bullet":
            pass
        else:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)

    @property
    def speed(self) -> float:
        if self.powerup is None:
            return self.BASE_SPEED + self._speed * int(self.tail_length / 5)
        else:
            return self.BASE_SPEED + self.powerup.speed * int(self.tail_length / 5)

    @property
    def tail_growth(self) -> int:
        if self.powerup is not None:
            return self.powerup.tail_growth
        else:
            return Snake.BASE_GROWTH

    @property
    def xs(self) -> list[int]:
        return [x for x, y in self.tail]

    @property
    def ys(self) -> list[int]:
        return [y for x, y in self.tail]

    @property
    def move_xs(self) -> list[tuple[int, int]]:
        return [x for x, y in self.tail]

    @property
    def move_ys(self) -> list[tuple[int, int]]:
        return [y for x, y in self.tail]

    def go(self):
        if self.powerup is not None:
            if time.time() - self.timestamp_powerup > self.powerup.powerup_duration:
                self.powerup._dead = True
                self.powerup = None
        last_x = self.x
        last_y = self.y
        if not self.dead and not GameObject.pause:
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
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)


class Apple(Sprite):
    EXPIRATION_DELAY = 12

    def __init__(
        self, x: int, y: int, color: np.ndarray[(3), np.int32] = PixelColors.RED.array, name: str = "apple"
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=1,
            name=name,
            color=color,
            has_gravity=False,
            destructible=True,
            damage=0,
        )
        self.animate = False
        self._dead = False
        self._dx = 0
        self._dy = 0
        self.airborne = False
        self.bounded = True
        self.creation_time = time.time()
        self.speed = Snake.BASE_SPEED
        self.tail_growth = Snake.BASE_GROWTH

    @property
    def dead(self) -> bool:
        if self.collided:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True
            self.color = PixelColors.YELLOW.array
        return self._dead

    def go(self):
        super().go()
        if time.time() - self.creation_time > Apple.EXPIRATION_DELAY:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True


class FastApple(Apple):
    def __init__(
        self, x: int, y: int, color: np.ndarray[3, np.int32] = PixelColors.GREEN.array, name: str = "fast apple"
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            color=color,
            name=name,
        )
        self.speed = Snake.BASE_SPEED * 2


class GrowyApple(Apple):
    def __init__(
        self,
        x: int,
        y: int,
        color: np.ndarray[3, np.int32] = PixelColors.CYAN2.array,
        name: str = "growy apple",
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            color=color,
            name=name,
        )
        self.tail_growth = 4
        self.speed = Snake.BASE_SPEED * 1.5


class BadApple(Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        owner: Snake,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
        name: str = "bad apple",
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=1,
            name=name,
            color=color,
            has_gravity=False,
            destructible=True,
            damage=10,
        )
        self.animate = False
        self._dead = False
        self._dx = 0
        self._dy = 0
        self.airborne = False
        self.bounded = True
        self.owner = owner
        self.creation_time = time.time()
        self.expiration_delay = 2.0
        self.powerup_duration = 5.0
        self.speed = int(Snake.BASE_SPEED / 2)
        self.tail_growth = 1

    @property
    def dead(self) -> bool:
        if self.collided:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True
        return self._dead

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        if self.owner.id != obj.id:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)

    def go(self):
        super().go()
        if time.time() - self.creation_time > self.expiration_delay:
            self._dead = True
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)


class EatGame(LightGame):
    COLOR_CHANGE_DELAY = 0.2
    BAD_APPLE_DELAY = 0.5
    BULLET_DELAY = 0.5
    START_SPEED = 0.45
    SNAKE_START_LENGTH = 3

    def __init__(self, lights: MatrixController) -> None:
        super().__init__(lights=lights)
        self.players: dict[int, Snake] = {}
        self.apple_delay = 2.0
        self.apple_time = time.time() - self.apple_delay
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_spaceship)
        self.splash_screen("eat", 20)

    def get_new_player(self, old_player: Snake | None) -> GameObject:
        color = PixelColors.WHITE.array
        if old_player is not None:
            color = old_player.color
        return Snake(
            x=random.randint(0, self.lights.realLEDXaxisRange - 1),
            y=random.randint(0, self.lights.realLEDYaxisRange - 1),
            color=color,
        )

    def add_spaceship(self, event: LightEvent):
        self.players[event.controller_instance_id] = self.get_new_player(None)

    def run(self):
        while not self.exiting:
            divisor = 1
            if len(self.get_controllers()):
                divisor = len(self.get_controllers())
            self.apple_delay = 1.5 / divisor
            self.check_for_winner()
            self.respawn_dead_players()
            self.show_scores()
            self.spawn_apple()
            for event in self.get_events():
                t = time.time()
                if event.controller_instance_id not in self.players:
                    self.players[event.controller_instance_id] = Snake(0, 0)
                    self.players[event.controller_instance_id].health = 0
                    self.players[event.controller_instance_id].timestamp_death -= 20
                else:
                    snake = self.players[event.controller_instance_id]
                    controller = cast("XboxController", event.controller)
                    if not snake.dead:
                        vector = controller.LS
                        snake.x_change = vector.x
                        snake.y_change = vector.x
                        if controller.RT > 0.0:
                            if t - snake.bullet_time >= EatGame.BULLET_DELAY and not self.pause:
                                snake.bullet_time = t
                                Projectile(
                                    owner=snake,
                                    name="bullet",
                                    x=snake.x + (2 * snake.x_direction),
                                    y=snake.y + (2 * snake.y_direction),
                                    dx=snake.x_direction * 2,
                                    dy=snake.y_direction * 2,
                                    color=PixelColors.BLUE.array,
                                    size=0,
                                )
                        if event.event_id == LightEventId.ButtonBottom:
                            if t - snake.bad_apple_time > EatGame.BAD_APPLE_DELAY:
                                snake.bad_apple_time = t
                                BadApple(
                                    x=snake.tail[0][0],
                                    y=snake.tail[0][1],
                                    color=snake.color,
                                    owner=snake,
                                )
                        elif event.event_id == LightEventId.ButtonTop:
                            if t - snake.color_change_time > EatGame.COLOR_CHANGE_DELAY:
                                snake.color_change_time = t
                                snake.color = PixelColors.RANDOM.array
                        elif event.event_id == LightEventId.ButtonPower and controller.controller.get_id() == 0:
                            # pygame.quit()
                            self.exiting = True
                            break
                        elif event.event_id == LightEventId.ButtonStart:
                            if t - self.pause_time > LightGame.PAUSE_DELAY:
                                self.pause_time = t
                                self.pause = not self.pause
                        elif event.event_id == LightEventId.HatUp and snake.dy == 0:
                            snake.y_change = -snake.speed
                            snake.x_change = 0
                        elif event.event_id == LightEventId.HatDown and snake.dy == 0:
                            snake.y_change = snake.speed
                            snake.x_change = 0
                        elif event.event_id == LightEventId.HatLeft and snake.dx == 0:
                            snake.x_change = -snake.speed
                            snake.y_change = 0
                        elif event.event_id == LightEventId.HatRight and snake.dx == 0:
                            snake.x_change = snake.speed
                            snake.y_change = 0
            for snake in self.players.values():
                if np.abs(snake.x_change) > LightGame.THRESHOLD or np.abs(snake.y_change) > LightGame.THRESHOLD:
                    if np.abs(snake.x_change) > np.abs(snake.y_change):
                        if snake.x_change > 0:
                            snake.dx = snake.speed
                        else:
                            snake.dx = -snake.speed
                        snake.dy = 0
                    else:
                        if snake.y_change > 0:
                            snake.dy = snake.speed
                        else:
                            snake.dy = -snake.speed
                        snake.dx = 0
            self.update_game()
            self.check_end_game()

    def spawn_apple(self):
        if time.time() - self.apple_time >= self.apple_delay and (
            self.first_render or (not all([player.dead for player in self.players.values()]) and not self.pause)
        ):
            self.apple_time = time.time()
            how_many = 2
            which = random.randint(0, how_many + 5)
            if which == 0:
                new_apple = FastApple(
                    random.randint(0, self.lights.realLEDYaxisRange - 1),
                    random.randint(0, self.lights.realLEDXaxisRange - 1),
                )
            elif which == 1:
                new_apple = GrowyApple(
                    random.randint(0, self.lights.realLEDYaxisRange - 1),
                    random.randint(0, self.lights.realLEDXaxisRange - 1),
                )
            else:
                new_apple = Apple(
                    random.randint(0, self.lights.realLEDYaxisRange - 1),
                    random.randint(0, self.lights.realLEDXaxisRange - 1),
                )
            while any(
                [
                    (abs(new_apple.x - snake.x) < 5) and (abs(new_apple.y - snake.y) < 5)
                    for snake in self.players.values()
                ]
            ):
                new_apple.x = random.randint(0, self.lights.realLEDYaxisRange - 1)
                new_apple.y = random.randint(0, self.lights.realLEDXaxisRange - 1)


def run_eat_game(lights: MatrixController):
    g = EatGame(lights=lights)
    try:
        g.run()
    except Exception as ex:  # noqa
        LOGGER.exception(EatGame.__name__)
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
        matrixShape=MATRIX_SHAPE,
        matrixLayout=MATRIX_LAYOUT,
        # simulate=True,
    )
    run_eat_game(lights)
