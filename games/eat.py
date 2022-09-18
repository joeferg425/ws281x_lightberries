#!/usr/bin/python3
from __future__ import annotations
import random
import time
from typing import cast
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import GameObject, Sprite, Projectile
import numpy as np
from light_game import LightEvent, LightEventId, LightGame, XboxController


class Snake(Sprite):
    snakes: dict[int, Snake] = {}

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
        Snake.snakes[GameObject.object_counter] = self
        self.speed_increment = 0.1
        self.speed_max = max_speed
        self.speed = speed
        self.tail = [(x, y)]
        self.tail_length = tail_length
        self.color_change_time = time.time()
        self.bad_apple_time = time.time()
        self.bullet_time = time.time()
        self.score = 1
        self.x_change = 0.0
        self.y_change = 0.0
        if random.randint(0, 1):
            self.dx = self.speed * [-1, 1][random.randint(0, 1)]
        else:
            self.dy = self.speed * [-1, 1][random.randint(0, 1)]

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        if obj.name == "apple":
            self.tail_length += 2
            self.score += 0.5
        elif obj.name == "snake":
            if (self.x, self.y) in xys:
                self.collided.append(obj)
                self.collision_xys.append(xys)
                self.health -= obj.damage
                if self.dead and self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
        elif obj.name == "bullet":
            pass
        elif obj.name == "bad apple":
            if obj.owner.id != self.id:
                self.collided.append(obj)
                self.collision_xys.append(xys)
                self.health -= obj.damage
                if self.dead and self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
        else:
            self.collided.append(obj)
            self.collision_xys.append(xys)
            self.health -= obj.damage
            if self.dead and self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)

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
    apples: dict[int, Apple] = {}

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
        Apple.apples[GameObject.object_counter] = self

    @property
    def dead(self) -> bool:
        if self.collided:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True
        return self._dead

    def go(self):
        super().go()
        if time.time() - self.creation_time > self.expiration_delay:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            self._dead = True


