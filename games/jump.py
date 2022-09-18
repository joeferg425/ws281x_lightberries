#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import (
    GameObject,
    Floor,
    Player,
    Projectile,
    check_for_collisions,
    XboxButton,
    XboxJoystick,
    GRAVITY,
    MAX_GRAVITY,
)
import pygame
import numpy as np
from light_game import LightGame
from light_game import LightEvent, LightEventId, LightGame


class PygameJumper(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.surf = pygame.Surface((LightGame.SIMULATED_SIZE, LightGame.SIMULATED_SIZE))
        self.surf.fill((128, 255, 40))
        self.rect = self.surf.get_rect(center=((x * LightGame.SIMULATED_SIZE), y * LightGame.SIMULATED_SIZE))
        self.rect.left = x * LightGame.SIMULATED_SIZE
        self.rect.top = y * LightGame.SIMULATED_SIZE
        self.rect.height = 2 * LightGame.SIMULATED_SIZE
        self.rect.width = LightGame.SIMULATED_SIZE


class PygamePlatform(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, size: int):
        super().__init__()
        self.surf = pygame.Surface((LightGame.SIMULATED_SIZE * size, LightGame.SIMULATED_SIZE))
        self.surf.fill((255, 0, 0))
        self.rect = self.surf.get_rect(center=(x * LightGame.SIMULATED_SIZE, y * LightGame.SIMULATED_SIZE))
        self.rect.left = x * LightGame.SIMULATED_SIZE
        self.rect.top = y * LightGame.SIMULATED_SIZE
        self.rect.height = LightGame.SIMULATED_SIZE
        self.rect.width = size * LightGame.SIMULATED_SIZE


class Jumper(Player):
    def __init__(
        self,
        x: int,
        y: int,
        name="player",
        color: np.ndarray[3, np.int32] = PixelColors.ORANGE2.array,
        has_gravity: bool = True,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name=name,
            color=color,
            has_gravity=has_gravity,
        )
        self.p_sprite = PygameJumper(x, y)
        self.timestamp_color = time.time()
        self.timestamp_jump = time.time()
        self.falling = True

    def go(self):
        super().go()
        self.p_sprite.rect.left = self.x * LightGame.SIMULATED_SIZE
        self.p_sprite.rect.height = (1 + self.dy) * LightGame.SIMULATED_SIZE
        self.p_sprite.rect.top = self.y * LightGame.SIMULATED_SIZE
        self.falling = True

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        super().collide(obj, xys)
        self.falling = False
        self.jump_count = 0

    @property
    def dead(self) -> bool:
        if self._dead:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.dead_time = time.time()
                self._dead = True
        elif self.health <= 0:
            if self.id not in GameObject.dead_objects:
                GameObject.dead_objects.append(self.id)
            if not self._dead:
                self.dead_time = time.time()
                self._dead = True
        elif self.bounded:
            if self.x > (GameObject.frame_size_x - 1) or self.x < 0:
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.dead_time = time.time()
                    self._dead = True
            elif self.y > (GameObject.frame_size_y - 1):
                if self.id not in GameObject.dead_objects:
                    GameObject.dead_objects.append(self.id)
                if not self._dead:
                    self.dead_time = time.time()
                    self._dead = True
        return self._dead


class Bullet(Projectile):
    def __init__(
        self,
        owner: GameObject,
        x: int,
        y: int,
        size: int = 1,
        name: str = "projectile",
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


class Platform(Floor):
    def __init__(
        self,
        x: int,
        y: int,
        size: int = 1,
        name: str = "floor",
        color: np.ndarray[3, np.int32] = PixelColors.GREEN.array,
    ) -> None:
        super().__init__(
            x,
            y,
            size,
            name,
            color,
        )
        self.damage = 0
        self.p_sprite = PygamePlatform(x, y, size)


class JumpGame(LightGame):
    THRESHOLD = 0.05
    WIN_DURATION = 10
    RESPAWN_DELAY = 1
    BULLET_DELAY = 0.2

    def __init__(self, lights: MatrixController) -> None:
        super().__init__(lights)
        self.players: dict[int, Jumper] = {}
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_player)
        self.all_sprites = pygame.sprite.Group()
        self.platforms = []

    def get_new_player(self) -> GameObject:
        j = Jumper(
            x=random.randint(0, 5),
            y=1,
        )
        # self.all_sprites.add(j.p_sprite)
        return j

    def add_player(self, event: LightEvent):
        if event.controller_instance_id not in self.players:
            self.players[event.controller_instance_id] = self.get_new_player()

    def create_level(self):
        p = Platform(x=0, y=9, size=18)
        self.platforms.append(p)
        # self.all_sprites.add(p.p_sprite)
        # p = Platform(x=0, y=15, size=31)
        # self.platforms.append(p)
        # self.all_sprites.add(p.p_sprite)

    def run(self):
        self.create_level()
        while not self.exiting:
            self.get_controllers()
            self.check_for_winner()
            self.respawn_dead_players()
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
                        if (t - player.bullet_time >= JumpGame.BULLET_DELAY) and not (self.pause):
                            player.bullet_time = t
                            Bullet(
                                x=player.x + player.x_aim,
                                y=player.y + player.y_aim,
                                dx=player.x_aim * 2,
                                dy=player.y_aim * 2,
                                owner=player,
                            )
                    elif event.event_id == LightEventId.ButtonStart:
                        if t - self.pause_time > JumpGame.PAUSE_DELAY:
                            self.pause_time = t
                            self.pause = not self.pause
                    elif event.event_id == LightEventId.ButtonPower:
                        self.exiting = True
                        break
                    elif event.event_id == LightEventId.ButtonTop:
                        if t - player.tim0estamp_color > 0.15:
                            player.timestamp_color = t
                            player.color = PixelColors.pseudoRandom().array
                    elif event.event_id == LightEventId.ButtonBottom:
                        if t - player.timestamp_jump > 0.2:
                            if player.dy > -8:
                                if player.jump_count < 2:
                                    player.jump_count += 1
                                    player.timestamp_jump = t
                                    if player.dy > 0:
                                        player.dy = -3.2
                                    else:
                                        player.dy -= 3.2
            self.check_end_game()
            self.update_game()


def run_jump_game(lights: MatrixController):
    JumpGame(lights=lights).run()
    # pause = True
    # os.environ["SDL_VIDEODRIVER"] = "dummy"
    # GameObject.frame_size_x = lights.realLEDXaxisRange
    # GameObject.frame_size_y = lights.realLEDYaxisRange
    # MAX_ENEMY_SPEED = 0.3
    # PAUSE_DELAY = 0.3
    # pygame.init()
    # THRESHOLD = 0.05
    # fade = ArrayFunction(lights, ArrayFunction.functionFade, ArrayPattern.DefaultColorSequenceByMonth())
    # fade = ArrayFunction(lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
    # fade.fadeAmount = 0.3
    # fade.colorFade = int(0.3 * 256)
    # fade.color = PixelColors.OFF.array
    # x_change = 0
    # y_change = 0
    # x_reticle = 0
    # y_reticle = 0
    # fizzled = []
    # dead_ones = []
    # BULLET_DELAY = 0.2
    # MIN_BULLET_SPEED = 0.2
    # MIN_ENEMY_SPEED = 0.01
    # ENEMY_DELAY = 2.0
    # bullet_time = time.time()
    # enemy_time = time.time()
    # player1_dead_time = time.time()
    # score = 1
    # player1 = Player(
    #     x=int(1),
    #     y=random.randint(1, lights.realLEDXaxisRange // 2),
    # )
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
    # WIN_SCORE = lights.realLEDYaxisRange
    # WIN_DURATION = 10
    # pause_time = time.time()
    # fake_pause_time = time.time() - 5
    # fake_pause = False
    # b9_time = time.time()
    # b10_time = time.time() - 1
    # # death_rays = []
    # death_ray_time = time.time() - 10
    # DEATH_RAY_DELAY = 3
    # FAKE_PAUSE_DELAY = 3
    # JUMP_DELAY = 0.3
    # jump_time = time.time() - JUMP_DELAY
    # READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.CYAN.array).array])
    # NOT_READY = np.array([Pixel(PixelColors.YELLOW.array).array, Pixel(PixelColors.ORANGE.array).array])
    # joystick_count = 0
    # joystick = None
    # DEATH_RAY_DURATION = 0.4
    # DEATH_RAY_FLICKER = 0.1
    # # floors: list[game_object] = []

    # # floors.append(
    # Floor(0, 9, 18)
    # Floor(0, 15, 31)
    # # )
    # # objects.append(floor)
    # exiting = False
    # while not exiting:
    #     events = list(pygame.event.get())
    #     if joystick_count != pygame.joystick.get_count():
    #         if pygame.joystick.get_count() > 0:
    #             joystick = pygame.joystick.Joystick(0)
    #             joystick.init()
    #         else:
    #             joystick.quit()
    #         joystick_count = pygame.joystick.get_count()
    #         if joystick_count == 0:
    #             pause = True
    #         else:
    #             pause = False
    #     if fake_pause and time.time() - fake_pause_time > FAKE_PAUSE_DELAY:
    #         pause = False
    #         fake_pause = False

    #     if score >= WIN_SCORE:
    #         if not win:
    #             win = True
    #             win_time = time.time()
    #         for firework in fireworks:
    #             firework.run()
    #         fade.run()
    #         lights.copyVirtualLedsToWS281X()
    #         lights.refreshLEDs()
    #         if time.time() - win_time > WIN_DURATION:
    #             win = False
    #             score = 1
    #             player1.dead = True
    #         continue
    #     if player1.dead:
    #         delta = time.time() - player1_dead_time
    #         if delta > 1:
    #             player1 = Player(
    #                 x=1,
    #                 y=random.randint(1, lights.realLEDXaxisRange // 2),
    #             )
    #             # enemies.clear()
    #             # bullets.clear()
    #             fizzled.clear()
    #             dead_ones.clear()
    #             score = 1
    #             fade.color = PixelColors.OFF.array

    #     fade.run()
    #     # if time.time() - death_ray_time >= DEATH_RAY_DELAY:
    #     #     lights.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, READY)
    #     # else:
    #     #     lights.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, NOT_READY)
    #     for event in events:
    #         if "joy" in event.dict and "axis" in event.dict:
    #             if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
    #                 x_change = event.dict["value"]
    #             # elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
    #             # y_change = event.dict["value"]
    #             elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_X:
    #                 if np.abs(event.dict["value"]) > MIN_BULLET_SPEED:
    #                     player1.x_aim = event.dict["value"] * 2
    #             elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_Y:
    #                 if np.abs(event.dict["value"]) > MIN_BULLET_SPEED:
    #                     player1.y_aim = event.dict["value"] * 2
    #             #            elif event.dict["axis"] == 4 and event.dict["value"] > 0.5:
    #             #                if (
    #             #                    abs(y_reticle) >= MIN_BULLET_SPEED
    #             #                    and abs(x_reticle) >= MIN_BULLET_SPEED
    #             #                    and time.time() - death_ray_time > DEATH_RAY_DELAY
    #             #                ) and not (pause or fake_pause):
    #             #                    # death_rays.append(
    #             #                    sprite(
    #             #                        "death ray",
    #             #                        player1.x,
    #             #                        player1.y,
    #             #                        x_reticle,
    #             #                        y_reticle,
    #             #                        bounded=True,
    #             #                        color=PixelColors.CYAN.array,
    #             #                    )
    #             #                    # )
    #             #                    death_ray_time = time.time()
    #             elif event.dict["axis"] == XboxJoystick.TRIGGER_RIGHT and event.dict["value"] > 0.5:
    #                 # if np.abs(x_reticle) > 0.25 and np.abs(y_reticle) > 0.25:
    #                 if (
    #                     (time.time() - bullet_time >= BULLET_DELAY)
    #                     and not (pause or fake_pause)
    #                     and (player1.x_aim != 0.0 and player1.y_aim != 0.0)
    #                 ):
    #                     bullet_time = time.time()
    #                     # bullets.append(
    #                     Projectile(
    #                         x=player1.x + player1.x_aim_direction,
    #                         y=player1.y + player1.y_aim_direction,
    #                         size=0,
    #                         dx=player1.x_aim,
    #                         dy=player1.y_aim,
    #                     )
    #                     # )
    #         if "joy" in event.dict and "button" in event.dict:
    #             if event.dict["button"] == XboxButton.START:
    #                 # if time.time() - pause_time > PAUSE_DELAY:
    #                 #     pause_time = time.time()
    #                 #     pause = not pause
    #                 player1._dead = True
    #             elif event.dict["button"] == XboxButton.XBOX:
    #                 exiting = True
    #                 GameObject.dead_objects.extend(GameObject.objects)
    #                 break
    #             elif event.dict["button"] == XboxButton.A:
    #                 if time.time() - jump_time > JUMP_DELAY and player1.dy >= 0 and player1.jump_count < 2:
    #                     player1.jump_count += 1
    #                     jump_time = time.time()
    #                     player1.dy -= 4.5
    #                     if player1.dy < -4.5:
    #                         player1.dy = -4.5
    #             elif event.dict["button"] == XboxButton.BUMPER_LEFT:
    #                 b9_time = time.time()
    #             elif event.dict["button"] == XboxButton.BUMPER_RIGHT:
    #                 b10_time = time.time()
    #         if time.time() - b9_time < 0.1 and time.time() - b10_time < 0.1:
    #             fake_pause = True
    #             fake_pause_time = time.time()
    #     if np.abs(x_change) > THRESHOLD:
    #         player1.dx = x_change
    #     else:
    #         player1.dx = 0
    #     # x_change * 0.5
    #     # if np.abs(y_change) > THRESHOLD:
    #     #     player1.dy = y_change
    #     # else:
    #     #     player1.dy = 0
    #     # x_change * 0.5
    #     # lights.virtualLEDBuffer[player1.x, player1.y] = Pixel(player1.color).array
    #     # for bullet in bullets:
    #     #     if bullet.dead:
    #     #         fizzled.append(bullet)
    #     #     else:
    #     #         if not player1.dead:
    #     #             lights.virtualLEDBuffer[bullet.x, bullet.y] = Pixel(bullet.color).array
    #     # for fizzle in fizzled:
    #     #     if fizzle in bullets:
    #     #         bullets.remove(fizzle)
    #     # fizzled.clear()
    #     # if time.time() - enemy_time >= ENEMY_DELAY and not player1.dead and not pause and not fake_pause:
    #     #     enemy_time = time.time()
    #     #     enemy = sprite(
    #     #         "enemy",
    #     #         random.randint(0, lights.realLEDColumnCount - 1),
    #     #         random.randint(0, lights.realLEDRowCount - 1),
    #     #         random.random() * [-1, 1][random.randint(0, 1)],
    #     #         random.random() * [-1, 1][random.randint(0, 1)],
    #     #         color=PixelColors.RED.array,
    #     #     )
    #     #     if abs(enemy.dx) < MIN_ENEMY_SPEED:
    #     #         if enemy.dx < 0:
    #     #             enemy.dx = -MIN_ENEMY_SPEED
    #     #         else:
    #     #             enemy.dx = MIN_ENEMY_SPEED
    #     #     elif abs(enemy.dx) > MAX_ENEMY_SPEED:
    #     #         if enemy.dx < 0:
    #     #             enemy.dx = -MAX_ENEMY_SPEED
    #     #         else:
    #     #             enemy.dx = MAX_ENEMY_SPEED
    #     #     if abs(enemy.dy) < MIN_ENEMY_SPEED:
    #     #         if enemy.dy < 0:
    #     #             enemy.dy = -MIN_ENEMY_SPEED
    #     #         else:
    #     #             enemy.dy = MIN_ENEMY_SPEED
    #     #     elif abs(enemy.dy) > MAX_ENEMY_SPEED:
    #     #         if enemy.dy < 0:
    #     #             enemy.dy = -MAX_ENEMY_SPEED
    #     #         else:
    #     #             enemy.dy = MAX_ENEMY_SPEED
    #     #     while abs(enemy.x - player1.x) < 5 and abs(enemy.y - player1.y) < 5:
    #     #         enemy.x = random.randint(0, lights.realLEDColumnCount - 1)
    #     #         enemy.y = random.randint(0, lights.realLEDRowCount - 1)
    #     #     enemies.append(enemy)
    #     # for death_ray in death_rays:
    #     #     duration = int((time.time() - death_ray_time) / DEATH_RAY_FLICKER)
    #     #     death_ray.x = player1.x
    #     #     death_ray.y = player1.y
    #     #     if x_reticle > 0.0:
    #     #         death_ray.dx = x_reticle
    #     #     if y_reticle > 0.0:
    #     #         death_ray.dy = y_reticle
    #     #     rxs, rys = death_ray.xy_ray
    #     #     if np.array_equal(death_ray.color, PixelColors.MAGENTA.array):
    #     #         death_ray.color = PixelColors.CYAN.array
    #     #     else:
    #     #         death_ray.color = PixelColors.MAGENTA.array
    #     #     lights.virtualLEDBuffer[rxs, rys] = Pixel(death_ray.color).array
    #     # for enemy in enemies:
    #     #     if not player1.dead and not (pause or fake_pause):
    #     #         for xy in zip(enemy.xs, enemy.ys):
    #     #             if xy == player1:
    #     #                 player1.dead = True
    #     #                 fade.color = Pixel(PixelColors.RED.array).array
    #     #                 player1_dead_time = time.time()
    #     #             if bullets:
    #     #                 for bullet in bullets:
    #     #                     if xy == bullet:
    #     #                         enemy.dead = True
    #     #                         score += 1
    #     #                         dead_ones.append(enemy)
    #     #                         fizzled.append(bullet)
    #     #                         break
    #     #             if enemy.dead:
    #     #                 break
    #     #             if death_rays:
    #     #                 for death_ray in death_rays:
    #     #                     rxs, rys = death_ray.xy_ray
    #     #                     rxy = list(zip(rxs, rys))
    #     #                     if xy in rxy:
    #     #                         enemy.dead = True
    #     #                         score += 1
    #     #                         dead_ones.append(enemy)
    #     #             if enemy.dead:
    #     #                 break

    #     # if not enemy.dead and not player1.dead:
    #     #     lights.virtualLEDBuffer[enemy.xs, enemy.ys] = Pixel(enemy.color).array
    #     # if time.time() - death_ray_time >= DEATH_RAY_DURATION:
    #     #     death_rays.clear()
    #     # for dead in dead_ones:
    #     #     lights.virtualLEDBuffer[
    #     #         dead.xs,
    #     #         dead.ys,
    #     #     ] = Pixel(PixelColors.YELLOW.array).array
    #     #     if dead in enemies:
    #     #         try:
    #     #             enemies.remove(dead)
    #     #         except:  # noqa
    #     #             pass
    #     check_for_collisions()
    #     for obj in GameObject.objects.values():
    #         try:
    #             lights.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
    #         except:  # noqa
    #             pass
    #     # for floor in floor.floors:
    #     #     lights.virtualLEDBuffer[floor.xs, floor.ys] = Pixel(floor.color).array
    #     dead_ones.clear()
    #     lights.copyVirtualLedsToWS281X()
    #     lights.refreshLEDs()


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
