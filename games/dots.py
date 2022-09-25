#!/usr/bin/python3
import random
import numpy as np
from lightberries.matrix_controller import MatrixController
from lightberries.pixel import PixelColors
from game_objects import Player, GameObject, SpriteShape, Projectile
import time
from light_game import LightEvent, LightEventId, LightGame


class Dot(Player):
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
            color=PixelColors.PSEUDO_RANDOM.array,
            has_gravity=False,
        )
        self.bounded = False
        self.wrap = True
        self.destructible = False
        self.timestamp_shoot = self.timestamp_spawn
        self.timestamp_shape = self.timestamp_spawn
        self.timestamp_size = self.timestamp_spawn
        self.splash_color = PixelColors.PSEUDO_RANDOM.array
        self._shape: SpriteShape = SpriteShape.CROSS
        self._size = 0

    @property
    def shape(self) -> SpriteShape:
        return SpriteShape.CROSS

    @shape.setter
    def shape(self, val: SpriteShape) -> None:
        self._shape = val

    @property
    def size(self) -> int:
        return 0

    @size.setter
    def size(self, val: int) -> None:
        self._size = val


class Splash(Projectile):
    def __init__(
        self,
        x: int,
        y: int,
        owner: Dot,
    ) -> None:
        super().__init__(
            x=x,
            y=y,
            size=0,
            name="splash",
            destructible=True,
            dx=0,
            dy=0,
            owner=owner,
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
        self.dot = owner
        self._shape: SpriteShape = SpriteShape.CROSS
        self._size = 0

    @property
    def color(self) -> np.ndarray[(3), np.int32]:
        return self.dot.splash_color

    @color.setter
    def color(self, val: np.ndarray[(3), np.int32]) -> None:
        pass

    @property
    def shape(self) -> SpriteShape:
        return self.dot._shape

    @shape.setter
    def shape(self, val: SpriteShape) -> None:
        pass

    @property
    def size(self) -> int:
        return self.dot._size

    @size.setter
    def size(self, val: int) -> None:
        pass

    @property
    def height(self) -> int:
        return self.dot._size

    @height.setter
    def height(self, val: int) -> None:
        pass

    @property
    def width(self) -> int:
        return self.dot._size

    @width.setter
    def width(self, val: int) -> None:
        pass

    @property
    def dx(self) -> float:
        return self.dot.x_aim

    @property
    def dy(self) -> float:
        return self.dot.y_aim * 2

    def collide(self, obj: "GameObject", xys: list[tuple[int, int]]) -> None:
        pass


class DotsGame(LightGame):
    THRESHOLD = 0.05
    SPEED = 2
    MIN_BULLET_SPEED = 0.05
    MAX_SIZE = 10

    def __init__(self, lights: MatrixController) -> None:
        super().__init__(lights)
        self.players: dict[int, Dot] = {}
        self.add_callback(event_id=LightEventId.ControllerAdded, callback=self.add_player)
        self.splash_screen("dots", 20)

    def add_player(self, event: LightEvent):
        if event.controller_instance_id not in self.players:
            self.players[event.controller_instance_id] = Dot(
                x=random.randint(0, GameObject.frame_size_x - 1),
                y=random.randint(0, GameObject.frame_size_y - 1),
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
                dx = controller.LS.x * DotsGame.SPEED
                dy = controller.LS.y * DotsGame.SPEED
                player.dx = dx if abs(dx) > DotsGame.MIN_BULLET_SPEED else 0.0
                player.dy = dy if abs(dy) > DotsGame.MIN_BULLET_SPEED else 0.0
                x_aim = controller.RS.x * DotsGame.SPEED
                y_aim = controller.RS.y * DotsGame.SPEED
                player.x_aim = x_aim if abs(x_aim) > DotsGame.MIN_BULLET_SPEED else 0.0
                player.y_aim = y_aim if abs(y_aim) > DotsGame.MIN_BULLET_SPEED else 0.0
                if event.event_id == LightEventId.TriggerLeft:
                    player.splash_color = PixelColors.RANDOM.array
                elif event.event_id == LightEventId.ButtonTop:
                    player.color = PixelColors.RANDOM.array
                elif event.event_id == LightEventId.TriggerRight:
                    if (t - player.timestamp_shoot >= GameObject.BUTTON_DEBOUNCE) and not (self.pause):
                        player.timestamp_shoot = t
                        Splash(
                            x=player.x + player.x_aim,
                            y=player.y + player.y_aim,
                            owner=player,
                        )
                elif event.event_id == LightEventId.HatUp:
                    if t - player.timestamp_size > GameObject.BUTTON_DEBOUNCE:
                        player.timestamp_size = t
                        if player._size < DotsGame.MAX_SIZE:
                            player._size += 1
                elif event.event_id == LightEventId.HatDown:
                    if t - player.timestamp_size > GameObject.BUTTON_DEBOUNCE:
                        player.timestamp_size = t
                        if player._size > 0:
                            player._size -= 1
                elif event.event_id == LightEventId.HatRight:
                    if t - player.timestamp_shape > GameObject.BUTTON_DEBOUNCE:
                        player.timestamp_shape = t
                        if player._shape == SpriteShape.CROSS:
                            player._shape = SpriteShape.CIRCLE
                        elif player._shape == SpriteShape.CIRCLE:
                            player._shape = SpriteShape.SQUARE
                        else:
                            player._shape = SpriteShape.CROSS
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