class BadApple(Sprite):
    bad_apples: dict[int, BadApple] = {}

    def __init__(
        self,
        x: int,
        y: int,
        owner: Snake,
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
        BadApple.bad_apples[GameObject.object_counter] = self

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
    START_SPEED = 0.4
    SNAKE_START_LENGTH = 3

    def __init__(self, lights: MatrixController) -> None:
        super().__init__(lights=lights)
        # os.environ["SDL_VIDEODRIVER"] = "dummy"
        # GameObject.frame_size_x = lights.realLEDXaxisRange
        # GameObject.frame_size_y = lights.realLEDYaxisRange
        # pause = True
        # PAUSE_DELAY = 0.3
        # THRESHOLD = 0.05
        # fade = ArrayFunction(lights, MatrixFunction.functionOff, ArrayPattern.DefaultColorSequenceByMonth())
        # fade.fadeAmount = 0.3
        # fade.color = PixelColors.OFF.array
        # fadeFireworks = ArrayFunction(
        #     lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth()
        # )
        # fadeFireworks.fadeAmount = 0.3
        # fadeFireworks.color = PixelColors.OFF.array
        self.players: dict[int, Snake] = {}
        # x_changes: dict[int, float] = {}
        # y_changes: dict[int, float] = {}
        # joysticks: dict[int, pygame.joystick.Joystick] = {}
        self.apple_delay = 2.0
        self.apple_time = time.time() - self.apple_delay
        # fireworks = []
        # for i in range(10):
        #     firework = MatrixFunction(lights, MatrixFunction.functionMatrixFireworks, ArrayPattern.RainbowArray(10))
        #     firework.rowIndex = random.randint(0, lights.realLEDXaxisRange - 1)
        #     firework.columnIndex = random.randint(0, lights.realLEDYaxisRange - 1)
        #     firework.size = 1
        #     firework.step = 1
        #     firework.sizeMax = min(int(lights.realLEDXaxisRange / 2), int(lights.realLEDYaxisRange / 2))
        #     firework.colorCycle = True
        #     for _ in range(i):
        #         firework.color = firework.colorSequenceNext
        #     fireworks.append(firework)
        # win = False
        # win_time = time.time()
        # WIN_SCORE = int(lights.realLEDYaxisRange / 2)
        # WIN_DURATION = 6
        # pause_time = time.time()
        # fake_pause_time = time.time() - 5
        # fake_pause = False
        # b9_time = time.time()
        # b10_time = time.time() - 1
        # FAKE_PAUSE_DELAY = 3
        # READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.CYAN.array).array])
        # NOT_READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.ORANGE.array).array])
        # joystick_count = 0
        # apples: list[Sprite] = []

        # pygame.init()
        # pygame_quit = False
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_spaceship)

    def get_new_player(self) -> GameObject:
        return Snake(
            x=random.randint(0, self.lights.realLEDXaxisRange - 1),
            y=random.randint(0, self.lights.realLEDYaxisRange - 1),
        )

    def add_spaceship(self, event: LightEvent):
        self.players[event.controller_instance_id] = self.get_new_player()

    def run(self):
        while not self.exiting:
            self.apple_delay = 1.5 / len(self.get_controllers())
            # self.g
            # if joystick_count != pygame.joystick.get_count():
            #     if pygame.joystick.get_count() > joystick_count:
            #         joystick_count = pygame.joystick.get_count()
            #         for i in range(joystick_count - len(players)):
            #             joysticks[len(players)] = pygame.joystick.Joystick(len(players))
            #             joysticks[len(players)].init()
            #             x_changes[len(players)] = 0.0
            #             y_changes[len(players)] = 0.0
            #             players[len(players)] = Snake(
            #                 x=random.randint(0, lights.realLEDXaxisRange) - 1,
            #                 y=random.randint(0, lights.realLEDYaxisRange) - 1,
            #                 tail_length=SNAKE_START_LENGTH,
            #                 speed=START_SPEED,
            #                 max_speed=1.5,
            #                 color=PixelColors.pseudoRandom().array,
            #             )
            #     else:
            #         joystick_count = pygame.joystick.get_count()
            #         while len(players) > joystick_count:
            #             players[len(players) - 1]._dead = True
            #             joysticks[len(players) - 1].quit()
            #             players.pop(len(players) - 1)
            #     if joystick_count == 0:
            #         pause = True
            #     else:
            #         pause = False
            # if fake_pause and time.time() - fake_pause_time > FAKE_PAUSE_DELAY:
            #     pause = False
            #     fake_pause = False
            self.check_for_winner()
            # if any([player.score >= WIN_SCORE for player in players.values()]):
            #     for player in players.values():
            #         if player.score >= WIN_SCORE:
            #             break
            #     if not win:
            #         win = True
            #         win_time = time.time()
            #         for firework in fireworks:
            #             firework.color = Pixel(player.color).array
            #     for firework in fireworks:
            #         firework.run()
            #     lights.copyVirtualLedsToWS281X()
            #     lights.refreshLEDs()
            #     if time.time() - win_time > WIN_DURATION:
            #         win = False
            #         for i in players.keys():
            #             players[i]._dead = True
            #             players[i] = Snake(
            #                 x=random.randint(0, lights.realLEDXaxisRange) * 1,
            #                 y=random.randint(0, lights.realLEDYaxisRange) * 1,
            #                 tail_length=SNAKE_START_LENGTH,
            #                 speed=START_SPEED,
            #                 max_speed=1.5,
            #                 color=players[i].color,
            #             )
            #     fadeFireworks.run()
            #     continue
            # else:
            #     fade.run()
            self.respawn_dead_players()
            # for index, player in players.items():
            # if player.dead:
            #     delta = time.time() - player.timestamp_death
            #     if delta > player.respawn_delay:
            #         color = player.color
            #         players[index] = Snake(
            #             x=random.randint(0, lights.realLEDXaxisRange // 2),
            #             y=random.randint(0, lights.realLEDYaxisRange // 2),
            #             speed=START_SPEED,
            #             max_speed=1.5,
            #             color=color,
            #             tail_length=SNAKE_START_LENGTH,
            #         )
            # if index % 2 == 0:
            #     if index == 0:
            #         x = 0
            #     else:
            #         x = lights.realLEDYaxisRange - 1
            #     if time.time() - player.bullet_time >= BULLET_DELAY:
            #         lights.virtualLEDBuffer[: int(player.score), x, :] = ArrayPattern.ColorTransitionArray(
            #             int(player.score), READY
            #         )
            #     else:
            #         lights.virtualLEDBuffer[: int(player.score), x, :] = ArrayPattern.ColorTransitionArray(
            #             int(player.score), NOT_READY
            #         )
            # else:
            self.show_scores()
            # if index == 1:
            #     x = 0
            # else:
            #     x = lights.realLEDYaxisRange - 1
            # if time.time() - player.bullet_time >= BULLET_DELAY:
            #     lights.virtualLEDBuffer[-int(player.score) :, x, :] = ArrayPattern.ColorTransitionArray(
            #         int(player.score), READY
            #     )
            # else:
            # lights.virtualLEDBuffer[-int(player.score) :, x, :] = ArrayPattern.ColorTransitionArray(
            # int(player.score), NOT_READY
            # )
            for event in self.get_events():
                t = time.time()
                if event.controller_instance_id not in self.players:
                    self.players[event.controller_instance_id] = Snake(0, 0)
                    self.players[event.controller_instance_id].health = 0
                    self.players[event.controller_instance_id].timestamp_death -= 20
                else:
                    snake = self.players[event.controller_instance_id]
                    controller = cast("XboxController", event.controller)
                    # print(event)
                    if not snake.dead:
                        vector = controller.LS
                        # if "joy" in event.dict and "axis" in event.dict:
                        # if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                        snake.x_change = vector.x
                        # elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
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
                        # if "joy" in event.dict and "button" in event.dict:
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
                                snake.color = PixelColors.random().array
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
            if (
                time.time() - self.apple_time >= self.apple_delay
                and not all([player.dead for player in self.players.values()])
                and not self.pause
            ):
                self.apple_time = time.time()
                new_apple = Apple(
                    random.randint(0, self.lights.realLEDYaxisRange - 1),
                    random.randint(0, self.lights.realLEDXaxisRange - 1),
                    color=PixelColors.RED.array,
                )
                while any(
                    [
                        (abs(new_apple.x - snake.x) < 5) and (abs(new_apple.y - snake.y) < 5)
                        for snake in self.players.values()
                    ]
                ):
                    new_apple.x = random.randint(0, self.lights.realLEDYaxisRange - 1)
                    new_apple.y = random.randint(0, self.lights.realLEDXaxisRange - 1)
                # self.apples.append(new_apple)
            self.update_game()
            self.check_end_game()
            # if not pause:
            #     check_for_collisions()
            #     for obj in GameObject.objects.values():
            #         try:
            #             lights.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
            #         except:  # noqa
            #             pass
            #     lights.copyVirtualLedsToWS281X()
            #     lights.refreshLEDs()


def run_eat_game(lights: MatrixController):
    EatGame(lights=lights).run()


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
