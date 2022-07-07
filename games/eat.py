#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
from lightberries.matrix_functions import MatrixFunction
from _game_objects import game_object, sprite, check_for_collisions, projectile, XboxButton, XboxJoystick
import os
import pygame
import numpy as np


class snake(sprite):
    snakes: dict[int, snake] = {}

    def __init__(
        self,
        x: int,
        y: int,
        tail_length: int = 2,
        speed: float = 0.1,
        max_speed: float = 1.5,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name="snake",
            color=color,
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
        self.color_change_time = time.time()
        self.bad_apple_time = time.time()
        self.bullet_time = time.time()
        self.score = 1
        if random.randint(0, 1):
            self.dx = self.speed * [-1, 1][random.randint(0, 1)]
        else:
            self.dy = self.speed * [-1, 1][random.randint(0, 1)]

    def collide(self, obj: "game_object", xys: list[tuple[int, int]]) -> None:
        if obj.name == "apple":
            self.tail_length += 2
            self.score += 0.5
        elif obj.name == "snake":
            if (self.x, self.y) in xys:
                self.collided.append(obj)
                self.collision_xys.append(xys)
                self.health -= obj.damage
                if self.dead and self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)
        elif obj.name == "bullet":
            pass
        elif obj.name == "bad apple":
            if obj.owner.id != self.id:
                self.collided.append(obj)
                self.collision_xys.append(xys)
                self.health -= obj.damage
                if self.dead and self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)
        else:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)

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
                if self.id not in game_object.dead_objects:
                    game_object.dead_objects.append(self.id)


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
        self.airborne = False
        self.bounded = True
        self.creation_time = time.time()
        self.expiration_delay = 10
        apple.apples[game_object.object_counter] = self

    @property
    def dead(self) -> bool:
        if self.collided:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            self._dead = True
        return self._dead

    def go(self):
        super().go()
        if time.time() - self.creation_time > self.expiration_delay:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            self._dead = True


class bad_apple(sprite):
    bad_apples: dict[int, bad_apple] = {}

    def __init__(
        self,
        x: int,
        y: int,
        owner: snake,
        color: np.ndarray[(3), np.int32] = PixelColors.WHITE.array,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=1,
            name="bad apple",
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
        bad_apple.bad_apples[game_object.object_counter] = self

    @property
    def dead(self) -> bool:
        if self.collided:
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)
            self._dead = True
        return self._dead

    def collide(self, obj: "game_object", xys: list[tuple[int, int]]) -> None:
        if self.owner.id != obj.id:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)

    def go(self):
        super().go()
        if time.time() - self.creation_time > self.expiration_delay:
            self._dead = True
            if self.id not in game_object.dead_objects:
                game_object.dead_objects.append(self.id)


