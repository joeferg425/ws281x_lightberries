#!/usr/bin/python3
import random
import numpy as np
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import Player, Sprite, GameObject, SpriteShape
import time
from light_game import LightEvent, LightEventId, LightGame


class Dot(Sprite):
    def __init__(
        self,
        x: int,
        y: int,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name="",
            color=PixelColors.pseudoRandom().array,
            has_gravity=False,
            destructible=False,
            bounded=False,
            wrap=True,
            dx=0,
            dy=0,
            health=1,
            max_health=1,
            damage=0,
            phased=True,
            shape=SpriteShape.CROSS,
        )
        self.button_delay = 0.25
        self.timestamp_shape = time.time()
        self.b_time = time.time()
        self.x_time = time.time()
        self.timestamp_shape = time.time()
        self.timestamp_size = time.time()
        self.timestamp_size = time.time()
        self.timestamp_size = time.time()
        self.right_time = time.time()


class Dots(Player):
    def __init__(
        self,
        left_dot: Dot,
        right_dot: Dot,
    ) -> None:
        super().__init__(
            x=0,
            y=0,
            size=0,
            name="",
            color=PixelColors.OFF.array,
            has_gravity=False,
        )
        self.destructible = False
        self.left_dot = left_dot
        self.right_dot = right_dot


class DotsGame(LightGame):
    THRESHOLD = 0.05
    SPEED = 2

    def __init__(self, lights: MatrixController) -> None:
        super().__init__(lights)
        self.left_sticks: dict[int, Dot] = {}
        self.right_sticks: dict[int, Dot] = {}
        self.players: dict[int, Dots] = {}
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_player)
        self.splash_screen("dots", 20)

    def add_player(self, event: LightEvent):
        if event.controller_instance_id not in self.players:
            if event.controller_instance_id in self.left_sticks:
                self.left_sticks[event.controller_instance_id].health = 0
            if event.controller_instance_id in self.right_sticks:
                self.right_sticks[event.controller_instance_id].health = 0
            if event.controller_instance_id in self.players:
                self.players[event.controller_instance_id].health = 0
            self.left_sticks[event.controller_instance_id] = Dot(
                x=random.randint(0, self.lights.realLEDXaxisRange),
                y=random.randint(0, self.lights.realLEDYaxisRange),
            )
            self.right_sticks[event.controller_instance_id] = Dot(
                x=random.randint(0, self.lights.realLEDXaxisRange),
                y=random.randint(0, self.lights.realLEDYaxisRange),
            )
            self.players[event.controller_instance_id] = Dots(
                self.left_sticks[event.controller_instance_id], self.right_sticks[event.controller_instance_id]
            )

    def run(self):
        while not self.exiting:
            self.get_controllers()
            for event in self.get_events():
                t = time.time()
                if event.controller_instance_id not in self.players:
                    self.add_player(event=event)
                player = self.players[event.controller_instance_id]
                controller = event.controller
                left_dot = player.left_dot
                right_dot = player.right_dot

                left_dot.dx = controller.LS.x * DotsGame.SPEED
                left_dot.dy = controller.LS.y * DotsGame.SPEED
                right_dot.dx = controller.RS.x * DotsGame.SPEED
                right_dot.dy = controller.RS.y * DotsGame.SPEED
                if event.event_id == LightEventId.TriggerLeft:
                    if np.abs(event.z) > DotsGame.THRESHOLD:
                        left_dot.color = PixelColors.random().array
                elif event.event_id == LightEventId.TriggerRight:
                    if np.abs(event.z) > DotsGame.THRESHOLD:
                        right_dot.color = PixelColors.random().array
                elif event.event_id == LightEventId.ButtonLeft:
                    if t - right_dot.timestamp_shape > right_dot.button_delay:
                        right_dot.timestamp_shape = t
                        if right_dot.shape == SpriteShape.CROSS:
                            right_dot.shape = SpriteShape.CIRCLE
                        else:
                            right_dot.shape = SpriteShape.CROSS
                elif event.event_id == LightEventId.ButtonBottom:
                    if t - left_dot.timestamp_shape > left_dot.button_delay:
                        left_dot.timestamp_shape = t
                        if left_dot.shape == SpriteShape.CROSS:
                            left_dot.shape = SpriteShape.CIRCLE
                        else:
                            left_dot.shape = SpriteShape.CROSS
                elif event.event_id == LightEventId.ButtonRight:
                    lights.virtualLEDBuffer *= 0
                elif event.event_id == LightEventId.HatUp:
                    if t - right_dot.timestamp_size > right_dot.button_delay:
                        right_dot.timestamp_size = t
                        if right_dot.size < 5:
                            right_dot.size += 1
                elif event.event_id == LightEventId.HatDown:
                    if t - right_dot.timestamp_size > right_dot.button_delay:
                        right_dot.timestamp_size = t
                        if right_dot.size > 0:
                            right_dot.size -= 1
                elif event.event_id == LightEventId.HatRight:
                    if t - left_dot.timestamp_size > left_dot.button_delay:
                        left_dot.right_time = t
                        if left_dot.size < 5:
                            left_dot.size += 1
                elif event.event_id == LightEventId.HatLeft:
                    if t - left_dot.timestamp_size > left_dot.button_delay:
                        left_dot.timestamp_size = t
                        if left_dot.size > 0:
                            left_dot.size -= 1
                elif event.event_id == LightEventId.ButtonPower:
                    self.exiting = True
                    GameObject.dead_objects.extend(GameObject.objects)
                    break
                elif event.event_id == LightEventId.BumperRight:
                    self.fade.fadeAmount -= 0.05
                    if self.fade.fadeAmount < 0.0:
                        self.fade.fadeAmount = 0.0
                elif event.event_id == LightEventId.BumperLeft:
                    self.fade.fadeAmount += 0.05
                    if self.fade.fadeAmount > 1.0:
                        self.fade.fadeAmount = 1.0
            self.check_end_game()
            self.update_game()


def run_dots_game(lights: MatrixController):
    g = DotsGame(lights=lights)
    try:
        g.run()
    except Exception as ex:  # noqa
        print(ex)
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
        run_dots_game(lights)
