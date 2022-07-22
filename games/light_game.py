import pygame
from typing import Callable, Generator
import random
from enum import IntEnum
import numpy as np
import os
from dataclasses import dataclass
from lightberries.matrix_controller import MatrixController
from lightberries.matrix_functions import MatrixFunction
from lightberries.array_functions import ArrayFunction
from lightberries.array_patterns import ArrayPattern
from lightberries.pixel import Pixel, PixelColors
import time
from game_objects import GameObject, Player, check_for_collisions


class ButtonState(IntEnum):
    Unknown = 0
    Down = 1
    Up = 2


class XboxButton(IntEnum):
    A = 0
    B = 1
    X = 2
    Y = 3
    OPTIONS = 4
    XBOX = 5
    START = 6
    JOY_LEFT = 7
    JOY_RIGHT = 8
    BUMPER_LEFT = 9
    BUMPER_RIGHT = 10
    UP = 11
    DOWN = 12
    LEFT = 13
    RIGHT = 14
    SHARE = 15


class XboxJoystick(IntEnum):
    JOY_LEFT_X = 0
    JOY_LEFT_Y = 1
    JOY_RIGHT_X = 2
    JOY_RIGHT_Y = 3
    TRIGGER_LEFT = 4
    TRIGGER_RIGHT = 5


class LightEventId(IntEnum):
    UnknownEvent = 0x0
    ControllerAdded = 0x1
    ControllerRemoved = 0x2
    Button = 0x10
    ButtonTop = 0x11
    ButtonBottom = 0x12
    ButtonLeft = 0x13
    ButtonRight = 0x14
    ButtonStart = 0x15
    ButtonOptions = 0x16
    ButtonShare = 0x17
    ButtonPower = 0x18
    ButtonStickLeft = 0x19
    ButtonStickRight = 0x1A
    Hat = 0x20
    HatUp = 0x21
    HatDown = 0x22
    HatLeft = 0x23
    HatRight = 0x24
    Bumper = 0x30
    BumperLeft = 0x31
    BumperRight = 0x32
    Trigger = 0x40
    TriggerLeft = 0x41
    TriggerRight = 0x42
    Stick = 0x50
    StickLeft = 0x51
    StickRight = 0x52


@dataclass
class vector:
    x: float
    y: float


class Controller:
    def __init__(self, controller: pygame.joystick.Joystick) -> None:
        self.controller = controller

    @property
    def B00(self) -> bool:
        return self.controller.get_button(0)

    @property
    def B01(self) -> bool:
        return self.controller.get_button(1)

    @property
    def B02(self) -> bool:
        return self.controller.get_button(2)

    @property
    def B03(self) -> bool:
        return self.controller.get_button(3)

    @property
    def B04(self) -> bool:
        return self.controller.get_button(4)

    @property
    def B05(self) -> bool:
        return self.controller.get_button(5)

    @property
    def B06(self) -> bool:
        return self.controller.get_button(6)

    @property
    def B07(self) -> bool:
        return self.controller.get_button(7)

    @property
    def B08(self) -> bool:
        return self.controller.get_button(8)

    @property
    def B09(self) -> bool:
        return self.controller.get_button(9)

    @property
    def B10(self) -> bool:
        return self.controller.get_button(10)

    @property
    def B11(self) -> bool:
        return self.controller.get_button(11)

    @property
    def B12(self) -> bool:
        return self.controller.get_button(12)

    @property
    def B13(self) -> bool:
        return self.controller.get_button(13)

    @property
    def B14(self) -> bool:
        return self.controller.get_button(14)

    @property
    def B15(self) -> bool:
        return self.controller.get_button(15)

    @property
    def H0(self) -> vector:
        return vector(*self.controller.get_hat(0))

    @property
    def H1(self) -> vector:
        return vector(*self.controller.get_hat(1))

    @property
    def A0(self) -> float:
        return self.controller.get_axis(0)

    @property
    def A1(self) -> float:
        return self.controller.get_axis(1)

    @property
    def A2(self) -> float:
        return self.controller.get_axis(2)

    @property
    def A3(self) -> float:
        return self.controller.get_axis(3)

    @property
    def A4(self) -> float:
        return self.controller.get_axis(4)

    @property
    def A5(self) -> float:
        return self.controller.get_axis(5)


