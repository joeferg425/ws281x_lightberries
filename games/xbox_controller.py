#!/usr/bin/python3
import random
import numpy as np
from lightberries.array_patterns import ArrayPattern
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors, Pixel
from lightberries.array_functions import ArrayFunction
import os
import pygame
from games.game_objects import XboxButton, XboxJoystick, Sprite, GameObject, SpriteShape

import time


class xbox_test(Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        size: int,
        name: str,
        color: np.ndarray[3, np.int32] = PixelColors.WHITE.array,
        has_gravity: bool = True,
        destructible: bool = True,
        bounded: bool = True,
        wrap: bool = False,
        dx: float = 0,
        dy: float = 0,
        health: int = 1,
        max_health: int = 1,
        damage: int = 1,
        phased: bool = False,
        shape: SpriteShape = SpriteShape.CROSS,
    ) -> None:
        super().__init__(
            x,
            y,
            size,
            name,
            color,
            has_gravity,
            destructible,
            bounded,
            wrap,
            dx,
            dy,
            health,
            max_health,
            damage,
            phased,
            shape,
        )
        self.button_delay = 0.25
        self.a_time = time.time()
        self.b_time = time.time()
        self.x_time = time.time()
        self.y_time = time.time()
        self.up_time = time.time()
        self.down_time = time.time()
        self.left_time = time.time()
        self.right_time = time.time()


def run_xbox_controller_test(lights: MatrixController):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    GameObject.frame_size_x = lights.realLEDXaxisRange
    GameObject.frame_size_y = lights.realLEDYaxisRange
    SPEED = 1.5
    pygame.init()
    joysticks = {}
    left_sprites: dict[int, xbox_test] = {}
    right_sprites: dict[int, xbox_test] = {}
    THRESHOLD = 0.05
    fade = ArrayFunction(lights, ArrayFunction.functionFadeOff, ArrayPattern.DefaultColorSequenceByMonth())
    fade.fadeAmount = 0.3
    exiting = False
    while not exiting:
        if len(joysticks) < pygame.joystick.get_count() and pygame.joystick.get_count() <= 4:
            for i in range(0, pygame.joystick.get_count()):
                if i not in joysticks:
                    joysticks[i] = pygame.joystick.Joystick(i)
                    joysticks[i].init()
                    left_sprites[i] = xbox_test(
                        name="left joystick",
                        size=0,
                        x=random.randint(0, lights.realLEDXaxisRange),
                        y=random.randint(0, lights.realLEDYaxisRange),
                        dx=0,
                        dy=0,
                        wrap=True,
                        bounded=False,
                        has_gravity=False,
                        color=PixelColors.pseudoRandom().array,
                    )
                    right_sprites[i] = xbox_test(
                        name="right joystick",
                        size=0,
                        x=random.randint(0, lights.realLEDXaxisRange),
                        y=random.randint(0, lights.realLEDYaxisRange),
                        dx=0,
                        dy=0,
                        wrap=True,
                        bounded=False,
                        has_gravity=False,
                        color=PixelColors.pseudoRandom().array,
                    )
        fade.run()
        for event in pygame.event.get():
            if "joy" in event.dict:
                t = time.time()
                left_obj = left_sprites[event.dict["joy"]]
                right_obj = right_sprites[event.dict["joy"]]
                if "axis" in event.dict:
                    if event.dict["axis"] == XboxJoystick.JOY_LEFT_X:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            left_obj.dx = event.dict["value"] * SPEED
                        else:
                            left_obj.dx = 0
                    elif event.dict["axis"] == XboxJoystick.JOY_LEFT_Y:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            left_obj.dy = event.dict["value"] * SPEED
                        else:
                            left_obj.dy = 0
                    elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_X:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            right_obj.dx = event.dict["value"] * SPEED
                        else:
                            right_obj.dx = 0
                    elif event.dict["axis"] == XboxJoystick.JOY_RIGHT_Y:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            right_obj.dy = event.dict["value"] * SPEED
                        else:
                            right_obj.dy = 0
                    elif event.dict["axis"] == XboxJoystick.TRIGGER_LEFT:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            left_obj.color = PixelColors.random().array
                    elif event.dict["axis"] == XboxJoystick.TRIGGER_RIGHT:
                        if np.abs(event.dict["value"]) > THRESHOLD:
                            right_obj.color = PixelColors.random().array
                elif "button" in event.dict:
                    if event.dict["button"] == XboxButton.X:
                        if t - right_obj.y_time > right_obj.button_delay:
                            right_obj.y_time = t
                            if right_obj.shape == SpriteShape.CROSS:
                                right_obj.shape = SpriteShape.CIRCLE
                            else:
                                right_obj.shape = SpriteShape.CROSS
                    elif event.dict["button"] == XboxButton.A:
                        if t - left_obj.a_time > left_obj.button_delay:
                            left_obj.a_time = t
                            if left_obj.shape == SpriteShape.CROSS:
                                left_obj.shape = SpriteShape.CIRCLE
                            else:
                                left_obj.shape = SpriteShape.CROSS
                    elif event.dict["button"] == XboxButton.B:
                        lights.virtualLEDBuffer *= 0
                    elif event.dict["button"] == XboxButton.UP:
                        if t - right_obj.up_time > right_obj.button_delay:
                            right_obj.up_time = t
                            if right_obj.size < 5:
                                right_obj.size += 1
                    elif event.dict["button"] == XboxButton.DOWN:
                        if t - right_obj.down_time > right_obj.button_delay:
                            right_obj.down_time = t
                            if right_obj.size > 0:
                                right_obj.size -= 1
                    elif event.dict["button"] == XboxButton.RIGHT:
                        if t - left_obj.up_time > left_obj.button_delay:
                            left_obj.right_time = t
                            if left_obj.size < 5:
                                left_obj.size += 1
                    elif event.dict["button"] == XboxButton.LEFT:
                        if t - left_obj.left_time > left_obj.button_delay:
                            left_obj.left_time = t
                            if left_obj.size > 0:
                                left_obj.size -= 1
                    elif event.dict["button"] == XboxButton.XBOX:
                        exiting = True
                        GameObject.dead_objects.extend(GameObject.objects)
                        break
                    elif event.dict["button"] == XboxButton.BUMPER_RIGHT:
                        fade.fadeAmount -= 0.05
                        if fade.fadeAmount < 0.0:
                            fade.fadeAmount = 0.0
                    elif event.dict["button"] == XboxButton.BUMPER_LEFT:
                        fade.fadeAmount += 0.05
                        if fade.fadeAmount > 1.0:
                            fade.fadeAmount = 1.0
        for obj in GameObject.objects.values():
            obj.go()
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
    BRIGHTNESS = 0.25
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
        run_xbox_controller_test(lights)
