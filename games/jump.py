#!/usr/bin/python3
from __future__ import annotations
import random
import time
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import Pixel, PixelColors
from lightberries.array_functions import ArrayFunction
from lightberries.matrix_functions import MatrixFunction
from games.game_objects import GameObject, Floor, Player, Projectile, check_for_collisions, XboxButton, XboxJoystick
import os
import pygame
import numpy as np


def run_jump_game(lights: MatrixController):
    pause = True
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    GameObject.frame_size_x = lights.realLEDXaxisRange
    GameObject.frame_size_y = lights.realLEDYaxisRange
    MAX_ENEMY_SPEED = 0.3
    PAUSE_DELAY = 0.3
    pygame.init()
    THRESHOLD = 0.05
    # fade = ArrayFunction(lights, ArrayFunction.functionFade, ArrayPattern.DefaultColorSequenceByMonth())
    fade = ArrayFunction(lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
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
    MIN_ENEMY_SPEED = 0.01
    ENEMY_DELAY = 2.0
    bullet_time = time.time()
    enemy_time = time.time()
    player1_dead_time = time.time()
    score = 1
    player1 = Player(
        x=int(1),
        y=random.randint(1, lights.realLEDXaxisRange // 2),
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
    pause_time = time.time()
    fake_pause_time = time.time() - 5
    fake_pause = False
    b9_time = time.time()
    b10_time = time.time() - 1
    # death_rays = []
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
    # floors: list[game_object] = []

    # floors.append(
    Floor(0, 9, 18)
    Floor(0, 15, 31)
    # )
    # objects.append(floor)
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
                player1.dead = True
            continue
        if player1.dead:
            delta = time.time() - player1_dead_time
            if delta > 1:
                player1 = Player(
                    x=1,
                    y=random.randint(1, lights.realLEDXaxisRange // 2),
                )
                # enemies.clear()
                # bullets.clear()
                fizzled.clear()
                dead_ones.clear()
                score = 1
                fade.color = PixelColors.OFF.array

        fade.run()
        # if time.time() - death_ray_time >= DEATH_RAY_DELAY:
        #     lights.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, READY)
        # else:
        #     lights.virtualLEDBuffer[:score, 0] = ArrayPattern.ColorTransitionArray(score, NOT_READY)
        for event in events:
            if "joy" in event.dict and "axis" in event.dict:
                if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                    x_change = event.dict["value"]
                # elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
                # y_change = event.dict["value"]
                elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_X:
                    if np.abs(event.dict["value"]) > MIN_BULLET_SPEED:
                        player1.x_aim = event.dict["value"] * 2
                elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_Y:
                    if np.abs(event.dict["value"]) > MIN_BULLET_SPEED:
                        player1.y_aim = event.dict["value"] * 2
                #            elif event.dict["axis"] == 4 and event.dict["value"] > 0.5:
                #                if (
                #                    abs(y_reticle) >= MIN_BULLET_SPEED
                #                    and abs(x_reticle) >= MIN_BULLET_SPEED
                #                    and time.time() - death_ray_time > DEATH_RAY_DELAY
                #                ) and not (pause or fake_pause):
                #                    # death_rays.append(
                #                    sprite(
                #                        "death ray",
                #                        player1.x,
                #                        player1.y,
                #                        x_reticle,
                #                        y_reticle,
                #                        bounded=True,
                #                        color=PixelColors.CYAN.array,
                #                    )
                #                    # )
                #                    death_ray_time = time.time()
                elif event.dict["axis"] == XboxJoystick.TRIGGER_RIGHT and event.dict["value"] > 0.5:
                    # if np.abs(x_reticle) > 0.25 and np.abs(y_reticle) > 0.25:
                    if (
                        (time.time() - bullet_time >= BULLET_DELAY)
                        and not (pause or fake_pause)
                        and (player1.x_aim != 0.0 and player1.y_aim != 0.0)
                    ):
                        bullet_time = time.time()
                        # bullets.append(
                        Projectile(
                            x=player1.x + player1.x_aim_direction,
                            y=player1.y + player1.y_aim_direction,
                            size=0,
                            dx=player1.x_aim,
                            dy=player1.y_aim,
                        )
                        # )
            if "joy" in event.dict and "button" in event.dict:
                if event.dict["button"] == XboxButton.START:
                    # if time.time() - pause_time > PAUSE_DELAY:
                    #     pause_time = time.time()
                    #     pause = not pause
                    player1._dead = True
                elif event.dict["button"] == XboxButton.XBOX:
                    exiting = True
                    GameObject.dead_objects.extend(GameObject.objects)
                    break
                elif event.dict["button"] == XboxButton.A:
                    if time.time() - jump_time > JUMP_DELAY and player1.dy >= 0 and player1.jump_count < 2:
                        player1.jump_count += 1
                        jump_time = time.time()
                        player1.dy -= 4.5
                        if player1.dy < -4.5:
                            player1.dy = -4.5
                elif event.dict["button"] == XboxButton.BUMPER_LEFT:
                    b9_time = time.time()
                elif event.dict["button"] == XboxButton.BUMPER_RIGHT:
                    b10_time = time.time()
            if time.time() - b9_time < 0.1 and time.time() - b10_time < 0.1:
                fake_pause = True
                fake_pause_time = time.time()
        if np.abs(x_change) > THRESHOLD:
            player1.dx = x_change
        else:
            player1.dx = 0
        # x_change * 0.5
        # if np.abs(y_change) > THRESHOLD:
        #     player1.dy = y_change
        # else:
        #     player1.dy = 0
        # x_change * 0.5
        # lights.virtualLEDBuffer[player1.x, player1.y] = Pixel(player1.color).array
        # for bullet in bullets:
        #     if bullet.dead:
        #         fizzled.append(bullet)
        #     else:
        #         if not player1.dead:
        #             lights.virtualLEDBuffer[bullet.x, bullet.y] = Pixel(bullet.color).array
        # for fizzle in fizzled:
        #     if fizzle in bullets:
        #         bullets.remove(fizzle)
        # fizzled.clear()
        # if time.time() - enemy_time >= ENEMY_DELAY and not player1.dead and not pause and not fake_pause:
        #     enemy_time = time.time()
        #     enemy = sprite(
        #         "enemy",
        #         random.randint(0, lights.realLEDColumnCount - 1),
        #         random.randint(0, lights.realLEDRowCount - 1),
        #         random.random() * [-1, 1][random.randint(0, 1)],
        #         random.random() * [-1, 1][random.randint(0, 1)],
        #         color=PixelColors.RED.array,
        #     )
        #     if abs(enemy.dx) < MIN_ENEMY_SPEED:
        #         if enemy.dx < 0:
        #             enemy.dx = -MIN_ENEMY_SPEED
        #         else:
        #             enemy.dx = MIN_ENEMY_SPEED
        #     elif abs(enemy.dx) > MAX_ENEMY_SPEED:
        #         if enemy.dx < 0:
        #             enemy.dx = -MAX_ENEMY_SPEED
        #         else:
        #             enemy.dx = MAX_ENEMY_SPEED
        #     if abs(enemy.dy) < MIN_ENEMY_SPEED:
        #         if enemy.dy < 0:
        #             enemy.dy = -MIN_ENEMY_SPEED
        #         else:
        #             enemy.dy = MIN_ENEMY_SPEED
        #     elif abs(enemy.dy) > MAX_ENEMY_SPEED:
        #         if enemy.dy < 0:
        #             enemy.dy = -MAX_ENEMY_SPEED
        #         else:
        #             enemy.dy = MAX_ENEMY_SPEED
        #     while abs(enemy.x - player1.x) < 5 and abs(enemy.y - player1.y) < 5:
        #         enemy.x = random.randint(0, lights.realLEDColumnCount - 1)
        #         enemy.y = random.randint(0, lights.realLEDRowCount - 1)
        #     enemies.append(enemy)
        # for death_ray in death_rays:
        #     duration = int((time.time() - death_ray_time) / DEATH_RAY_FLICKER)
        #     death_ray.x = player1.x
        #     death_ray.y = player1.y
        #     if x_reticle > 0.0:
        #         death_ray.dx = x_reticle
        #     if y_reticle > 0.0:
        #         death_ray.dy = y_reticle
        #     rxs, rys = death_ray.xy_ray
        #     if np.array_equal(death_ray.color, PixelColors.MAGENTA.array):
        #         death_ray.color = PixelColors.CYAN.array
        #     else:
        #         death_ray.color = PixelColors.MAGENTA.array
        #     lights.virtualLEDBuffer[rxs, rys] = Pixel(death_ray.color).array
        # for enemy in enemies:
        #     if not player1.dead and not (pause or fake_pause):
        #         for xy in zip(enemy.xs, enemy.ys):
        #             if xy == player1:
        #                 player1.dead = True
        #                 fade.color = Pixel(PixelColors.RED.array).array
        #                 player1_dead_time = time.time()
        #             if bullets:
        #                 for bullet in bullets:
        #                     if xy == bullet:
        #                         enemy.dead = True
        #                         score += 1
        #                         dead_ones.append(enemy)
        #                         fizzled.append(bullet)
        #                         break
        #             if enemy.dead:
        #                 break
        #             if death_rays:
        #                 for death_ray in death_rays:
        #                     rxs, rys = death_ray.xy_ray
        #                     rxy = list(zip(rxs, rys))
        #                     if xy in rxy:
        #                         enemy.dead = True
        #                         score += 1
        #                         dead_ones.append(enemy)
        #             if enemy.dead:
        #                 break

        # if not enemy.dead and not player1.dead:
        #     lights.virtualLEDBuffer[enemy.xs, enemy.ys] = Pixel(enemy.color).array
        # if time.time() - death_ray_time >= DEATH_RAY_DURATION:
        #     death_rays.clear()
        # for dead in dead_ones:
        #     lights.virtualLEDBuffer[
        #         dead.xs,
        #         dead.ys,
        #     ] = Pixel(PixelColors.YELLOW.array).array
        #     if dead in enemies:
        #         try:
        #             enemies.remove(dead)
        #         except:  # noqa
        #             pass
        check_for_collisions()
        for obj in GameObject.objects.values():
            try:
                lights.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
            except:  # noqa
                pass
        # for floor in floor.floors:
        #     lights.virtualLEDBuffer[floor.xs, floor.ys] = Pixel(floor.color).array
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
        run_jump_game(lights)