@dataclass
class LightEvent:
    controller_instance_id: int
    controller: Controller
    controller_index: int
    event_id: LightEventId

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"controller_index={self.controller_index}"
        )


class XboxController(Controller):
    def __init__(self, controller: pygame.joystick.Joystick) -> None:
        super().__init__(controller=controller)
        self.controller = controller

    @property
    def A(self) -> bool:
        return self.B00

    @property
    def B(self) -> bool:
        return self.B01

    @property
    def Y(self) -> bool:
        return self.B03

    @property
    def X(self) -> bool:
        return self.B02

    @property
    def LB(self) -> bool:
        return self.B09

    @property
    def RB(self) -> bool:
        return self.B10

    @property
    def DPAD(self) -> vector:
        return self.H0

    @property
    def LS(self) -> vector:
        return vector(self.A0, self.A1)

    @property
    def RS(self) -> vector:
        return vector(self.A2, self.A3)

    @property
    def LT(self) -> float:
        return self.A4

    @property
    def RT(self) -> float:
        return self.A5


class LightGame:
    PAUSE_DELAY = 0.3
    THRESHOLD = 0.05
    WIN_DURATION = 10
    RESPAWN_DELAY = 1
    SPECIAL_WEAPON_DELAY = 3

    def __init__(self, lights: MatrixController) -> None:
        pygame.init()
        self.lights = lights
        GameObject.frame_size_x = self.lights.realLEDXaxisRange
        GameObject.frame_size_y = self.lights.realLEDYaxisRange
        self.players: dict[int, GameObject] = {}
        self.rs: list[pygame.Rect] = []
        self.win = False
        self.win_time = time.time()
        self.win_score = int(lights.realLEDYaxisRange // 2)
        self.display = None
        self.exiting = False
        self.pause = True
        if lights.testing:
            self.display = pygame.display.set_mode((lights.realLEDXaxisRange * 10, lights.realLEDYaxisRange * 10))
            self.display.fill((127, 127, 127))
            for i in range(32):
                for j in range(32):
                    self.rs.append(
                        pygame.draw.rect(
                            self.display,
                            (0, 0, 0),
                            (((i * 10) + 1, (j * 10) + 1), (8, 8)),
                        )
                    )
            pygame.display.flip()
        else:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        self.fade = ArrayFunction(
            lights, MatrixFunction.functionMatrixFadeOff, ArrayPattern.DefaultColorSequenceByMonth()
        )
        self.fade.fadeAmount = 0.5
        self.fade.color = PixelColors.OFF.array
        self.fireworks = []
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
            self.fireworks.append(firework)
        self.pause_time = time.time()
        self._controller_instance_dict: dict[int, XboxController] = {}
        self._controller_index_dict: dict[int, XboxController] = {}
        self._instance_to_index_dict: dict[int, int] = {}
        self._callbacks: dict[LightEventId, Callable[[LightEvent], None]] = {}

    def get_new_player(self) -> GameObject:
        return Player(0, 0)

    def add_callback(self, event_id: LightEventId, callback: Callable[[LightEvent], None]) -> None:
        self._callbacks[event_id] = callback

    def get_controllers(self) -> dict[int, XboxController]:
        joystick_count = pygame.joystick.get_count()
        for i in range(joystick_count):
            j = pygame.joystick.Joystick(i)
            if i in self._controller_index_dict:
                self._controller_index_dict[i].controller.quit()
            j.init()
            xj = XboxController(j)
            self._controller_index_dict[i] = xj
            self._controller_instance_dict[j.get_instance_id()] = xj
            self._instance_to_index_dict[i] = j.get_instance_id()
            self.pause = False
        return self._controller_index_dict

    def get_events(self) -> Generator[LightEvent, None, None]:
        light_events: list[LightEvent] = []
        left_joysticks: list[LightEvent] = []
        left_joystick_x_count = 0
        left_joystick_y_count = 0
        right_joysticks: list[LightEvent] = []
        right_joystick_x_count = 0
        right_joystick_y_count = 0
        for pygame_event in pygame.event.get():
            if "joy" in pygame_event.dict:
                controller_index = pygame_event.dict["joy"]
                controller_instance_id = pygame_event.dict["instance_id"]
                controller = self._controller_instance_dict[controller_instance_id]
                if "button" in pygame_event.dict:
                    button_id = pygame_event.dict["button"]
                    if button_id == XboxButton.A:
                        light_events.append(
                            ButtonBottom(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.B:
                        light_events.append(
                            ButtonRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.X:
                        light_events.append(
                            ButtonLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.Y:
                        light_events.append(
                            ButtonTop(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.BUMPER_LEFT:
                        light_events.append(
                            ButtonBumperLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.BUMPER_RIGHT:
                        light_events.append(
                            ButtonBumperRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.START:
                        light_events.append(
                            ButtonStart(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.OPTIONS:
                        light_events.append(
                            ButtonOptions(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.XBOX:
                        light_events.append(
                            ButtonPower(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.SHARE:
                        light_events.append(
                            ButtonShare(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.UP:
                        light_events.append(
                            ButtonHatUp(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.DOWN:
                        light_events.append(
                            ButtonHatDown(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.LEFT:
                        light_events.append(
                            ButtonHatLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.RIGHT:
                        light_events.append(
                            ButtonHatRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.JOY_LEFT:
                        light_events.append(
                            ButtonStickLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    elif button_id == XboxButton.JOY_RIGHT:
                        light_events.append(
                            ButtonStickRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                state=ButtonState.Down if pygame_event.type == 1539 else ButtonState.Up,
                            )
                        )
                    else:
                        print(pygame_event)
                elif "axis" in pygame_event.dict:
                    axis = pygame_event.dict["axis"]
                    if axis == XboxJoystick.JOY_RIGHT_X:
                        if right_joystick_x_count >= len(right_joysticks):
                            light_event = StickRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            right_joysticks.append(light_event)
                            light_events.append(light_event)
                        right_joysticks[right_joystick_x_count].x = pygame_event.dict["value"]
                        right_joystick_x_count += 1
                    elif axis == XboxJoystick.JOY_RIGHT_Y:
                        if right_joystick_y_count >= len(right_joysticks):
                            light_event = StickRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            right_joysticks.append(light_event)
                            light_events.append(light_event)
                        right_joysticks[right_joystick_y_count].y = pygame_event.dict["value"]
                        right_joystick_y_count += 1
                    elif axis == XboxJoystick.JOY_LEFT_X:
                        if left_joystick_x_count >= len(left_joysticks):
                            light_event = StickLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            left_joysticks.append(light_event)
                            light_events.append(light_event)
                        left_joysticks[left_joystick_x_count].x = pygame_event.dict["value"]
                        left_joystick_x_count += 1
                    elif axis == XboxJoystick.JOY_LEFT_Y:
                        if left_joystick_y_count >= len(left_joysticks):
                            light_event = StickLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                            )
                            left_joysticks.append(light_event)
                            light_events.append(light_event)
                        left_joysticks[left_joystick_y_count].y = pygame_event.dict["value"]
                        left_joystick_y_count += 1
                    elif axis == XboxJoystick.TRIGGER_RIGHT:
                        light_events.append(
                            TriggerRight(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                z=pygame_event.dict["value"],
                            )
                        )
                    elif axis == XboxJoystick.TRIGGER_LEFT:
                        light_events.append(
                            TriggerLeft(
                                controller_index=controller_index,
                                controller=controller,
                                controller_instance_id=controller_instance_id,
                                z=pygame_event.dict["value"],
                            )
                        )
                    else:
                        pass
                        print(pygame_event)
                else:
                    pass
                    print(pygame_event)
            elif pygame_event.type == 1541:
                controller_index = pygame_event.dict["device_index"]
                if controller_index not in self._controller_index_dict:
                    self.get_controllers()
                controller = self._controller_index_dict[controller_index]
                controller_instance_id = controller.controller.get_instance_id()
                self._controller_instance_dict[controller_instance_id] = controller
                self._instance_to_index_dict[controller_instance_id] = controller_index
                light_events.append(
                    ControllerAdded(
                        controller_instance_id=controller_instance_id,
                        controller_index=controller_index,
                        controller=controller,
                    )
                )
            elif pygame_event.type == 1542:
                controller_instance_id = pygame_event.dict["instance_id"]
                controller = self._controller_instance_dict[controller_instance_id]
                controller_index = self._instance_to_index_dict[controller_instance_id]
                light_events.append(
                    ControllerRemoved(
                        controller_instance_id=controller_instance_id,
                        controller_index=controller_index,
                        controller=controller,
                    )
                )
            else:
                print(pygame_event)
        for event in light_events:
            if event.event_id in self._callbacks:
                self._callbacks[event.event_id](event)
            yield event

    def check_for_winner(self):
        t = time.time()
        if any([player.score >= self.win_score for player in self.players.values()]):
            if not self.win:
                for ship in self.spaceships.values():
                    if ship.score >= self.win_score:
                        break
                self.win = True
                self.win_time = t
                for firework in self.fireworks:
                    firework.color = Pixel(ship.color).array
            for firework in self.fireworks:
                firework.run()
            self.lights.copyVirtualLedsToWS281X()
            self.lights.refreshLEDs()
            if t - self.win_time > LightGame.WIN_DURATION:
                self.win = False
                for i in self.spaceships.keys():
                    self.spaceships[i].score = 0
                    self.spaceships[i]._dead = True

    def respawn_dead_players(self):
        for index, ship in self.players.items():
            if ship.dead:
                if time.time() - ship.dead_time > LightGame.RESPAWN_DELAY:
                    color = self.players[index].color
                    self.players[index] = self.get_new_player
                    self.players[index].color = color

    def show_scores(self):
        for index, ship in self.players.items():
            ready = np.array([Pixel(PixelColors.GRAY.array).array, Pixel(ship.color).array])
            not_ready = np.array([Pixel(PixelColors.OFF.array).array, Pixel(ship.color).array])
            if index % 2 == 0:
                if index == 0:
                    x = 0
                else:
                    x = self.lights.realLEDYaxisRange - 1
                if time.time() - ship.deathray_time >= LightGame.SPECIAL_WEAPON_DELAY:
                    self.lights.virtualLEDBuffer[: int(ship.score), x, :] = ArrayPattern.ColorTransitionArray(
                        int(ship.score), ready
                    )
                else:
                    self.lights.virtualLEDBuffer[: int(ship.score), x, :] = ArrayPattern.ColorTransitionArray(
                        int(ship.score), not_ready
                    )
            else:
                if index == 1:
                    x = 0
                else:
                    x = self.lights.realLEDYaxisRange - 1
                if ship.score > 0:
                    if time.time() - ship.deathray_time >= LightGame.SPECIAL_WEAPON_DELAY:
                        self.lights.virtualLEDBuffer[-int(ship.score) :, x, :] = ArrayPattern.ColorTransitionArray(
                            int(ship.score), ready
                        )
                    else:
                        self.lights.virtualLEDBuffer[-int(ship.score) :, x, :] = ArrayPattern.ColorTransitionArray(
                            int(ship.score), not_ready
                        )

    def update_game(self):
        if not self.win:
            self.fade.run()
        else:
            self.fade.run()
        if not self.pause and not self.win:
            check_for_collisions()
            for obj in GameObject.objects.values():
                try:
                    self.lights.virtualLEDBuffer[obj.xs, obj.ys] = Pixel(obj.color).array
                except:  # noqa
                    pass
            if not self.lights.simulate:
                self.lights.copyVirtualLedsToWS281X()
                self.lights.refreshLEDs()
            else:
                counter = 0
                for row in self.lights.virtualLEDBuffer:
                    for column in row:
                        pygame.draw.rect(self.display, [int(x) for x in column], self.rs[counter])
                        counter += 1
                pygame.display.update()
                time.sleep(0.10)


@dataclass
class ControllerAdded(LightEvent):
    event_id: LightEventId = LightEventId.ControllerAdded


@dataclass
class ControllerRemoved(LightEvent):
    event_id: LightEventId = LightEventId.ControllerRemoved


@dataclass
class ButtonEvent(LightEvent):
    event_id: LightEventId = LightEventId.Button
    state: ButtonState = ButtonState.Unknown

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"button_state={self.state.name}"
        )


@dataclass
class ButtonBottom(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonBottom


@dataclass
class ButtonTop(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonTop


@dataclass
class ButtonLeft(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonLeft


@dataclass
class ButtonRight(ButtonEvent):
    event_id = LightEventId.ButtonRight


@dataclass
class ButtonStart(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonStart


@dataclass
class ButtonOptions(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonOptions


@dataclass
class ButtonPower(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonPower


@dataclass
class ButtonShare(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonShare


@dataclass
class ButtonBumper(ButtonEvent):
    event_id: LightEventId = LightEventId.Bumper


@dataclass
class ButtonBumperLeft(ButtonBumper):
    event_id: LightEventId = LightEventId.BumperLeft


@dataclass
class ButtonBumperRight(ButtonBumper):
    event_id: LightEventId = LightEventId.BumperRight


@dataclass
class ButtonHat(ButtonEvent):
    event_id: LightEventId = LightEventId.Hat
    x: float = 0.0
    y: float = 0.0

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"(x={self.x:0.2f}, "
            + f"y={self.y:0.2f}), "
            + f"button_state={self.state.name}"
        )


@dataclass
class ButtonHatUp(ButtonHat):
    event_id: LightEventId = LightEventId.HatUp
    y: float = 1.0


@dataclass
class ButtonHatDown(ButtonHat):
    event_id: LightEventId = LightEventId.HatDown
    y: float = -1.0


@dataclass
class ButtonHatLeft(ButtonHat):
    event_id: LightEventId = LightEventId.HatLeft
    x: float = -1.0


@dataclass
class ButtonHatRight(ButtonHat):
    event_id: LightEventId = LightEventId.HatRight
    x: float = 1.0


@dataclass
class ButtonStickLeft(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonStickLeft


@dataclass
class ButtonStickRight(ButtonEvent):
    event_id: LightEventId = LightEventId.ButtonStickRight


@dataclass
class Stick(LightEvent):
    event_id: LightEventId = LightEventId.Stick
    x: float = 0.0
    y: float = 0.0

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"(x={self.x:0.2f}, "
            + f"y={self.y:0.2f}), "
        )


@dataclass
class StickRight(Stick):
    event_id: LightEventId = LightEventId.StickRight


@dataclass
class StickLeft(Stick):
    event_id: LightEventId = LightEventId.StickLeft


@dataclass
class Trigger(LightEvent):
    event_id: LightEventId = LightEventId.Trigger
    z: float = 0.0

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__:20s}> "
            + f"event_id={self.event_id.name:15s}:{self.event_id.value}, "
            + f"controller_index={self.controller_index}, "
            + f"controller_instance_id={self.controller_instance_id}, "
            + f"(z={self.z:0.2f}), "
        )


@dataclass
class TriggerRight(Trigger):
    event_id: LightEventId = LightEventId.TriggerRight


@dataclass
class TriggerLeft(Trigger):
    event_id: LightEventId = LightEventId.TriggerLeft