def run_eat_game(lights: MatrixController) -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    game_object.frame_size_x = lights.realLEDXaxisRange
    game_object.frame_size_y = lights.realLEDYaxisRange
    pause = True
    PAUSE_DELAY = 0.3
    THRESHOLD = 0.05
    fade = ArrayFunction(lights, MatrixFunction.functionOff, ArrayPattern.DefaultColorSequenceByMonth())
    fade.fadeAmount = 0.3
    fade.color = PixelColors.OFF.array
    fadeFireworks = ArrayFunction(
        lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth()
    )
    fadeFireworks.fadeAmount = 0.3
    fadeFireworks.color = PixelColors.OFF.array
    players: dict[int, snake] = {}
    x_changes: dict[int, float] = {}
    y_changes: dict[int, float] = {}
    joysticks: dict[int, pygame.joystick.Joystick] = {}
    COLOR_CHANGE_DELAY = 0.2
    BAD_APPLE_DELAY = 0.5
    BULLET_DELAY = 0.5
    apple_delay = 2.0
    apple_time = time.time() - apple_delay
    START_SPEED = 0.4
    SNAKE_START_LENGTH = 3
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
    WIN_SCORE = int(lights.realLEDYaxisRange / 2)
    WIN_DURATION = 6
    pause_time = time.time()
    fake_pause_time = time.time() - 5
    fake_pause = False
    b9_time = time.time()
    b10_time = time.time() - 1
    FAKE_PAUSE_DELAY = 3
    READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.CYAN.array).array])
    NOT_READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.ORANGE.array).array])
    joystick_count = 0
    apples: list[sprite] = []

    pygame.init()
    pygame_quit = False
    while not pygame_quit:
        events = list(pygame.event.get())
        if joystick_count != pygame.joystick.get_count():
            if pygame.joystick.get_count() > joystick_count:
                joystick_count = pygame.joystick.get_count()
                for i in range(joystick_count - len(players)):
                    joysticks[len(players)] = pygame.joystick.Joystick(len(players))
                    joysticks[len(players)].init()
                    x_changes[len(players)] = 0.0
                    y_changes[len(players)] = 0.0
                    players[len(players)] = snake(
                        x=random.randint(0, lights.realLEDXaxisRange) - 1,
                        y=random.randint(0, lights.realLEDYaxisRange) - 1,
                        tail_length=SNAKE_START_LENGTH,
                        speed=START_SPEED,
                        max_speed=1.5,
                        color=PixelColors.pseudoRandom().array,
                    )
                    apple_delay = 1.5 / len(players)
            else:
                joystick_count = pygame.joystick.get_count()
                while len(players) > joystick_count:
                    players[len(players) - 1]._dead = True
                    joysticks[len(players) - 1].quit()
                    players.pop(len(players) - 1)
            if joystick_count == 0:
                pause = True
            else:
                pause = False
        if fake_pause and time.time() - fake_pause_time > FAKE_PAUSE_DELAY:
            pause = False
            fake_pause = False
        if any([player.score >= WIN_SCORE for player in players.values()]):
            for player in players.values():
                if player.score >= WIN_SCORE:
                    break
            if not win:
                win = True
                win_time = time.time()
                for firework in fireworks:
                    firework.color = Pixel(player.color).array
            for firework in fireworks:
                firework.run()
            lights.copyVirtualLedsToWS281X()
            lights.refreshLEDs()
            if time.time() - win_time > WIN_DURATION:
                win = False
                for i in players.keys():
                    players[i]._dead = True
                    players[i] = snake(
                        x=random.randint(0, lights.realLEDXaxisRange) * 1,
                        y=random.randint(0, lights.realLEDYaxisRange) * 1,
                        tail_length=SNAKE_START_LENGTH,
                        speed=START_SPEED,
                        max_speed=1.5,
                        color=players[i].color,
                    )
            fadeFireworks.run()
            continue
        else:
            fade.run()
        for index, player in players.items():
            if player.dead:
                delta = time.time() - player.death_timestamp
                if delta > player.respawn_delay:
                    color = player.color
                    players[index] = snake(
                        x=random.randint(0, lights.realLEDXaxisRange // 2),
                        y=random.randint(0, lights.realLEDYaxisRange // 2),
                        speed=START_SPEED,
                        max_speed=1.5,
                        color=color,
                        tail_length=SNAKE_START_LENGTH,
                    )
        for index, player in players.items():
            if index % 2 == 0:
                if index == 0:
                    x = 0
                else:
                    x = lights.realLEDYaxisRange - 1
                if time.time() - player.bullet_time >= BULLET_DELAY:
                    lights.virtualLEDBuffer[: int(player.score), x, :] = ArrayPattern.ColorTransitionArray(
                        int(player.score), READY
                    )
                else:
                    lights.virtualLEDBuffer[: int(player.score), x, :] = ArrayPattern.ColorTransitionArray(
                        int(player.score), NOT_READY
                    )
            else:
                if index == 1:
                    x = 0
                else:
                    x = lights.realLEDYaxisRange - 1
                if time.time() - player.bullet_time >= BULLET_DELAY:
                    lights.virtualLEDBuffer[-int(player.score) :, x, :] = ArrayPattern.ColorTransitionArray(
                        int(player.score), READY
                    )
                else:
                    lights.virtualLEDBuffer[-int(player.score) :, x, :] = ArrayPattern.ColorTransitionArray(
                        int(player.score), NOT_READY
                    )
        for event in events:
            if "joy" in event.dict and "axis" in event.dict:
                if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                    x_changes[event.dict["joy"]] = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
                    y_changes[event.dict["joy"]] = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.TRIGGER_RIGHT and event.dict["value"] > 0.5:
                    player = players[event.dict["joy"]]
                    if time.time() - player.bullet_time >= BULLET_DELAY and not (pause or fake_pause):
                        player.bullet_time = time.time()
                        projectile(
                            owner=player,
                            name="bullet",
                            x=player.x + (2 * player.x_direction),
                            y=player.y + (2 * player.y_direction),
                            dx=player.x_direction * 2,
                            dy=player.y_direction * 2,
                            color=PixelColors.BLUE.array,
                            size=0,
                        )
            if "joy" in event.dict and "button" in event.dict:
                if event.dict["button"] == XboxButton.A:
                    if time.time() - players[event.dict["joy"]].bad_apple_time > BAD_APPLE_DELAY:
                        players[event.dict["joy"]].bad_apple_time = time.time()
                        bad_apple(
                            x=players[event.dict["joy"]].tail[0][0],
                            y=players[event.dict["joy"]].tail[0][1],
                            color=players[event.dict["joy"]].color,
                            owner=players[event.dict["joy"]],
                        )
                elif event.dict["button"] == XboxButton.Y:
                    if time.time() - players[event.dict["joy"]].color_change_time > COLOR_CHANGE_DELAY:
                        players[event.dict["joy"]].color_change_time = time.time()
                        players[event.dict["joy"]].color = PixelColors.random().array
                elif event.dict["button"] == XboxButton.XBOX and event.dict["joy"] == 0:
                    pygame.quit()
                    pygame_quit = True
                    break
                elif event.dict["button"] == XboxButton.START:
                    if time.time() - pause_time > PAUSE_DELAY:
                        pause_time = time.time()
                        pause = not pause
                elif event.dict["button"] == XboxButton.UP and players[event.dict["joy"]].dy == 0:
                    y_changes[event.dict["joy"]] = -players[event.dict["joy"]].speed
                    x_changes[event.dict["joy"]] = 0
                elif event.dict["button"] == XboxButton.DOWN and players[event.dict["joy"]].dy == 0:
                    y_changes[event.dict["joy"]] = players[event.dict["joy"]].speed
                    x_changes[event.dict["joy"]] = 0
                elif event.dict["button"] == XboxButton.LEFT and players[event.dict["joy"]].dx == 0:
                    x_changes[event.dict["joy"]] = -players[event.dict["joy"]].speed
                    y_changes[event.dict["joy"]] = 0
                elif event.dict["button"] == XboxButton.RIGHT and players[event.dict["joy"]].dx == 0:
                    x_changes[event.dict["joy"]] = players[event.dict["joy"]].speed
                    y_changes[event.dict["joy"]] = 0
        if pygame_quit:
            game_object.dead_objects.extend(game_object.objects)
            break
        if time.time() - b9_time < 0.1 and time.time() - b10_time < 0.1:
            fake_pause = True
            fake_pause_time = time.time()
        for i in players.keys():
            if np.abs(x_changes[i]) > THRESHOLD or np.abs(y_changes[i]) > THRESHOLD:
                if np.abs(x_changes[i]) > np.abs(y_changes[i]):
                    if x_changes[i] > 0:
                        players[i].dx = players[i].speed
                    else:
                        players[i].dx = -players[i].speed
                    players[i].dy = 0
                else:
                    if y_changes[i] > 0:
                        players[i].dy = players[i].speed
                    else:
                        players[i].dy = -players[i].speed
                    players[i].dx = 0
        if (
            time.time() - apple_time >= apple_delay
            and not all([player.dead for player in players.values()])
            and not pause
            and not fake_pause
        ):
            apple_time = time.time()
            new_apple = apple(
                random.randint(0, lights.realLEDYaxisRange - 1),
                random.randint(0, lights.realLEDXaxisRange - 1),
                color=PixelColors.RED.array,
            )
            while any(
                [(abs(new_apple.x - player.x) < 5) and (abs(new_apple.y - player.y) < 5) for player in players.values()]
            ):
                new_apple.x = random.randint(0, lights.realLEDYaxisRange - 1)
                new_apple.y = random.randint(0, lights.realLEDXaxisRange - 1)
            apples.append(new_apple)
        if not pause:
            check_for_collisions()
            for obj in game_object.objects.values():
                try:
                    lights.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
                except:  # noqa
                    pass
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
    )
    while True:
        run_eat_game(lights)
